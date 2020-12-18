import logging
import os
from Qt.QtWidgets import QWidget, QSizePolicy, QLabel, QSplitter, QHBoxLayout, \
            QTabWidget, QTreeView
from Qt.QtCore import Qt, Signal

from .WaNoEditorWidget import WaNoEditor
from .WFEditorPanel import WFTabsWidget
from .WaNoRegistrySelection import WaNoRegistrySelection
from .WFEditorWidgets import WFEWaNoListWidget, WFEListWidget, WFEWorkflowistWidget
from .WFEditorLogTab import LogTab
from .WFRemoteFileSystem import WFRemoteFileSystem

class WFEditor(QWidget):
    REGISTRY_CONNECTION_STATES = WaNoRegistrySelection.CONNECTION_STATES

    _controls = [
            #("SubWorkflow", "ctrl_img/ForEach.png"),
            ("ForEach", "ctrl_img/ForEach.png"),
            ("If", "ctrl_img/If.png"),
            ("Parallel", "ctrl_img/Parallel.png"),
            ("While", "ctrl_img/While.png")
        ]

    registry_changed        = Signal(int, name="RegistryChanged")
    disconnect_registry     = Signal(name='disconnectRegistry')
    connect_registry        = Signal(int, name='connectRegistry')

    request_job_list_update     = Signal(name="requestJobListUpdate")
    request_worflow_list_update = Signal(name="requestWorkflowListUpdate")
    request_job_update          = Signal(str, name="requestJobUpdate")
    request_worflow_update      = Signal(str, name="requestWorkflowUpdate")
    request_directory_update    = Signal(str, name="requestDirectoryUpdate")
    download_file               = Signal(str, name="downloadFile")
    upload_file_to              = Signal(str, name="uploadFile")
    delete_file                 = Signal(str, name="deleteFile")
    delete_job                  = Signal(str, name="deleteJob")
    abort_job                   = Signal(str, name="abortJob")
    browse_workflow             = Signal(str, name="browseWorkflow")
    delete_workflow             = Signal(str, name="deleteWorkflow")
    abort_workflow              = Signal(str, name="abortWorkflow")

    workflow_saved              = Signal(bool, str, name="WorkflowSaved")



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

        #infobox = self.__build_infobox()

        leftPanel = QSplitter(Qt.Vertical)
        leftPanel.setSizePolicy(QSizePolicy.Maximum,QSizePolicy.Expanding)
        leftPanel.setMaximumWidth(150)
        leftPanel.setMinimumWidth(150)

        rightPanel = QSplitter(Qt.Vertical)
        rightPanel.setSizePolicy(QSizePolicy.Fixed,QSizePolicy.Expanding)


        layout = QHBoxLayout()

        #hbox_splitter = QSplitter(Qt.Horizontal)
        #layout.addWidget(self.fileTreePanel)
        layout.addWidget(leftPanel)
        layout.addWidget(self.workflowWidget)
        layout.addWidget(rightPanel)
        """
        hbox_splitter.addWidget(leftPanel)
        hbox_splitter.setStretchFactor(0,2)
        hbox_splitter.addWidget(self.workflowWidget)
        hbox_splitter.setStretchFactor(1, 4)
        hbox_splitter.addWidget(rightPanel)
        hbox_splitter.setStretchFactor(2, 2)
        layout.addWidget(hbox_splitter)
        """
        #layout.addStretch(1)
         
        #self.mainPanels = layout  
        self.setLayout(layout)

        self.wanoListWidget = WFEWaNoListWidget(self)
        self.ctrlListWidget = WFEListWidget(self, self._controls)
        self.workflowListWidget = WFEWorkflowistWidget(self)

        self.remoteFileTree = WFRemoteFileSystem(self)

        nodelabel = QLabel('Nodes')

        #0
        leftPanel.addWidget(nodelabel)
        leftPanel.setStretchFactor(0, 0)
        #1
        leftPanel.addWidget(self.wanoListWidget)
        leftPanel.setStretchFactor(1, 1)
        #2
        leftPanel.addWidget(QLabel('Workflows'))
        leftPanel.setStretchFactor(2, 0)
        #3
        leftPanel.addWidget(self.workflowListWidget)
        leftPanel.setStretchFactor(3, 1)
        #4
        leftPanel.addWidget(QLabel('Controls'))
        leftPanel.setStretchFactor(4, 0)
        #5
        leftPanel.addWidget(self.ctrlListWidget)
        leftPanel.setStretchFactor(5, 1)


        self.settingsAndFilesTabs = QTabWidget()
        self.settingsAndFilesTabs.setTabsClosable(False)
        self.wanoSettingsTab = self.settingsAndFilesTabs.addTab(
                self.wanoEditor, "WaNo Settings")
        self.fileSystemTab = self.settingsAndFilesTabs.addTab(
                self.remoteFileTree, "Jobs && Workflows")

        rightPanel.addWidget(self.registrySelection)
        rightPanel.setStretchFactor(0, 0)
        rightPanel.addWidget(self.settingsAndFilesTabs)
        rightPanel.setStretchFactor(1, 1)
#        rightPanel.addWidget(infobox)

        
        self.lastActive = None



    def _convert_ctrl_icon_paths_to_absolute(self):
        script_path=os.path.dirname(os.path.realpath(__file__))

        for i in range(len(self._controls)):
            self._controls[i] = (self._controls[i][0], os.path.join(script_path,"..",self._controls[i][1]))

        #import pprint

        #pprint.pprint(self._controls)

    def _connect_signals(self):
        self.registrySelection.registrySelectionChanged.connect(self.registry_changed)
        self.registrySelection.connect_registry.connect(self.connect_registry)
        self.registrySelection.disconnect_registry.connect(self.disconnect_registry)

        self.remoteFileTree.request_job_list_update.connect(self.request_job_list_update)
        self.remoteFileTree.request_worflow_list_update.connect(self.request_worflow_list_update)
        self.remoteFileTree.request_job_update.connect(self.request_job_update)
        self.remoteFileTree.request_worflow_update.connect(self.request_worflow_update)
        self.remoteFileTree.request_directory_update.connect(self.request_directory_update)
        self.remoteFileTree.download_file.connect(self.download_file)
        self.remoteFileTree.upload_file_to.connect(self.upload_file_to)
        self.remoteFileTree.delete_job.connect(self.delete_job)
        self.remoteFileTree.abort_job.connect(self.abort_job)
        self.remoteFileTree.browse.connect(self.browse_workflow)
        self.remoteFileTree.delete_workflow.connect(self.delete_workflow)
        self.remoteFileTree.abort_workflow.connect(self.abort_workflow)
        self.remoteFileTree.delete_file.connect(self.delete_file)

        self.workflowWidget.workflow_saved.connect(self.workflow_saved)

    def resizeEvent(self, *args, **kwargs):
        self.workflowWidget.relayout()

    def __init__(self, parent=None):
        super(WFEditor, self).__init__(parent)
        self._convert_ctrl_icon_paths_to_absolute()
        self.logger = logging.getLogger('WFELOG')
        self.__init_ui()
        self._connect_signals()
        self.resizeEvent()
        self.wanoSettingsTab    = 0
        self.fileSystemTab      = 0

    def update_wano_list(self, wanos):
        self.wanos = wanos
        self.wanoListWidget.update_list(wanos)

    def update_saved_workflows_list(self, workflows):
        self.workflowListWidget.update_list(workflows)

    def update_registries(self, registries, selected=0):
        self.registrySelection.update_registries(registries, index=selected)

    def update_filesystem_model(self, path, files):
        self.remoteFileTree.update_file_tree_node(path, files)

    def update_job_list(self, jobs):
        self.remoteFileTree.update_job_list(jobs)

    def update_workflow_list(self, wfs):
        self.remoteFileTree.update_workflow_list(wfs)

    def set_registry_connection_status(self, status):
        self.registrySelection.setStatus(status)

    def deactivateWidget(self):
        if self.lastActive != None:
            self.lastActive.setColor(Qt.lightGray)
            self.lastActive = None
       
        
    def openWaNoEditor(self,wanoWidget):
        if self.wanoEditor.init(wanoWidget.wano_view):
            self.settingsAndFilesTabs.setCurrentIndex(self.wanoSettingsTab)
            wanoWidget.setColor(Qt.green)
            self.lastActive = wanoWidget
    
    def openWorkFlow(self,workFlow):
        self.workflowWidget.openWorkFlow(workFlow)

    def remove(self,wfwanowidget):
        if wfwanowidget.is_wano:
            self.wanoEditor.remove_if_open(wfwanowidget.wano_view)

    """
    def SizeHint(self):
        s = QSize()
        if self.wanoEditor == None:
            s.setWidth(400)
        else:
            s.setWidth(800)
        s.setHeight(600)
        return s
    """
    
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

    def run(self):
        return self.workflowWidget.run()

    def loadFile(self,fileName):
        self.workflowWidget.loadFile(fileName)

