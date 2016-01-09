from PySide.QtGui import QPlainTextEdit
import logging

class LogTab(QPlainTextEdit):
    def __init__(self, parent = None):
        super(LogTab, self).__init__(parent)
        self.parent = parent
        self.logger = logging.getLogger('WFELOG')
        handler = logging.StreamHandler(self)
        logging.basicConfig(stream=self)
        self.logger.addHandler(handler)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s','%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        self.setReadOnly(True)

    def copyContent(self):
        pass

    def write(self,message):
        if message == '\n':
            return
        message.replace("\n","")
        #print ("<%s>"%message)
        self.appendPlainText(message)
        self.ensureCursorVisible()

"""
class LogTab(QtGui.QTextBrowser):
    def __init__(self, parent = None):
        super(LogTab, self).__init__(parent)
        self.logger = logging.getLogger('WFELOG')
        handler = logging.StreamHandler(self)
        logging.basicConfig(stream=self)
        self.logger.addHandler(handler)        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s','%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        self.logger.info("Logging Tab Enabled Version: " + get_git_revision_short_hash())
    
    def copyContent(self):
        pass  
   
    def write(self,message):
        #self.append('<span>'+message+'</span>')
        #print (message)
        message.replace("\n","")
        print(message)
        self.append(message)
        #for m in message:
            #self.append('<span>' + m + '<span>')
        #c = self.textCursor()
        #c.setPosition(QtGui.QTextCursor.End)
        #self.setTextCursor(c)
        #s = self.verticalScrollBar()
        #s.setValue(s.maximum)
        self.ensureCursorVisible()
"""
        
        
