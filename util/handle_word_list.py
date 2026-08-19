from decryptencrypt.debase64 import debase64
import json
import os


def handle_word_result(public_info) -> None:
    word_list = []
    word_dict = {}
    try:
        for word in public_info.get_word_list_result['data']['word_list']:
            word_list.append(word['word'])
            word_dict[word['word_zh']] = word['word']
    except:
        for word in debase64(public_info.get_word_list_result['data'], public_info.get_word_list_result['jv'])['word_list']:
            word_list.append(word['word'])
            word_dict[word['word_zh']] = word['word']
    # 当前单元词表覆盖 word_list(判词依赖当前单元)
    public_info.word_list = word_list
    # word_dict 跨单元合并(全局词表池: mode 73 前缀单词可能在其他单元词表)
    if not isinstance(getattr(public_info, 'word_dict', None), dict):
        public_info.word_dict = {}
    public_info.word_dict.update(word_dict)
    # 持久化(跨进程累积: 单任务/不同刷题顺序下全局池完整); 词表池自学习关闭时不写入
    if getattr(public_info, '_self_learn_pool', True):
        try:
            with open(os.path.join(public_info.path, "config", "word_pool.json"), 'w', encoding='utf-8') as f:
                json.dump(public_info.word_dict, f, ensure_ascii=False)
        except Exception:
            pass
