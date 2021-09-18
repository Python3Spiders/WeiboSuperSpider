# -*- coding: utf-8 -*-
# author:           inspurer(月小水长)
# pc_type           lenovo
# create_time:      2019/8/16 11:40
# file_name:        MyDialog.py
# github            https://github.com/inspurer
# qq邮箱            2391527690@qq.com
# 微信公众号         月小水长(ID: inspurer)

from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import QDialogButtonBox,QLabel,QLineEdit,QCheckBox,QDialog

from PyQt5.QtGui import QIcon

class MyDialog(QDialog):

    def __init__(self, parent,info):
        super().__init__(parent)
        self.isChecked = True
        self.info = info
        self.initUI()

    def initUI(self):
        self.setWindowTitle('搜索设置')
        self.setWindowIcon(QIcon('logo.jpg'))
        self.resize(280, 200)

        self.l1 = QLabel(self.info, self)
        self.l1.setGeometry(30, 40, 100, 30)
        self.l1.setAlignment(Qt.AlignCenter)

        self.e1 = QLineEdit(self)
        self.e1.setGeometry(130, 40, 100, 25)

        self.l2 = QLabel('只抓取原创微博', self)
        self.l2.setGeometry(30, 100, 100, 30)
        self.l2.setAlignment(Qt.AlignCenter)

        # 创建复选框1，并默认选中，当状态改变时信号触发事件
        # self.checkBox1 = QCheckBox("&Checkbox1",self)
        self.checkBox1 = QCheckBox(self)
        self.checkBox1.setGeometry(170, 100, 80, 30)
        self.checkBox1.setChecked(True)
        self.checkBox1.stateChanged.connect(self.btnClicked)

        # 确定取消按钮

        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setGeometry(120,160,100,30)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel |QDialogButtonBox.Ok)

        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

    def btnClicked(self):
        self.isChecked = not self.isChecked
        print(self.e1.text(), self.isChecked)

    def getData(self):
        return [self.e1.text(), self.isChecked]