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


# response is 200
def handle_response(response):
    if response.json()['code'] == 1:
        basic_api.logger.info(f"请求成功{response.content}")
    else:
        basic_api.logger.info(f"请求有问题{response.text}退出程序")
        exit(-1)


# 使用spacy获取单词原型
def get_prototype(word: str) -> str:
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


def get_all_unit(public_info):
    timestamp = create_timestamp()
    url = f'StudyTask/List?course_id={public_info.course_id}&timestamp={timestamp}&version=2.6.1.231204&app_type=1'
    user_data = requests.rqs_session.get(basic_url + url)
    # check response is success
    handle_response(user_data)
    public_info.all_unit = user_data.json()['data']


def get_unit_words(public_info):
    timestamp = create_timestamp()
    url_params = {'task_id': public_info.task_id or -1, "course_id": public_info.course_id, 'timestamp': timestamp,
                  'version': '2.6.1.240305', 'app_type': '1'}
    if public_info.is_self_built:
        url_params.update({'release_id': public_info.release_id})
    else:
        url_params.update({'list_id': public_info.now_unit})
    rsp = requests.rqs_session.get(basic_url + 'StudyTask/Info', params=url_params)
    # check request is success
    handle_response(rsp)
    rsp_json = rsp.json()
    public_info.get_word_list_result = rsp_json


def get_book_all_words(public_info):
    basic_api.logger.info('获取该本书的所有单词')
    url = f'https://resource.vocabgo.com/Resource/CoursePage/{public_info.course_id}.json'
    rsp = requests.rsq_self_built.get(url)
    # all the words in the book
    public_info.get_book_words_data = rsp.json()
