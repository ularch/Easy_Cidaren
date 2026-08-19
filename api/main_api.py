import json
import random
import time
from functools import wraps

import api.request_header as requests
from decryptencrypt.debase64 import debase64, JV_TWO, JV_THREE
from decryptencrypt.encrypt_md5 import encrypt_md5
from log.log import Log, get_file_logger
from publicInfo.publicInfo import PublicInfo
from util.answer_lib import add_answer, add_word_answer
from util.basic_util import create_timestamp

# create logger
api = Log('main_api')

basic_url = 'https://app.vocabgo.com/student/api/Student/'

file_logger = get_file_logger('_main_api')


class SecurityVerifyError(Exception):
    """服务端风控: 11003 需安全验证(要求用户在 App/微信端完成验证), 重试无意义, 应立即停止并提示"""


# response is 200
def handle_response(response):
    """
    检查response
    :param response:
    :return:
    """
    response_json = response.json()
    code = response_json['code']
    # error_view.showUI()
    if code == 11003:
        api.logger.error(f"需安全验证: {response.text}")
        raise SecurityVerifyError("服务端需安全验证，请打开词达人 App/微信完成安全验证后重试")
    if code == 1:
        # 获取成功
        api.logger.info(f"请求成功{response.text}")
    # complete exam
    elif code == 20001 and response_json['data'] or code == 20004:
        pass
    elif code == 0 and response_json['msg'] == '加载单词卡片失败，请重新加载':
        api.logger.error("查找不到单词(第三方库转原型失败),请手动答题")
        raise Exception("查找不到单词,请手动答题")
    else:
        api.logger.error(f"请求有问题{response.text}")
        raise Exception("请求有问题，中止程序")


def check_jv_and_retry_post(request_func, url, **kwargs):
    """
    检查post请求的jv
    :param request_func:
    :param url:
    :param kwargs:
    :return:
    """
    for _ in range(5):
        response = request_func(url, **kwargs)
        try:
            response_json = response.json()
            jv = str(response_json.get('jv', ''))
            if not jv or jv == '0' or jv in JV_TWO or jv in JV_THREE:
                return response
        except Exception:
            return response
        time.sleep(random.uniform(2, 3))
    api.logger.error("连续5次请求jv均不在已知范围内")
    raise Exception("jv解码失败")


def check_jv_and_retry_get(request_func, url, **kwargs):
    """
    检查get请求的jv
    :param request_func:
    :param url:
    :param kwargs:
    :return:
    """
    for _ in range(5):
        response = request_func(url, **kwargs)
        try:
            response_json = response.json()
            jv = str(response_json.get('jv', ''))
            if not jv or jv == '0' or jv in JV_TWO or jv in JV_THREE:
                return response
        except Exception:
            return response
        time.sleep(random.uniform(2, 3))
    api.logger.error("连续5次请求jv均不在已知范围内")
    raise Exception("jv解码失败")


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
    api.logger.info("无法完成，跳过题目")
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
    rsp = check_jv_and_retry_post(requests.rqs2_session.post, basic_url + url, data=json.dumps(params))
    # check response is success
    handle_response(rsp)
    # 检查jv
    # update exam
    if rsp.json()['msg'] == '任务已完成！' or rsp.json()['msg'] == '需要选词！':
        public_info.exam = 'complete'
    # decrypt response
    else:
        public_info.exam = debase64(rsp.json()['data'], rsp.json()['jv'])


# 勾选所有单词 bug
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
    rsp = check_jv_and_retry_post(requests.rqs3_session.post, basic_url + url, data=json.dumps(data))
    # 检查请求是否成功
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


# start

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
    rsp = check_jv_and_retry_get(requests.class_task_request.get, basic_url + url, params=params)
    # {'task_id': 143960071, 'task_type': 1, 'topic_mode': 0, 'stem': {'content': 'trade', 'remark': None, 'ph_us_url': '/Resource/unitAudio_US/JJ_3_1_0/trade.mp3', 'ph_en_url': '/Resource/unitAudio_EN/JJ_3_1_0/trade.mp3', 'au_addr': None}, 'options': [{'content': 'verb 互相交换', 'remark': None, 'answer': None, 'answer_tag': 0, 'check_code': None, 'sub_options': None, 'ph_info': {'ph_en': 'treɪd', 'ph_en_url': '/Resource/unitAudio_EN/JJ_3_1_0/trade.mp3', 'ph_us': 'treɪd', 'ph_us_url': '/Resource/unitAudio_US/JJ_3_1_0/trade.mp3', 'group': '0'}}, {'content': 'noun 职业；手艺', 'remark': None, 'answer': None, 'answer_tag': 1, 'check_code': None, 'sub_options': None, 'ph_info': {'ph_en': 'treɪd', 'ph_en_url': '/Resource/unitAudio_EN/JJ_3_1_0/trade.mp3', 'ph_us': 'treɪd', 'ph_us_url': '/Resource/unitAudio_US/JJ_3_1_0/trade.mp3', 'group': '0'}}], 'sound_mark': 'treɪd', 'ph_en': 'treɪd', 'ph_us': 'treɪd', 'answer_num': 1, 'chance_num': 1, 'topic_done_num': 1, 'topic_total': 127, 'w_lens': [], 'w_len': 0, 'w_tip': '', 'tips': '', 'word_type': 1, 'enable_i': 2, 'enable_i_i': 2, 'enable_i_o': 2, 'topic_code': 'lFiAe5drW46DfnrEaJVol2hbXlrWqpianVhlZmGZlmKPvo+UkWOTZWdiYm9ubJuXamCVaGpnaGSUj2STZGhob2JybGuWnG5tjZRlZWuVcmxmYW9pZZSSZ2mebmZtcWRsZWiZaWdsZGaW', 'answer_state': 1, 'show_card_type': 1}
    # 检查请求结果
    handle_response(rsp)
    if rsp.json().get('msg') == '任务已完成！' or rsp.json().get('msg') == '需要选词！':
        public_info.exam = 'complete'
        return
    #  decrypt response
    public_info.exam = debase64(rsp.json()['data'], rsp.json()['jv'])
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
    sign = encrypt_md5(
        "&".join([f'{key}={value}' for key, value in params.items()]) + 'ajfajfamsnfaflfasakljdlalkflak')  # 加密
    params.update({'sign': sign})
    data = check_jv_and_retry_post(requests.rqs2_session.post, basic_url + url, data=json.dumps(params))
    # 检查请求是否成功
    handle_response(data)
    if data.json()['msg'] == '任务已完成！' or data.json()['msg'] == '需要选词！':
        public_info.exam = 'complete'
    # decrypt response
    else:
        public_info.exam = debase64(data.json()['data'], data.json()['jv'])


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


# 查询单词
@check_is_self_built
def query_word(public_info, word):
    time.sleep(random.randint(0, 2))
    api.logger.info(f"查询单词{word}")
    # query word in the unit
    url = f'Course/StudyWordInfo?course_id={public_info.course_id}&list_id={public_info.now_unit}&word={word}&timestamp={create_timestamp()}&version=2.6.1.231204&app_type=1'
    word = check_jv_and_retry_get(requests.rqs_session.get, basic_url + url)
    # 检查请求是否成功
    handle_response(word)
    # decrypt  response
    public_info.word_query_result = debase64(word.json()['data'], word.json()['jv'])
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
    rsp = check_jv_and_retry_post(requests.rqs2_session.post, basic_url + url, data=json.dumps(data))
    # check request is success
    handle_response(rsp)
    result = debase64(rsp.json()['data'], rsp.json()['jv'])
    answer_result = result.get('answer_result')
    api.logger.info(f"答题判分: answer_result={answer_result} answer_corrects={result.get('answer_corrects')}")
    # 对错计数(进度条右侧统计)
    if answer_result == 1:
        public_info.right_count += 1
    elif answer_result == 2:
        public_info.wrong_count += 1
    # 记录标准答案到本地答案库(word_zh -> answer_corrects, 仅短语类题型)
    exam = public_info.exam
    if isinstance(exam, dict):
        mode = exam.get('topic_mode')
        stem = exam.get('stem')
        word_zh = stem.get('remark') if isinstance(stem, dict) else None
        corrects = result.get('answer_corrects')
        if getattr(public_info, '_self_learn_lib', True):
            if mode == 32 and word_zh and corrects:
                # mode 32: answer_corrects 是完整短语, 入短语库
                add_answer(word_zh, corrects)
            elif mode == 73 and word_zh and corrects:
                # mode 73: answer_corrects 是空位单词(非完整短语), 入单词库防污染短语库
                add_word_answer(word_zh, corrects)
            elif mode == 42 and word_zh and corrects:
                # mode 42: answer_corrects 是选项下标数组, 通过 options 取正确答案单词入库
                options = exam.get('options') or []
                words = []
                for idx in corrects:
                    if isinstance(idx, int) and 0 <= idx < len(options):
                        content = options[idx].get('content') if isinstance(options[idx], dict) else None
                        if content:
                            words.append(content)
                if words:
                    add_word_answer(word_zh, words)
    api.logger.info("提取下一题的请求参数")
    # next exam topic_code
    public_info.topic_code = result['topic_code']


def get_task_score(public_info):
    """
    获取任务分数
    """
    try:
        # 根据任务类型获取分数
        if hasattr(public_info, 'release_id') and public_info.release_id:
            # 班级任务
            url = 'https://app.vocabgo.com/student/api/Student/ClassTask/Info'
            params = {
                'task_id': public_info.task_id,
                'release_id': public_info.release_id,
                'timestamp': int(time.time() * 1000),
                'version': '2.6.1.240122',
                'app_type': 1
            }
        else:
            # 自学任务
            url = 'https://app.vocabgo.com/student/api/Student/StudyTask/Info'
            params = {
                'task_id': public_info.task_id,
                'course_id': public_info.course_id,
                'timestamp': int(time.time() * 1000),
                'version': '2.6.1.240122',
                'app_type': 1
            }

        response = requests.class_task_request.get(url, params=params)
        if response.status_code == 200 and response.json().get('code') == 1:
            data = response.json().get('data', {})
            # 尝试从不同字段获取分数
            score = data.get('score') or data.get('task_score') or data.get('grade')
            if score is not None:
                return float(score)
        return None
    except Exception as e:
        api.logger.error(f"获取任务分数失败: {e}")
        return None


if __name__ == '__main__':
    pass
