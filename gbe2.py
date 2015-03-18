#!/usr/bin/python

# Import PySide classes
import sys
import copy
import PySide.QtCore as QtCore
import PySide.QtGui  as QtGui

import WFELicense
from GridBean import GridBean, GridBeanRepository

class GBEditor(QtGui.QDialog):
    def __init__(self, gb, exportedFiles, exportedVars,parent = None):
        super(GBEditor, self).__init__(parent)
        
        self.gb = gb
        
        tabWidget       = QtGui.QTabWidget()
        self.activeTabs = []
        if len(exportedFiles) > 0:
            tab = GBFileImportEditor(gb,exportedFiles)
            tabWidget.addTab(tab, "File Import")
            self.activeTabs.append(tab)
            
        if len(exportedFiles) > 0:
            tab = GBVarImportEditor(gb,exportedVars)
            tabWidget.addTab(tab, "Var Import")
            self.activeTabs.append(tab)
      
        if  gb.preScript != None:
            tab = ScriptTab(gb.preScript)
            tabWidget.addTab(tab, "Prepocessor")
            self.activeTabs.append(tab)
            
        tab = GBItemEditor(gb)
        tabWidget.addTab(tab, "Items")
        self.activeTabs.append(tab)
        
        if  gb.postScript != None:
            tab = ScriptTab(gb.postScript)
            tabWidget.addTab(tab, "Postpocessor")
            self.activeTabs.append(tab)
        
        tab = GBExportEditor(gb,exportedFiles)
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
        self.setWindowTitle("GridBeanEditor " + gb.name)
        
    def CopyContent(self):
        for tab in self.activeTabs:
            tab.copyContent()
        print self.gb
        self.accept()
        
class DummyTab(QtGui.QWidget):
    def __init__(self, parent = None):
        super(DummyTab, self).__init__(parent)
        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(QtGui.QTextEdit('Hello World'))
        self.setLayout(mainLayout)
        
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
        
        
class GBImportEditor(QtGui.QWidget):
    def __init__(self,gb,exportedItems, parent = None):
        super(GBImportEditor, self).__init__(parent)
        
        self.exportedItems = exportedItems
        self.data          = []  # list of (localNameWidget,GlobalNameWidget) tuples 
        self.buttons       = []  # list of the kill buttons
        self.gb            = gb
        
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
                
class GBExportEditor(GBImportEditor):
    def __init__(self,gb,exportedItems, parent = None):
        super(GBExportEditor, self).__init__(gb,exportedItems,parent)
    
    def fillExistingData(self):
        pass 
       
    def getGlobalNameWidget(self,globalNameS):
        return QtGui.QLineEdit()    
    
    def copyContent(self):
        self.gb.fileExports = {} # erase old stuff
        # not implemented: there should be a warning for multiple keys
        for (loc,glob,xxx) in self.data:
            localName = loc.text()
            self.gb.fileExports[localName] = str(glob.text())
           

class GBFileImportEditor(GBImportEditor):
    def __init__(self,gb,exportedItems, parent = None):
        super(GBFileImportEditor, self).__init__(gb,exportedItems,parent)
        
    def fillExistingData(self):
        for localName in gb.fileImports:
            self.addData(localName,gb.fileImports[localName]) 
            
    def copyContent(self):
        self.gb.fileImports = {} # erase old stuff
        # not implemented: there should be a warning for multiple keys
        for (loc,glob,xxx) in self.data:
            localName = loc.text()
            self.gb.fileImports[localName] = str(glob.currentText())
           
           
class GBVarImportEditor(GBImportEditor):
    def __init__(self,gb,exportedItems, parent = None):
        super(GBVarImportEditor, self).__init__(gb,exportedItems,parent)
        
    def fillExistingData(self):
        for localName in gb.varImports:
            self.addData(localName,gb.varImports[k]) 
            
    def copyContent(self):
        self.gb.varImports = {} # erase old stuff
        for (loc,glob,xxx) in self.data:
            localName = loc.text()
            self.gb.varImports[localName] = str(glob.currentText())
            
             



class GBItemEditor(QtGui.QWidget):
    def __init__(self, gb, parent = None):
        super(GBItemEditor, self).__init__(parent)
        
        self.gb = gb
   
        # scroll area widget contents - layout
        self.scrollLayout = QtGui.QFormLayout()        # empty layout to be filled later
        
        self.items = []
        for element in self.gb.elements:
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
        for e,v in zip(self.gb.elements,self.items):
            print e.name,v.text()
            e.value = v.text()
        
       
if __name__ == '__main__':
    gbr = GridBeanRepository()
    
    gb                  = copy.deepcopy(gbr['Gromacs'])
    gb.fileImports['File1'] = 'GLOBAL1'
    gb.fileImports['File2'] = 'GLOBAL2'
    
    exportedFiles      = ['FILEA','FILEB','FILEC'] + gb.fileImports.values()
    exportedVariables  = ['ITER','ACC']
    
    app = QtGui.QApplication(sys.argv)
    gbe = GBEditor(gb,exportedFiles,exportedVariables)
    gbe.show()
    app.exec_()