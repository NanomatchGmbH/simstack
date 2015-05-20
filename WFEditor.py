from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future_builtins import *

import os
import sys
import WFELicense

import PySide.QtCore as QtCore
import PySide.QtGui  as QtGui

from WaNoEditor import *
from WFEditorPanel import WFWidget

class WFEListWidget(QtGui.QListWidget):
    def __init__(self, indir, parent=None):
        super(WFEListWidget, self).__init__(parent) 
        self.setDragEnabled(True)
        path = os.path.dirname(__file__)
        for image in sorted(os.listdir(os.path.join(path, indir))):
            if image.endswith(".png"):
                item = QtGui.QListWidgetItem(image.split(".")[0])
                item.setIcon(QtGui.QIcon(os.path.join(path,
                                   "images/{0}".format(image))))
                self.addItem(item)

class WFEWaNoListWidget(QtGui.QListWidget):
    def __init__(self, indir, parent=None):
        super(WFEWaNoListWidget, self).__init__(parent) 
        self.setDragEnabled(True)
        path = os.path.dirname(__file__)
        wanoRep = WaNoRepository()
        
        for infile in sorted(os.listdir(os.path.join(path, indir))):
            if infile.endswith(".xml"):
                item = QtGui.QListWidgetItem(infile.split(".")[0])
                xxi = os.path.join(path,indir+"/{0}".format(infile))
                self.addItem(item)
                element = wanoRep.parse_xml_file(xxi) 
                item.WaNo = element
                item.setIcon(QtGui.QIcon(os.path.join(path,"infile/{0}".format(infile))))
                self.addItem(item)
                
class WFEWorkflowistWidget(QtGui.QListWidget):
    def __init__(self, indir, parent=None):
        super(WFEWorkflowistWidget, self).__init__(parent) 
        self.setDragEnabled(True)
        path = os.path.dirname(__file__)
        
        for infile in sorted(os.listdir(os.path.join(path, indir))):
            if infile.endswith(".xml"):
                item = QtGui.QListWidgetItem(infile.split(".")[0])
                xxi = os.path.join(path,indir+"/{0}".format(infile))
                self.addItem(item)
                try:
                    inputData = etree.parse(filename)
                except:
                    self.logger.error('File not found: ' + filename)
                    raise 
                r = self.inputData.getroot()
                if r.tag == "Workflow":
                    element = Workflow(r) 
                item.WaNo = element
                item.setIcon(QtGui.QIcon(os.path.join(path,"infile/{0}".format(infile))))
                self.addItem(item)

        
class WFEditor(QtGui.QDialog):

    def __init__(self, parent=None):
        super(WFEditor, self).__init__(parent)

        self.workflowWidget = WFWidget(self)
        self.workflowWidget.setAcceptDrops(True)
        
        self.workflowWidget.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
        self.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
       
        selectionPanel = QtGui.QSplitter(QtCore.Qt.Vertical)
        selectionPanel.setSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Expanding)
      
        
        WanoListWidget = WFEWaNoListWidget('WaNoRepository')
        CtrlListWidget = WFEListWidget('ctrl_img')
        WorkListWidget = WFEListWidget('workflow_img')
        
        
        selectionPanel.addWidget(QtGui.QLabel('Nodes'))
        selectionPanel.addWidget(WanoListWidget)
        selectionPanel.addWidget(QtGui.QLabel('Workflows'))      
        selectionPanel.addWidget(WorkListWidget)
        selectionPanel.addWidget(QtGui.QLabel('Controls'))
        selectionPanel.addWidget(CtrlListWidget)
        
        self.wanoEditor = WaNoEditor(self) 
       
        
        layout = QtGui.QHBoxLayout()       
        layout.addWidget(selectionPanel)
        layout.addWidget(self.workflowWidget)
        layout.addWidget(self.wanoEditor)
         
        self.mainPanels = layout  
        self.setLayout(layout)
      
        self.lastActive = None

    def deactivateWidget(self):
        if self.lastActive != None:
            self.lastActive.setColor(QtCore.Qt.lightGray)
            self.lastActive = None
       
        
    def openWaNoEditor(self,wanoWidget,varExports,fileExports,waNoNames):
        if self.wanoEditor != None:            
            if self.wanoEditor.closeAction() == QtGui.QMessageBox.Cancel:
                return
            self.wanoEditor.deleteClose()
        wanoWidget.setColor(QtCore.Qt.green)
        self.lastActive = wanoWidget
        self.wanoEditor.init(wanoWidget.wano,varExports,fileExports,waNoNames) 
       
   
    def resizeEvent(self,e):
        super(WFEditor,self).resizeEvent(e)
        print ("RES")
        
    def SizeHint(self):
        s = QtGui.QSize()
        if self.wanoEditor == None:
            s.setWidth(400)
        else:
            s.setWidth(800)
        s.setHeight(600)
        return s
    
    def clear(self):
        self.workflowWidget.clear()
        
    def saveFile(self,fileName):
        self.workflowWidget.saveFile(fileName)
        
    def loadFile(self,fileName):
        self.workflowWidget.loadFile(fileName)
        
class WFEditorApplication(QtGui.QMainWindow):
    def __init__(self,parent=None):
        super(WFEditorApplication,self).__init__(parent)
        
        self.curFile = None 
        self.wfEditor = WFEditor()
        self.setCentralWidget(self.wfEditor)
        
             
        self.createActions()
        
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.newAct)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.saveAct)
        self.fileMenu.addAction(self.saveAsAct)
        self.fileMenu.addAction(self.printAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)
        
        self.runMenu = self.menuBar().addMenu("&Run")
        
        
        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutWFEAct)
        
        message = "Welcome to the Nanomatch Workflow Editor"
        self.statusBar().showMessage(message)
        
        self.setWindowTitle("Nanomatch Workflow Editor (C) 2015")
        
    def newFile(self):
        reply = QtGui.QMessageBox(self)
        reply.setText("The document has been modified.")
        reply.setInformativeText("Do you want to save your changes?")
        reply.setStandardButtons(QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard | QtGui.QMessageBox.Cancel)
        reply.setDefaultButton(QtGui.QMessageBox.Save)
        ret = reply.exec_()
        
        if ret == QtGui.QMessageBox.Cancel:
            return
        if ret == QtGui.QMessageBox.Save:
            self.save()
        self.wfEditor.clear()
        
        
    def open(self):
        fileName, filtr = QtGui.QFileDialog(self).getOpenFileName(self,'Open Workflow','.','xml (*.xml *.xm)')
        if fileName:
            print ("Loading Workflow from File:",fileName) 
            self.newFile()
            self.loadFile(fileName)
        
    def saveFile(self,fileName):
        self.wfEditor.saveFile(fileName)
        
    def loadFile(self,fileName):
        self.wfEditor.loadFile(fileName)
        
        
    def save(self):
        if self.curFile == None:
            return self.saveAs()
        else:
            return self.saveFile(self.curFile)

    def saveAs(self):
        fileName, filtr = QtGui.QFileDialog.getSaveFileName(self, 'Open Workflow',self.curFile,'xml (*.xml *.xm)')
        if not fileName:
            return False

        return self.saveFile(fileName)

    def print_(self):
        self.infoLabel.setText("Invoked <b>File|Print</b>")

    def about(self):
        self.infoLabel.setText("Invoked <b>Help|About</b>")
        QtGui.QMessageBox.about(self, "About Menu",
                "The <b>Menu</b> example shows how to create menu-bar menus "
                "and context menus.")
        
    def aboutWFE(self):
        self.infoLabel.setText("Invoked <b>Help|About Qt</b>")

    def createActions(self):
        self.newAct = QtGui.QAction("&New", self,
                shortcut=QtGui.QKeySequence.New,
                statusTip="Create a new file", triggered=self.newFile)

        self.openAct = QtGui.QAction("&Open...", self,
                shortcut=QtGui.QKeySequence.Open,
                statusTip="Open an existing file", triggered=self.open)

        self.saveAct = QtGui.QAction("&Save", self,
                shortcut=QtGui.QKeySequence.Save,
                statusTip="Save the document to file", triggered=self.save)
        
        self.saveAsAct = QtGui.QAction("Save &As", self,
                               shortcut=QtGui.QKeySequence.SaveAs,
                statusTip="Save the document to new file", triggered=self.saveAs)

        self.printAct = QtGui.QAction("&Print...", self,
                shortcut=QtGui.QKeySequence.Print,
                statusTip="Print the document", triggered=self.print_)

        self.exitAct = QtGui.QAction("E&xit", self, shortcut="Ctrl+Q",
                statusTip="Exit the application", triggered=self.close)


        self.aboutAct = QtGui.QAction("&Help", self,
                statusTip="Show the application's Help box",
                triggered=self.about)

        self.aboutWFEAct = QtGui.QAction("About &WorkflowEditor", self,
                statusTip="About the Nanomatch Workflow Editor",
                triggered=self.aboutWFE)
        
        self.aboutWFEAct.triggered.connect(QtGui.qApp.aboutQt)
        
if __name__ == '__main__':   
    app = QtGui.QApplication(sys.argv)
    logging.basicConfig(filename='wfeditor.log',filemode='w',level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.StreamHandler())
    
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)


    editor = WFEditorApplication()
    editor.show()
    app.exec_()
