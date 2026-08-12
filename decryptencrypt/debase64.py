import base64
import json
import re
from log.log import Log, get_file_logger

bs64 = Log("base64")
file_logger = get_file_logger('_base64')

JV_TWO = {
    '2_1254':  [0, 1, 2, 4, 5, 36, 47, 48, 59, 96, 107],
    '2_9214':  [0, 1, 2, 4, 5, 6, 7, 48, 49, 66, 149, 150, 284, 374, 375],
    '2_10232': [0, 1, 2, 5, 6, 7, 8, 46, 65, 66, 199, 270, 328, 329],
    '2_10234': [0, 1, 2, 4, 5, 6, 7, 46, 65, 66, 198, 270, 328, 329],
}

JV_THREE = {
    '3_1021': {
        "uc": [{"s": 0, "n": 1}, {"s": 1, "n": 2}, {"s": 33, "n": 1}, {"s": 57, "n": 1}, {"s": 111, "n": 1}],
        "avg": 5, "loc": [1, 3, 2, 0, 4]
    },
    '3_2265': {
        "uc": [{"s": 0, "n": 2}, {"s": 1, "n": 3}, {"s": 33, "n": 1}, {"s": 57, "n": 1}, {"s": 121, "n": 1}],
        "avg": 5, "loc": [3, 1, 0, 4, 2]
    },
    '3_2277': {
        "uc": [{"s": 0, "n": 3}, {"s": 1, "n": 3}, {"s": 32, "n": 2}, {"s": 50, "n": 1}, {"s": 110, "n": 1}],
        "avg": 5, "loc": [3, 1, 0, 4, 2]
    },
}

DEFAULT_JV_TWO = JV_TWO['2_9214']


def strip_noise(d: str, rules) -> str:
    """
    去除混淆
    :param d: 待去除的乱码数据
    :param rules: 乱码规则
    :return:
    """
    if rules and isinstance(rules[0], int):
        chars = list(d)
        for i in sorted(rules, reverse=True):
            if 0 <= i < len(chars):
                del chars[i]
        return ''.join(chars)
    for r in rules:
        s, n = r["s"], r["n"]
        d = (d[:s] if s else "") + d[s + n:]
    return d


def debase64(data: dict or str, jv: str = 0):
    """
    base64解码
    :param data: 待解码的数据
    :param jv: 乱码版本标识，默认为0
    :return:
    """
    if type(data) is dict:
        data = data["data"]

    file_logger.info(f"开始解码jv:{jv},{data}")
    try:
        bs64_str = base64.b64decode(data.encode("utf-8")).decode("utf-8")
    except:
        if jv.startswith("2_") and jv in JV_TWO:
            clean_data = strip_noise(data, JV_TWO[jv])
        elif jv.startswith("3_") and jv in JV_THREE:
            cfg = JV_THREE[jv]
            d = strip_noise(data, cfg["uc"])
            chunk = len(d) // cfg["avg"]
            pieces = [d[i*chunk:(i+1)*chunk] for i in range(cfg["avg"])]
            out = "".join(pieces[cfg["loc"].index(i)] for i in range(cfg["avg"]))
            if len(d) % chunk:
                out += d[cfg["avg"]*chunk:]
            clean_data = out
        else:
            clean_data = strip_noise(data, DEFAULT_JV_TWO)

        file_logger.info(f"去除混淆后：{clean_data}")
        bs64_str = base64.b64decode(clean_data.encode("utf-8")).decode("utf-8", errors='ignore')
    result = re.findall("{\".*", bs64_str)[0]
    try:
        json.loads(result)
        bs64.logger.info(f"解码成功{result}")
        return json.loads(result)
    except:
        if result.startswith('{'):
            result = result[1:]
            result = re.findall("{\".*", result)[0]
            try:
                json.loads(result)
                bs64.logger.info(f"解码成功{result}")
                return json.loads(result)
            except:
                bs64.logger.error("解码失败！")
                raise
        else:
            bs64.logger.error("解码失败！")
            raise


if __name__ == '__main__':
    debase64(
        "E7ke9IyJ0YXNrX2lkIjoxNDM4ODgwNDMsInRChc2tfdHlwZgKSI6MSwiY2961cnNlX2lkIjoiSkpfMyIsInRhc2tfbmFtZSI06IuiHquW7uwuS7u+WKoSIsIndvcmRfbGlzdCI6W3sicHJvZ3Jlc3MiOjMwLCJzY29yZSI6MS4wLCJ0aW1lX3NwZW50IjoxMzE4Mywic3RhdHVzIjoxLCJjb3Vyc2VfaWQiOiJKSl8zIiwibGlzdF9pZCI6IkpKXzNfMV8wIiwid29yZCI6ImNyYXNoIiwid29yZF90eXBlIjoxLCJ3b3JkX3poIjoiIiwid29yZF9hdWRpbyI6IiJ9LHsicHJvZ3Jlc3MiOjUwLCJzY29yZSI6NS4wLCJ0aW1lX3NwZW50IjoxMzQzOSwic3RhdHVzIjoxLCJjb3Vyc2VfaWQiOiJKSl8zIiwibGlzdF9pZCI6IkpKXzNfMV8wIiwid29yZCI6InNpZ2h0c2VlaW5nIiwid29yZF90eXBlIjoxLCJ3b3JkX3poIjoiIiwid29yZF9hdWRpbyI6IiJ9LHsicHJvZ3Jlc3MiOjI1LCJzY29yZSI6MS4yLCJ0aW1lX3NwZW50Ijo3NTIyLCJzdGF0dXMiOjEsImNvdXJzZV9pZCI6IkpKXzMiLCJsaXN0X2lkIjoiSkpfM18xXzAiLCJ3b3JkIjoiZW1wbG95bWVudCIsIndvcmRfdHlwZSI6MSwid29yZF96aCI6IiIsIndvcmRfYXVkaW8iOiIifSx7InByb2dyZXNzIjo1MCwic2NvcmUiOjUuMCwidGltZV9zcGVudCI6MTAyODEsInN0YXR1cyI6MSwiY291cnNlX2lkIjoiSkpfMyIsImxpc3RfaWQiOiJKSl8zXzFfMCIsIndvcmQiOiJjbHVlIiwid29yZF90eXBlIjoxLCJ3b3JkX3poIjoiIiwid29yZF9hdWRpbyI6IiJ9LHsicHJvZ3Jlc3MiOjUwLCJzY29yZSI6NS4wLCJ0aW1lX3NwZW50Ijo5ODczLCJzdGF0dXMiOjEsImNvdXJzZV9pZCI6IkpKXzMiLCJsaXN0X2lkIjoiSkpfM18xXzAiLCJ3b3JkIjoiem9uZSIsIndvcmRfdHlwZSI6MSwid29yZF96aCI6IiIsIndvcmRfYXVkaW8iOiIifSx7InByb2dyZXNzIjo1NSwic2NvcmUiOjQuNCwidGltZV9zcGVudCI6Mjg3ODcsInN0YXR1cyI6MSwiY291cnNlX2lkIjoiSkpfMyIsImxpc3RfaWQiOiJKSl8zXzFfMCIsIndvcmQiOiJlbWJyYWNlIiwid29yZF90eXBlIjoxLCJ3b3JkX3poIjoiIiwid29yZF9hdWRpbyI6IiJ9LHsicHJvZ3Jlc3MiOjUwLCJzY29yZSI6Mi41LCJ0aW1lX3NwZW50IjoxOTI4MCwic3RhdHVzIjoxLCJjb3Vyc2VfaWQiOiJKSl8zIiwibGlzdF9pZCI6IkpKXzNfMV8wIiwid29yZCI6InNvbG8iLCJ3b3JkX3R5cGUiOjEsIndvcmRfemgiOiIiLCJ3b3JkX2F1ZGlvIjoiIn0seyJwcm9ncmVzcyI6NjYsInNjb3JlIjo2LjYsInRpbWVfc3BlbnQiOjg4OTIsInN0YXR1cyI6MSwiY291cnNlX2lkIjoiSkpfMyIsImxpc3RfaWQiOiJKSl8zXzFfMCIsIndvcmQiOiJibG9nIiwid29yZF90eXBlIjoxLCJ3b3JkX3poIjoiIiwid29yZF9hdWRpbyI6IiJ9XSwiZ3JhZGUiOjMsImdyYWRlX2luZm9fbGlzdCI6W3sidmFsdWUiOjEsInRleHQiOiLlv6vpgJ/mqKHlvI8iLCJ0b3BpY19tb2RlX251bSI6MywiYmFzZV90aW1lIjoyNiwidGltZSI6MjA4LCJyZW1hcmsiOiLljIXlkKvvvJoxLOWNleivjeWxleekujsgMiznnIvlj6XpgInkuYk7IDMs5ZCs6Z+z6YCJ5LmJOyAifSx7InZhbHVlIjoyLCJ0ZXh0Ijoi5pmu6YCa5qih5byPIiwidG9waWNfbW9kZV9udW0iOjUsImJhc2VfdGltZSI6NzYsInRpbWUiOjYwOCwicmVtYXJrIjoi5YyF5ZCr77yaMSzljZXor43lsZXnpLo7IDIs55yL5Y+l6YCJ5LmJOyAzLOWQrOmfs+mAieS5iTsgNCzlhbPogZTmkK3phY07IDUs6YCJ6K+N5pCt6YWNOyAifSx7InZhbHVlIjozLCJ0ZXh0Ijoi5a6M5pW05qih5byPIiwidG9waWNfbW9kZV9udW0iOjYsImJhc2VfdGltZSI6OTYsInRpbWUiOjc2OCwicmVtYXJrIjoi5YyF5ZCr77yaMSzljZXor43lsZXnpLo7IDIs55yL5Y+l6YCJ5LmJOyAzLOWQrOmfs+mAieS5iTsgNCzlhbPogZTmkK3phY07IDUs6YCJ6K+N5pCt6YWNOyA2LOeci+S5ieWGmeivjTsgIn1dLCJzY29yZSI6MzguMywicHJvZ3Jlc3MiOjQ3LCJ0aW1lX3NwZW50IjoxMTEyNTcsImF1ZGlvX2FkZHIiOiJodHRwczovL3Jlc291cmNlLWNkbi52b2NhYmdvLmNvbSIsImV4aXN0X2xpdHRsZV90YXNrIjoyfQ=="
        , "2_1254")