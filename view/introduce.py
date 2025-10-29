import os
import sys

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QApplication


class Ui_Form(QWidget):
    def __init__(self):
        super(Ui_Form, self).__init__()
        self.setupUi(self)

    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(400, 200)
        # 固定窗口大小，禁止缩放
        Form.setFixedSize(400, 200)
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon.ico')
        if os.path.exists(icon_path):
            Form.setWindowIcon(QIcon(icon_path))
        self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.label = QtWidgets.QLabel(parent=Form)
        self.label.setGeometry(QtCore.QRect(20, 10, 361, 171))
        self.label.setObjectName("label")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "使用教程"))
        self.label.setText(_translate("Form", "1.获取用户token\n"
                                              "2. 在用户token栏输入token\n"
                                              "3.点击“登录”，系统会自动获取用户信息和待完成的学习任务\n"
                                              "4.可自由选择待获取的任务类型\n"
                                              "5.选中需要完成的任务\n"
                                              "6.点击“开始任务”即可自动完成\n"
                                              "7.在自动刷题时,可点击“中止任务 ”按钮手动停止当前任务"))