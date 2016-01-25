from PySide.QtGui import QWidget, QTreeView, QVBoxLayout, QLabel, QPushButton
from PySide.QtCore import Signal, QModelIndex
from ..lib.FileSystemTree import FileSystemModel, FileSystemElement
from enum import Enum


#TODO Delete after testing:
import os
#########################



class RemoteFileSystemElement(FileSystemElement):
    class NODE_TYPES(Enum):
        NT_ROOT     = 0
        NT_FILE     = 1
        NT_DIR      = 2
        NT_LOADING  = 3
    
    def __init__(self, path, abspath, nodeType = NODE_TYPES.NT_ROOT):
        super(RemoteFileSystemElement, self).__init__(path, abspath)
        self._node_type = nodeType

    def _getChildren(self):
        print("getting children")
        return self._subelements

    def dir_query(self):
        if os.path.isdir(self.abspath):
            self._subelements = [FileSystemElement(mypath,os.path.join(self.abspath,mypath)) for mypath in os.listdir(self.abspath)]
        else:
            #print self.abspath,"is not a path"
            self._subelements = []

    def get_node_type(self):
        return self._node_type

    def update_subelements(self, subelements):
        print("update_subelements: %s, %d" % (self.name, len(self._subelements)))
        if len(self._subelements) == 1 \
                and self._subelements[0].get_node_type() == self.NODE_TYPES.NT_LOADING \
        :
            print("clearing loading note...")
            self._subelements.clear()

            for s in subelements:
                self._subelements.append(RemoteFileSystemElement(s, s, self.NODE_TYPES.NT_FILE))
            print("new lenght: %d" % len(self._subelements))


    # --- Properties
    @property
    def subelements(self):
        print("subelements called on %s(len: %d)" % (self.name, len(self._subelements)))
        if self.path_is_file:
            return []

        if len(self._subelements) == 0 and self.get_node_type() != self.NODE_TYPES.NT_LOADING:
            self._subelements = [RemoteFileSystemElement("Loading...", "", self.NODE_TYPES.NT_LOADING)]
            print("added loading")
        #elif len(self._subelements) == 1 \
        #        and self._subelements[0].get_node_type() == self.NODE_TYPES.NT_LOADING \
        #:
        #    print("WIP... (%s)" % self.name)
        #    print("sub: %s" % self._subelements[0].name)
        #else:
        return self._subelements

    def remove_subelements(self):
        print("\nremoving: %s" % self._subelements)
        self._subelements.clear()
        print("\nremoving: %s" % self._subelements)

class RemoteFileSystemModel(FileSystemModel):
    def __init__(self, rootElement):
        super(RemoteFileSystemModel, self).__init__(rootElement)

    def removeRows(self, row, rows=1, index=QModelIndex()):
        print("RemoteFileSystemModel.removeRows")
        node = index.internalPointer()
        self.beginRemoveRows(QModelIndex(), row, row + rows - 1)
        #self.items = self.items[:row] + self.items[row + rows:]
        print("\tnode %s has %d children (%s)" % \
            ((node.ref.name, len(node.ref._subelements), str(node._getChildren())) \
            if not getattr(node, 'ref', None) is None else (node,0,[])))
        children = node._getChildren()
        for child in children:
            if child in self._subnodes:
                self._subnodes.pop(child)
        if node in self._ref2node:
            self._ref2node.pop(node)
        self.endRemoveRows()
        return True

    def insertRows(self, position, rows=1, index=QModelIndex()):
        print("RemoteFileSystemModel.insertRows")
        pass

    def remove_subelements(self, index):
        node = index.internalPointer()
        if not getattr(node, 'ref', None) is None:
            node.ref.remove_subelements()
            self.removeRows(index.row(), index=index)
        
        # #TODO if non index.isValid()
        # node = index.internalPointer()
        # print("\nremove_subelements for %s," % (node))
        # if not getattr(node, 'ref', None) is None:
        #     print("\t\t%s" % (node.ref.name))
        #     print("self.beginRemoveRows(index, 0, len(index.subnodes=%d))" % (len(node.ref._subelements) - 1))
        #     self.beginRemoveRows(index, 0, (len(node.ref.subelements) - 1))
        #     #node.ref._subelements.clear()
        #     node.ref.remove_subelements()
        #     self.endRemoveRows()
        #     #self.lyoutChanged.emit()
        #     self.layoutChanged.emit()


    def set_subelements(self, index, subelements):
        #self.remove_subelements(index)
        #TODO if non index.isValid()
        node = index.internalPointer()
        if getattr(node, 'ref', None) is None:
            print("set_subelements: node.ref does not exist.")

        #self.rowsAboutToBeInserted.emit(parent, 0, len(subelements))
        self.beginInsertRows(index, 0, len(subelements) - 1)
        print("Updating %s, parent: %s" % (node.ref.name, index.parent()))
        node.ref.update_subelements(subelements)
        #self.rowsInserted.emit(parent, 0, len(subelements))
        self.endInsertRows()
        self.layoutChanged.emit()


    def data(self, index, role):
        #print("RemoteFileSystemModel: data.")
        return super().data(index, role)


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
            element = self.__current_requests[path][0]
            index   = self.__current_requests[path][1]
            print("calling: element.update(subelements)")
            #element.update_subelements(subelements)
            #self.__fs_model.set_subelements(index, subelements)
            self.__fs_model.remove_subelements(index)
            print("layoutChanged")
            # remove request
            self.__current_requests.pop(path)
            #self.__fs_model.refreshData()
            #self.__fs_model.reset()
            self.__fs_model.invalidate()
        #TODO allow arbitrary updates?

    def __get_valid_element(self, model_index):
        element = None
        index = model_index
        while element is None:
            try:
                element = self.__fs_model.get_element_by_index(index)
            except Exception as e:
                # We cant handle anything here...
                print("Exception...\n%s" % e) ##TODO remove
                break
            if element.get_node_type() == RemoteFileSystemElement.NODE_TYPES.NT_LOADING:
                print("%s is a Loading element, trying parent %s" % (model_index, model_index.parent()))
                index = model_index.parent()
                element = None
        print("found element '%s' at %s" % (element, index))
        return element

    #TODO rename
    def __got_request(self, model_index):
        element = self.__get_valid_element(model_index)
        if not element is None:
            filePath = self.__fs_model.filePath(model_index)
            self.__current_requests.update(
                    {filePath: (element, model_index)}
                )
            print("Emitting request for %s." % filePath)
            self.request_model_update.emit(filePath)
        else:
            print("element is None")
            #TODO remove

    def __reload(self):
        self.__fileTree.expandAll()
        #self.request_model_update.emit('')

    def __connect_signals(self):
        self.__fileTree.doubleClicked.connect(self.__got_request)
        self.__fileTree.expanded.connect(self.__got_request)
        self.__btn_reload.clicked.connect(self.__reload)
    
    def __init__(self, parent=None):
        super(WFRemoteFileSystem, self).__init__(parent)
        self.__fs_model = RemoteFileSystemModel(
                rootElement=RemoteFileSystemElement("foo", "bar")
            )
        self.__fileTree     = QTreeView(self)
        self.__btn_reload   = QPushButton()
        self.__init_ui()
        self.__connect_signals()
        self.__current_requests = {}
