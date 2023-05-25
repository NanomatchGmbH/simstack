import sys
import os
import copy
import logging

import Qt.QtCore as QtCore
import Qt.QtGui  as QtGui
import Qt.QtWidgets  as QtWidgets


class WaNoEditor(QtWidgets.QTabWidget):
    changedFlag = False

    def __init__(self,editor,parent=None):
        super(WaNoEditor, self).__init__(parent)
        self.logger = logging.getLogger('WFELOG')
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        self.editor = editor
        self.activeTabs = []

        self.tabWidget = self
        self.setTabsClosable(True)

        self.tabCloseRequested.connect(self.closeTab)

    @QtCore.Slot(int)
    def closeTab(self,myid):
        self.removeTab(myid)

    def paintEvent(self, event):
        super(WaNoEditor, self).paintEvent(event)
        if self.count() == 0:
            painter = QtGui.QPainter()
            painter.begin(self)
            #painter.setPen(QtCore.Qt.lightGray)
            painter.setFont(QtGui.QFont("Arial", 10))
            painter.drawText(
                    self.contentsRect(),
                    QtCore.Qt.AlignVCenter \
                            | QtCore.Qt.TextDontClip \
                            | QtCore.Qt.AlignHCenter,
                    "Select WaNo first.")
            painter.end()
            event.accept()

    @staticmethod  
    def hasChanged():
        logger = logging.getLogger('WFELOG')
        logger.debug("WaNo has changed")
        WaNoEditor.changedFlag=True

    def init(self, wano):
        # first, close all open tabs
        self.clear()

        # take care of the open 
        if WaNoEditor.changedFlag and len(self.activeTabs) > 1:
            ret = self.closeAction() # save is taken care inside
            if ret == QtWidgets.QMessageBox.Cancel: 
                return False

        if len(self.activeTabs) > 1:
            self.editor.deactivateWidget()
            self.clear()
            
        self.wano = wano
        WaNoEditor.changedFlag=False
        self.setMinimumWidth(400)
        self.tabWidget.addTab(self.wano.get_widget(),self.wano.model.name)
        self.tabWidget.addTab(self.wano.get_resource_widget(),"Resources")
        self.tabWidget.addTab(self.wano.get_import_widget(), "Imports")
        self.tabWidget.addTab(self.wano.get_export_widget(), "Exports")

        return True

    def remove_if_open(self,wano_view):
        if wano_view.get_widget() is self.tabWidget.widget(0):
            for i in range(self.tabWidget.count() - 1, -1, -1):
                self.tabWidget.closeTab(i)



       
    def deleteClose(self):
        if WaNoEditor.changedFlag:
            self.logger.debug("WaNo Content has changed")
            ret = self.closeAction()
            if ret == QtWidgets.QMessageBox.Save:
                # WaNo has changed means WF has changed 
                from .WFEditorPanel import WFWorkflowWidget
                WFWorkflowWidget.hasChanged()
                self.copyContent()
            elif ret == QtWidgets.QMessageBox.Cancel:
                return
        self.editor.deactivateWidget()
        self.clear()
           
    def saveClose(self):
        if WaNoEditor.changedFlag:          # WaNo has changed means WF has changed 
            from .WFEditorPanel import WFWorkflowWidget
            WFWorkflowWidget.hasChanged()
        self.copyContent()
        self.deleteClose()
        
    def copyContent(self):
        for tab in self.activeTabs:
            tab.copyContent()
        WaNoEditor.changedFlag = False
       
    def closeAction(self):
        reply = QtWidgets.QMessageBox(self)
        reply.setText("The Workflow Active Node Data has changed.")
        reply.setInformativeText("Do you want to save your changes?")
        reply.setStandardButtons(QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel)
        reply.setDefaultButton(QtWidgets.QMessageBox.Save)
        ret = reply.exec_()
    
        if ret == QtWidgets.QMessageBox.Cancel:
            return ret
        if ret == QtWidgets.QMessageBox.Save:
            self.copyContent()
        return ret
