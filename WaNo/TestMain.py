#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

#requires python 2.7,
try:
    import collections
except ImportError as e:
    print("OrderedDict requires Python 2.7 or higher or Python 3.1 or higher")
    raise

import abc
import sys
from PySide import QtGui, QtCore
from lxml import etree

class WaNoNotImplementedError(Exception):
    pass

class AbstractWanoView(object):
    def __init__(self,*args, **kwargs):
        self.model = None

    def onChanged(self, *args, **kwargs):
        if self.model is not None:
            self.model.view_changed(*args,**kwargs)

    def model_changed(self,*args,**kwargs):
        self.init_from_model()

    @abc.abstractmethod
    def init_from_model(self):
        pass

    def set_model(self,model):
        self.model = model
        model.set_view(self)
        #self.init_from_model()

class AbstractWanoQTView(AbstractWanoView):
    def __init__(self,*args, **kwargs):
        super(AbstractWanoQTView,self).__init__(*args,**kwargs)
        import pprint
        pprint.pprint(kwargs)
        if "model" in kwargs:
            model = kwargs['model']
            parent = model.get_parent()
            self.qt_parent = parent.view.get_widget()

    @abc.abstractmethod
    def get_widget(self):
        return None

    def set_model(self,model):
        super(AbstractWanoQTView,self).set_model(model)




class WanoQtViewRoot(AbstractWanoQTView):
    def __init__(self,*args,**kwargs):
        super(WanoQtViewRoot,self).__init__(*args,**kwargs)
        self.actual_widget = QtGui.QWidget()
        self.vbox = QtGui.QVBoxLayout()
        self.actual_widget.setLayout(self.vbox)

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):
        for key,model in self.model.wano_dict.items():
            self.vbox.addWidget(model.view.get_widget())






class AbstractWanoModel(object):
    def __init__(self, *args, **kwargs):
        #self.view = None
        self.root_model = None
        if "root_model" in kwargs:
            self.root_model = kwargs["root_model"]
        #The root view has to be set explicitly, otherwise nobody has a parent.
        #if 'view' in kwargs:
        #    self.view = kwargs['view']
        self.parent = kwargs['parent_model']

        self.name=kwargs['xml'].attrib["name"]

    def get_parent(self):
        return self.parent

    #I'm not sure whether we actually require the set method
    #@abc.abstractmethod
    def __setitem__(self, key, item):
        raise NotImplementedError("I don't think this method is needed")

    #To access Wanomodels belonging to this one:
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

    def onChanged(self, *args, **kwargs):
        if self.view is not None:
            self.view.model_changed(*args, **kwargs)

    def view_changed(self, *args, **kwargs):
        pass

    def set_view(self, view):
        self.view = view

    @abc.abstractmethod
    def get_data(self):
        pass

    @abc.abstractmethod
    def set_data(self, data):
        pass

    #This method constructs all children after both view and model have been constructed
    def construct_children(self):
        pass


class WaNoModelDictLike(AbstractWanoModel):
    def __init__(self, *args, **kwargs):
        super(WaNoModelDictLike, self).__init__(*args, **kwargs)
        self.wano_dict = collections.OrderedDict()
        self.xml = kwargs["xml"]

        for child in self.xml:
            model = WaNoFactory.get_objects(child, self, self)
            print ("XML.tag %s"%self.xml.tag)
            #view.set_model(model)
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



#This is the parent class and grandfather. Children have to be unique, no lists here
class WaNoModelRoot(WaNoModelDictLike):
    def __init__(self, *args, **kwargs):
        self.root_model = self
        super(WaNoModelRoot,self).__init__(*args,**kwargs)

    @staticmethod
    def construct_from_wano(filename,rootview):
        tree = etree.ElementTree(file=filename)
        root = tree.getroot()
        modelroot = WaNoModelRoot(xml=root,view=rootview,parent_model=None)
        return modelroot

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
            model = WaNoFactory.get_objects(child, self.root_model, self)
            #view.set_model(model)
            self.wano_list.append(model)

class WaNoBoxView(AbstractWanoQTView):
    def __init__(self, *args, **kwargs):
        super(WaNoBoxView,self).__init__(*args,**kwargs)
        self.actual_widget = QtGui.QWidget(self.qt_parent)
        self.vbox = QtGui.QVBoxLayout()
        self.actual_widget.setLayout(self.vbox)

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):
        for model in self.model.wano_list:
            self.vbox.addWidget(model.view.get_widget())


class WaNoItemFloatModel(AbstractWanoModel):
    def __init__(self,*args,**kwargs):
        super(WaNoItemFloatModel,self).__init__(*args,**kwargs)
        self.myfloat = 15.0

    def get_data(self):
        return self.myfloat

    def set_data(self,data):
        self.myfloat = float(data)

    def __getitem__(self, item):
        return None

    def onChanged(self, *args, **kwargs):
        pass
        #self.controller.model_changed(*args,**kwargs)


class WaNoItemFloatView(AbstractWanoQTView):
    def __init__(self,*args, **kwargs):
        super(WaNoItemFloatView,self).__init__(*args,**kwargs)
        """ Widget code here """
        self.actual_widget = QtGui.QWidget(self.qt_parent)
        vbox = QtGui.QHBoxLayout()
        self.spinner = QtGui.QDoubleSpinBox()
        # self.line_edit = QtGui.QLineEdit()
        self.spinner.setValue(0.0)
        self.label = QtGui.QLabel("ABC")
        vbox.addWidget(self.label)
        vbox.addWidget(self.spinner)
        # vbox.addWidget(self.line_edit)
        self.actual_widget.setLayout(vbox)
        """ Widget code end """

    def get_widget(self):
        return self.actual_widget

    def init_from_model(self):

        self.spinner.setValue(self.model.get_data())
        self.label.setText(self.model.name)

class WaNoItemListModel(AbstractWanoModel):
    def __init__(self, *args, **kwargs):
        super(WaNoItemListModel, self).__init__(*args, **kwargs)
        self.child_wano_models = []


class WaNoItemListView(AbstractWanoQTView):
    def __init__(self,*args,**kwargs):
        super(WaNoItemListView,self).__init__(*args,**kwargs)


    @abc.abstractmethod
    def init_from_model(self):
        self.actual_widget = QtGui.QWidget(self.qt_parent)
        self.hbox = QtGui.QHBoxLayout()
        self.actual_widget.setLayout(self.hbox)
        pass


class ViewGeneratorHelper(object):
    def __init__(self,viewobject):
        self.viewobject=viewobject

    def set_model(self,model):
        self.model = model

    def generate(self):
        self.view = self.viewobject(model=self.model)
        self.model.set_view(self.view)
        self.view.set_model(self.model)

    def init(self):
        self.view.init_from_model()

class WaNoFactory(object):
    wano_list = {
        "WaNoFloat" : (WaNoItemFloatModel,WaNoItemFloatView),
        "WaNoBox" : (WaNoModelListLike,WaNoBoxView)
    }

    postregisterlist=[]

    @classmethod
    def build_views(cls):
        for vgh in cls.postregisterlist:
            vgh.generate()

        for vgh in cls.postregisterlist:
            vgh.init()

        cls.postregisterlist.clear()

    @classmethod
    def get_objects(cls,xml,root_model,parent_model):
        if xml.tag not in cls.wano_list:
            print("Unknown Wano")
            raise WaNoNotImplementedError()
        else:
            model,view = cls.wano_list[xml.tag]
            vgh = ViewGeneratorHelper(view)
            cls.postregisterlist.append(vgh)
            m = model(root_model=root_model,parent_model=parent_model,xml=xml)
            vgh.set_model(m)

            m.construct_children()

            return m







"""
class WaNoItemFloatController(AbstractWanoController):
    def __init__(self):
        super(WaNoItemFloatController,self).__init__()
"""




class Example(QtGui.QWidget):

    def __init__(self):
        super(Example, self).__init__()

        self.initUI()

    def initUI(self):

        okButton = QtGui.QPushButton("OK")
        cancelButton = QtGui.QPushButton("Cancel")

        wifv = WanoQtViewRoot(qt_parent=None)
        wifm = WaNoModelRoot.construct_from_wano("DFT.xml",rootview=wifv)
        wifm.set_view(wifv)
        wifv.set_model(wifm)
        wifm.construct_children()
        WaNoFactory.build_views()
        wifv.init_from_model()


        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        #hbox.addWidget(okButton)
        #hbox.addWidget(cancelButton)
        hbox.addWidget(wifv.get_widget())

        vbox = QtGui.QVBoxLayout()
        vbox.addStretch(1)
        vbox.addLayout(hbox)

        self.setLayout(vbox)

        self.setGeometry(300, 300, 300, 150)
        self.setWindowTitle('Buttons')
        self.show()

def main():

    app = QtGui.QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
