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
    raise

from WaNo.model.AbstractWaNoModel import AbstractWanoModel
import WaNo.WaNoFactory
from lxml import etree


class WaNoModelDictLike(AbstractWanoModel):
    def __init__(self, *args, **kwargs):
        super(WaNoModelDictLike, self).__init__(*args, **kwargs)
        self.wano_dict = collections.OrderedDict()
        self.xml = kwargs["xml"]

        for child in self.xml:
            model = WaNo.WaNoFactory.WaNoFactory.get_objects(child, self, self)
            print("XML.tag %s" % self.xml.tag)
            # view.set_model(model)
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


# This is the parent class and grandfather. Children have to be unique, no lists here
class WaNoModelRoot(WaNoModelDictLike):
    def __init__(self, *args, **kwargs):
        self.root_model = self
        super(WaNoModelRoot, self).__init__(*args, **kwargs)

    @staticmethod
    def construct_from_wano(filename, rootview):
        tree = etree.ElementTree(file=filename)
        root = tree.getroot()
        modelroot = WaNoModelRoot(xml=root, view=rootview, parent_model=None)
        return modelroot


class WaNoItemFloatModel(AbstractWanoModel):
    def __init__(self, *args, **kwargs):
        super(WaNoItemFloatModel, self).__init__(*args, **kwargs)
        self.myfloat = 15.0

    def get_data(self):
        return self.myfloat

    def set_data(self, data):
        self.myfloat = float(data)

    def __getitem__(self, item):
        return None

    def onChanged(self, *args, **kwargs):
        pass
        # self.controller.model_changed(*args,**kwargs)
