import os
import random
import sys
import time

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication

from answer_questions.answer_questions import *
from api.basic_api import get_all_unit, get_unit_words, get_book_all_words
from api.main_api import get_exam, select_all_word, skip_exam, get_task_score
from log.log import Log
from publicInfo.publicInfo import PublicInfo
from util.basic_util import extract_book_word, query_word_unit
from util.handle_word_list import handle_word_result
from api.update import get_update
from decryptencrypt.debase64 import debase64
from view.main_window import UiMainWindow


class TaskWorker(QThread):
    task_finished = pyqtSignal(str)
    task_error = pyqtSignal(str)
    task_progress = pyqtSignal(str)
    task_notice = pyqtSignal(str)     # 重试/跳过等提示
    batch_finished = pyqtSignal(str)  # 批量模式全部执行结束

    def __init__(self, task_infos, batch_mode=False):
        super().__init__()
        self.task_infos = task_infos
        self.batch_mode = batch_mode
        self._is_running = True
        self.start_time = None

    def run(self):
        total = len(self.task_infos)
        success_count = 0
        failed_tasks = []
        for index, task_info in enumerate(self.task_infos, start=1):
            if not self._is_running:
                break
            task_name = task_info['task_name']
            main.logger.info(f"开始执行任务[{index}/{total}]：{task_name}")
            attempts = 0
            while self._is_running:
                attempts += 1
                try:
                    self.start_time = time.time()
                    self.complete_test(task_info)
                    if self._is_running:
                        elapsed_time = time.time() - self.start_time
                        message = f"[{index}/{total}] {task_name} 已完成，用时 {elapsed_time:.2f} 秒"
                        self.task_finished.emit(message)
                        get_task_score(public_info)
                        success_count += 1
                    break
                except Exception as e:
                    main.logger.error(f"任务 {task_name} 执行出错（第{attempts}次）: {e}", exc_info=True)
                    if attempts >= 3:
                        if self.batch_mode:
                            failed_tasks.append(task_name)
                            self.task_notice.emit(f"[{index}/{total}] 任务 {task_name} 连续失败3次，已跳过，继续下一个")
                        else:
                            self.task_error.emit(f"任务 {task_name} 连续失败3次：{e}")
                            return
                        break
                    if not self._is_running:
                        break
                    self.task_notice.emit(f"[{index}/{total}] 任务 {task_name} 第{attempts}次出错：{e}，2秒后自动重试")
                    time.sleep(2)

        if self._is_running and self.batch_mode:
            summary = f"一键刷题完成：成功 {success_count} 个，失败 {len(failed_tasks)} 个"
            if failed_tasks:
                summary += f"\n失败任务：{', '.join(failed_tasks)}"
            self.batch_finished.emit(summary)

    def stop(self):
        self._is_running = False

    def complete_test(self, task_info: dict):
        task_name = task_info['task_name']
        public_info.course_id = task_info['course_id']
        main.logger.info(f'开始执行任务：{task_name}')
        main.logger.info('用课程course_id获取单元list_id')
        main.logger.info('获取该课程的所有单元')
        get_all_unit(public_info)
        public_info.release_id = task_info['release_id']
        all_unit_name = []
        for unit in public_info.all_unit['task_list']:
            if not self._is_running:
                return
            unit_name = unit['task_name']
            all_unit_name.append(unit_name)
            public_info.all_unit_name.append(unit['list_id'])
            if unit_name == task_name:
                public_info.now_unit = unit['list_id']
                public_info.task_id = unit['task_id']
                break
        unit_progress = task_info['progress']
        if task_name not in all_unit_name:
            public_info.is_self_built = True
            main.logger.info(f"{task_name}为自建任务")
            if task_info['task_type'] == 1:
                main.logger.info("完成学习任务的自建任务")
                main.logger.info('获取该自建任务的单词')
                public_info.task_id = task_info['task_id']
                get_unit_words(public_info)
                main.logger.info("获取提交单词")
                query_word_unit(public_info)
                main.logger.info(f"获取成功：{public_info.word_list}")
                if (unit_progress < 2 and public_info.get_word_list_result['exist_little_task'] != 1) or \
                        public_info.get_word_list_result['exist_little_task'] == 2:
                    select_all_word(public_info.word_list, public_info.task_id)
            else:
                main.logger.info("开始测试任务的自建任务")
            get_book_all_words(public_info)
            extract_book_word(public_info)
            self.class_task_answer()
        else:
            if task_info['task_type'] == 1:
                main.logger.info(f'开始班级学习任务{public_info.now_unit}')
                self.complete_practice(public_info.now_unit, unit_progress, task_info['task_id'])
            else:
                main.logger.info(f'开始班级测试任务{public_info.now_unit}')
                get_unit_words(public_info)
                handle_word_result(public_info)
                main.logger.info(f"获取单元所有单词{public_info.word_list}")
                public_info.task_id = task_info['task_id']
                self.class_task_answer()

    def emit_progress(self):
        """
        发送答题进度
        :return:
        """
        if isinstance(public_info.exam, dict):
            done = public_info.exam.get('topic_done_num', 0)
            total = public_info.exam.get('topic_total', 0)
            if total:
                self.task_progress.emit(f"{done}/{total}")

    def class_task_answer(self):
        token = PublicInfo.token
        get_exam(public_info)
        public_info.topic_code = public_info.exam['topic_code']
        self.emit_progress()
        main.logger.info("开始答题")
        while self._is_running:
            main.logger.info("获取题目类型")
            if public_info.exam == 'complete':
                break
            mode = public_info.exam['topic_mode']
            main.logger.info(f'题目类型{mode}')
            if mode == 0:
                jump_read(public_info)
                self.emit_progress()
                continue
            option = answer(public_info, mode)
            if option is None:
                public_info.topic_code = public_info.exam['topic_code']
                skip_exam(public_info)
            else:
                submit(public_info, option)
            self.emit_progress()
            time.sleep(random.randint(public_info.min_time, public_info.max_time))

    def complete_practice(self, unit: str, progress: int, task_id=None):
        main.logger.info(f"获取该{unit}单元的单词")
        public_info.now_unit = unit
        public_info.task_id = task_id
        get_unit_words(public_info)
        main.logger.info("处理words")
        handle_word_result(public_info)
        main.logger.info("选择该单元所有单词")
        exist_little_task = None
        gwlr = public_info.get_word_list_result
        if isinstance(gwlr, dict) and 'data' in gwlr:
            data_field = gwlr['data']
            if isinstance(data_field, dict):
                exist_little_task = data_field.get('exist_little_task')
            else:
                try:
                    if 'jv' in gwlr:
                        decoded = debase64(data_field, gwlr.get('jv'))
                        if isinstance(decoded, dict):
                            exist_little_task = decoded.get('exist_little_task')
                            public_info.get_word_list_result = decoded
                except Exception as e:
                    main.logger.error(f"解析 get_word_list_result 失败: {e}", exc_info=True)
        if (progress < 2 and exist_little_task != 1) or exist_little_task == 2:
            try:
                select_all_word({f"{public_info.course_id}:{unit}": public_info.word_list}, public_info.task_id)
            except Exception as e:
                main.logger.info("任务已经开启")
        get_exam(public_info)
        public_info.topic_code = public_info.exam['topic_code']
        self.emit_progress()
        main.logger.info("开始答题")
        while self._is_running:
            main.logger.info("获取题目类型")
            if public_info.exam == 'complete':
                main.logger.info('该单元已完成')
                break
            mode = public_info.exam['topic_mode']
            if mode == 0:
                jump_read(public_info)
                self.emit_progress()
                continue
            option = answer(public_info, mode)
            if option is None:
                public_info.topic_code = public_info.exam['topic_code']
                skip_exam(public_info)
            else:
                submit(public_info, option)
            self.emit_progress()
            time.sleep(random.randint(public_info.min_time, public_info.max_time))


if __name__ == '__main__':
    main = Log("main")
    main.logger.info("初始化主页面")
    path = os.path.dirname(__file__)
    main.logger.info("初始化公共组件")
    public_info = PublicInfo(path)
    main.logger.info(f"当前版本号：{public_info.version}")

    app = QApplication(sys.argv)
    if not public_info.read:
        main.logger.info("显示首次使用提示页面")
        import view.first_note

        note = view.first_note.Ui_Form(public_info)
        note.show()
        app.exec()

    try:
        ui = UiMainWindow(public_info, path, main, TaskWorker)
        ui.show()


        class UpdateCheckThread(QThread):
            version_ready = pyqtSignal(str)

            def run(self):
                self.version_ready.emit(get_update())


        update_thread = UpdateCheckThread()


        def on_version_checked(latest_version):
            if public_info.version < latest_version and public_info.know_version < latest_version:
                import view.update
                update = view.update.Ui_Form(public_info)
                update.exec()


        update_thread.version_ready.connect(on_version_checked)
        update_thread.start()

        app.exec()
    except Exception as e:
        main.logger.error(e)
        main.logger.error("程序异常")
        import view.error

        ui = view.error.Ui_Form()
        ui.show()
        app.exec()
