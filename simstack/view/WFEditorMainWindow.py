import time
import os

import PySide6.QtGui as QtGui
import PySide6.QtWidgets as QtWidgets

from PySide6.QtCore import Signal

from .WaNoSettings import WaNoPathSettings, SimStackClusterSettingsView
from .ViewTimer import ViewTimer

from PySide6.QtCore import QMutex
from PySide6.QtWidgets import QMessageBox


class StatusMessageManager:
    def __sort(self):
        """Sorts by time of arrival, newest first.

        Note:
            self._list_lock must be held.
        """
        self._list.sort(key=lambda entry: entry[1])
        self._list.reverse()

    def update(self, elapsed_time):
        self._list_lock.lock()
        tmplist = []
        stringlist = []
        for e in self._list:
            time_left = e[2] - elapsed_time
            if time_left > 0:
                tmplist.append(e[:-1] + (time_left,))
                stringlist.append(e[0])
        self._list = tmplist

        self._stringlist = stringlist
        self.__set_text()

        self._list_lock.unlock()

    def __set_text(self):
        """
        Note:
            self._list_lock must be held.
        """
        self._callback(", ".join(self._stringlist))

    def stop(self):
        self._timer.stop()

    def add_message(self, message, duration=5):
        arrival = time.time()

        self._list_lock.lock()
        self._list.append((message, arrival, duration))
        self.__sort()

        self._stringlist.insert(0, message)
        self.__set_text()

        self._list_lock.unlock()

        self._timer.update_interval(duration)

    def __init__(self, callback):
        self._list = []
        self._list_lock = QMutex()
        self._callback = callback
        self._timer = ViewTimer(self.update)
        self._stringlist = []


class WFEditorMainWindow(QtWidgets.QMainWindow):
    new_file = Signal(name="NewFile")
    open_file = Signal(name="OpenFile")
    save = Signal(name="Save")
    save_as = Signal(name="SaveAs")
    save_registries = Signal(list, name="SaveRegistries")
    save_paths = Signal(dict, name="SavePaths")
    open_registry_settings = Signal(name="OpenRegistrySettings")
    open_path_settings = Signal(name="OpenPathSettings")
    exit_client = Signal(name="ExitClient")
    run = Signal(name="Run")

    def __init_ui(self, parent=None):
        script_path = os.path.dirname(os.path.realpath(__file__))
        media_path = os.path.join(script_path, "..", "Media")
        imagepath = os.path.join(media_path, "Logo_Nanomatch.png")
        self.setWindowIcon(QtGui.QIcon(imagepath))
        self.setCentralWidget(self.wfEditor)

        self._createActions()
        self.fileMenu = self.menuBar().addMenu("&File")
        # self.fileMenu.addAction(self.newAct)
        # self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.saveAct)
        self.fileMenu.addAction(self.saveAsAct)
        # self.fileMenu.addAction(self.printAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)

        self.runMenu = self.menuBar().addMenu("&Run")
        self.runMenu.addAction(self.runAct)

        self.settingsMenu = self.menuBar().addMenu("&Configuration")
        self.settingsMenu.addAction(self.configServAct)
        self.settingsMenu.addAction(self.configPathSettingsAct)

        message = "Welcome to the SimStack Framework"
        self.statusBar().showMessage(message)
        self._status_manager = StatusMessageManager(self.statusBar().showMessage)

        self.setWindowTitle("SimStack")

    def __init__(self, editor, parent=None):
        super(WFEditorMainWindow, self).__init__(parent)
        self.wfEditor = editor
        self.__init_ui()

    def show_status_message(self, message, duration):
        self._status_manager.add_message(message, duration)

    def closeEvent(self, event):
        if (
            QMessageBox.question(
                None,
                "",
                "Are you sure you want to quit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            == QMessageBox.Yes
        ):
            event.accept()
            self.exit()
        else:
            event.ignore()

    def exit(self):
        self.exit_client.emit()
        self._status_manager.stop()
        self.close()

    def action_openSettingsDialog(self):
        self.open_registry_settings.emit()

    def action_openPathSettingsDialog(self):
        self.open_path_settings.emit()

    def open_dialog_registry_settings(self, current_registries):
        dialog = SimStackClusterSettingsView()

        if dialog.exec_():
            pass
        else:
            pass

    def open_dialog_path_settings(self, pathsettings):
        dialog = WaNoPathSettings(parent=self, pathsettings=pathsettings)
        if dialog.exec_():
            self.save_paths.emit(dialog.get_settings())
        else:
            pass

    def action_newFile(self):
        self.new_file.emit()

    def action_open(self):
        self.open_file.emit()

    def action_save(self):
        self.save.emit()

    def action_saveAs(self):
        self.save_as.emit()

    def action_print_(self):
        self.infoLabel.setText("Invoked <b>File|Print</b>")

    def action_close(self):
        self.exit()

    def action_about(self):
        self.infoLabel.setText("Invoked <b>Help|About</b>")
        QtWidgets.QMessageBox.about(
            self,
            "About Menu",
            "The <b>Menu</b> example shows how to create menu-bar menus "
            "and context menus.",
        )

    def action_aboutWFE(self):
        pass
        # self.infoLabel.setText("Invoked <b>Help|About Qt</b>")

    def action_run(self):
        self.run.emit()

    def _createActions(self):
        self.newAct = QtGui.QAction(
            "&New",
            self,
            shortcut=QtGui.QKeySequence.New,
            statusTip="Create a new file",
            triggered=self.action_newFile,
        )

        self.openAct = QtGui.QAction(
            "&Open...",
            self,
            shortcut=QtGui.QKeySequence.Open,
            statusTip="Open an existing file",
            triggered=self.action_open,
        )

        self.saveAct = QtGui.QAction(
            "&Save",
            self,
            shortcut=QtGui.QKeySequence.Save,
            statusTip="Save the document to file",
            triggered=self.action_save,
        )

        self.saveAsAct = QtGui.QAction(
            "Save &As",
            self,
            shortcut=QtGui.QKeySequence.SaveAs,
            statusTip="Save the document to new file",
            triggered=self.action_saveAs,
        )

        self.printAct = QtGui.QAction(
            "&Print...",
            self,
            shortcut=QtGui.QKeySequence.Print,
            statusTip="Print the document",
            triggered=self.action_print_,
        )

        self.exitAct = QtGui.QAction(
            "E&xit",
            self,
            shortcut="Ctrl+Q",
            statusTip="Exit the application",
            triggered=self.action_close,
        )

        self.runAct = QtGui.QAction(
            "R&un",
            self,
            shortcut="Ctrl+R",
            statusTip="Run the currently active Workflow",
            triggered=self.action_run,
        )

        self.configServAct = QtGui.QAction(
            "&Servers",
            self,
            statusTip="Configure Servers",
            triggered=self.action_openSettingsDialog,
        )

        self.configPathSettingsAct = QtGui.QAction(
            "&Paths",
            self,
            statusTip="Configure Paths",
            triggered=self.action_openPathSettingsDialog,
        )
