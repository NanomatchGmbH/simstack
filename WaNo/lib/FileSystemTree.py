#
# Adapted by: Nanomatch
# Original Code by: Virgil Dupras
# Created On: 2009-09-14
# Copyright 2014 Hardcoded Software (http://www.hardcoded.net)
# 
# This software is licensed under the "BSD" License as described in the "LICENSE" file, 
# which should be included with this package. The terms are also available at 
# http://www.hardcoded.net/licenses/bsd_license

import logging

from PySide.QtCore import QAbstractItemModel, QModelIndex, QFileInfo
from PySide.QtGui import QFileIconProvider
import PySide.QtCore
import abc
import shutil

def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)

class NodeContainer(object):
    def __init__(self):
        self._subnodes = []
        self._ref2node = {}

    # --- Protected
    @abc.abstractmethod
    def _createNode(self, ref, row):
        # This returns a TreeNode instance from ref
        raise NotImplementedError()

    @abc.abstractmethod
    def _getChildren(self):
        # This returns a list of ref instances, not TreeNode instances
        raise NotImplementedError()

    # --- Public
    def invalidate(self):
        # Invalidates cached data and list of subnodes without resetting ref2node.
        self._subnodes = []


    # --- Properties
    @property
    def subnodes(self):
        if len(self._subnodes) == 0:
            print("self._subnodes: self: %s" % self)
			#TODO remove
            if isinstance(self, DummyNode):
                return []
            children = self._getChildren()
            for index, child in enumerate(children):
                if child in self._ref2node:
                    node = self._ref2node[child]
                    node.row = index
                else:
                    node = self._createNode(child, index)
                    self._ref2node[child] = node
                self._subnodes.append(node)
        return self._subnodes


class TreeNode(NodeContainer):
    def __init__(self, model, parent, row):
        super(TreeNode,self).__init__()
        self.model = model
        self.parent = parent
        self.row = row

    @property
    def index(self):
        return self.model.createIndex(self.row, 0, self)


# We use a specific TreeNode subclass to easily spot dummy nodes, especially in exception tracebacks.
class DummyNode(TreeNode):
    pass


class TreeModel(QAbstractItemModel,NodeContainer):
    def __init__(self, **kwargs):
        #super(TreeModel,self).__init__(**kwargs)
        QAbstractItemModel.__init__(self,**kwargs)
        self._dummyNodes = set()  # dummy nodes' reference have to be kept to avoid segfault
        NodeContainer.__init__(self)

    # --- Private
    def _createDummyNode(self, parent, row):
        # In some cases (drag & drop row removal, to be precise), there's a temporary discrepancy
        # between a node's subnodes and what the model think it has. This leads to invalid indexes
        # being queried. Rather than going through complicated row removal crap, it's simpler to
        # just have rows with empty data replacing removed rows for the millisecond that the drag &
        # drop lasts. Override this to return a node of the correct type.
        return DummyNode(self, parent, row)

    @abc.abstractmethod
    def _getRootNodes(self):
        raise NotImplementedError()

    def _lastIndex(self):
        """Index of the very last item in the tree.
        """
        currentIndex = QModelIndex()
        rowCount = self.rowCount(currentIndex)
        while rowCount > 0:
            currentIndex = self.index(rowCount - 1, 0, currentIndex)
            rowCount = self.rowCount(currentIndex)
        return currentIndex

    # --- Overrides
    def index(self, row, column, parent):
        if not self.subnodes:
            return QModelIndex()
        node = self #parent.internalPointer() if parent.isValid() else self
        try:
            return self.createIndex(row, column, node.subnodes[row])
        except IndexError:
            logging.debug("Wrong tree index called (%r, %r, %r). Returning DummyNode",
                          row, column, node)
            parentNode = parent.internalPointer() if parent.isValid() else None
            dummy = self._createDummyNode(parentNode, row)
            self._dummyNodes.add(dummy)
            return self.createIndex(row, column, dummy)

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        node = index.internalPointer()
        if node.parent is None:
            return QModelIndex()
        else:
            return self.createIndex(node.parent.row, 0, node.parent)

    def reset(self):
        print("Reset")
        super().beginResetModel()
        self.invalidate()
        self._ref2node = {}
        print("setting dummyNode")
        self._dummyNodes = set()
        print("endResetModel")
        super().endResetModel()

    def rowCount(self, parent=QModelIndex()):
        node = parent.internalPointer() if parent.isValid() else self
        return len(node.subnodes)

    # --- Public
    def findIndex(self, rowPath):
        """Returns the QModelIndex at `rowPath`
        
        `rowPath` is a sequence of node rows. For example, [1, 2, 1] is the 2nd child of the
        3rd child of the 2nd child of the root.
        """
        result = QModelIndex()
        for row in rowPath:
            result = self.index(row, 0, result)
        return result

    @staticmethod
    def pathForIndex(index):
        reversedPath = []
        while index.isValid():
            reversedPath.append(index.row())
            index = index.parent()
        return list(reversed(reversedPath))

    def refreshData(self):
        """Updates the data on all nodes, but without having to perform a full reset.
        
        A full reset on a tree makes us lose selection and expansion states. When all we want to do
        is to refresh the data on the nodes without adding or removing a node, a call on
        dataChanged() is better. But of course, Qt makes our life complicated by asking us topLeft
        and bottomRight indexes. This is a convenience method refreshing the whole tree.
        """
        columnCount = self.columnCount()
        topLeft = self.index(0, 0, QModelIndex())
        bottomLeft = self._lastIndex()
        bottomRight = self.sibling(bottomLeft.row(), columnCount - 1, bottomLeft)
        self.dataChanged.emit(topLeft, bottomRight)

import glob,os

class FileSystemElement(object):
    def __init__(self,path,abspath):
        self.name = path
        self.abspath = abspath
        self.path_is_file = os.path.isfile(self.abspath)
        self._subelements = []

    def dir_query(self):
        if os.path.isdir(self.abspath):
            self._subelements = [FileSystemElement(mypath,os.path.join(self.abspath,mypath)) for mypath in os.listdir(self.abspath)]
        else:
            #print self.abspath,"is not a path"
            self._subelements = []

    def get_name(self):
        return self.name

    def get_abspath(self):
        return self.abspath


    # --- Properties
    @property
    def subelements(self):
        if self.path_is_file:
            return []
        if len(self._subelements) == 0:
            print("Querying",self.abspath)
            self.dir_query()
        return self._subelements


class FileSystemModel(TreeModel):
    def __init__(self, rootElement):
        self.rootElement = rootElement
        self.rootNode = NamedNode(self,None,self.rootElement,0)
        super(FileSystemModel,self).__init__()

    def _getRootNodes(self):
        return [self.rootNode]


    def columnCount(self, parent=None):
        return 1

    def _createNode(self, ref, row):
        return NamedNode(self, self.rootNode, ref,row)

    def get_element_by_index(self, index):
        if index.model() != self:
            raise ValueError("Luke, I am _NOT_ your father!")
        path = self.pathForIndex(index)
        path.reverse()
        filename = None

        # This is the first element, we only have one root, so pop it.
        path.pop()
        sub = None
        element = self.rootElement

        while len(path) > 0:
            sub = element.subelements
            row = path.pop()
            if len(sub) > row:
                element = sub[row]
            else:
                # this can only happen, if an old QModelIndex was used...
                raise RuntimeError("Invalid model index.")
        return element

    def fileName(self, index):
        element = self.get_element_by_index(index)
        return element.get_name()

    def filePath(self, index):
        element = self.get_element_by_index(index)
        return element.get_abspath()

    def _getChildren(self):
        return self.rootElement.subelements

    def data(self, index, role):

        if not index.isValid():
            return None
        node = index.internalPointer()
        if getattr(node, 'ref', None) is None:
            print("node.ref does not exist.")
            return None
        if role == PySide.QtCore.Qt.DisplayRole and index.column() == 0:
            return node.ref.name

        if role == PySide.QtCore.Qt.DecorationRole and index.column() == 0:
            #qfi = QFileInfo(node.ref.abspath)
            #return QFileIconProvider().icon(qfi)
            if node.ref.path_is_file:
                return QFileIconProvider().icon(QFileIconProvider.File)
            else:
                return QFileIconProvider().icon(QFileIconProvider.Folder)
        return None

    def headerData(self, section, orientation, role):
        if orientation == PySide.QtCore.Qt.Horizontal and role == PySide.QtCore.Qt.DisplayRole and section == 0:
            return 'Name'
        return None

class NamedNode(TreeNode):
    def __init__(self, model, parent, ref, row):
        self.ref = ref
        #super(NamedNode,self).__init__(self, model, parent, row)
        super(NamedNode,self).__init__(model, parent, row)

    def _getChildren(self):
        return self.ref.subelements

    def _createNode(self, ref, row):
        return NamedNode(self.model,self,ref,row)

if __name__ == '__main__':
    import sys, os, pprint, time
    from PySide.QtCore import *
    from PySide.QtGui import *
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    app = QApplication(sys.argv)
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # init widgets
    view = QTreeView()
    view.setSelectionBehavior(QAbstractItemView.SelectRows)


    model = FileSystemModel(rootElement=FileSystemElement("/home/strunk/Downloads","/home/strunk/Downloads"))

    #model.setHorizontalHeaderLabels(['col1', 'col2', 'col3'])
    view.setModel(model)
    view.setUniformRowHeights(True)

    view.show()
    sys.exit(app.exec_())
