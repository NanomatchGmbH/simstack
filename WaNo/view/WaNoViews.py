#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

from WaNo.view.AbstractWaNoView import AbstractWanoQTView
from PySide import QtGui


class WaNoBoxView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoBoxView, self).__init__(*args, **kwargs)
        self.actual_widget = QtGui.QWidget(self.qt_parent)
        self.vbox = QtGui.QVBoxLayout()
        self.actual_widget.setLayout(self.vbox)

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):
        for model in self.model.wano_list:
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
