#!/usr/bin/python

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys
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

class ScriptTab(QtWidgets.QWidget):
    waNoChangedSig = QtCore.Signal()
    
    def __init__(self, script, importSelection, parent = None):
        super(ScriptTab, self).__init__(parent)
        
        self.logger          = logging.getLogger('WFELOG')
        self.importSelection = importSelection
        self.script = script    
        
        mainLayout  = QtWidgets.QVBoxLayout()
        
        topLine = QtWidgets.QHBoxLayout()
        self.language = QtWidgets.QComboBox()
        languages = ['bash','python','java']
        self.language.addItems(['bash','python','java'])
        idx = 1
        if 'language' in script.attrib:
            try:
                idx = languages.index(script.attrib['language'])
            except:
                self.logger.critical('Unsupported language for Preprocessor set in script <%s>' % script.name)
                idx = 1
        else:
            self.logger.error('No language for Preprocessor set in script <%s>' % script.name)
        self.language.setCurrentIndex(idx)
        self.language.currentIndexChanged[str].connect(self.uchanged)
        topLine.addWidget(self.language)
        
        topLine.addStretch(1)
        if len(importSelection) > 0:
            button = QtWidgets.QPushButton('Import')
            topLine.addWidget(button)
            button.clicked.connect(self.addImport)
              
        self.hiddenButton = QtWidgets.QCheckBox('hide')
        if 'hidden' in self.script.attrib and self.script.attrib['hidden'] == 'True':
            self.hiddenButton.setChecked(True)
                
            
        self.hiddenButton.clicked.connect(self.changed)
        topLine.addWidget(self.hiddenButton)
        
        self.editor = QtWidgets.QTextEdit(script.value)
        
        mainLayout.addLayout(topLine)
        
        self.importWidgets = []
        self.importList = QtWidgets.QGridLayout()
        for imp in script.imports:
            self.addImport(imp)
      
        mainLayout.addLayout(self.importList)
        
        mainLayout.addWidget(self.editor)
        self.setLayout(mainLayout)
 
        self.editor.textChanged.connect(self.changed) 
        self.waNoChangedSig.connect(WaNoEditor.hasChanged)
       
        
    def addImport(self,importData=None):
        if importData == None:  # make default data
            importData = ('local',self.importSelection[0],'source')
            
        nn = self.importList.rowCount()
        localName = QtWidgets.QLineEdit(importData[0])
        localName.textChanged.connect(self.changed)       
        self.importList.addWidget(localName,nn+1,0)
        
        importSelect    = QtWidgets.QComboBox()
        importSelect.addItems(self.importSelection)
        self.importList.addWidget(importSelect,nn+1,1)
        
        try:
            idx = self.importSelection.index(importData[1])
            importSelect.setCurrentIndex(idx)
        except:
            self.logger.error("Could not set current index in import selection of script tab Item#:" + str(nn) + \
                              " key: " + importData[1] + " items: " + str(self.importSelection))
        
        fromName = QtWidgets.QLineEdit(importData[2])
        fromName.textChanged.connect(self.changed)
        self.importList.addWidget(fromName,nn+1,2)
        
        delButton = QtWidgets.QPushButton('delete')
        delButton.clicked.connect(self.deleteImport)
        self.importList.addWidget(delButton,nn+1,3)
        
        self.importWidgets.append((localName,importSelect,fromName,delButton))
        self.changed()
        
    def changed(self):
        self.waNoChangedSig.emit()
        
    def deleteImport(self):
        self.logger.info("delete import requested")
        
    def uchanged(self,u):
        self.waNoChangedSig.emit()
        
    def copyContent(self):
        self.script.value = self.editor.toPlainText()
        self.script.imports = []
        for imp in self.importWidgets:
            self.script.imports.append((imp[0].text(),imp[1].currentText(),imp[2].text()))
       
        self.script.attrib['hidden']   = str(self.hiddenButton.isChecked())
        print ("setting hidden to",self.hiddenButton.isChecked())
        self.script.attrib['language'] = self.language.currentText()
        
        
class WaNoImportEditor(QtWidgets.QWidget):
    def __init__(self,wano,exportedItems, parent = None):
        super(WaNoImportEditor, self).__init__(parent)
        
        self.exportedItems = exportedItems
        self.data          = []  # list of (localNameWidget,GlobalNameWidget) tuples 
        self.buttons       = []  # list of the kill buttons
        self.wano          = wano
        
        # main button
        self.addButton = QtWidgets.QPushButton('Add')
        self.addButton.clicked.connect(self.addData)

        # scroll area widget contents - layout
        self.linesLayout = QtWidgets.QVBoxLayout()        # empty layout to be filled later
        self.fillExistingData()  
        
        # scroll area widget contents
        self.scrollWidget = QtWidgets.QWidget()
        self.scrollWidget.setLayout(self.linesLayout) # layout is set for widget
       
        #
        # now we make some space at the bottom
        #
        self.spacingLayout = QtWidgets.QVBoxLayout()
        self.spacingLayout.addWidget(self.scrollWidget)
        self.spacingLayout.addStretch(1)
        
        self.spacingWidget = QtWidgets.QWidget()
        self.spacingWidget.setLayout(self.spacingLayout) # layout is set for widget
       
                
        # scroll area
        self.scrollArea = QtWidgets.QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.spacingWidget)
        # main layout
        self.mainLayout = QtWidgets.QVBoxLayout()

        # add all main to the main vLayout
        self.mainLayout.addWidget(self.addButton)
        self.mainLayout.addWidget(self.scrollArea)
        
        
        self.setLayout(self.mainLayout) 

    def addData(self,localName=None,globalName=None):
        pos = len(self.data)
        #print 'adding at',pos,self.linesLayout.count()
        
        singleLineLayout = QtWidgets.QHBoxLayout()
        
        buttonKill    = QtWidgets.QPushButton('X')
        buttonKill.clicked.connect(self.buttonKillClick)
        self.buttons.append(buttonKill)
        
        if localName == None:
            localName = 'Item'+str(pos)

        localNameWidget  = QtWidgets.QLineEdit(localName)
        globalNameWidget = self.getGlobalNameWidget(globalName)
        
        singleLineLayout.addWidget(localNameWidget)
        singleLineLayout.addWidget(globalNameWidget)
        singleLineLayout.addWidget(buttonKill)
        
        lineWidget = QtWidgets.QWidget()
        lineWidget.setLayout(singleLineLayout)
        
       
        
        self.linesLayout.addWidget(lineWidget)
        self.data.append((localNameWidget,globalNameWidget,lineWidget))
                   
        
    def buttonKillClick(self):
        try:
            idx = self.buttons.index(self.sender())
        except:
            print ('Button not found')
        
        ind = self.linesLayout.indexOf(self.data[idx][2])        
        t = self.linesLayout.takeAt(ind)
        t.widget().setParent(None)
       
        del self.buttons[idx]
        del self.data[idx]

    def getGlobalNameWidget(self,globalName):
        globalNameWidget = QtWidgets.QComboBox()
        for e in self.exportedItems:
            globalNameWidget.addItem(e)
        # set default if globalName is already defined
        if globalName != None:
            try:
                idx = self.exportedItems.index(globalName)
                globalNameWidget.setCurrentIndex(idx)
            except ValueError:
                print ('Global Name' + globalName + ' not found in ' + str(self.exportedItems))
        return globalNameWidget
                
class WaNoExportEditor(WaNoImportEditor):
    def __init__(self,wano,exportedItems, parent = None):
        super(WaNoExportEditor, self).__init__(wano,exportedItems,parent)
    
    def fillExistingData(self):
        pass 
       
    def getGlobalNameWidget(self,globalNameS):
        return QtWidgets.QLineEdit()    
    
    def copyContent(self):
        self.wano.fileExports = {} # erase old stuff
        # not implemented: there should be a warning for multiple keys
        for (loc,glob,xxx) in self.data:
            localName = loc.text()
            self.wano.fileExports[localName] = str(glob.text())
           

class WaNoFileImportEditor(WaNoImportEditor):
    def __init__(self,wano,exportedItems, parent = None):
        super(WaNoFileImportEditor, self).__init__(wano,exportedItems,parent)
        
    def fillExistingData(self):
        for localName in wano.fileImports:
            self.addData(localName,wano.fileImports[localName]) 
            
    def copyContent(self):
        self.wano.fileImports = {} # erase old stuff
        # not implemented: there should be a warning for multiple keys
        for (loc,glob,xxx) in self.data:
            localName = loc.text()
            self.wano.fileImports[localName] = str(glob.currentText())
           
           
class WaNoVarImportEditor(WaNoImportEditor):
    def __init__(self,wano,exportedItems, parent = None):
        super(WaNoVarImportEditor, self).__init__(wano,exportedItems,parent)
        
    def fillExistingData(self):
        for localName in wano.varImports:
            self.addData(localName,wano.varImports[k]) 
            
    def copyContent(self):
        self.wano.varImports = {} # erase old stuff
        for (loc,glob,xxx) in self.data:
            localName = loc.text()
            self.wano.varImports[localName] = str(glob.currentText())
            
           
class WaNoItemEditor(QtWidgets.QWidget):
    def __init__(self, wano, importSelection, parent = None):
        super(WaNoItemEditor, self).__init__(parent)
        
        self.wano = wano
        
        # scroll area widget contents - layout
        self.scrollLayout = QtWidgets.QVBoxLayout()        # empty layout to be filled later
        # left top right bottom
        self.scrollLayout.setContentsMargins(1,1,1,1)
        self.items = []
        
        if len(self.wano.elements) > 0:
            ll = max( [ len(element.name) for element in self.wano.elements] )
        else:
            ll = 10
        for element in self.wano.elements:
            widget = element.makeWidget(ll,importSelection)  
            self.items.append(widget) 
            self.scrollLayout.addWidget(widget) # this sets the parent 
    
        self.scrollLayout.addStretch(1)
        # scroll area widget contents
        self.scrollWidget = QtWidgets.QWidget()
        self.scrollWidget.setLayout(self.scrollLayout) # layout is set for widget

        # scroll area
        self.scrollArea = QtWidgets.QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.scrollWidget)

        # main layout
        self.mainLayout = QtWidgets.QVBoxLayout()
        
        # add all main to the main vLayout
        self.mainLayout.addWidget(self.scrollArea)
        
        self.setLayout(self.mainLayout)

    def copyContent(self):
        for e in self.wano.elements:
            e.copyContent()
        
import argparse

if __name__ == '__main__':
    from .WaNo import WaNoRepository
    mypath = os.path.dirname(os.path.realpath(__file__))
    parser = argparse.ArgumentParser('Option Parser')
    parser.add_argument('--log', default='DEBUG')
    
    args  = parser.parse_args()

    logging.basicConfig(filename='wano.log',filemode='w',level=logging.DEBUG)
    logging.getLogger(__name__).addHandler(logging.StreamHandler())
     
    print (args)
    

    wanoRep = WaNoRepository()
    wanoRep.parse_xml_file(mypath + '/WaNoRepository/Simona.xml')

    
    wano                      = copy.copy(wanoRep['Simona'])
    wano.fileImports['File1'] = 'GLOBAL1'
    wano.fileImports['File2'] = 'GLOBAL2'
    
    exportedFiles      = ['FILEA','FILEB','FILEC'] + list(wano.fileImports.values())
    exportedVariables  = ['ITER','ACC']
    
    app = QtWidgets.QApplication(sys.argv)
    wanoe = WaNoEditor(wano,None,exportedFiles,exportedVariables)
    wanoe.show()
    app.exec_()
