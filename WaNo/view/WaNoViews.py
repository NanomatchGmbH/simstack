#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

from WaNo.view.MultiselectDropDownList import MultiselectDropDownList
from WaNo.view.AbstractWaNoView import AbstractWanoQTView, AbstractWanoView
from PySide import QtGui, QtCore

class GroupBoxWithButton(QtGui.QGroupBox):
    def __init__(self,*args,**kwargs):
        super(GroupBoxWithButton,self).__init__(*args,**kwargs)
        self.add_button = QtGui.QPushButton("", parent=self)
        self.add_button.setIcon(QtGui.QIcon.fromTheme("list-add"))
        #self.add_button.setFlat(True)
        self.remove_button = QtGui.QPushButton("", parent=self)
        self.remove_button.setIcon(QtGui.QIcon.fromTheme("list-remove"))
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
        self.vbox = QtGui.QVBoxLayout()
        self.actual_widget.setLayout(self.vbox)
        add,rem = self.actual_widget.get_button_objects()
        add.clicked.connect(self.add_button_clicked)
        rem.clicked.connect(self.remove_button_clicked)


    def add_button_clicked(self):
        self.model.add_item()
        line = QtGui.QFrame(self.actual_widget)
        line.setFrameShape(QtGui.QFrame.HLine)
        line.setFrameShadow(QtGui.QFrame.Sunken)
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
            line = QtGui.QFrame(self.actual_widget)
            line.setFrameShape(QtGui.QFrame.HLine)
            line.setFrameShadow(QtGui.QFrame.Sunken)
            self.vbox.addWidget(line)
        line.deleteLater()

class EmptyView(AbstractWanoView):
    def __init__(self,*args,**kwargs):
        super(EmptyView,self).__init__(*args,**kwargs)

class WaNoGroupView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoGroupView, self).__init__(*args, **kwargs)
        self.actual_widget = QtGui.QWidget(self.qt_parent)
        self.vbox = QtGui.QVBoxLayout()
        self.actual_widget.setLayout(self.vbox)

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):
        for model in self.model.wanos():
            self.vbox.addWidget(model.view.get_widget())

class WaNoBoxView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoBoxView, self).__init__(*args, **kwargs)
        #self.actual_widget = QtGui.QWidget(self.qt_parent)
        self.actual_widget = QtGui.QGroupBox(parent=self.qt_parent)
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
        #self.actual_widget.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
        self.vbox = QtGui.QVBoxLayout()
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
        self.actual_widget = QtGui.QWidget(self.qt_parent)
        hbox = QtGui.QHBoxLayout()
        self.actual_widget.setLayout(hbox)
        self.spinner = QtGui.QSpinBox()
        # self.line_edit = QtGui.QLineEdit()
        self.spinner.setValue(0)
        self.spinner.setMaximum(1000000000)
        self.spinner.setMinimum(-1000000000)
        self.label = QtGui.QLabel("ABC")
        hbox.addWidget(self.label)
        hbox.addStretch()
        hbox.addWidget(self.spinner)
        #self.actual_widget.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        #self.actual_widget.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
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
        self.actual_widget = QtGui.QWidget(self.qt_parent)
        hbox = QtGui.QHBoxLayout()
        self.actual_widget.setLayout(hbox)
        self.spinner = QtGui.QDoubleSpinBox()
        # self.line_edit = QtGui.QLineEdit()
        self.spinner.setValue(0.0)
        self.spinner.setMaximum(10000000000)
        self.spinner.setMinimum(-10000000000)
        self.spinner.setDecimals(5)
        self.spinner.setSingleStep(1.0)
        #self.actual_widget.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        #self.actual_widget.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        self.label = QtGui.QLabel("ABC")
        #self.label.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed
        #self.label.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
        hbox.addWidget(self.label)
        hbox.addStretch()
        hbox.addWidget(self.spinner)
        # hbox.addWidget(self.line_edit)

        self.spinner.valueChanged.connect(self.value_changed)

        #print(self.actual_widget.minimumSize())

        #print(self.spinner.sizeHint())

        #self.spinner.setMinimumSize(self.spinner.sizeHint())
        #self.spinner.setSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Minimum)
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
        self.actual_widget = QtGui.QWidget(self.qt_parent)
        hbox = QtGui.QHBoxLayout()
        self.actual_widget.setLayout(hbox)
        self.checkbox = QtGui.QCheckBox()
        self.label = QtGui.QLabel("ABC")
        hbox.addWidget(self.label)
        hbox.addStretch()
        hbox.addWidget(self.checkbox)
        # hbox.addWidget(self.line_edit)

        #self.actual_widget.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

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
        print("HERE")
        """ Widget code here """
        self.actual_widget = QtGui.QWidget(self.qt_parent)
        vbox = QtGui.QVBoxLayout()
        self.actual_widget.setLayout(vbox)
        self.menubar = QtGui.QWidget()
        hbox = QtGui.QHBoxLayout()
        self.menubar.setLayout(hbox)
        self.combobox = QtGui.QComboBox()
        self.combobox.addItem("Python")
        self.combobox.addItem("Bash")
        self.combobox.addItem("Perl")
        self.savebutton = QtGui.QPushButton(QtGui.QIcon.fromTheme("document-save"),"")
        self.savebutton.clicked.connect(self.on_save)
        hbox.addWidget(self.savebutton)
        hbox.addStretch()
        hbox.addWidget(self.combobox)

        vbox.addWidget(self.menubar)
        self.textedit = QtGui.QTextEdit()
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
        self.actual_widget = QtGui.QWidget(self.qt_parent)
        vbox = QtGui.QHBoxLayout()
        self.lineedit = QtGui.QLineEdit()
        self.label = QtGui.QLabel("ABC")
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
        scroll = QtGui.QScrollArea(parent=self.qt_parent)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll.setWidgetResizable(True)
        me = QtGui.QWidget(parent=scroll)
        scroll.setWidget(me)
        # scroll.resize(460,700)
        self.actual_widget = scroll
        self.vbox = QtGui.QVBoxLayout()
        # me.setMinimumSize(QtCore.QSize(900, 900))
        me.setLayout(self.vbox)

    def init_without_scroller(self):
        me = QtGui.QWidget(parent=self.qt_parent)
        self.vbox = QtGui.QVBoxLayout()
        me.setLayout(self.vbox)
        self.actual_widget = me

    def get_widget(self):
        return self.actual_widget

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
        self.actual_widget = QtGui.QWidget(self.qt_parent)
        hbox = QtGui.QHBoxLayout()
        self.lineedit = QtGui.QLineEdit(parent=self.actual_widget)
        self.label = QtGui.QLabel("ABC",parent=self.actual_widget)
        self.openfilebutton = QtGui.QPushButton("",parent=self.actual_widget)

        self.openfilebutton.setIcon(QtGui.QFileIconProvider().icon(QtGui.QFileIconProvider.File))

        """
        self.openwfbutton = QtGui.QPushButton("",parent=self.actual_widget)
        self.openwfbutton.clicked.connect(self.showWFDialog)
        """
        #begin change
        self.openwfbutton = MultiselectDropDownList(self, autoset_text=False)
        self.openwfbutton.setIcon(QtGui.QFileIconProvider().icon(QtGui.QFileIconProvider.Network))
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

        #self.actual_widget.setSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        """ Widget code end """

    def showLocalDialog(self):
        fname, success = QtGui.QFileDialog.getOpenFileName(self.actual_widget, 'Open file', QtCore.QDir.homePath())
        self.lineedit.setText(fname)
        self.line_edited()

    """
    def showWFDialog(self):
        wf = self.model.root_model.parent_wf
        importable_files = wf.assemble_files()
    """

    def load_wf_files(self):
        wf = self.model.root_model.parent_wf
        importable_files = wf.assemble_files("")
        self.openwfbutton.set_items(importable_files)
        self.model.set_local(False)

    def on_wf_file_change(self):
        self.lineedit.setText(" ".join(self.openwfbutton.get_selection()))
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


class WaNoChoiceView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoChoiceView,self).__init__(*args,**kwargs)
        """ Widget code here """
        self.actual_widget = QtGui.QGroupBox(self.qt_parent)
        self.bg = QtGui.QButtonGroup(self.qt_parent)
        self.vbox = QtGui.QVBoxLayout(self.actual_widget)
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
        ##self.actual_widget.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        """" Widget code end """

    def init_from_model(self):
        self.actual_widget.setTitle(self.model.name)
        for myid,entry in enumerate(self.model.choices):
            checkbox = QtGui.QRadioButton(entry,parent=self.actual_widget)
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
        self.actual_widget = QtGui.QTabWidget(self.qt_parent)
        """" Widget code end """

    def init_from_model(self):

        for key, model in self.model.items():
            scroll = QtGui.QScrollArea(parent=self.actual_widget)
            scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
            scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
            scroll.setWidgetResizable(True)
            scroll.setWidget(model.view.get_widget())
            self.actual_widget.addTab(scroll,model.name)


    def get_widget(self):
        return self.actual_widget
