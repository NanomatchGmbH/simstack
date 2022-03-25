import sys
from Qt import QtGui, QtWidgets



from SimStackServer.WorkflowModel import Resources
from functools import partial
import numpy as np

from WaNo.view.HorizontalTextEditWithFileImport import HorizontalTextEditWithFileImport
from WaNo.view.QHVLine import QHLine


class ResourcesView(QtWidgets.QWidget):
    _field_name_to_display_name = {
        "base_URI": "Hostname"
    }
    _field_name_to_intention = {
        "extra_config": "file",
        "ssh_private_key" : "file",
        "queueing_system": "queueing_system"
    }
    render_order = [


    ]
    def __init__(self, resources):
        super().__init__()
        self._resources = resources
        self.initUI()

    @classmethod
    def field_name_to_display_name(cls, field_name: str) -> str:
        return cls._field_name_to_display_name.get(field_name,field_name)

    def field_name_to_intention(self, field_name: str) -> str:
        if field_name in self._field_name_to_intention:
            return self._field_name_to_intention[field_name]

        mytype = self._resources.field_type(field_name)
        if mytype in [int, np.uint64]:
            return "int"
        elif mytype == str:
            return "str"

    def _get_queue_dropdown_widget(self):
        qs = QtWidgets.QComboBox(self)
        qs.addItem("pbs")
        qs.addItem("slurm")
        qs.addItem("lsf")
        qs.addItem("sge_smp")
        qs.addItem("AiiDA")
        qs.addItem("Internal")
        return qs

    def initUI(self):
        #self.setGeometry(300, 300, 400, 800)
        self.setWindowTitle('Resource view')
        self.renderJobResources()
        #self.setWindowIcon(QtGui.QIcon('web.png'))

    @staticmethod
    def _fieldChanger(fieldname: str, model: Resources, newvalue):
        """

        :param fieldname:
        :param newvalue:
        :return:
        """

        # adapt value below
        print(fieldname, newvalue)
        model.set_field_value(fieldname, newvalue)

    def renderJobResources(self, exclude_items = None):
        """
        Shows only job specific resouces -> things like sw dir not to be modified
        :return:
        """
        if exclude_items is None:
            exclude_items = {}

        minHeight = 20
        current_flo = QtWidgets.QFormLayout()
        current_flo.addRow(QtWidgets.QLabel("<b>Host Settings</b>"), QtWidgets.QWidget())

        for this_key in self._resources.render_order():
            field_name = self.field_name_to_display_name(this_key)
            #if not this_key in ["walltime", "cpu_per_node", "nodes", "queue", "memory", "custom_requests"]:
            #    continue
            if this_key == "nodes":
                #vbox.addLayout(flo1)
                current_flo.addRow(QtWidgets.QLabel("<b>Default Resources</b>"), QtWidgets.QWidget())
                #vbox.addWidget(qhl)
                #current_flo = flo2
            this_value = self._resources.get_field_value(this_key)
            intention = self.field_name_to_intention(this_key)
            myfunc = partial(self._fieldChanger, this_key, self._resources)
            if intention == "int":
                this_i = QtWidgets.QSpinBox()
                this_i.valueChanged.connect(myfunc)
                this_i.setMinimum(0)
                this_i.setMaximum(100000)
                this_i.setValue(this_value)
                current_flo.addRow(field_name, this_i)
            elif intention =="file":
                this_i = HorizontalTextEditWithFileImport()
                this_i.line_edit.setText(this_value)
                this_i.line_edit.textChanged.connect(myfunc)
                current_flo.addRow(field_name, this_i)
            elif intention =="str":
                this_i = QtWidgets.QLineEdit()
                this_i.setText(this_value)
                this_i.textChanged.connect(myfunc)
                current_flo.addRow(field_name, this_i)
            elif intention == "queueing_system":
                this_i = self._get_queue_dropdown_widget()
                this_i.setCurrentText(this_value)
                this_i.currentTextChanged.connect(myfunc)
                current_flo.addRow(field_name, this_i)

        for i in range(0, current_flo.rowCount()):
            itemAt = current_flo.itemAt(i, QtWidgets.QFormLayout.FieldRole).widget()
            itemAt.setMinimumHeight(minHeight)


        self.setLayout(current_flo)
