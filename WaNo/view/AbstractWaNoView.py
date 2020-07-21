#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import abc
import copy

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
        self._parent = parent_view
        if self._parent is not None:
            self._qt_parent = parent_view.get_widget()

    @abc.abstractmethod
    def get_widget(self):
        return None

    def set_model(self, model):
        super(AbstractWanoQTView, self).set_model(model)

    def decommission(self):
        widget = self.get_widget()
        if widget != None:
            widget.deleteLater()

