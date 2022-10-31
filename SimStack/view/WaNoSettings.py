from os.path import join

from Qt.QtWidgets import QDialog, QLabel, QGridLayout, QLineEdit, QPushButton, \
        QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QTabBar, \
        QToolButton, QFileIconProvider, QFileDialog, QComboBox
import Qt.QtWidgets as QtWidgets
from Qt.QtGui import QIntValidator
from Qt.QtCore import Signal, QSignalMapper, QDir
import Qt.QtCore as QtCore

from SimStackServer.Settings.ClusterSettingsProvider import ClusterSettingsProvider
from SimStackServer.WorkflowModel import Resources
from SimStack.lib.QtClusterSettingsProvider import QtClusterSettingsProvider
from SimStack.view.ResourcesView import ResourcesView


class WaNoPathSettings(QDialog):
    def __init__(self,pathsettings,parent):
        self.pathsettings = pathsettings
        super(WaNoPathSettings,self).__init__(parent=parent)
        self.__init_ui()

    def __showLocalDialogWaNo(self):
        self.__showLocalDialogHelper(self.wanopath)

    def __showLocalDialogWorkflow(self):
        self.__showLocalDialogHelper(self.workflowpath)

    def __showLocalDialogHelper(self, qlineedit):
        dirname = QFileDialog.getExistingDirectory(self, 'Choose Directory', QDir.homePath())
        if dirname:
            dirname = QDir.toNativeSeparators(dirname)
            qlineedit.setText(dirname)

    def get_settings(self):
        rdict = {"wanoRepo" : self.wanopath.text(),
                 "workflows": self.workflowpath.text()
                 }
        return rdict

    def __init_ui(self):
        self.setWindowTitle("Select Paths")
        layout = QVBoxLayout()
        upper = QWidget(parent = self)
        lower = QWidget(parent=self)

        upperlayout = QGridLayout(self)

        upperlayout.addWidget(QLabel("Workflow Workspace"),0, 0)
        upperlayout.addWidget(QLabel("WaNo Repository"), 1, 0)
        self.workflowpath = QLineEdit("Workflow Path")
        self.workflowpath.setText(self.pathsettings["workflows"])
        self.wanopath = QLineEdit("WaNo Path")
        self.wanopath.setText(self.pathsettings["wanoRepo"])

        upperlayout.addWidget(self.workflowpath, 0, 1)
        upperlayout.addWidget(self.wanopath, 1, 1)

        self.workflowpicker = QPushButton("")
        self.workflowpicker.setIcon(QFileIconProvider().icon(QFileIconProvider.Folder))
        self.workflowpicker.pressed.connect(self.__showLocalDialogWorkflow)

        self.wanopicker = QPushButton("")
        self.wanopicker.setIcon(QFileIconProvider().icon(QFileIconProvider.Folder))
        self.wanopicker.pressed.connect(self.__showLocalDialogWaNo)

        upperlayout.addWidget(self.workflowpicker, 0, 2)
        upperlayout.addWidget(self.wanopicker, 1, 2)

        upper.setLayout(upperlayout)

        lowerlayout = QHBoxLayout()
        self.cancel = QPushButton("Cancel")
        self.save = QPushButton("Save")
        self.cancel.clicked.connect(self._on_cancel)
        self.save.clicked.connect(self._on_save)
        lowerlayout.addWidget(self.cancel)
        lowerlayout.addWidget(self.save)

        lower.setLayout(lowerlayout)

        layout.addWidget(upper)
        layout.addWidget(lower)

        self.setLayout(layout)

    def _on_save(self):
        self.accept()

    def _on_cancel(self):
        self.reject()

class WaNoTabButtonsWidget(QWidget):
    addClicked      = Signal(name='onAddClicked')
    removeClicked   = Signal(name='onRemoveClicked')

    def __connect_signals(self):
        self.__btn_addRegistry.clicked.connect(self.addClicked)
        self.__btn_removeRegistry.clicked.connect(self.removeClicked)

    def disable_remove(self):
        self.__btn_removeRegistry.setEnabled(False)

    def enable_remove(self):
        self.__btn_removeRegistry.setEnabled(True)

    def __init_ui(self):
        layout = QHBoxLayout(self)

        self.__btn_addRegistry          = QToolButton(self)
        self.__btn_removeRegistry       = QToolButton(self)

        self.__btn_addRegistry.setText("+")
        self.__btn_removeRegistry.setText("-")

        self.__btn_addRegistry.setToolTip("Add Registry")
        self.__btn_removeRegistry.setToolTip("Remove Registry")

        self.__btn_addRegistry.resize(self.__btn_addRegistry.sizeHint())
        self.__btn_removeRegistry.resize(self.__btn_removeRegistry.sizeHint())

        layout.addWidget(self.__btn_addRegistry)
        layout.addWidget(self.__btn_removeRegistry)

        self.setLayout(layout)
        self.resize(self.sizeHint())

    def __init__(self, config):
        super(WaNoTabButtonsWidget, self).__init__()
        self.__init_ui()
        self.__connect_signals()

class SimStackClusterSettingsView(QDialog):
    DEFAULT_NAME = "[Unnamed Registry]"

    def __init__(self):
        super().__init__()
        self.__tabs     = None
        self._registries = QtClusterSettingsProvider.get_registries()
        self.__init_ui()
        self._init_tabs()
        self.__connect_signals()

    def __on_save(self):
        QtClusterSettingsProvider.get_instance().write_settings()
        self.accept()

    def __on_cancel(self):
        self.reject()

    def _init_tabs(self):
        for tab_id, (registry_name, resource) in enumerate(self._registries.items()):
            self.__add_tab(registry_name, self.__tabs.count() -1, resource)
            if tab_id == 0:
                self.__tabs.setCurrentIndex(self.__tabs.count() - 1)

    def __add_tab(self, name, index, resource = None):
        if resource is None:
            resource = Resources(resource_name = name)
        tabWidget = ResourcesView(resource, render_type="clustersettings")
        self.__tabs.addTab(tabWidget, name)
        return tabWidget


    def __on_add_registry(self):
        clustername,ok = QtWidgets.QInputDialog.getText(self, self.tr("Specify Cluster Name"),
                                     self.tr("Name"), QtWidgets.QLineEdit.Normal,
                                     "Cluster Name")
        if ok:
            if clustername in self._registries:
                # warn and return
                message = f"Clustername {clustername} already exists. Please remove first."
                QtWidgets.QMessageBox.critical(None, "Clustername already exists.", message)
                return
            csp = QtClusterSettingsProvider.get_instance()
            new_resource = csp.add_resource(resource_name=clustername)
            print(new_resource.resource_name)
            self.__add_tab(clustername, self.__tabs.count() - 1, resource=new_resource)
            self.__tabs.setCurrentIndex(self.__tabs.count() - 1)

    def __connect_signals(self):
        self.__tab_buttons.addClicked.connect(self.__on_add_registry)
        self.__tab_buttons.removeClicked.connect(self.__on_remove_registry)
        self.__btn_save.clicked.connect(self.__on_save)
        self.__btn_cancel.clicked.connect(self.__on_cancel)

    def __on_remove_registry(self):
        # -1 for tab buttons
        index = self.__tabs.currentIndex()
        if (index > 0):
            registry_name = self.__tabs.tabText(index)
            csp = QtClusterSettingsProvider.get_instance()
            csp.remove_resource(registry_name)
            self.__tabs.removeTab(index)

        if (self.__tabs.count() == 1):
            self.__tab_buttons.disable_remove()

    def __title_edited(self, index):
        tabWidget = self.__tabs.widget(index)
        if (not tabWidget is None):
            text = tabWidget.get_name()
            self.__tabs.setTabText(index, text if text != "" else self.DEFAULT_NAME)

    def __init_ui(self):
        layout = QVBoxLayout(self)
        self.__tabs = QTabWidget(self)
        self.__tab_buttons = WaNoTabButtonsWidget(self)

        self.__btn_save = QPushButton(self)
        self.__btn_cancel = QPushButton(self)

        self.__btn_save.setText("Save")
        self.__btn_cancel.setText("Cancel")
        default_label = QLabel('Add Registry by clicking \"+\"')
        default_label.setAlignment(QtCore.Qt.AlignCenter)
        self.__tabs.addTab(default_label, '')
        self.__tabs.setTabEnabled(0, False)
        self.__tabs.setUsesScrollButtons(True)
        self.__tabs.tabBar().setTabButton(0, QTabBar.RightSide, self.__tab_buttons)

        layout.addWidget(self.__tabs)
        layout.addWidget(self.__btn_save)
        layout.addWidget(self.__btn_cancel)
        self.setLayout(layout)

        self.setMinimumSize(420, 520)
