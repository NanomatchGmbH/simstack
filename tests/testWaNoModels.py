import os
import sys
import unittest
from functools import partial

from Qt import QtGui, QtCore, QtWidgets

from os import path
from pprint import pprint

from PyQt5.QtWidgets import QWidget, QApplication
from lxml import etree
from TreeWalker.TreeWalker import TreeWalker
from WaNo.model.AbstractWaNoModel import OrderedDictIterHelper
from WaNo.model.WaNoModels import WaNoItemFloatModel, WaNoModelRoot, WaNoModelDictLike, WaNoModelListLike, \
    MultipleOfModel
from WaNo.view.WaNoViews import WanoQtViewRoot



def subdict_skiplevel(subdict,
                      call_info):
    newsubdict = None
    try:
        newsubdict = subdict["content"]
    except KeyError as e:
        pass
    try:
        newsubdict = subdict["TABS"]
    except KeyError as e:
        pass

    if newsubdict is not None:
        pvf = call_info["path_visitor_function"]
        svf = call_info["subdict_visitor_function"]
        dvf = call_info["data_visitor_function"]
        tw = TreeWalker(newsubdict)
        return tw.walker(capture = True, path_visitor_function=pvf,
                  subdict_visitor_function=svf,
                  data_visitor_function=dvf
        )
    return None

def subdict_view(subdict,
                      call_info):
    newsubdict = None
    try:
        newsubdict = subdict["content"]
    except KeyError as e:
        pass
    try:
        newsubdict = subdict["TABS"]
    except KeyError as e:
        pass

    if newsubdict is not None:
        pvf = call_info["path_visitor_function"]
        svf = call_info["subdict_visitor_function"]
        dvf = call_info["data_visitor_function"]
        tw = TreeWalker(newsubdict)
        return tw.walker(capture = True, path_visitor_function=pvf,
                  subdict_visitor_function=svf,
                  data_visitor_function=dvf
        )
    return None

class PathCollector:
    def __init__(self):
        self._paths = []

    @property
    def paths(self):
        return self._paths

    def assemble_paths(self,twpath):
        mypath = ".".join([str(p) for p in twpath])
        self._paths.append(mypath)
        return twpath

class ViewCollector:
    def __init__(self):
        self._views_by_path = {}

    def get_views_by_path(self):
        return self._views_by_path

    def _get_mypath_treewalker(self, call_info):
        tw_paths = call_info["treewalker_paths"]
        tw: TreeWalker = call_info["treewalker"]
        relpath = tw_paths.relpath
        abspath = tw_paths.abspath
        if abspath is None:
            mypath = tuple("")
        else:
            mypath = tuple(abspath)
        return mypath, tw

    def assemble_views(self, subdict, call_info):
        if isinstance(subdict, OrderedDictIterHelper):
            return

        mypath,tw = self._get_mypath_treewalker(call_info)

        ViewClass = subdict.get_view_class()

        vc = ViewClass()
        self._views_by_path[mypath] = vc
        """
        if mypath != tuple(""):
            parent = tw.resolve(mypath[:-1])
            vc.set_parent(parent.view)
        """
        if isinstance(subdict, MultipleOfModel):
            print("MMM")
        subdict.set_view(vc)
        vc.set_model(subdict)
        return None

    def assemble_views_parenter(self, subdict, call_info):
        if isinstance(subdict, OrderedDictIterHelper):
            return

        mypath,tw = self._get_mypath_treewalker(call_info)

        #ViewClass = subdict.get_view_class()

        vc = subdict.view
        #self._views_by_path[mypath] = vc

        if mypath != tuple(""):
            parent = tw.resolve(mypath[:-1])
            vc.set_parent(parent.view)
        #subdict.set_view(vc)
        #vc.set_model(subdict)
        return None

    def data_visitor_view_assembler(self, data, call_info):
        if isinstance(data, OrderedDictIterHelper):
            return data
        mypath, tw = self._get_mypath_treewalker(call_info)

        ViewClass = data.get_view_class()
        vc = ViewClass()
        self._views_by_path[mypath] = vc
        """
        if mypath != tuple(""):
            parent = None
            checktuple = mypath[:-1]

            parent = tw.resolve(mypath[:-1])
            while isinstance(parent, OrderedDictIterHelper):
                checktuple = checktuple[:-1]
                parent = tw.resolve(checktuple)
            print("HERE", parent,type(parent), parent.view)
            vc.set_parent(parent.view)
        """
        if isinstance(data, MultipleOfModel):
            print("MMM")
        data.set_view(vc)
        vc.set_model(data)
        return data

    def data_visitor_view_parenter(self, data, call_info):
        if isinstance(data, OrderedDictIterHelper):
            return data
        mypath, tw = self._get_mypath_treewalker(call_info)

        #ViewClass = data.get_view_class()
        vc = data.view
        #self._views_by_path[mypath] = vc

        if mypath != tuple(""):
            parent = None
            checktuple = mypath[:-1]

            parent = tw.resolve(mypath[:-1])
            while isinstance(parent, OrderedDictIterHelper):
                checktuple = checktuple[:-1]
                parent = tw.resolve(checktuple)
            print("HERE", parent, type(parent), parent.view)
            vc.set_parent(parent.view)
        #data.set_view(vc)
        #vc.set_model(data)
        return data


class WaNoTreeWalker(TreeWalker):
    @staticmethod
    def _isdict(myobject) -> bool:
        return isinstance(myobject, WaNoModelDictLike) or \
               isinstance(myobject, OrderedDictIterHelper) or \
               isinstance(myobject, MultipleOfModel)

    @staticmethod
    def _islist(myobject) -> bool:
        return isinstance(myobject, WaNoModelListLike) or isinstance(myobject, MultipleOfModel)

class TestWaNoModels(unittest.TestCase):
    def setUp(self):
        self._app = QApplication(sys.argv)

        self.deposit_dir = "%s/inputs/wanos/Deposit" % path.dirname(path.realpath(__file__))
        depxml = path.join(self.deposit_dir,"Deposit3.xml")
        with open(depxml, 'rt') as infile:
            self.depxml = etree.parse(infile)

    def initUI(self):
        container = QtWidgets.QWidget(parent = None)
        scroller = QtWidgets.QScrollArea(parent=container)
        scroller.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        scroller.setWidgetResizable(True)
        container_widget = QtWidgets.QWidget(parent=scroller)
        container_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)
        container.setSizePolicy(QtWidgets.QSizePolicy.Expanding,QtWidgets.QSizePolicy.Expanding)

        container_layout = QtWidgets.QVBoxLayout()


        #wifm.construct_children()
        #WaNoFactory.build_views()
        # The build views has to be done like this:
        # Always set the view class on construction. MultipleOf only duplicates so the views are known.
        # Then use the treewalker library to walk through the models and collect all viewclasses and construct them
        # set view, set model
        #
        # For multiple of: The viewclass is known, you can keep constructing in constructor - well not really
        # if it's none, don't do anything.
        #wifv.init_from_model()

        #container_layout.addWidget(wifv.get_widget())
        #submit_push = QtWidgets.QPushButton("Submit", parent=container_widget)
        #submit_push.clicked.connect(self.render_slot)
        #container_layout.addWidget(submit_push)
        container_widget.setLayout(container_layout)
        scroller.setWidget(container_widget)
        ##scroller.setSizePolicy()
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(scroller)

        #vbox.addStretch(1)
        container.setLayout(vbox)

        container.setGeometry(300, 300, 460, 700)
        container.setWindowTitle('WaNoTest')
        container.show()
        return container, container_layout


    def test_WaNoItemFloatModel(self):
        myfloatmodel = WaNoItemFloatModel(bypass_init = True)
        outdict = {}
        myfloatmodel.model_to_dict(outdict)

    def test_construct_deposit_wano(self):
        wmr = WaNoModelRoot(wano_dir_root = self.deposit_dir)
        wmr.set_view_class(WanoQtViewRoot)
        WQVR = wmr.get_view_class()
        #view = WQVR()

        wmr.parse_from_xml(self.depxml)
        print(type(wmr))
        self.assertAlmostEqual(float(str(wmr["TABS"]["Simulation Parameters"]["Simulation Box"]["Lx"])), 40.0)
        outdict = {}
        wmr.model_to_dict(outdict)

        tw = TreeWalker(outdict)
        secondoutdict = tw.walker(capture = True, path_visitor_function=None, subdict_visitor_function=None, data_visitor_function=None)

        self.assertDictEqual(outdict, secondoutdict)
        thirdoutdict = tw.walker(capture=True, path_visitor_function=None, subdict_visitor_function=subdict_skiplevel,
                                  data_visitor_function=None)

        pc = PathCollector()
        tw = TreeWalker(thirdoutdict)
        tw.walker(path_visitor_function=pc.assemble_paths,
                  subdict_visitor_function=None,
                  data_visitor_function=None)
        #print(pc.paths)
        vc = ViewCollector()
        newtw = WaNoTreeWalker(wmr)
        # Stage 1: Construct all views
        newtw.walker(capture=False, path_visitor_function=None, subdict_visitor_function=vc.assemble_views,
                                  data_visitor_function=vc.data_visitor_view_assembler)

        # Stage 2: Parent all views
        newtw.walker(capture=False, path_visitor_function=None, subdict_visitor_function=vc.assemble_views_parenter,
                                  data_visitor_function=vc.data_visitor_view_parenter)

        views_by_path = vc.get_views_by_path()

        sorted_paths = [*reversed(sorted(views_by_path.keys(), key=len))]

        rootview = vc.get_views_by_path()[tuple("")]
        container, container_layout = self.initUI()
        rootview.set_parent(container)

        for path in sorted_paths:
            print("INITIGINGN",path)
            views_by_path[path].init_from_model()
        print(sorted_paths)


        rootview.init_from_model()
        container_layout.addWidget(rootview.get_widget())
        container.update()
        self._app.exec_()



