#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

from WaNo.view.AbstractWaNoView import AbstractWanoQTView
from PySide import QtGui, QtCore

class GroupBoxWithButton(QtGui.QGroupBox):
    def __init__(self,*args,**kwargs):
        super(GroupBoxWithButton,self).__init__(*args,**kwargs)
        self.button = QtGui.QPushButton("ABC", parent=self)
        self.init_button()

    def init_button(self):
        width = self.size().width()
        #print(width)
        self.button.move(width - self.button.size().width()-10, -4)

    def resizeEvent(self, event):
        returnval = super(GroupBoxWithButton,self).resizeEvent(event)
        self.init_button()
        return returnval
        #r = self.rect()
        #s = event.size()
        #self.frame.setGeometry(r.x(), r.y(), s.width(), s.height())

class WaNoBoxView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoBoxView, self).__init__(*args, **kwargs)
        #self.actual_widget = QtGui.QWidget(self.qt_parent)
        #self.actual_widget = QtGui.QGroupBox(self.qt_parent)
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


        #self.actual_widget.setCheckable(True)
        self.vbox = QtGui.QVBoxLayout()
        self.actual_widget.setLayout(self.vbox)

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):
        self.actual_widget.setTitle(self.model.name)
        for model in self.model.wanos():
            self.vbox.addWidget(model.view.get_widget())


class WaNoItemFloatView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoItemFloatView, self).__init__(*args, **kwargs)
        """ Widget code here """
        self.actual_widget = QtGui.QWidget(self.qt_parent)
        vbox = QtGui.QHBoxLayout()
        self.spinner = QtGui.QDoubleSpinBox()
        # self.line_edit = QtGui.QLineEdit()
        self.spinner.setValue(0.0)
        self.label = QtGui.QLabel("ABC")
        vbox.addWidget(self.label)
        vbox.addWidget(self.spinner)
        # vbox.addWidget(self.line_edit)
        self.actual_widget.setLayout(vbox)
        """ Widget code end """

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):
        self.spinner.setValue(self.model.get_data())
        self.label.setText(self.model.name)

class WaNoItemBoolView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoItemBoolView, self).__init__(*args, **kwargs)
        """ Widget code here """
        self.actual_widget = QtGui.QWidget(self.qt_parent)
        vbox = QtGui.QHBoxLayout()
        self.checkbox = QtGui.QCheckBox()
        self.label = QtGui.QLabel("ABC")
        vbox.addWidget(self.label)
        vbox.addWidget(self.checkbox)
        # vbox.addWidget(self.line_edit)
        self.actual_widget.setLayout(vbox)
        """ Widget code end """

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):
        self.checkbox.setChecked(self.model.get_data())
        self.label.setText(self.model.name)

class WaNoItemStringView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoItemStringView, self).__init__(*args, **kwargs)
        """ Widget code here """
        self.actual_widget = QtGui.QWidget(self.qt_parent)
        vbox = QtGui.QHBoxLayout()
        self.lineedit = QtGui.QLineEdit()
        self.label = QtGui.QLabel("ABC")
        vbox.addWidget(self.label)
        vbox.addWidget(self.lineedit)
        # vbox.addWidget(self.line_edit)
        self.actual_widget.setLayout(vbox)
        """ Widget code end """

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):
        self.lineedit.setText(self.model.get_data())
        self.label.setText(self.model.name)

class WaNoItemListView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoItemListView, self).__init__(*args, **kwargs)

    def init_from_model(self):
        self.actual_widget = QtGui.QWidget(self.qt_parent)
        self.hbox = QtGui.QHBoxLayout()
        self.actual_widget.setLayout(self.hbox)


class WanoQtViewRoot(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WanoQtViewRoot, self).__init__(*args, **kwargs)
        self.actual_widget = QtGui.QWidget()
        self.vbox = QtGui.QVBoxLayout()
        self.actual_widget.setLayout(self.vbox)

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):
        for key, model in self.model.wano_dict.items():
            self.vbox.addWidget(model.view.get_widget())

class WaNoItemFileView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoItemFileView, self).__init__(*args, **kwargs)
        """ Widget code here """
        self.actual_widget = QtGui.QWidget(self.qt_parent)
        vbox = QtGui.QHBoxLayout()
        self.lineedit = QtGui.QLineEdit()
        self.label = QtGui.QLabel("ABC")
        self.openfilebutton = QtGui.QPushButton("File",self.actual_widget)
        self.openwfbutton = QtGui.QPushButton("Workflow",self.actual_widget)
        vbox.addWidget(self.label)
        vbox.addWidget(self.lineedit)
        vbox.addWidget(self.openfilebutton)
        vbox.addWidget(self.openwfbutton)
        self.openfilebutton.clicked.connect(self.showLocalDialog)
        self.actual_widget.setLayout(vbox)
        """ Widget code end """

    def showLocalDialog(self):
        fname, success = QtGui.QFileDialog.getOpenFileName(self.actual_widget, 'Open file', QtCore.QDir.homePath())
        import pprint
        pprint.pprint(success)

        if success:
            self.lineedit.setText(fname)

    def showWFDialog(self):
        pass

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):
        self.lineedit.setText(self.model.get_data())
        self.label.setText(self.model.name)


#Still need to code enable if and
# Multiple Of
# and Choice