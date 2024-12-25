import json
import os

from log.log import Log


class PublicInfo:
    # 这俩暂时不知道有啥用
    task_type: str
    task_type_int: int

    #
    def __init__(self, path):
        self.get_word_list_result = {}
        self.path = path
        with open(os.path.join(self.path, "config", "config.json"), 'r', encoding='utf-8') as f:
            # user config
            user_config = json.load(f)
            self._min_time = user_config['min_time']
            self._max_time = user_config['max_time']
            self._spend_min_time = user_config['spend_min_time']
            self._spend_max_time = user_config['spend_max_time']
            self._api_choices = user_config['api_choices']
        # 任务列表
        self.task_list = ""
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
        # 任务类型选择（默认1）
        self._task_choices = 1
        # unit task amount
        self.task_total_count = ''
        self.now_page = ''
        self.release_id = ''
        # self_built
        self.get_book_words_data = []
        self.is_self_built = False  # bool
        self.all_unit_name = []
        self.source_option = []
        pub_info = Log("public_info")
        pub_info.logger.info("公共组件初始化成功")

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
    def task_type_choices(self):
        return self._task_choices

    @property
    def min_time(self) -> int:
        return self._min_time

    @property
    def max_time(self) -> int:
        return self._max_time

    @property
    def spend_min_time(self) -> int:
        return self._spend_min_time

    @property
    def spend_max_time(self) -> int:
        return self._spend_max_time

    @property
    def api_choices(self) -> int:
        return self._api_choices

    def input_info(self, min_time, max_time, min_time_2, max_time_2, choices_api):
        self._min_time = min_time
        self._max_time = max_time
        self._spend_min_time = min_time_2
        self._spend_max_time = max_time_2
        self._api_choices = choices_api
        with open(os.path.join(self.path, "config", "config.json"), 'r', encoding="utf-8") as f:
            data = json.load(f)
            data['min_time'] = self._min_time
            data['max_time'] = self._max_time
            data['spend_min_time'] = self._spend_min_time
            data['spend_max_time'] = self._spend_max_time
            data['api_choices'] = self._api_choices
        data_str = json.dumps(data, indent=2)
        with open(os.path.join(self.path, "config", "config.json"), 'w', encoding="utf-8") as f:
            f.write(data_str)