import base64
import binascii
import json
import re
from log.log import Log

bs64 = Log("base64")


def debase64(data: dict or str):
    """
    base64解码
    :param data:
    :return:
    """
    if type(data) is dict:
        data = data["data"]

    bs64.logger.info(f"开始解码{data}")
    try:
        bs64_str = base64.b64decode(data.encode("utf-8")).decode("utf-8")
    except:
        # 英译汉 插入乱码
        char_list = list(data)
        # indices_to_remove = [0, 1, 2, 4, 5, 36, 47, 48, 59, 96, 107] #上一次的混淆
        indices_to_remove = [0, 1, 2, 4, 5, 6, 7, 48, 49, 66, 149, 150, 284, 374, 375]

        for index in sorted(indices_to_remove, reverse=True):
            if 0 <= index < len(char_list):
                del char_list[index]
        new_data = ''.join(char_list)
        bs64_str = base64.b64decode(new_data.encode("utf-8")).decode("utf-8", errors='ignore')
    # 正则小概率还是会报错,bs64解出来前面会乱码
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
        "EZeJ2uxyJ3b3JkIjoiZG9taW5hdGUiLCJ0b3BpY19jb2RlIoLjoibEZoNWRveHNtTEmlUVmx5SGVIdUxiSmV2WkplU2FsbGlXcHFvbzU3VHhhcVpnNDlxYVdPYmJXdGlqR3FWWmIyK1lHR1JabUp4NvYjI1cmEzR2FhV2hzYjI1cllwREFscE9SalpSbGFXZVRaVzlzWjJsd2NadU5abHlXYUc5dmNIQnNZbWlPYW1obmEydHRiR2Fha0dsbWs1eHZiV3FPYVpNPSIsIm92ZXJfc3RhtdHVzIjoxLCJhbnN3ZXJfcmVzdWx0IjoxLCJjbGVhbl9zdGF0dXMiOjIsImFuc3dlcl9jb3JyZWN0cyI6WzJdfQ=="
    )
