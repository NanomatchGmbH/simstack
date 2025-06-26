import logging

import PySide6.QtCore as QtCore
import PySide6.QtGui as QtGui
import PySide6.QtWidgets as QtWidgets

from SimStackServer.WaNo.MiscWaNoTypes import WaNoListEntry


class WFEListWidget(QtWidgets.QListWidget):
    def __init__(self, parent=None, controls=[]):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.update_list(controls)

    def update_list(self, controls):
        for name, icon in controls:
            item = QtWidgets.QListWidgetItem(name)
            item.setIcon(QtGui.QIcon(icon))
            self.addItem(item)
        self.myHeight = 10
        self.sortItems()

    def sizeHint(self):
        return QtCore.QSize(100, self.myHeight)


class WFEWaNoListWidget(QtWidgets.QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.myHeight = 10

    def update_list(self, wanos):
        self.clear()
        for wano in wanos:
            wano: WaNoListEntry
            item = QtWidgets.QListWidgetItem(wano.name)
            wano_icon = wano.icon
            item.setIcon(QtGui.QIcon(wano_icon))
            self.addItem(item)
            item.WaNo = wano
        self.myHeight = self.count() * 10
        self.sortItems()

    def sizeHint(self):
        return QtCore.QSize(100, max(self.myHeight, 200))


class WFEWorkflowistWidget(QtWidgets.QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger("WFEOG")
        self.setDragEnabled(True)
        self.myHeight = 10
        self.itemDoubleClicked.connect(self.openWf)

    def openWf(self, pressedItem):
        self.parent().parent().openWorkFlow(pressedItem.workflow)

    def update_list(self, workflows):
        self.clear()

        for element in workflows:
            item = QtWidgets.QListWidgetItem(element.name)

            item.workflow = element
            self.addItem(item)
        self.myHeight = self.count() * 10
        self.sortItems()

    def sizeHint(self):
        return QtCore.QSize(100, max(self.myHeight, 100))
