import requests
import json

from log.log import Log

response = requests.get("https://api.github.com/repos/ularch/Cidaren_Automatic_Answer/releases/latest")

update = Log("update")


def get_update() -> str:
    if response.status_code == 200:
        data = json.loads(response.text)
        return data["tag_name"]
    else:
        update.logger.info("获取更新失败")
        return "null"


def get_update_detail() -> str:
    if response.status_code == 200:
        data = json.loads(response.text)
        return data["body"]
    else:
        update.logger.info("获取更新内容失败")
        return "null"
