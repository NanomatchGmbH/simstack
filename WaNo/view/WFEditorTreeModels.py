from PySide.QtCore import QAbstractItemModel, QModelIndex
from enum import Enum
from abc import abstractmethod


# imports for tests only.
# TODO remove when done.
from PySide.QtCore import QAbstractItemModel, QModelIndex, QFileInfo, Qt, QSize
from PySide.QtGui import QFileIconProvider, QTreeView
from PySide.QtGui import *
import PySide.QtCore
import abc
import os, sys, time
from enum import Enum

from pyura.pyura.Constants import JobStatus

########################

class DATA_TYPE(Enum):
    FILE        = 0
    DIRECTORY   = 1
    UNKNOWN     = 2
    LOADING     = 3
    SEPARATOR1  = 4
    SEPARATOR2  = 5
    SEPARATOR3  = 6
    SEPARATOR4  = 7
    ###These are basically exclusive to icon types
    JOB_QUEUED  = 8
    JOB_RUNNING = 9
    JOB_READY   = 10
    JOB_FAILED  = 11
    JOB_SUCCESSFUL = 12
    JOB_ABORTED    = 13
    WF_QUEUED = 14
    WF_RUNNING = 15
    WF_READY = 16
    WF_FAILED = 17
    WF_SUCCESSFUL = 18
    WF_ABORTED = 19

JOB_STATUS_TO_DATA_TYPE = {
    JobStatus.READY : DATA_TYPE.JOB_READY,
    JobStatus.FAILED : DATA_TYPE.JOB_FAILED,
    JobStatus.ABORTED: DATA_TYPE.JOB_ABORTED,
    JobStatus.SUCCESSFUL: DATA_TYPE.JOB_SUCCESSFUL,
    JobStatus.QUEUED: DATA_TYPE.JOB_QUEUED, 
    JobStatus.RUNNING : DATA_TYPE.JOB_RUNNING
}

WF_STATUS_TO_DATA_TYPE = {
    JobStatus.READY : DATA_TYPE.WF_READY,
    JobStatus.FAILED : DATA_TYPE.WF_FAILED,
    JobStatus.ABORTED: DATA_TYPE.WF_ABORTED,
    JobStatus.SUCCESSFUL: DATA_TYPE.WF_SUCCESSFUL,
    JobStatus.QUEUED: DATA_TYPE.WF_QUEUED, 
    JobStatus.RUNNING : DATA_TYPE.WF_RUNNING
}


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
        return self._children[row] if row >= 0 and row < len(self._children) \
                else None
   
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
        if not parentNode is None:
            self.beginInsertRows(parent, row, row + len(data_rows))
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

            if child is None:
                continue

            childLength = len(child)
            if len(child) > 0:
                childIndex = self.index(row, count, parentIndex)
                print("removing %d subchildren of %s" % (childLength, child._data))
                self.beginRemoveRows(parentIndex, 0, childLength)
                self._removeRows(0, childLength, childIndex, emitSignals)
                self.endRemoveRows()
            print("\tremoving: %s with %d children\n" % (child._data, childLength))
            parentNode.removeChild(i)
        return True

    def removeRows(self, row, count, parentIndex):
        self.beginRemoveRows(parentIndex, row, row + count - 1)
        result = self._removeRows(row, count, parentIndex, emitSignals=True)
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

        if row < len(node) and row >= 0:
            child = node.childAtRow(row)
            if not child is None:
                childAtPosition = self.createIndex(row, column, child)
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
                #print("decoration: %s" % rv)
            elif role == Qt.TextAlignmentRole:
                #print("text align")
                rv = Qt.AlignTop | Qt.AlignLeft
            elif role == Qt.DisplayRole:
                #print("text")
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

    def getPath(self):
        return self._data['path']

    def getText(self):
        return self.getPath()

    def getDataType(self):
        rv = self._data['data_type'] 
        if rv is None:
            rv = DATA_TYPE.DIRECTORY if len(self) > 0 else DATA_TYPE.FILE
            self._data['data_type'] = rv
        return rv

    def getIconType(self):
        return self.getDataType()

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
        self.rowsInserted.connect(self.print_rowsInserted)

    def print_rowsInserted(self, index, fromIndex, toIndex):
        print("\n\nInsertedSignal for child %s of %s, %d, %d" % \
                ("(invalid)" if not index.isValid() \
                        else index.internalPointer().getText(),
                    index.parent(),
                    fromIndex,
                    toIndex
                )
            )

    def _getDecorationIcon(self, index):
        node = self.getNodeByIndex(index)
        icon_type = node.getIconType()
        icon = None
        if icon_type == DATA_TYPE.FILE:
            icon = QFileIconProvider().icon(QFileIconProvider.File)
        elif icon_type == DATA_TYPE.DIRECTORY:
            icon = QFileIconProvider().icon(QFileIconProvider.Folder)
        elif icon_type == DATA_TYPE.LOADING:
            icon = QFileIconProvider().icon(QFileIconProvider.File)
        return icon

    def createNode(self, data, parent=None):
        return WFEFileSystemEntry(data, parent)

    def filePath(self, index):
        path = None
        if index.isValid():
            node = self.getNodeByIndex(index)
            path = node.getPath()
        return path

    def loading(self, index, text="Loading"):
        self.removeSubRows(index)
        #new = [WFEFileSystemEntry.createData(text, 'abs', DATA_TYPE.LOADING) for i in range(1, 5)]
        new = [WFEFileSystemEntry.createData(text, 'abs', DATA_TYPE.LOADING)]
        rv = self.insertDataRows(
                0,
                new,
                index
            )

        print("insertDataRows: %s" % rv)

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

class WFEUnicoreFileSystemEntry(WFEFileSystemEntry):
    def __init__(self, data, parent=None):
        super(WFEUnicoreFileSystemEntry, self).__init__(data, parent)

    def getName(self):
        return self._data['name'] if self._data['name'] != "" \
                else self._data['id']

    def getID(self):
        return self._data['id']

    def getStatus(self):
        return self._data['status']

    def getIconType(self):
        if self._data['data_type'] == WFEUnicoreRemoteFileSystemModel.DATA_TYPE_JOB:
            if self._data['status'] != None:
                return JOB_STATUS_TO_DATA_TYPE[self._data["status"]]

        if self._data['data_type'] == WFEUnicoreRemoteFileSystemModel.DATA_TYPE_WORKFLOW:
            if self._data['status'] != None:
                return WF_STATUS_TO_DATA_TYPE[self._data["status"]]

        return super(WFEUnicoreFileSystemEntry,self).getIconType()

    @staticmethod
    def createData(id, name, path, abspath, data_type=None, status = None):
        return {
                'id'        : id,
                'name'      : name,
                'abspath'   : abspath,
                'path'      : path,
                'data_type' : data_type,
                'status'    : status
            }


class WFEUnicoreRemoteFileSystemModel(WFEFileSystemModel):
    DATA_TYPE_FILE          = DATA_TYPE.FILE
    DATA_TYPE_DIRECTORY     = DATA_TYPE.DIRECTORY
    DATA_TYPE_UNKNOWN       = DATA_TYPE.UNKNOWN
    DATA_TYPE_LOADING       = DATA_TYPE.LOADING
    DATA_TYPE_JOB           = DATA_TYPE.SEPARATOR1
    DATA_TYPE_WORKFLOW      = DATA_TYPE.SEPARATOR2
    HEADER_TYPE_JOB         = DATA_TYPE.SEPARATOR3
    HEADER_TYPE_WORKFLOW    = DATA_TYPE.SEPARATOR4

    def colorize_icon(self,icon,color):
        if isinstance(icon,QIcon):
            pixmap = icon.pixmap(QSize(16,16))
            #color = QColor.QC
            painter = QPainter()
            painter.begin(pixmap)
            painter.setCompositionMode(painter.RasterOp_SourceAndDestination)
            painter.fillRect(pixmap.rect(),color)
            painter.end()
            return QIcon(pixmap)

    def icons(self,itype):
        if itype in self._icons.keys():
            return self._icons[itype]
        else:
            print("--!!!!--")
            print(itype,self._icons)
            print("--!!!!--")
            icon = QFileIconProvider().icon(QFileIconProvider.Computer)
            return icon

    def __init__(self, parent=None):
        
        self._icons = {
            DATA_TYPE.SEPARATOR1: QFileIconProvider().icon(QFileIconProvider.Computer),
            DATA_TYPE.SEPARATOR2: QFileIconProvider().icon(QFileIconProvider.Desktop),
            DATA_TYPE.SEPARATOR3: QFileIconProvider().icon(QFileIconProvider.Trashcan),
            DATA_TYPE.SEPARATOR4: QFileIconProvider().icon(QFileIconProvider.Drive),
            DATA_TYPE.JOB_QUEUED: QFileIconProvider().icon(QFileIconProvider.Computer),
            #DATA_TYPE.JOB_QUEUED: self.colorize_icon(QFileIconProvider().icon(QFileIconProvider.Computer),Qt.darkYellow),
            DATA_TYPE.JOB_RUNNING: self.colorize_icon(QFileIconProvider().icon(QFileIconProvider.Computer),Qt.yellow),
            DATA_TYPE.JOB_READY: QFileIconProvider().icon(QFileIconProvider.Computer),
            DATA_TYPE.JOB_FAILED: self.colorize_icon(QFileIconProvider().icon(QFileIconProvider.Computer), Qt.red),
            DATA_TYPE.JOB_SUCCESSFUL: self.colorize_icon(QFileIconProvider().icon(QFileIconProvider.Computer),Qt.green),
            DATA_TYPE.JOB_ABORTED: self.colorize_icon(QFileIconProvider().icon(QFileIconProvider.Computer), Qt.red),
            
            #DATA_TYPE.WF_QUEUED: self.colorize_icon(QFileIconProvider().icon(QFileIconProvider.Desktop),Qt.darkYellow),
            DATA_TYPE.WF_QUEUED: QFileIconProvider().icon(QFileIconProvider.Desktop),
            DATA_TYPE.WF_RUNNING: self.colorize_icon(QFileIconProvider().icon(QFileIconProvider.Desktop), Qt.yellow),
            DATA_TYPE.WF_READY: QFileIconProvider().icon(QFileIconProvider.Desktop),
            DATA_TYPE.WF_FAILED: self.colorize_icon(QFileIconProvider().icon(QFileIconProvider.Desktop), Qt.red),
            DATA_TYPE.WF_SUCCESSFUL: self.colorize_icon(QFileIconProvider().icon(QFileIconProvider.Desktop),
                                                         Qt.green),
            DATA_TYPE.WF_ABORTED: self.colorize_icon(QFileIconProvider().icon(QFileIconProvider.Desktop), Qt.red),
        }

        super(WFEUnicoreRemoteFileSystemModel, self).__init__(parent)
        print("WFEUnicoreRemoteFileSystemModel")
        self._add_headers()

    def createNode(self, data, parent=None):
        return WFEUnicoreFileSystemEntry(data, parent)


    def _getDecorationIcon(self, index):
        icon = super(WFEUnicoreRemoteFileSystemModel, self)._getDecorationIcon(index)
        if icon is None:
            node = self.getNodeByIndex(index)
            icon_type = node.getIconType()
            icon = self.icons(icon_type)
        return icon

    def _recursive_find_parent(self, index, parent_types):
        rv      = None
        has_parent_type = False
        if not index is None and index.isValid():
            parent  = index.parent()
            node    = self.getNodeByIndex(index)

            for t in parent_types:
                if t == node.getDataType():
                    has_parent_type = True
                    break

            if has_parent_type:
                rv = parent
            else:
                rv = self._recursive_find_parent(parent, parent_type)

        return rv

    def get_id(self, index):
        node = self.getNodeByIndex(index)
        t = None
        if not node is None:
            t = node.getID()
        return t

    def get_type(self, index):
        node = self.getNodeByIndex(index)
        t = None
        if not node is None:
            t = node.getDataType()
        return t

    def get_abspath(self, index):
        node = self.getNodeByIndex(index)
        abspath = None
        if not node is None:
            abspath = node.getAbsolutePath()
        return abspath


    def get_headers(self, index):
        return self._recursive_find_parent(
                index, [self.HEADER_TYPE_WORKFLOW, self.HEADER_TYPE_JOB])

    def get_category_parent(self, index):
        return self._recursive_find_parent(
                index, [self.DATA_TYPE_WORKFLOW, self.DATA_TYPE_JOB])

    def get_parent_job(self, index):
        return self._recursive_find_parent(index, [self.DATA_TYPE_JOB])

    def get_parent_workflow(self, index):
        return self._recursive_find_parent(index, [self.DATA_TYPE_WORKFLOW])

    def _add_headers(self):
        new = [
                WFEFileSystemEntry.createData(
                        "Workflows",
                        'abs',
                        self.HEADER_TYPE_WORKFLOW),
                WFEFileSystemEntry.createData(
                        "Jobs",
                        'abs',
                        self.HEADER_TYPE_JOB)
            ]
        rv = self.insertDataRows(
                0,
                new,
                QModelIndex()       # insert at highest level
            )

    def clear(self):
        super(WFEUnicoreRemoteFileSystemModel, self).clear()
        self._add_headers()

    def get_separator_indices(self):
        indices = []
        for i in range(0, len(self._root)):
            indices.append(self.index(i, 0))
        return indices

    def loading(self, index, text="Loading"):
        if not index.isValid():
            print("not index.isValid()")
            self.clear()
            for i in range(0, len(self._root)):

                child = self.index(i, 0)
                child_node = self.getNodeByIndex(child)
                super(WFEUnicoreRemoteFileSystemModel, self).loading(
                        child, text="Loading")
        else:
            self.removeSubRows(index)
        



#app = QApplication(sys.argv)
#model = WFEFileSystemModel()
#node = model.addNode(WFEFileSystemEntry.createData("test", "full/test", DATA_TYPE.DIRECTORY))
#node = model.addNode(WFEFileSystemEntry.createData("file", "full/test/file", DATA_TYPE.FILE), node)
#view = QTreeView()
#
#def delete():
#    index = model.findIndex([2])
#    node = index.internalPointer()
#    print("before delete: %s\n\n\n" % model.subelementsToText())
#    print("fond index %s" % node)
#    model.removeRow(index.row(), index.parent())
#    print("after delete: %s\n\n\n" % model.subelementsToText())
#
#def test():
#    delete()
#
#def on_expand(index):
#    print("Expanded: \n\tindex: %s\n\tnode: %s" % (index, index.internalPointer().getText()))
#
#def on_item_delete(indexes):
#    for index in indexes:
#        node = index.internalPointer()
#        print("deleting node %s" % node.getText())
#        model.removeRows([index.row()], 1, index.parent())
#
#def on_add_sibling(indexes):
#    for index in indexes:
#        node = index.internalPointer()
#        print("adding sibling to node %s" % node.getText())
#    #    model.insertRows(index.row(), ["blubb_%s" % (len(index.parent().internalPointer()._getChildren()) + 1)], index.parent())
#        model.insertDataRows(len(node),
#                [WFEFileSystemEntry.createData("sibling_%s" % len(node), "")],
#                index.parent())
#        
#
#def on_add_subnode(indexes):
#    for index in indexes:
#        node = index.internalPointer()
#        print("adding subnode to node %s" % node.getText())
#        #model.insertRows(0, ["subnode_%s" % (len(index.internalPointer()._getChildren()) + 1)], index)
#        model.insertDataRows(len(node),
#                [WFEFileSystemEntry.createData("test_%s" % len(node), "")],
#                index)
#        #newnode = model.addNode("test_%s" % len(node), node)
#        #model.insertRows(len(node), 0, index)
#        #newindex = model.index(len(node), 0, index)
#        #model.setData(newindex, newnode)
#
#def delete_item():
#    #TODO signal
#    on_item_delete(view.selectedIndexes())
#
#def add_subnode():
#    on_add_subnode(view.selectedIndexes())
#
#def add_sibling():
#    on_add_sibling(view.selectedIndexes())
#
#def print_rowsRemoved(index, fromIndex, toIndex):
#    print("\n\nRemovedSignal for child %s of %s, %d, %d" % \
#            ("(invalid)" if not index.isValid() else "", index.parent(), fromIndex, toIndex))
#
#def print_modelReset():
#    print("\n\nModel Reset")
#
#def print_rowsInserted(index, fromIndex, toIndex):
#    print("\n\nInsertedSignal for child %s of %s, %d, %d" % \
#            ("(invalid)" if not index.isValid() else index.internalPointer().getText(), index.parent(), fromIndex, toIndex))
#
#def print_layoutChanged():
#    print("\n\nLayoutChanged.\n\n")
#
#def print_subnodes(nodes, prefix):
#    if len(nodes) > 0:
#        for s in nodes:
#            print("%s%s" % (prefix, s._data))
#            print_subnodes(s.children, "\t%s" % prefix)
#    else:
#        print("%s[]" % prefix)
#
#def print_tree_subnodes():
#    print("_subnodes")
#    print_subnodes(model._nodes, "\t")
#
#def print_ref2node(node, prefix):
#    if len(node._ref2node) > 0:
#        for s in node._ref2node:
#            print("%s%s" % (prefix, node._ref2node[s].getText()))
#            print_ref2node(node._ref2node[s], "\t%s" % prefix)
#    else:
#        print("%s[]" % prefix)
#
#def print_tree_ref2node():
#    print("_ref2node")
#    print_ref2node(model, "\t")
#
#
#def contextMenu(point):
## Infos about the node selected.
#     index = view.indexAt(point)
#
#     if not index.isValid():
#        return
#
#     item = index.internalPointer()
#     name = item.getText()  # The text of the node.
#
## We build the menu.
#     menu=QMenu()
#     action=menu.addAction("Menu")
#     action=menu.addAction(name)
#     menu.addSeparator()
#     action_1=menu.addAction("remove")
#     action_1.triggered.connect(delete_item)
#     action_2=menu.addAction("add sibling")
#     action_2.triggered.connect(add_sibling)
#     action_3=menu.addAction("add subnode")
#     action_3.triggered.connect(add_subnode)
#
#     print(QCursor.pos())
#     menu.exec_(QCursor.pos())
#
#def refreshData():
#    modelreshData(model)
#
#def clear_all():
#    print("before clear: %s\n\n\n" % model.subelementsToText())
#    model.clear()
#    print("after clear: %s\n\n\n" % model.subelementsToText())
#
#
#if __name__ == '__main__':
#    import sys, os, pprint, time
#    from PySide.QtCore import *
#    from PySide.QtGui import *
#    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#    # init widgets
#    view.setSelectionBehavior(QAbstractItemView.SelectRows)
#    view.setContextMenuPolicy(Qt.CustomContextMenu)
#
#
#    view.customContextMenuRequested.connect(contextMenu)
#
#    #model.setHorizontalHeaderLabels(['col1', 'col2', 'col3'])
#    view.setModel(model)
#    view.setUniformRowHeights(True)
#
#    #view.show()
#
#    view.doubleClicked.connect(on_expand)
#    model.rowsRemoved.connect(print_rowsRemoved)
#    model.rowsInserted.connect(print_rowsInserted)
#    model.modelReset.connect(print_modelReset)
#    model.layoutChanged.connect(print_layoutChanged)
#    view.expanded.connect(on_expand)
#
#    widget = QWidget()
#    layout = QVBoxLayout()
#    btn_print_subnodes = QPushButton('Print Subnodes')
#    btn_print_ref2node = QPushButton('Print ref2node')
#    btn_clear_all = QPushButton('Clear All')
#    btn_reset = QPushButton("reset")
#    btn_refresh = QPushButton("refreshData()")
#
#    layout.addWidget(view)
#    layout.addWidget(btn_print_subnodes)
#    layout.addWidget(btn_print_ref2node)
#    layout.addWidget(btn_clear_all)
#    layout.addWidget(btn_reset)
#    layout.addWidget(btn_refresh)
#
#    widget.setLayout(layout)
#    widget.resize(widget.sizeHint())
#    widget.show()
#
#    btn_print_ref2node.clicked.connect(print_tree_ref2node)
#    btn_print_subnodes.clicked.connect(print_tree_subnodes)
#    btn_clear_all.clicked.connect(clear_all)
#    btn_reset.clicked.connect(model.reset)
#    btn_refresh.clicked.connect(refreshData)
#
#    sys.exit(app.exec_())
