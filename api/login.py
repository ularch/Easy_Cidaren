import json

import api.request_header as requests
from decryptencrypt.encrypt_md5 import encrypt_md5
from log.log import Log
from util.basic_util import create_timestamp

# 基础url
basic_url = 'https://app.vocabgo.com/student/api/'
# 初始化log
login = Log("login")


def verify_token(token):
    # 初始化所有请求头
    requests.set_token(token)
    timestamp = create_timestamp()
    url = f'Student/Main?timestamp={timestamp}&version=2.6.1.231204&app_type=1'
    result = requests.rqs_session.get(basic_url + url).json()
    # 判断是否过期 code = 1 为未过期
    if result['code'] != 1:
        login.logger.info("token已过期")
        return 0
    else:
        return result
