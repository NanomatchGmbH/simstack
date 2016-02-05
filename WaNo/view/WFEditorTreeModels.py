from PySide.QtCore import QAbstractItemModel, QModelIndex
from enum import Enum
from abc import abstractmethod


# imports for tests only.
# TODO remove when done.
from PySide.QtCore import QAbstractItemModel, QModelIndex, QFileInfo, Qt
from PySide.QtGui import QFileIconProvider, QTreeView
from PySide.QtGui import *
import PySide.QtCore
import abc
import os, sys, time
from enum import Enum

########################

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
        return self.removeRows([row], 1, parentIndex)

    def _removeRows(self, row, count, parentIndex, emitSignals=False):
        parentNode = self.getNodeByIndex(parentIndex)
        for i in range(row + count - 1, row - 1, -1):
            child = parentNode.childAtRow(i)
            childLength = len(child)
            if len(child) > 0:
                childIndex = self.index(row, count, parentIndex)
                print("removing %d subchildren of %s" % (childLength, child._data))
                self._removeRows(0, childLength, childIndex, emitSignals)
                if emitSignals:
                    self.beginRemoveRows(parentIndex, 0, childLength)
                    self.endRemoveRows()
            print("\tremoving: %s with %d children\n" % (child._data, childLength))
            parentNode.removeChild(i)
        return True

    def removeRows(self, row, count, parentIndex):
        result = self._removeRows(row, count, parentIndex, emitSignals=True)
        if result:
            self.beginRemoveRows(parentIndex, row, row + count - 1)
            self.endRemoveRows()
        return result

    def removeSubRows(self, index):
        result = False
        if index.isValid:
            node = self.getNodeByIndex(index)
            result = self.removeRows(0, len(node), index)
        return result




    def clear(self):
        rootIndex = QModelIndex()
        
        self.beginResetModel()
        self._removeRows(0, len(self._root), rootIndex, emitSignals=False)
        self.endResetModel()



    def index(self, row, column, parent=QModelIndex()):
        childAtPosition = None

        # getNodeByIndex is robust. We don't need to check if parent is valid.
        node = self.getNodeByIndex(parent)

        if row < len(node):
            childAtPosition = self.createIndex(row, column, node.childAtRow(row))
        else:
            # return invalid index
            childAtPosition = QModelIndex()
        return childAtPosition

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


###############################################################################
###############################################################################
###############################################################################
#                           Test Code
###############################################################################
###############################################################################
###############################################################################

    def subelementsToText(self, parent=QModelIndex(), prefix=""):
        node = self.getNodeByIndex(parent)
        print("%s%s (%d)" % (prefix, node._data, len(node)))
        newPrefix = "\t%s" % prefix
        for c in [self.index(r, 0, parent) for r in range(0, len(node))]:
            childNode = self.getNodeByIndex(c)
            self.subelementsToText(c, newPrefix)
            
app = QApplication(sys.argv)
model = WFEFileSystemModel()
node = model.addNode(WFEFileSystemEntry.createData("test", "full/test", DATA_TYPE.DIRECTORY))
node = model.addNode(WFEFileSystemEntry.createData("file", "full/test/file", DATA_TYPE.FILE), node)
view = QTreeView()

def delete():
    index = model.findIndex([2])
    node = index.internalPointer()
    print("before delete: %s\n\n\n" % model.subelementsToText())
    print("fond index %s" % node)
    model.removeRow(index.row(), index.parent())
    print("after delete: %s\n\n\n" % model.subelementsToText())

def test():
    delete()

def on_expand(index):
    print("Expanded: \n\tindex: %s\n\tnode: %s" % (index, index.internalPointer().getText()))

def on_item_delete(indexes):
    for index in indexes:
        node = index.internalPointer()
        print("deleting node %s" % node.getText())
        model.removeRows([index.row()], 1, index.parent())

def on_add_sibling(indexes):
    for index in indexes:
        node = index.internalPointer()
        print("adding sibling to node %s" % node.getText())
    #    model.insertRows(index.row(), ["blubb_%s" % (len(index.parent().internalPointer()._getChildren()) + 1)], index.parent())
        model.insertDataRows(len(node),
                [WFEFileSystemEntry.createData("sibling_%s" % len(node), "")],
                index.parent())
        

def on_add_subnode(indexes):
    for index in indexes:
        node = index.internalPointer()
        print("adding subnode to node %s" % node.getText())
        #model.insertRows(0, ["subnode_%s" % (len(index.internalPointer()._getChildren()) + 1)], index)
        model.insertDataRows(len(node),
                [WFEFileSystemEntry.createData("test_%s" % len(node), "")],
                index)
        #newnode = model.addNode("test_%s" % len(node), node)
        #model.insertRows(len(node), 0, index)
        #newindex = model.index(len(node), 0, index)
        #model.setData(newindex, newnode)

def delete_item():
    #TODO signal
    on_item_delete(view.selectedIndexes())

def add_subnode():
    on_add_subnode(view.selectedIndexes())

def add_sibling():
    on_add_sibling(view.selectedIndexes())

def print_rowsRemoved(index, fromIndex, toIndex):
    print("\n\nRemovedSignal for child %s of %s, %d, %d" % \
            ("(invalid)" if not index.isValid() else "", index.parent(), fromIndex, toIndex))

def print_rowsInserted(index, fromIndex, toIndex):
    print("\n\nInsertedSignal for child %s of %s, %d, %d" % \
            ("(invalid)" if not index.isValid() else index.internalPointer().getText(), index.parent(), fromIndex, toIndex))

def print_layoutChanged():
    print("\n\nLayoutChanged.\n\n")

def print_subnodes(nodes, prefix):
    if len(nodes) > 0:
        for s in nodes:
            print("%s%s" % (prefix, s._data))
            print_subnodes(s.children, "\t%s" % prefix)
    else:
        print("%s[]" % prefix)

def print_tree_subnodes():
    print("_subnodes")
    print_subnodes(model._nodes, "\t")

def print_ref2node(node, prefix):
    if len(node._ref2node) > 0:
        for s in node._ref2node:
            print("%s%s" % (prefix, node._ref2node[s].getText()))
            print_ref2node(node._ref2node[s], "\t%s" % prefix)
    else:
        print("%s[]" % prefix)

def print_tree_ref2node():
    print("_ref2node")
    print_ref2node(model, "\t")


def contextMenu(point):
# Infos about the node selected.
     index = view.indexAt(point)

     if not index.isValid():
        return

     item = index.internalPointer()
     name = item.getText()  # The text of the node.

# We build the menu.
     menu=QMenu()
     action=menu.addAction("Menu")
     action=menu.addAction(name)
     menu.addSeparator()
     action_1=menu.addAction("remove")
     action_1.triggered.connect(delete_item)
     action_2=menu.addAction("add sibling")
     action_2.triggered.connect(add_sibling)
     action_3=menu.addAction("add subnode")
     action_3.triggered.connect(add_subnode)

     print(QCursor.pos())
     menu.exec_(QCursor.pos())

def refreshData():
    modelreshData(model)

def clear_all():
    print("before clear: %s\n\n\n" % model.subelementsToText())
    model.clear()
    print("after clear: %s\n\n\n" % model.subelementsToText())


if __name__ == '__main__':
    import sys, os, pprint, time
    from PySide.QtCore import *
    from PySide.QtGui import *
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # init widgets
    view.setSelectionBehavior(QAbstractItemView.SelectRows)
    view.setContextMenuPolicy(Qt.CustomContextMenu)


    view.customContextMenuRequested.connect(contextMenu)

    #model.setHorizontalHeaderLabels(['col1', 'col2', 'col3'])
    view.setModel(model)
    view.setUniformRowHeights(True)

    #view.show()

    view.doubleClicked.connect(on_expand)
    model.rowsRemoved.connect(print_rowsRemoved)
    model.rowsInserted.connect(print_rowsInserted)
    model.layoutChanged.connect(print_layoutChanged)
    view.expanded.connect(on_expand)

    widget = QWidget()
    layout = QVBoxLayout()
    btn_print_subnodes = QPushButton('Print Subnodes')
    btn_print_ref2node = QPushButton('Print ref2node')
    btn_clear_all = QPushButton('Clear All')
    btn_reset = QPushButton("reset")
    btn_refresh = QPushButton("refreshData()")

    layout.addWidget(view)
    layout.addWidget(btn_print_subnodes)
    layout.addWidget(btn_print_ref2node)
    layout.addWidget(btn_clear_all)
    layout.addWidget(btn_reset)
    layout.addWidget(btn_refresh)

    widget.setLayout(layout)
    widget.resize(widget.sizeHint())
    widget.show()

    btn_print_ref2node.clicked.connect(print_tree_ref2node)
    btn_print_subnodes.clicked.connect(print_tree_subnodes)
    btn_clear_all.clicked.connect(clear_all)
    btn_reset.clicked.connect(model.reset)
    btn_refresh.clicked.connect(refreshData)

    sys.exit(app.exec_())
