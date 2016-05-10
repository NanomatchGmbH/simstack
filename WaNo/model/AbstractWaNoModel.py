#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import abc
import copy

class WaNoNotImplementedError(Exception):
    pass


class AbstractWanoModel(object):
    def __init__(self, *args, **kwargs):
        self.view = None
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

    def set_view(self, view):
        self.view = view

    @abc.abstractmethod
    def get_data(self):
        pass

    def render(self, rendered_wano, path):
        pass


    @abc.abstractmethod
    def update_xml(self):
        pass

    def construct_children(self):
        pass

