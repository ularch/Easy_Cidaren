import random
import re
import time
import json
from urllib.parse import unquote

from api.main_api import query_word, submit_result, next_exam
from log.log import Log
from publicInfo.publicInfo import PublicInfo
from decryptencrypt.debase64 import debase64
from util.basic_util import delete_other_char
from util.answer_lib import lookup, lookup_word
from util.select_mean import select_mean, handle_query_word_mean, filler_option, select_match_word, word_examples, \
    is_word_exist
from util.word_revert import word_revert

query_answer = Log('answer_questions')


def _template_slots(content: str):
    """mode 32 模板空位解析: 返回 (空位token列表, 总词位数)。
    '_'=1 词位(接受连字符词整体, 如 low-carbon), '_-_'=2 词位(需拆分词 waste,free, 实证 165203)。
    用正则匹配空位 token(兼容标点粘连如 '_,'/'(_,)'), split() 只识别独立 token"""
    slots = []
    total = 0
    for m in re.finditer(r'_-_|_', content or ''):
        tok = m.group(0)
        if tok == '_':
            slots.append('_')
            total += 1
        else:
            slots.append('_-_')
            total += 2
    return slots, total


def _norm_word(w: str) -> str:
    """去词首尾标点(保留内部连字符/撇号): 'struggle,' -> 'struggle'"""
    return w.strip(' \t,;:.()[]"\'，。、；：')


def _build_phrase_answer(public_info, phrase: str) -> str:
    """
    mode 32 汉译英填空: 按题目 options 单词池过滤短语中的固定词(and/of/for/the等),
    按模板空位对齐提交(逗号连接), 服务端按逗号 split 依次填入空位重建比对判分
    """
    options = [o.get('content') for o in (public_info.exam.get('options') or []) if isinstance(o, dict)]
    if not options:
        return delete_other_char(phrase)
    opt_lower = [o.lower() for o in options if isinstance(o, str)]
    opt_set = set(opt_lower)
    # 选项段聚合: 短语词序从左到右——优先多词选项段(最长优先, 'all our'/'the country'/'a New Era' 整段占一空位),
    # 再 1 词匹配(原词优先, 其次去标点 'struggle,'->'struggle'); 未命中视为固定词跳过;
    # 连字符词不在 options 但其拆分词都在 options(waste/free)时保留整体, 由模板对齐决定拆分
    tokens = phrase.split()
    cand = []
    i = 0
    while i < len(tokens):
        w = tokens[i]
        matched = False
        for k in range(3, 1, -1):
            if i + k <= len(tokens):
                seg = ' '.join(tokens[i:i + k])
                if seg.lower() in opt_set:
                    cand.append(seg)
                    i += k
                    matched = True
                    break
        if matched:
            continue
        nw = _norm_word(w)
        if w.lower() in opt_set:
            cand.append(w)
            i += 1
            continue
        if nw.lower() in opt_set:
            cand.append(nw)
            i += 1
            continue
        if '-' in w:
            parts = [p.lower() for p in w.split('-') if p]
            if parts and all(p in opt_set for p in parts):
                cand.append(w)
                i += 1
                continue
        i += 1
    if not cand:
        return delete_other_char(phrase)
    # 模板对齐: '_' 空位取 1 词(连字符词整体), '_-_' 空位取连字符词拆 2 词
    content = public_info.exam.get('stem', {}).get('content', '') if isinstance(public_info.exam, dict) else ''
    slots, slot_words = _template_slots(content)
    if slot_words:
        result = []
        ci = 0
        for slot in slots:
            if ci >= len(cand):
                break
            w = cand[ci]
            if slot == '_-_' and '-' in w:
                parts = w.split('-')
                if all(p.lower() in opt_set for p in parts):
                    result.extend(parts)
                    ci += 1
                    continue
            result.append(w)
            ci += 1
        # 词位校验: 提交词数必须等于模板词位数, 否则按词位补足/截断会判错, 回退拆分提交
        if len(result) == slot_words:
            picked = result
        else:
            picked = [p for w in cand for p in (w.split('-') if '-' in w else [w])]
            picked = [p for p in picked if p.lower() in opt_set]
    else:
        picked = cand
    if not picked:
        return delete_other_char(phrase)
    query_answer.logger.info(f"短语过滤固定词:{cand} -> {picked}")
    return ','.join(picked)


def _match_phrase_by_word_zh(public_info, word_mean):
    """
    按中文释义匹配词表中的英文短语(术语课程)
    :param public_info:
    :param word_mean:
    :return:
    """
    word_map = getattr(public_info, 'word_dict', None) or {}
    if not word_map:
        # 兼容词表未经过 handle_word_result 的场景
        data = getattr(public_info, 'get_word_list_result', None)
        try:
            if isinstance(data, dict) and 'data' in data:
                raw = data['data']
                if isinstance(raw, dict):
                    word_list = raw.get('word_list', [])
                elif 'jv' in data:
                    word_list = debase64(raw, data['jv'])['word_list']
                else:
                    word_list = []
                for item in word_list:
                    word_map[item['word_zh']] = item['word']
        except Exception as e:
            query_answer.logger.error(f"词表解析失败:{e}")
    if not word_map:
        return None
    # 精确匹配
    if word_mean in word_map:
        return word_map[word_mean]
    # 归一化匹配(去空白/括号/引号等)
    pattern = r'[\s（）()“”"\'‘’《》]'
    norm_mean = re.sub(pattern, '', word_mean)
    for zh, en in word_map.items():
        if re.sub(pattern, '', zh) == norm_mean:
            return en
    return None


# submit
def submit(public_info: PublicInfo, option: int or str or dict):
    """
    提交答案
    :param public_info:
    :param option: 选项索引或单词
    :return: None
    """
    public_info.topic_code = public_info.exam['topic_code']
    # submit result
    if type(option) == dict:
        # resolve mode == 31
        for answer_index in option.values():
            submit_result(public_info, answer_index)
    else:
        submit_result(public_info, option)
    #
    time.sleep(random.randint(1, 2))
    # get next exam
    next_exam(public_info)


# skip read word
def jump_read(public_info):
    """
    跳过阅读卡片
    """
    time.sleep(random.randint(1, 3))
    query_answer.logger.info("跳过阅读单词卡片")
    next_exam(public_info)
    public_info.topic_code = public_info.exam['topic_code']


# mean form word
def select_word(public_info) -> int or str or None:
    word_mean = public_info.exam['stem']['remark']
    query_answer.logger.info("汉译英:" + word_mean)
    # 本地答案库命中优先(标准答案,按题目 options 过滤固定词后逗号提交)
    lib_answers = lookup(word_mean)
    if lib_answers:
        query_answer.logger.info(f"答案库命中:{lib_answers[0]}")
        return _build_phrase_answer(public_info, lib_answers[0])
    # option word
    options = filler_option(public_info)
    for option in options:
        # word is exist word_list
        if is_word_exist(public_info, option):
            # two response types
            if public_info.word_query_result.get('means'):
                query_result = public_info.word_query_result['means']
                for means in query_result:
                    for usage in means['usages']:
                        phrases_infos = usage['phrases_infos']
                        if phrases_infos:
                            for phrases_info in phrases_infos:
                                # match same mean
                                if phrases_info['sen_mean_cn'] == word_mean:
                                    return delete_other_char(phrases_info['sen_content'])

            else:
                query_result = public_info.word_query_result['options']
                for content in query_result:
                    for usage_info in content['content']['usage_infos']:
                        if usage_info['sen_mean_cn'] == word_mean:
                            return delete_other_char(usage_info['sen_content'])
    # 词表短语兜底: 术语课程按中文释义反查英文短语
    phrase = _match_phrase_by_word_zh(public_info, word_mean)
    if phrase:
        query_answer.logger.info(f"词表匹配到短语:{phrase}")
        return _build_phrase_answer(public_info, unquote(phrase))
    query_answer.logger.info("查询失败,准备跳过")
    # exit(-1)
    return None


def word_form_mean(public_info: PublicInfo) -> int:
    """
    英译汉
    :param public_info:
    :return:
    """
    query_answer.logger.info("英译汉")
    # is listen
    exam = public_info.exam['stem']['content'].replace(' ', "")
    # 题干格式xxx{word}xxx
    query_answer.logger.info(f"从{exam}提取单词")
    word = re.findall("{(.*?)}", exam)
    query_answer.logger.info(f"提取到{word}")
    word = word[0] if word else exam
    # 判断单词是否在单词列表中
    if word not in public_info.word_list:
        if word.endswith("ed") and word[:-2] in public_info.word_list:
            word = word[:-2]
        elif word.endswith("ing") and word[:-3] in public_info.word_list:
            word = word[:-3]
        else:
            query_answer.logger.info(f"将{word}转原型")
            # 单词转原型
            word = word_revert(word)
    # 请求单词释义
    query_word(public_info, word)
    # 提取释义
    handle_query_word_mean(public_info)
    query_answer.logger.info('选择意思')
    # 选择正确释义
    return select_mean(public_info)


def mean_to_word(public_info):
    """
    看义选词
    :param public_info:
    :return:
    """
    # mode 17
    word_mean = public_info.exam['stem']['content']
    # match answer
    return select_match_word(public_info, word_mean)


# select together word
def together_word(public_info) -> dict:
    query_answer.logger.info("意思相似单词")
    # exam options
    options = filler_option(public_info)
    # answer
    result_word = {word['relation']: options.index(word['relation']) for word in public_info.exam['stem']['remark']}
    query_answer.logger.info(f"选项{options}")
    query_answer.logger.info(f"答案{result_word}")
    return result_word


# complete a sentence
def full_sentence(public_info) -> int or str:
    query_answer.logger.info("选择最合适的单词完成句子")
    options = filler_option(public_info)
    # 单词库命中优先(mode 42: answer_corrects 下标对应的正确答案单词)
    remark = public_info.exam.get('stem', {}).get('remark') if isinstance(public_info.exam, dict) else None
    word_answers = lookup_word(remark)
    if word_answers:
        # 排除题干中已出现的固定词(如 environmentally {} manufacturing 中 manufacturing),
        # 避免单词库含完整短语多个词时定位到固定词(如 绿色制造 误选 manufacturing 而非 conscious)
        content = public_info.exam.get('stem', {}).get('content', '') if isinstance(public_info.exam, dict) else ''
        fixed = set(re.findall(r'[A-Za-z]+', content.replace('{}', ' ').replace('{', ' ').replace('}', ' ')))
        fixed = {w.lower() for w in fixed}
        lower_words = [w.lower() for w in word_answers if w.lower() not in fixed]
        if not lower_words:
            lower_words = [w.lower() for w in word_answers]
        for option in public_info.exam['options']:
            if isinstance(option, dict) and option.get('content', '').lower() in lower_words:
                query_answer.logger.info(f"单词库命中,提交{option.get('content')}(tag={option.get('answer_tag')})")
                return option.get('answer_tag')
    # word in examples sentence
    word = word_examples(public_info, options)
    # extract answer tag
    for option in public_info.exam['options']:
        # match answer
        option_word = option['answer_tag']
        if type(option_word) == str:
            if option['sub_options']:
                for sub_option in option['sub_options']:
                    if sub_option['content'] == word:
                        return option_word + str(sub_option['answer_tag'])
            # no need to  match  tenses
            if option['content'] == word:
                return option_word + '0'
        else:
            if option['content'] == word:
                return option_word
    query_answer.logger.error("补全句子失败,猜第3个选项")
    # submit 1#0,0#2 or 1 应该分开写提升正确率
    return public_info.exam['options'][2]['answer_tag']


# full word
def complete_sentence(public_info):
    query_answer.logger.info("补全单词")
    word_len = public_info.exam['w_lens'][0]
    # submit not  case sensitive
    word_start_with = public_info.exam['w_tip'].lower()
    # iterate over all word in the unit
    for word in public_info.word_list:
        if word.startswith(word_start_with):
            query_answer.logger.info(word)
            if len(word) == word_len:
                return word
            elif len(word) + 1 == word_len:
                return word + 's'
            else:
                result = word_examples(public_info, [word])
                if result:
                    return result
    query_answer.logger.error(f"找不到答案,提交{word}")
    return word


# mode 73: 多空首字母补全单词(提交JSON数组)
def _match_tips_words(tips, word_lens, words, strict_len=True, exclude=None):
    """按 tips 前缀(可选长度)匹配单词, 全部匹配返回列表, 否则 None. exclude=题干固定词集合(小写), 匹配时跳过"""
    exclude = exclude or set()
    answers = []
    for i, tip in enumerate(tips):
        wlen = word_lens[i] if i < len(word_lens) else None
        matched = None
        for w in words:
            if w.lower() in exclude:
                continue
            if w.lower().startswith(tip.lower()) and (not strict_len or not wlen or len(w) == int(wlen)):
                matched = w
                break
        if matched is None:
            return None
        answers.append(matched)
    return answers


def _candidate_words(public_info, remark):
    """mode 73 候选答案单词池(合并): 短语库[0] -> 单词库(变体) -> 词表短语, 按空白/连字符/括号拆分, 去重保序"""
    pool = []
    lib_answers = lookup(remark)
    if lib_answers:
        pool += [w for w in re.split(r'[\s\-(),]+', lib_answers[0]) if w]
    word_answers = lookup_word(remark)
    if word_answers:
        pool += list(word_answers)
    phrase = _match_phrase_by_word_zh(public_info, remark)
    if phrase:
        pool += [w for w in re.split(r'[\s\-(),]+', unquote(phrase)) if w]
    return list(dict.fromkeys(pool)) or None


def _global_word_pool(public_info):
    """全局词表单词池: 所有词条英文短语按 空白/连字符/括号/斜杠 拆分, 去重保序。
    mode 73 前缀单词(如 utilization/conservation/transform)常存在于其他词条词表中,
    候选池按词条隔离用不到, 此池跨词条兜底"""
    word_map = getattr(public_info, 'word_dict', None) or {}
    if not word_map:
        return None
    pool = []
    for en in word_map.values():
        pool += [w for w in re.split(r'[\s\-(),/]+', unquote(en)) if w]
    return list(dict.fromkeys(pool)) or None


def complete_spelling(public_info):
    query_answer.logger.info("补全拼写")
    content = public_info.exam['stem']['content']
    remark = public_info.exam['stem']['remark']
    tips = re.findall(r'\{(\w+)\}', content)
    word_lens = public_info.exam.get('w_lens') or []
    # 题干固定词(如 {gr}{sto} 前的 green、Lucid waters 中的 Lucid、and 等), 前缀匹配时排除,
    # 避免误把固定词当空位答案(green->gr、and->a、Lucid->lu)
    fixed = set(w.lower() for w in re.findall(r'[A-Za-z]+', re.sub(r'\{[^}]*\}', ' ', content)))
    if not tips:
        # 无前缀空位题({}): 候选单词 ∩ 题目 options(答案单词池) 直接提交
        slot_count = content.count('{}')
        options = [o.get('content') for o in (public_info.exam.get('options') or []) if isinstance(o, dict)]
        opt_lower = [o.lower() for o in options if isinstance(o, str)]
        candidates = _candidate_words(public_info, remark)
        if candidates:
            picked = [w for w in candidates if w.lower() in opt_lower]
            if picked:
                answers = picked[:slot_count] if slot_count else picked
                query_answer.logger.info(f"无前缀空位命中,补全拼写结果:{answers}")
                return json.dumps(answers)
        query_answer.logger.error("补全拼写失败:无前缀空位无匹配")
        return None
    # 1. 本地答案库短语命中(标准答案,按前缀匹配单词)
    lib_answers = lookup(remark)
    if lib_answers:
        # 按 空白/连字符/括号/斜杠 拆分(air/atmospheric -> air, atmospheric)
        words = [w for w in re.split(r'[\s\-(),/]+', lib_answers[0]) if w]
        answers = _match_tips_words(tips, word_lens, words, exclude=fixed)
        if answers:
            query_answer.logger.info(f"答案库命中,补全拼写结果:{answers}")
            return json.dumps(answers)
    # 2. 单词库命中(同义变体,如 {sup}->supervision; 由 mode 42 提交后捕获)
    word_answers = lookup_word(remark)
    if word_answers:
        answers = _match_tips_words(tips, word_lens, word_answers, strict_len=False, exclude=fixed)
        if answers:
            query_answer.logger.info(f"单词库变体命中,补全拼写结果:{answers}")
            return json.dumps(answers)
    # 3. 词表短语兜底
    phrase = _match_phrase_by_word_zh(public_info, remark)
    if phrase:
        words = unquote(phrase).split()
        answers = _match_tips_words(tips, word_lens, words, exclude=fixed)
        if answers:
            query_answer.logger.info(f"补全拼写结果:{answers}")
            return json.dumps(answers)
    # 4. 合并候选池兜底(跨来源组合, 如 {ze}-{wa} -> zero+waste): 先严格长度, 失败再宽松
    candidates = _candidate_words(public_info, remark)
    if candidates:
        answers = _match_tips_words(tips, word_lens, candidates, exclude=fixed)
        if answers:
            query_answer.logger.info(f"合并候选池命中,补全拼写结果:{answers}")
            return json.dumps(answers)
        answers = _match_tips_words(tips, word_lens, candidates, strict_len=False, exclude=fixed)
        if answers:
            query_answer.logger.info(f"合并候选池宽松命中,补全拼写结果:{answers}")
            return json.dumps(answers)
    # 5. 全局词表单词池兜底(前缀单词在其他词条词表中, 如 {uti}->utilization、{con}->conservation、{tra}->transform)
    gpool = _global_word_pool(public_info)
    if gpool:
        answers = _match_tips_words(tips, word_lens, gpool, exclude=fixed)
        if answers:
            query_answer.logger.info(f"全局词表命中,补全拼写结果:{answers}")
            return json.dumps(answers)
        # 宽松兜底(如 {res}->resources 9 位 vs w_lens 8): 提交判错 -> answer_corrects 入库 -> 下次自愈(判错优于永远跳过)
        answers = _match_tips_words(tips, word_lens, gpool, strict_len=False, exclude=fixed)
        if answers:
            query_answer.logger.info(f"全局词表宽松命中,补全拼写结果:{answers}")
            return json.dumps(answers)
    query_answer.logger.error(f"补全拼写失败:未匹配到前缀")
    return None


def answer(public_info, mode):
    '''
    15 看词选义（一星）
    16 看词选义（二星）
    17 看义选词（一星）
    18 看义选词（二星）
    :param mode: 题型编号
    :return:
    '''
    if mode == 11:
        option = word_form_mean(public_info)
    elif mode == 13:
        # guess option 没思路
        option = 3
    elif mode == 15 or mode == 16 or mode == 21 or mode == 22:
        option = word_form_mean(public_info)
        # 英译汉
    elif mode == 17 or mode == 18:
        option = mean_to_word(public_info)
    elif mode == 31:
        option = together_word(public_info)
    elif mode == 32:
        option = select_word(public_info)
        query_answer.logger.info(f'翻译结果{option}')
    elif mode == 41 or mode == 42 or mode == 43 or mode == 44:
        option = full_sentence(public_info)
        query_answer.logger.info(f'提交选项{option}')
    # mode == 43  "content":"Reading  is  of  {}  importance  in  language  learning.","remark":"阅读在语言学习中至关重要。" 选时态
    elif mode == 51 or mode == 52 or mode == 53 or mode == 54:
        option = complete_sentence(public_info)
        query_answer.logger.info(f'补全单词结果{option}')
    elif mode == 73:
        option = complete_spelling(public_info)
        query_answer.logger.info(f'补全拼写结果{option}')
    else:
        option = 0
        query_answer.logger.error(public_info.exam)
        query_answer.logger.error(f"其他题型{mode},程序退出")
        # 此处抛出异常
        raise Exception
    return option
