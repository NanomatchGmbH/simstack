import os
from Qt.QtWidgets import QWidget, QComboBox, QPushButton, QHBoxLayout, QSizePolicy
from Qt.QtGui import QPixmap, QIcon

from Qt.QtCore import Signal, Slot, QSize

from enum import Enum


class WaNoRegistrySelection(QWidget):
    class CONNECTION_STATES(Enum):
        connected = 0
        connecting = 1
        disconnected = 2

    __text = [
            "Disconnect",
            "[Connecting]",
            "Connect",
        ]
    __icons = [
            'cs-xlet-running.svg',
            'cs-xlet-update.svg',
            'cs-xlet-error.svg',
        ]

    registrySelectionChanged    = Signal(int, name='registrySelectionChanged')
    disconnect_registry          = Signal(name='disconnectRegistry')
    connect_registry             = Signal(int, name='connectRegistry')

    def select_registry(self, index):
        self.registryComboBox.setCurrentIndex(index)

    def update_registries(self, registies, index=0):
        self.__emit_signal = False
        self.registryComboBox.clear()
        for r in registies:
            self.registryComboBox.addItem(r)
        self.select_registry(index)
        self.__emit_signal = True

    def get_iconpath(self,icon):
        script_path = os.path.dirname(os.path.realpath(__file__))
        media_path = os.path.join(script_path, "..", "Media","icons")
        imagepath = os.path.join(media_path, icon)
        return imagepath

    def __update_status(self):
        p = QPixmap(self.get_iconpath(self.__icons[self.__status.value]))
        buttonIcon = QIcon(p)
        self.isConnectedIcon.setIcon(buttonIcon)
        self.isConnectedIcon.setText(self.__text[self.__status.value])

    def setStatus(self, status):
        self.__status = status
        self.__update_status()

    def __init_ui(self, parent):
        button_height = 20
        self.registryComboBox   = QComboBox(self)
        self.isConnectedIcon    = QPushButton(self)
        #self.isConnectedIcon.resize(self.isConnectedIcon.sizeHint())

        self.isConnectedIcon.setFixedSize(100, button_height)
        self.isConnectedIcon.setIconSize(QSize(button_height, button_height))

        layout = QHBoxLayout(self)
        layout.addWidget(self.registryComboBox)
        layout.addWidget(self.isConnectedIcon)
        self.setLayout(layout)
        #self.resize(self.sizeHint())

    def __on_selection_changed(self, index):
        if self.__emit_signal:
            self.registrySelectionChanged.emit(index)

    def __on_button_clicked(self):
        if self.__status == self.CONNECTION_STATES.connected:
            self.disconnect_registry.emit()
        elif self.__status == self.CONNECTION_STATES.disconnected:
            self.connect_registry.emit(self.registryComboBox.currentIndex())

    def __connect_signals(self):
        self.isConnectedIcon.clicked.connect(self.__on_button_clicked)
        self.registryComboBox.currentIndexChanged.connect(self.__on_selection_changed)

    def __init__(self, parent):
        super(WaNoRegistrySelection, self).__init__(parent)
        self.setSizePolicy(QSizePolicy.Minimum,QSizePolicy.Minimum)
        self.__init_ui(parent)
        self.setStatus(WaNoRegistrySelection.CONNECTION_STATES.disconnected)
        self.__emit_signal = True
        self.__connect_signals()
