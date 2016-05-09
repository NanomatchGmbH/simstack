#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

# requires python 2.7,
try:
    import collections
except ImportError as e:
    print("OrderedDict requires Python 2.7 or higher or Python 3.1 or higher")
    raise e

from WaNo.model.AbstractWaNoModel import AbstractWanoModel
import WaNo.WaNoFactory
from lxml import etree
import copy

from PySide import QtCore

class WaNoModelDictLike(AbstractWanoModel):
    def __init__(self, *args, **kwargs):
        super(WaNoModelDictLike, self).__init__(*args, **kwargs)
        self.wano_dict = collections.OrderedDict()
        self.xml = kwargs["xml"]

        for child in self.xml:
            model = WaNo.WaNoFactory.WaNoFactory.get_objects(child, self, self)
            self.wano_dict[child.tag] = model

    def __getitem__(self, item):
        return self.wano_dict[item]

    def keys(self):
        return self.wano_dict.keys()

    def values(self):
        return self.wano_dict.values()

    def items(self):
        return self.wano_dict.items()

    def __iter__(self):
        return iter(self.wano_dict)

    def get_data(self):
        return self.wano_dict

    def set_data(self, wano_dict):
        self.wano_dict = wano_dict

    def wanos(self):
        return self.wano_dict.values()

    def update_xml(self):
        for wano in self.wano_dict.values():
            wano.update_xml()

class WaNoChoiceModel(AbstractWanoModel):
    def __init__(self, *args, **kwargs):
        super(WaNoChoiceModel,self).__init__(*args,**kwargs)

        self.xml = kwargs["xml"]
        self.choices = []
        self.chosen=0
        for child in self.xml.iter("Entry"):
            myid = int(child.attrib["id"])
            self.choices.append(child.text)
            assert(len(self.choices) == myid + 1)
            if "chosen" in child.attrib:
                if child.attrib["chosen"].lower() == "true":
                    self.chosen = myid

    def __getitem__(self, item):
        return None

    def get_data(self):
        return self.choices[self.chosen]

    @QtCore.Slot(int)
    def set_chosen(self,choice):
        self.chosen = int(choice)

    def update_xml(self):
        for child in self.xml.iter("Entry"):
            myid = int(child.attrib["id"])
            if "chosen" in child.attrib:
                del child.attrib["chosen"]

            if self.chosen == myid:
                child.attrib["chosen"] = "True"




class WaNoModelListLike(AbstractWanoModel):
    def __init__(self, *args, **kwargs):
        super(WaNoModelListLike, self).__init__(*args, **kwargs)
        self.wano_list = []
        self.xml = kwargs["xml"]

        if "style" in self.xml.attrib:
            self.style = self.xml.attrib["style"]
        else:
            self.style = ""

        for child in self.xml:
            model = WaNo.WaNoFactory.WaNoFactory.get_objects(child, self.root_model, self)
            # view.set_model(model)
            self.wano_list.append(model)

    def __getitem__(self, item):
        return self.wano_list[item]

    def wanos(self):
        return self.wano_list

    def update_xml(self):
        for wano in self.wano_list:
            wano.update_xml()


class MultipleOfModel(AbstractWanoModel):
    def __init__(self, *args, **kwargs):
        super(MultipleOfModel, self).__init__(*args, **kwargs)
        self.xml = kwargs["xml"]
        self.first_xml_child = None
        self.list_of_dicts = []
        for child in self.xml:
            if self.first_xml_child is None:
                self.first_xml_child = child
            wano_temp_dict = self.parse_one_child(child)
            self.list_of_dicts.append(wano_temp_dict)

    def numitems_per_add(self):
        return len(self.first_xml_child)

    def parse_one_child(self,child):
        wano_temp_dict = collections.OrderedDict()
        for cchild in child:
            model = WaNo.WaNoFactory.WaNoFactory.get_objects(cchild, self, self)
            wano_temp_dict[cchild.tag] = model
        return wano_temp_dict

    def __getitem__(self, item):
        return self.list_of_dicts[item]

    def __iter__(self):
        return iter(self.list_of_dicts)

    def __reversed__(self):
        return reversed(self.list_of_dicts)

    def get_data(self):
        return self.list_of_dicts

    def set_data(self, list_of_dicts):
        self.list_of_dicts = list_of_dicts

    def delete_item(self):
        if len(self.list_of_dicts) > 1:
            self.list_of_dicts.pop()
            #print(etree.tostring(self.xml,pretty_print=True).decode("utf-8"))
            for child in reversed(self.xml):
                self.xml.remove(child)
                break
            #print(etree.tostring(self.xml, pretty_print=True).decode("utf-8"))
            return True
        return False

    def add_item(self):
        #print(etree.tostring(self.xml, pretty_print=True).decode("utf-8"))
        my_xml = copy.copy(self.first_xml_child)
        my_xml.attrib["id"] = str(len(self.list_of_dicts))
        self.xml.append(my_xml)
        #print(etree.tostring(self.xml, pretty_print=True).decode("utf-8"))
        model_dict = self.parse_one_child(my_xml)
        WaNo.WaNoFactory.WaNoFactory.build_views()
        self.list_of_dicts.append(model_dict)

    def update_xml(self):
        for wano_dict in self.list_of_dicts:
            for wano in wano_dict.values():
                wano.update_xml()


# This is the parent class and grandfather. Children have to be unique, no lists here
class WaNoModelRoot(WaNoModelDictLike):
    def __init__(self, *args, **kwargs):
        self.root_model = self
        super(WaNoModelRoot, self).__init__(*args, **kwargs)

    @staticmethod
    def construct_from_wano(filename, rootview):
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.ElementTree(file=filename,parser=parser)
        root = tree.getroot()
        modelroot = WaNoModelRoot(xml=root, view=rootview, parent_model=None)
        return modelroot

    def save_xml(self,filename):
        with open(filename,'w') as outfile:
            outfile.write(etree.tostring(self.xml,pretty_print=True).decode("utf-8"))


class WaNoItemFloatModel(AbstractWanoModel):
    def __init__(self, *args, **kwargs):
        super(WaNoItemFloatModel, self).__init__(*args, **kwargs)
        self.myfloat = float(kwargs['xml'].text)
        self.xml = kwargs['xml']

    def get_data(self):
        return self.myfloat

    def set_data(self, data):
        self.myfloat = float(data)

    def __getitem__(self, item):
        return None

    def update_xml(self):
        self.xml.text = str(self.myfloat)

class WaNoItemBoolModel(AbstractWanoModel):
    def __init__(self, *args, **kwargs):
        super(WaNoItemBoolModel, self).__init__(*args, **kwargs)
        bool_as_text = kwargs['xml'].text
        self.xml = kwargs['xml']
        if bool_as_text.lower() == "true":
            self.mybool = True
        else:
            self.mybool = False

    def get_data(self):
        return self.mybool

    def set_data(self, data):
        self.mybool = data

    def __getitem__(self, item):
        return None

    def update_xml(self):
        if self.mybool:
            self.xml.text = "True"
        else:
            self.xml.text = "False"


class WaNoItemStringModel(AbstractWanoModel):
    def __init__(self, *args, **kwargs):
        super(WaNoItemStringModel, self).__init__(*args, **kwargs)
        self.xml = kwargs['xml']
        self.mystring = kwargs['xml'].text

    def get_data(self):
        return self.mystring

    def set_data(self, data):
        self.mystring = str(data)

    def __getitem__(self, item):
        return None

    def update_xml(self):
        self.xml.text = self.mystring

