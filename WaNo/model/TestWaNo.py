#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import os

from Qt import QtWidgets
from SimStackServer.WaNo.WaNoModels import WaNoModelRoot
from WaNo.view.WaNoViews import WanoQtViewRoot
from SimStackServer.WaNo.WaNoFactory import WaNoFactory
from WaNo.WFEditorApplication import WFEditorApplication as wea

class TestWaNo(QtWidgets.QWidget):
    def __init__(self,wanofile):
        super(TestWaNo, self).__init__()
        self.wanofile = wanofile
        self.initUI()
        wea.license_check()

    def initUI(self):
        raise NotImplementedError("Not implemented anymore")
        scroller = QtWidgets.QScrollArea(parent=self)
        scroller.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        scroller.setWidgetResizable(True)
        container_widget = QtWidgets.QWidget(parent=scroller)
        container_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)

        container_layout = QtWidgets.QVBoxLayout()

        wifv = WanoQtViewRoot(qt_parent=container_widget)
        wifm = WaNoModelRoot.construct_from_wano(self.wanofile, rootview=wifv, parent_wf = None)
        self.wifm = wifm
        wifm.set_view(wifv)
        wifv.set_model(wifm)
        wifm.construct_children()
        WaNoFactory.build_views()
        wifv.init_from_model()

        container_layout.addWidget(wifv.get_widget())
        submit_push = QtWidgets.QPushButton("Submit", parent=container_widget)
        submit_push.clicked.connect(self.render_slot)
        container_layout.addWidget(submit_push)
        container_widget.setLayout(container_layout)
        scroller.setWidget(container_widget)
        #scroller.setSizePolicy()
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(scroller)

        #vbox.addStretch(1)
        self.setLayout(vbox)
        self.setGeometry(300, 300, 460, 700)
        self.setWindowTitle('WaNoTest')
        self.show()

    def render_slot(self):
        try:
            try:
                os.makedirs("Submitted")
            except OSError as e:
                pass
            return self.wifm.render_and_write_input_files("Submitted")
        except Exception as e:
            a = QtWidgets.QMessageBox.critical(None, 'Error!', "Error during rendering, error was: %s" %e, QtWidgets.QMessageBox.Abort)

