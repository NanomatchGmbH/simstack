#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import abc


from WaNo.view.RemoteImporterDialog import RemoteImporterDialog

class AbstractWanoView(object):
    def __init__(self, *args, **kwargs):
        self.model = None

    @abc.abstractmethod
    def init_from_model(self):
        pass

    def set_model(self, model):
        self.model = model
        model.set_view(self)

    """
    Disables editing of element
    """
    @abc.abstractmethod
    def set_enabled(self,enabled):
        pass


class AbstractWanoQTView(AbstractWanoView):
    def __init__(self, *args, **kwargs):
        super(AbstractWanoQTView, self).__init__(*args, **kwargs)
        self.actual_widget = None

    def set_visible(self,truefalse):
        if self.actual_widget:
            self.actual_widget.setVisible(truefalse)

    def set_parent(self, parent_view):
        """

        :param parent_view:
        :return:
        """
        #self._parent = parent_view
        #if self._parent is not None:
        if hasattr(parent_view, "get_widget"):
            self._qt_parent = parent_view.get_widget()
        else:
            self._qt_parent = parent_view

    @abc.abstractmethod
    def set_disable(self, true_or_false):
        raise NotImplementedError("Please implement in child class")

    def open_remote_importer(self):
        varpaths = self.model.get_root().get_parent_wf().assemble_variables("")
        mydialog = RemoteImporterDialog(varname ="Import variable \"%s\" from:" % self.model.name, importlist = varpaths)
        mydialog.setModal(True)
        mydialog.exec()
        result = mydialog.result()
        if mydialog.result() == True:
            choice = mydialog.getchoice()
            self.model.set_import(choice)
            self.set_disable(True)
        else:
            self.set_disable(False)
            self.model.set_import(None)

    @abc.abstractmethod
    def get_widget(self):
        return None

    def set_model(self, model):
        super(AbstractWanoQTView, self).set_model(model)

    def decommission(self):
        widget = self.get_widget()
        if widget != None:
            widget.deleteLater()

