import os
import sys

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QApplication


class Ui_Form(QWidget):
    def __init__(self, public_info):
        super(Ui_Form, self).__init__()
        self.public_info = public_info
        self.setupUi(self)

    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(400, 220)
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon.ico')
        if os.path.exists(icon_path):
            Form.setWindowIcon(QIcon(icon_path))
        self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.confirmBtn = QtWidgets.QPushButton(parent=Form)
        self.confirmBtn.setGeometry(QtCore.QRect(310, 170, 75, 24))
        self.confirmBtn.setObjectName("pushButton")
        self.confirmBtn_3 = QtWidgets.QPushButton(parent=Form)
        self.confirmBtn_3.setGeometry(QtCore.QRect(230, 170, 75, 24))
        self.confirmBtn_3.setObjectName("pushButton_3")
        self.textBrowser = QtWidgets.QTextBrowser(parent=Form)
        self.textBrowser.setGeometry(QtCore.QRect(10, 10, 381, 150))
        self.textBrowser.setObjectName("textBrowser")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

        # 点击关闭事件
        self.confirmBtn.clicked.connect(self.cancel)
        # 点击不再提醒事件
        self.confirmBtn_3.clicked.connect(self.ignore)


    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "温馨提示"))
        self.confirmBtn.setText(_translate("Form", "关闭"))
        self.confirmBtn_3.setText(_translate("Form", "不再提醒"))
        self.textBrowser.setHtml(_translate("Form",
                                            "<!DOCTYPE HTML>"
                                            "<html><head><meta charset=\"utf-8\" /></head><body>"
                                            "<h1>本软件为免费软件</h1>"
                                            "如果你从其他地方付费获得本软件，请立即退款并举报，<br>本软件完全免费并在github开源（https://github.com/ularch/Cidaren_Automatic_Answer），<br>本软件仅用于学习交流，任何后果由使用者承担"
                                            "</body></html>"))

    def cancel(self):
        self.close()

    def ignore(self):
        self.public_info.read_seen()
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    update = Ui_Form()
    update.show()
    app.exec()