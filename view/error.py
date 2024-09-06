import os
import threading

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QWidget, QApplication
from playsound import playsound


class Ui_Form(QWidget):
    def __init__(self):
        super(Ui_Form, self).__init__()
        self.setupUi(self)

    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(400, 92)
        self.label = QtWidgets.QLabel(parent=Form)
        self.label.setGeometry(QtCore.QRect(20, 20, 351, 51))
        self.label.setObjectName("label")

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "程序停止"))
        self.label.setText(_translate("Form", "程序出现异常错误，已经停止运行，可通过控制台参看报错信息，\n"
                                              "可能会略微影响分数，刷题进度已保存，可重启软件重试，一般情况下重试即可正常刷题\n"
                                              "如遇到无法运行的情况，请将问题反馈至作者主页邮箱"))


def showError():
    music_thread = threading.Thread(target=play_music)
    music_thread.start()
    import sys
    app = QApplication(sys.argv)
    ui = Ui_Form()
    ui.show()
    app.exec()

def play_music():
    path = os.path.dirname(__file__)
    playsound(path + "\\music.mp3")

if __name__ == '__main__':
    showError()
