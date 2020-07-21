import sys
import unittest

from Qt import QtWidgets

from os import path

from PyQt5.QtWidgets import QApplication
from lxml import etree
from TreeWalker.TreeWalker import TreeWalker
from WaNo.model.WaNoModels import WaNoItemFloatModel, WaNoModelRoot
from WaNo.model.WaNoTreeWalker import WaNoTreeWalker, ViewCollector
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
        container_widget.setLayout(container_layout)
        scroller.setWidget(container_widget)
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(scroller)
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

        wmr.parse_from_xml(self.depxml)
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
        container, container_layout = self.initUI()
        rootview.set_parent(container)

        # Stage 4: Put actual data into the views from the ones deep in the hierarchy to the shallow ones
        sorted_paths = reversed(sorted(views_by_path.keys(), key=len))
        for path in sorted_paths:
            views_by_path[path].init_from_model()

        rootview.init_from_model()

        # Stage 5: Update the layout
        container_layout.addWidget(rootview.get_widget())
        container.update()
        self._app.exec_()



