"""
词形还原
"""

# 屈折后缀规则：从词表里的原形出发，枚举它可能出现的表面词形
_SUFFIX_RULES = ('s', 'es', 'd', 'ed', 'ing', 'ings', 'er', 'est', 'ly')


def _inflections(base: str) -> set:
    """枚举 base 可能的屈折形式。"""
    forms = {base}
    for suffix in _SUFFIX_RULES:
        forms.add(base + suffix)
    if base.endswith('y'):
        stem = base[:-1]
        forms.update({stem + 'ies', stem + 'ied', stem + 'ier', stem + 'iest', stem + 'ily'})
    if base.endswith('e'):
        stem = base[:-1]
        forms.update({stem + 'ed', stem + 'ing', stem + 'es', stem + 'er', stem + 'est'})
    if len(base) > 2 and base[-1] not in 'aeiou':
        # 双写辅音: stop -> stopped / stopping
        forms.update({base + base[-1] + s for s in ('ed', 'ing', 'er', 'est')})
    return forms


def match_in_list(surface: str, word_list) -> str or None:
    """把表面词形还原成 word_list 中真实存在的词。
    :param surface: 题干里出现的词
    :param word_list: 本单元词表
    :return: word_list中的词，无法还原返回 None
    """
    if not surface or not word_list:
        return None
    target = surface.strip().strip('*').lower()
    if not target:
        return None
    table = {}
    for word in word_list:
        if word:
            table.setdefault(word.lower(), word)
    if target in table:
        return table[target]
    for base, original in table.items():
        if target in _inflections(base):
            return original
    return None
