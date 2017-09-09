from Qt.QtWidgets import QDialog, QLabel, QGridLayout, QLineEdit, QPushButton, \
        QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QCheckBox, QTabBar, \
        QToolButton, QFileIconProvider, QFileDialog
from Qt.QtCore import Signal, QSignalMapper, QDir


class WaNoPathSettings(QDialog):
    def __init__(self,pathsettings,parent):
        self.pathsettings = pathsettings
        print(self.pathsettings)
        super(WaNoPathSettings,self).__init__(parent=parent)
        self.__init_ui()

    def __showLocalDialogWaNo(self):
        self.__showLocalDialogHelper(self.wanopath)

    def __showLocalDialogWorkflow(self):
        self.__showLocalDialogHelper(self.workflowpath)

    def __showLocalDialogHelper(self, qlineedit):
        dirname = QFileDialog.getExistingDirectory(self, 'Choose Directory', QDir.homePath())
        if dirname:
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


class WaNoRegistrySettings(QWidget):
    title_edited = Signal(str, name='titleEdited')
    default_set  = Signal(bool, name='defaultSet')
    
    def get_name(self):
        return self.__registryName.text()

    def get_uri(self):
        return self.__baseUri.text()

    def get_user(self):
        return self.__username.text()

    def get_password(self):
        return self.__password.text()

    def get_default(self):
        return self.__cb_default.isChecked()

    def get_ca_package(self):
        return self.__ca_package.text()

    def get_workflows(self):
        return self.__workflows.text()

    def __on_title_edited(self):
        self.title_edited.emit(str(self.__registryName.text()))

    def __on_password_show(self):
        if (self.__cb_show_password.isChecked()):
            self.__password.setEchoMode(QLineEdit.Normal)
        else:
            self.__password.setEchoMode(QLineEdit.Password)

    def __on_default_set(self):
        self.default_set.emit(self.__cb_default.isChecked())

    def __on_show_cert_filepicker(self):
        fname, success = QFileDialog.getOpenFileName(self, 'Select cacert.pem', QDir.homePath())
        if success:
            self.__ca_package.setText(fname)

    def __connect_signals(self):
        self.__registryName.editingFinished.connect(self.__on_title_edited)
        self.__cb_show_password.stateChanged.connect(self.__on_password_show)
        self.__cb_default.stateChanged.connect(self.__on_default_set)
        self.__cert_openfilebutton.pressed.connect(self.__on_show_cert_filepicker)

    def __init_ui(self):
        grid = QGridLayout(self)

        self.__label_registryName   = QLabel(self)
        self.__label_baseUri        = QLabel(self)
        self.__label_username       = QLabel(self)
        self.__label_password       = QLabel(self)
        self.__label_ca_package     = QLabel(self)
        self.__label_workflows      = QLabel(self)

        self.__label_registryName.setText("<b>Registry Name</b>")
        self.__label_baseUri.setText("<b>Base URI</b>")
        self.__label_username.setText("<b>Username</b>")
        self.__label_password.setText("<b>Password</b>")
        self.__label_ca_package.setText("<b>Certificate Path</b>")
        self.__label_workflows.setText("<b>Workflow Link</b>")

        self.__registryName = QLineEdit(self)
        self.__baseUri      = QLineEdit(self)
        self.__username     = QLineEdit(self)
        self.__password     = QLineEdit(self)
        self.__ca_package   = QLineEdit(self)
        self.__workflows    = QLineEdit(self)

        self.__password.setEchoMode(QLineEdit.Password)

        self.__cb_show_password = QCheckBox(self)
        self.__cb_show_password.setText("show")
        self.__cb_show_password.setChecked(False)

        self.__cb_default = QCheckBox(self)
        self.__cb_default.setText("is default")
        self.__cb_default.setChecked(False)

        self.__cert_openfilebutton = QPushButton("",parent=self)

        self.__cert_openfilebutton.setIcon(QFileIconProvider().icon(QFileIconProvider.File))

        grid.addWidget(self.__label_registryName, 0, 0)
        grid.addWidget(self.__label_baseUri     , 1, 0)
        grid.addWidget(self.__label_username    , 2, 0)
        grid.addWidget(self.__label_password    , 3, 0)
        grid.addWidget(self.__label_ca_package  , 4, 0)
        grid.addWidget(self.__label_workflows   , 5, 0)

        grid.addWidget(self.__registryName,         0, 1 )
        grid.addWidget(self.__baseUri,              1, 1 )
        grid.addWidget(self.__username,             2, 1 )
        grid.addWidget(self.__password,             3, 1 )
        grid.addWidget(self.__cb_show_password,     3, 2 )
        grid.addWidget(self.__ca_package,           4, 1 )
        grid.addWidget(self.__cert_openfilebutton,  4, 2 )
        grid.addWidget(self.__workflows,            5, 1 )

        self.setLayout(grid)

    def set_default(self, is_default):
        self.__cb_default.setChecked(is_default)

    def set_fields(self, name, uri, user, password, ca_package, workflows, is_default):
        self.__registryName.setText(name)
        self.__baseUri.setText(uri)
        self.__username.setText(user)
        self.__password.setText(password)
        self.__ca_package.setText(ca_package)
        self.__workflows.setText(workflows)
        self.set_default(is_default)

    def __init__(self):
        super(WaNoRegistrySettings, self).__init__()
        self.__init_ui()
        self.__connect_signals()

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

class WaNoUnicoreSettings(QDialog):
    DEFAULT_NAME = "[Unnamed Registry]"

    def get_settings(self):
        registries = []
        for index in range(1, self.__tabs.count()):
            tabWidget = self.__tabs.widget(index)
            registries.append(
                    self.__build_registry_settings(
                        tabWidget.get_name(),
                        tabWidget.get_uri(),
                        tabWidget.get_user(),
                        tabWidget.get_password(),
                        tabWidget.get_ca_package(),
                        tabWidget.get_workflows(),
                        tabWidget.get_default()
                    )
                )

        return registries

    def __build_registry_settings(self, name, uri, user, password, ca_package, workflows,
            default):
        return {
                'name': name,
                'baseURI': uri,
                'username': user,
                'password': password,
                'ca_package': ca_package,
                'workflows': workflows,
                'default': default
            }

    def __add_tab(self, name, index):
        tabWidget = WaNoRegistrySettings()
        self.__tabs.addTab(tabWidget, name)

        # We want to identify the Tab by index -> +1 for tab buttons
        self.__signalMapper_title.setMapping(tabWidget, index + 1)
        tabWidget.title_edited.connect(self.__signalMapper_title.map)

        self.__signalMapper_default.setMapping(tabWidget, index + 1)
        tabWidget.default_set.connect(self.__signalMapper_default.map)

        return tabWidget


    def __on_add_registry(self):
        self.__add_tab(self.DEFAULT_NAME, self.__tabs.count() - 1)
        self.__tabs.setCurrentIndex(self.__tabs.count() - 1)

    def __on_remove_registry(self):
        # -1 for tab buttons
        index = self.__tabs.currentIndex()
        if (index > 0):
            tabWidget = self.__tabs.widget(index)
            self.__signalMapper_title.removeMappings(tabWidget)
            self.__signalMapper_default.removeMappings(tabWidget)
            self.__tabs.removeTab(index)

        if (self.__tabs.count() == 1):
            self.__tab_buttons.disable_remove()

    def __on_save(self):
        self.accept()

    def __on_cancel(self):
        self.reject()

    def __connect_signals(self):
        self.__tab_buttons.addClicked.connect(self.__on_add_registry)
        self.__tab_buttons.removeClicked.connect(self.__on_remove_registry)
        self.__btn_save.clicked.connect(self.__on_save)
        self.__btn_cancel.clicked.connect(self.__on_cancel)

        self.__signalMapper_title.mapped.connect(self.__title_edited)
        self.__signalMapper_default.mapped.connect(self.__on_default_set)

    def __title_edited(self, index):
        tabWidget = self.__tabs.widget(index)
        if (not tabWidget is None):
            text = tabWidget.get_name()
            self.__tabs.setTabText(index, text if text != "" else self.DEFAULT_NAME)

    def __on_default_set(self, index):
        tabWidget = self.__tabs.widget(index)
        if not self.__ignore_default_signal:
            self.__ignore_default_signal = True
            for i in [x for x in range(1, self.__tabs.count()) if x != index]:
                t = self.__tabs.widget(i)
                t.set_default(False)
            self.__ignore_default_signal = False

    def __update(self, config):
        if self.__tabs is None:
            raise RuntimeError("WaNoUnicoreSettings not initialized correctly")

        if not config is None and len(config) > 0:
            for i, registry in enumerate(config):
                tabWidget = self.__add_tab(registry['name'], i)
                tabWidget.set_fields(
                        registry['name'],
                        registry['baseURI'],
                        registry['username'],
                        registry['password'],
                        registry['ca_package'] if 'ca_package' in registry else '',
                        registry['workflows'] if 'workflows' in registry else '',
                        registry['is_default']
                )


            if (len(config) > 0):
                self.__tabs.setCurrentIndex(1) # not 0, because of tab buttons

    def __init_ui(self):
        layout = QVBoxLayout(self)
        self.__tabs                     = QTabWidget(self)
        self.__tab_buttons              = WaNoTabButtonsWidget(self)

        self.__btn_save                 = QPushButton(self)
        self.__btn_cancel               = QPushButton(self)

        self.__btn_save.setText("Save")
        self.__btn_cancel.setText("Cancel")

        #self.__tabs.setTabPosition(QTabWidget.TabPosition.West)
        self.__tabs.addTab(QLabel('Add Registry by clicking \"+\"'), '')
        self.__tabs.setTabEnabled(0, False)
        self.__tabs.setUsesScrollButtons(True)
        self.__tabs.tabBar().setTabButton(0, QTabBar.RightSide, self.__tab_buttons)
        

        layout.addWidget(self.__tabs)
        layout.addWidget(self.__btn_save)
        layout.addWidget(self.__btn_cancel)
        self.setLayout(layout)

        self.setMinimumSize(420, 420)

    def __init__(self, config):
        super(WaNoUnicoreSettings, self).__init__()
        self.__tabs     = None
        self.__config   = config

        self.__signalMapper_title       = QSignalMapper(self)
        self.__signalMapper_default     = QSignalMapper(self)
        self.__ignore_default_signal    = False

        self.__init_ui()

        self.__connect_signals()
        self.__update(config)
        self.get_settings()
