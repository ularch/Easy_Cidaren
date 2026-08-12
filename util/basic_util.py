import time

from log.log import Log
from decryptencrypt.debase64 import debase64

basic_util = Log("basic_util")


def filler_not_complete_unit(public_info) -> None:
    not_complete_unit = []
    for task in public_info.all_unit['task_list']:
        progress = task['progress']
        if progress <= 97:
            not_complete_unit.append([task['list_id'], progress, task['task_id']])
    public_info.not_complete_unit = not_complete_unit


# get all task
def get_all_task(public_info):
    """
    获取全部任务（包括已完成），排除已过期
    :param public_info: 公共组件
    """
    all_task_list = []
    for tasks in public_info.class_task:
        for task in tasks['records']:
            # over_status 1 未开始 2 未过期 3 已过期
            if task['over_status'] != 3:
                # 1为班级学习任务，2为班级测试任务
                choice = public_info.task_type_choices
                if task['task_type'] == choice:
                    all_task_list.append(task)
    basic_util.logger.info(f'获取到:{all_task_list}')
    public_info.task_list = all_task_list


# create timestamp
def create_timestamp() -> int:
    return int(time.time() * 1000)


def delete_other_char(result: str) -> str:
    delete_list = ['}', '{', ' ...', ' …']
    for delete_str in delete_list:
        result = result.replace(delete_str, '')
    return result.replace(' ', ',')


# extract word
def extract_book_word(public_info):
    public_info.word_list = [d['word'] for d in public_info.get_book_words_data]


# 在单元中查找单词
def query_word_unit(public_info):
    public_info.get_word_list_result = debase64(public_info.get_word_list_result['data'], public_info.get_word_list_result['jv'])
    all_unit = {}
    # 创建所有单元字典
    for unit in public_info.all_unit_name:
        all_unit.update({public_info.course_id + ':' + unit: []})
    # 单词分类
    for word_info in public_info.get_word_list_result['word_list']:
        all_unit[public_info.course_id + ":" + word_info['list_id']].append(word_info['word'])
    # 清除无效单元
    all_unit = {key: value for key, value in all_unit.items() if value}
    public_info.word_list = all_unit
