import re
import unicodedata


def norm_text(text):
    """全角转半角、NBSP 转空格、压缩空白、转小写"""
    if text is None:
        return ''
    s = unicodedata.normalize('NFKC', str(text)).replace('\u00a0', ' ')
    return re.sub(r'\s+', ' ', s).strip().lower()


def norm_key(text):
    """在 norm_text 基础上去掉空白与标点, 用于答案/选项的宽松比较"""
    return re.sub(r'[\s\W_]+', '', norm_text(text))
