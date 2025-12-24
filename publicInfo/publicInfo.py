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
            # 用户配置文件
            user_config = json.load(f)
            self._min_time = user_config['min_time']
            self._max_time = user_config['max_time']
            self._spend_min_time = user_config['spend_min_time']
            self._spend_max_time = user_config['spend_max_time']
            self._br_choices = user_config['br_choices']
            self._headers_accept_encoding = user_config['accept_encoding']
            self._version = user_config['version']
            self._know_version = user_config['know_version']
            self._read = user_config['read']
            self._auto_confirm = user_config.get('auto_confirm', False)
            self._show_finish_dialog = user_config.get('show_finish_dialog', True)
            self._play_music = user_config.get('play_music', False)  # 默认为False
            self._music_path = user_config.get('music_path', "")  # 默认为空，使用默认音乐
            self._auto_next_task = user_config.get('auto_next_task', True)
            self._auto_next_order = user_config.get('auto_next_order', 'desc')
            self._auto_next_delay_sec = user_config.get('auto_next_delay_sec', 2)
            self._auto_open_token_tool = user_config.get('auto_open_token_tool', True)
            self._play_error_sound = user_config.get('play_error_sound', True)

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
    def accept_encoding(self) -> str:
        return self._headers_accept_encoding

    @property
    def br_choices(self) -> bool:
        return self._br_choices

    @property
    def play_music(self) -> bool:
        return self._play_music

    @property
    def music_path(self) -> str:
        return self._music_path

    @property
    def auto_next_task(self) -> bool:
        return self._auto_next_task

    @property
    def auto_next_order(self) -> str:
        return self._auto_next_order

    @property
    def auto_next_delay_sec(self) -> int:
        return self._auto_next_delay_sec

    @property
    def auto_open_token_tool(self) -> bool:
        return self._auto_open_token_tool

    @property
    def play_error_sound(self) -> bool:
        return self._play_error_sound

    @property
    def version(self) -> str:
        return self._version

    @property
    def know_version(self) -> str:
        return self._know_version

    @property
    def read(self) -> bool:
        return self._read

    @property
    def auto_confirm(self) -> bool:
        return self._auto_confirm

    @property
    def show_finish_dialog(self) -> bool:
        return self._show_finish_dialog

    def read_seen(self):
        with open(os.path.join(self.path, "config", "config.json"), 'r', encoding="utf-8") as f:
            data = json.load(f)
            data['read'] = True
            self._read = True
        with open(os.path.join(self.path, "config", "config.json"), 'w', encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def input_info(self, min_time, max_time, min_time_2, max_time_2, br_choices, accept_encoding, play_music=None, music_path=None, auto_confirm=None, show_finish_dialog=None, auto_next_task=None, auto_next_order=None, auto_next_delay_sec=None, auto_open_token_tool=None, play_error_sound=None):
        self._min_time = min_time
        self._max_time = max_time
        self._spend_min_time = min_time_2
        self._spend_max_time = max_time_2
        self._br_choices = br_choices
        self._headers_accept_encoding = accept_encoding
        if play_music is not None:
            self._play_music = play_music
        if music_path is not None:
            self._music_path = music_path
        if auto_confirm is not None:
            self._auto_confirm = auto_confirm
        if show_finish_dialog is not None:
            self._show_finish_dialog = show_finish_dialog
        if auto_next_task is not None:
            self._auto_next_task = auto_next_task
        if auto_next_order is not None:
            self._auto_next_order = auto_next_order
        if auto_next_delay_sec is not None:
            self._auto_next_delay_sec = auto_next_delay_sec
        if auto_open_token_tool is not None:
            self._auto_open_token_tool = auto_open_token_tool
        if play_error_sound is not None:
            self._play_error_sound = play_error_sound

        with open(os.path.join(self.path, "config", "config.json"), 'r', encoding="utf-8") as f:
            data = json.load(f)
            data['min_time'] = self._min_time
            data['max_time'] = self._max_time
            data['spend_min_time'] = self._spend_min_time
            data['spend_max_time'] = self._spend_max_time
            data['br_choices'] = self._br_choices
            data['accept_encoding'] = self._headers_accept_encoding
            if play_music is not None:
                data['play_music'] = self._play_music
            if music_path is not None:
                data['music_path'] = self._music_path
            if auto_confirm is not None:
                data['auto_confirm'] = self._auto_confirm
            if show_finish_dialog is not None:
                data['show_finish_dialog'] = self._show_finish_dialog
            if auto_next_task is not None:
                data['auto_next_task'] = self._auto_next_task
            if auto_next_order is not None:
                data['auto_next_order'] = self._auto_next_order
            if auto_next_delay_sec is not None:
                data['auto_next_delay_sec'] = self._auto_next_delay_sec
            if auto_open_token_tool is not None:
                data['auto_open_token_tool'] = self._auto_open_token_tool
            if play_error_sound is not None:
                data['play_error_sound'] = self._play_error_sound
        data_str = json.dumps(data, indent=2)
        with open(os.path.join(self.path, "config", "config.json"), 'w', encoding="utf-8") as f:
            f.write(data_str)

    def ignore_version(self, version):
        with open(os.path.join(self.path, "config", "config.json"), 'r', encoding="utf-8") as f:
            data = json.load(f)
            data['know_version'] = version
            self._know_version = version
        with open(os.path.join(self.path, "config", "config.json"), 'w', encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
