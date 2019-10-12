#coding=utf-8

from PyQt5.QtWidgets import QListView, QMenu, QAction
import webbrowser
from PyQt5.QtGui import QIcon

from ListModel import ListModel
from PyQt5.QtCore import QObject,pyqtSignal

class VGSignal(QObject):
    ps = pyqtSignal(str)

vgs = VGSignal()

class ListView(QListView):

    def __init__(self,parent):
        super().__init__(parent=parent)
        self.m_pModel = ListModel([])
        self.setModel(self.m_pModel)
        
    def contextMenuEvent(self, event):
        hitIndex = self.indexAt(event.pos()).column()
        if hitIndex > -1:
            pmenu = QMenu(self)
            pDownloadAct = QAction(QIcon('logo.jpg'),"抓取微博",pmenu)
            pmenu.addAction(pDownloadAct)
            pDownloadAct.triggered.connect(self.doScrapy)
            pOpenMenu = QAction(QIcon('logo.jpg'),"在浏览器中打开" ,pmenu)
            pmenu.addAction(pOpenMenu)

            pOpenMenu.triggered.connect(self.openInBrowser)


            pmenu.popup(self.mapToGlobal(event.pos()))

    def clearData(self):
        self.m_pModel = ListModel([])
        self.setModel(self.m_pModel)

    def openInBrowser(self):
        index = self.currentIndex().row()
        url = "https://weibo.com/u/{}".format(self.m_pModel.getItem(index).get('uid'))
        print(url)
        webbrowser.open(url)

    
    def doScrapy(self):
        global vgs
        index = self.currentIndex().row()
        vgs.ps.emit(self.m_pModel.getItem(index).get('uid'))
        print(index)


    def addItem(self, pitem):
        self.m_pModel.addItem(pitem)
