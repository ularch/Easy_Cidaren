import json
import os
import threading

from log.log import Log

answer_lib_logger = Log('answer_lib')

LIB_FILE = 'answer_lib.json'
_lock = threading.Lock()
_lib = None


def _lib_path():
    return os.path.join(os.getcwd(), 'config', LIB_FILE)


def load_lib(force=False):
    global _lib
    if _lib is None or force:
        path = _lib_path()
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    _lib = json.load(f)
            except Exception as e:
                answer_lib_logger.error(f"加载答案库失败: {e}")
                _lib = {}
        else:
            _lib = {}
    return _lib


def lookup(word_zh):
    if not word_zh:
        return None
    answers = load_lib().get(word_zh)
    if not answers:
        return None
    return answers if isinstance(answers, list) else [answers]


WORD_KEY = '_word_answers'


def lookup_word(word_zh):
    """单词级答案(mode 42 选项单词/同义变体), 与短语答案分开存储"""
    if not word_zh:
        return None
    answers = load_lib().get(WORD_KEY, {}).get(word_zh)
    if not answers:
        return None
    return answers if isinstance(answers, list) else [answers]


def add_word_answer(word_zh, words):
    if not word_zh or not words:
        return
    word_answers = [w for w in words if isinstance(w, str) and w]
    if not word_answers:
        return
    with _lock:
        lib = load_lib()
        word_map = lib.get(WORD_KEY, {})
        if not isinstance(word_map, dict):
            word_map = {}
        old = word_map.get(word_zh, [])
        if not isinstance(old, list):
            old = [old]
        added = False
        for w in word_answers:
            if w not in old:
                old.append(w)
                added = True
        if added:
            word_map[word_zh] = old
            lib[WORD_KEY] = word_map
        else:
            return
        try:
            with open(_lib_path(), 'w', encoding='utf-8') as f:
                json.dump(lib, f, ensure_ascii=False, indent=2)
        except Exception as e:
            answer_lib_logger.error(f"保存答案库失败: {e}")


def add_answer(word_zh, corrects):
    if not word_zh or not corrects:
        return
    answers = [c for c in corrects if isinstance(c, str) and c]
    if not answers:
        return
    with _lock:
        lib = load_lib()
        old = lib.get(word_zh, [])
        if not isinstance(old, list):
            old = [old]
        added = False
        for a in answers:
            if a not in old:
                old.append(a)
                added = True
        if not added:
            return
        lib[word_zh] = old
        try:
            with open(_lib_path(), 'w', encoding='utf-8') as f:
                json.dump(lib, f, ensure_ascii=False, indent=2)
        except Exception as e:
            answer_lib_logger.error(f"保存答案库失败: {e}")
