from PySide.QtCore import QAbstractItemModel
from enum import Enum
from abc import abstractmethod

class DATA_TYPE(Enum):
    FILE        = 0
    DIRECTORY   = 1
    UNKNOWN     = 2

class DataNode(object):
    def __init__(self, data, parent=None):
        self._data = data
       
        self._parent = parent
        self._children = []
       
        self.setParent(parent)
       
    def setParent(self, parent):
        if parent != None:
            self._parent = parent
            self._parent.appendChild(self)
        else:
            self._parent = None
           
    def appendChild(self, child):
        self._children.append(child)
       
    def childAtRow(self, row):
        return self._children[row]
   
    def rowOfChild(self, child):       
        for i, item in enumerate(self._children):
            if item == child:
                return i
        return -1
   
    def removeChild(self, row):
        value = self._children[row]
        self._children.remove(value)

        return True
       
    def __len__(self):
        return len(self._children)

    @abstractmethod
    def getText(self):
        # Return text to display in TreeView
        raise NotImplementedError()

    @abstractmethod
    def getIconType(self):
        # Return text to display in TreeView
        raise NotImplementedError()

    def getParent(self):
        return self._parent

       

class DataTreeModel(QAbstractItemModel):
   
    def __init__(self, parent=None):
        super(DataTreeModel, self).__init__(parent)
        self._root = DataNode('root node')
        self._columns = 1
        self._items = []


    def getNodeByIndex(self, index):
        return index.internalPointer() if index.isValid() else self._root

    def insertDataRows(self, row, data_rows, parent):
        parentNode = self.getNodeByIndex(parent)
        added = False
        if not node is None:
            self.beginInsertRows(parent, row, row + len(data_rows) - 1)
            for data_row in data_rows:
                self.addNode(data_row, parentNode)
            self.endInsertRows()
            added = True
        return added

    def removeRow(self, row, parentIndex):
        return self.removeRows(row, 1, parentIndex)

    def removeRows(self, row, count, parentIndex):
        self.beginRemoveRows(parentIndex, row, row)
        node = self.getNodeByIndex(parentIndex)
        node.removeChild(row)
        self.endRemoveRows()
        return True


    def index(self, row, column, parent):
        node = self.getNodeByIndex(parent)
        return self.createIndex(row, column, node.childAtRow(row))

    def _getDecorationIcon(self, index):
        raise NotImplementedError()

    def data(self, index, role):
        rv = None
        if index.column() == 0:
            if role == Qt.DecorationRole:
                rv = self._getDecorationIcon(index)
                print("decoration: %s" % rv)
            elif role == Qt.TextAlignmentRole:
                print("text align")
                rv = Qt.AlignTop | Qt.AlignLeft
            elif role == Qt.DisplayRole:
                print("text")
                node = self.getNodeByIndex(index)
                rv = node.getText() if node != self._root else ""
        return rv

    def columnCount(self, parent):
        return self._columns


    def rowCount(self, parent):
        node = self.getNodeByIndex(parent)
        return len(node) if not node is None else 0

    def parent(self, child):
        if not child.isValid():
            return QModelIndex()

        node = self.getNodeByIndex(child)
       
        if node is None:
            return QModelIndex()

        parent = node.getParent()
           
        if parent is None:
            return QModelIndex()
       
        grandparent = parent.getParent()
        if grandparent is None:
            return QModelIndex()
        row = grandparent.rowOfChild(parent)
       
        assert row != - 1
        return self.createIndex(row, 0, parent)



    @abstractmethod
    def createNode(self, data, parent=None):
        #return DataNode(name, self._root if parent is None else parent)
        raise NotImplementedError()

    def addNode(self, data, parent=None):
        return self.createNode(data, self._root if parent is None else parent)


class WFEFileSystemEntry(DataNode):
    def __init__(self, data, parent=None):
        super(WFEFileSystemEntry, self).__init__(data, parent)

    def getAbsolutePath(self):
        return self._data['abspath']

    def getText(self):
        return self._data['path']

    def getIconType(self):
        rv = self._data['data_type'] 
        if rv is None:
            rv = DATA_TYPE.DIRECTORY if len(self) > 0 else DATA_TYPE.FILE
        return rv

    @staticmethod
    def createData(path, abspath, data_type=None):
        return {
                'abspath'   : abspath,
                'path'      : path,
                'data_type' : data_type
            }

class WFEFileSystemModel(DataTreeModel):
    def __init__(self, parent=None):
        super(WFEFileSystemModel, self).__init__(parent)

    def _getDecorationIcon(self, index):
        node = self.getNodeByIndex(index)
        icon_type = node.getIconType()
        icon = None
        if icon_type == DATA_TYPE.FILE:
            icon = QFileIconProvider().icon(QFileIconProvider.File)
        elif icon_type == DATA_TYPE.DIRECTORY:
            icon = QFileIconProvider().icon(QFileIconProvider.Folder)
        return icon

    def createNode(self, data, parent=None):
        return WFEFileSystemEntry(data, parent)
