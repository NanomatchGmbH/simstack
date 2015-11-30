from PySide.QtGui import QDialog, QLabel, QGridLayout, QLineEdit, QPushButton, \
        QTabWidget
from PySide.QtCore import Signal


class WaNoRegistrySettings(QWidget):
    def __init_ui(self):
        grid = QGridLayout(self)

        self.__label_registryName = QLabel(self)
        self.__label_baseUri      = QLabel(self)
        self.__label_username     = QLabel(self)
        self.__label_password     = QLabel(self)

        self.__label_registryName.setText("<b>Registry Name</b>")
        self.__label_baseUri.setText("<b>Base URI</b>")
        self.__label_username.setText("<b>Username</b>")
        self.__label_password.setText("<b>Password</b>")

        self.__registryName = QLineEdit(self)
        self.__baseUri      = QLineEdit(self)
        self.__username     = QLineEdit(self)
        self.__password     = QLineEdit(self)


        grid.addWidget(self.__label_registryName, 0, 0)
        grid.addWidget(self.__label_baseUri     , 1, 0)
        grid.addWidget(self.__label_username    , 2, 0)
        grid.addWidget(self.__label_password    , 3, 0)

        grid.addWidget(self.__registryName, 0, 1 )
        grid.addWidget(self.__baseUri     , 1, 1 )
        grid.addWidget(self.__username    , 2, 1 )
        grid.addWidget(self.__password    , 3, 1 )

    def __init__(self, config):
        self.__init_ui

class WaNoUnicoreSettings(QDialog):
    on_save_config = Signal(dict, name='onSaveConfig')

    def __update(self, config):
        if self.__tabs is None:
            raise RuntimeError("WaNoUnicoreSettings not initialized correctly")

        for registry in config['registries']:
            tabWidget = WaNoRegistrySettings(registry)
            self.__tabs.addTab(registy['name'], tabWidget)

    def __init_ui(self):
        self.__tabs = QTabWidget(self)
        self.__addRegistryBtn = QPushButton(self)
        self.__removeRegistryBtn = QPushButton(self)

    def __init__(self, config):
        self.__tabs     = None
        self.__config   = config
        self.__init_ui()
