#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import sys
from PySide import QtGui, QtCore
from WaNo.model.WaNoModels import WaNoModelRoot
from WaNo.view.WaNoViews import WanoQtViewRoot
from WaNo.WaNoFactory import WaNoFactory

import yaml

class Example(QtGui.QWidget):
    def __init__(self):
        super(Example, self).__init__()

        self.initUI()

    def initUI(self):

        wifv = WanoQtViewRoot(qt_parent=None)
        wifm = WaNoModelRoot.construct_from_wano("DFT.xml", rootview=wifv)
        self.wifm = wifm
        wifm.set_view(wifv)
        wifv.set_model(wifm)
        wifm.construct_children()
        WaNoFactory.build_views()
        wifv.init_from_model()

        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(wifv.get_widget())

        vbox = QtGui.QVBoxLayout()
        vbox.addStretch(1)
        vbox.addLayout(hbox)

        self.setLayout(vbox)

        self.setGeometry(300, 300, 300, 150)
        self.setWindowTitle('Buttons')
        self.show()


def main():
    app = QtGui.QApplication(sys.argv)
    ex = Example()

    app.exec_()
    ex.wifm.update_xml()
    ex.wifm.save_xml("Newdft.xml")
    print(yaml.dump(ex.wifm))
    sys.exit(0)


if __name__ == '__main__':
    main()
