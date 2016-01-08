from PySide.QtGui import QWidget, QComboBox, QLabel, QHBoxLayout
from PySide.QtCore import Signal, Slot


class WaNoRegistrySelection(QWidget):
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
        self.isConnectedIcon.setStyleSheet(
                "background-color: %s; " \
                "font-weight: bold; " \
                "font-size: 20px;" % ['red', 'green'][self.is_connected]
            );


    def setStatus(self, is_connected):
        self.is_connected = is_connected
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
        self.setStatus(False)
        self.__emit_signal = True
        self.__connect_signals()
