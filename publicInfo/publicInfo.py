import json
import os


class PublicInfo:
    # task_choice: str
    task_type: str
    task_type_int: int

    def __init__(self, path):
        self.get_word_list_result = {}
        self.path = path
        user_input = input("请输入token：")
        self._token = user_input
        # 设置待刷任务类型
        user_choice = input("请输入任务选择（1：学习任务；2：测试任务）：")
        self._task_choices = int(user_choice)
        # 设置间隔
        min_time_input = input("请输入最短间隔秒数:")
        self._min_time = int(min_time_input)
        max_time_input = input("请输入最长间隔秒数:")
        self._max_time = int(max_time_input)
        # query_answer
        self._topic_code = ''
        self.word_query_result = ''
        self.word_means = ''
        self.exam = ''
        # all word
        self.word_list = []
        # translate
        self.zh_en = ''
        # all unit info
        self.all_unit = []
        self.not_complete_unit = {}
        self.task_id = ''
        self.now_unit = ''
        self.course_id = ''
        # class task
        self.class_task = []
        # unit task amount
        self.task_total_count = ''
        self.now_page = ''
        self.release_id = ''
        # self_built
        self.get_book_words_data = []
        self.is_self_built = False  # bool
        self.all_unit_name = []
        self.source_option = []

    @property
    # only read
    def topic_code(self):
        return self._topic_code

    @topic_code.setter
    # only write
    def topic_code(self, value):
        self._topic_code = value

    @topic_code.deleter
    # only del
    def topic_code(self):
        del self._topic_code

    @property
    def token(self):
        return self._token

    @property
    def task_choices(self):
        return self._task_choices

    @property
    def min_time(self):
        return self._min_time

    @property
    def max_time(self):
        return self._max_time
