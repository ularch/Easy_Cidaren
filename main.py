import os
import subprocess
import threading
import sys
import winsound
import time

from PyQt6.QtGui import QAction, QIcon
from playsound import playsound

import api.request_header as requests
import view.setting, view.introduce, view.update, view.first_note, view.error
from answer_questions.answer_questions import *
from api.basic_api import get_all_unit, get_unit_words, get_book_all_words
from api.login import verify_token
from api.main_api import get_exam, select_all_word, get_class_task, skip_exam
from log.log import Log
from publicInfo.publicInfo import PublicInfo
from util.basic_util import get_todo_task, extract_book_word, query_word_unit, get_choices_task
from util.handle_word_list import handle_word_result
from api.update import get_update, get_update_detail

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QMainWindow, QApplication, QMessageBox, QFileDialog
from PyQt6.QtCore import QThread, pyqtSignal


class TaskWorker(QThread):
    """
    工作线程类，用于在后台执行任务
    """
    task_finished = pyqtSignal(str)  # 任务完成信号
    task_error = pyqtSignal(str)    # 任务错误信号
    task_progress = pyqtSignal(str) # 任务进度信号

    def __init__(self, task_info):
        super().__init__()
        self.task_info = task_info
        self._is_running = True
        self.start_time = None

    def run(self):
        """
        开始运行
        """
        try:
            self.start_time = time.time()  # 记录任务开始时间
            self.complete_test(self.task_info)
            if self._is_running:
                elapsed_time = time.time() - self.start_time  # 计算用时
                self.task_finished.emit(f"任务已完成，用时 {elapsed_time:.2f} 秒")
        except Exception as e:
            if self._is_running:
                self.task_error.emit(str(e))

    def stop(self):
        """
        停止任务
        """
        self._is_running = False
        
    def complete_test(self, task_info: dict):
        """
        带有停止检查的完成班级任务
        """
        task_name = task_info['task_name']
        # course_id 课程id (course_id)
        public_info.course_id = task_info['course_id']
        main.logger.info(f'开始执行任务：{task_name}')
        # 获取单元id (list_id)
        main.logger.info('用课程course_id获取单元list_id')
        # 获取该用户所有单元
        main.logger.info('获取该课程的所有单元')
        get_all_unit(public_info)
        # release_id 任务id
        public_info.release_id = task_info['release_id']
        all_unit_name = []
        for unit in public_info.all_unit['task_list']:
            # 检查是否需要停止
            if not self._is_running:
                return
                
            unit_name = unit['task_name']
            all_unit_name.append(unit_name)
            public_info.all_unit_name.append(unit['list_id'])
            # 验证单元名与任务名相等
            if unit_name == task_name:
                public_info.now_unit = unit['list_id']
                public_info.task_id = unit['task_id']
                break
        unit_progress = task_info['progress']
        # 自建任务
        if task_name not in all_unit_name:
            public_info.is_self_built = True
            main.logger.info(f"{task_name}为自建任务")
            if task_info['task_type'] == 1:
                main.logger.info("完成自学任务的自建任务")
                main.logger.info('获取该自建任务的单词')
                public_info.task_id = task_info['task_id']
                get_unit_words(public_info)
                main.logger.info("获取提交单词")
                query_word_unit(public_info)
                if (unit_progress < 2 and public_info.get_word_list_result['data']['exist_little_task'] != 1) or \
                        public_info.get_word_list_result['data']['exist_little_task'] == 2:
                    select_all_word(public_info.word_list, public_info.task_id)
            else:
                main.logger.info("开始班级自建任务")
                # 获取书籍所有单词
            get_book_all_words(public_info)
            # 处理单词
            extract_book_word(public_info)
            # 答题
            self.class_task_answer()
        else:
            # 班级自学任务
            if task_info['task_type'] == 1:
                main.logger.info('开始班级自学任务')
                self.complete_practice(public_info.now_unit, unit_progress, task_info['task_id'])
            else:
                # 班级测试任务
                main.logger.info('开始班级测试任务')
                # 获取单元所有单词
                get_unit_words(public_info)
                handle_word_result(public_info)
                public_info.task_id = task_info['task_id']
                self.class_task_answer()

    def class_task_answer(self):
        """
        带有停止检查的测试任务及自建任务
        """
        token = PublicInfo.token
        # 获取第一个试题
        get_exam(public_info)
        public_info.topic_code = public_info.exam['topic_code']
        main.logger.info("开始答题")
        while self._is_running:
            main.logger.info("获取题目类型")
            if public_info.exam == 'complete':
                # 单元完成
                break
            mode = public_info.exam['topic_mode']
            main.logger.info(f'题目类型{mode}')
            if mode == 0:
                # 跳过阅读卡片
                jump_read(public_info)
                continue
            option = answer(public_info, mode)
            if option is None:
                public_info.topic_code = public_info.exam['topic_code']
                skip_exam(public_info)
            else:
                submit(public_info, option)
            # 暂停
            time.sleep(random.randint(public_info.min_time, public_info.max_time))

    def complete_practice(self, unit: str, progress: int, task_id=None):
        """
        班级任务和自学任务共用
        :param task_id: 任务id
        :param unit: 单元名称
        :param progress: 单元进度
        """
        main.logger.info(f"获取该{unit}单元的单词")
        public_info.now_unit = unit
        public_info.task_id = task_id
        # 获取单元所有单词
        get_unit_words(public_info)
        main.logger.info("处理words")
        handle_word_result(public_info)
        main.logger.info("选择该单元所有单词")
        # {"CET4_pre:CET4_pre_10":["survey","apply","defasdfa"]} word
        # 未完成单元选择所有单词
        if (progress < 2 and public_info.get_word_list_result['data']['exist_little_task'] != 1) or \
                public_info.get_word_list_result['data']['exist_little_task'] == 2:
            select_all_word({f"{public_info.course_id}:{unit}": public_info.word_list}, public_info.task_id)
        # 获取第一个试题
        get_exam(public_info)
        public_info.topic_code = public_info.exam['topic_code']
        main.logger.info("开始答题")
        # topic_mode 题型
        while self._is_running:
            main.logger.info("获取题目类型")
            if public_info.exam == 'complete':
                main.logger.info('该单元已完成')
                # 当前单元已完成
                break
            mode = public_info.exam['topic_mode']
            # 处理答案（选项）
            if mode == 0:
                # 跳过单词阅读
                jump_read(public_info)
                continue
            option = answer(public_info, mode)
            # 选项
            if option is None:
                public_info.topic_code = public_info.exam['topic_code']
                skip_exam(public_info)
            else:
                submit(public_info, option)
            # 暂停
            time.sleep(random.randint(public_info.min_time, public_info.max_time))


class UiMainWindow(QMainWindow):
    """
    主菜单ui
    """
    output = "软件初始化成功！"

    def __init__(self):
        super(UiMainWindow, self).__init__()
        self.token = ''
        self.task_worker = None
        self.task_index = 0
        self.setupUi(self)

    def setupUi(self, MainWindow):
        """
        绘制ui
        """
        MainWindow.setObjectName("MainWindow")
        MainWindow.setFixedSize(720, 280)
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(__file__), 'assets', 'icon.ico')
        if os.path.exists(icon_path):
            MainWindow.setWindowIcon(QIcon(icon_path))
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.output_info = QtWidgets.QTextBrowser(parent=self.centralwidget)
        self.output_info.setGeometry(QtCore.QRect(460, 40, 256, 181))
        self.output_info.setObjectName("textBrowser")
        self.label = QtWidgets.QLabel(parent=self.centralwidget)
        self.label.setGeometry(QtCore.QRect(20, 20, 71, 16))
        self.label.setObjectName("label")
        self.token_input = QtWidgets.QLineEdit(parent=self.centralwidget)
        self.token_input.setGeometry(QtCore.QRect(20, 40, 301, 20))
        self.token_input.setObjectName("token")
        self.login = QtWidgets.QPushButton(parent=self.centralwidget)
        self.login.setGeometry(QtCore.QRect(330, 40, 61, 24))
        self.login.setObjectName("login")
        # 登录点击事件
        self.login.clicked.connect(self.token_login)
        self.warn_info = QtWidgets.QLabel(parent=self.centralwidget)
        self.warn_info.setGeometry(QtCore.QRect(20, 60, 441, 16))
        self.warn_info.setStyleSheet("")
        self.warn_info.setObjectName("warn_info")
        self.label_3 = QtWidgets.QLabel(parent=self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(460, 20, 61, 16))
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(parent=self.centralwidget)
        self.label_4.setGeometry(QtCore.QRect(20, 90, 61, 16))
        self.label_4.setObjectName("label_4")
        self.user_info = QtWidgets.QLabel(parent=self.centralwidget)
        self.user_info.setGeometry(QtCore.QRect(20, 110, 441, 16))
        self.user_info.setObjectName("user_info")
        self.label_6 = QtWidgets.QLabel(parent=self.centralwidget)
        self.label_6.setGeometry(QtCore.QRect(20, 140, 71, 16))
        self.label_6.setObjectName("label_6")
        self.formLayoutWidget = QtWidgets.QWidget(parent=self.centralwidget)
        self.formLayoutWidget.setGeometry(QtCore.QRect(100, 140, 211, 22))
        self.formLayoutWidget.setObjectName("formLayoutWidget")
        self.formLayout = QtWidgets.QFormLayout(self.formLayoutWidget)
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.formLayout.setObjectName("formLayout")
        self.learn_task = QtWidgets.QRadioButton(parent=self.formLayoutWidget)
        self.learn_task.setObjectName("learn_task")
        self.learn_task.setChecked(True)
        # 学习任务点击事件
        self.learn_task.clicked.connect(self.get_task_list)
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.learn_task)
        self.test_task = QtWidgets.QRadioButton(parent=self.formLayoutWidget)
        self.test_task.setObjectName("test_task")
        # 测试任务点击事件
        self.test_task.clicked.connect(self.get_task_list)
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.test_task)
        self.task_list = QtWidgets.QComboBox(parent=self.centralwidget)
        self.task_list.setGeometry(QtCore.QRect(20, 170, 291, 22))
        self.task_list.setObjectName("task_list")
        self.start_task = QtWidgets.QPushButton(parent=self.centralwidget)
        self.start_task.setGeometry(QtCore.QRect(20, 200, 111, 24))
        self.start_task.setObjectName("start_task")
        # 开始任务点击事件
        self.start_task.clicked.connect(self.start)
        self.stop_task = QtWidgets.QPushButton(parent=self.centralwidget)
        self.stop_task.setGeometry(QtCore.QRect(150, 200, 111, 24))
        self.stop_task.setObjectName("stop_task")
        # 停止任务点击事件
        self.stop_task.clicked.connect(self.stop_current_task)
        self.follow_output = QtWidgets.QRadioButton(parent=self.centralwidget)
        self.follow_output.setGeometry(QtCore.QRect(607, 19, 101, 16))
        self.follow_output.setObjectName("follow_output")
        self.follow_output.setChecked(True)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setEnabled(True)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 720, 33))
        self.menubar.setObjectName("menubar")
        # 让菜单栏根据系统主题自适应，同时确保在各种主题下都有良好的可见性
        self.menubar.setStyleSheet("""
            QMenuBar {
                background-color: palette(menu);
                color: palette(text);
                border: none;
            }
            QMenuBar::item {
                background: transparent;
                color: palette(text);
            }
            QMenuBar::item:selected {
                background: palette(highlight);
            }
            QMenuBar::item:pressed {
                background: palette(highlight);
            }
            QMenu {
                background-color: palette(menu);
                color: palette(text);
            }
            QMenu::item {
                color: palette(text);
            }
            QMenu::item:selected {
                background-color: palette(highlight);
            }
        """)

        # 添加菜单栏和主内容区域之间的分隔线
        self.menu_separator = QtWidgets.QFrame(parent=MainWindow)
        self.menu_separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.menu_separator.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.menu_separator.setObjectName("menu_separator")

        self.menu = QtWidgets.QMenu(parent=self.menubar)
        self.menu.setObjectName("menu")
        self.menu_2 = QtWidgets.QMenu(parent=self.menubar)
        self.menu_2.setObjectName("menu_2")
        MainWindow.setMenuBar(self.menubar)

        # 设置分隔线的位置和大小
        self.menu_separator.setGeometry(QtCore.QRect(0, 33, 720, 3))

        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.action = QtGui.QAction(parent=MainWindow)
        self.action.setObjectName("action")
        self.action_3 = QtGui.QAction(parent=MainWindow)
        self.action_3.setObjectName("action_3")
        self.action_4 = QtGui.QAction(parent=MainWindow)
        self.action_4.setObjectName("action_4")
        self.action_6 = QtGui.QAction(parent=MainWindow)
        self.action_6.setObjectName("action_6")
        self.action_7 = QtGui.QAction(parent=MainWindow)
        self.action_7.setObjectName("action_7")
        self.action_8 = QtGui.QAction(parent=MainWindow)
        self.action_8.setObjectName("action_8")
        # 导出日志文件夹
        self.action_open_logs = QtGui.QAction(parent=MainWindow)
        self.action_open_logs.setObjectName("action_open_logs")
        self.menu.addAction(self.action)
        # 设置菜单名项点击事件
        self.menu.triggered[QAction].connect((self.open_settings))
        self.menu_2.addAction(self.action_4)
        self.menu_2.addSeparator()
        self.menu_2.addAction(self.action_6)
        self.menu_2.addAction(self.action_7)
        self.menu_2.addSeparator()
        self.menu_2.addAction(self.action_8)
        self.action_open_logs.setText("导出日志文件")
        self.menu_2.addAction(self.action_open_logs)
        # 帮助菜单点击事件
        self.menu_2.triggered[QAction].connect((self.open_helper))
        # 连接导出日志文件的动作
        # self.action_open_logs.triggered.connect(Log.open_logs_folder)
        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.menu_2.menuAction())
        self.retranslate_ui(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslate_ui(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(
            _translate("MainWindow", f"EasyCidaren_v{public_info.version}（github免费开源，严禁倒卖，作者ularch）"))
        self.output_info.setHtml(_translate("MainWindow", f"<pre>{UiMainWindow.output}</pre>"))
        self.label.setText(_translate("MainWindow", "用户token："))
        self.login.setText(_translate("MainWindow", "登录"))
        self.label_3.setText(_translate("MainWindow", "输出信息："))
        self.label_4.setText(_translate("MainWindow", "用户信息："))
        self.user_info.setText(_translate("MainWindow", "未获取"))
        self.label_6.setText(_translate("MainWindow", "待完成任务："))
        self.learn_task.setText(_translate("MainWindow", "班级自学任务"))
        self.test_task.setText(_translate("MainWindow", "班级测试任务"))
        self.start_task.setText(_translate("MainWindow", "开始任务"))
        self.stop_task.setText(_translate("MainWindow", "中止任务"))
        self.follow_output.setText(_translate("MainWindow", "随新消息滚动"))
        self.menu.setTitle(_translate("MainWindow", "设置"))
        self.menu_2.setTitle(_translate("MainWindow", "帮助"))
        self.action.setText(_translate("MainWindow", "首选项..."))
        self.action_4.setText(_translate("MainWindow", "使用教程"))
        self.action_6.setText(_translate("MainWindow", "关于Easy_Cidaren"))
        self.action_7.setText(_translate("MainWindow", "关于作者"))
        self.action_8.setText(_translate("MainWindow", "获取token"))
        self.action_open_logs.setText(_translate("MainWindow", "导出日志文件"))

    def update_output_info(self, info):
        """
        更新输出信息并滚动到最下
        :return:
        """
        ui.output = ui.output + f"\n{info}"
        self.output_info.setHtml(f"<pre>{ui.output}</pre>")
        if self.follow_output.isChecked():
            scrollbar = self.output_info.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def token_login(self):
        """
        token登录
        """
        # 重置警告信息
        self.warn_info.setText("")
        # 修复获取token问题
        input_text = self.token_input.text()
        if '\n' in input_text:
            # 如果包含换行符，只取第一行
            self.token = input_text.split('\n')[0].strip()
        else:
            # 如果不包含换行符，直接使用
            self.token = input_text.strip()
        if self.token == '':
            self.warn_info.setStyleSheet("color: red;")
            self.warn_info.setText("登录失败！请输入token！")
        else:
            result = verify_token(self.token)
            self.warn_info.setStyleSheet("color: red;")
            if result == 1:
                self.warn_info.setText("登录失败！token已过期，请重新获取！")
            elif result == 2:
                self.warn_info.setText("登录失败！HTTP请求错误！")
            elif result == 3:
                self.warn_info.setText("登录失败！请检查网络连接！")
            elif result == 4:
                self.warn_info.setText("登录失败！响应内容不是有效的JSON格式！")
            elif result == 5:
                self.warn_info.setText("登录失败！请检查token获取软件是否关闭！")
            elif result == 6:
                self.warn_info.setText("登录失败！请检查或关闭代理软件！")
            elif result == 7:
                self.warn_info.setText("登录失败！请检查网络连接！")
            else:
                self.warn_info.setStyleSheet("color: green;")
                self.warn_info.setText("登录成功！")
                ui.update_output_info("登录成功！")
                # 获取用户信息
                student_name = result['data']['user_info']['student_name']
                student_code = result['data']['user_info']['student_code']
                school_name = result['data']['user_info']['school_name']
                class_name = result['data']['user_info']['class_name']
                self.user_info.setText(f"{student_name} {student_code} {school_name} {class_name}")
                ui.update_output_info("用户信息获取成功！")
                # 初始化请求token()
                requests.set_token(self.token)
                # 同时自动获取任务
                self.get_task_list()

    def get_task_list(self):
        """
        获取任务列表
        """
        self.task_list.clear()
        if not self.user_info.text() == "未获取":
            if self.learn_task.isChecked():
                public_info._task_choices = 1
                ui.update_output_info("开始获取：班级学习任务")
            elif self.test_task.isChecked():
                public_info._task_choices = 2
                ui.update_output_info("开始获取：班级测试任务")
            # 重置class_task
            public_info.class_task = []
            # 获取任务列表
            main.logger.info('开始获取任务')
            PublicInfo.task_type = 'ClassTask'
            PublicInfo.task_type_int = 2
            now_page = 1
            get_class_task(public_info, now_page)
            while public_info.task_total_count > now_page * 10:
                now_page += 1
                get_class_task(public_info, now_page)
            # 获取需要完成的任务
            get_todo_task(public_info)
            # 获取任务名称
            if not public_info.task_list == []:
                task_names = [task['task_name'] for task in public_info.task_list]
                main.logger.info(f'{task_names}')
                for task in task_names:
                    self.task_list.addItem(f"{task}")
                ui.update_output_info("获取成功！")
            else:
                ui.update_output_info("获取失败！没有待完成的任务！")

    def start(self):
        try:
            if not public_info.task_list == [] and not public_info.class_task == []:
                main.logger.info("开始任务")
                # 获取所选任务名称
                task_name = self.task_list.currentText()
                self.task_index = self.task_list.currentIndex()
                get_choices_task(public_info, task_name)
                ui.update_output_info(f"开始任务{task_name}")
                # 开始任务 启动等待页面
                reply = QMessageBox.question(self, f"开始任务{task_name}",
                                             f"确认开始任务{task_name}吗？\n任务开始后，主页面将无法操作，可点击“中止任务”按钮手动中止任务\n系统将在后台自动执行刷题\n运行期间请勿关闭程序窗口",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                             QMessageBox.StandardButton.Yes)
                if reply == QMessageBox.StandardButton.Yes:
                    # 关闭自建任务
                    task_info = public_info.class_task[0]
                    public_info.is_self_built = False
                    
                    # 禁用所有控件（除了停止任务按钮）
                    self.set_ui_enabled(False)
                    
                    # 创建并启动工作线程
                    self.task_worker = TaskWorker(task_info)
                    self.task_worker.task_finished.connect(self.on_task_finished)
                    self.task_worker.task_error.connect(self.on_task_error)
                    self.task_worker.task_progress.connect(self.update_output_info)
                    self.task_worker.start()
                    
                    self.update_output_info("任务已在后台开始执行...")
            else:
                self.update_output_info("没有可执行的任务")
        except Exception as e:
            main.logger.error(f"运行出错，错误信息：{e}")
            self.update_output_info(f"运行出错，错误信息：{e}")

    def on_task_finished(self, message):
        """任务完成时调用"""
        # 重新启用所有控件
        self.set_ui_enabled(True)
        
        # 任务完成提示音乐
        music_thread = threading.Thread(target=self.play_music)
        music_thread.start()
        
        # 任务完成提示
        QtWidgets.QMessageBox.information(self, "任务完成！", message)
        main.logger.info(f'{message}')
        task_name = public_info.class_task[0]['task_name']
        self.update_output_info(f"{task_name}运行完成")
        self.update_output_info(message)  # 显示任务用时信息
        
        # 删除已完成任务
        self.task_list.removeItem(self.task_index)
        
        # 清理工作线程
        if self.task_worker:
            self.task_worker.deleteLater()
            self.task_worker = None

    def on_task_error(self, error_message):
        """任务出错时调用"""
        # 重新启用所有控件
        self.set_ui_enabled(True)
        
        main.logger.error(f"运行出错，错误信息：{error_message}")
        self.update_output_info(f"运行出错，错误信息：{error_message}")
        
        # 显示错误页面
        error = view.error.Ui_Form()
        error.exec()
        
        # 清理工作线程
        if self.task_worker:
            self.task_worker.deleteLater()
            self.task_worker = None

    def open_settings(self, m):

        """
        首选项设置栏
        """
        if m.text() == "首选项...":
            self.settings = view.setting.Ui_Form(public_info)
            self.settings.show()

    def open_helper(self, m):
        """
        帮助栏
        """
        if m.text() == "使用教程":
            self.use_introduction = view.introduce.Ui_Form()
            self.use_introduction.show()
        elif m.text() == "关于Easy_Cidaren":
            QtGui.QDesktopServices.openUrl(QtCore.QUrl('https://github.com/ularch/Easy_Cidaren'))
        elif m.text() == "关于作者":
            QtGui.QDesktopServices.openUrl(QtCore.QUrl('https://github.com/ularch'))
        elif m.text() == "获取token":
            self.get_token()
        elif m.text() == "导出日志文件":
            from log.log import export_logs
            export_logs(self)

    def play_music(self):
        """
        播放提示音乐
        :return:
        """
        # 检查是否设置了自定义音乐路径
        if hasattr(public_info, 'music_path') and public_info.music_path:
            # 检查文件是否存在
            if os.path.exists(public_info.music_path):
                music_path = public_info.music_path
            else:
                # 文件不存在，使用默认音乐
                music_path = path + "/assets/music.wav"
                main.logger.error("自定义音乐文件不存在，使用默认音乐")
        else:
            # 使用默认音乐
            music_path = path + "/assets/music.wav"
        try:
            # 首先尝试使用playsound播放
            playsound(music_path)
        except Exception as e:
            # playsound播放失败时，使用winsound播放
            main.logger.info(f"playsound播放失败，使用winsound播放: {e}")
            try:
                winsound.PlaySound(music_path, winsound.SND_FILENAME)
            except Exception as e2:
                main.logger.info(f"winsound播放失败: {e2}")

    def get_token(self):
        exe_path = path + "\\get token\\词达人token获取.exe"
        try:
            subprocess.Popen([exe_path], shell=True)
        except:
            main.logger.info("词达人token获取.exe打开失败")

    def set_ui_enabled(self, enabled):
        """启用或禁用主界面控件"""
        # 禁用/启用登录相关控件
        self.token_input.setEnabled(enabled)
        self.login.setEnabled(enabled)
        
        # 禁用/启用任务相关控件
        self.learn_task.setEnabled(enabled)
        self.test_task.setEnabled(enabled)
        self.task_list.setEnabled(enabled)
        self.start_task.setEnabled(enabled)
        
        # 菜单栏的启用/禁用
        self.menu.setEnabled(enabled)
        self.menu_2.setEnabled(enabled)
        
        # 特别处理停止任务按钮 - 始终启用
        if not enabled:
            self.stop_task.setEnabled(True)

    def stop_current_task(self):
        """停止当前任务"""
        if self.task_worker and self.task_worker.isRunning():
            reply = QMessageBox.question(
                self, 
                "确认停止", 
                "确定要停止当前任务吗？", 
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, 
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # 停止工作线程
                self.task_worker.stop()
                self.task_worker.quit()
                self.task_worker.wait()
                
                # 重新启用所有控件
                self.set_ui_enabled(True)
                
                self.update_output_info("任务已手动停止")
                QMessageBox.information(self, "任务停止", "任务已成功停止")
                
                # 清理工作线程
                self.task_worker.deleteLater()
                self.task_worker = None
                main.logger.info("任务已手动停止")
        else:
            return


if __name__ == '__main__':
    main = Log("main")
    main.logger.info("初始化主页面")
    # 路径
    path = os.path.dirname(__file__)
    # 初始化公共组件
    main.logger.info("初始化公共组件")
    public_info = PublicInfo(path)
    main.logger.info(f"当前版本号：{public_info.version}")

    # 创建窗口对象
    app = QApplication(sys.argv)
    # 首次使用提示
    if not public_info.read:
        main.logger.info("显示首次使用提示页面")
        note = view.first_note.Ui_Form(public_info)
        note.show()
        app.exec()

    # 判断更新
    if public_info.version < get_update() and public_info.know_version < get_update():
        update = view.update.Ui_Form(public_info)
        update.show()
        app.exec()

    # 主界面
    try:
        ui = UiMainWindow()
        ui.show()
        app.exec()
    except Exception as e:
        main.logger.error(e)
        main.logger.error("程序异常")
        ui = view.error.Ui_Form()
        ui.show()
        app.exec()
