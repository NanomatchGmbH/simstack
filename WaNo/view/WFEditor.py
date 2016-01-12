import logging
import os
from PySide.QtGui import QWidget, QSizePolicy, QLabel, QSplitter, QHBoxLayout, \
        QTabWidget
from PySide.QtCore import Qt, Signal

from .WaNoEditorWidget import WaNoEditor
from .WFEditorPanel import WFTabsWidget
from .WaNoRegistrySelection import WaNoRegistrySelection
from .WFEditorWidgets import WFEWaNoListWidget, WFEListWidget, WFEWorkflowistWidget
from .WFEditorLogTab import LogTab

class WFEditor(QWidget):
    REGISTRY_CONNECTION_STATES = WaNoRegistrySelection.CONNECTION_STATES

    _controls = [
            ("ForEach", "ctrl_img/ForEach.png"),
            ("If", "ctrl_img/If.png"),
            ("Parallel", "ctrl_img/Parallel.png"),
            ("While", "ctrl_img/While.png")
        ]

    registry_changed        = Signal(int, name="RegistryChanged")
    disconnect_registry     = Signal(name='disconnectRegistry')
    connect_registry        = Signal(int, name='connectRegistry')


    def __build_infobox(self):
        infobox = QTabWidget(self)
        infobox.setTabsClosable(False)
        infobox.addTab(LogTab(), "Log")
        infobox.addTab(QWidget(), "Copyright")
        return infobox

    def __init_ui(self):
        self.wanoEditor = WaNoEditor(self) # make this first to enable logging
        self.wanoEditor.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
        
        self.workflowWidget = WFTabsWidget(self)
        self.workflowWidget.setAcceptDrops(True)
        self.workflowWidget.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

        self.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)

        self.registrySelection = WaNoRegistrySelection(self)

        infobox = self.__build_infobox()

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
        rightPanel.addWidget(infobox)
        
        self.lastActive = None

    def _convert_ctrl_icon_paths_to_absolute(self):
        script_path=os.path.dirname(os.path.realpath(__file__))

        for i in range(len(self._controls)):
            self._controls[i] =(self._controls[i][0], os.path.join(script_path,"..",self._controls[i][1]))

        #import pprint

        #pprint.pprint(self._controls)

    def _connect_signals(self):
        self.registrySelection.registrySelectionChanged.connect(self.registry_changed)
        self.registrySelection.connect_registry.connect(self.connect_registry)
        self.registrySelection.disconnect_registry.connect(self.disconnect_registry)

    def __init__(self, parent=None):
        super(WFEditor, self).__init__(parent)
        self._convert_ctrl_icon_paths_to_absolute()
        self.logger = logging.getLogger('WFELOG')
        self.__init_ui()
        self._connect_signals()

    def update_wano_list(self, wanos):
        self.wanoListWidget.update_list(wanos)

    def update_saved_workflows_list(self, workflows):
        self.workflowListWidget.update_list(workflows)

    def update_registries(self, registries, selected=0):
        self.registrySelection.update_registries(registries, index=selected)

    def set_registry_connection_status(self, status):
        self.registrySelection.setStatus(status)

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
