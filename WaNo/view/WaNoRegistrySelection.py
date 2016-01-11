from PySide.QtGui import QWidget, QComboBox, QLabel, QHBoxLayout, QPixmap
from PySide.QtCore import Signal, Slot

from enum import Enum


class WaNoRegistrySelection(QWidget):
    class CONNECTION_STATES(Enum):
        connected = 0
        connecting = 1
        disconnected = 2

    __icons = [
            'WaNo/Media/icons/cs-xlet-error.svg',
            'WaNo/Media/icons/cs-xlet-error.svg',
            'WaNo/Media/icons/cs-xlet-error.svg',
        ]

    registrySelectionChanged = Signal(int, name='registrySelectionChanged')

    def select_registry(self, index):
        self.registryComboBox.setCurrentIndex(index)

    def update_registries(self, registies, index=0):
        self.__emit_signal = False
        self.registryComboBox.clear()
        for r in registies:
            self.registryComboBox.addItem(r)
        self.select_registry(index)
        self.__emit_signal = True

    def __update_status(self):
        p = QPixmap(self.__icons[self.__status.value])
        self.isConnectedIcon.setPixmap(p.scaled(self.isConnectedIcon.size()))

    def setStatus(self, status):
        self.__status = status
        self.__update_status()

    def __init_ui(self, parent):
        self.registryComboBox   = QComboBox(self)
        self.isConnectedIcon    = QLabel(self)

        self.isConnectedIcon.setFixedSize(20, 20)

        layout = QHBoxLayout(self)
        layout.addWidget(self.registryComboBox)
        layout.addWidget(self.isConnectedIcon)
        self.resize(self.sizeHint())

    def __on_selection_changed(self, index):
        if self.__emit_signal:
            self.registrySelectionChanged.emit(index)

    def __connect_signals(self):
        self.registryComboBox.currentIndexChanged.connect(self.__on_selection_changed)

    def __init__(self, parent):
        super(WaNoRegistrySelection, self).__init__(parent)
        self.__init_ui(parent)
        self.setStatus(WaNoRegistrySelection.CONNECTION_STATES.disconnected)
        self.__emit_signal = True
        self.__connect_signals()
