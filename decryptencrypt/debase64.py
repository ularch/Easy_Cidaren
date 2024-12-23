import base64
import binascii
import json
import re


def debase64(data: dict or str):
    """
    base64解码
    :param data:
    :return:
    """
    data = data["data"]
    try:
        bs64_str = base64.b64decode(data.encode("utf-8")).decode("utf-8", errors='ignore')
    except binascii.Error as e:
        # 英译汉 插入乱码
        char_list = list(data)
        indices_to_remove = [0, 1, 2, 4, 5, 36, 47, 48, 59, 96, 107]
        for index in sorted(indices_to_remove, reverse=True):
            if 0 <= index < len(char_list):
                del char_list[index]
        new_data = ''.join(char_list)
        bs64_str = base64.b64decode(new_data.encode("utf-8")).decode("utf-8", errors='ignore')
    # 正则小概率还是会报错,bs64解出来前面会乱码
    return json.loads(re.findall("{\".*", bs64_str)[0])


if __name__ == '__main__':
    print(debase64(
        "IUnsaHMPi61aUocCrfw16gE7IiRezjE9eyJ0YXNrX2lkIjo5ODM4ODc1OSwidGFza190eXBlIjoyLCJ0b3BpY19tb2RlIjoxNywic3RlbSI6eyJjb250ZW50IjoidmVyYiAg5byV6LW377yb5Lqn55SfIiwicmVtYXJrIjpudWxsLCJwaF91c191cmwiOm51bGwsInBoX2VuX3VybCI6bnVsbCwiYXVfYWRkciI6bnVsbH0sIm9wdGlvbnMiOlt7ImNvbnRlbnQiOiJjb25zaXN0IiwicmVtYXJrIjpudWxsLCJhbnN3ZXIiOm51bGwsImFuc3dlcl90YWciOjAsImNoZWNrX2NvZGUiOm51bGwsInN1Yl9vcHRpb25zIjpudWxsLCJwaF9pbmZvIjpudWxsfSx7ImNvbnRlbnQiOiJnZW5lcmF0ZSIsInJlbWFyayI6bnVsbCwiYW5zd2VyIjpudWxsLCJhbnN3ZXJfdGFnIjoxLCJjaGVja19jb2RlIjpudWxsLCJzdWJfb3B0aW9ucyI6bnVsbCwicGhfaW5mbyI6bnVsbH0seyJjb250ZW50IjoiaW5xdWlyZSIsInJlbWFyayI6bnVsbCwiYW5zd2VyIjpudWxsLCJhbnN3ZXJfdGFnIjoyLCJjaGVja19jb2RlIjpudWxsLCJzdWJfb3B0aW9ucyI6bnVsbCwicGhfaW5mbyI6bnVsbH0seyJjb250ZW50IjoibG9jYXRlIiwicmVtYXJrIjpudWxsLCJhbnN3ZXIiOm51bGwsImFuc3dlcl90YWciOjMsImNoZWNrX2NvZGUiOm51bGwsInN1Yl9vcHRpb25zIjpudWxsLCJwaF9pbmZvIjpudWxsfV0sInNvdW5kX21hcmsiOiIiLCJwaF9lbiI6IiIsInBoX3VzIjoiIiwiYW5zd2VyX251bSI6MSwiY2hhbmNlX251bSI6MSwidG9waWNfZG9uZV9udW0iOjUsInRvcGljX3RvdGFsIjo0NCwid19sZW5zIjpbXSwid19sZW4iOjAsIndfdGlwIjoiIiwidGlwcyI6IiIsIndvcmRfdHlwZSI6MSwiZW5hYmxlX2kiOjIsImVuYWJsZV9pX2kiOjIsImVuYWJsZV9pX28iOjIsInRvcGljX2NvZGUiOiJrMU9EZkpWblY0NkRmbnJFWjVWb2wyaGJYbHJKbmFXYnFwZXRtMWVSbFcxZ2twbHZZSktUbFYyVWoySm1ZWk9OWldlV1oyWnBiR2xyWW1pWmEyT1JsV0p1WW1tWmtHNWxtcFZ2YVd5T2FsMXlhbWx0YlptV2JWeVdhVzVwYW10eFltK09hbWx0YUd4dmFtR1Z3UT09IiwiYW5zd2VyX3N0YXRlIjoxfQ=="))
