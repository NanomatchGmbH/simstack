#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

from WaNo.view.MultiselectDropDownList import MultiselectDropDownList
from WaNo.view.AbstractWaNoView import AbstractWanoQTView, AbstractWanoView
from Qt import QtGui, QtCore, QtWidgets
import os

class GroupBoxWithButton(QtWidgets.QGroupBox):
    def __init__(self,*args,**kwargs):
        super(GroupBoxWithButton,self).__init__(*args,**kwargs)
        script_path = os.path.dirname(os.path.realpath(__file__))
        media_path = os.path.join(script_path, "..", "Media")
        listaddpath = os.path.join(media_path, "list-add.png")
        self.add_button = QtWidgets.QPushButton("", parent=self)
        self.add_button.setIcon(QtGui.QIcon(listaddpath))
        #self.add_button.setFlat(True)
        listremovepath = os.path.join(media_path, "list-remove.png")
        self.remove_button = QtWidgets.QPushButton("", parent=self)
        self.remove_button.setIcon(QtGui.QIcon(listremovepath))
        #self.remove_button.setFlat(True)
        self.add_button.setFixedSize(24,24)
        self.remove_button.setFixedSize(24, 24)
        self.init_button()

    def init_button(self):
        width = self.size().width()
        #print(width)
        self.add_button.move(width - self.add_button.size().width()-40, 0)
        self.remove_button.move(width - self.remove_button.size().width() - 10, 0)

    def resizeEvent(self, event):
        returnval = super(GroupBoxWithButton,self).resizeEvent(event)
        self.init_button()
        return returnval

    def get_button_objects(self):
        return self.add_button,self.remove_button

class MultipleOfView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(MultipleOfView, self).__init__(*args, **kwargs)
        self.actual_widget = GroupBoxWithButton(self.qt_parent)
        self.actual_widget.setStyleSheet("""
            QGroupBox {
                border: 1px solid gray;
                border-radius: 9px;
                margin-top: 0.5em;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            """)

        # self.actual_widget.setCheckable(True)
        self.vbox = QtWidgets.QVBoxLayout()
        self.actual_widget.setLayout(self.vbox)
        add,rem = self.actual_widget.get_button_objects()
        add.clicked.connect(self.add_button_clicked)
        rem.clicked.connect(self.remove_button_clicked)


    def add_button_clicked(self):
        self.model.add_item()
        line = QtWidgets.QFrame(self.actual_widget)
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.vbox.addWidget(line)
        for model_dict in reversed(self.model):
            for model in model_dict.values():
                self.vbox.addWidget(model.view.get_widget())
            break




    def remove_button_clicked(self):
        removed = self.model.delete_item()
        numwidgets = self.vbox.count()
        if removed:
            for i in range(0,self.model.numitems_per_add()+1):
                self.vbox.itemAt(numwidgets - 1 - i).widget().deleteLater()

    def get_widget(self):
        return self.actual_widget


    def init_from_model(self):
        self.actual_widget.setTitle(self.model.name)
        for model_dict in self.model:
            for model in model_dict.values():
                self.vbox.addWidget(model.view.get_widget())
            line = QtWidgets.QFrame(self.actual_widget)
            line.setFrameShape(QtWidgets.QFrame.HLine)
            line.setFrameShadow(QtWidgets.QFrame.Sunken)
            self.vbox.addWidget(line)
        line.deleteLater()

class EmptyView(AbstractWanoView):
    def __init__(self,*args,**kwargs):
        super(EmptyView,self).__init__(*args,**kwargs)

class WaNoGroupView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoGroupView, self).__init__(*args, **kwargs)
        self.actual_widget = QtWidgets.QWidget(self.qt_parent)
        self.vbox = QtWidgets.QVBoxLayout()
        self.actual_widget.setLayout(self.vbox)

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):
        for model in self.model.wanos():
            self.vbox.addWidget(model.view.get_widget())

class WaNoConditionalView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoConditionalView, self).__init__(*args, **kwargs)
        #self.actual_widget = QtWidgets.QWidget(self.qt_parent)
        self.actual_widget = QtWidgets.QWidget(parent=self.qt_parent)
        #self.actual_widget = GroupBoxWithButton(self.qt_parent)
        self.vbox = QtWidgets.QVBoxLayout()
        self.actual_widget.setLayout(self.vbox)

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):
        self.actual_widget.setTitle(self.model.name)
        for model in self.model.wanos():
            self.vbox.addWidget(model.view.get_widget())

class WaNoBoxView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoBoxView, self).__init__(*args, **kwargs)
        #self.actual_widget = QtWidgets.QWidget(self.qt_parent)
        self.actual_widget = QtWidgets.QGroupBox(parent=self.qt_parent)
        #self.actual_widget = GroupBoxWithButton(self.qt_parent)
        self.actual_widget.setStyleSheet("""
        QGroupBox {
            border: 1px solid gray;
            border-radius: 9px;
            margin-top: 0.5em;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px 0 3px;
        }
        """)
        #self.actual_widget.setCheckable(True)
        #self.actual_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        self.vbox = QtWidgets.QVBoxLayout()
        self.actual_widget.setLayout(self.vbox)

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):
        self.actual_widget.setTitle(self.model.name)
        for model in self.model.wanos():
            self.vbox.addWidget(model.view.get_widget())


class WaNoItemIntView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoItemIntView, self).__init__(*args, **kwargs)
        """ Widget code here """
        self.actual_widget = QtWidgets.QWidget(self.qt_parent)
        hbox = QtWidgets.QHBoxLayout()
        self.actual_widget.setLayout(hbox)
        self.spinner = QtWidgets.QSpinBox()
        # self.line_edit = QtWidgets.QLineEdit()
        self.spinner.setValue(0)
        self.spinner.setMaximum(1000000000)
        self.spinner.setMinimum(-1000000000)
        self.label = QtWidgets.QLabel("ABC")
        hbox.addWidget(self.label)
        hbox.addStretch()
        hbox.addWidget(self.spinner)
        #self.actual_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        #self.actual_widget.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        # hbox.addWidget(self.line_edit)

        self.spinner.valueChanged.connect(self.value_changed)
        """ Widget code end """

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):
        self.spinner.setValue(self.model.get_data())
        self.label.setText(self.model.name)

    def value_changed(self,value):
        self.model.set_data(value)


class WaNoItemFloatView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoItemFloatView, self).__init__(*args, **kwargs)
        """ Widget code here """
        self.actual_widget = QtWidgets.QWidget(self.qt_parent)
        hbox = QtWidgets.QHBoxLayout()
        self.actual_widget.setLayout(hbox)
        self.spinner = QtWidgets.QDoubleSpinBox()
        # self.line_edit = QtWidgets.QLineEdit()
        self.spinner.setValue(0.0)
        self.spinner.setMaximum(10000000000)
        self.spinner.setMinimum(-10000000000)
        self.spinner.setDecimals(5)
        self.spinner.setSingleStep(1.0)
        #self.actual_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        #self.actual_widget.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.label = QtWidgets.QLabel("ABC")
        #self.label.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed
        #self.label.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        hbox.addWidget(self.label)
        hbox.addStretch()
        hbox.addWidget(self.spinner)
        # hbox.addWidget(self.line_edit)

        self.spinner.valueChanged.connect(self.value_changed)

        #print(self.actual_widget.minimumSize())

        #print(self.spinner.sizeHint())

        #self.spinner.setMinimumSize(self.spinner.sizeHint())
        #self.spinner.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        """ Widget code end """

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):
        self.spinner.setValue(self.model.get_data())
        self.label.setText(self.model.name)
        #self.model.root_model.view.actual_widget.viewport().update_geometry()
        #self.model.root_model.view.actual_widget.viewport().update()
        #self.model.root_model.view.actual_widget.update()

    def value_changed(self,value):
        self.model.set_data(value)

class WaNoItemBoolView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoItemBoolView, self).__init__(*args, **kwargs)
        """ Widget code here """
        self.actual_widget = QtWidgets.QWidget(self.qt_parent)
        hbox = QtWidgets.QHBoxLayout()
        self.actual_widget.setLayout(hbox)
        self.checkbox = QtWidgets.QCheckBox()
        self.label = QtWidgets.QLabel("ABC")
        hbox.addWidget(self.label)
        hbox.addStretch()
        hbox.addWidget(self.checkbox)
        # hbox.addWidget(self.line_edit)

        #self.actual_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.checkbox.stateChanged.connect(self.state_changed)
        """ Widget code end """

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):

        self.checkbox.setChecked(self.model.get_data())
        self.label.setText(self.model.name)

    def state_changed(self):
        if self.checkbox.isChecked():
            self.model.set_data(True)
        else:
            self.model.set_data(False)


class WaNoScriptView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoScriptView,self).__init__(*args,**kwargs)
        """ Widget code here """
        self.actual_widget = QtWidgets.QWidget(self.qt_parent)
        vbox = QtWidgets.QVBoxLayout()
        self.actual_widget.setLayout(vbox)
        self.menubar = QtWidgets.QWidget()
        hbox = QtWidgets.QHBoxLayout()
        self.menubar.setLayout(hbox)
        self.savelabel = QtWidgets.QLabel("Save script")
        self.savebutton = QtWidgets.QPushButton(QtGui.QIcon.fromTheme("document-save"),"Save Script")
        self.savebutton.clicked.connect(self.on_save)
        hbox.addWidget(self.savebutton)
        vbox.addWidget(self.menubar)
        self.textedit = QtWidgets.QTextEdit()
        vbox.addWidget(self.textedit)
        """ Widget code end """

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):
        text = self.model.get_as_text()
        self.textedit.setText(text)

    def on_save(self):
        self.model.save_text(self.textedit.toPlainText())



class WaNoItemStringView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoItemStringView, self).__init__(*args, **kwargs)
        """ Widget code here """
        self.actual_widget = QtWidgets.QWidget(self.qt_parent)
        vbox = QtWidgets.QHBoxLayout()
        self.lineedit = QtWidgets.QLineEdit()
        self.label = QtWidgets.QLabel("ABC")
        vbox.addWidget(self.label)
        vbox.addStretch()
        vbox.addWidget(self.lineedit)
        # vbox.addWidget(self.line_edit)
        self.actual_widget.setLayout(vbox)
        self.lineedit.editingFinished.connect(self.line_edited)
        """ Widget code end """

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):
        self.lineedit.setText(self.model.get_data())
        self.label.setText(self.model.name)

    def line_edited(self):
        self.model.set_data(self.lineedit.text())


class WanoQtViewRoot(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WanoQtViewRoot, self).__init__(*args, **kwargs)
        self.init_to_scroller()

    def init_to_scroller(self):
        scroll = QtWidgets.QScrollArea(parent=self.qt_parent)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll.setWidgetResizable(True)
        me = QtWidgets.QWidget(parent=scroll)
        scroll.setWidget(me)
        # scroll.resize(460,700)
        self.actual_widget = scroll
        self.vbox = QtWidgets.QVBoxLayout()
        # me.setMinimumSize(QtCore.QSize(900, 900))
        me.setLayout(self.vbox)

    def init_without_scroller(self):
        me = QtWidgets.QWidget(parent=self.qt_parent)
        self.vbox = QtWidgets.QVBoxLayout()
        me.setLayout(self.vbox)
        self.actual_widget = me

    def get_widget(self):
        return self.actual_widget

    def get_resource_widget(self):
        model = self.model.get_resource_model()
        from WaNo.view.PropertyListView import ResourceView
        self.resourceview = ResourceView()
        self.resourceview.setModel(model)
        return self.resourceview

    def get_import_widget(self):
        model = self.model.get_import_model()
        from WaNo.view.PropertyListView import ImportView
        self.importview = ImportView()
        self.importview.setModel(model)
        return self.importview

    def get_export_widget(self):
        model = self.model.get_export_model()
        from WaNo.view.PropertyListView import ExportView
        self.exportview = ExportView()
        self.exportview.setModel(model)
        return self.exportview

    def init_from_model(self):
        from WaNo.view.WaNoViews import WaNoTabView
        for key, model in self.model.wano_dict.items():

            if isinstance(model.view,WaNoTabView):
                self.init_without_scroller()

            self.vbox.addWidget(model.view.get_widget())
        #self.actual_widget.viewport().update()
        self.actual_widget.update()

class WaNoItemFileView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoItemFileView, self).__init__(*args, **kwargs)
        """ Widget code here """
        self.actual_widget = QtWidgets.QWidget(self.qt_parent)
        hbox = QtWidgets.QHBoxLayout()
        self.lineedit = QtWidgets.QLineEdit(parent=self.actual_widget)
        self.label = QtWidgets.QLabel("ABC",parent=self.actual_widget)
        self.openfilebutton = QtWidgets.QPushButton("",parent=self.actual_widget)

        self.openfilebutton.setIcon(QtWidgets.QFileIconProvider().icon(QtWidgets.QFileIconProvider.File))

        """
        self.openwfbutton = QtWidgets.QPushButton("",parent=self.actual_widget)
        self.openwfbutton.clicked.connect(self.showWFDialog)
        """
        #begin change
        self.openwfbutton = MultiselectDropDownList(self, autoset_text=False)
        self.openwfbutton.setIcon(QtWidgets.QFileIconProvider().icon(QtWidgets.QFileIconProvider.Network))
        self.openwfbutton.connect_workaround(self.load_wf_files)
        self.openwfbutton.itemSelectionChanged.connect(self.on_wf_file_change)

        #End of change
        hbox.addWidget(self.label)
        hbox.addStretch()
        hbox.addWidget(self.lineedit)
        hbox.addWidget(self.openfilebutton)
        hbox.addWidget(self.openwfbutton)
        self.openfilebutton.clicked.connect(self.showLocalDialog)

        self.actual_widget.setLayout(hbox)
        self.lineedit.editingFinished.connect(self.line_edited)
        #print(self.actual_widget.minimumSize())

        #self.actual_widget.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        """ Widget code end """

    def showLocalDialog(self):
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(self.actual_widget, 'Open file', QtCore.QDir.homePath())
        if fname:
            self.lineedit.setText(fname)
            self.model.set_local(True)
            self.line_edited()

    """
    def showWFDialog(self):
        wf = self.model.root_model.parent_wf
        importable_files = wf.assemble_files()
    """

    def load_wf_files(self):
        wf = self.model.root_model.parent_wf.get_root()
        print(type(wf))
        importable_files = wf.assemble_files("")
        self.openwfbutton.set_items(importable_files)

    def on_wf_file_change(self):
        self.lineedit.setText(" ".join(self.openwfbutton.get_selection()))
        self.model.set_local(False)
        self.line_edited()

    """
        self.open_variables = MultiselectDropDownList(self,text="Import")
        self.open_variables.itemSelectionChanged.connect(self.onItemSelectionChange)
        self.open_variables.connect_workaround(self._load_variables)
        self.topLineLayout.addWidget(self.open_variables)
        return 1

    def _load_variables(self):
        parent = self.parent()
        while not parent.topWidget:
            parent = parent.parent()
        vars = parent.get_wano_variables()
        self.open_variables.set_items(vars)

    def onItemSelectionChange(self):
        self.list_of_variables.setText(" ".join(self.open_variables.get_selection()))
    """

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):
        self.lineedit.setText(self.model.get_data())
        self.label.setText(self.model.name)

    def line_edited(self):
        self.model.set_data(self.lineedit.text())

class OnlyFloatDelegate(QtWidgets.QItemDelegate):
    def createEditor(self, parent, option, index):
        return QtWidgets.QDoubleSpinBox(parent)

class WaNoMatrixFloatView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoMatrixFloatView,self).__init__(*args,**kwargs)
        self.has_col_header = False
        self.has_row_header = False
        """ Widget code here """
        self.actual_widget = QtWidgets.QWidget(self.qt_parent)

        self.tablewidget = QtWidgets.QTableWidget(1,3,self.actual_widget)
        delegate=OnlyFloatDelegate()
        self.tablewidget.setItemDelegate(delegate)
        self.tablewidget.verticalHeader().setVisible(False)
        self.tablewidget.horizontalHeader().setVisible(False)
        self.tablewidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tablewidget.setSizePolicy(QtWidgets.QSizePolicy.Minimum,QtWidgets.QSizePolicy.Minimum)
        #self.tablewidget.horizontalHeader().setMinimumSectionSize(1)
        #self.tablewidget.verticalHeader().setMinimumSectionSize(1)
        #self.tablewidget.horizontalHeader().setDefaultSectionSize(1)
        self.tablewidget.verticalHeader().setDefaultSectionSize(24)
        self.tablewidget.horizontalHeader().setFixedHeight(20)
        #self.tablewidget.verticalHeader().setSectionResiz
        self.tablewidget.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        self.tablewidget.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        #self.tablewidget.resizeColumnsToContents()
        #self.tablewidget.resizeRowsToContents()



        hbox = QtWidgets.QHBoxLayout()
        self.actual_widget.setLayout(hbox)
        self.label = QtWidgets.QLabel("Table")
        hbox.addWidget(self.label)
        hbox.addStretch()
        hbox.addWidget(self.tablewidget)
        self.tablewidget.cellChanged.connect(self.cellChanged)
        """" Widget code end """

    def cellChanged(self,i,j):
        self.model.storage[i][j] = float(self.tablewidget.item(i,j).text())

    def reset_table(self):
        self.tablewidget.clear()
        self.tablewidget.setRowCount(self.model.rows)
        self.tablewidget.setColumnCount(self.model.cols)

        if not self.model.col_header is None:
            self.has_col_header = True
            self.tablewidget.setHorizontalHeaderLabels(self.model.col_header)
            self.tablewidget.horizontalHeader().setVisible(True)

        if not self.model.row_header is None:
            self.has_row_header = True
            self.tablewidget.setVerticalHeaderLabels(self.model.row_header)
            self.tablewidget.verticalHeader().setVisible(True)

        for i in range(0, self.tablewidget.rowCount()):
            for j in range(0, self.tablewidget.columnCount()):
                item = QtWidgets.QTableWidgetItem()
                self.tablewidget.setItem(i, j, item)
                self.tablewidget.item(i, j).setTextAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        extra_size = 2
        if self.has_row_header:
            extra_size = 2 + 20
        self.tablewidget.setFixedHeight(24*self.tablewidget.rowCount() + extra_size)

    def init_from_model(self):
        self.label.setText(self.model.name)
        self.tablewidget.blockSignals(True)
        self.reset_table()

        storage = self.model.storage
        for i in range(len(storage)):
            for j in range(len(storage[0])):
                self.tablewidget.item(i,j).setText(str(storage[i][j]))

        self.tablewidget.blockSignals(False)
        return

    def get_widget(self):
        return self.actual_widget

class WaNoDropDownView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoDropDownView,self).__init__(*args,**kwargs)
        """ Widget code here """
        self.actual_widget = QtWidgets.QWidget(self.qt_parent)

        self.combobox = QtWidgets.QComboBox(self.actual_widget)
        self.combobox.currentIndexChanged[int].connect(self.onButtonClicked)

        hbox = QtWidgets.QHBoxLayout()
        self.actual_widget.setLayout(hbox)
        self.label = QtWidgets.QLabel("Combo")
        hbox.addWidget(self.label)
        hbox.addStretch()
        hbox.addWidget(self.combobox)
        self.init = False
        """" Widget code end """

    def init_from_model(self):
        self.label.setText(self.model.name)
        for myid,entry in enumerate(self.model.choices):
            self.combobox.addItem(entry)


        self.combobox.setCurrentIndex(self.model.chosen)
        self.init = True

    def onButtonClicked(self, id):
        if self.init:
            self.model.set_chosen(id)

    def get_widget(self):
        return self.actual_widget


class WaNoChoiceView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoChoiceView,self).__init__(*args,**kwargs)
        """ Widget code here """
        self.actual_widget = QtWidgets.QGroupBox(self.qt_parent)
        self.bg = QtWidgets.QButtonGroup(self.qt_parent)
        self.vbox = QtWidgets.QVBoxLayout(self.actual_widget)
        self.actual_widget.setLayout(self.vbox)

        self.actual_widget.setStyleSheet("""
        QGroupBox {
            border: 1px solid gray;
            border-radius: 9px;
            margin-top: 0.5em;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 3px 0 3px;
        }
        """)
        self.buttons = []
        self.bg.buttonClicked[int].connect(self.onButtonClicked)
        ##self.actual_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        """" Widget code end """

    def init_from_model(self):
        self.actual_widget.setTitle(self.model.name)
        for myid,entry in enumerate(self.model.choices):
            checkbox = QtWidgets.QRadioButton(entry,parent=self.actual_widget)
            self.buttons.append(checkbox)
            self.bg.addButton(checkbox,myid)
            self.vbox.addWidget(checkbox)
        #print(self.model.chosen)
        self.buttons[self.model.chosen].setChecked(True)

    def onButtonClicked(self, id):
        self.model.set_chosen(id)

    def get_widget(self):
        return self.actual_widget


class WaNoTabView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoTabView, self).__init__(*args, **kwargs)
        """ Widget code here """
        self.actual_widget = QtWidgets.QTabWidget(self.qt_parent)
        """" Widget code end """

    def init_from_model(self):

        for key, model in self.model.items():
            scroll = QtWidgets.QScrollArea(parent=self.actual_widget)
            scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
            scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
            scroll.setWidgetResizable(True)
            scroll.setWidget(model.view.get_widget())
            self.actual_widget.addTab(scroll,model.name)


    def get_widget(self):
        return self.actual_widget
