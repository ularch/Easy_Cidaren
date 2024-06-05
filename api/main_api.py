import json
import random
import time
from functools import wraps


import api.request_header as requests
from decryptencrypt.debase64 import debase64
from decryptencrypt.encrypt_md5 import encrypt_md5
from log.log import Log
from publicInfo.publicInfo import PublicInfo
from util.basic_util import create_timestamp
from  view.error import showError

# create logger
api = Log('api')

basic_url = 'https://app.vocabgo.com/student/api/Student/'


# response is 200
def handle_response(response):
    from PyQt6.QtWidgets import QApplication
    import sys

    response_json = response.json()
    code = response_json['code']
    # error_view.showUI()
    if code == 1:
        # 获取成功
        api.logger.info(f"请求成功{response.content}")
    # complete exam
    elif code == 20001 and response_json['data'] or code == 20004:
        pass
    elif code == 0 and response_json['msg'] == '加载单词卡片失败，请重新加载':
        api.logger.error("查找不到单词(第三方库转原型失败),请手动答题")
        showError()
        exit(-1)
    else:
        api.logger.info(f"请求有问题{response.text}退出程序", stack_info=True)
        showError()
        exit(-1)


def is_close() -> bool:
    url = 'https://gitee.com/hhhuuuu/cdr/access/add_access_log'
    rsp = requests.requests.get(url)
    if rsp.status_code == 200:
        return True
    else:
        return False


def skip_exam(public_info):
    """
    跳过过不了的题目
    :return:
    """
    api.logger.info("跳过题目")
    url = f'{PublicInfo.task_type}/SkipAnswer'
    params = {'it_font_size': 42,
              'it_img_w': 804,
              'opt_font_c': '#000000',
              'opt_font_size': 37,
              'opt_img_w': 684,
              'time_spent': 20000,
              'timestamp': create_timestamp(),
              'topic_code': public_info.topic_code,
              'version': '2.6.2.24031302'}
    sign = encrypt_md5("&".join([f'{key}={value}' for key, value in params.items()]) + 'ajfajfamsnfaflfasakljdlalkflak')
    params.update({'sign': sign})
    rsp = requests.rqs2_session.post(basic_url + url, data=json.dumps(params))
    # check response is success
    handle_response(rsp)
    # update exam
    if rsp.json()['msg'] == '任务已完成！' or rsp.json()['msg'] == '需要选词！':
        public_info.exam = 'complete'
    # decrypt response
    else:
        public_info.exam = debase64(rsp.json())


# select all word
def select_all_word(word_info, task_id: int, ) -> None:
    api.logger.info("勾选全部单词并提交")
    timestamp = create_timestamp()
    url = f'{PublicInfo.task_type}/SubmitChoseWord'
    # 取消键值对的空格(紧密排版)
    word_map = json.dumps(word_info, separators=(',', ':'))
    source_str = f'chose_err_item=2&task_id={task_id}&timestamp={timestamp}&version=2.6.1.231204&word_map={word_map}ajfajfamsnfaflfasakljdlalkflak'
    sign = encrypt_md5(source_str)
    data = {"task_id": task_id, "word_map": word_info, "chose_err_item": 2,
            "timestamp": timestamp, "version": "2.6.1.231204", "sign": sign,
            "app_type": 1}
    rsp = requests.rqs3_session.post(basic_url + url, data=json.dumps(data))
    # check request is success
    handle_response(rsp)


# class task
# 获取所有班级任务
def get_class_task(public_info, page_count: int):
    """
    :param public_info:
    :param page_count:  第几页的数据
    :return:
    """
    api.logger.info(f'获取第{page_count}页任务')
    url = 'ClassTask/PageTask'
    timestamp = create_timestamp()
    sign = f"page_count={page_count}&page_size=10&search_type=0&timestamp={timestamp}&version=2.6.1.240122ajfajfamsnfaflfasakljdlalkflak"
    data = {
        'search_type': '0',
        'page_count': page_count,
        'page_size': 10,
        'timestamp': timestamp,
        "version": "2.6.1.231204",
        "sign": encrypt_md5(sign),
        "app_type": 1
    }
    # "task_type": 2 是班级测试任务 1 是班级自学任务
    task = requests.class_task_request.post(url=basic_url + url, json=data)
    # check response is success
    handle_response(task)
    # 转换成字典
    task_dict = task.json()
    # sava public_info
    public_info.class_task.append(task_dict['data'])
    # number of task
    public_info.task_total_count = task_dict['data']['total']


# # start

def get_exam(public_info):
    api.logger.info("获取第一题")
    url = f'{PublicInfo.task_type}/StartAnswer'
    params = {'task_id': public_info.task_id or -1, 'task_type': PublicInfo.task_type_int,
              'opt_img_w': '684',
              'opt_font_size': '37', 'opt_font_c': '%23000000', 'it_img_w': '804', 'it_font_size': '42',
              'timestamp': create_timestamp(), 'version': '2.6.1.240122', 'app_type': '1'}
    if PublicInfo.task_type_int == 2:
        params.update({'release_id': public_info.release_id})
    else:
        params.update({'course_id': public_info.course_id})
    rsp = requests.class_task_request.get(url=basic_url + url, params=params)
    # check response is success
    handle_response(rsp)
    #  decrypt response
    public_info.exam = debase64(rsp.json())
    api.logger.info("写入成功")


# next exam
def next_exam(public_info):
    # 获取每一题提交的用时，500为一秒
    min_time = public_info.spend_min_time * 500
    max_time = public_info.spend_max_time * 500
    api.logger.info("获取下一题")
    url = f'{PublicInfo.task_type}/SubmitAnswerAndSave'
    params = {'it_font_size': 42,
              'it_img_w': 804,
              'opt_font_c': '#000000',
              'opt_font_size': 37,
              'opt_img_w': 684,
              'time_spent': random.randint(min_time, max_time),
              'timestamp': create_timestamp(),
              'topic_code': public_info.topic_code,
              'version': '2.6.2.24031302'}
    sign = encrypt_md5("&".join([f'{key}={value}' for key, value in params.items()]) + 'ajfajfamsnfaflfasakljdlalkflak')
    params.update({'sign': sign})
    data = requests.rqs2_session.post(basic_url + url, data=json.dumps(params))
    # 检查请求是否成功
    handle_response(data)
    if data.json()['msg'] == '任务已完成！' or data.json()['msg'] == '需要选词！':
        public_info.exam = 'complete'
    # decrypt response
    else:
        public_info.exam = debase64(data.json())


def check_is_self_built(func):
    @wraps(func)
    def is_self_built(public_info, word):
        if public_info.is_self_built:
            # 从单词列表获取索引
            word_index = public_info.word_list.index(word)
            # 获取单元单词
            public_info.now_unit = public_info.get_book_words_data[word_index]["list_id"]
        return func(public_info, word)

    return is_self_built


# query word
@check_is_self_built
def query_word(public_info, word):
    time.sleep(random.randint(0, 2))
    api.logger.info(f"查询单词{word}")
    # query word in the unit
    url = f'Course/StudyWordInfo?course_id={public_info.course_id}&list_id={public_info.now_unit}&word={word}&timestamp={create_timestamp()}&version=2.6.1.231204&app_type=1'
    word = requests.rqs_session.get(basic_url + url)
    # 检查请求是否成功
    handle_response(word)
    # decrypt  response
    public_info.word_query_result = debase64(word.json())
    api.logger.info("查询单词成功")


# submit word
def submit_result(public_info, option):
    api.logger.info("开始提交答案")
    timestamp = create_timestamp()
    topic_code = public_info.topic_code
    sign = encrypt_md5(
        f"answer={option}&timestamp={timestamp}&topic_code={topic_code}&version=2.6.1.231204ajfajfamsnfaflfasakljdlalkflak")
    url = f"{PublicInfo.task_type}/VerifyAnswer"
    data = {"answer": option,
            "topic_code": topic_code,
            "timestamp": timestamp, "version": "2.6.1.231204", "sign": sign,
            "app_type": 1}
    rsp = requests.rqs2_session.post(basic_url + url, data=json.dumps(data))
    # check request is success
    handle_response(rsp)
    api.logger.info("提取下一题的请求参数")
    # next exam topic_code
    public_info.topic_code = debase64(rsp.json())['topic_code']


if __name__ == '__main__':
    pass
