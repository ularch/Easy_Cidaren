import re

from api.main_api import query_word
from log.log import Log
from util.word_revert import word_revert

# log module
select_module = Log("select_module")


#
def handle_query_word_mean(public_info) -> None:
    # {'course_id': 'CET4_pre', 'list_id': 'CET4_pre_03', 'word': 'pack', 'update_version': '2402041319', 'means': [{'mean': ['verb', '收拾（行李）；装（箱）'], 'ph_info': {'ph_en': 'pæk', 'ph_en_url': '/Resource/unitAudio_EN/CET4_pre_03/pack.mp3', 'ph_us': 'pæk', 'ph_us_url': '/Resource/unitAudio_US/CET4_pre_03/pack.mp3'}, 'usages': [{'usage': None, 'phrases': [], 'phrases_infos': [], 'examples': [{'sen_id': '688', 'sen_content': "Mary, I hope you're {packed} and ready to leave.", 'sen_mean_cn': '玛丽，我希望你收拾好行李准备离开。', 'sen_source': '[CET4 07年12月]', 'sen_source_code': 'CET4_0712_LL1_1M_1', 'audio_file': '/CET4_pre_03/pack/688.mp3'}, {'sen_id': '695', 'sen_content': "I've {packed} it, but I can't remember which bag it's in.", 'sen_mean_cn': '我把它装好了，但我记不起它在哪个包里了。', 'sen_source': '[CET4 07年12月]', 'sen_source_code': 'CET4_0712_LL1_4W_3', 'audio_file': '/CET4_pre_03/pack/695.mp3'}, {'sen_id': '562846', 'sen_content': 'We can {pack} a suitcase with flashlights, a radio, food, drinking water and some tools.', 'sen_mean_cn': '我们可以把手电筒、收音机、食物、饮用水和一些工具打包装入手提箱。', 'sen_source': '[CET6 13年06月]', 'sen_source_code': 'CET6_13063_LP2_1_5_01', 'audio_file': '/CET4_pre_03/pack/562846.mp3'}, {'sen_id': '521628', 'sen_content': 'She hurriedly {packed} a bag and bought a train ticket for home.', 'sen_mean_cn': '她赶快收拾了一下手提包，买了车票回家。', 'sen_source': '', 'sen_source_code': '', 'audio_file': '/CET4_pre_03/pack/521628.mp3'}, {'sen_id': '521637', 'sen_content': 'She {packed} her few belongings in a bag and left.', 'sen_mean_cn': '她把她的几件东西装进包里便离开了。', 'sen_source': '', 'sen_source_code': '', 'audio_file': '/CET4_pre_03/pack/521637.mp3'}]}]}, {'mean': ['noun', '包；盒'], 'ph_info': {'ph_en': 'pæk', 'ph_en_url': '/Resource/unitAudio_EN/CET4_pre_03/pack.mp3', 'ph_us': 'pæk', 'ph_us_url': '/Resource/unitAudio_US/CET4_pre_03/pack.mp3'}, 'usages': [{'usage': None, 'phrases': [], 'phrases_infos': [], 'examples': [{'sen_id': '2185', 'sen_content': "Likewise, a married man who smokes more than a {pack} a day is likely to live as long as a divorced man who doesn't smoke.", 'sen_mean_cn': '同样地，一个每天吸烟超过一包的已婚男人很可能和一个不吸烟的离婚男人一样长寿。', 'sen_source': '[CET4 10年12月]', 'sen_source_code': 'CET4_1012_RP2_02_03', 'audio_file': '/CET4_pre_03/pack/2185.mp3'}, {'sen_id': '521639', 'sen_content': 'Each {pack} contains a book and accompanying CD.', 'sen_mean_cn': '每包内装书一本，并附光盘一张。', 'sen_source': '', 'sen_source_code': '', 'audio_file': '/CET4_pre_03/pack/521639.mp3'}, {'sen_id': '562705', 'sen_content': 'Envelopes are cheaper if you buy them in {packs} of 100.', 'sen_mean_cn': '信封如果按每包100个地成包购买会便宜一些。', 'sen_source': '', 'sen_source_code': '', 'audio_file': '/CET4_pre_03/pack/562705.mp3'}]}, {'usage': {'marked': 'a {pack} of <i>sth</i> ', 'text': 'a pack of sth ', 'cn': '一包/盒…', 'eg': 'a {pack} of cigarettes', 'eg_cn': ''}, 'phrases': ['a {pack} of … 一包……'], 'phrases_infos': [{'sen_id': '156901', 'sen_content': 'a {pack} of …', 'sen_mean_cn': '一包……', 'audio_file': '/CET4_pre_03/pack/156901.mp3'}], 'examples': [{'sen_id': '477487', 'sen_content': 'He reached into a drawer for a {pack} of cigarettes.', 'sen_mean_cn': '他把手伸进抽屉里，掏出一包香烟。', 'sen_source': '', 'sen_source_code': '', 'audio_file': '/CET4_pre_03/pack/477487.mp3'}]}]}], 'version': '2', 'has_au': 1, 'au_addr': 'https://resource-cdn.vocabgo.com', 'au_word': 'pack', 'word_info': {'store_status': 0}}
    means = []
    if public_info.word_query_result.get('options'):
        # {'course_id': 'XSJ_4', 'list_id': 'XSJ_4_7_A', 'word': 'detached', 'update_version': '2402041319', 'ph_en': 'dɪˈtætʃt', 'ph_us': 'dɪˈtætʃt', 'options': [{'content': {'mean': 'adj  超然的；冷漠的', 'ph_info': {'ph_en': 'dɪˈtætʃt', 'ph_en_url': '/Resource/unitAudio_EN/XSJ_4_7_A/detached.mp3', 'ph_us': 'dɪˈtætʃt', 'ph_us_url': '/Resource/unitAudio_US/XSJ_4_7_A/detached.mp3'}, 'usage_infos': [{'sen_id': '83415', 'sen_content': '{detached} observer', 'sen_mean_cn': '超然的旁观者', 'audio_file': '/XSJ_4_7_A/detached/83415.mp3'}, {'sen_id': '83416', 'sen_content': '{detached} attitude', 'sen_mean_cn': '超然的态度', 'audio_file': '/XSJ_4_7_A/detached/83416.mp3'}], 'usage': ['{detached} observer 超然的旁观者', '{detached} attitude 超然的态度'], 'example': [{'sen_id': '150878', 'sen_content': 'She wanted him to stop being so cool, so {detached}.', 'sen_mean_cn': '她希望他不再那么冷酷无情，那么无动于衷。', 'sen_source': '', 'sen_source_code': '', 'audio_file': '/XSJ_4_7_A/detached/150878.mp3'}, {'sen_id': '282590', 'sen_content': 'Through all the arguments among other committee members, she kept a {detached} attitude.', 'sen_mean_cn': '在其他委员会成员辩论时，她始终保持超然的态度。', 'sen_source': '', 'sen_source_code': '', 'audio_file': '/XSJ_4_7_A/detached/282590.mp3'}, {'sen_id': '445016', 'sen_content': 'Throughout the novel, the whole story is seen through the eyes of a {detached} observer.', 'sen_mean_cn': '小说自始至终是从一个超然的旁观者的角度来看整个故事的。', 'sen_source': '', 'sen_source_code': '', 'audio_file': '/XSJ_4_7_A/detached/445016.mp3'}, {'sen_id': '150879', 'sen_content': 'He tries to remain emotionally {detached} from the prisoners, but fails.', 'sen_mean_cn': '他试图不带感情地对待那些犯人，但是做不到。', 'sen_source': '', 'sen_source_code': '', 'audio_file': '/XSJ_4_7_A/detached/150879.mp3'}]}}, {'content': {'mean': 'adj 客观的，公正的', 'ph_info': {'ph_en': 'dɪˈtætʃt', 'ph_en_url': '/Resource/unitAudio_EN/XSJ_4_7_A/detached.mp3', 'ph_us': 'dɪˈtætʃt', 'ph_us_url': '/Resource/unitAudio_US/XSJ_4_7_A/detached.mp3'}, 'usage_infos': [{'sen_id': '89188', 'sen_content': '{detached} evaluation', 'sen_mean_cn': '客观公正的评估', 'audio_file': '/XSJ_4_7_A/detached/89188.mp3'}, {'sen_id': '89189', 'sen_content': 'take a {detached} view', 'sen_mean_cn': '采用公正客观的视角', 'audio_file': '/XSJ_4_7_A/detached/89189.mp3'}], 'usage': ['{detached} evaluation 客观公正的评估', 'take a {detached} view 采用公正客观的视角'], 'example': [{'sen_id': '150929', 'sen_content': 'As a judge, he has always been {detached} in dealing with cases.', 'sen_mean_cn': '作为法官，他在处理案件时总是客观公正的。', 'sen_source': '', 'sen_source_code': '', 'audio_file': '/XSJ_4_7_A/detached/150929.mp3'}, {'sen_id': '150922', 'sen_content': 'Evaluation of public servants shall be {detached}.', 'sen_mean_cn': '对公务员的考核应当客观公正。', 'sen_source': '', 'sen_source_code': '', 'audio_file': '/XSJ_4_7_A/detached/150922.mp3'}, {'sen_id': '150915', 'sen_content': 'A judge must be {detached} when weighing evidence.', 'sen_mean_cn': '法官在掂量证据时应该客观公正。', 'sen_source': '', 'sen_source_code': '', 'audio_file': '/XSJ_4_7_A/detached/150915.mp3'}]}}], 'version': '1', 'has_au': 1, 'au_addr': 'https://resource-cdn.vocabgo.com', 'au_word': 'detached', 'word_info': {'store_status': 0}}
        for mean in public_info.word_query_result['options']:
            means.append(re.sub("（.*）", "", mean['content']['mean']))
    else:
        for mean in public_info.word_query_result['means']:
            means.append(' '.join(mean['mean']))
            # means.append(re.sub("（.*）", "", mean['content']['mean']))
    public_info.word_means = means


# extract options
def filler_option(public_info) -> list:
    """
    提取返回的选以及排序优化
    :param public_info:
    :return:
    """
    # exam options
    options = []
    source = []
    # filler option
    for option_info in public_info.exam["options"]:
        option = option_info['content']
        source.append(option)
        if option in public_info.word_list:
            options.insert(0, option)
        else:
            options.append(option)
    public_info.source_option = source
    return options


# match options
def select_mean(public_info) -> int:
    options = filler_option(public_info)
    # match option
    for index, option in enumerate(options, 0):
        for mean in public_info.word_means:
            # exam option content is disorder,re-order
            if sorted(option.replace(" ", '')) == sorted(mean.replace(" ", '')) or mean in option:
                select_module.logger.info(f"匹配选项{option}")
                return index
    # failed match 乱选一个0~3
    return 2


# select match word
def select_match_word(public_info, word_mean) -> int:
    options = filler_option(public_info)
    for word in options:
        # query word mean
        query_word(public_info, word)
        handle_query_word_mean(public_info)
        # is match word mean
        for mean in public_info.word_means:
            if sorted(word_mean.replace(" ", '')) == sorted(mean.replace(" ", '')):
                return public_info.source_option.index(word)
    select_module.logger.info("匹配失败,猜第3个选项")
    return 2


def is_word_exist(public_info, option) -> bool:
    """
    word是否存在word_list中
    :param public_info:
    :param option: word
    :return: None
    """
    if option in public_info.word_list:
        # word is exist word_list
        query_word(public_info, option)
        return True
    else:
        select_module.logger.info('转原型')
        revert_option = word_revert(option)
        if revert_option in public_info.word_list:
            query_word(public_info, revert_option)
            return True
    return False


# extract sentence word
def word_examples(public_info, options) -> str:
    """
    匹配单词例句中的单词,也就是例句中的单词
    :param public_info:
    :param options: words
    :return: word
    """
    exam_zh = public_info.exam['stem']['remark']
    for word in options:
        if is_word_exist(public_info, word):
            if public_info.word_query_result.get('means'):
                query_result = public_info.word_query_result['means']
                for means in query_result:
                    for examples in means['usages']:
                        for sentences in examples['examples']:
                            # match same mean
                            if sentences["sen_mean_cn"] == exam_zh:
                                # answer
                                return re.findall(r'{(.+?)}', sentences['sen_content'])[0]
            else:
                query_result = public_info.word_query_result['options']
                for contents in query_result:
                    for example in contents['content']['example']:
                        if example["sen_mean_cn"] == exam_zh:
                            # answer
                            return re.findall(r'{(.+?)}', example['sen_content'])[0]

    return ''
