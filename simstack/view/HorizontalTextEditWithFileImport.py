from PySide6 import QtGui, QtWidgets, QtCore

class HorizontalTextEditWithFileImport(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self._initUI()
        self._last_opened_dir = QtCore.QDir.homePath()
        self._connect_signals()

    def _initUI(self):
        self._layout = QtWidgets.QHBoxLayout()
        self._textedit = QtWidgets.QLineEdit()
        self._openfilebrowser_button = QtWidgets.QPushButton("")
        self._openfilebrowser_button.setIcon(QtWidgets.QFileIconProvider().icon(QtWidgets.QFileIconProvider.File))
        self._layout.addWidget(self._textedit)
        self._layout.addWidget(self._openfilebrowser_button)
        self._layout.setContentsMargins(0,0,0,0)
        self.setLayout(self._layout)

    def _connect_signals(self):
        self._openfilebrowser_button.clicked.connect(self.show_file_dialog)

    @property
    def line_edit(self):
        return self._textedit

    @property
    def button(self):
        return self._openfilebrowser_button

    def show_file_dialog(self):
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open file', self._last_opened_dir)
        if fname:
            fname = QtCore.QDir.toNativeSeparators(fname)
            self._textedit.setText(fname)