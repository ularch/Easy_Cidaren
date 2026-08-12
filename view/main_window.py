import os
import subprocess
import threading

import winsound
from playsound import playsound

from PyQt6.QtGui import QAction, QIcon
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QMainWindow, QApplication, QMessageBox

import api.request_header as requests
import view.setting, view.introduce, view.error
from api.login import verify_token
from api.main_api import get_class_task
from util.basic_util import get_all_task
from publicInfo.publicInfo import PublicInfo
from api.geuuid import get_uuid


class UiMainWindow(QMainWindow):
    output = "软件初始化成功！"

    def __init__(self, public_info, root_path, main_logger, task_worker_class):
        super(UiMainWindow, self).__init__()
        self.public_info = public_info
        self.root_path = root_path
        self.main_logger = main_logger
        self.task_worker_class = task_worker_class
        self.token = ''
        self.task_worker = None
        self._batch_mode = False
        self.setupUi(self)

    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setFixedSize(720, 370)
        icon_path = os.path.join(self.root_path, 'assets', 'icon.ico')
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
        self.learn_task.clicked.connect(self.get_task_list)
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.learn_task)
        self.test_task = QtWidgets.QRadioButton(parent=self.formLayoutWidget)
        self.test_task.setObjectName("test_task")
        self.test_task.clicked.connect(self.get_task_list)
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.test_task)
        self.task_list = QtWidgets.QTableWidget(parent=self.centralwidget)
        self.task_list.setGeometry(QtCore.QRect(20, 170, 291, 80))
        self.task_list.setObjectName("task_list")
        # 四列：单选框 | 任务名 | 进度 | 得分，每列左对齐
        self.task_list.setColumnCount(4)
        self.task_list.verticalHeader().setVisible(False)
        self.task_list.horizontalHeader().setVisible(False)
        self.task_list.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.task_list.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.task_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.task_list.setShowGrid(False)
        self.task_list.setWordWrap(False)
        self.task_list.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.task_list.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.task_list.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.task_list.horizontalHeader().setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeMode.Fixed)
        self.task_list.setColumnWidth(0, 30)
        self.task_list.setColumnWidth(2, 55)
        self.task_list.setColumnWidth(3, 75)
        # 目标任务选择：互斥单选框，勾选时同步选中表格行
        self.task_radio_group = QtWidgets.QButtonGroup(self)
        self.task_radio_group.setExclusive(True)
        self.task_list.itemClicked.connect(self._on_task_item_clicked)
        self.start_task = QtWidgets.QPushButton(parent=self.centralwidget)
        self.start_task.setGeometry(QtCore.QRect(20, 260, 85, 24))
        self.start_task.setObjectName("start_task")
        self.start_task.clicked.connect(self.start)
        self.batch_start = QtWidgets.QPushButton(parent=self.centralwidget)
        self.batch_start.setGeometry(QtCore.QRect(115, 260, 85, 24))
        self.batch_start.setObjectName("batch_start")
        self.batch_start.setText("一键刷题")
        self.batch_start.clicked.connect(self.start_batch)
        self.stop_task = QtWidgets.QPushButton(parent=self.centralwidget)
        self.stop_task.setGeometry(QtCore.QRect(210, 260, 85, 24))
        self.stop_task.setObjectName("stop_task")
        self.stop_task.clicked.connect(self.stop_current_task)
        # 答题进度条
        self.progress_bar = QtWidgets.QProgressBar(parent=self.centralwidget)
        self.progress_bar.setGeometry(QtCore.QRect(20, 290, 291, 20))
        self.progress_bar.setObjectName("progress_bar")
        self.progress_bar.setValue(0)
        # 进度文字（已完成数/总数）
        self.progress_label = QtWidgets.QLabel(parent=self.centralwidget)
        self.progress_label.setGeometry(QtCore.QRect(320, 290, 50, 20))
        self.progress_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.follow_output = QtWidgets.QRadioButton(parent=self.centralwidget)
        self.follow_output.setGeometry(QtCore.QRect(607, 19, 101, 16))
        self.follow_output.setObjectName("follow_output")
        self.follow_output.setChecked(True)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setEnabled(True)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 720, 33))
        self.menubar.setObjectName("menubar")
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

        self.menu_separator = QtWidgets.QFrame(parent=MainWindow)
        self.menu_separator.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.menu_separator.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.menu_separator.setObjectName("menu_separator")

        self.menu = QtWidgets.QMenu(parent=self.menubar)
        self.menu.setObjectName("menu")
        self.menu_2 = QtWidgets.QMenu(parent=self.menubar)
        self.menu_2.setObjectName("menu_2")
        MainWindow.setMenuBar(self.menubar)

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
        self.menu_get_token = QtWidgets.QMenu(parent=self.menubar)
        self.menu_get_token.setObjectName("menu_get_token")
        self.action_builtin = QtGui.QAction(parent=MainWindow)
        self.action_builtin.setObjectName("action_builtin")
        self.action_third_party = QtGui.QAction(parent=MainWindow)
        self.action_third_party.setObjectName("action_third_party")
        self.action_8 = QtGui.QAction(parent=MainWindow)
        self.action_8.setObjectName("action_8")
        self.action_open_logs = QtGui.QAction(parent=MainWindow)
        self.action_open_logs.setObjectName("action_open_logs")
        self.action_about = QtGui.QAction(parent=MainWindow)
        self.action_about.setObjectName("action_about")
        self.menu.addAction(self.action)
        self.menu.triggered[QAction].connect((self.open_settings))
        self.menu_2.addAction(self.action_4)
        self.menu_2.addSeparator()
        self.menu_2.addAction(self.action_6)
        self.menu_2.addAction(self.action_7)
        self.menu_2.addAction(self.action_about)
        self.menu_2.addSeparator()
        self.menu_2.addMenu(self.menu_get_token)
        self.menu_get_token.addAction(self.action_builtin)
        self.menu_get_token.addAction(self.action_third_party)
        self.action_open_logs.setText("导出日志文件")
        self.menu_2.addAction(self.action_open_logs)
        self.menu_2.triggered[QAction].connect((self.open_helper))
        self.menubar.addAction(self.menu.menuAction())
        self.menubar.addAction(self.menu_2.menuAction())
        self.retranslate_ui(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslate_ui(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(
            _translate("MainWindow", f"EasyCidaren_v{self.public_info.version}（github免费开源，严禁倒卖，作者ularch）"))
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
        self.action_6.setText(_translate("MainWindow", "项目首页"))
        self.action_7.setText(_translate("MainWindow", "作者首页"))
        self.menu_get_token.setTitle(_translate("MainWindow", "获取 token"))
        self.action_builtin.setText(_translate("MainWindow", "内置"))
        self.action_third_party.setText(_translate("MainWindow", "第三方"))
        self.action_open_logs.setText(_translate("MainWindow", "导出日志文件"))
        self.action_about.setText(_translate("MainWindow", "关于"))

    def update_output_info(self, info):
        self.output = self.output + f"\n{info}"
        self.output_info.setHtml(f"<pre>{self.output}</pre>")
        if self.follow_output.isChecked():
            scrollbar = self.output_info.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def token_login(self):
        self.warn_info.setText("")
        input_text = self.token_input.text()
        if '\n' in input_text:
            self.token = input_text.split('\n')[0].strip()
        else:
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
                self.update_output_info("登录成功！")
                student_name = result['data']['user_info']['student_name']
                student_code = result['data']['user_info']['student_code']
                school_name = result['data']['user_info']['school_name']
                class_name = result['data']['user_info']['class_name']
                self.user_info.setText(f"{student_name} {student_code} {school_name} {class_name}")
                self.update_output_info("用户信息获取成功！")
                requests.set_token(self.token)
                self.get_task_list()

    def get_task_list(self):
        self.task_list.setRowCount(0)
        if not self.user_info.text() == "未获取":
            if self.learn_task.isChecked():
                self.public_info._task_choices = 1
                self.update_output_info("开始获取：班级学习任务")
                self.main_logger.info("开始获取：班级学习任务")
            elif self.test_task.isChecked():
                self.public_info._task_choices = 2
                self.update_output_info("开始获取：班级测试任务")
                self.main_logger.info("开始获取：班级测试任务")
            self.public_info.class_task = []
            PublicInfo.task_type = 'ClassTask'
            PublicInfo.task_type_int = 2
            now_page = 1
            get_class_task(self.public_info, now_page)
            while self.public_info.task_total_count > now_page * 10:
                now_page += 1
                get_class_task(self.public_info, now_page)
            get_all_task(self.public_info)
            if not self.public_info.task_list == []:
                task_names = [task['task_name'] for task in self.public_info.task_list]
                self.main_logger.info(f'{task_names}')
                for task in self.public_info.task_list:
                    task_name = task['task_name']
                    progress = task.get('progress', 0)
                    score = task.get('score') or 0
                    over_status = task.get('over_status', 2)
                    row = self.task_list.rowCount()
                    self.task_list.insertRow(row)
                    # 左侧目标任务单选框（容器+布局使其在格内居中）
                    radio = QtWidgets.QRadioButton(self.task_list)
                    radio.clicked.connect(lambda checked, r=row: self._select_task_row(r))
                    self.task_radio_group.addButton(radio)
                    radio_container = QtWidgets.QWidget(self.task_list)
                    radio_layout = QtWidgets.QHBoxLayout(radio_container)
                    radio_layout.setContentsMargins(0, 0, 0, 0)
                    radio_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                    radio_layout.addWidget(radio)
                    self.task_list.setCellWidget(row, 0, radio_container)
                    score_text = str(score)
                    if over_status == 1:
                        score_text += " (未开始)"
                    # 任务数据存入三个数据列单元格，点任意列都能取到任务
                    for col, text in enumerate([task_name, f"{progress}%", score_text], start=1):
                        cell = QtWidgets.QTableWidgetItem(text)
                        cell.setData(QtCore.Qt.ItemDataRole.UserRole, task)
                        # 已完成的任务显示绿色
                        if progress >= 100:
                            cell.setForeground(QtGui.QColor("green"))
                        # 未开始的任务显示灰色
                        elif over_status == 1:
                            cell.setForeground(QtGui.QColor("gray"))
                        self.task_list.setItem(row, col, cell)
                self.update_output_info("获取成功！")
            else:
                self.update_output_info("获取失败！没有任务！")

    def _select_task_row(self, row):
        """勾选单选框时同步选中表格行"""
        item = self.task_list.item(row, 1)
        if item:
            self.task_list.setCurrentItem(item)

    def _on_task_item_clicked(self, item):
        """点击任务行时自动勾选该行单选框"""
        try:
            row = item.row()
            widget = self.task_list.cellWidget(row, 0)
            radio = widget.findChild(QtWidgets.QRadioButton) if widget else None
            if radio and not radio.isChecked():
                radio.setChecked(True)
        except Exception as e:
            self.main_logger.error(f"选择任务行失败: {e}")

    def start(self):
        try:
            current_item = self.task_list.currentItem()
            if not self.public_info.task_list == [] and not self.public_info.class_task == [] and current_item:
                if self.learn_task.isChecked():
                    self.main_logger.info("开始班级学习任务")
                else:
                    self.main_logger.info("开始班级测试任务")
                task_info = current_item.data(QtCore.Qt.ItemDataRole.UserRole)
                task_name = task_info['task_name']
                self.public_info._task_name = task_name
                self.public_info.class_task = [task_info]
                self.update_output_info(f"开始任务{task_name}")
                reply = QMessageBox.question(self, f"开始任务{task_name}",
                                             f"确认开始任务{task_name}吗？\n任务开始后，主页面将无法操作，可点击“中止任务”按钮手动中止任务\n系统将在后台自动执行刷题\n运行期间请勿关闭程序窗口",
                                             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                             QMessageBox.StandardButton.Yes)
                if reply == QMessageBox.StandardButton.Yes:
                    task_info = self.public_info.class_task[0]
                    self.public_info.is_self_built = False
                    self._batch_mode = False
                    self.set_ui_enabled(False)
                    self.task_worker = self.task_worker_class([task_info], batch_mode=False)
                    self.task_worker.task_finished.connect(self.on_task_finished)
                    self.task_worker.task_error.connect(self.on_task_error)
                    self.task_worker.task_progress.connect(self.update_progress)
                    self.task_worker.task_notice.connect(self.on_task_notice)
                    self.task_worker.start()
                    self.update_output_info("任务已在后台开始执行...")
            else:
                self.update_output_info("没有可执行的任务")
        except Exception as e:
            self.main_logger.error(f"运行出错，错误信息：{e}")
            self.update_output_info(f"运行出错，错误信息：{e}")

    def start_batch(self):
        """一键刷题：按顺序自动执行列表中所有未完成的任务"""
        try:
            if self.user_info.text() == "未获取":
                self.update_output_info("请先登录后再使用一键刷题")
                return
            tasks = [t for t in self.public_info.task_list if t.get('progress', 0) < 100]
            if not tasks:
                self.update_output_info("没有可执行的任务（已完成的任务已跳过）")
                return
            skipped = len(self.public_info.task_list) - len(tasks)
            reply = QMessageBox.question(
                self,
                "一键刷题",
                f"将按顺序自动执行 {len(tasks)} 个未完成任务"
                + (f"（已跳过 {skipped} 个已完成任务）" if skipped else "")
                + "\n任务开始后，主页面将无法操作，可点击“中止任务”按钮手动中止任务\n运行期间请勿关闭程序窗口",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
            self.public_info.is_self_built = False
            self._batch_mode = True
            self.set_ui_enabled(False)
            self.task_worker = self.task_worker_class(tasks, batch_mode=True)
            self.task_worker.task_finished.connect(self.on_task_finished)
            self.task_worker.task_error.connect(self.on_task_error)
            self.task_worker.task_progress.connect(self.update_progress)
            self.task_worker.task_notice.connect(self.on_task_notice)
            self.task_worker.batch_finished.connect(self.on_batch_finished)
            self.task_worker.start()
            self.update_output_info(f"开始一键刷题：共 {len(tasks)} 个任务")
        except Exception as e:
            self.main_logger.error(f"一键刷题启动失败: {e}")
            self.update_output_info(f"运行出错，错误信息：{e}")

    def update_progress(self, progress_text):
        """
        更新进度
        :param progress_text:
        :return:
        """
        parts = progress_text.split('/')
        if len(parts) == 2:
            try:
                done = int(parts[0])
                total = int(parts[1])
                self.progress_bar.setMaximum(total)
                self.progress_bar.setValue(done)
                self.progress_label.setText(progress_text)
            except ValueError:
                pass

    def on_task_finished(self, message):
        """
        任务完成
        :param message:
        :return:
        """
        self.main_logger.info(f'{message}')
        if self._batch_mode:
            # 批量模式：不弹窗，输出信息并刷新任务列表，自动继续下一个任务
            self.update_output_info(message)
            self.progress_bar.setValue(0)
            self.progress_label.setText("")
            self.get_task_list()
            return
        self.set_ui_enabled(True)
        self.progress_bar.setValue(self.progress_bar.maximum())
        music_thread = threading.Thread(target=self.play_music)
        music_thread.start()
        QtWidgets.QMessageBox.information(self, "任务完成！", message)
        task_name = self.public_info.class_task[0]['task_name']
        self.update_output_info(f"{task_name}运行完成")
        self.update_output_info(message)
        # 自动刷新任务列表，显示最新进度和得分
        self.get_task_list()
        if self.task_worker:
            self.task_worker.deleteLater()
            self.task_worker = None

    def on_batch_finished(self, summary):
        """一键刷题全部任务执行结束"""
        self._batch_mode = False
        self.set_ui_enabled(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("")
        self.main_logger.info(summary)
        self.update_output_info(summary)
        self.get_task_list()
        music_thread = threading.Thread(target=self.play_music)
        music_thread.start()
        QtWidgets.QMessageBox.information(self, "一键刷题完成", summary)
        if self.task_worker:
            self.task_worker.deleteLater()
            self.task_worker = None

    def on_task_notice(self, message):
        """任务执行中的提示信息（重试/跳过等）"""
        self.main_logger.info(message)
        self.update_output_info(message)

    def on_task_error(self, error_message):
        """
        任务出错
        :param error_message:
        :return:
        """
        self._batch_mode = False
        self.set_ui_enabled(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("")
        self.main_logger.error(f"运行出错，错误信息：{error_message}")
        self.update_output_info(f"运行出错，错误信息：{error_message}")
        error = view.error.Ui_Form()
        error.exec()
        if self.task_worker:
            self.task_worker.deleteLater()
            self.task_worker = None

    def open_settings(self, m):
        if m.text() == "首选项...":
            self.settings = view.setting.Ui_Form(self.public_info)
            self.settings.show()

    def open_helper(self, m):
        if m.text() == "使用教程":
            self.use_introduction = view.introduce.Ui_Form()
            self.use_introduction.show()
        elif m.text() == "关于Easy_Cidaren":
            QtGui.QDesktopServices.openUrl(QtCore.QUrl('https://github.com/ularch/Easy_Cidaren'))
        elif m.text() == "关于作者":
            QtGui.QDesktopServices.openUrl(QtCore.QUrl('https://github.com/ularch'))
        elif m.text() == "关于":
            uid = get_uuid()
            msg_box = QMessageBox()
            msg_box.setWindowTitle("关于")
            msg_box.setText(f"EasyCidaren\n版本: {self.public_info.version}\n作者: ularch\n开源地址: https://github.com/ularch/Easy_Cidaren\n唯一设备ID: {uid}")
            msg_box.setIcon(QMessageBox.Icon.Information)
            copy_button = msg_box.addButton("复制", QMessageBox.ButtonRole.ActionRole)
            close_button = msg_box.addButton("关闭", QMessageBox.ButtonRole.AcceptRole)
            msg_box.setDefaultButton(close_button)
            msg_box.exec()
            if msg_box.clickedButton() == copy_button:
                clipboard = QApplication.clipboard()
                info_text = f"EasyCidaren\n版本: {self.public_info.version}\n作者: ularch\n开源地址: https://github.com/ularch/Easy_Cidaren\n唯一设备ID: {uid}"
                clipboard.setText(info_text)
                QMessageBox.information(self, "复制成功", "已将相关信息复制到剪贴板")
        elif m.text() == "第三方":
            self.get_token()
        elif m.text() == "内置":
            self.open_builtin_token_dialog()
        elif m.text() == "导出日志文件":
            from log.log import export_logs
            export_logs(self)

    def play_music(self):
        if hasattr(self.public_info, 'music_path') and self.public_info.music_path:
            if os.path.exists(self.public_info.music_path):
                music_path = self.public_info.music_path
            else:
                music_path = self.root_path + "/assets/music.wav"
                self.main_logger.error("自定义音乐文件不存在，使用默认音乐")
        else:
            music_path = self.root_path + "/assets/music.wav"
        try:
            playsound(music_path)
        except Exception as e:
            self.main_logger.info(f"playsound播放失败，使用winsound播放: {e}")
            try:
                winsound.PlaySound(music_path, winsound.SND_FILENAME)
            except Exception as e2:
                self.main_logger.info(f"winsound播放失败: {e2}")

    def get_token(self):
        exe_path = self.root_path + "\\get token\\词达人token获取.exe"
        try:
            subprocess.Popen([exe_path], shell=True)
        except:
            self.main_logger.info("词达人token获取.exe打开失败")

    def open_builtin_token_dialog(self):
        try:
            from view.builtin_token import BuiltinTokenDialog
            fetch_token_path = os.path.join(self.root_path, "get token", "fetch_token")
            if not os.path.exists(fetch_token_path):
                QMessageBox.critical(self, "错误", f"fetch_token 目录不存在：{fetch_token_path}")
                return
            dialog = BuiltinTokenDialog(parent=self, fetch_token_path=fetch_token_path)
            dialog.captured.connect(self.on_builtin_token_captured)
            dialog.exec()
        except ImportError as e:
            QMessageBox.critical(self, "错误", f"无法导入 builtin_token 模块：{e}")
            self.main_logger.error(f"导入 builtin_token 模块失败: {e}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开内置 token 获取功能失败：{e}")
            self.main_logger.error(f"打开内置 token 获取功能失败: {e}", exc_info=True)

    def on_builtin_token_captured(self, token):
        if token:
            self.token_input.setText(token)
            self.update_output_info("Token 已自动填充到输入框")
            self.main_logger.info("内置 token 捕获成功，已自动填充")
            reply = QMessageBox.question(
                self,
                "自动登录",
                "Token 已捕获成功！是否立即登录？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.token_login()

    def set_ui_enabled(self, enabled):
        self.token_input.setEnabled(enabled)
        self.login.setEnabled(enabled)
        self.learn_task.setEnabled(enabled)
        self.test_task.setEnabled(enabled)
        self.task_list.setEnabled(enabled)
        self.start_task.setEnabled(enabled)
        self.batch_start.setEnabled(enabled)
        self.menu.setEnabled(enabled)
        self.menu_2.setEnabled(enabled)
        if not enabled:
            self.stop_task.setEnabled(True)

    def stop_current_task(self):
        if self.task_worker and self.task_worker.isRunning():
            reply = QMessageBox.question(
                self,
                "确认停止",
                "确定要停止当前任务吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.task_worker.stop()
                self.task_worker.quit()
                self.task_worker.wait()
                self._batch_mode = False
                self.set_ui_enabled(True)
                self.progress_bar.setValue(0)
                self.progress_label.setText("")
                self.update_output_info("任务已手动停止")
                QMessageBox.information(self, "任务停止", "任务已安全停止")
                self.task_worker.deleteLater()
                self.task_worker = None
                self.main_logger.info("任务已手动停止")
        else:
            return
