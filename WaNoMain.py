import ctypes
import signal
import platform
import logging
import sys
import yaml
from PySide.QtGui import QApplication
from PySide.QtCore import QTimer
from os import path

from WaNo import WFEditorApplication
from WaNo import WaNoSettingsProvider

SETTINGS_FILE = "settings.yaml"

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


    settings = WaNoSettingsProvider(SETTINGS_FILE)
    if path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as infile:
            settings.load_from_dict(yaml.load(infile))
        settings._finish_parsing()
    else:
        # Default settings are already loaded, lets save them to file
        settings.dump_to_file(SETTINGS_FILE)
   
    editor = WFEditorApplication(settings)
#    editor.show()

    # This timer is required to let the python interpreter handle terminal
    # input from time to time. See: http://stackoverflow.com/a/4939113
    timer = QTimer()
    timer.start(500)  # You may change this if you wish.
    timer.timeout.connect(lambda: None)  # Let the interpreter run each 500 ms.

    sys.exit(app.exec_())
