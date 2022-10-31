import copy
import sys
from Qt import QtGui, QtWidgets, QtCore

from SimStackServer.WorkflowModel import Resources
from functools import partial
import numpy as np

from simstack.lib.QtClusterSettingsProvider import QtClusterSettingsProvider
from simstack.view.HorizontalTextEditWithFileImport import HorizontalTextEditWithFileImport
from simstack.view.QHVLine import QHLine
from simstack.view.WaNoRegistrySelection import WaNoRegistrySelection


class ResourcesView(QtWidgets.QWidget):
    _field_name_to_display_name = {
        "base_URI": "Hostname",
        "resource_name": "Resource",
        "port": "Port",
        "queueing_system": "Queueing System",
        "username": "Username",
        "sw_dir_on_resource": "SW Directory on Resource",
        "extra_config": "Extra config",
        "basepath": "Calculation basepath",
        "ssh_private_key": "SSH private Key",
        "sge_pe": "SGE PE",
    }
    _field_name_to_intention = {
        "extra_config": "file",
        "ssh_private_key" : "file",
        "queueing_system": "queueing_system",
        "resource_name": "resource_chooser"
    }
    wano_exclusion_items = {
        "base_URI",
        "username",
        "port",
        "ssh_private_key",
        "sw_dir_on_resource",
        "basepath",
        "queueing_system",
        "extra_config",
    }
    serverconfig_exclusion_items = {
        "resource_name"
    }
    _connected_server_text = "<Connected Server>"
    def __init__(self, resources, render_type: str):
        super().__init__()
        self._widgets = {}
        self._render_type = render_type
        self._resources = resources
        self._cluster_dropdown = None
        self._init_done = False
        self.initUI()
        self._init_done = True


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

    def blockSignals(self, do_block):
        super().blockSignals(do_block)
        for widget in self._widgets.values():
            widget.blockSignals(do_block)

    def _get_queue_dropdown_widget(self):
        qs = QtWidgets.QComboBox(self)
        qs.addItem("pbs")
        qs.addItem("slurm")
        qs.addItem("lsf")
        qs.addItem("sge_multi")
        qs.addItem("AiiDA")
        qs.addItem("Internal")
        return qs

    def _update_cluster_dropdown(self):
        curchoice = self._cluster_dropdown.currentText()
        self._cluster_dropdown.clear()
        self._cluster_dropdown.addItem(self._connected_server_text)
        csp = QtClusterSettingsProvider.get_instance()
        regs = [*csp.get_registries().keys()]
        for reg in regs:
            self._cluster_dropdown.addItem(reg)
        if curchoice == "":
            curchoice = self._connected_server_text
        self._cluster_dropdown.setCurrentText(curchoice)

    def _update_default_choices(self, mychoice: str):
        """
        In this function we display the default choices of the resource in case <Connected Server> is set
        :param mychoice:
        :return:
        """
        return
        if self._cluster_dropdown.currentText() != self._connected_server_text:
            return
        default_resources = Resources()
        regs = QtClusterSettingsProvider.get_registries()
        settings = regs[mychoice]

        for this_key in self._resources.render_order():
            this_value = self._resources.get_field_value(this_key)
            default_value = default_resources.get_field_value(this_key)
            intention = self._field_name_to_intention[this_key]
            if this_value != default_value:
                default_case = False
                # In this case we can assume this value was set by the user
                return

            if intention == "int":
                this_i = QtWidgets.QSpinBox()
                this_i.valueChanged.connect(myfunc)
                this_i.setMinimum(0)
                this_i.setMaximum(100000)
                this_i.setValue(this_value)
            elif intention =="file":
                this_i = HorizontalTextEditWithFileImport()
                this_i.line_edit.setText(this_value)
                this_i.line_edit.textChanged.connect(myfunc)
            elif intention =="str":
                this_i = QtWidgets.QLineEdit()
                this_i.setText(this_value)
                this_i.textChanged.connect(myfunc)
            else: # intention == "queueing_system":
                this_i = self._get_queue_dropdown_widget()
                this_i.setCurrentText(this_value)
                this_i.currentTextChanged.connect(myfunc)


    def _reinit_values_from_resource(self):
        for key, widget in self._widgets.items():
            intention = self.field_name_to_intention(key)
            this_value = self._resources.get_field_value(key)
            if intention == "int":
                widget.setValue(this_value)
            elif intention =="file":
                widget.line_edit.setText(this_value)
            elif intention =="str":
                widget.setText(this_value)
            elif intention == "queueing_system":
                widget.setCurrentText(this_value)
            elif intention == "resource_chooser":
                widget.setCurrentText(this_value)

    def _on_cluster_dropdown_change(self, mychoice):
        if not self._init_done:
            return
        if mychoice in {self._connected_server_text, "unset"}:
            # In case we are going back to connected server, we need to reset all fields, which are server dependent
            settings = Resources()
            for field in self.wano_exclusion_items:
                self._resources.set_field_value(field, settings.get_field_value(field))
            self._resources.set_field_value("resource_name", self._connected_server_text)
            self._reinit_values_from_resource()
            return

        regs = QtClusterSettingsProvider.get_registries()
        settings = regs[mychoice]
        for key in self._resources.render_order():
            self._resources.set_field_value(key, settings.get_field_value(key))

        self._reinit_values_from_resource()

    def _init_cluster_dropdown_widget(self):
        if self._cluster_dropdown:
            # Do not double init
            return

        self._cluster_dropdown = QtWidgets.QComboBox(self)
        self._cluster_dropdown.setEditable(True)
        self._cluster_dropdown.lineEdit().setAlignment(QtCore.Qt.AlignCenter)
        self._cluster_dropdown.lineEdit().setReadOnly(True)
        self._cluster_dropdown.currentTextChanged.connect(self._on_cluster_dropdown_change)
        csp = QtClusterSettingsProvider.get_instance()
        csp.settings_changed.connect(self._update_cluster_dropdown)
        wrs :WaNoRegistrySelection = WaNoRegistrySelection.get_instance()
        wrs.registrySelectionChanged.connect(self._update_default_choices)
        self._update_cluster_dropdown()

        return self._cluster_dropdown


    def initUI(self):
        self.setWindowTitle('Resource view')
        if self._render_type == "wano":
            self.render_wano_resource_config()
        else:
            self.render_server_config()

    @staticmethod
    def _fieldChanger(fieldname: str, model: Resources, newvalue):
        """

        :param fieldname:
        :param newvalue:
        :return:
        """

        # adapt value below
        model.set_field_value(fieldname, newvalue)

    def _get_formlayout(self, exclude_items = None, headers = True):
        """
        Shows only job specific resouces -> things like sw dir not to be modified
        :return:
        """
        if exclude_items is None:
            exclude_items = {}

        minHeight = 20
        current_flo = QtWidgets.QFormLayout()
        if headers:
            current_flo.addRow(QtWidgets.QLabel("<b>Host Settings</b>"), QtWidgets.QWidget())

        for this_key in self._resources.render_order():
            if this_key in exclude_items:
                continue
            field_name = self.field_name_to_display_name(this_key)
            #if not this_key in ["walltime", "cpu_per_node", "nodes", "queue", "memory", "custom_requests"]:
            #    continue
            if this_key == "nodes" and headers:
                current_flo.addRow(QtWidgets.QLabel("<b>Default Resources</b>"), QtWidgets.QWidget())
            if this_key == "sge_pe" and headers:
                current_flo.addRow(QtWidgets.QLabel("<b>SGE specific config</b>"), QtWidgets.QWidget())
            this_value = self._resources.get_field_value(this_key)
            intention = self.field_name_to_intention(this_key)
            myfunc = partial(self._fieldChanger, this_key, self._resources)
            if intention == "int":
                this_i = QtWidgets.QSpinBox()
                this_i.valueChanged.connect(myfunc)
                this_i.setMinimum(0)
                this_i.setMaximum(31536000)
                this_i.setValue(this_value)
            elif intention =="file":
                this_i = HorizontalTextEditWithFileImport()
                this_i.line_edit.setText(this_value)
                this_i.line_edit.textChanged.connect(myfunc)
            elif intention =="str":
                this_i = QtWidgets.QLineEdit()
                this_i.setText(this_value)
                this_i.textChanged.connect(myfunc)
            elif intention == "queueing_system":
                this_i = self._get_queue_dropdown_widget()
                this_i.setCurrentText(this_value)
                this_i.currentTextChanged.connect(myfunc)
            elif intention == "resource_chooser":
                this_i = self._init_cluster_dropdown_widget()
                this_i.setCurrentText(this_value)
                this_i.currentTextChanged.connect(myfunc)
            else:
                raise NotImplementedError(f"Intention {intention} not implemented in ResourcesView.")
            current_flo.addRow(field_name, this_i)
            self._widgets[this_key] = this_i
        for i in range(0, current_flo.rowCount()):
            itemAt = current_flo.itemAt(i, QtWidgets.QFormLayout.FieldRole).widget()
            itemAt.setMinimumHeight(minHeight)

        return current_flo

    def render_wano_resource_config(self):
        current_flo = self._get_formlayout(exclude_items=self.wano_exclusion_items, headers=False)
        self.setLayout(current_flo)

    def render_server_config(self):
        current_flo = self._get_formlayout(exclude_items=self.serverconfig_exclusion_items, headers = True)
        self.setLayout(current_flo)
