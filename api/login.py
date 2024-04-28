import json

import api.request_header as requests
from decryptencrypt.encrypt_md5 import encrypt_md5
from log.log import Log
from util.basic_util import create_timestamp

# basic url
basic_url = 'https://app.vocabgo.com/student/api/'
# log init
login = Log("login")


def get_token(public_info):
    # init requests header
    requests.set_token('null')
    code = public_info.code if public_info.code else exit('code不存在')
    url = 'Auth/Wechat/LoginByWechatCode'
    timestamp = create_timestamp()
    sign = encrypt_md5(
        f'timestamp={timestamp}&version=2.6.1.231204&wechat_code=041cUPFa1BKYCG0Lz0Ha1br9iG3cUPF8ajfajfamsnfaflfasakljdlalkflak')
    requests.rqs3_session.headers.update(
        {"Referer": f"https://app.vocabgo.com/student/?authorize=2&code={code}&state=STATE"})
    # success code
    # {"code":1,"msg":"success","data":{"auth_type":"UserToken","access":["student_or_teacher"],"token":"c8488f0d370a9097d3ee170260c56","subscribe":"1"},"jv":"0","cv":"0"}
    # fail code
    # {"code":0,"msg":"微信服务异常!","data":null,"jv":"0","cv":"0"}
    data = {"wechat_code": code, "timestamp": timestamp, "version": "2.6.1.231204",
            "sign": sign, "app_type": 1}
    rsp = requests.rqs3_session.post(basic_url + url, data=json.dumps(data)).json()
    rsp_data = rsp['data']
    if rsp_data:
        public_info._token = rsp_data['token']
        # update request header token
        requests.set_token(rsp_data['token'])
        login.logger.info(f"token获取成功{rsp_data['token']}")
    else:
        login.logger.info("code 已经被使用请重新抓取")
        exit('程序退出')


def verify_token(token):
    import main
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
