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
        Form.resize(400, 200)
        # 固定窗口大小，禁止缩放
        Form.setFixedSize(400, 200)
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
                                            "本软件开源(https://github.com/ularch/Easy_Cidaren)且免费，任何人都可以直接下载并使用，Easy_Cidaren 不会在任何平台对软件本体及源码进行交易售卖、收取费用等活动（比如：咸鱼、淘宝、哔哩哔哩）。<br><strong>如果你是花钱购买的本软件，请及时退款并举报商家。<strong>"
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