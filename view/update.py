import os
import sys

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QApplication

import api.update as update


class Ui_Form(QWidget):
    def __init__(self, public_info):
        super(Ui_Form, self).__init__()
        self.public_info = public_info
        self.setupUi(self)

    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(400, 200)
        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'icon.ico')
        if os.path.exists(icon_path):
            Form.setWindowIcon(QIcon(icon_path))
        self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.label = QtWidgets.QLabel(parent=Form)
        self.label.setGeometry(QtCore.QRect(10, 10, 381, 16))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(parent=Form)
        self.label_2.setGeometry(QtCore.QRect(10, 30, 381, 20))
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred,
                                           QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label_2.sizePolicy().hasHeightForWidth())
        self.label_2.setSizePolicy(sizePolicy)
        self.label_2.setObjectName("label_2")
        self.confirmBtn = QtWidgets.QPushButton(parent=Form)
        self.confirmBtn.setGeometry(QtCore.QRect(310, 170, 75, 24))
        self.confirmBtn.setObjectName("pushButton")
        self.confirmBtn_2 = QtWidgets.QPushButton(parent=Form)
        self.confirmBtn_2.setGeometry(QtCore.QRect(220, 170, 75, 24))
        self.confirmBtn_2.setObjectName("pushButton_2")
        self.confirmBtn_3 = QtWidgets.QPushButton(parent=Form)
        self.confirmBtn_3.setGeometry(QtCore.QRect(130, 170, 75, 24))
        self.confirmBtn_3.setObjectName("pushButton_3")
        self.textBrowser = QtWidgets.QTextBrowser(parent=Form)
        self.textBrowser.setGeometry(QtCore.QRect(10, 50, 381, 111))
        self.textBrowser.setObjectName("textBrowser")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

        # 点击取消事件
        self.confirmBtn.clicked.connect(self.cancel)
        # 点击前往更新事件
        self.confirmBtn_2.clicked.connect(self.go_update)
        # 点击忽略事件
        self.confirmBtn_3.clicked.connect(self.ignore)

        update.logger.info("检测到更新")

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "软件更新"))
        self.label.setText(_translate("Form", f"当前版本：{self._now_version}"))
        self.label_2.setText(_translate("Form", f"最新版本：{self._new_version}"))
        self.confirmBtn.setText(_translate("Form", "取消"))
        self.confirmBtn_2.setText(_translate("Form", "前往更新"))
        self.confirmBtn_3.setText(_translate("Form", "忽略此版本"))
        self.textBrowser.setHtml(_translate("Form",
                                            "<!DOCTYPE HTML>"
                                            "<html><head><meta charset=\"utf-8\" /></head><body>"
                                            f"{self._update_detail}"
                                            "</body></html>"))

    def cancel(self):
        self.close()

    def go_update(self):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl('https://github.com/ularch/Cidaren_Automatic_Answer/releases/latest'))

    def ignore(self):
        self.public_info.ignore_version(self._new_version)
        self.close()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    update = Ui_Form()
    update.show()
    app.exec()
