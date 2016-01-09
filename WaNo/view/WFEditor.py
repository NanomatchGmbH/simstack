import logging
from PySide.QtGui import QWidget, QSizePolicy, QLabel, QSplitter, QHBoxLayout
from PySide.QtCore import Qt, Signal

from .WaNoEditorWidget import WaNoEditor
from .WFEditorPanel import WFTabsWidget
from .WaNoRegistrySelection import WaNoRegistrySelection
from .WFEditorWidgets import WFEWaNoListWidget, WFEListWidget, WFEWorkflowistWidget

class WFEditor(QWidget):
    _controls = [
            ("ForEach", "ctrl_img/ForEach.png"),
            ("If", "ctrl_img/If.png"),
            ("Parallel", "ctrl_img/Parallel.png"),
            ("While", "ctrl_img/While.png")
        ]

    registry_changed        = Signal(int, name="RegistryChanged")

    def __init_ui(self):
        self.wanoEditor = WaNoEditor(self) # make this first to enable logging
        self.wanoEditor.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        
        self.workflowWidget = WFTabsWidget(self)
        self.workflowWidget.setAcceptDrops(True)
        self.workflowWidget.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

        self.registrySelection = WaNoRegistrySelection(self)
       
        leftPanel = QSplitter(Qt.Vertical)
        leftPanel.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Expanding)

        rightPanel = QSplitter(Qt.Vertical)
        rightPanel.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Expanding)
                
        layout = QHBoxLayout()       
        layout.addWidget(leftPanel)
        layout.addWidget(self.workflowWidget)
        layout.addWidget(rightPanel)
        #layout.addStretch(1)
         
        #self.mainPanels = layout  
        self.setLayout(layout)

        self.wanoListWidget = WFEWaNoListWidget(self)
        self.ctrlListWidget = WFEListWidget(self, self._controls)
        self.workflowListWidget = WFEWorkflowistWidget(self)
        
        leftPanel.addWidget(QLabel('Nodes'))
        leftPanel.addWidget(self.wanoListWidget)
        leftPanel.addWidget(QLabel('Workflows'))      
        leftPanel.addWidget(self.workflowListWidget)
        leftPanel.addWidget(QLabel('Controls'))
        leftPanel.addWidget(self.ctrlListWidget)

        rightPanel.addWidget(self.registrySelection)
        rightPanel.addWidget(self.wanoEditor)
        
        self.lastActive = None

    def __init__(self, parent=None):
        super(WFEditor, self).__init__(parent)
        self.logger = logging.getLogger('WFELOG')
        self.__init_ui()
        self.registrySelection.registrySelectionChanged.connect(self.registry_changed)

    def update_wano_list(self, wanos):
        self.wanoListWidget.update_list(wanos)

    def update_saved_workflows_list(self, workflows):
        self.workflowListWidget.update_list(workflows)

    def update_registries(self, registries, selected=0):
        self.registrySelection.update_registries(registries, index=selected)

    def deactivateWidget(self):
        if self.lastActive != None:
            self.lastActive.setColor(Qt.lightGray)
            self.lastActive = None
       
        
    def openWaNoEditor(self,wanoWidget,varExports,fileExports,waNoNames):
        if self.wanoEditor.init(wanoWidget.wano,varExports,fileExports,waNoNames):
            wanoWidget.setColor(Qt.green)
            self.lastActive = wanoWidget
    
    def openWorkFlow(self,workFlow):
        self.workflowWidget.openWorkFlow(workFlow)
        
     
        
    def SizeHint(self):
        s = QSize()
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
        self.workflowListWidget.update()
        
    def saveAs(self):
        self.workflowWidget.saveAs()
        self.workflowListWidget.update()
        
    def loadFile(self,fileName):
        self.workflowWidget.loadFile(fileName)
