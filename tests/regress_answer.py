"""离线回归：用真实的 app_*.log 回放「词形还原」和「英译汉选义」两条逻辑。

用法：
    python tests/regress_answer.py                # 只跑内置词形用例（不需要日志）
    python tests/regress_answer.py <app_xxx.log>  # 额外回放日志里每一道判分题

断言：
    1. 日志里出现过的屈折词形都能还原成单元词表里的原形
       （decreed -> decree、magnifies -> magnify；这两条曾导致服务端 code 120，任务被中止）
    2. 原本判对的题，新选义逻辑不得改变选择（零回退）

日志解析只依赖日志里的「解码成功{json}」「查询单词X」「答题判分: answer_result=1/2」三行。
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from util.mean_match import choose_option  # noqa: E402
from util.word_form import match_in_list  # noqa: E402

# 从 app_20261101_184547.log 抽出的两个单元词表（CET6 List 20 / List 21）
UNIT_20 = ("illicit wretched exempt repute vogue icon refund prone maritime innumerable potent intercourse "
           "intrigue grim lime decree dismay liner emulate swamp prolong shatter coincide pottery leaflet "
           "stoop secular pathetic stray auction").split()
UNIT_21 = ("endeavor midwife magnify scrub cunning amplify censor blunt majesty inmate dart hostage tilt perch "
           "chancellor unanimous revolt compartment mutter conspicuous emigrate contemplate bald erupt "
           "proofread complacent snap archive glide captive").split()

# (题干词形, 期望还原结果, 所属词表)
FORM_CASES = [
    ("decreed", "decree", UNIT_20),        # 曾原样返回 decreed -> 120
    ("magnifies", "magnify", UNIT_21),     # 曾返回 magnifie -> 120
    ("magnified", "magnify", UNIT_21),
    ("snapped", "snap", UNIT_21),
    ("endeavors", "endeavor", UNIT_21),
    ("inmates", "inmate", UNIT_21),
    ("glides", "glide", UNIT_21),
    ("erupts", "erupt", UNIT_21),
    ("emigrated", "emigrate", UNIT_21),
    ("archives", "archive", UNIT_21),
    ("amplified", "amplify", UNIT_21),
    ("perched", "perch", UNIT_21),
    ("scrubbing", "scrub", UNIT_21),
    ("auctioned", "auction", UNIT_20),
    ("dismayed", "dismay", UNIT_20),
    ("exempted", "exempt", UNIT_20),
    # 已经是原形：必须原样返回，不能被乱改
    ("magnify", "magnify", UNIT_21),
    ("decree", "decree", UNIT_20),
    ("blunt", "blunt", UNIT_21),
]


def check_word_form():
    failures = []
    for surface, expected, words in FORM_CASES:
        got = match_in_list(surface, words)
        if got != expected:
            failures.append(f"  词形还原 {surface}: 期望 {expected!r}，实际 {got!r}")
    # 词表内的词必须映射到自身
    for words in (UNIT_20, UNIT_21):
        for word in words:
            got = match_in_list(word, words)
            if got != word:
                failures.append(f"  词表词 {word}: 应返回自身，实际 {got!r}")
    print(f"[词形还原] 用例 {len(FORM_CASES) + len(UNIT_20) + len(UNIT_21)} 条，失败 {len(failures)} 条")
    return failures


def _json_of(line):
    if '解码成功' not in line:
        return None
    try:
        return json.loads(line.split('解码成功', 1)[1])
    except Exception:
        return None


def parse_log(path):
    """把日志还原成题目序列：每道题带上题面、选项、查词结果、旧选择与判分"""
    lines = open(path, encoding='utf-8', errors='replace').read().splitlines()
    exams, means, verdicts, chosen, asked = {}, {}, {}, {}, {}
    current_word = None
    for index, line in enumerate(lines):
        found = re.search(r'INFO: 查询单词(\S+)$', line)
        if found and found.group(1) != '成功':
            current_word = found.group(1)
        data = _json_of(line)
        if isinstance(data, dict):
            if 'topic_mode' in data:
                exams[index] = data
            elif 'means' in data and current_word:
                means[current_word] = data
        result = re.search(r'答题判分: answer_result=(\d)', line)
        if result:
            verdicts[index] = int(result.group(1))
            asked[index] = current_word
        option = re.search(r'选项\[(.+?)\]', line)
        if option and '匹配第' in line:
            chosen[index] = option.group(1)
    return exams, means, verdicts, chosen, asked


def last_before(mapping, index):
    keys = [k for k in mapping if k < index]
    return mapping[max(keys)] if keys else None


def replay(path):
    exams, means, verdicts, chosen, asked = parse_log(path)
    regression, rescued, same, missing = [], 0, 0, 0
    for index, verdict in sorted(verdicts.items()):
        exam = last_before(exams, index)
        if not exam:
            missing += 1
            continue
        query_result = means.get(asked.get(index) or '') or {}
        options = [item.get('content') for item in exam.get('options') or []]
        pick = choose_option(query_result, exam, options)
        old = last_before(chosen, index)
        if pick is None:
            missing += 1
            continue
        if old is None or pick == old:
            same += 1
            continue
        if verdict == 1:
            regression.append(f"  判对却被改动: {asked.get(index)} 旧={old!r} 新={pick!r}")
        else:
            rescued += 1
    print(f"[选义回放] 判分题 {len(verdicts)} 道：一致/无旧记录 {same}、"
          f"错题改变 {rescued}、判对被改（回退）{len(regression)}、无匹配 {missing}")
    return regression


def main():
    failures = check_word_form()
    if len(sys.argv) > 1:
        log_path = sys.argv[1]
        if not os.path.exists(log_path):
            print(f"日志不存在：{log_path}")
            return 1
        failures += replay(log_path)
    else:
        print("（未提供日志，跳过选义回放）")
    if failures:
        print("\n失败项：")
        print("\n".join(failures))
        return 1
    print("\n全部通过")
    return 0


if __name__ == '__main__':
    sys.exit(main())
