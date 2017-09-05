from Qt.QtWidgets import QMessageBox
from enum import Enum

class MessageDialog(QMessageBox):
    class MESSAGE_TYPES(Enum):
        critical = 0
        error = 1
        warning = 2
        info = 3

    _window_titles = ["Critical Error", "Error", "Warning", "Info"]
    _icons = [QMessageBox.Critical, QMessageBox.Critical, QMessageBox.Warning,
            QMessageBox.Information
        ]

    def __init__(self, msg_type, msg, direct_show=True, parent=None, details=None):
        super(MessageDialog, self).__init__(parent)

        self.setWindowTitle(self._window_titles[msg_type.value])
        self.setText(msg)
        self.setIcon(self._icons[msg_type.value])
        if not details is None and details != "":
            self.setDetailedText(details)

        if direct_show:
            self.exec_()

if __name__ == "__main__":
    from PySide.QtGui import QApplication
    import sys
    qapp = QApplication(sys.argv)

    MessageDialog(MessageDialog.MESSAGE_TYPES.warning, "Ich bin ein Text", True)

    sys.exit(qapp.exec_())
