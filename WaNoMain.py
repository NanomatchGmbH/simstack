#!/usr/bin/env python

from os import path
import os
import sys

if __name__ == '__main__':
    #In case pyura is hosted in the external directory, we append the path on our own
    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = path.join(dir_path,"external")

    if not dir_path in sys.path:
        sys.path.append(dir_path)

import ctypes
import signal
import platform
import logging

import yaml
from PySide.QtGui import QApplication,QDesktopServices
from PySide.QtCore import QTimer


from WaNo import WFEditorApplication
from WaNo import WaNoSettingsProvider

_SETTINGS_DIR="NanoMatch"
_SETTINGS_FILE="clientsettings.yml"

editor = None

def signal_handler(*args):
    global editor
    if not editor is None:
        editor.exit()


if __name__ == '__main__':   
    signal.signal(signal.SIGINT, signal_handler)

    myappid = 'Nanomatch.WorkFlowEditor.Developer.V10' # arbitrary string

    if platform.system() == 'Windows':
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        
    app = QApplication(sys.argv)
    logging.basicConfig(filename='wfeditor.log',filemode='w',level=logging.INFO)
    logger = logging.getLogger('WFELOG')

    SETTINGS_FOLDER = QDesktopServices.storageLocation(QDesktopServices.DataLocation)
    SETTINGS_FOLDER = path.dirname(SETTINGS_FOLDER)
    SETTINGS_FOLDER = path.join(SETTINGS_FOLDER,_SETTINGS_DIR)

    if not path.isdir(SETTINGS_FOLDER):
        os.makedirs(SETTINGS_FOLDER)
    SETTINGS_FILE = path.join(SETTINGS_FOLDER,_SETTINGS_FILE)
    print(SETTINGS_FILE)
    settings = WaNoSettingsProvider.get_instance(SETTINGS_FILE)
    if path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as infile:
            settings.load_from_dict(yaml.safe_load(infile))
        settings._finish_parsing()
    else:
        # Default settings are already loaded, lets save them to file
        settings.dump_to_file(SETTINGS_FILE)
   
    editor = WFEditorApplication(settings)

    # This timer is required to let the python interpreter handle terminal
    # input from time to time. See: http://stackoverflow.com/a/4939113
    timer = QTimer()
    timer.start(500)  # You may change this if you wish.
    timer.timeout.connect(lambda: None)  # Let the interpreter run each 500 ms.

    sys.exit(app.exec_())
