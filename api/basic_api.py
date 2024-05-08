import json
import re
import spacy
import time

import api.request_header as requests
from log.log import Log
from util.basic_util import create_timestamp

# init log
basic_api = Log("basic_api")
basic_url = 'https://app.vocabgo.com/student/api/Student/'


def handle_response(response):
    """
    判断请求是否成功
    response is 200
    """
    if response.json()['code'] == 1:
        basic_api.logger.info(f"请求成功{response.content}")
    else:
        basic_api.logger.info(f"请求有问题{response.text}退出程序")
        exit(-1)


def get_prototype(word: str) -> str:
    """
    获取单词原型，这个方法相当于是备选
    :param word: 目标单词
    :return: 单词原型
    """
    nlp = spacy.load('en_core_web_sm')
    prototype = nlp(word)[0].lemma_
    basic_api.logger.info(f"单词{word}转原型为{prototype}")
    return prototype


def get_select_course(public_info):
    url = 'Main?timestamp=1704182548197&version=2.6.1.231204&app_type=1'
    rsp = requests.rqs_session.get(basic_url + url)
    # check request is success
    handle_response(rsp)
    # course id
    public_info.course_id = rsp.json()['data']['user_info']['course_id']


# 获取课程所有单元
def get_all_unit(public_info):
    timestamp = create_timestamp()
    url = f'StudyTask/List?course_id={public_info.course_id}&timestamp={timestamp}&version=2.6.1.231204&app_type=1'
    user_data = requests.rqs_session.get(basic_url + url)
    # 检查请求是否成功
    handle_response(user_data)
    public_info.all_unit = user_data.json()['data']


# 获取单元所有单词
def get_unit_words(public_info):
    timestamp = create_timestamp()
    url_params = {'task_id': public_info.task_id or -1, "course_id": public_info.course_id, 'timestamp': timestamp,
                  'version': '2.6.1.240305', 'app_type': '1'}
    if public_info.is_self_built:
        # 自建任务
        url_params.update({'release_id': public_info.release_id})
    else:
        # 测试任务
        url_params.update({'list_id': public_info.now_unit})
    word_data = requests.rqs_session.get(basic_url + 'StudyTask/Info', params=url_params)
    # 检查请求是否成功
    handle_response(word_data)
    word_data_json = word_data.json()
    public_info.get_word_list_result = word_data_json


def get_book_all_words(public_info):
    basic_api.logger.info('获取该本书的所有单词')
    url = f'https://resource.vocabgo.com/Resource/CoursePage/{public_info.course_id}.json'
    rsp = requests.rsq_self_built.get(url)
    # all the words in the book
    public_info.get_book_words_data = rsp.json()
