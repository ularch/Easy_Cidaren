import requests


def zh_en(public_info, zh: str) -> None:
    """
    走谷歌中译英
    :param public_info:
    :param zh:
    :return:
    """
    rsp = requests.get(
        f'https://translate.googleapis.com/translate_a/single?client=gtx&dt=t&sl=zh-CN&tl=en&q={zh}').json()
    print(f"{rsp[0][0][0]}")
    # public_info.zh_en = rsp[0][0][0]


if __name__ == '__main__':
    zh_en('aa', '测试案例')
