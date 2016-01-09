#!/usr/bin/env python2
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import logging
from lxml import etree

import PySide.QtCore as QtCore
import PySide.QtGui  as QtGui

from .WaNo       import WorkFlow

class WFEListWidget(QtGui.QListWidget):
    def __init__(self, parent=None, controls=[]):
        super(WFEListWidget, self).__init__(parent) 
        self.setDragEnabled(True)
        self.update_list(controls)

    def update_list(self, controls):
        for name, icon in controls:
            item = QtGui.QListWidgetItem(name)
            item.setIcon(QtGui.QIcon(icon))
            self.addItem(item)
        self.myHeight = 10
        self.sortItems()

    def sizeHint(self):
        return QtCore.QSize(100,self.myHeight)
        
class WFEWaNoListWidget(QtGui.QListWidget):
    def __init__(self, parent=None):
        super(WFEWaNoListWidget, self).__init__(parent) 
        self.setDragEnabled(True)
        self.myHeight = 10

    def update_list(self, wanos):
        self.clear()
        for wano in wanos:
            item = QtGui.QListWidgetItem(wano[0])
            self.addItem(item)
            item.WaNo = wano[1]
        self.myHeight = self.count()*10
        self.sortItems()
        
    def sizeHint(self):
        return QtCore.QSize(100,max(self.myHeight,200))
    
class WFEWorkflowistWidget(QtGui.QListWidget):
    def __init__(self, parent=None):
        super(WFEWorkflowistWidget, self).__init__(parent) 
        self.logger = logging.getLogger('WFEOG')
        self.setDragEnabled(True)
        self.myHeight = 10

    def update_list(self, workflows):
        self.clear()
        path = os.path.dirname(os.path.realpath(__file__))

        for element in workflows:
            item = QtGui.QListWidgetItem(element.name)
            item.WaNo = element
            self.addItem(item)
        self.myHeight = self.count()*10
        self.sortItems()

    def sizeHint(self):
        return QtCore.QSize(100,max(self.myHeight,100))
    
