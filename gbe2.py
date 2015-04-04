#!/usr/bin/python

# Import PySide classes
import sys
import copy
import logging

import PySide.QtCore as QtCore
import PySide.QtGui  as QtGui

import WFELicense
from WaNo import WaNo, WaNoRepository

class WaNoEditor(QtGui.QDialog):
    def __init__(self, wano, exportedFiles, exportedVars,parent = None):
        super(WaNoEditor, self).__init__(parent)
        
        self.wano = wano
        
        tabWidget       = QtGui.QTabWidget()
        self.activeTabs = []
        if len(exportedFiles) > 0:
            tab = WaNoFileImportEditor(wano,exportedFiles)
            tabWidget.addTab(tab, "File Import")
            self.activeTabs.append(tab)
            
        if len(exportedFiles) > 0:
            tab = WaNoVarImportEditor(wano,exportedVars)
            tabWidget.addTab(tab, "Var Import")
            self.activeTabs.append(tab)
      
        if  wano.preScript != None:
            tab = ScriptTab(wano.preScript)
            tabWidget.addTab(tab, "Prepocessor")
            self.activeTabs.append(tab)
            
        tab = WaNoItemEditor(wano)
        tabWidget.addTab(tab, "Items")
        self.activeTabs.append(tab)
        
        if  wano.postScript != None:
            tab = ScriptTab(wano.postScript)
            tabWidget.addTab(tab, "Postpocessor")
            self.activeTabs.append(tab)
        
        tab = WaNoExportEditor(wano,exportedFiles)
        tabWidget.addTab(tab, "Export")
        self.activeTabs.append(tab)
            
        buttonBox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok | 
                                           QtGui.QDialogButtonBox.Cancel)
      
        
        buttonBox.accepted.connect(self.CopyContent)
        buttonBox.rejected.connect(self.reject)
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(tabWidget)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)
        self.setWindowTitle("WaNoEditor " + wano.name)
        
    def CopyContent(self):
        for tab in self.activeTabs:
            tab.copyContent()
        print self.wano
        self.accept()
        

class ScriptTab(QtGui.QWidget):
    def __init__(self, script, parent = None):
        super(ScriptTab, self).__init__(parent)
        mainLayout = QtGui.QVBoxLayout()
        self.editor = QtGui.QTextEdit(script.content)
        mainLayout.addWidget(self.editor)
        self.setLayout(mainLayout)
        self.script = script
    def copyContent(self):
        self.script.content = self.editor.toPlainText()
        
        
class WaNoImportEditor(QtGui.QWidget):
    def __init__(self,wano,exportedItems, parent = None):
        super(WaNoImportEditor, self).__init__(parent)
        
        self.exportedItems = exportedItems
        self.data          = []  # list of (localNameWidget,GlobalNameWidget) tuples 
        self.buttons       = []  # list of the kill buttons
        self.wano            = wano
        
        # main button
        self.addButton = QtGui.QPushButton('Add')
        self.addButton.clicked.connect(self.addData)

        # scroll area widget contents - layout
        self.linesLayout = QtGui.QVBoxLayout()        # empty layout to be filled later
        self.fillExistingData()                       # abstract function
        
        # scroll area widget contents
        self.scrollWidget = QtGui.QWidget()
        self.scrollWidget.setLayout(self.linesLayout) # layout is set for widget

        # scroll area
        self.scrollArea = QtGui.QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.scrollWidget)

        # main layout
        self.mainLayout = QtGui.QVBoxLayout()

        # add all main to the main vLayout
        self.mainLayout.addWidget(self.addButton)
        self.mainLayout.addWidget(self.scrollArea)

        self.setLayout(self.mainLayout) 

    def addData(self,localName=None,globalName=None):
        pos = len(self.data)
        #print 'adding at',pos,self.linesLayout.count()
        
        singleLineLayout = QtGui.QHBoxLayout()
        
        buttonKill    = QtGui.QPushButton('X')
        buttonKill.clicked.connect(self.buttonKillClick)
        self.buttons.append(buttonKill)
        
        if localName == None:
            localName = 'Item'+str(pos)

        localNameWidget = QtGui.QLineEdit(localName)
        
        globalNameWidget = self.getGlobalNameWidget(globalName)
        
        singleLineLayout.addWidget(localNameWidget)
        singleLineLayout.addWidget(globalNameWidget)
        singleLineLayout.addWidget(buttonKill)
        
        lineWidget = QtGui.QWidget()
        lineWidget.setLayout(singleLineLayout)
        
        self.linesLayout.addWidget(lineWidget)
        self.data.append((localNameWidget,globalNameWidget,lineWidget))
        #print 'Rows: ',self.linesLayout.count()
                         
        
    def buttonKillClick(self):
        try:
            idx = self.buttons.index(self.sender())
        except:
            print 'Button not found'  
        
        ind = self.linesLayout.indexOf(self.data[idx][2])        
        t = self.linesLayout.takeAt(ind)
        t.widget().setParent(None)
       
        del self.buttons[idx]
        del self.data[idx]

    def getGlobalNameWidget(self,globalName):
        globalNameWidget = QtGui.QComboBox()
        for e in self.exportedItems:
            globalNameWidget.addItem(e)
        # set default if globalName is already defined
        if globalName != None:
            try:
                idx = self.exportedItems.index(globalName)
                globalNameWidget.setCurrentIndex(idx)
            except ValueError:
                print 'Global Name' + globalName + ' not found in ' + str(self.exportedItems)
        return globalNameWidget
                
class WaNoExportEditor(WaNoImportEditor):
    def __init__(self,wano,exportedItems, parent = None):
        super(WaNoExportEditor, self).__init__(wano,exportedItems,parent)
    
    def fillExistingData(self):
        pass 
       
    def getGlobalNameWidget(self,globalNameS):
        return QtGui.QLineEdit()    
    
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
            
           
class WaNoItemEditor(QtGui.QWidget):
    def __init__(self, wano, parent = None):
        super(WaNoItemEditor, self).__init__(parent)
        
        self.wano = wano
   
        # scroll area widget contents - layout
        self.scrollLayout = QtGui.QFormLayout()        # empty layout to be filled later
        
        self.items = []
        for element in self.wano.elements:
            line_edit = QtGui.QLineEdit(str(element.value))
            self.items.append(line_edit)
            self.scrollLayout.addRow(element.name,line_edit)
    
        # scroll area widget contents
        self.scrollWidget = QtGui.QWidget()
        self.scrollWidget.setLayout(self.scrollLayout) # layout is set for widget

        # scroll area
        self.scrollArea = QtGui.QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.scrollWidget)

        # main layout
        self.mainLayout = QtGui.QVBoxLayout()
        
        # add all main to the main vLayout
        self.mainLayout.addWidget(self.scrollArea)
        self.setLayout(self.mainLayout)

    def copyContent(self):
        for e,v in zip(self.wano.elements,self.items):
            print e.name,v.text()
            e.value = v.text()
        
import argparse

if __name__ == '__main__':
    parser = argparse.ArgumentParser('Option Parser')
    parser.add_argument('--log', default='DEBUG')
    
    args  = parser.parse_args()

    logging.basicConfig(filename='WaNo.log',filemode='w',level=logging.DEBUG)
    
    print args
    

    wanoRep = WaNoRepository()
    wanoRep.parse_yml_dir('WaNoRepository')

    
    wano                      = copy.copy(wanoRep['Gromacs'])
    wano.fileImports['File1'] = 'GLOBAL1'
    wano.fileImports['File2'] = 'GLOBAL2'
    
    exportedFiles      = ['FILEA','FILEB','FILEC'] + wano.fileImports.values()
    exportedVariables  = ['ITER','ACC']
    
    app = QtGui.QApplication(sys.argv)
    wanoe = WaNoEditor(wano,exportedFiles,exportedVariables)
    wanoe.show()
    app.exec_()