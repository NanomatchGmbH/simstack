from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import PySide.QtGui  as QtGui
from PySide.QtCore import Signal

from .WaNoSettings import WaNoUnicoreSettings

class WFEditorMainWindow(QtGui.QMainWindow):
    new_file            = Signal(name="NewFile")
    open_file           = Signal(name="OpenFile")
    save                = Signal(name="Save")
    save_as             = Signal(name="SaveAs")
    save_registries     = Signal(list, name="SaveRegistries")
    open_registry_settings = Signal(name="OpenRegistrySettings")
   
    def __init_ui(self,parent=None):
        self.setWindowIcon(QtGui.QIcon('./WaNo/Media/Logo_Nanomatch.png'))
        self.setCentralWidget(self.wfEditor)
    
        self._createActions()
        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.newAct)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.saveAct)
        self.fileMenu.addAction(self.saveAsAct)
        self.fileMenu.addAction(self.printAct)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAct)
        
        self.runMenu = self.menuBar().addMenu("&Run")

        self.settingsMenu = self.menuBar().addAction(
                QtGui.QAction(
                    "&Configuration",
                    self,
                    statusTip="Open Settings",
                    triggered=self.action_openSettingsDialog
                )
            )
        
        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.aboutAct)
        self.helpMenu.addAction(self.aboutWFEAct)
        
        message = "Welcome to the Nanomatch Workflow Editor"
        self.statusBar().showMessage(message)
        
        self.setWindowTitle("Nanomatch Workflow Editor (C) 2015")
   
    def __init__(self, editor, parent=None):
        super(WFEditorMainWindow, self).__init__(parent)
        self.wfEditor = editor
        self.__init_ui()

    def action_openSettingsDialog(self):
        self.open_registry_settings.emit()

    def open_dialog_registry_settings(self, current_registries):
        dialog = WaNoUnicoreSettings(current_registries)

        if (dialog.exec_()):
            self.save_registries.emit(dialog.get_settings())
        else:
            #print("fail")
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
        self.close()

    def action_about(self):
        self.infoLabel.setText("Invoked <b>Help|About</b>")
        QtGui.QMessageBox.about(self, "About Menu",
                "The <b>Menu</b> example shows how to create menu-bar menus "
                "and context menus.")
        
    def action_aboutWFE(self):
        self.infoLabel.setText("Invoked <b>Help|About Qt</b>")

    def _createActions(self):
        self.newAct = QtGui.QAction("&New", self,
                shortcut=QtGui.QKeySequence.New,
                statusTip="Create a new file", triggered=self.action_newFile)

        self.openAct = QtGui.QAction("&Open...", self,
                shortcut=QtGui.QKeySequence.Open,
                statusTip="Open an existing file", triggered=self.action_open)

        self.saveAct = QtGui.QAction("&Save", self,
                shortcut=QtGui.QKeySequence.Save,
                statusTip="Save the document to file", triggered=self.action_save)
        
        self.saveAsAct = QtGui.QAction("Save &As", self,
                               shortcut=QtGui.QKeySequence.SaveAs,
                statusTip="Save the document to new file", triggered=self.action_saveAs)

        self.printAct = QtGui.QAction("&Print...", self,
                shortcut=QtGui.QKeySequence.Print,
                statusTip="Print the document", triggered=self.action_print_)

        self.exitAct = QtGui.QAction("E&xit", self, shortcut="Ctrl+Q",
                statusTip="Exit the application", triggered=self.action_close)


        self.aboutAct = QtGui.QAction("&Help", self,
                statusTip="Show the application's Help box",
                triggered=self.action_about)

        self.aboutWFEAct = QtGui.QAction("About &WorkflowEditor", self,
                statusTip="About the Nanomatch Workflow Editor",
                triggered=self.action_aboutWFE)
        
        self.aboutWFEAct.triggered.connect(QtGui.qApp.aboutQt)
        
