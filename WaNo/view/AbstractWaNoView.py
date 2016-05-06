#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import abc


class AbstractWanoView(object):
    def __init__(self, *args, **kwargs):
        self.model = None

    def onChanged(self, *args, **kwargs):
        if self.model is not None:
            self.model.view_changed(*args, **kwargs)

    def model_changed(self, *args, **kwargs):
        self.init_from_model()

    @abc.abstractmethod
    def init_from_model(self):
        pass

    def set_model(self, model):
        self.model = model
        model.set_view(self)
        # self.init_from_model()


class AbstractWanoQTView(AbstractWanoView):
    def __init__(self, *args, **kwargs):
        super(AbstractWanoQTView, self).__init__(*args, **kwargs)
        import pprint
        pprint.pprint(kwargs)
        if "model" in kwargs:
            model = kwargs['model']
            parent = model.get_parent()
            self.qt_parent = parent.view.get_widget()

    @abc.abstractmethod
    def get_widget(self):
        return None

    def set_model(self, model):
        super(AbstractWanoQTView, self).set_model(model)
