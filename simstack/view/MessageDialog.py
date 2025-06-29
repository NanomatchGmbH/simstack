from PySide6.QtWidgets import QMessageBox
from enum import Enum


class MessageDialog(QMessageBox):
    class MESSAGE_TYPES(Enum):
        critical = 0
        error = 1
        warning = 2
        info = 3

    _window_titles = ["Critical Error", "Error", "Warning", "Info"]
    _icons = [
        QMessageBox.Critical,
        QMessageBox.Critical,
        QMessageBox.Warning,
        QMessageBox.Information,
    ]

    def __init__(self, msg_type, msg, direct_show=True, parent=None, details=None):
        super().__init__(parent)

        self.setWindowTitle(self._window_titles[msg_type.value])
        self.setText(msg)
        self.setIcon(self._icons[msg_type.value])
        if details is not None and details != "":
            self.setDetailedText(details)

        if direct_show:
            self.exec_()
