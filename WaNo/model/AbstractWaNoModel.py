#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

from boolexp import Expression
import abc
import copy
import PySide.QtCore as QtCore

class WaNoNotImplementedError(Exception):
    pass


class AbstractWanoModel(QtCore.QObject):
    def __init__(self, *args, **kwargs):

        self.view = None
        self.root_model = None
        self.is_wano = True
        self.name = "unset"
        #if "root_model" in kwargs:
        self.root_model = kwargs["root_model"]
        # The root view has to be set explicitly, otherwise nobody has a parent.
        # if 'view' in kwargs:
        #    self.view = kwargs['view']
        self.parent = kwargs['parent_model']
        self.visibility_condition = None
        self.visibility_var_path = None
        self.name = kwargs['xml'].attrib["name"]

        self.parse_visibility_condition(kwargs['xml'])
        super(AbstractWanoModel, self).__init__()



    def set_name(self,new_name):
        self.name = new_name

    def parse_visibility_condition(self,xml):
        if "visibility_condition" in xml.attrib:
            self.visibility_condition = xml.attrib["visibility_condition"]
            self.visibility_var_path  = xml.attrib["visibility_var_path"]
            self.root_model.dataChanged.connect(self.evaluate_visibility_condition)

    def evaluate_visibility_condition(self,changed_path):
        # Ok, Plan:
        # here
        # we need two more inputs - one: which expression needs to be evaluated, two: what does it need to be replaced with
        # Then plug this expression to truefalse and we are good to go.
        # who calls it?
        #if changed_path != self.visibility_var_path:
        #    return

        value = self.root_model.get_value(self.visibility_var_path).get_data()
        #print(self.visibility_condition % value)
        truefalse = Expression(self.visibility_condition%value).evaluate()
        self.view.set_visible(truefalse)
        #print(truefalse,value,changed_path)
        #print("Path %s changed" % changed_path)

    def get_name(self):
        return self.name

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

    # Upon rendering the model might provide data different in comparison to the displayed one
    # (For example: the rendered wano only contains the logical filename and not local PC filename
    # By default however get_rendered_wano_data == get_data
    def get_rendered_wano_data(self):
        return self.get_data()

    def set_view(self, view):
        self.view = view

    @abc.abstractmethod
    def get_data(self):
        pass

    @abc.abstractmethod
    def set_data(self,data):
        self.root_model.dataChanged.emit("Test")


    @abc.abstractmethod
    def get_type_str(self):
        pass

    def render(self, rendered_wano, path, submitdir):
        return self.get_rendered_wano_data()

    @abc.abstractmethod
    def update_xml(self):
        pass

    def construct_children(self):
        pass

