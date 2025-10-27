import os
import sys
import threading

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QApplication, QDialog


class Ui_Form(QDialog):
    def __init__(self):
        super(Ui_Form, self).__init__()
        self.setupUi(self)

    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(400, 150)
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon.ico')
        if os.path.exists(icon_path):
            Form.setWindowIcon(QIcon(icon_path))
        self.setModal(True)  # 设置为模态对话框
        self.label = QtWidgets.QLabel(parent=Form)
        self.label.setGeometry(QtCore.QRect(20, 20, 351, 80))
        self.label.setObjectName("label")
        
        # 添加关闭按钮
        self.closeButton = QtWidgets.QPushButton(parent=Form)
        self.closeButton.setGeometry(QtCore.QRect(160, 110, 80, 24))
        self.closeButton.setObjectName("closeButton")
        
        # 连接关闭按钮的点击事件
        self.closeButton.clicked.connect(self.accept)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "任务停止"))
        self.label.setText(_translate("Form", "任务出现异常错误，已经停止运行，可通过控制台参看报错信息，\n"
                                              "可将完整报错信息发给作者，以便改进程序，\n"
                                              "可能会略微影响分数，刷题进度已保存，可尝试重试任务\n"
                                              "如遇到无法运行的情况，请将问题反馈至作者主页邮箱"))
        # 翻译关闭按钮文本
        self.closeButton.setText(_translate("Form", "关闭"))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    error = Ui_Form()
    error.show()
    app.exec()