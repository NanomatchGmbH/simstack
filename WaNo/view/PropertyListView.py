#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import abc
from enum import IntEnum
from functools import partial

from Qt import QtGui, QtCore, QtWidgets

import yaml
import operator
import os

import Qt
#if Qt.__binding__ == "PyQt5":
from SimStackServer.Util.ClientResourceModelToServerResourceModel import ClientResourceModelToServerResourceModel, \
    get_default_resource_list, load_resource_list

if False:
    # The handling of intflags differs between implementations. Currently we get a warning for pyqt5, but it will be fixed in a future pyqt5 release, therefore we take it.
    def pyside_int_workaround(val):
        return int(val)
else:
    def pyside_int_workaround(val):
        return val


class ResourceTableBase(QtCore.QAbstractTableModel):
    def save(self,filename):
        with filename.open('wt') as outfile:
            outfile.write(yaml.safe_dump(self.mylist, default_flow_style=False))

    @abc.abstractmethod
    def make_default_list(self):
        raise NotImplementedError("Please implement in child class")

    def load(self,filename):
        with filename.open('rt') as infile:
            self.mylist = yaml.safe_load(infile)

    def __init__(self, parent, *args,**kwargs):
        super(ResourceTableBase, self).__init__(parent, *args)
        if "wano_parent" in kwargs:
            self.wano_parent = kwargs["wano_parent"]
        self.mylist = [[]]
        self.types = []
        self.header = []
        self.alignments = []

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.mylist)

    def columnCount(self,parent=QtCore.QModelIndex()):
        return len(self.mylist[0])

    def data(self, index, role):
        if not index.isValid():
            return None
        elif role == QtCore.Qt.TextAlignmentRole:
            return self.alignments[index.column()]
        elif role != QtCore.Qt.DisplayRole:
            return None
        return self.mylist[index.row()][index.column()]

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            row = index.row()
            col = index.column()
            #print("Settings row%d ,col%d ,val%s" %(row,col,value))
            self.mylist[row][col] = value
            return True
        return False

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.header[col]
        if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
            return "%d"%(col+1)
        return None

    def sort(self, col, order):
        """sort table by given column number col"""
        self.layoutAboutToBeChanged.emit()
        self.mylist = sorted(self.mylist,
                             key=operator.itemgetter(col))
        if order == QtCore.Qt.DescendingOrder:
            self.mylist.reverse()
        self.layoutChanged.emit()


class ExportTableModel(ResourceTableBase):
    class COLTYPE(IntEnum):
        filename = 1

    def __init__(self, parent, *args, **kwargs):
        super(ExportTableModel,self).__init__(parent, *args,**kwargs)

    def get_contents(self):
        return self.mylist

    def flags(self, index):
        defaultflags = QtCore.Qt.ItemFlags()
        return pyside_int_workaround(QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | defaultflags)

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.mylist) + 1

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 1

    def data(self, index, role):
        if not index.isValid():
            return None
        elif role == QtCore.Qt.TextAlignmentRole:
            return self.alignments[index.column()]
        elif role != QtCore.Qt.DisplayRole:
            return None
        if index.row() >= len(self.mylist):
            return " "
        return self.mylist[index.row()][index.column()]

    def delete_entry(self,row):
        if len(self.mylist) <= 0 or row >= len(self.mylist):
            return
        self.beginRemoveRows(QtCore.QModelIndex(),row,row)
        self.mylist.pop(row)
        self.endRemoveRows()

    def add_entry(self):
        self.mylist.append(["File_%d" % len(self.mylist)])

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        row = index.row()
        col = index.column()
        # print("Setting %d %d"%(col,row))
        if role == QtCore.Qt.EditRole:
            if value.strip() == "":
                return False

        if row == len(self.mylist):
            self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount())
            self.add_entry()
            returnval = super(ExportTableModel, self).setData(index, value, role)
            self.endInsertRows()
            return returnval

        returnval = super(ExportTableModel, self).setData(index, value, role)
        return returnval

    def make_default_list(self):
        self.mylist = [
        ]
        self.header = ["Filename"]
        self.alignments = [pyside_int_workaround(QtCore.Qt.AlignCenter)]


class ImportTableModel(ResourceTableBase):
    class COLTYPE(IntEnum):
        name = 1
        ImportFrom = 2
        ImportTo = 3

    def __init__(self, parent, *args,**kwargs):
        super(ImportTableModel, self).__init__(parent, *args,**kwargs)
        #self.dataChanged.connect(self.changeValuesAfterImport)
        #self.

    #def changeValuesAfterImport(self, table):
    #    print("here")
    #    print(table)

    def get_contents(self):
        return self.mylist

    def delete_entry(self,row):
        if len(self.mylist) <= 0 or row >= len(self.mylist):
            return
        self.beginRemoveRows(QtCore.QModelIndex(),row,row)
        self.mylist.pop(row)
        self.endRemoveRows()

    def flags(self, index):
        defaultflags = pyside_int_workaround(QtCore.Qt.ItemFlags() | QtCore.Qt.ItemIsSelectable)
        return pyside_int_workaround(QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | defaultflags)


    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.mylist) + 1

    def columnCount(self,parent=QtCore.QModelIndex()):
        return 3

    def data(self, index, role):
        if not index.isValid():
            return None
        elif role == QtCore.Qt.TextAlignmentRole:
            return self.alignments[index.column()]
        elif role != QtCore.Qt.DisplayRole:
            return None
        if index.row() >= len(self.mylist):
            return " "
        return self.mylist[index.row()][index.column()]

    def add_entry(self):
        self.mylist.append(["File_%d"%len(self.mylist), "",""])

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        row = index.row()
        col = index.column()
        #print("Setting %d %d"%(col,row))
        if role == QtCore.Qt.EditRole:
            if value.strip() == "":
                return False
        if row == len(self.mylist):
            self.beginInsertRows(QtCore.QModelIndex(), self.rowCount(), self.rowCount())
            self.add_entry()
            returnval = super(ImportTableModel, self).setData(index, value, role)
            self.endInsertRows()
            if col == 1:
                valsplit = value.split()
                basepath = os.path.basename(valsplit[0])
                #print(row)
                newindex = self.index(row, col - 1,QtCore.QModelIndex())
                self.setData(newindex,basepath,role)
                self.dataChanged.emit(newindex, newindex)
                #print(row)
                newindex = self.index(row, col + 1 ,QtCore.QModelIndex())
                #print("NEWINDEX",newindex.column(),newindex.row())
                self.setData(newindex, basepath, role)
                self.dataChanged.emit(newindex,newindex)
            return returnval


        returnval = super(ImportTableModel, self).setData(index, value, role)
        if col == 1:
            valsplit = value.split()
            basepath = os.path.basename(valsplit[0])
            #print(row)
            newindex = self.index(row, col - 1, QtCore.QModelIndex())
            self.setData(newindex, basepath, role)
            self.dataChanged.emit(newindex, newindex)
            #print(row)
            newindex = self.index(row, col + 1, QtCore.QModelIndex())
            #print("NEWINDEX", newindex.column(), newindex.row())
            self.setData(newindex, basepath, role)
            self.dataChanged.emit(newindex, newindex)
        #print("End of %d %d" %(col,row))
        return returnval

    def make_default_list(self):
        self.mylist = [
        ]
        self.header = ["Name", "ImportFrom", "Target Filename"]
        self.alignments = [pyside_int_workaround(QtCore.Qt.AlignCenter), pyside_int_workaround(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter),
                           pyside_int_workaround(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter),pyside_int_workaround(QtCore.Qt.AlignCenter)]


class ResourceTableModel(ResourceTableBase):


    def __init__(self, parent, *args,**kwargs):
        super(ResourceTableModel, self).__init__(parent, *args,**kwargs)
        self.mylist = [
        ]
        self.header = ["Enable", "Property", "Value"]
        self.alignments = [pyside_int_workaround(QtCore.Qt.AlignCenter),pyside_int_workaround(QtCore.Qt.AlignLeft| QtCore.Qt.AlignVCenter),pyside_int_workaround(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)]

    def render_to_simstack_server_model(self):
        return ClientResourceModelToServerResourceModel(self.mylist)

    def flags(self, index):
        if (index.column() == 1):
            return QtCore.Qt.ItemIsEnabled
        else:
            return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled


    def make_default_list(self):
        self.mylist = get_default_resource_list()
        self.header = ["Enable", "Property", "Value"]
        self.alignments = [pyside_int_workaround(QtCore.Qt.AlignCenter), pyside_int_workaround(QtCore.Qt.AlignLeft| QtCore.Qt.AlignVCenter),pyside_int_workaround(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)]

    def load(self,filename):
        self.mylist = load_resource_list(filename)

class GlobalFileChooserDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent):
        QtWidgets.QStyledItemDelegate.__init__(self, parent)

    def paint(self, painter, option, index):
        if (option.state & QtWidgets.QStyle.State_Selected):
            painter.fillRect(option.rect, option.palette.highlight())
        return

    def open_remote_importer_files(self, label, custom_widget):
        wf = self.parent().model().wano_parent.get_root().get_parent_wf()

        varpaths = wf.assemble_files("")
        from WaNo.view.RemoteImporterDialog import RemoteImporterDialog
        mydialog = RemoteImporterDialog(varname ="Import file",
                                        importlist = varpaths,
                                        window_title="Workflow File Importer")
        mydialog.setModal(True)
        mydialog.exec_()
        result = mydialog.result()
        if mydialog.result() == True:
            choice = mydialog.getchoice()
            #self.change_wf_file(choice)
            label.setText(choice)
            #self.set_file_import(choice)
            #self.set_disable(True)
        else:
            #self.change_wf_file("")
            label.setText("")
            #self.set_disable(False)
            #slf.set_file_import(None)
        self.commitData.emit(custom_widget)


    def createEditor(self, parent, option, index):
        from WaNo.view.MultiselectDropDownList import MultiselectDropDownList

        custom_widget = QtWidgets.QWidget(parent)
        hbl = QtWidgets.QHBoxLayout()
        custom_widget.setLayout(hbl)

        label = QtWidgets.QLabel(str(index.data()), custom_widget)
        hbl.addWidget(label)
        hbl.addStretch()
        openwfbutton = QtWidgets.QPushButton(QtGui.QIcon.fromTheme("insert-object"),"")
        #MultiselectDropDownList(self, autoset_text=False)
        openwfbutton.setFixedSize(28,28)
        #openwfbutton.setIcon(QtWidgets.QFileIconProvider().icon(QtWidgets.QFileIconProvider.Network))
        #openwfbutton.itemSelectionChanged.connect(self.on_wf_file_change)
        #openwfbutton.connect_workaround(self.load_wf_files)
        #openwfbutton.external_label = label
        #openwfbutton.editor = custom_widget
        myopenreport = lambda: self.open_remote_importer_files(label=label, custom_widget=custom_widget)
        openwfbutton.clicked.connect(myopenreport)
        hbl.addWidget(openwfbutton)

        #hbl.setSpacing(0)
        hbl.setContentsMargins(0,0,0,0)
        hbl.setAlignment(QtCore.Qt.AlignCenter)
        hbl.setSizeConstraint(QtWidgets.QLayout.SetMaximumSize)
        return custom_widget

    def load_wf_files(self):
        #I know this would be better the other way, i.e. make a signal, forward the signal, etc.
        #but it's the only place we would need this signal.
        s = self.sender()
        wf = self.parent().model().wano_parent.get_root().get_parent_wf()
        importable_files = wf.get_root().assemble_files("")
        s.set_items(importable_files)

    def change_wf_file(self, filename):
        print(f"Chose filename  {filename}")
        #label.setText(filename)
        #openwfbutton = self.sender()
        #print(openwfbutton)
        #flist = " ".join(openwfbutton.get_selection())
        #openwfbutton.external_label.setText(flist)
        #self.commitData.emit(None)
        #print("emitting")
        #self.commitData.emit(openwfbutton.external_label)
        #self.commitData.emit(openwfbutton.editor)

    def setEditorData(self, editor, index):
        editor.blockSignals(True)
        #editor.setCurrentIndex(int(index.model().data(index)))
        #editor.layout().itemAt(0).setText(index.data())
        #         self.label.setText(index.data())
        editor.blockSignals(False)

    def setModelData(self, editor, model, index):
        #print("SetModelData called")
        model.setData(index, editor.layout().itemAt(0).widget().text())

    def currentIndexChanged(self):
        self.commitData.emit(self.sender())


class FileChooserDelegate(QtWidgets.QItemDelegate):
    def __init__(self, parent):
        QtWidgets.QItemDelegate.__init__(self, parent)

    def paint(self, painter, option, index):

        if (option.state & QtWidgets.QStyle.State_Selected):
            painter.fillRect(option.rect, option.palette.highlight())
        return
        if index.column() == IMAGE:
            painter.drawPixmap(option.rect,
                               QPixmap(index.model().data(index).toString()))

        #QItemDelegate.paint(self, painter, option, index)

    def createEditor(self, parent, option, index):
        custom_widget = QtWidgets.QWidget(parent)
        hbl = QtWidgets.QHBoxLayout()
        custom_widget.setLayout(hbl)

        label = QtWidgets.QLabel(str(index.data()), custom_widget)
        hbl.addWidget(label)
        hbl.addStretch()
        combo = QtWidgets.QPushButton(str(index.data()), custom_widget)
        hbl.addWidget(combo)

        #hbl.setSpacing(0)
        hbl.setContentsMargins(0,0,0,0)
        hbl.setAlignment(QtCore.Qt.AlignCenter)
        hbl.setSizeConstraint(QtWidgets.QLayout.SetMaximumSize)
        # self.connect(combo, QtCore.SIGNAL("currentIndexChanged(int)"), self, QtCore.SLOT("currentIndexChanged()"))
        #combo.clicked.connect(self.currentIndexChanged)
        return custom_widget

    def setEditorData(self, editor, index):
        editor.blockSignals(True)
        # editor.setCurrentIndex(int(index.model().data(index)))
        editor.blockSignals(False)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.text())

    def currentIndexChanged(self):
        self.commitData.emit(self.sender())

class ButtonDelegate(QtWidgets.QItemDelegate):
    def __init__(self, parent):
        QtWidgets.QItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        self.combo = QtWidgets.QPushButton(str(index.data()), parent)
        # self.connect(combo, QtCore.SIGNAL("currentIndexChanged(int)"), self, QtCore.SLOT("currentIndexChanged()"))
        self.combo.clicked.connect(self.on_button_clicked)
        return self.combo

    def on_button_clicked(self):
        pass


    #def setEditorData(self, editor, index):
    #    editor.blockSignals(True)
    #    self.combo.setText(index.model().data(index))
    #    # editor.setCurrentIndex(int(index.model().data(index)))
    #    editor.blockSignals(False)



    #def setModelData(self, editor, model, index):
    #    model.setData(index, editor.text())

    #def currentIndexChanged(self):
    #    self.commitData.emit(self.sender())


class CheckBoxDelegate(QtWidgets.QStyledItemDelegate):
    """
    A delegate that places a fully functioning QCheckBox in every
    cell of the column to which it's applied
    """
    def __init__(self, parent):
        super(CheckBoxDelegate,self).__init__(parent)
        #QtWidgets.QItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        '''
        Important, otherwise an editor is created if the user clicks in this cell.
        ** Need to hook up a signal to the model
        '''
        return None

    def paint(self, painter, option, index):
        '''
        Paint a checkbox without the label.
        '''

        checked = index.data()
        check_box_style_option = QtWidgets.QStyleOptionButton()

        if (index.flags() & QtCore.Qt.ItemIsEditable):
            check_box_style_option.state |= QtWidgets.QStyle.State_Enabled
        else:
            check_box_style_option.state |= QtWidgets.QStyle.State_ReadOnly

        if checked:
            check_box_style_option.state |= QtWidgets.QStyle.State_On
        else:
            check_box_style_option.state |= QtWidgets.QStyle.State_Off

        check_box_style_option.rect = self.getCheckBoxRect(option)

        # this will not run - hasFlag does not exist
        #if not index.model().hasFlag(index, QtCore.Qt.ItemIsEditable):
            #check_box_style_option.state |= QtWidgets.QStyle.State_ReadOnly

        check_box_style_option.state |= QtWidgets.QStyle.State_Enabled

        QtWidgets.QApplication.style().drawControl(QtWidgets.QStyle.CE_CheckBox, check_box_style_option, painter)

    def editorEvent(self, event, model, option, index):
        '''
        Change the data in the model and the state of the checkbox
        if the user presses the left mousebutton or presses
        Key_Space or Key_Select and this cell is editable. Otherwise do nothing.
        '''
        if not (index.flags() & QtCore.Qt.ItemIsEditable):
            return False

        # Do not change the checkbox-state
        if event.type() == QtCore.QEvent.MouseButtonPress:
          return False
        if event.type() == QtCore.QEvent.MouseButtonRelease or event.type() == QtCore.QEvent.MouseButtonDblClick:
            if event.button() != QtCore.Qt.LeftButton or not self.getCheckBoxRect(option).contains(event.pos()):
                return False
            if event.type() == QtCore.QEvent.MouseButtonDblClick:
                return True
        elif event.type() == QtCore.QEvent.KeyPress:
            if event.key() != QtCore.Qt.Key_Space and event.key() != QtCore.Qt.Key_Select:
                return False
            else:
                return False

        # Change the checkbox-state
        self.setModelData(None, model, index)
        return True

    def setModelData (self, editor, model, index):
        '''
        The user wanted to change the old state in the opposite.
        '''
        newValue = not index.data()
        model.setData(index, newValue, QtCore.Qt.EditRole)

    def getCheckBoxRect(self, option):
        check_box_style_option = QtWidgets.QStyleOptionButton()
        check_box_rect = QtWidgets.QApplication.style().subElementRect(QtWidgets.QStyle.SE_CheckBoxIndicator, check_box_style_option, None)
        check_box_point = QtCore.QPoint (option.rect.x() +
                            option.rect.width() / 2 -
                            check_box_rect.width() / 2,
                            option.rect.y() +
                            option.rect.height() / 2 -
                            check_box_rect.height() / 2)
        return QtCore.QRect(check_box_point, check_box_rect.size())

class ComboDelegate(QtWidgets.QItemDelegate):
    """
    A delegate that places a fully functioning QComboBox in every
    cell of the column to which it's applied
    """

    def __init__(self, parent):
        QtWidgets.QItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        combo = QtWidgets.QComboBox(parent)
        li = []
        li.append("Zero")
        li.append("One")
        li.append("Two")
        li.append("Three")
        li.append("Four")
        li.append("Five")
        combo.addItems(li)
        self.connect(combo, QtCore.SIGNAL("currentIndexChanged(int)"), self, QtCore.SLOT("currentIndexChanged()"))
        return combo

    def setEditorData(self, editor, index):
        editor.blockSignals(True)
        editor.setCurrentIndex(int(index.model().data(index)))
        editor.blockSignals(False)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentIndex())

    def currentIndexChanged(self):
        self.commitData.emit(self.sender())


class TableView(QtWidgets.QTableView):
    """
    A simple table to demonstrate the QComboBox delegate.
    """

    def __init__(self, *args, **kwargs):
        QtWidgets.QTableView.__init__(self, *args, **kwargs)


        # Set the delegate for column 0 of our table
        # self.setItemDelegateForColumn(0, ButtonDelegate(self))

        #self.setItemDelegateForColumn(0, ComboDelegate(self))
        self.setItemDelegateForColumn(0, CheckBoxDelegate(self))
        #self.setItemDelegateForColumn(0, FileChooserDelegate(self))
        #self.setItemDelegateForColumn(1, CheckBoxDelegate(self))




class ResourceView(QtWidgets.QTableView):
    """
    A simple table to demonstrate the QComboBox delegate.
    """
    def __init__(self, *args, **kwargs):
        QtWidgets.QTableView.__init__(self, *args, **kwargs)
        self.setItemDelegateForColumn(0, CheckBoxDelegate(self))
        #self.setItemDelegateForColumn(2, GlobalFileChooserDelegate(self))

    def setModel(self,model):
        super(ResourceView,self).setModel(model)
        for row in range(0, model.rowCount()):
            self.openPersistentEditor(model.index(row, 0))


class ImportView(QtWidgets.QTableView):
    """
    A simple table to demonstrate the QComboBox delegate.
    """
    def __init__(self, *args, **kwargs):
        QtWidgets.QTableView.__init__(self, *args, **kwargs)
        gfcd = GlobalFileChooserDelegate(self)
        self.setItemDelegateForColumn(1, gfcd)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.verticalHeader().show()
        self.horizontalHeader().show()
        #self.verticalHeader().sectionClicked.connect(self._selectRow)
        self.setStyleSheet("QTreeView::item:selected{background-color: palette(highlight); color: palette(highlightedText);};")
        #connect(ui->tableWidget->verticalHeader(), SIGNAL(sectionClicked(int)), this, SLOT(verticalHeaderClicked(int)));


    def keyPressEvent(self,event):
        if (event.key() == QtCore.Qt.Key_Delete):
            selectionmodel = self.selectionModel()
            for rowm in selectionmodel.selectedRows():
                self.model().delete_entry(rowm.row())
                #print (rowm.row())
            #In delete condition. We tell the model our selectionindex and delete
            return
        super(ImportView,self).keyPressEvent(event)


    def setModel(self,model):

        super(ImportView,self).setModel(model)
        for row in range(0, model.rowCount()):
            self.openPersistentEditor(model.index(row, 1))
        model.rowsInserted.connect(self.openpersistentslot)

    def openpersistentslot(self):
        for row in range(0, self.model().rowCount()):
            self.openPersistentEditor(self.model().index(row, 1))


class ExportView(QtWidgets.QTableView):
    """
    A simple table to demonstrate the QComboBox delegate.
    """
    def __init__(self, *args, **kwargs):
        QtWidgets.QTableView.__init__(self, *args, **kwargs)
        #gfcd = GlobalFileChooserDelegate(self)
        #self.setItemDelegateForColumn(1, gfcd)


    def keyPressEvent(self, event):
        if (event.key() == QtCore.Qt.Key_Delete):
            selectionmodel = self.selectionModel()
            for rowm in selectionmodel.selectedRows():
                self.model().delete_entry(rowm.row())
                # print (rowm.row())
            # In delete condition. We tell the model our selectionindex and delete
            return
        super(ExportView, self).keyPressEvent(event)

if __name__ == "__main__":
    from sys import argv, exit


    class Widget(QtWidgets.QWidget):
        """
        A simple test widget to contain and own the model and table.
        """

        def __init__(self, parent=None):
            QtWidgets.QWidget.__init__(self, parent)

            l = QtWidgets.QVBoxLayout(self)

            self._tm = ResourceTableModel(self)

            #self._tm = ImportTableModel(self)
            self._tm.make_default_list()
            self._tv = TableView(self)
            self._tv.setModel(self._tm)
            for row in range(0, self._tm.rowCount()):
                self._tv.openPersistentEditor(self._tm.index(row, 0))


            l.addWidget(self._tv)
            self._tv.resizeColumnsToContents()


    a = QtWidgets.QApplication(argv)
    w = Widget()
    w.show()
    w.raise_()
    exit(a.exec_())
