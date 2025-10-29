from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor, QIcon
from PyQt6.QtWidgets import QWidget

from log.log import Log


class Ui_Form(QWidget):
    def __init__(self, public_info):
        super(Ui_Form, self).__init__()
        # 获取用户配置
        self.public_info = public_info
        self._min_time = self.public_info.min_time
        self._max_time = self.public_info.max_time
        self._spend_min_time = self.public_info.spend_min_time
        self._spend_max_time = self.public_info.spend_max_time
        self._br_choices = self.public_info.br_choices
        self._play_music = self.public_info.play_music
        self.setupUi(self)

    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(400, 344)
        # 设置窗口图标
        import os
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon.ico')
        if os.path.exists(icon_path):
            Form.setWindowIcon(QIcon(icon_path))
        
        # 固定窗口大小，禁止缩放
        Form.setFixedSize(400, 344)
        
        self.tabWidget = QtWidgets.QTabWidget(parent=Form)
        self.tabWidget.setGeometry(QtCore.QRect(20, 20, 361, 261))
        self.tabWidget.setObjectName("tabWidget")
        self.tab_1 = QtWidgets.QWidget()
        self.tab_1.setObjectName("tab_1")
        self.scrollArea = QtWidgets.QScrollArea(parent=self.tab_1)
        self.scrollArea.setGeometry(QtCore.QRect(0, 0, 361, 231))
        self.scrollArea.setAutoFillBackground(False)
        self.scrollArea.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.scrollArea.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.scrollArea.setLineWidth(1)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        self.scrollAreaWidgetContents_1 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_1.setGeometry(QtCore.QRect(0, 0, 361, 231))
        self.scrollAreaWidgetContents_1.setMinimumSize(QtCore.QSize(0, 195))
        self.scrollAreaWidgetContents_1.setStyleSheet("background-color: palette(base);")
        self.scrollAreaWidgetContents_1.setObjectName("scrollAreaWidgetContents_1")
        self.groupBox = QtWidgets.QGroupBox(parent=self.scrollAreaWidgetContents_1)
        self.groupBox.setGeometry(QtCore.QRect(10, 10, 331, 121))
        self.groupBox.setObjectName("groupBox")
        self.verticalLayoutWidget = QtWidgets.QWidget(parent=self.groupBox)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(10, 20, 311, 92))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(parent=self.verticalLayoutWidget)
        self.label.setObjectName("label")
        self.label.setCursor(QCursor(Qt.CursorShape.WhatsThisCursor))
        self.label.setToolTip("设置每一道题之间提交的最短间隔（不推荐过短）")
        self.verticalLayout.addWidget(self.label)
        self.min_time = QtWidgets.QSpinBox(parent=self.verticalLayoutWidget)
        self.min_time.setObjectName("min_time")
        self.verticalLayout.addWidget(self.min_time)
        self.label_2 = QtWidgets.QLabel(parent=self.verticalLayoutWidget)
        self.label_2.setObjectName("label_2")
        self.label_2.setCursor(QCursor(Qt.CursorShape.WhatsThisCursor))
        self.label_2.setToolTip("设置每一道题之间提交的最长间隔（不推荐过短）")
        self.verticalLayout.addWidget(self.label_2)
        self.max_time = QtWidgets.QSpinBox(parent=self.verticalLayoutWidget)
        self.max_time.setObjectName("max_time")
        self.verticalLayout.addWidget(self.max_time)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents_1)
        self.tabWidget.addTab(self.tab_1, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setEnabled(True)
        self.tab_2.setObjectName("tab_2")
        self.scrollArea_2 = QtWidgets.QScrollArea(parent=self.tab_2)
        self.scrollArea_2.setGeometry(QtCore.QRect(0, 0, 361, 241))
        self.scrollArea_2.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.scrollArea_2.setWidgetResizable(True)
        self.scrollArea_2.setObjectName("scrollArea_2")
        self.scrollArea_2.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scrollAreaWidgetContents_2 = QtWidgets.QWidget()
        self.scrollAreaWidgetContents_2.setGeometry(QtCore.QRect(0, 0, 361, 300))  # 增加高度以容纳所有内容
        self.scrollAreaWidgetContents_2.setMinimumSize(QtCore.QSize(0, 300))  # 设置最小高度确保所有控件可见
        self.scrollAreaWidgetContents_2.setStyleSheet("background-color: palette(base);")
        self.scrollAreaWidgetContents_2.setObjectName("scrollAreaWidgetContents_2")
        self.groupBox_2 = QtWidgets.QGroupBox(parent=self.scrollAreaWidgetContents_2)
        self.groupBox_2.setGeometry(QtCore.QRect(10, 10, 331, 121))
        self.groupBox_2.setObjectName("groupBox_2")
        self.verticalLayoutWidget_2 = QtWidgets.QWidget(parent=self.groupBox_2)
        self.verticalLayoutWidget_2.setGeometry(QtCore.QRect(10, 20, 311, 92))
        self.verticalLayoutWidget_2.setObjectName("verticalLayoutWidget_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label_4 = QtWidgets.QLabel(parent=self.verticalLayoutWidget_2)
        self.label_4.setObjectName("label_4")
        self.label_4.setCursor(QCursor(Qt.CursorShape.WhatsThisCursor))
        self.label_4.setToolTip("设置每一题提交后台显示的最短答题用时")
        self.verticalLayout_2.addWidget(self.label_4)
        self.min_time_2 = QtWidgets.QSpinBox(parent=self.verticalLayoutWidget_2)
        self.min_time_2.setObjectName("min_time_2")
        self.verticalLayout_2.addWidget(self.min_time_2)
        self.label_5 = QtWidgets.QLabel(parent=self.verticalLayoutWidget_2)
        self.label_5.setObjectName("label_5")
        self.label_5.setCursor(QCursor(Qt.CursorShape.WhatsThisCursor))
        self.label_5.setToolTip("设置每一题提交后台显示的最长答题用时")
        self.verticalLayout_2.addWidget(self.label_5)
        self.max_time_2 = QtWidgets.QSpinBox(parent=self.verticalLayoutWidget_2)
        self.max_time_2.setObjectName("max_time_2")
        self.verticalLayout_2.addWidget(self.max_time_2)
        self.groupBox_3 = QtWidgets.QGroupBox(parent=self.scrollAreaWidgetContents_2)
        self.groupBox_3.setGeometry(QtCore.QRect(10, 140, 331, 150))  # 增加高度以容纳新选项
        self.groupBox_3.setObjectName("groupBox_3")
        self.br_checkBox = QtWidgets.QCheckBox(parent=self.groupBox_3)
        self.br_checkBox.setGeometry(QtCore.QRect(10, 20, 311, 16))
        self.br_checkBox.setChecked(True)
        self.br_checkBox.setObjectName("br_checkBox")
        # 为br压缩复选框添加鼠标悬停提示
        self.br_checkBox.setCursor(QCursor(Qt.CursorShape.WhatsThisCursor))
        self.br_checkBox.setToolTip("启用br压缩可以减小网络传输数据量，但某些旧系统可能不支持")
        # 添加播放音乐复选框
        self.playMusicCheckBox = QtWidgets.QCheckBox(parent=self.groupBox_3)
        self.playMusicCheckBox.setGeometry(QtCore.QRect(10, 50, 311, 16))
        self.playMusicCheckBox.setChecked(True)
        self.playMusicCheckBox.setObjectName("playMusicCheckBox")
        # 为播放音乐复选框添加鼠标悬停提示
        self.playMusicCheckBox.setCursor(QCursor(Qt.CursorShape.WhatsThisCursor))
        self.playMusicCheckBox.setToolTip("控制任务完成时是否播放提示音乐")
        
        # 添加自定义音乐路径输入框和默认音乐选项
        self.musicPathLineEdit = QtWidgets.QLineEdit(parent=self.groupBox_3)
        self.musicPathLineEdit.setGeometry(QtCore.QRect(10, 80, 220, 20))
        self.musicPathLineEdit.setObjectName("musicPathLineEdit")
        self.musicPathLineEdit.setPlaceholderText("自定义提示音乐文件路径（可选）")
        
        self.selectMusicBtn = QtWidgets.QPushButton(parent=self.groupBox_3)
        self.selectMusicBtn.setGeometry(QtCore.QRect(240, 80, 35, 20))
        self.selectMusicBtn.setObjectName("selectMusicBtn")
        self.selectMusicBtn.setText("...")
        
        self.defaultMusicBtn = QtWidgets.QPushButton(parent=self.groupBox_3)
        self.defaultMusicBtn.setGeometry(QtCore.QRect(280, 80, 40, 20))
        self.defaultMusicBtn.setObjectName("defaultMusicBtn")
        self.defaultMusicBtn.setText("默认")
        
        self.scrollArea_2.setWidget(self.scrollAreaWidgetContents_2)
        self.tabWidget.addTab(self.tab_2, "")
        self.horizontalLayoutWidget = QtWidgets.QWidget(parent=Form)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(140, 310, 239, 31))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.confirmBtn = QtWidgets.QPushButton(parent=self.horizontalLayoutWidget)
        self.confirmBtn.setObjectName("confirmBtn")
        self.horizontalLayout.addWidget(self.confirmBtn)
        self.cancelBtn = QtWidgets.QPushButton(parent=self.horizontalLayoutWidget)
        self.cancelBtn.setObjectName("cancelBtn")
        self.horizontalLayout.addWidget(self.cancelBtn)
        self.inputBtn = QtWidgets.QPushButton(parent=self.horizontalLayoutWidget)
        self.inputBtn.setObjectName("inputBtn")
        self.horizontalLayout.addWidget(self.inputBtn)
        self.warn_info = QtWidgets.QLabel(parent=Form)
        self.warn_info.setGeometry(QtCore.QRect(30, 290, 341, 20))
        self.warn_info.setStyleSheet("color:rgb(255, 0, 0);")
        self.warn_info.setText("")
        self.warn_info.setObjectName("warn_info")

        # 点击应用事件
        self.confirmBtn.clicked.connect(self.confirm)
        # 取消点击事件
        self.cancelBtn.clicked.connect(self.cancel)
        # 确定点击事件
        self.inputBtn.clicked.connect(self.input)
        # 选择音乐文件按钮事件
        self.selectMusicBtn.clicked.connect(self.select_music_file)
        # 默认音乐按钮事件
        self.defaultMusicBtn.clicked.connect(self.set_default_music)
        
        # 显示设置中的数据
        self.min_time.setValue(self._min_time)
        self.max_time.setValue(self._max_time)
        self.min_time_2.setValue(self._spend_min_time)
        self.max_time_2.setValue(self._spend_max_time)
        self.br_checkBox.setChecked(self._br_choices)
        self.playMusicCheckBox.setChecked(self._play_music)
        # 设置音乐路径
        self._music_path = self.public_info.music_path if hasattr(self.public_info, 'music_path') else ""
        self.musicPathLineEdit.setText(self._music_path)
        
        self.retranslateUi(Form)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "首选项"))
        self.groupBox.setTitle(_translate("Form", "刷题间隔"))
        self.label.setText(_translate("Form", "最短间隔："))
        self.min_time.setSuffix(_translate("Form", "    秒"))
        self.label_2.setText(_translate("Form", "最长间隔："))
        self.max_time.setSuffix(_translate("Form", "    秒"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_1), _translate("Form", "刷题设置"))
        self.groupBox_2.setTitle(_translate("Form", "答题用时"))
        self.label_4.setText(_translate("Form", "最短用时："))
        self.min_time_2.setSuffix(_translate("Form", "    秒"))
        self.label_5.setText(_translate("Form", "最长用时："))
        self.max_time_2.setSuffix(_translate("Form", "    秒"))
        self.groupBox_3.setTitle(_translate("Form", "系统设置（重启后生效）"))
        self.br_checkBox.setText(_translate("Form", "启用br压缩"))
        self.playMusicCheckBox.setText(_translate("Form", "任务完成时播放提示音乐"))
        self.selectMusicBtn.setText(_translate("Form", "..."))
        self.defaultMusicBtn.setText(_translate("Form", "默认"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("Form", "高级设置"))
        self.confirmBtn.setText(_translate("Form", "确认"))
        self.cancelBtn.setText(_translate("Form", "取消"))
        self.inputBtn.setText(_translate("Form", "应用"))

    def select_music_file(self):
        """
        选择自定义音乐文件
        """
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择音乐文件", 
            "", 
            "音频文件 (*.wav)"
        )
        if file_path:
            self.musicPathLineEdit.setText(file_path)

    def set_default_music(self):
        """
        设置为默认音乐
        """
        self.musicPathLineEdit.clear()
        self.warn_info.setStyleSheet("color: green;")
        self.warn_info.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.warn_info.setText("已恢复默认提示音乐设置！")

    def confirm(self):
        """
        点击确认事件
        :return:
        """
        if self.input():
            self.close()

    def cancel(self):
        self.close()

    def input(self):
        """
        点击应用事件
        """
        self.warn_info.clear()
        if self.max_time.value() < self.min_time.value():
            self.warn_info.setText("修改失败！最长间隔不得短于最短间隔！")
        elif self.max_time_2.value() < self.min_time_2.value():
            self.warn_info.setText("设置失败！最长用时不得短于最短用时！")
        else:
            min_time = self.min_time.value()
            max_time = self.max_time.value()
            min_time_2 = self.min_time_2.value()
            max_time_2 = self.max_time_2.value()
            br_choices = self.br_checkBox.isChecked()
            play_music = self.playMusicCheckBox.isChecked()
            music_path = self.musicPathLineEdit.text().strip()

            if br_choices:
                accept_encoding = 'gzip, deflate, br'
            else:
                accept_encoding = 'gzip, deflate'
            self.public_info.input_info(min_time, max_time, min_time_2, max_time_2, br_choices, accept_encoding, play_music, music_path)
            setting = Log("setting")
            setting.logger.info("修改首选项设置成功")
            return True
