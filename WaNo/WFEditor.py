#!/usr/bin/env python2
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import sys
import logging
from lxml import etree
from . import WFELicense

import PySide.QtCore as QtCore
import PySide.QtGui  as QtGui

from .WaNo       import WorkFlow
from .WaNoEditor import *
from .WFEditorPanel import WFTabsWidget
from .WaNoSettingsProvider import WaNoSettingsProvider
from .WaNoSettings import WaNoUnicoreSettings
from .Constants import SETTING_KEYS
from .view.WaNoRegistrySelection import WaNoRegistrySelection

class WFEListWidget(QtGui.QListWidget):
    def __init__(self, indir, parent=None):
        super(WFEListWidget, self).__init__(parent) 
        self.setDragEnabled(True)
        path = os.path.dirname(os.path.realpath(__file__))
        for image in sorted(os.listdir(os.path.join(path, indir))):
            if image.endswith(".png"):
                item = QtGui.QListWidgetItem(image.split(".")[0])
                item.setIcon(QtGui.QIcon(os.path.join(path,
                                   "images/{0}".format(image))))
                self.addItem(item)
        self.myHeight = self.count()*10

    def sizeHint(self):
        return QtCore.QSize(100,self.myHeight)
        
class WFEWaNoListWidget(QtGui.QListWidget):
    def __init__(self, indir, parent=None):
        super(WFEWaNoListWidget, self).__init__(parent) 
        self.setDragEnabled(True)
        path = os.path.dirname(os.path.realpath(__file__))
        wanoRep = WaNoRepository()
        
        for infile in sorted(os.listdir(os.path.join(path, indir))):
            if infile.endswith(".xml"):
                item = QtGui.QListWidgetItem(infile.split(".")[0])
                xxi = os.path.join(path,indir+"/{0}".format(infile))
                self.addItem(item)
                element = wanoRep.parse_xml_file(xxi) 
                item.WaNo = element
                #item.setIcon(QtGui.QIcon(os.path.join(path,"infile/{0}".format(infile))))
                #self.addItem(item)
                
        self.myHeight = self.count()*10
        
    def sizeHint(self):
        return QtCore.QSize(100,max(self.myHeight,200))
    
class WFEWorkflowistWidget(QtGui.QListWidget):
    def __init__(self, indir, parent=None):
        super(WFEWorkflowistWidget, self).__init__(parent) 
        self.logger = logging.getLogger('WFEOG')
        self.setDragEnabled(True)
        self.update(indir)

    def update(self,indir = "WorkFlows"):
        self.clear()
        path = os.path.dirname(os.path.realpath(__file__))
        for infile in sorted(os.listdir(os.path.join(path, indir))):
            if infile.endswith(".xml"):
                xxi = os.path.join(path,indir+"/{0}".format(infile))
                try:
                    inputData = etree.parse(xxi)
                except:
                    self.logger.error('File not found: ' + xxi)
                    raise 
                r = inputData.getroot()
                if r.tag == "Workflow":
                    element = WorkFlow(r) 
                else:
                    self.logger.critical('Loading Workflows: no workflow in file ' + xxi)
                item = QtGui.QListWidgetItem(element.name)
                item.WaNo = element
                self.addItem(item)
        self.myHeight = self.count()*10

    def sizeHint(self):
        return QtCore.QSize(100,max(self.myHeight,100))
    
class WFEditor(QtGui.QDialog):
    def __init_ui(self):
        self.wanoEditor = WaNoEditor(self) # make this first to enable logging
        self.wanoEditor.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
        
        self.workflowWidget = WFTabsWidget(self)
        self.workflowWidget.setAcceptDrops(True)
        
        self.workflowWidget.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
        self.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)

        self.registrySelection = WaNoRegistrySelection(self)
       
        leftPanel = QtGui.QSplitter(QtCore.Qt.Vertical)
        leftPanel.setSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Expanding)

        rightPanel = QtGui.QSplitter(QtCore.Qt.Vertical)
        rightPanel.setSizePolicy(QtGui.QSizePolicy.Fixed,QtGui.QSizePolicy.Expanding)
                
        layout = QtGui.QHBoxLayout()       
        layout.addWidget(leftPanel)
        layout.addWidget(self.workflowWidget)
        layout.addWidget(rightPanel)
        layout.addStretch(1)
         
        self.mainPanels = layout  
        self.setLayout(layout)
        
        WanoListWidget = WFEWaNoListWidget('WaNoRepository')
        CtrlListWidget = WFEListWidget('ctrl_img')
        self.WorkListWidget = WFEWorkflowistWidget('WorkFlows')
        
        
        leftPanel.addWidget(QtGui.QLabel('Nodes'))
        leftPanel.addWidget(WanoListWidget)
        leftPanel.addWidget(QtGui.QLabel('Workflows'))      
        leftPanel.addWidget(self.WorkListWidget)
        leftPanel.addWidget(QtGui.QLabel('Controls'))
        leftPanel.addWidget(CtrlListWidget)

        rightPanel.addWidget(self.registrySelection)
        rightPanel.addWidget(self.wanoEditor)
        
        self.lastActive = None

    def __init__(self, settings, parent=None):
        super(WFEditor, self).__init__(parent)
        self.__settings = settings
        self.logger = logging.getLogger('WFELOG')
        self.__init_ui()
        self.update_registries()
#        self.registrySelection.registrySelectionChanged.connect(self.test)


    def update_registries(self):
        default = 0
        registries = self.__settings.get_value(SETTING_KEYS['registries'])
        regList = []
        for i, r in enumerate(registries):
            regList.append(r[SETTING_KEYS['registry.name']])
            if r[SETTING_KEYS['registry.is_default']]:
                default = i
        self.registrySelection.update_registries(regList, index=default)

    
    def deactivateWidget(self):
        if self.lastActive != None:
            self.lastActive.setColor(QtCore.Qt.lightGray)
            self.lastActive = None
       
        
    def openWaNoEditor(self,wanoWidget,varExports,fileExports,waNoNames):
        if self.wanoEditor.init(wanoWidget.wano,varExports,fileExports,waNoNames):
            wanoWidget.setColor(QtCore.Qt.green)
            self.lastActive = wanoWidget
    
    def openWorkFlow(self,workFlow):
        self.workflowWidget.openWorkFlow(workFlow)
        
     
        
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
    
    def open(self):
        self.workflowWidget.open()
        
    def save(self):
        self.workflowWidget.save()
        self.WorkListWidget.update()
        
    def saveAs(self):
        self.workflowWidget.saveAs()
        self.WorkListWidget.update()
        
    def loadFile(self,fileName):
        self.workflowWidget.loadFile(fileName)
        
class WFEditorApplication(QtGui.QMainWindow):
    def __init_ui(self):
        self.setWindowIcon(QtGui.QIcon('./WaNo/Media/Logo_Nanomatch.jpg'))
        
        self.wfEditor = WFEditor(self.__settings)
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

        self.settingsMenu = self.menuBar().addAction(
                QtGui.QAction(
                    "&Configuration",
                    self,
                    statusTip="Open Settings",
                    triggered=self.openSettingsDialog
                )
            )
        
        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutWFEAct)
        
        message = "Welcome to the Nanomatch Workflow Editor"
        self.statusBar().showMessage(message)
        
        self.setWindowTitle("Nanomatch Workflow Editor (C) 2015")
   
    def __init__(self, settings, parent=None):
        super(WFEditorApplication,self).__init__(parent)
        self.__settings = settings
        self.__init_ui()

    def openSettingsDialog(self):
        print(self.__settings.as_dict())
        print("SETTING_KEYS['registries']: %s" % str(type(
                self.__settings.get_value(SETTING_KEYS['registries'])
            )))
        dialog = WaNoUnicoreSettings(
                self.__settings.get_value(SETTING_KEYS['registries'])
            )

        if (dialog.exec_()):
            print("success: %s" % str(dialog.get_settings()))
            # first, delete all previous settings
            self.__settings.delete_value(SETTING_KEYS['registries'])

            # second, add new registries
            for i, registry in enumerate(dialog.get_settings()):
                settings_path = "%s.%d" % (SETTING_KEYS['registries'], i)
                self.__settings.set_value(
                        "%s.%s" % (settings_path, SETTING_KEYS['registry.name']),
                        registry['name']
                    )
                self.__settings.set_value(
                        "%s.%s" % (settings_path, SETTING_KEYS['registry.baseURI']),
                        registry['baseURI']
                    )
                self.__settings.set_value(
                        "%s.%s" % (settings_path, SETTING_KEYS['registry.username']),
                        registry['username']
                    )
                self.__settings.set_value(
                        "%s.%s" % (settings_path, SETTING_KEYS['registry.password']),
                        registry['password']
                    )
                self.__settings.set_value(
                        "%s.%s" % (settings_path, SETTING_KEYS['registry.is_default']),
                        registry['default']
                    )


            # last, save new settings to file
            self.__settings.save()
            
            # update registry list
            self.wfEditor.update_registries()
        else:
            print("fail")
        
    def newFile(self):
        self.wfEditor.clear()
        
    def open(self):
        self.wfEditor.open()
        
    def save(self):
        self.wfEditor.save()
    
    def saveAs(self):
        self.wfEditor.saveAs()
        
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
        
