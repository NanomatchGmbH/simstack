from PySide6.QtWidgets import QPlainTextEdit
import logging


class LogTab(QPlainTextEdit):
    def __init__(self, parent=None):
        super(LogTab, self).__init__(parent)
        self.parent = parent
        self.logger = logging.getLogger("WFELOG")
        handler = logging.StreamHandler(self)
        logging.basicConfig(stream=self)
        self.logger.addHandler(handler)
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        self.setReadOnly(True)

    def copyContent(self):
        pass

    def write(self, message):
        if message == "\n":
            return
        message.replace("\n", "")
        # print ("<%s>"%message)
        self.appendPlainText(message)
        self.ensureCursorVisible()
