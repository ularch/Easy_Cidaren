"""
英译汉（看词选义）的选项匹配：释义归一化 + 用例句反查义项。
"""

import re

_POS_RE = re.compile(r'^\s*([A-Za-z]+)\.\s*')
_POS_ALIAS = {
    'n': 'n', 'noun': 'n',
    'v': 'v', 'vt': 'v', 'vi': 'v', 'verb': 'v',
    'a': 'a', 'adj': 'a', 'ad': 'a', 'adv': 'a',
}
_SPLIT_RE = re.compile(r'[，,、；;/]')
_BRACKET_RE = re.compile(r'（[^）]*）|\([^)]*\)')
_EN_RE = re.compile(r'[^a-z]')


def parse_pos(text: str) -> str or None:
    """提取释义开头的词性标记，并归一化：vt./vi./v. -> v，adj./a. -> a"""
    match = _POS_RE.match(text or '')
    if not match:
        return None
    return _POS_ALIAS.get(match.group(1).lower())


def norm_groups(text: str) -> set:
    """释义归一化成词组集合：去括号补充说明、去词性前缀、按标点切分"""
    plain = _BRACKET_RE.sub('', text or '')
    plain = _POS_RE.sub('', plain.strip())
    return {part.strip() for part in _SPLIT_RE.split(plain) if part.strip()}


def groups_match(option: str, target: str) -> bool:
    """两组释义是否为同一意思（相等或一方包含另一方）"""
    option_groups, target_groups = norm_groups(option), norm_groups(target)
    if not option_groups or not target_groups:
        return False
    return option_groups == target_groups or option_groups <= target_groups or target_groups <= option_groups


def _norm_sentence(text: str) -> str:
    """英文句子归一化"""
    return _EN_RE.sub('', (text or '').lower())


def locate_sense(query_result: dict, exam: dict) -> int or None:
    """用题干句子反查义项"""
    if not isinstance(query_result, dict) or not isinstance(exam, dict):
        return None
    stem = exam.get('stem') or {}
    content = stem.get('content') or ''
    remark = (stem.get('remark') or '').strip()
    if '{' not in content and ' ' not in content:
        return None
    key = _norm_sentence(content)
    if not key:
        return None
    for index, mean in enumerate(query_result.get('means') or []):
        if not isinstance(mean, dict):
            continue
        for usage in mean.get('usages') or []:
            if not isinstance(usage, dict):
                continue
            for example in usage.get('examples') or []:
                if not isinstance(example, dict):
                    continue
                if _norm_sentence(example.get('sen_content')) == key:
                    return index
                if remark and (example.get('sen_mean_cn') or '').strip() == remark:
                    return index
    return None


def means_of(query_result: dict) -> list:
    if not isinstance(query_result, dict):
        return []
    options = query_result.get('options')
    if options:
        means = []
        for item in options:
            content = (item or {}).get('content') or {}
            mean = content.get('mean') if isinstance(content, dict) else None
            if mean:
                means.append(_BRACKET_RE.sub('', mean))
        return means
    means = []
    for mean in query_result.get('means') or []:
        if isinstance(mean, dict) and mean.get('mean'):
            means.append(' '.join(mean['mean']))
    return means


def pick_by_sense(options, target):
    """已知目标义项时选选项"""
    for strict in (True, False):
        target_pos = parse_pos(target)
        for option in options:
            if not groups_match(option, target):
                continue
            if strict and target_pos and parse_pos(option) and parse_pos(option) != target_pos:
                continue
            return option
    return None


def pick_by_option_order(options, targets):
    """未知义项时的兜底"""
    for option in options:
        for target in targets:
            if groups_match(option, target):
                return option
    return None


def choose_option(query_result: dict, exam: dict, options) -> str or None:
    """给出应提交的选项文本"""
    means = means_of(query_result)
    if not means or not options:
        return None
    sense = locate_sense(query_result, exam)
    if sense is not None and 0 <= sense < len(means):
        hit = pick_by_sense(options, means[sense])
        if hit:
            return hit
    return pick_by_option_order(options, means)
