import time
from log.log import Log

basic_util = Log("basic_util")
def filler_not_complete_unit(public_info) -> None:
    not_complete_unit = []
    for task in public_info.all_unit['task_list']:
        progress = task['progress']
        if progress <= 97:
            not_complete_unit.append([task['list_id'], progress, task['task_id']])
    public_info.not_complete_unit = not_complete_unit


# delete expire task
def get_todo_task(public_info):
    todo_task_list = []
    todo_task = []
    for tasks in public_info.class_task:
        for task in tasks['records']:
            # over_status 2 未过期
            if task['over_status'] == 2:
                # 进度小于100%
                if task['progress'] < 100:
                    # 1为班级学习
                    choice = public_info.task_choices
                    if task['task_type'] == choice:
                        todo_task_list.append(task)
                        # 第一次赛选出来后的任务放在todo_task_list中
    basic_util.logger.info(f'获取任务成功:{todo_task_list}')
    task_names = [task['task_name'] for task in todo_task_list]
    basic_util.logger.info(f'当前选择下的任务有:{task_names}')
    task_choices = input("请输入您要操作的章节：")
    for task in todo_task_list:
        if task['task_name'] == task_choices:
            todo_task.append(task)
    public_info.class_task = todo_task


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


# look up the word in the unit
def query_word_unit(public_info):
    all_unit = {}
    # create all unit dict
    for unit in public_info.all_unit_name:
        all_unit.update({public_info.course_id + ':' + unit: []})
    # word classify
    for word_info in public_info.get_word_list_result["data"]['word_list']:
        all_unit[public_info.course_id + ":" + word_info['list_id']].append(word_info['word'])
    # clear unit is null
    all_unit = {key: value for key, value in all_unit.items() if value}
    public_info.word_list = all_unit
