from Qt import QtCore, QtWidgets

class RemoteImporterDialog(QtWidgets.QDialog):
    def __init__(self, *args, **kwargs):
        importlist = kwargs["importlist"]
        varname = kwargs["varname"]
        del kwargs["varname"]
        del kwargs["importlist"]
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Import Workflow Variable")
        self._mylayout = QtWidgets.QGridLayout(self)
        self._heading = QtWidgets.QLabel("ABC")
        self._varname = QtWidgets.QLabel("ABC")

        label = QtWidgets.QLabel(varname)
        self._mylineedit = QtWidgets.QLineEdit()

        self._completer = QtWidgets.QCompleter(importlist)
        self._completer.setCompletionMode(QtWidgets.QCompleter.UnfilteredPopupCompletion)
        self._completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self._mylineedit.setCompleter(self._completer)
        self._mylayout.addWidget(label, 0, 0)
        self._mylayout.addWidget(self._mylineedit, 1,0)
        self._buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok |QtWidgets.QDialogButtonBox.Cancel)
        self._mylayout.addWidget(self._buttonBox,2,0)
        self._buttonBox.accepted.connect(self.accept)
        self._buttonBox.rejected.connect(self.reject)
        self.setMinimumWidth(800)
        self.setMinimumHeight(120)

    def getchoice(self):
        return self._mylineedit.text()