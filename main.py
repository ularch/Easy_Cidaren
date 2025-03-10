import os
import threading

from PyQt6.QtGui import QAction
from playsound import playsound

import api.request_header as requests
import view.setting, view.introduce
from answer_questions.answer_questions import *
from api.basic_api import get_all_unit, get_unit_words, get_book_all_words
from api.login import verify_token
from api.main_api import get_exam, select_all_word, get_class_task, skip_exam
from log.log import Log
from publicInfo.publicInfo import PublicInfo
from util.basic_util import get_todo_task, extract_book_word, query_word_unit, get_choices_task
from util.handle_word_list import handle_word_result

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QMainWindow, QApplication, QMessageBox


class UiMainWindow(QMainWindow):
    """
    主菜单ui
    """
    output = "软件初始化成功！"

    def __init__(self):
        super(UiMainWindow, self).__init__()
        self.token = ''
        self.setupUi(self)

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setFixedSize(720, 280)
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
        self.stop_task.clicked.connect(stop_task)
        self.follow_output = QtWidgets.QRadioButton(parent=self.centralwidget)
        self.follow_output.setGeometry(QtCore.QRect(607, 19, 101, 16))
        self.follow_output.setObjectName("follow_output")
        self.follow_output.setChecked(True)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setEnabled(True)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 720, 33))
        self.menubar.setObjectName("menubar")
        self.menu = QtWidgets.QMenu(parent=self.menubar)
        self.menu.setObjectName("menu")
        self.menu_2 = QtWidgets.QMenu(parent=self.menubar)
        self.menu_2.setObjectName("menu_2")
        MainWindow.setMenuBar(self.menubar)
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
        self.menu.addAction(self.action)
        # 设置菜单名项点击事件
        self.menu.triggered[QAction].connect((self.open_settings))
        self.menu_2.addAction(self.action_4)
        self.menu_2.addSeparator()
        self.menu_2.addAction(self.action_6)
        self.menu_2.addAction(self.action_7)
        # 帮助菜单点击事件
        self.menu_2.triggered[QAction].connect((self.open_helper))
        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.menu_2.menuAction())

        self.retranslate_ui(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslate_ui(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "词达人自动答题"))
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
        self.stop_task.setText(_translate("MainWindow", "结束任务"))
        self.follow_output.setText(_translate("MainWindow", "随新消息滚动"))
        self.menu.setTitle(_translate("MainWindow", "设置"))
        self.menu_2.setTitle(_translate("MainWindow", "帮助"))
        self.action.setText(_translate("MainWindow", "首选项..."))
        self.action_4.setText(_translate("MainWindow", "使用教程"))
        self.action_6.setText(_translate("MainWindow", "关于词达人自动答题"))
        self.action_7.setText(_translate("MainWindow", "关于作者"))

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
        self.token = self.token_input.text().rstrip('\n')
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
        if not public_info.class_task == []:
            main.logger.info("开始任务")
            # 获取所选任务名称
            task_name = self.task_list.currentText()
            task_index = self.task_list.currentIndex()
            get_choices_task(public_info, task_name)
            ui.update_output_info(f"开始任务{task_name}")
            # 开始任务 启动等待页面
            reply = QMessageBox.question(self, f"开始任务{task_name}",
                                         f"确认开始任务{task_name}吗？\n任务开始后，主页面将消失，系统将在后台自动刷题\n期间请勿关闭cmd窗口，关闭cmd窗口将结束运行\n如果刷题过程中程序报错，请重新打开软件重试",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.Yes)
            if reply == QMessageBox.StandardButton.Yes:
                # 隐藏主页面
                self.hide()
                # 关闭自建任务
                task_info = public_info.class_task[0]
                public_info.is_self_built = False
                complete_test(task_info)
                # 任务完成提示音乐
                music_thread = threading.Thread(target=self.play_music)
                music_thread.start()
                # 任务完成 关闭等待页面
                QtWidgets.QMessageBox.information(self, "任务完成！", f"已完成{task_name}")
                main.logger.info('运行完成')
                ui.update_output_info(f"{task_name}运行完成")
                # 删除已完成任务
                self.task_list.removeItem(task_index)
                # 显示主页面
                self.show()

    def open_settings(self, m):
        """
        设置栏
        """
        if m.text() == "首选项...":
            self.settings = view.setting.Ui_Form(public_info)
            self.settings.show()

    def open_helper(self, m):
        """
        帮助栏
        """
        if m.text() == "使用教程":
            self.use_introduction = view.introduce.Ui_Form(public_info)
            self.use_introduction.show()
        elif m.text() == "关于词达人自动答题":
            QtGui.QDesktopServices.openUrl(QtCore.QUrl('https://github.com/ularch/Cidaren_Automatic_Answer'))
        elif m.text() == "关于作者":
            QtGui.QDesktopServices.openUrl(QtCore.QUrl('https://github.com/ularch'))

    def play_music(self):
        playsound(path + "\\view\\music.mp3")

def stop_task():
    """
    结束任务
    """
    quit()


def class_task_answer():
    """
    测试任务及自建任务
    """
    token = PublicInfo.token
    # 获取第一个试题
    get_exam(public_info)
    public_info.topic_code = public_info.exam['topic_code']
    main.logger.info("开始答题")
    while True:
        main.logger.info("获取题目类型")
        if public_info.exam == 'complete':
            # unit complete skip next unit
            break
        mode = public_info.exam['topic_mode']
        main.logger.info(f'题目类型{mode}')
        if mode == 0:
            # skip read cord
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


def complete_test(task_info: dict):
    """
    完成班级任务
    :param task_info: 任务信息
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
            # get all the words for the book
        get_book_all_words(public_info)
        # extract word
        extract_book_word(public_info)
        # answer
        class_task_answer()
    else:
        # 班级自学任务
        if task_info['task_type'] == 1:
            main.logger.info('开始班级自学任务')
            complete_practice(public_info.now_unit, unit_progress, task_info['task_id'])
        else:
            # 班级测试任务
            main.logger.info('开始班级测试任务')
            # 获取单元所有单词
            get_unit_words(public_info)
            handle_word_result(public_info)
            public_info.task_id = task_info['task_id']
            class_task_answer()


def complete_practice(unit: str, progress: int, task_id=None):
    """
    班级任务和自学共用
    :param task_id: 任务id
    :param unit:  单元名称
    :param progress: 单元进度
    :return: None
    """
    main.logger.info(f"获取该{unit}单元的单词")
    public_info.now_unit = unit
    public_info.task_id = task_id
    # get all the words in the unit
    get_unit_words(public_info)
    main.logger.info("处理words")
    handle_word_result(public_info)
    main.logger.info("选择该单元所有单词")
    # {"CET4_pre:CET4_pre_10":["survey","apply","defasdfa"]} word
    # not complete unit choice all word
    if (progress < 2 and public_info.get_word_list_result['data']['exist_little_task'] != 1) or \
            public_info.get_word_list_result['data']['exist_little_task'] == 2:
        select_all_word({f"{public_info.course_id}:{unit}": public_info.word_list}, public_info.task_id)
    # get first exam
    get_exam(public_info)
    public_info.topic_code = public_info.exam['topic_code']
    main.logger.info("开始答题")
    # topic_mode 题型
    while True:
        main.logger.info("获取题目类型")
        if public_info.exam == 'complete':
            main.logger.info('该单元已完成')
            # 当前单元已完成
            break
        mode = public_info.exam['topic_mode']
        # handle answer (choice)
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


if __name__ == '__main__':
    import sys

    main = Log("main")
    main.logger.info("初始化主页面")
    # 路径
    path = os.path.dirname(__file__)
    # 初始化公共组件
    main.logger.info("初始化公共组件")
    public_info = PublicInfo(path)

    # 创建窗口对象
    app = QApplication(sys.argv)
    ui = UiMainWindow()
    ui.show()
    app.exec()