import ctypes
import platform
import logging
import sys
from PySide.QtGui import QApplication

from WaNo import WFEditorApplication

if __name__ == '__main__':   
    myappid = 'Nanomatch.WorkFlowEditor.Developer.V10' # arbitrary string

    if platform.system() == 'Windows':
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        
    app = QApplication(sys.argv)
    logging.basicConfig(filename='wfeditor.log',filemode='w',level=logging.INFO)
    logger = logging.getLogger('WFELOG')
   
    editor = WFEditorApplication()
    editor.show()
    app.exec_()
