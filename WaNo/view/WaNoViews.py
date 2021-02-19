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
        self.actual_widget = GroupBoxWithButton(None)
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

        #List of bar widgets nobody else takes care about (for later deletion)
        self._list_of_bar_widgets = []

    def set_parent(self, parent_view):
        super().set_parent(parent_view)
        self.actual_widget.setParent(self._qt_parent)

    def add_button_clicked(self):
        self.model.add_item()
        self.init_from_model()
        return

    def remove_button_clicked(self):
        if self.model.last_item_check():
            return

        removed = self.model.delete_item()
        assert removed
        self.init_from_model()

    def get_widget(self):
        return self.actual_widget


    def init_from_model(self):
        self.actual_widget.setTitle(self.model.name)
        vbcount= self.vbox.count()

        for i in range(0, vbcount):
            myid = vbcount - 1  -i
            item = self.vbox.itemAt(myid)
            self.vbox.removeItem(item)


        while len(self._list_of_bar_widgets) > 0:
            mywidget = self._list_of_bar_widgets.pop()
            mywidget.deleteLater()

        nummodels = len(self.model)
        for mdictid, model_dict in enumerate(self.model):
            for mname, my_model in model_dict.items():
                self.vbox.addWidget(my_model.view.get_widget())

            if mdictid != nummodels - 1:
                line = QtWidgets.QFrame(self.actual_widget)
                line.setFrameShape(QtWidgets.QFrame.HLine)
                line.setFrameShadow(QtWidgets.QFrame.Sunken)
                self.vbox.addWidget(line)
                self._list_of_bar_widgets.append(line)
        super().init_from_model()

class EmptyView(AbstractWanoView):
    def __init__(self,*args,**kwargs):
        super(EmptyView,self).__init__(*args,**kwargs)

class WaNoGroupView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoGroupView, self).__init__(*args, **kwargs)
        self.actual_widget = QtWidgets.QWidget(None)
        self.vbox = QtWidgets.QVBoxLayout()
        self.actual_widget.setLayout(self.vbox)

    def set_parent(self, parent_view):
        super().set_parent(parent_view)
        self.actual_widget.setParent(self._qt_parent)

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):
        for model in self.model.wanos():
            #print(model, self.model.path, self, self.model)
            self.vbox.addWidget(model.view.get_widget())
        super().init_from_model()

class WaNoSwitchView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoSwitchView, self).__init__(*args, **kwargs)
        self.actual_widget = QtWidgets.QWidget(parent=None)
        self.vbox = QtWidgets.QVBoxLayout()
        self.actual_widget.setLayout(self.vbox)
        self._widgets_parsed = False

    def set_parent(self, parent_view):
        super().set_parent(parent_view)
        self.actual_widget.setParent(self._qt_parent)

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):
        if not self._widgets_parsed:
            try:
                for _,model in self.model.wanos():
                    addview = model.view.get_widget()
                    if addview is None:
                        raise IndexError("WaNo not yet initialized.")
                    self.vbox.addWidget(addview)
                self._widgets_parsed = True
            except IndexError as e:
                self._widgets_parsed = False
                self.vbox.clear()
                return

        selid = self.model.get_selected_id()
        for mid,(_,model) in enumerate(self.model.wanos()):
            if mid == selid:
                truefalse = True
            else:
                truefalse = False
            model.view.set_visible(truefalse)
        super().init_from_model()

class WaNoConditionalView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoConditionalView, self).__init__(*args, **kwargs)
        #self.actual_widget = QtWidgets.QWidget(self._qt_parent)
        self.actual_widget = QtWidgets.QWidget(parent=self._qt_parent)
        #self.actual_widget = GroupBoxWithButton(self._qt_parent)
        self.vbox = QtWidgets.QVBoxLayout()
        self.actual_widget.setLayout(self.vbox)

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):
        self.actual_widget.setTitle(self.model.name)
        for model in self.model.wanos():
            self.vbox.addWidget(model.view.get_widget())
        super().init_from_model()

class WaNoBoxView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoBoxView, self).__init__(*args, **kwargs)
        self.actual_widget = QtWidgets.QGroupBox(parent=None)
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

    def set_parent(self, parent_view):
        super().set_parent(parent_view)
        self.actual_widget.setParent(self._qt_parent)

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):
        self.actual_widget.setTitle(self.model.name)
        for model in self.model.wanos():
            self.vbox.addWidget(model.view.get_widget())
        super().init_from_model()

class WaNoNone(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoNone, self).__init__(*args, **kwargs)
        self.actual_widget = QtWidgets.QFrame(parent=None)
        self.vbox = QtWidgets.QVBoxLayout()
        self.actual_widget.setLayout(self.vbox)
        self.actual_widget.layout().setContentsMargins(0, 0, 0, 0)
        #self.actual_widget.layout().setContentsMargins(0, 0, 0, 0)

    def set_parent(self, parent_view):
        super().set_parent(parent_view)
        self.actual_widget.setParent(self._qt_parent)

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):
        super().init_from_model()

class WaNoInvisibleBoxView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoInvisibleBoxView, self).__init__(*args, **kwargs)
        self.actual_widget = QtWidgets.QFrame(parent=None)

        self.vbox = QtWidgets.QVBoxLayout()
        self.actual_widget.setLayout(self.vbox)
        self.actual_widget.layout().setContentsMargins(0, 0, 0, 0)

    def set_parent(self, parent_view):
        super().set_parent(parent_view)
        self.actual_widget.setParent(self._qt_parent)

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):
        for model in self.model.wanos():
            self.vbox.addWidget(model.view.get_widget())
        super().init_from_model()

class WaNoItemIntView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoItemIntView, self).__init__(*args, **kwargs)
        """ Widget code here """
        self.actual_widget = QtWidgets.QWidget(None)
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

        self._global_import_button = QtWidgets.QPushButton(QtGui.QIcon.fromTheme("insert-object"),"")
        self._global_import_button.clicked.connect(self.open_remote_importer)
        hbox.addWidget(self._global_import_button)
        #self.actual_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        #self.actual_widget.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        # hbox.addWidget(self.line_edit)

        self.spinner.valueChanged.connect(self.value_changed)
        """ Widget code end """

    def set_disable(self, true_or_false):
        self.spinner.setDisabled(true_or_false)

    def set_parent(self, parent_view):
        super().set_parent(parent_view)
        self.actual_widget.setParent(self._qt_parent)

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):
        self.spinner.setValue(self.model.get_data())
        self.label.setText(self.model.name)
        if self.model.do_import:
            self.set_disable(True)
        super().init_from_model()

    def value_changed(self,value):
        self.model.set_data(value)


class WaNoItemFloatView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoItemFloatView, self).__init__(*args, **kwargs)
        """ Widget code here """
        self.actual_widget = QtWidgets.QWidget(None)
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
        self._global_import_button = QtWidgets.QPushButton(QtGui.QIcon.fromTheme("insert-object"),"")
        self._global_import_button.clicked.connect(self.open_remote_importer)
        # hbox.addWidget(self.line_edit)
        #hbox.addStretch()
        hbox.addWidget(self._global_import_button)

        self.spinner.valueChanged.connect(self.value_changed)

        #print(self.actual_widget.minimumSize())

        #print(self.spinner.sizeHint())

        #self.spinner.setMinimumSize(self.spinner.sizeHint())
        #self.spinner.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        """ Widget code end """

    def set_disable(self, true_or_false):
        self.spinner.setDisabled(true_or_false)

    def set_parent(self, parent_view):
        super().set_parent(parent_view)
        self.actual_widget.setParent(self._qt_parent)

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):
        self.spinner.setValue(self.model.get_data())
        self.label.setText(self.model.name)
        if self.model.do_import:
            self.set_disable(True)
        super().init_from_model()

    def value_changed(self,value):
        self.model.set_data(value)

class WaNoItemBoolView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoItemBoolView, self).__init__(*args, **kwargs)
        """ Widget code here """
        self.actual_widget = QtWidgets.QWidget(None)
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

    def set_parent(self, parent_view):
        super().set_parent(parent_view)
        self.actual_widget.setParent(self._qt_parent)

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):

        self.checkbox.setChecked(self.model.get_data())
        self.label.setText(self.model.name)
        super().init_from_model()

    def state_changed(self):
        if self.checkbox.isChecked():
            self.model.set_data(True)
        else:
            self.model.set_data(False)


class WaNoScriptView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoScriptView,self).__init__(*args,**kwargs)
        """ Widget code here """
        self.actual_widget = QtWidgets.QWidget(None)
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

    def set_parent(self, parent_view):
        super().set_parent(parent_view)
        self.actual_widget.setParent(self._qt_parent)

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):
        text = self.model.get_as_text()
        self.textedit.setText(text)
        super().init_from_model()

    def on_save(self):
        self.model.save_text(self.textedit.toPlainText())



class WaNoItemStringView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoItemStringView, self).__init__(*args, **kwargs)
        """ Widget code here """
        self.actual_widget = QtWidgets.QWidget(None)
        vbox = QtWidgets.QHBoxLayout()
        self.lineedit = QtWidgets.QLineEdit()
        self.label = QtWidgets.QLabel("ABC")
        vbox.addWidget(self.label)
        vbox.addStretch()
        vbox.addWidget(self.lineedit)

        self._global_import_button = QtWidgets.QPushButton(QtGui.QIcon.fromTheme("insert-object"),"")
        self._global_import_button.clicked.connect(self.open_remote_importer)
        # hbox.addWidget(self.line_edit)
        #hbox.addStretch()
        vbox.addWidget(self._global_import_button)

        # vbox.addWidget(self.line_edit)
        self.actual_widget.setLayout(vbox)
        self.lineedit.editingFinished.connect(self.line_edited)
        """ Widget code end """

    def set_disable(self, true_or_false):
        self.lineedit.setDisabled(true_or_false)

    def set_parent(self, parent_view):
        super().set_parent(parent_view)
        self.actual_widget.setParent(self._qt_parent)

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):
        self.lineedit.setText(self.model.get_data())
        self.label.setText(self.model.name)
        if self.model.do_import:
            self.set_disable(True)
        super().init_from_model()

    def line_edited(self):
        self.model.set_data(self.lineedit.text())


class WanoQtViewRoot(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WanoQtViewRoot, self).__init__(*args, **kwargs)

    def set_parent(self, parent_view):
        if isinstance(parent_view, QtCore.QObject):
            self._qt_parent = parent_view
        else:
            super().set_parent(parent_view)
        self.init_to_scroller()

    def init_to_scroller(self):
        scroll = QtWidgets.QScrollArea(parent=self._qt_parent)
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
        me = QtWidgets.QWidget(parent=self._qt_parent)
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
        while self.vbox.count() > 0:
            self.vbox.removeItem(self.vbox.takeAt(0))

        from WaNo.view.WaNoViews import WaNoTabView
        for key, model in self.model.wano_dict.items():
            if isinstance(model.view,WaNoTabView):
                self.init_without_scroller()

            self.vbox.addWidget(model.view.get_widget())
        self.vbox.addStretch()
        #self.actual_widget.viewport().update()
        self.actual_widget.update()

class WaNoItemFileView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoItemFileView, self).__init__(*args, **kwargs)
        """ Widget code here """
        self.actual_widget = QtWidgets.QWidget(None)
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

    def set_parent(self, parent_view):
        super().set_parent(parent_view)

        self.actual_widget.setParent(self._qt_parent)

    def showLocalDialog(self):
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(self.actual_widget, 'Open file', QtCore.QDir.homePath())
        if fname:
            fname = QtCore.QDir.toNativeSeparators(fname)
            self.lineedit.setText(fname)
            self.model.set_local(True)
            self.line_edited()

    """
    def showWFDialog(self):
        wf = self.model.root_model.parent_wf
        importable_files = wf.assemble_files()
    """

    def load_wf_files(self):
        wf = self.model.get_root().get_parent_wf().get_root()
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
        super().init_from_model()

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
        self.actual_widget = QtWidgets.QWidget(None)

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

    def set_parent(self, parent_view):
        super().set_parent(parent_view)
        self.actual_widget.setParent(self._qt_parent)

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
        super().init_from_model()

    def get_widget(self):
        return self.actual_widget

class WaNoDropDownView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoDropDownView,self).__init__(*args,**kwargs)
        """ Widget code here """
        self.actual_widget = QtWidgets.QWidget(None)

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

    def set_parent(self, parent_view):
        super().set_parent(parent_view)
        self.actual_widget.setParent(self._qt_parent)

    def init_from_model(self):
        chosen_before = self.model.chosen
        self.combobox.clear()
        self.label.setText(self.model.name)
        for myid,entry in enumerate(self.model.choices):
            self.combobox.addItem(entry)
        self.combobox.setCurrentIndex(self.model.chosen)
        self.init = True
        self.model.set_chosen(chosen_before)
        super().init_from_model()

    def onButtonClicked(self, id):
        if self.init:
            self.model.set_chosen(id)

    def get_widget(self):
        return self.actual_widget


class WaNoChoiceView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoChoiceView,self).__init__(*args,**kwargs)
        """ Widget code here """
        self.actual_widget = QtWidgets.QGroupBox(None)
        self.bg = QtWidgets.QButtonGroup(None)
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

    def set_parent(self, parent_view):
        super().set_parent(parent_view)
        self.actual_widget.setParent(self._qt_parent)
        self.bg.setParent(self._qt_parent)

    def init_from_model(self):
        self.actual_widget.setTitle(self.model.name)
        for myid,entry in enumerate(self.model.choices):
            checkbox = QtWidgets.QRadioButton(entry,parent=self.actual_widget)
            self.buttons.append(checkbox)
            self.bg.addButton(checkbox,myid)
            self.vbox.addWidget(checkbox)
        #print(self.model.chosen)
        self.buttons[self.model.chosen].setChecked(True)
        super().init_from_model()

    def onButtonClicked(self, id):
        self.model.set_chosen(id)

    def get_widget(self):
        return self.actual_widget


class WaNoTabView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoTabView, self).__init__(*args, **kwargs)
        """ Widget code here """
        self.actual_widget = QtWidgets.QTabWidget(None)
        """" Widget code end """

    def set_parent(self, parent_view):
        super().set_parent(parent_view)
        self.actual_widget.setParent(self._qt_parent)


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
