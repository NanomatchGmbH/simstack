#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys,os

if __name__ == '__main__':
    #In case pyura is hosted in the external directory, we append the path on our own
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = os.path.join(dir_path,"external")

    if not dir_path in sys.path:
        sys.path.append(dir_path)

from Qt import QtGui, QtCore, QtWidgets
from simstack.model.TestWaNo import TestWaNo

def main():
    app = QtWidgets.QApplication(sys.argv)
    wanofile = sys.argv[1]
    ex = TestWaNo(wanofile)
    app.exec_()
    ex.wifm.update_xml()
    outfile = "%s_edited.xml"%wanofile.split('.')[0]
    ex.wifm.save_xml(outfile)
    sys.exit(0)

if __name__ == '__main__':
    main()
