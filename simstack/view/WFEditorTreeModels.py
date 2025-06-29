from abc import abstractmethod


from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt, QSize
from PySide6.QtWidgets import QFileIconProvider
from PySide6.QtGui import QIcon, QPainter, QColor, qGray, QPixmap

from enum import Enum


########################
from SimStackServer.MessageTypes import JobStatus


class DATA_TYPE(Enum):
    FILE = 0
    DIRECTORY = 1
    UNKNOWN = 2
    LOADING = 3
    SEPARATOR1 = 4
    SEPARATOR2 = 5
    SEPARATOR3 = 6
    SEPARATOR4 = 7
    ###These are basically exclusive to icon types
    JOB_QUEUED = 8
    JOB_RUNNING = 9
    JOB_READY = 10
    JOB_FAILED = 11
    JOB_SUCCESSFUL = 12
    JOB_ABORTED = 13
    JOB_REUSED_RESULT = 14
    WF_QUEUED = 15
    WF_RUNNING = 16
    WF_READY = 17
    WF_FAILED = 18
    WF_SUCCESSFUL = 19
    WF_ABORTED = 20
    UNDELETEABLE_DIRECTORY = 21


JOB_STATUS_TO_DATA_TYPE = {
    JobStatus.READY: DATA_TYPE.JOB_READY,
    JobStatus.FAILED: DATA_TYPE.JOB_FAILED,
    JobStatus.ABORTED: DATA_TYPE.JOB_ABORTED,
    JobStatus.SUCCESSFUL: DATA_TYPE.JOB_SUCCESSFUL,
    JobStatus.QUEUED: DATA_TYPE.JOB_QUEUED,
    JobStatus.RUNNING: DATA_TYPE.JOB_RUNNING,
}

WF_STATUS_TO_DATA_TYPE = {
    JobStatus.READY: DATA_TYPE.WF_READY,
    JobStatus.FAILED: DATA_TYPE.WF_FAILED,
    JobStatus.ABORTED: DATA_TYPE.WF_ABORTED,
    JobStatus.SUCCESSFUL: DATA_TYPE.WF_SUCCESSFUL,
    JobStatus.QUEUED: DATA_TYPE.WF_QUEUED,
    JobStatus.RUNNING: DATA_TYPE.WF_RUNNING,
    JobStatus.MARKED_FOR_DELETION: DATA_TYPE.WF_FAILED,
}


class DataNode(object):
    def __init__(self, data, parent=None):
        self._data = data

        self._parent = parent
        self._children = []

        self.setParent(parent)

    def setParent(self, parent):
        if parent is not None:
            self._parent = parent
            self._parent.appendChild(self)
        else:
            self._parent = None

    def appendChild(self, child):
        self._children.append(child)

    def childAtRow(self, row):
        return self._children[row] if row >= 0 and row < len(self._children) else None

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
        super().__init__(parent)
        self._root = DataNode("root node")
        self._columns = 1
        self._items = []
        self.junk = []

    def getNodeByIndex(self, index):
        return index.internalPointer() if index.isValid() else self._root

    def insertDataRows(self, row, data_rows, parent):
        parentNode = self.getNodeByIndex(parent)
        added = False
        if parentNode is not None:
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
                # print("removing %d subchildren of %s" % (childLength, child._data))
                self.beginRemoveRows(parentIndex, 0, childLength)
                self._removeRows(0, childLength, childIndex, emitSignals)
                self.endRemoveRows()
            # print("\tremoving: %s with %d children\n" % (child._data, childLength))
            parentNode.removeChild(i)
        return True

    def removeRows(self, row, count, parentIndex):
        self.beginRemoveRows(parentIndex, row, row + count - 1)
        result = self._removeRows(row, count, parentIndex, emitSignals=True)
        self.endRemoveRows()
        return result

    def removeSubRows(self, index):
        result = False
        if index.isValid():
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
            if child is not None:
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
                # print("decoration: %s" % rv)
            elif role == Qt.TextAlignmentRole:
                # print("text align")
                rv = Qt.AlignTop | Qt.AlignLeft
            elif role == Qt.DisplayRole:
                # print("text")
                node = self.getNodeByIndex(index)
                rv = node.getText() if node != self._root else ""
        return rv

    def columnCount(self, parent):
        return self._columns

    def rowCount(self, parent):
        node = self.getNodeByIndex(parent)
        return len(node) if node is not None else 0

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
        if row < 0:
            print("Impossible condition in DataTreeModel, please debug")
            return QModelIndex()
        assert row != -1
        return self.createIndex(row, 0, parent)

    @abstractmethod
    def createNode(self, data, parent=None):
        # return DataNode(name, self._root if parent is None else parent)
        raise NotImplementedError()

    def addNode(self, data, parent=None):
        temp = self.createNode(data, self._root if parent is None else parent)
        # This is a huge memory leak. Currently it's the only way and I have to talk about it with Flo when he's back

        self.junk.append(temp)
        return temp


class WFEFileSystemEntry(DataNode):
    def __init__(self, data, parent=None):
        super().__init__(data, parent)

    def getAbsolutePath(self):
        return self._data["abspath"]

    def getPath(self):
        return self._data["path"]

    def getText(self):
        return self.getPath()

    def getDataType(self):
        rv = self._data["data_type"]
        if rv is None:
            rv = DATA_TYPE.DIRECTORY if len(self) > 0 else DATA_TYPE.FILE
            self._data["data_type"] = rv
        return rv

    def getIconType(self):
        return self.getDataType()

    @staticmethod
    def createData(path, abspath, data_type=None):
        return {"abspath": abspath, "path": path, "data_type": data_type}


class WFEFileSystemModel(DataTreeModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rowsInserted.connect(self.print_rowsInserted)

    def print_rowsInserted(self, index, fromIndex, toIndex):
        return
        print(
            "\n\nInsertedSignal for child %s of %s, %d, %d"
            % (
                "(invalid)"
                if not index.isValid()
                else index.internalPointer().getText(),
                index.parent(),
                fromIndex,
                toIndex,
            )
        )

    def _getDecorationIcon(self, index):
        node = self.getNodeByIndex(index)
        icon_type = node.getIconType()
        icon = None
        if icon_type == DATA_TYPE.FILE:
            icon = QFileIconProvider().icon(QFileIconProvider.File)
        elif (
            icon_type == DATA_TYPE.DIRECTORY
            or icon_type == DATA_TYPE.UNDELETEABLE_DIRECTORY
        ):
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
        # new = [WFEFileSystemEntry.createData(text, 'abs', DATA_TYPE.LOADING) for i in range(1, 5)]
        new = [WFEFileSystemEntry.createData(text, "abs", DATA_TYPE.LOADING)]
        rv = self.insertDataRows(0, new, index)

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
        # print("%s%s (%d)" % (prefix, node._data, len(node)))
        newPrefix = "\t%s" % prefix
        for c in [self.index(r, 0, parent) for r in range(0, len(node))]:
            self.subelementsToText(c, newPrefix)


class WFERemoteFileSystemEntry(WFEFileSystemEntry):
    def __init__(self, data, parent=None):
        super().__init__(data, parent)

    def getName(self):
        return self._data["name"] if self._data["name"] != "" else self._data["id"]

    def getID(self):
        return self._data["id"]

    def getStatus(self):
        return self._data["status"]

    def getIconType(self):
        if self._data["data_type"] == WFERemoteFileSystemModel.DATA_TYPE_JOB:
            if self._data["status"] is not None:
                if (
                    self._data["status"] == JobStatus.SUCCESSFUL
                    and self._data["original_result_directory"] is not None
                ):
                    return DATA_TYPE.JOB_REUSED_RESULT
                else:
                    return JOB_STATUS_TO_DATA_TYPE[self._data["status"]]

        if self._data["data_type"] == WFERemoteFileSystemModel.DATA_TYPE_WORKFLOW:
            if self._data["status"] is not None:
                return WF_STATUS_TO_DATA_TYPE[self._data["status"]]

        return super().getIconType()

    @staticmethod
    def createData(
        id,
        name,
        path,
        abspath,
        data_type=None,
        status=None,
        original_result_directory=None,
    ):
        return {
            "id": id,
            "name": name,
            "abspath": abspath,
            "path": path,
            "data_type": data_type,
            "status": status,
            "original_result_directory": original_result_directory,
        }


class WFERemoteFileSystemModel(WFEFileSystemModel):
    DATA_TYPE_FILE = DATA_TYPE.FILE
    DATA_TYPE_DIRECTORY = DATA_TYPE.DIRECTORY
    DATA_TYPE_UNKNOWN = DATA_TYPE.UNKNOWN
    DATA_TYPE_LOADING = DATA_TYPE.LOADING
    DATA_TYPE_JOB = DATA_TYPE.SEPARATOR1
    DATA_TYPE_WORKFLOW = DATA_TYPE.SEPARATOR2
    HEADER_TYPE_JOB = DATA_TYPE.SEPARATOR3
    HEADER_TYPE_WORKFLOW = DATA_TYPE.SEPARATOR4
    HEADER_TYPE_DIRECTORY = DATA_TYPE.UNDELETEABLE_DIRECTORY

    def pixmap_to_grayscale(self, pixmap):
        image = pixmap.toImage()
        # data = image.bits()
        # data.setsize(image.byteCount())
        for i in range(0, image.width()):
            for j in range(0, image.height()):
                pixel = image.pixel(i, j)
                gray_value = qGray(pixel)
                gray_value = 255 - gray_value
                image.setPixel(
                    i, j, QColor(gray_value, gray_value, gray_value, 255).rgba()
                )
        return QPixmap.fromImage(image)

    def colorize_icon(self, icon, color):
        if isinstance(icon, QIcon):
            pixmap = icon.pixmap(QSize(16, 16))
            pixmap = self.pixmap_to_grayscale(pixmap)
            painter = QPainter()
            painter.begin(pixmap)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Screen)
            painter.fillRect(pixmap.rect(), color)
            painter.end()
            return QIcon(pixmap)

    def icons(self, itype):
        if itype in self._icons.keys():
            return self._icons[itype]
        else:
            icon = QFileIconProvider().icon(QFileIconProvider.Computer)
            return icon

    def __init__(self, parent=None):
        self._icons = {
            DATA_TYPE.SEPARATOR1: QFileIconProvider().icon(QFileIconProvider.Computer),
            DATA_TYPE.SEPARATOR2: QFileIconProvider().icon(QFileIconProvider.Desktop),
            DATA_TYPE.SEPARATOR3: QFileIconProvider().icon(QFileIconProvider.Trashcan),
            DATA_TYPE.SEPARATOR4: QFileIconProvider().icon(QFileIconProvider.Drive),
            DATA_TYPE.JOB_QUEUED: QFileIconProvider().icon(QFileIconProvider.Computer),
            # DATA_TYPE.JOB_QUEUED: self.colorize_icon(QFileIconProvider().icon(QFileIconProvider.Computer),Qt.darkYellow),
            DATA_TYPE.JOB_RUNNING: self.colorize_icon(
                QFileIconProvider().icon(QFileIconProvider.Computer), Qt.yellow
            ),
            DATA_TYPE.JOB_READY: QFileIconProvider().icon(QFileIconProvider.Computer),
            DATA_TYPE.JOB_FAILED: self.colorize_icon(
                QFileIconProvider().icon(QFileIconProvider.Computer), Qt.red
            ),
            DATA_TYPE.JOB_SUCCESSFUL: self.colorize_icon(
                QFileIconProvider().icon(QFileIconProvider.Computer), Qt.green
            ),
            DATA_TYPE.JOB_ABORTED: self.colorize_icon(
                QFileIconProvider().icon(QFileIconProvider.Computer), Qt.red
            ),
            DATA_TYPE.JOB_REUSED_RESULT: self.colorize_icon(
                QFileIconProvider().icon(QFileIconProvider.Computer), Qt.blue
            ),
            # DATA_TYPE.WF_QUEUED: self.colorize_icon(QFileIconProvider().icon(QFileIconProvider.Desktop),Qt.darkYellow),
            DATA_TYPE.WF_QUEUED: QFileIconProvider().icon(QFileIconProvider.Desktop),
            DATA_TYPE.WF_RUNNING: self.colorize_icon(
                QFileIconProvider().icon(QFileIconProvider.Desktop), Qt.yellow
            ),
            DATA_TYPE.WF_READY: QFileIconProvider().icon(QFileIconProvider.Desktop),
            DATA_TYPE.WF_FAILED: self.colorize_icon(
                QFileIconProvider().icon(QFileIconProvider.Desktop), Qt.red
            ),
            DATA_TYPE.WF_SUCCESSFUL: self.colorize_icon(
                QFileIconProvider().icon(QFileIconProvider.Desktop), Qt.green
            ),
            DATA_TYPE.WF_ABORTED: self.colorize_icon(
                QFileIconProvider().icon(QFileIconProvider.Desktop), Qt.red
            ),
        }

        super().__init__(parent)
        self._add_headers()

    def createNode(self, data, parent=None):
        return WFERemoteFileSystemEntry(data, parent)

    def _getDecorationIcon(self, index):
        icon = super()._getDecorationIcon(index)
        if icon is None:
            node = self.getNodeByIndex(index)
            icon_type = node.getIconType()
            icon = self.icons(icon_type)
        return icon

    def _recursive_find_parent(self, index, parent_types):
        rv = None
        has_parent_type = False
        if index is not None and index.isValid():
            parent = index.parent()
            node = self.getNodeByIndex(index)

            for t in parent_types:
                if t == node.getDataType():
                    has_parent_type = True
                    break

            if has_parent_type:
                rv = parent
            else:
                rv = self._recursive_find_parent(parent, parent_types)

        return rv

    def get_id(self, index):
        node = self.getNodeByIndex(index)
        t = None
        if node is not None:
            t = node.getID()
        return t

    def get_type(self, index):
        node = self.getNodeByIndex(index)
        t = None
        if node is not None:
            t = node.getDataType()
        return t

    def get_abspath(self, index):
        node = self.getNodeByIndex(index)
        abspath = None
        if node is not None:
            abspath = node.getAbsolutePath()
        return abspath

    def get_headers(self, index):
        return self._recursive_find_parent(
            index, [self.HEADER_TYPE_WORKFLOW, self.HEADER_TYPE_JOB]
        )

    def get_category_parent(self, index):
        return self._recursive_find_parent(
            index, [self.DATA_TYPE_WORKFLOW, self.DATA_TYPE_JOB]
        )

    def get_parent_job(self, index):
        return self._recursive_find_parent(index, [self.DATA_TYPE_JOB])

    def get_parent_workflow(self, index):
        return self._recursive_find_parent(index, [self.DATA_TYPE_WORKFLOW])

    def _add_headers(self):
        new = [
            WFEFileSystemEntry.createData(
                "Workflows", "abs", self.HEADER_TYPE_WORKFLOW
            ),
            WFEFileSystemEntry.createData("Home", ".", self.HEADER_TYPE_DIRECTORY),
        ]
        self.insertDataRows(
            0,
            new,
            QModelIndex(),  # insert at highest level
        )

    def clear(self):
        super().clear()
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
                super().loading(child, text="Loading")
        else:
            self.removeSubRows(index)
