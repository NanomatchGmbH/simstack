#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import


class ViewGeneratorHelper(object):
    def __init__(self, viewobject):
        self.viewobject = viewobject
        self.model = None
        self.view = None

    def set_model(self, model):
        self.model = model

    def generate(self):
        self.view = self.viewobject(model=self.model)
        self.model.set_view(self.view)
        self.view.set_model(self.model)

    def init(self):
        self.view.init_from_model()


class WaNoFactory(object):
    postregisterlist = []

    @classmethod
    def build_views(cls):
        for vgh in cls.postregisterlist:
            vgh.generate()

        for vgh in cls.postregisterlist:
            vgh.init()

        del cls.postregisterlist[:]

    @classmethod
    def get_objects(cls, xml, root_model, parent_model):
        from WaNo.model.AbstractWaNoModel import WaNoNotImplementedError
        from WaNo.model.WaNoModels import WaNoItemFloatModel, WaNoModelListLike,\
            WaNoItemStringModel, WaNoItemBoolModel, WaNoModelDictLike
        from WaNo.view.WaNoViews import WaNoItemFloatView, WaNoBoxView, WaNoItemStringView, \
            WaNoItemBoolView, WaNoItemFileView

        wano_list = {
            "WaNoFloat": (WaNoItemFloatModel, WaNoItemFloatView),
            "WaNoString": (WaNoItemStringModel, WaNoItemStringView),
            "WaNoListBox": (WaNoModelListLike, WaNoBoxView),
            "WaNoDictBox": (WaNoModelDictLike, WaNoBoxView),
            "WaNoBool": (WaNoItemBoolModel, WaNoItemBoolView),
            "WaNoFile": (WaNoItemStringModel,WaNoItemFileView)
        }

        if xml.tag not in wano_list:
            print("Unknown Wano")
            raise WaNoNotImplementedError()
        else:
            model, view = wano_list[xml.tag]
            vgh = ViewGeneratorHelper(view)
            cls.postregisterlist.append(vgh)
            m = model(root_model=root_model, parent_model=parent_model, xml=xml)
            vgh.set_model(m)

            m.construct_children()

            return m
