import ctypes
import platform
import logging
import sys
import yaml
from PySide.QtGui import QApplication
from os import path

from WaNo import WFEditorApplication
from WaNo import WaNoSettingsProvider

SETTINGS_FILE = "settings.yaml"

if __name__ == '__main__':   
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
    editor.show()
    app.exec_()
