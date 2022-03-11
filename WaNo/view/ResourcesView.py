import sys
from Qt import QtGui, QtWidgets

from SimStackServer.WorkflowModel import Resources
from functools import partial
import numpy as np


class ResourcesView(QtWidgets.QWidget):
    def __init__(self, resources):
        super().__init__()
        self._resources = resources
        self.initUI()

    def initUI(self):
        self.setGeometry(300, 300, 400, 800)
        self.setWindowTitle('Resource view')
        #self.setWindowIcon(QtGui.QIcon('web.png'))

    def renderAll(self):
        flo = QtWidgets.QFormLayout()
        for field in self._resources.fields():
            this_key = field[0]
            this_value = field[2]
            if isinstance(this_value, int):
                this_i = QtWidgets.QSpinBox()
                this_i.setMinimum(0)
                this_i.setMaximum(100000)
                this_i.setValue(this_value)
                flo.addRow(this_key, this_i)
            elif isinstance(this_value, str):
                this_s = QtWidgets.QLineEdit()
                this_s.setText(this_value)
                flo.addRow(this_key, this_s)
        self.setLayout(flo)

    @staticmethod
    def _fieldChanger(fieldname: str, model: Resources, newvalue):
        """

        :param fieldname:
        :param newvalue:
        :return:
        """

        # adapt value below
        model.set_field_value(fieldname, newvalue)

    def renderJobResources(self):
        """
        Shows only job specific resouces -> things like sw dir not to be modified
        :return:
        """
        flo = QtWidgets.QFormLayout()
        for field in self._resources.fields():
            this_key = field[0]
            if not this_key in ["walltime", "cpu_per_node", "nodes", "queue", "memory", "custom_requests"]:
                continue
            this_value = self._resources.get_field_value(this_key)
            myfunc = partial(self._fieldChanger, field[0], self._resources)
            if isinstance(this_value, int) or isinstance(this_value, np.uint64):
                this_i = QtWidgets.QSpinBox()
                this_i.valueChanged.connect(myfunc)
                this_i.setMinimum(0)
                this_i.setMaximum(100000)
                this_i.setValue(this_value)
                flo.addRow(this_key, this_i)
            elif isinstance(this_value, str):
                this_i = QtWidgets.QLineEdit()
                this_i.setText(this_value)
                #this_i.editingFinished.connect(myfunc)
                this_i.textChanged.connect(myfunc)
                flo.addRow(this_key, this_i)
        self.setLayout(flo)
