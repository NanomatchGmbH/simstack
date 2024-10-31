import os
import sys
import unittest
from pathlib import Path

from PySide6 import QtWidgets
from PySide6 import QtCore

from os import path

from PySide6.QtWidgets import QApplication
from lxml import etree
from TreeWalker.TreeWalker import TreeWalker
from SimStackServer.WaNo.WaNoFactory import wano_constructor_helper, wano_without_view_constructor_helper
from SimStackServer.WaNo.WaNoModels import WaNoItemFloatModel, WaNoModelRoot
from SimStackServer.WaNo.WaNoTreeWalker import ViewCollector, PathCollector, subdict_skiplevel
from simstack.view.WaNoViews import WanoQtViewRoot


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




class TestWaNoModels(unittest.TestCase):
    def setUp(self):
        self._app = QApplication(sys.argv)

        self.deposit_dir = "%s/inputs/wanos/Deposit" % path.dirname(path.realpath(__file__))
        self.depxml = path.join(self.deposit_dir,"Deposit3.xml")

        self.lf_dir = "%s/inputs/wanos/lightforge2" % path.dirname(path.realpath(__file__))
        self.lfxml = path.join(self.lf_dir, "lightforge2.xml")

    def tearDown(self) -> None:
        self._app.exit()


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

    def _construct_wano_nogui(self,wanofile):
        with open(wanofile, 'rt') as infile:
            xml = etree.parse(infile)
        wano_dir_root = Path(os.path.dirname(os.path.realpath(wanofile)))

        wmr = WaNoModelRoot(wano_dir_root = wano_dir_root)
        wmr.parse_from_xml(xml)
        wmr = wano_without_view_constructor_helper(wmr)
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
        wanopaths = wmr.get_all_variable_paths()
        self.assertListEqual(pc.paths, wanopaths)
        print("here")

    def test_dep_nogui(self):
        self._construct_wano_nogui(self.depxml)


    #@unittest.skip
    def test_deposit_wano(self):
        self._construct_wano_only(self.lfxml)

    def _construct_wano_only(self, wanofile):
        with open(wanofile, 'rt') as infile:
            xml = etree.parse(infile)
        wano_dir_root = Path(os.path.dirname(os.path.realpath(wanofile)))

        wmr = WaNoModelRoot(wano_dir_root = wano_dir_root)
        wmr.set_view_class(WanoQtViewRoot)

        wmr.parse_from_xml(xml)
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

        container, container_layout = self.initUI()
        wmr.set_parent(container)
        wmr.get_root()

        rootmodel, rootview = wano_constructor_helper(wmr)
        container_layout.addWidget(rootview.get_widget())
        container.update()
        wmr.datachanged_force()
        self._app.exec_()

    def test_qt_completer_wano(self):
        with open(self.depxml, 'rt') as infile:
            xml = etree.parse(infile)
        wano_dir_root = Path(os.path.dirname(os.path.realpath(self.depxml)))

        wmr = WaNoModelRoot(wano_dir_root = wano_dir_root)
        wmr.set_view_class(WanoQtViewRoot)

        wmr.parse_from_xml(xml)
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
        suggestions = pc.paths
        label = QtWidgets.QLabel("Depositpaths")
        mylineedit = QtWidgets.QLineEdit()
        completer = QtWidgets.QCompleter(suggestions)
        completer.setCompletionMode(QtWidgets.QCompleter.UnfilteredPopupCompletion)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        mylineedit.setCompleter(completer)
        container, container_layout = self.initUI()
        container_layout.addWidget(label)
        container_layout.addWidget(mylineedit)
        container.update()
        self._app.exec_()

    def test_qt_completer(self):

        label = QtWidgets.QLabel("Obstauswahl")
        mylineedit = QtWidgets.QLineEdit()
        suggestions =["Affe","Birne","Kirsche", "Kisch", "Kirche"]
        completer = QtWidgets.QCompleter(suggestions)
        completer.setCompletionMode(QtWidgets.QCompleter.UnfilteredPopupCompletion)
        completer.setCaseSensitivity(QtCore.Qt.CaseInsensitive)
        mylineedit.setCompleter(completer)
        container, container_layout = self.initUI()
        container_layout.addWidget(label)
        container_layout.addWidget(mylineedit)
        container.update()
        self._app.exec_()

    def _construct_wano(self, wanofile):
        with open(wanofile, 'rt') as infile:
            xml = etree.parse(infile)
        wano_dir_root = Path(os.path.dirname(os.path.realpath(wanofile)))

        wmr = WaNoModelRoot(wano_dir_root = wano_dir_root)
        wmr.set_view_class(WanoQtViewRoot)

        wmr.parse_from_xml(xml)
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
        start_path = ["ABC","DEF"]
        vc.set_start_path(start_path)
        container, container_layout = self.initUI()
        wmr.set_parent(container)
        wmr.get_root()

        rootmodel, rootview = wano_constructor_helper(wmr)
        container_layout.addWidget(rootview.get_widget())
        container.update()
        wmr.datachanged_force()
        self._app.exec_()



