import requests
import json

from log.log import Log

update = Log("update")


def get_update() -> str:
    try:
        response = requests.get("https://api.github.com/repos/ularch/Cidaren_Automatic_Answer/releases/latest")
        if response.status_code == 200:
            data = json.loads(response.text)
            return data["tag_name"]
        else:
            update.logger.error("获取更新失败")
            return '0'
    except:
        update.logger.error("获取更新失败")
        return '0'


def get_update_detail() -> str:
    try:
        response = requests.get("https://api.github.com/repos/ularch/Easy_Cidaren/releases/latest")
        if response.status_code == 200:
            data = json.loads(response.text)
            return data["body"]
        else:
            update.logger.error("获取更新内容失败")
            return 'null'
    except:
        update.logger.error("获取更新内容失败")
        return 'null'
