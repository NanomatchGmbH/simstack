#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import sys,os

if __name__ == '__main__':
    #In case pyura is hosted in the external directory, we append the path on our own
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = os.path.join(dir_path,"external")

    if not dir_path in sys.path:
        sys.path.append(dir_path)

from PySide import QtGui, QtCore
from WaNo.model.WaNoModels import WaNoModelRoot
from WaNo.view.WaNoViews import WanoQtViewRoot
from WaNo.WaNoFactory import WaNoFactory

class Example(QtGui.QWidget):
    def __init__(self,wanofile):
        super(Example, self).__init__()
        self.wanofile = wanofile
        self.initUI()

    def initUI(self):
        scroller = QtGui.QScrollArea(parent=self)
        scroller.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
        scroller.setWidgetResizable(True)
        container_widget = QtGui.QWidget(parent=scroller)
        container_widget.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)
        self.setSizePolicy(QtGui.QSizePolicy.Expanding,QtGui.QSizePolicy.Expanding)

        container_layout = QtGui.QVBoxLayout()

        wifv = WanoQtViewRoot(qt_parent=container_widget)
        wifm = WaNoModelRoot.construct_from_wano(self.wanofile, rootview=wifv, parent_wf = None)
        self.wifm = wifm
        wifm.set_view(wifv)
        wifv.set_model(wifm)
        wifm.construct_children()
        WaNoFactory.build_views()
        wifv.init_from_model()

        container_layout.addWidget(wifv.get_widget())
        submit_push = QtGui.QPushButton("Submit", parent=container_widget)
        submit_push.clicked.connect(self.render_slot)
        container_layout.addWidget(submit_push)
        container_widget.setLayout(container_layout)
        scroller.setWidget(container_widget)
        #scroller.setSizePolicy()
        vbox = QtGui.QVBoxLayout()
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
            a = QtGui.QMessageBox.critical(None, 'Error!', "Error during rendering, error was: %s" %e, QtGui.QMessageBox.Abort)

def main():
    app = QtGui.QApplication(sys.argv)
    wanofile = sys.argv[1]
    ex = Example(wanofile)
    app.exec_()
    ex.wifm.update_xml()
    outfile = "%s_edited.xml"%wanofile.split('.')[0]
    ex.wifm.save_xml(outfile)
    sys.exit(0)


if __name__ == '__main__':
    main()
