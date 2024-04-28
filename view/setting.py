from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QWidget


class Ui_Form(QWidget):
    def __init__(self, public_info):
        super(Ui_Form, self).__init__()
        # 获取时间间隔
        self.public_info = public_info
        self._min_time = self.public_info.min_time
        self._max_time = self.public_info.max_time
        self.setupUi(self)

    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(400, 342)
        self.tabWidget = QtWidgets.QTabWidget(parent=Form)
        self.tabWidget.setGeometry(QtCore.QRect(20, 20, 361, 261))
        self.tabWidget.setObjectName("tabWidget")
        self.tab_1 = QtWidgets.QWidget()
        self.tab_1.setObjectName("tab_1")
        self.groupBox = QtWidgets.QGroupBox(parent=self.tab_1)
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
        self.label.setToolTip("设置自动刷题时两道题之间的最短时间间隔")
        self.verticalLayout.addWidget(self.label)
        self.min_time = QtWidgets.QSpinBox(parent=self.verticalLayoutWidget)
        self.min_time.setValue(self._min_time)
        self.min_time.setObjectName("min_time")
        self.verticalLayout.addWidget(self.min_time)
        self.label_2 = QtWidgets.QLabel(parent=self.verticalLayoutWidget)
        self.label_2.setObjectName("label_2")
        self.label_2.setToolTip("设置自动刷题时两道题之间的最长时间间隔")
        self.verticalLayout.addWidget(self.label_2)
        self.max_time = QtWidgets.QSpinBox(parent=self.verticalLayoutWidget)
        self.max_time.setValue(self._max_time)
        self.max_time.setObjectName("spinBox_2")
        self.verticalLayout.addWidget(self.max_time)
        self.tabWidget.addTab(self.tab_1, "")
        # self.tab_2 = QtWidgets.QWidget()
        # self.tab_2.setEnabled(True)
        # self.tab_2.setObjectName("tab_2")
        # self.tabWidget.addTab(self.tab_2, "")
        self.horizontalLayoutWidget = QtWidgets.QWidget(parent=Form)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(140, 310, 239, 31))
        self.horizontalLayoutWidget.setObjectName("horizontalLayoutWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.confirmBtn = QtWidgets.QPushButton(parent=self.horizontalLayoutWidget)
        self.confirmBtn.setObjectName("pushButton_2")
        self.confirmBtn.clicked.connect(self.confirm)
        self.horizontalLayout.addWidget(self.confirmBtn)
        self.cancelBtn = QtWidgets.QPushButton(parent=self.horizontalLayoutWidget)
        self.cancelBtn.setObjectName("pushButton")
        self.cancelBtn.clicked.connect(self.cancel)
        self.horizontalLayout.addWidget(self.cancelBtn)
        self.inputBtn = QtWidgets.QPushButton(parent=self.horizontalLayoutWidget)
        self.inputBtn.setObjectName("pushButton_3")
        # 点击应用事件
        self.inputBtn.clicked.connect(self.input)
        self.horizontalLayout.addWidget(self.inputBtn)
        self.warn_info = QtWidgets.QLabel(parent=Form)
        self.warn_info.setGeometry(QtCore.QRect(30, 290, 341, 20))
        self.warn_info.setStyleSheet("color:rgb(255, 0, 0);")
        self.warn_info.setText("")
        self.warn_info.setObjectName("label_3")

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
        # self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("Form", "答题设置"))
        self.confirmBtn.setText(_translate("Form", "确认"))
        self.cancelBtn.setText(_translate("Form", "取消"))
        self.inputBtn.setText(_translate("Form", "应用"))

    def confirm(self):
        import main
        self.warn_info.clear()
        if self.max_time.value() >= self.min_time.value():
            min_time = self.min_time.value()
            max_time = self.max_time.value()
            self.public_info.input_info(min_time, max_time)
            self.close()
        else:
            self.warn_info.setText("修改失败！最长间隔不得短于最短间隔！")

    def cancel(self):
        self.close()

    def input(self):
        import main
        self.warn_info.clear()
        if self.max_time.value() >= self.min_time.value():
            min_time = self.min_time.value()
            max_time = self.max_time.value()
            self.public_info.input_info(min_time, max_time)
        else:
            self.warn_info.setText("修改失败！最长间隔不得短于最短间隔！")
