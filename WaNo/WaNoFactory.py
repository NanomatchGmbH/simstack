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


def wano_constructor_helper(wanofile,container_widget,parent_wf):
    from WaNo.model.WaNoModels import WaNoModelRoot
    from WaNo.view.WaNoViews import WanoQtViewRoot
    wifv = WanoQtViewRoot(qt_parent=container_widget)
    wifm = WaNoModelRoot.construct_from_wano(wanofile, rootview=wifv,parent_wf = parent_wf)
    wifm.set_view(wifv)
    wifv.set_model(wifm)
    wifm.construct_children()
    WaNoFactory.build_views()
    wifv.init_from_model()
    wifm.dataChanged.emit("force")
    return wifm,wifv

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
    def get_objects(cls, xml, root_model, parent_model, current_path):
        from WaNo.model.AbstractWaNoModel import WaNoNotImplementedError
        from WaNo.model.WaNoModels import WaNoItemFloatModel, WaNoModelListLike,\
            WaNoItemStringModel, WaNoItemBoolModel, WaNoModelDictLike, WaNoChoiceModel, \
            MultipleOfModel, WaNoItemFileModel, WaNoItemIntModel, WaNoItemScriptFileModel, \
            WaNoMatrixModel
        from WaNo.view.WaNoViews import WaNoItemFloatView, WaNoBoxView, WaNoItemStringView, \
            WaNoItemBoolView, WaNoItemFileView, WaNoChoiceView, MultipleOfView, WaNoItemIntView,\
            WaNoTabView, WaNoGroupView, WaNoScriptView, WaNoDropDownView, WaNoMatrixFloatView

        wano_list = {
            "WaNoFloat": (WaNoItemFloatModel, WaNoItemFloatView),
            "WaNoMatrixFloat": (WaNoMatrixModel, WaNoMatrixFloatView),
            "WaNoInt": (WaNoItemIntModel, WaNoItemIntView),
            "WaNoString": (WaNoItemStringModel, WaNoItemStringView),
            "WaNoListBox": (WaNoModelListLike, WaNoBoxView),
            "WaNoBox": (WaNoModelDictLike, WaNoBoxView),
            "WaNoDictBox": (WaNoModelDictLike, WaNoBoxView),
            "WaNoGroup": (WaNoModelDictLike, WaNoGroupView),
            "WaNoBool": (WaNoItemBoolModel, WaNoItemBoolView),
            "WaNoFile": (WaNoItemFileModel, WaNoItemFileView),
            "WaNoChoice": (WaNoChoiceModel, WaNoChoiceView),
            "WaNoDropDown": (WaNoChoiceModel, WaNoDropDownView),
            "WaNoMultipleOf": (MultipleOfModel,MultipleOfView),
            "WaNoScript": (WaNoItemScriptFileModel, WaNoScriptView),
            "WaNoTabs": (WaNoModelDictLike,WaNoTabView)
        }

        if xml.tag not in wano_list:
            print("Unknown Wano", xml.tag)
            raise WaNoNotImplementedError()
        else:
            model, view = wano_list[xml.tag]
            vgh = ViewGeneratorHelper(view)
            cls.postregisterlist.append(vgh)
            m = model(root_model=root_model, parent_model=parent_model, xml=xml, full_path=current_path)
            vgh.set_model(m)
            m.construct_children()
            return m
