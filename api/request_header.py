import requests

from decryptencrypt.encrypt_md5 import encrypt_md5

Token = ''
user_age = 'Mozilla/5.0 (Linux; Android 8.1.2; LIO-AN00 Build/LIO-AN00; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/92.0.4515.131 Safari/537.36 MMWEBID/4462 MicroMessenger/8.0.20.2100(0x28001438) Process/toolsmp WeChat/arm64 Weixin Android Tablet NetType/WIFI Language/zh_CN ABI/arm64'
headers = {"Host": "app.vocabgo.com",
           "Accept": "application/json, text/plain, */*",
           "Abc": encrypt_md5(user_age),
           "Authorization-V": "cfcd208495d565ef66e7dff9f98764da",
           "X-Requested-With": "XMLHttpRequest",
           "User-Agent": user_age,
           "Accept-Language": "*",
           "Sec-Fetch-Site": "same-origin",
           "Sec-Fetch-Mode": "cors",
           "Sec-Fetch-Dest": "empty",
           "Referer": "https://app.vocabgo.com/student/",
           "Accept-Encoding": "gzip, deflate, br"
           }

rqs_session = rqs2_session = rqs3_session = class_task_request = rsq_self_built = ''


def set_token(token):
    # update global value
    global Token
    Token = token
    global rqs_session, rqs2_session, rqs3_session, class_task_request, rsq_self_built
    requests.DEFAULT_RETRIES = 5
    rqs_session = requests.session()
    rqs_session.headers = headers
    rqs_session.headers.update({'Usertoken': Token})
    # submit request header
    rqs2_session = requests.session()
    rqs2_session.keep_alive = False
    rqs2_session.headers = headers.copy()
    rqs2_session.headers.update(
        {"Authorization-V": "c4ca4238a0b923820dcc509a6f75849b", 'Usertoken': Token, "Origin": "https://app.vocabgo.com",
         "Content-Type": "application/json", "Content-Length": "393"})
    rqs3_session = requests.session()
    rqs3_session.headers = headers.copy()
    rqs3_session.headers.update({"Origin": "https://app.vocabgo.com", 'Usertoken': Token,
                                 "Content-Type": "application/json", "Content-Length": "460"})
    class_task_request = requests.session()
    class_task_request.headers = headers
    # self_built request
    rsq_self_built = requests.session()
    rsq_self_built.headers = headers.copy()
    rsq_self_built.headers.update(
        {"Origin": "https://app.vocabgo.com", "Referer": "https://app.vocabgo.com", "Host": 'resource.vocabgo.com',
         "X-Requested-With": 'com.tencent.mm'})
    rsq_self_built.headers.pop('Authorization-V')
    rsq_self_built.headers.pop('Abc')
