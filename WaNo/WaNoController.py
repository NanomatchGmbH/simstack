from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import


class AbstractWaNoController(object):
    def __init__(self,parent,model,view,rootnode,xml_local):
        self.rootnode = rootnode
        self.parent = parent
        self.model = model
        self.view = view
        self.xml_local = xml_local

    @abc.abstractmethod
    def valueChanged(self):
        # This method is called, when value was changed, it should take data from the view and
        # update the model accordingly.
        raise NotImplementedError("Abstract Method called")

    def advertiseTreeChange(self):
        self.rootnode.treeChanged()

    @abc.abstractmethod
    def treeChanged(self,**kwargs):
        #If data in the tree has changed, every element has to be notified in case of
        #Boolean logic during rendering
        #This is pseudocode:
        # for child in mychildren:
        #     child.treeChanged(**kwargs)
        # #Now act on my own change:
        # if rootnode.queryModel("Element.value.0.Lx") > 25:
        #     self.view.enable()
        raise NotImplementedError("Abstract Method called")


class AbstractWaNoModel(object):
    def __init__(self,xml_local,simple_data_local,simple_data_global):
        self.name = xml_local.get("name")
        self.attrib = xml_local.attrib
        self.xml = xml_local
        self.simple_data_local = simple_data_local
        self.simple_data_global = simple_data_global

    @abc.abstractmethod
    def queryModel(self,location):
        raise NotImplementedError("Abstract Method called")


