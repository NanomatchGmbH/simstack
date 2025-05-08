#!/usr/bin/env python3

from os import path
import os
import sys

from os.path import join

from simstack.SimStackPaths import SimStackPaths

import ctypes
import signal
import platform
import logging
import uuid

import yaml


from PySide6.QtWidgets import QApplication, QStyleFactory
from PySide6.QtCore import QTimer, QLocale
import PySide6.QtCore as QtCore
import traceback


from simstack.WFEditorApplication import WFEditorApplication
from simstack.WaNoSettingsProvider import WaNoSettingsProvider


editor = None


def signal_handler(*args):
    global editor
    if editor is not None:
        editor.exit()


def override_locale():
    QLocale.setDefault(QLocale(QLocale.English, QLocale.UnitedStates))


def main():
    signal.signal(signal.SIGINT, signal_handler)

    override_locale()
    myappid = "Nanomatch.WorkFlowEditor.Developer.V10"  # arbitrary string

    if platform.system() == "Windows":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_ShareOpenGLContexts)

    app = QApplication(sys.argv)
    if platform.system() == "Darwin":
        # OSX QT bug here, if we don't force the style to Fusion, things like the resource table won't work.
        app.setStyle(QStyleFactory.create("Fusion"))
    tempfile = join(SimStackPaths.get_temp_folder(), "%s-wfeditor.log" % uuid.uuid4())
    logging.basicConfig(filename=tempfile, filemode="w", level=logging.INFO)

    SETTINGS_FOLDER = SimStackPaths.get_settings_folder_nanomatch()

    if not path.isdir(SETTINGS_FOLDER):
        os.makedirs(SETTINGS_FOLDER)
    SimStackPaths.gen_empty_local_hostfile_if_not_present()

    SETTINGS_FILE = SimStackPaths.get_settings_file()
    print("Loading settings from %s" % SETTINGS_FILE)
    settings = WaNoSettingsProvider.get_instance(SETTINGS_FILE)
    if path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as infile:
            settings.load_from_dict(yaml.safe_load(infile))
        settings._finish_parsing()
    else:
        # Default settings are already loaded, lets save them to file
        settings.dump_to_file(SETTINGS_FILE)

    global editor
    editor = WFEditorApplication(settings)

    # This timer is required to let the python interpreter handle terminal
    # input from time to time. See: http://stackoverflow.com/a/4939113
    timer = QTimer()
    timer.start(500)  # You may change this if you wish.
    timer.timeout.connect(lambda: None)  # Let the interpreter run each 500 ms.
    try:
        exitcode = app.exec_()
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        with open(tempfile, "a") as out:
            out.write(
                "The client has crashed. Please send the following traceback to Nanomatch:\n"
            )
            traceback.print_tb(exc_traceback, limit=None, file=out)
            out.write(str(e) + "\n")
    if app is not None:
        del app

    sys.exit(exitcode)


if __name__ == "__main__":
    main()
