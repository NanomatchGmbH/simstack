#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from Qt import QtGui, QtWidgets
from lxml import etree

from WaNo.model.WaNoTreeWalker import ViewCollector, WaNoTreeWalker


def wano_constructor_helper(wanofile, parent_wf):
    wano_dir_root = os.path.dirname(os.path.realpath(wanofile))
    from WaNo.model.WaNoModels import WaNoModelRoot
    from WaNo.view.WaNoViews import WanoQtViewRoot
    wmr = WaNoModelRoot(wano_dir_root=wano_dir_root)
    wmr.set_view_class(WanoQtViewRoot)

    with open(wanofile, 'rt') as infile:
        xml = etree.parse(infile)
    wmr.parse_from_xml(xml)

    vc = ViewCollector()
    newtw = WaNoTreeWalker(wmr)
    # Stage 1: Construct all views
    newtw.walker(capture=False, path_visitor_function=None, subdict_visitor_function=vc.assemble_views,
                 data_visitor_function=vc.data_visitor_view_assembler)

    # Stage 2: Parent all views
    newtw.walker(capture=False, path_visitor_function=None, subdict_visitor_function=vc.assemble_views_parenter,
                 data_visitor_function=vc.data_visitor_view_parenter)

    views_by_path = vc.get_views_by_path()

    # Stage 3 (or Stage 0): Initialize the rootview parent
    rootview = vc.get_views_by_path()[tuple("")]
    anonymous_parent = QtWidgets.QWidget()
    rootview.set_parent(anonymous_parent)

    # Stage 4: Put actual data into the views from the ones deep in the hierarchy to the shallow ones
    sorted_paths = reversed(sorted(views_by_path.keys(), key=len))
    for path in sorted_paths:
        views_by_path[path].init_from_model()


    rootview.init_from_model()

    # Stage 5: Update the layout
    anonymous_parent.update()
    return wmr,rootview

class WaNoFactory(object):
    @classmethod
    def get_model_class(cls, name):
        from WaNo.model.WaNoModels import WaNoItemFloatModel, WaNoModelListLike, \
            WaNoItemStringModel, WaNoItemBoolModel, WaNoModelDictLike, WaNoChoiceModel, \
            MultipleOfModel, WaNoItemFileModel, WaNoItemIntModel, WaNoItemScriptFileModel, \
            WaNoMatrixModel, WaNoThreeRandomLetters, WaNoSwitchModel, WaNoDynamicChoiceModel, \
            WaNoNoneModel
        from WaNo.view.WaNoViews import WaNoItemFloatView, WaNoBoxView, WaNoItemStringView, \
            WaNoItemBoolView, WaNoItemFileView, WaNoChoiceView, MultipleOfView, WaNoItemIntView, \
            WaNoTabView, WaNoGroupView, WaNoScriptView, WaNoDropDownView, WaNoMatrixFloatView, \
            WaNoSwitchView, WaNoInvisibleBoxView, WaNoNone

        wano_list = {  # kwargs['xml'] = self.full_xml.find("WaNoRoot")
            "WaNoFloat": (WaNoItemFloatModel, WaNoItemFloatView),
            "WaNoMatrixFloat": (WaNoMatrixModel, WaNoMatrixFloatView),
            "WaNoInt": (WaNoItemIntModel, WaNoItemIntView),
            "WaNoString": (WaNoItemStringModel, WaNoItemStringView),
            "WaNoListBox": (WaNoModelListLike, WaNoBoxView),
            "WaNoBox": (WaNoModelDictLike, WaNoBoxView),
            "WaNoDictBox": (WaNoModelDictLike, WaNoBoxView),
            "WaNoInviBox": (WaNoModelDictLike, WaNoInvisibleBoxView),
            "WaNoSwitch": (WaNoSwitchModel, WaNoSwitchView),
            "WaNoGroup": (WaNoModelDictLike, WaNoGroupView),
            "WaNoBool": (WaNoItemBoolModel, WaNoItemBoolView),
            "WaNoFile": (WaNoItemFileModel, WaNoItemFileView),
            "WaNoChoice": (WaNoChoiceModel, WaNoChoiceView),
            "WaNoDropDown": (WaNoChoiceModel, WaNoDropDownView),
            "WaNoMultipleOf": (MultipleOfModel, MultipleOfView),
            "WaNoScript": (WaNoItemScriptFileModel, WaNoScriptView),
            "WaNoDynamicDropDown": (WaNoDynamicChoiceModel, WaNoDropDownView),
            "WaNoTabs": (WaNoModelDictLike, WaNoTabView),
            "WaNone": (WaNoNoneModel, WaNoNone),
            "WaNoThreeRandomLetters": (WaNoThreeRandomLetters, WaNoItemStringView)
        }
        return wano_list[name][0]

    @classmethod
    def get_qt_view_class(cls, name):
        from WaNo.model.WaNoModels import WaNoItemFloatModel, WaNoModelListLike, \
            WaNoItemStringModel, WaNoItemBoolModel, WaNoModelDictLike, WaNoChoiceModel, \
            MultipleOfModel, WaNoItemFileModel, WaNoItemIntModel, WaNoItemScriptFileModel, \
            WaNoMatrixModel, WaNoThreeRandomLetters, WaNoSwitchModel, WaNoDynamicChoiceModel, \
            WaNoNoneModel
        from WaNo.view.WaNoViews import WaNoItemFloatView, WaNoBoxView, WaNoItemStringView, \
            WaNoItemBoolView, WaNoItemFileView, WaNoChoiceView, MultipleOfView, WaNoItemIntView, \
            WaNoTabView, WaNoGroupView, WaNoScriptView, WaNoDropDownView, WaNoMatrixFloatView, \
            WaNoSwitchView, WaNoInvisibleBoxView, WaNoNone

        wano_list = {  # kwargs['xml'] = self.full_xml.find("WaNoRoot")
            "WaNoFloat": (WaNoItemFloatModel, WaNoItemFloatView),
            "WaNoMatrixFloat": (WaNoMatrixModel, WaNoMatrixFloatView),
            "WaNoInt": (WaNoItemIntModel, WaNoItemIntView),
            "WaNoString": (WaNoItemStringModel, WaNoItemStringView),
            "WaNoListBox": (WaNoModelListLike, WaNoBoxView),
            "WaNoBox": (WaNoModelDictLike, WaNoBoxView),
            "WaNoDictBox": (WaNoModelDictLike, WaNoBoxView),
            "WaNoInviBox": (WaNoModelDictLike, WaNoInvisibleBoxView),
            "WaNoSwitch": (WaNoSwitchModel, WaNoSwitchView),
            "WaNoGroup": (WaNoModelDictLike, WaNoGroupView),
            "WaNoBool": (WaNoItemBoolModel, WaNoItemBoolView),
            "WaNoFile": (WaNoItemFileModel, WaNoItemFileView),
            "WaNoChoice": (WaNoChoiceModel, WaNoChoiceView),
            "WaNoDropDown": (WaNoChoiceModel, WaNoDropDownView),
            "WaNoMultipleOf": (MultipleOfModel, MultipleOfView),
            "WaNoScript": (WaNoItemScriptFileModel, WaNoScriptView),
            "WaNoDynamicDropDown": (WaNoDynamicChoiceModel, WaNoDropDownView),
            "WaNoTabs": (WaNoModelDictLike, WaNoTabView),
            "WaNone": (WaNoNoneModel, WaNoNone),
            "WaNoThreeRandomLetters": (WaNoThreeRandomLetters, WaNoItemStringView)
        }
        return wano_list[name][1]