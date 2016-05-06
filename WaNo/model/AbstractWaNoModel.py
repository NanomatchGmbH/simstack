#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import abc


class WaNoNotImplementedError(Exception):
    pass


class AbstractWanoModel(object):
    def __init__(self, *args, **kwargs):
        # self.view = None
        self.root_model = None
        if "root_model" in kwargs:
            self.root_model = kwargs["root_model"]
        # The root view has to be set explicitly, otherwise nobody has a parent.
        # if 'view' in kwargs:
        #    self.view = kwargs['view']
        self.parent = kwargs['parent_model']

        self.name = kwargs['xml'].attrib["name"]

    def get_parent(self):
        return self.parent

    # I'm not sure whether we actually require the set method
    # @abc.abstractmethod
    def __setitem__(self, key, item):
        raise NotImplementedError("I don't think this method is needed")

    # To access Wanomodels belonging to this one:
    # <Box>
    #   <Float name="me" />
    # <Box>
    # Box["me"] == Float Wano
    # Few remarks:
    # If There is a for loop, multiple of, etc., we require a specific syntax
    # multipleof should implement a list abc[0],abc[1]... etc.
    # everything else should be dict-like.
    # For trivial wanos without children this will return None
    @abc.abstractmethod
    def __getitem__(self, key):
        pass

    def onChanged(self, *args, **kwargs):
        if self.view is not None:
            self.view.model_changed(*args, **kwargs)

    def view_changed(self, *args, **kwargs):
        pass

    def set_view(self, view):
        self.view = view

    @abc.abstractmethod
    def get_data(self):
        pass

    @abc.abstractmethod
    def set_data(self, data):
        pass

    # This method constructs all children after both view and model have been constructed
    def construct_children(self):
        pass
