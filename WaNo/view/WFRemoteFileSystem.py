from PySide.QtGui import QWidget, QTreeView, QVBoxLayout, QLabel, QPushButton
from PySide.QtCore import Signal, QModelIndex
#from ..lib.FileSystemTree import FileSystemModel, FileSystemElement
from enum import Enum

from .WFEditorTreeModels import WFEFileSystemModel, WFEFileSystemEntry


#TODO Delete after testing:
import os
#########################

class WFRemoteFileSystem(QWidget):
    request_model_update = Signal(str, name="requestRemoteFileSystemModelUpdate")
    def __init_ui(self):
        layout      = QVBoxLayout(self)

        label       = QLabel("File System")
        selection   = QLabel("Placeholder for Display selection.")

        self.__fileTree.setModel(self.__fs_model)
        self.__btn_reload.setText("Reload")

        layout.addWidget(label)
        layout.addWidget(selection)
        layout.addWidget(self.__fileTree)
        layout.addWidget(self.__btn_reload)

    def update_file_tree_node(self, path, subelements):
        print("new file tree nodes for path: %s:\n%s" % (path, subelements))

        if path in self.__current_requests:
            index   = self.__current_requests[path]

            self.__fs_model.removeSubRows(index)
            # remove request
            self.__current_requests.pop(path)
            print(subelements)
        else:
            print("path '%s' not in current_requests." % path)

#TODO obsolete
    #def __get_valid_element(self, model_index):
    #    element = None
    #    index = model_index
    #    while element is None:
    #        try:
    #            element = self.__fs_model.get_element_by_index(index)
    #        except Exception as e:
    #            # We cant handle anything here...
    #            print("Exception...\n%s" % e) ##TODO remove
    #            break
    #        if element.get_node_type() == RemoteFileSystemElement.NODE_TYPES.NT_LOADING:
    #            print("%s is a Loading element, trying parent %s" % (model_index, model_index.parent()))
    #            index = model_index.parent()
    #            element = None
    #    print("found element '%s' at %s" % (element, index))
    #    return element

    #TODO rename
    def __got_request(self, model_index):
        if model_index.isValid():
            filePath = self.__fs_model.filePath(model_index)
            self.__current_requests.update( {filePath: model_index} )

            print("Emitting request for %s." % filePath)
            self.request_model_update.emit(filePath)
        else:
            print("index invalid")
            #TODO remove

    def __reload(self):
        self.request_model_update.emit('')

    def __connect_signals(self):
        self.__fileTree.doubleClicked.connect(self.__got_request)
        self.__fileTree.expanded.connect(self.__got_request)
        self.__btn_reload.clicked.connect(self.__reload)
    
    def __init__(self, parent=None):
        super(WFRemoteFileSystem, self).__init__(parent)
        self.__fs_model     = WFEFileSystemModel(self)
        self.__fileTree     = QTreeView(self)
        self.__btn_reload   = QPushButton()
        self.__init_ui()
        self.__connect_signals()
        self.__current_requests = {}
