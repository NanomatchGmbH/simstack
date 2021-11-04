from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import datetime
import time
import os

import logging
import traceback
import uuid

import abc

from enum import Enum
from os.path import join
import posixpath
from pathlib import Path

from   lxml import etree

import Qt.QtCore as QtCore
import Qt.QtGui  as QtGui
import Qt.QtWidgets  as QtWidgets
from Qt.QtCore import Signal

import SimStackServer.WaNo.WaNoFactory as WaNoFactory
from SimStackServer.WorkflowModel import WorkflowExecModule, Workflow, DirectedGraph, WorkflowElementList, SubGraph, \
    ForEachGraph, StringList, WFPass, IfGraph, WhileGraph, VariableElement
from SimStackServer.WaNo.MiscWaNoTypes import WaNoListEntry
from WaNo.SimStackPaths import SimStackPaths
from WaNo.WaNoSettingsProvider import WaNoSettingsProvider
from WaNo.Constants import SETTING_KEYS

from WaNo.view.RemoteImporterDialog import RemoteImporterDialog

from WaNo.view.WFEditorWidgets import WFEWaNoListWidget, WFEListWidget
from WaNo.lib.FileSystemTree import copytree, copytree_pathlib

#def mapClassToTag(name):
#    xx = name.replace('Widget','')
#    return xx[2:]
    
widgetColors = {'MainEditor' : '#F5FFF5' , 'Control': '#EBFFD6' , 'Base': '#F5FFEB' ,
               'WaNo' : '#FF00FF', 'ButtonColor':'#D4FF7F' }

#Blue Theme
#widgetColors = {'MainEditor' : '#D5E9FF' , 'Control': '#D5E9FF' , 'Base': '#AABBCC' ,
#               'WaNo' : '#AABBCC', 'ButtonColor':'#88C2FF' }


import copy


def linuxjoin(*args, **kwargs):
    return posixpath.join(*args,**kwargs)

class DragDropTargetTracker(object):
    def manual_init(self):
        self._initial_parent = self.parent()

    @abc.abstractmethod
    def parent(self):
        pass

    def _target_tracker(self,event):
        self._newparent = event

    def mouseMoveEvent_feature(self, e):
        if e.buttons() != QtCore.Qt.LeftButton:
            return

        #self.parent().removeElement(self)
        mimeData = QtCore.QMimeData()
        self.drag = QtGui.QDrag(self)
        self.drag.setMimeData(mimeData)
        self.drag.setHotSpot(e.pos() - self.rect().topLeft())
        #self.move(e.globalPos())
        self.drag.targetChanged.connect(self._target_tracker)
        self._newparent = self.parent()
        dropAction = self.drag.exec_(QtCore.Qt.MoveAction)

        #In case the target of the drop changed we are outside the workflow editor
        #In that case we would like to remove ourselves
        if self._newparent is None:
            self.parent().removeElement(self.model)
            self.model.view.deleteLater()
        elif self._newparent == self._initial_parent:
            # Nothing to be done
            pass
        else:
            # In this case we assume both types have "correct" dropevents
            # print("Passing")
            pass

class WFWaNoWidget(QtWidgets.QToolButton,DragDropTargetTracker):
    def __init__(self, text, wano :WaNoListEntry, parent):
        super(WFWaNoWidget, self).__init__(parent)
        self.manual_init()
        self.logger = logging.getLogger('WFELOG')
        self.moved = False
        lvl = self.logger.getEffectiveLevel() # switch off too many infos
        self.logger.setLevel(logging.ERROR)
        self.is_wano = True
        self.logger.setLevel(lvl)
        self.wf_model = parent.model.get_root()
        stylesheet ="""
        QToolButton
        {
        background-color: %s;
            border: 3px solid black;
            border-radius: 12px;
            color: black;
            font-size: 24px;
            padding: 4px;
            padding-left: 6px;
            padding-right: 6px;
            icon-size: 64px;
            }

        """ %widgetColors["ButtonColor"]
        self.setStyleSheet(stylesheet) # + widgetColors['WaNo'])
        self.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.setText(text)
        self.setIcon(QtGui.QIcon(wano.icon))
        self._wano_type = wano.name
        #self.setAutoFillBackground(True)
        #self.setColor(QtCore.Qt.lightGray)
        self.wano = copy.copy(wano)
        self.model = self
        self.view = self
        self.wano_model = None
        self.wano_view = None
        self.constructed = False
        self.uuid = str(uuid.uuid4())
        self.construct_wano()
        self.name = self.text()
        # today int he evening: add info on aiida node ids, while executing workflow.
        # read output and check if it actually works

    @classmethod
    def instantiate_from_folder(cls,folder,wanotype, parent):
        folder = Path(folder)
        iconpath = folder / (wanotype + ".png")
        if not os.path.isfile(iconpath):
            icon = QtWidgets.QFileIconProvider().icon(QtWidgets.QFileIconProvider.Computer)
            wano_icon = icon.pixmap(icon.actualSize(QtCore.QSize(128, 128)))
        else:
            wano_icon = QtGui.QIcon(str(iconpath))
        uuid = folder.name
        wano = WaNoListEntry(name=wanotype, folder=folder, icon = wano_icon)
        #[wanotype,folder,os.path.join(folder,wanotype) + ".xml", wano_icon]
        returnobject = cls(text=wano.name, wano=wano, parent=parent)
        #overwrite old uuid
        returnobject.uuid=uuid
        return returnobject

    def place_elements(self):
        pass

    def setText(self,*args,**kwargs):
        self.name = args[0]
        super(WFWaNoWidget,self).setText(*args,**kwargs)

    def mouseMoveEvent(self, e):
        self.mouseMoveEvent_feature(e)


    def setColor(self,color):
        p = QtGui.QPalette()
        p.setColor(QtGui.QPalette.Button,color)
        self.setPalette(p)
        
    def get_xml(self):
        me = etree.Element("WaNo")
        me.attrib["type"] = str(self.wano.name)
        me.attrib["uuid"] = str(self.uuid)
        return me

    def instantiate_in_folder(self,folder):
        outfolder = folder/"wanos"/self.uuid

        try:
            os.makedirs(outfolder)
        except OSError as e:
            pass

        #print(self.wano[1],outfolder)
        if outfolder != self.wano.folder:
            try:
                print("Copying %s to %s"%(outfolder,self.wano.folder))

                copytree_pathlib(self.wano.folder, outfolder)
            except Exception as e:
                self.logger.error("Failed to copy tree: %s." % str(e))
                import traceback
                traceback.print_exc()
                return False

        self.wano.folder = outfolder

        self.wano_model.update_xml()
        return self.wano_model.save_xml(self.wano)

    def render(self, path_list, output_path_list, basefolder,stageout_basedir=""):
        #myfolder = os.path.join(basefolder,self.uuid)
        print("rendering wano with stageout_basedir %s" %stageout_basedir)
        jsdl, wem = self.wano_model.render_and_write_input_files_newmodel(basefolder,stageout_basedir=stageout_basedir)
        wem: WorkflowExecModule
        wem.set_wano_xml(self.wano_model.name + ".xml")
        return jsdl, wem, path_list + [wem.name]

    def clear(self):
        pass 

    def construct_wano(self):
        if not self.constructed:
            self.wano_model,self.wano_view = WaNoFactory.wano_constructor(self.wano)
            self.wano_model.set_parent_wf(self.wf_model)
            self.wano_model.datachanged_force()
            self.constructed = True

    def mouseDoubleClickEvent(self,e):
        if self.wano_model is None:
            self.construct_wano()
        self.parent().openWaNoEditor(self)  # pass the widget to remember it

    def get_variables(self):
        if self.wano_model is not None:
            return self.wano_model.get_all_variable_paths()
        return []

class SubmitType(Enum):
    SINGLE_WANO = 0
    WORKFLOW = 1

class WFItemListInterface(object):
    def __init__(self, *args, **kwargs):
        self.is_wano = False
        self.editor = kwargs['editor']
        self.view = kwargs["view"]
        self.elements = [] # List of Elements,Workflows, ControlElements
        # Name of the saved folder
        self.elementnames = []
        self.foldername = None

    def element_to_name(self, element):
        idx = self.elements.index(element)
        return self.elementnames[idx]

    def move_element_to_position(self, element, new_position):
        old_index = self.elements.index(element)

        if old_index != new_position:
            ele = self.elements.pop(old_index)
            ele_name = self.elementnames.pop(old_index)
            if old_index < new_position:
                new_position -= 1
            self.elements.insert(new_position, ele)
            self.elementnames.insert(new_position, ele_name)

    def unique_name(self, oldbase):
        base = oldbase
        i = 1
        while base in self.elementnames:
            base = "%s_%d" % (oldbase, i)
            i += 1
        return base

    def add_element(self, element, pos=None):
        if pos is not None:
            newname = self.unique_name(element.name)
            if newname != element.name:
                element.setText(newname)
                element.name = newname
            self.elements.insert(pos, element)

            self.elementnames.insert(pos, newname)
        else:
            self.elements.append(element)
            self.elementnames.append(element.text())

    def remove_element(self, element):
        myid = self.elements.index(element)
        self.elements.remove(element)
        del self.elementnames[myid]

    def openWaNoEditor(self, wanoWidget):
        self.editor.openWaNoEditor(wanoWidget)

    def removeElement(self, element):
        # remove element both from the buttons and child list
        element.close()
        self.editor.remove(element)
        myid = self.elements.index(element)
        self.elements.remove(element)
        del self.elementnames[myid]
        element.view.deleteLater()

class WFItemModel:
    def __init__(self, *args, **kwargs):
        pass

    def render_to_simple_wf(self,path_list, output_path_list, submitdir,jobdir):
        activities = []
        transitions = []
        #wf = WFtoXML.xml_subworkflow(Transition=transitions,Activity=activities)

    #this function assembles all files relative to the workflow root
    #The files will be export to c9m:${WORKFLOW_ID}/the file name below
    def assemble_files(self,path):
        myfiles = []
        return myfiles

    def assemble_variables(self, path):
        return []

    def close(self):
        pass

    def setText(self,*args,**kwargs):
        self.name = args[0]

    def save_to_disk(self, complete_foldername):
        xml = []
        return xml

    def read_from_disk(self, full_foldername, xml_subelement):
        return


class SubWFModel(WFItemModel,WFItemListInterface):
    def __init__(self,*args,**kwargs):
        WFItemListInterface.__init__(self,*args,**kwargs)
        self.wf_root = kwargs["wf_root"]
        self.name = "SubWF"

    def get_root(self):
        return self.wf_root

    def render_to_simple_wf(self, path_list, output_path_list, submitdir,jobdir,path, parent_ids):
        """

        :param submitdir:
        :param jobdir:
        :param path:
        :param parent_ids (list): List of parent ids, this WF has to transition from
        :return:
        """

        activities = []
        transitions = []
        my_jobdir = jobdir
        basepath = path
        for myid, (ele, elename) in enumerate(zip(self.elements, self.elementnames)):
            toids = []
            if ele.is_wano:
                wano_dir = os.path.join(jobdir, self.element_to_name(ele))
                try:
                    os.makedirs(wano_dir)
                except OSError:
                    pass

                stageout_basedir = "%s/%s" %(basepath,elename)

                jsdl, wem, wem_path_list= ele.render(path_list, output_path_list, wano_dir, stageout_basedir=stageout_basedir)
                wem.set_given_name(elename)
                wem : WorkflowExecModule

                wem.set_given_name(elename)
                mypath = "/".join(path_list + [elename])
                myoutputpath = "/".join(output_path_list + [elename])
                wem.set_path(mypath)
                wem.set_outputpath(myoutputpath)
                toids = [wem.uid]
                activities.append(["WorkflowExecModule",wem])
                for pid in parent_ids:
                    for toid in toids:
                        transitions.append((pid, toid))
            else:
                my_activities, my_transitions, toids = ele.render_to_simple_wf(path_list, output_path_list, submitdir,jobdir,path=path, parent_ids = parent_ids)
                activities += my_activities
                transitions += my_transitions


            parent_ids = toids

        return activities, transitions, parent_ids

    def assemble_files(self, path):
        # this function assembles all files relative to the workflow root
        # The files will be export to c9m:${WORKFLOW_ID}/the file name below

        myfiles = []
        for myid, (ele, name) in enumerate(zip(self.elements, self.elementnames)):
            if ele.is_wano:
                for file in ele.wano_model.get_output_files():
                    fn = linuxjoin(path, name, "outputs", file)
                    myfiles.append(fn)
            else:
                for otherfile in ele.assemble_files(path):
                    myfiles.append(linuxjoin(path,otherfile))
        return myfiles

    def assemble_variables(self, path):
        myvars = []
        for myid, (ele, name) in enumerate(zip(self.elements, self.elementnames)):
            if ele.is_wano:
                for var in ele.get_variables():
                    newpath = merge_path(path,ele.name,var)
                    myvars.append(newpath)
            else:
                for myvar in ele.assemble_variables(path):
                    myvars.append(myvar)
        return myvars

    def read_from_disk(self, full_foldername, xml_subelement):
        #self.foldername = foldername
        #xml_filename = os.path.join(foldername,os.path.basename(foldername)) + ".xml"
        #tree = etree.parse(xml_filename)
        #root = tree.getroot()
        for child in xml_subelement:
            if child.tag == "WaNo":
                type = child.attrib["type"]
                name = child.attrib["name"]
                uuid = child.attrib["uuid"]
                myid = int(child.attrib["id"])
                #print(len(self.elements),myid)
                assert (myid == len(self.elements))
                wanofolder = os.path.join(full_foldername,"wanos",uuid)
                widget = WFWaNoWidget.instantiate_from_folder(wanofolder, type, parent=self.view)
                widget.setText(name)
                self.elements.append(widget)
                self.elementnames.append(name)
            elif child.tag == "WFControl":
                name = child.attrib["name"]
                type = child.attrib["type"]
                model,view = ControlFactory.construct(type,qt_parent=self.view,logical_parent=self.view,editor=self.editor,wf_root=self.wf_root)
                self.elements.append(model)
                self.elementnames.append(name)
                view.setText(name)
                model.read_from_disk(full_foldername=full_foldername,xml_subelement=child)


    def save_to_disk(self,foldername):
        success = False
        attributes = {"name":self.view.text(),"type":"SubWorkflow"}
        root = etree.Element("WFControl",attrib=attributes)

        #my_foldername = os.path.join(foldername,self.view.text())
        my_foldername = foldername
        # TODO revert changes in filesystem in case instantiate_in_folder fails
        for myid, (ele, name) in enumerate(zip(self.elements, self.elementnames)):
            if ele.is_wano:
                subxml = ele.get_xml()
                subxml.attrib["id"] = str(myid)
                subxml.attrib["name"] = name
                success = ele.instantiate_in_folder(my_foldername)
                root.append(subxml)
                if not success:
                    break
            else:
                root.append(ele.save_to_disk(my_foldername))
        return root

    def remove_element(self,element):
        myid = self.elements.index(element)
        self.elements.remove(element)
        del self.elementnames[myid]

    def removeElement(self, element):
        #print("subwf Removing",element)
        self.remove_element(element)
        return

class WhileModel(WFItemModel):
    def __init__(self,*args,**kwargs):
        #super(ForEachModel,self).__init__(*args,**kwargs)
        super(WhileModel, self).__init__(*args, **kwargs)
        self.wf_root = kwargs["wf_root"]
        self.is_wano = False
        self.editor = kwargs['editor']
        self.view = kwargs["view"]
        self._subwf_model, self._subwf_view = ControlFactory.construct("SubWorkflow",editor=self.editor,qt_parent=self.view, logical_parent=self.view.logical_parent,wf_root = self.wf_root)
        self.subwf_models = [self._subwf_model]
        self.subwf_views = [self._subwf_view]
        self.name = "While"
        self.itername = "While_iterator"
        self._condition = "Condition"

    def set_condition(self, condition):
        self._condition = condition

    def get_condition(self):
        return self._condition

    def set_itername(self, itername):
        self.itername = itername

    def get_itername(self):
        return self.itername

    def render_to_simple_wf(self, path_list, output_path_list, submitdir ,jobdir ,path , parent_ids):
        transitions = []

        if jobdir == "":
            my_jobdir = self.name
        else:
            my_jobdir = "%s/%s" % (jobdir, self.name)

        if path == "":
            path = self.name
        else:
            path = "%s/%s" %(path,self.name)


        my_path_list = path_list + [self.name]
        my_output_path_list = output_path_list + [self.name, "${" + self.itername.replace(" ","") + "}"]

        sub_activities, sub_transitions, sub_toids = self._subwf_model.render_to_simple_wf(my_path_list, my_output_path_list, submitdir,my_jobdir,path = path, parent_ids = ["temporary_connector"])
        sg = SubGraph(elements = WorkflowElementList(sub_activities),
                 graph = DirectedGraph(sub_transitions))

        mypass = WFPass()
        finish_uid = mypass.uid
        fe = WhileGraph(subgraph = sg,
                          finish_uid = finish_uid,
                          iterator_name = self.itername,
                          condition = self._condition,
                          subgraph_final_ids = StringList(sub_toids)
        )

        toids = [fe.uid]
        for parent_id in parent_ids:
            transitions.append((parent_id, toids[0]))

        return [("WhileGraph",fe),("WFPass", mypass)], transitions, [finish_uid]  #WFtoXML.xml_subwfforeach(IteratorName=self.itername,IterSet=filesets,SubWorkflow=swf,Id=muuid)


    def assemble_variables(self, path):
        if path == "":
            mypath = "While.${%s_ITER}"%self.itername
            myvalue = "While.${%s}"%self.itername
        else:
            mypath = "%s.While.${%s_ITER}" % (path, self.itername)
            myvalue= "%s.While.${%s}" % (path, self.itername)
        myvars = self._subwf_model.assemble_variables(mypath)
        my_iterator = "${%s}"%self.itername
        myvars.append(my_iterator)
        return myvars

    def assemble_files(self,path):
        myfiles = []
        for otherfile in self._subwf_model.assemble_files(path):
            myfiles.append(linuxjoin(path, self.view.text(),"*",otherfile))
        return myfiles

    def save_to_disk(self, foldername):
        #view needs varname
        attributes = {"name": self.name,
                      "type": "While",
                      "condition": self._condition}
        root = etree.Element("WFControl", attrib=attributes)
        my_foldername = foldername
        root.append(self._subwf_model.save_to_disk(my_foldername))
        iter_xml = etree.SubElement(root,"IterName")
        iter_xml.text = self.itername
        return root

    def read_from_disk(self, full_foldername, xml_subelement):
        attribs = xml_subelement.attrib
        assert attribs["type"] == "While"
        self._condition = attribs["condition"]
        for child in xml_subelement:
            if child.tag == "IterName":
                self.itername = child.text
                continue
            if child.tag != "WFControl":
                continue
            if child.attrib["type"] != "SubWorkflow":
                continue
            name = child.attrib["name"]
            type = child.attrib["type"]

            self._subwf_view.setText(name)
            self._subwf_model.read_from_disk(full_foldername=full_foldername,xml_subelement=child)


class IfModel(WFItemModel):
    def __init__(self,*args,**kwargs):
        super(IfModel, self).__init__(*args, **kwargs)
        self.wf_root = kwargs["wf_root"]

        self.is_wano = False
        self.editor = kwargs['editor']
        self.view = kwargs["view"]
        self._subwf_true_branch_model, self._subwf_true_branch_view = ControlFactory.construct("SubWorkflow",editor=self.editor,qt_parent=self.view, logical_parent=self.view.logical_parent,wf_root = self.wf_root)
        self._subwf_false_branch_model, self._subwf_false_branch_view = ControlFactory.construct("SubWorkflow",editor=self.editor,qt_parent=self.view, logical_parent=self.view.logical_parent,wf_root = self.wf_root)
        self.subwf_models = [self._subwf_true_branch_model, self._subwf_false_branch_model]
        self.subwf_views = [self._subwf_true_branch_view, self._subwf_false_branch_view]
        self.name = "Branch"
        self._condition = ""

    def set_condition(self, condition):
        self._condition = condition

    def get_condition(self):
        return self._condition

    def render_to_simple_wf(self, path_list, output_path_list, submitdir ,jobdir ,path , parent_ids):
        filesets = []
        transitions = []

        if jobdir == "":
            my_jobdir = self.name
        else:
            my_jobdir = "%s/%s" % (jobdir, self.name)

        if path == "":
            path = self.name
        else:
            path = "%s/%s" %(path,self.name)

        my_true_path_list = path_list + [self.name, "True"]
        my_false_path_list =  path_list + [self.name, "False"]
        output_path_list_true = output_path_list + [self.name,"True"]
        output_path_list_false = output_path_list + [self.name, "False"]

        sub_activities_true, sub_transitions_true, sub_toids_true = self._subwf_true_branch_model.render_to_simple_wf(my_true_path_list, output_path_list_true, submitdir,my_jobdir+ "/True",path = path + "/True/", parent_ids = ["temporary_connector"])
        sub_activities_false, sub_transitions_false, sub_toids_false = self._subwf_false_branch_model.render_to_simple_wf(
            my_false_path_list, output_path_list_false, submitdir, my_jobdir + "/False", path = path + "/False/", parent_ids=["temporary_connector"])
        sg_true = SubGraph(elements = WorkflowElementList(sub_activities_true),
                 graph = DirectedGraph(sub_transitions_true))
        sg_false = SubGraph(elements=WorkflowElementList(sub_activities_false),
                           graph=DirectedGraph(sub_transitions_false))

        mypass = WFPass()
        finish_uid = mypass.uid


        fe = IfGraph(finish_uid = finish_uid,
                     truegraph = sg_true,
                     falsegraph = sg_false,
                     true_final_ids = StringList(sub_toids_true),
                     false_final_ids = StringList(sub_toids_false),
                     condition = self._condition
        )

        toids = [fe.uid]
        for parent_id in parent_ids:
            transitions.append((parent_id, toids[0]))

        # We are now generating a break in this workflow. The break will be resolved (hopefully) once the FE runs.

        return [("IfGraph",fe),("WFPass", mypass)], transitions, [finish_uid]

    def assemble_variables(self, path):
        myvars = []
        for swfid,(swfm,truefalse) in enumerate(zip([self._subwf_true_branch_model, self._subwf_true_branch_model],["True", "False"])):
            truefalsepath = merge_path(path, self.name,truefalse)
            for var in swfm.assemble_variables(truefalsepath):
                myvars.append(var)
        return myvars

    def assemble_files(self,path):
        myfiles = []
        for swfid,(swfm,truefalse) in enumerate(zip([self._subwf_true_branch_model, self._subwf_true_branch_model],["True", "False"])):
            for otherfile in swfm.assemble_files(path):
                myfiles.append(linuxjoin(path, self.name, truefalse, otherfile))
        return myfiles

    def save_to_disk(self, foldername):
        attributes = {"name": self.name,
                      "type": "If",
                      "condition": self._condition}
        root = etree.Element("WFControl", attrib=attributes)
        true_xml = self._subwf_true_branch_model.save_to_disk(foldername)
        false_xml = self._subwf_false_branch_model.save_to_disk(foldername)
        true_xml.attrib["branch"] = "true"
        false_xml.attrib["branch"] = "false"
        root.append(true_xml)
        root.append(false_xml)

        return root

    def read_from_disk(self, full_foldername, xml_subelement):
        self.subwf_models = []
        for view in self.subwf_views:
            view.deleteLater()
        self.subwf_views = []
        attribs = xml_subelement.attrib
        assert attribs["type"] == "If"
        self._condition = attribs["condition"]
        print("Setting condition to", self._condition)


        for child in xml_subelement:
            if child.tag != "WFControl":
                continue
            if child.attrib["type"] != "SubWorkflow":
                continue
            subwfmodel,subwfview = ControlFactory.construct("SubWorkflow", qt_parent=self.view, logical_parent=self.view,editor=self.editor,wf_root = self.wf_root)
            name = child.attrib["name"]

            subwfview.setText(name)
            subwfmodel.read_from_disk(full_foldername=full_foldername,xml_subelement=child)
            if child.attrib["branch"] == "true":
                self._subwf_true_branch_model = subwfmodel
                self._subwf_true_branch_view = subwfview
            elif child.attrib["branch"] == "false":
                self._subwf_false_branch_model = subwfmodel
                self._subwf_false_branch_view = subwfview
        self.subwf_models = [self._subwf_true_branch_model, self._subwf_false_branch_model]
        self.subwf_views = [self._subwf_true_branch_view, self._subwf_false_branch_view]
        self.view.init_from_model()

class ParallelModel(WFItemModel):
    def __init__(self,*args,**kwargs):
        super(ParallelModel, self).__init__(*args, **kwargs)
        self.wf_root = kwargs["wf_root"]

        self.is_wano = False
        self.editor = kwargs['editor']
        self.view = kwargs["view"]
        self.numbranches = 1
        self.subwf_models = []
        self.subwf_views = []
        subwfmodel, subwfview = ControlFactory.construct("SubWorkflow",editor=self.editor,qt_parent=self.view, logical_parent=self.view.logical_parent,wf_root = self.wf_root)
        self.subwf_models.append(subwfmodel)
        self.subwf_views.append(subwfview)
        self.name = "Parallel"


    def render_to_simple_wf(self, path_list, output_path_list, submitdir, jobdir, path, parent_ids):

        """
        split_activity = WFtoXML.xml_split()
        splitid = split_activity.attrib["Id"]
        transitions = []
        transitions.append(split_activity)
        swfs = []
        """
        if jobdir == "":
            my_jobdir = self.name
        else:
            my_jobdir = "%s/%s" % (jobdir, self.name)
        if path == "":
            path = self.name
        else:
            path = "%s/%s" % (path, self.name)

        activities = []
        transitions = []
        toids = []
        for swf_id,swfm in enumerate(self.subwf_models):
            inner_jobdir = "%s/%d" % (my_jobdir,swf_id)
            inner_path = "%s/%d" % (path,swf_id)

            new_output_path_list = output_path_list + [self.name, str(swf_id)]
            new_path_list = path_list + [self.name, str(swf_id)]

            my_activities, my_transitions, my_toids = swfm.render_to_simple_wf(new_path_list, new_output_path_list, submitdir,inner_jobdir,path = inner_path, parent_ids = parent_ids)
            transitions += my_transitions
            activities += my_activities
            toids += my_toids

        return activities, transitions, toids

    def assemble_variables(self, path):
        myvars = []
        for swfid, swfm in enumerate(self.subwf_models):
            for var in swfm.assemble_variables(path):
                newpath = merge_path(path, "%s.%d"%(self.name,swfid),var)
                myvars.append(newpath)
        return myvars

    def add(self):
        subwfmodel, subwfview = ControlFactory.construct("SubWorkflow",editor=self.editor,qt_parent=self.view, logical_parent=self.view.logical_parent,wf_root = self.wf_root)
        self.subwf_models.append(subwfmodel)
        self.subwf_views.append(subwfview)

    def deletelast(self):
        if len(self.subwf_views) <= 1:
            return
        self.subwf_views[-1].deleteLater()
        self.subwf_views.pop()
        self.subwf_models.pop()

    def assemble_files(self,path):
        myfiles = []
        for swfid,swfm in enumerate(self.subwf_models):
            for otherfile in swfm.assemble_files(path):
                myfiles.append(linuxjoin(path, self.name, "%d"%swfid, otherfile))
        return myfiles

    def save_to_disk(self, foldername):
        attributes = {"name": self.name, "type": "Parallel"}
        root = etree.Element("WFControl", attrib=attributes)
        my_foldername = foldername
        # TODO revert changes in filesystem in case instantiate_in_folder fails
        #root.append(self.subwfmodel.save_to_disk(my_foldername))
        for swf in self.subwf_models:
            root.append(swf.save_to_disk(foldername))

        return root

    def read_from_disk(self, full_foldername, xml_subelement):
        self.subwf_models = []
        for view in self.subwf_views:
            view.deleteLater()
        self.subwf_views = []
        for child in xml_subelement:
            if child.tag != "WFControl":
                continue
            if child.attrib["type"] != "SubWorkflow":
                continue
            subwfmodel,subwfview = ControlFactory.construct("SubWorkflow", qt_parent=self.view, logical_parent=self.view,editor=self.editor,wf_root = self.wf_root)
            name = child.attrib["name"]

            subwfview.setText(name)
            subwfmodel.read_from_disk(full_foldername=full_foldername,xml_subelement=child)
            self.subwf_models.append(subwfmodel)
            self.subwf_views.append(subwfview)
        self.view.init_from_model()




class ForEachModel(WFItemModel):
    def __init__(self,*args,**kwargs):
        super(ForEachModel, self).__init__(*args, **kwargs)
        self.wf_root = kwargs["wf_root"]

        self.is_wano = False
        self.editor = kwargs['editor']
        self.view = kwargs["view"]
        self.itername = "ForEach_iterator"
        self.subwfmodel, self.subwfview = ControlFactory.construct("SubWorkflow",editor=self.editor,qt_parent=self.view, logical_parent=self.view.logical_parent,wf_root = self.wf_root)
        self.fileliststring = ""
        self.name = "ForEach"
        self._is_file_iterator = True
        self._is_multivar_iterator = False


    def set_is_file_iterator(self, true_or_false):
        self._is_file_iterator = true_or_false

    def set_filelist(self,filelist):
        self.fileliststring = filelist

    def assemble_variables(self, path):
        if path == "":
            mypath = "ForEach.${%s_ITER}"%self.itername
        else:
            mypath = "%s.ForEach.${%s_ITER}" % (path, self.itername)
        myvars = self.subwfmodel.assemble_variables(mypath)
        my_iterator = "${%s_ITER}"%self.itername
        myvars.append(my_iterator)
        myvalue = "${%s}"%self.itername
        myvars.append(myvalue)
        return myvars

    def render_to_simple_wf(self, path_list, output_path_list, submitdir ,jobdir ,path , parent_ids):
        filesets = []
        transitions = []

        if self._is_file_iterator:
            for myfile in self.fileliststring.split():

                gpath = "${STORAGE}/workflow_data/%s"%myfile
                #localfn = os.path.basename(myfile)
                #gpath = join(gpath,localfn)
                filesets.append(gpath)
        else:
            for myfile in self.fileliststring.split():
                filesets.append(myfile)

        if jobdir == "":
            my_jobdir = self.name
        else:
            my_jobdir = "%s/%s" % (jobdir, self.name)

        if path == "":
            path = self.name
        else:
            path = "%s/%s" %(path,self.name)

        my_path_list = path_list + [self.name]
        my_output_path_list = output_path_list + [self.name, "${" + self.itername.replace(" ","") + "_ITER}"]

        sub_activities, sub_transitions, sub_toids = self.subwfmodel.render_to_simple_wf(my_path_list, my_output_path_list, submitdir,my_jobdir,path = path, parent_ids = ["temporary_connector"])
        sg = SubGraph(elements = WorkflowElementList(sub_activities),
                 graph = DirectedGraph(sub_transitions))

        mypass = WFPass()
        finish_uid = mypass.uid

        if self._is_file_iterator:
            fe = ForEachGraph(subgraph = sg,
                              #parent_ids=StringList(parent_ids),
                              finish_uid = finish_uid,
                              iterator_name = self.itername,
                              iterator_files = StringList(filesets),
                              subgraph_final_ids = StringList(sub_toids)
            )
        elif self._is_multivar_iterator:
            fe = ForEachGraph(subgraph=sg,
                              # parent_ids=StringList(parent_ids),
                              finish_uid=finish_uid,
                              iterator_name=self.itername,
                              iterator_definestring=self.fileliststring,
                              subgraph_final_ids=StringList(sub_toids)
                              )
        else:
            fe = ForEachGraph(subgraph = sg,
                              #parent_ids=StringList(parent_ids),
                              finish_uid = finish_uid,
                              iterator_name = self.itername,
                              iterator_variables = StringList(filesets),
                              subgraph_final_ids = StringList(sub_toids)
            )

        toids = [fe.uid]
        for parent_id in parent_ids:
            transitions.append((parent_id, toids[0]))

        # We are now generating a break in this workflow. The break will be resolved (hopefully) once the FE runs.


        return [("ForEachGraph",fe),("WFPass", mypass)], transitions, [finish_uid]  #WFtoXML.xml_subwfforeach(IteratorName=self.itername,IterSet=filesets,SubWorkflow=swf,Id=muuid)

    def assemble_files(self,path):
        myfiles = []
        myfiles.append("${%s}" %(self.itername))
        for otherfile in self.subwfmodel.assemble_files(path):
            myfiles.append(linuxjoin(path, self.view.text(),"*",otherfile))
            myfiles.append(linuxjoin(path, self.view.text(), "${%s_ITER}"%self.itername, otherfile))
        return myfiles

    def save_to_disk(self, foldername):
        true_false = { True: "True", False: "False"}
        mytype = "ForEach"
        if self._is_multivar_iterator:
            mytype = "AdvancedFor"
        attributes = {"name": self.view.text(), "type": mytype, "is_file_iterator": true_false[self._is_file_iterator]}
        root = etree.Element("WFControl", attrib=attributes)
        my_foldername = foldername
        # TODO revert changes in filesystem in case instantiate_in_folder fails
        root.append(self.subwfmodel.save_to_disk(my_foldername))
        filelist = etree.SubElement(root,"FileList")
        for fn in self.fileliststring.split():
            fxml = etree.SubElement(filelist, "File")
            fxml.text = fn
            filelist.append(fxml)
        iter_xml = etree.SubElement(root,"IterName")
        iter_xml.text = self.itername
        return root

    def read_from_disk(self, full_foldername, xml_subelement):
        #TODO: missing save filelist
        #TODO: missing render
        try:
            is_file_iter = xml_subelement.attrib["is_file_iterator"]
            if is_file_iter == "True":
                self._is_file_iterator = True
            else:
                self._is_file_iterator = False
        except KeyError as e:
            self._is_file_iterator = True
        self.fileliststring = ""
        for child in xml_subelement:
            if child.tag == "FileList":
                for xml_ss in child:
                    self.fileliststring += "%s "%xml_ss.text
                continue
            if child.tag == "IterName":
                self.itername = child.text
                continue
            if child.tag != "WFControl":
                continue
            if child.attrib["type"] != "SubWorkflow":
                continue
            #self.subwfmodel,self.subwfview = ControlFactory.construct("SubWorkflow", qt_parent=self.view, logical_parent=self.view,editor=self.editor,wf_root = self.wf_root)
            name = child.attrib["name"]
            type = child.attrib["type"]

            self.subwfview.setText(name)
            self.subwfmodel.read_from_disk(full_foldername=full_foldername,xml_subelement=child)

        self.fileliststring = self.fileliststring[:-1]


class AdvancedForEachModel(ForEachModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = "AdvancedForEach"
        self.itername = "a,b"
        self.fileliststring = "zip([1,2],[3,4])"
        self.set_is_file_iterator(False)
        self._is_multivar_iterator = True


    def assemble_variables(self, path):
        if path == "":
            mypath = "AdvancedForEach.${%s_ITER}"%self.itername.replace(" ","")
        else:
            mypath = "%s.AdvancedForEach.${%s_ITER}" % (path, self.itername.replace(" ",""))

        myvars = self.subwfmodel.assemble_variables(mypath)
        iterators = self.itername.replace(" ","").split(",")
        myvars.append("${%s_ITER}"%(self.itername.replace(" ","")))
        for it in iterators:
            myvars.append("${%s}"%it)
            #myvars.append("${%s_ITER}" % it)
        return myvars

def merge_path(path, name, var):
    newpath = "%s.%s.%s" % (path, name, var)
    if newpath.startswith("."):
        newpath = newpath[1:]
    return newpath


class WFModel(object):
    def __init__(self, *args, **kwargs):
        """
         Workflow:
            Root:
              [ Element, Workflow, ControlElement ]
            ControlElement:
              [ Element, Workflow, ControlElement ]

        Every Element is a folder
         WorkflowName
            - Element-uuid
            - Workflow-uuid
            - ControlElement-uuid

        These are copies of the current wanos or workflows
        """
        self.editor = kwargs['editor']
        self.view = kwargs["view"]
        self.elements = [] # List of Elements,Workflows, ControlElements
        # Name of the saved folder
        self.elementnames = []
        self.foldername = None
        self.wf_name = "Unset"
        #Few Use Cases
        """
            Workflow containing Workflow:
            What happens if the (inner) workflow-base changes?
            The encapsulated workflow does not change. We might want to do that later, but not now.

            In other words:
            When an element is drawn into the workflow, a copy of the
                WaNo, Workflow, ControlElement is made
                & a unique Name + uuid is assigned
            When the element is closed, or the workflow is submitted, these are written to disk using the UUID
            WaNos are completely copied once they are instantiated.

            Data Format
            List of elements
            #element->Name -> Object
            Displayname should be Saved in Object
            #element.displayname i.e.. It really must be unique except for multicopies using for and while
            #it doesn't have to be unique among workflow nesting.
        """

    def get_root(self):
        return self

    def element_to_name(self,element):
        idx = self.elements.index(element)
        return self.elementnames[idx]

    def assemble_variables(self, path):
        myvars = []
        for myid, (ele, name) in enumerate(zip(self.elements, self.elementnames)):
            if ele.is_wano:
                for var in ele.get_variables():
                    newpath = merge_path(path,ele.name,var)
                    myvars.append(newpath)
            else:
                for myvar in ele.assemble_variables(path):
                    myvars.append(myvar)
        return myvars

    def render_to_simple_wf(self, submitdir,jobdir):
        activities = []
        transitions = []
        swfs = []
        #start = WFtoXML.xml_start()
        #parent_xml = etree.Element()

        path_list = []
        output_path_list = []
        fromids = ["0"]
        for myid, (ele, elename) in enumerate(zip(self.elements, self.elementnames)):
            if ele.is_wano:
                wano_dir = os.path.join(jobdir, self.element_to_name(ele))
                try:
                    os.makedirs(wano_dir)
                except OSError:
                    pass
                #stageout_basedir = "wanos/%s" % (elename)
                my_path_list = path_list.copy()
                jsdl, wem, other = ele.render(my_path_list, output_path_list, wano_dir, stageout_basedir=elename)
                wem.set_given_name(elename)
                mypath = "/".join(path_list + [elename])
                myoutputpath = "/".join(output_path_list + [elename])
                wem.set_path(mypath)
                wem.set_outputpath(myoutputpath)
                wem : WorkflowExecModule
                toids = [wem.uid]
                activities.append(["WorkflowExecModule",wem])
                for fromid in fromids:
                    for toid in toids:
                        transitions.append((fromid, toid))
            else:
                #only subworkflow remaining
                my_path_list = path_list.copy()
                my_activities, my_transitions,  toids = ele.render_to_simple_wf(my_path_list, output_path_list, submitdir,jobdir,path="", parent_ids = fromids)
                activities+=my_activities
                transitions += my_transitions

            #transition = WFtoXML.xml_transition(From=fromid, To=toid)
            #print((fromid,toid))

            fromids = toids

        wf = Workflow(elements = WorkflowElementList(activities),
                      graph = DirectedGraph( transitions),
                      name=self.wf_name,
                      storage="${BASEFOLDER}",
                      queueing_system="${QUEUE}"
                      )
        xml = etree.Element("Workflow")
        wf.to_xml(parent_element=xml)

        return xml


    #this function assembles all files relative to the workflow root
    #The files will be export to c9m:${WORKFLOW_ID}/the file name below
    # Here we also need to assemble all variables

    # Tomorrow: update the variable assembler here
    # Then, unbundle the qt stuff also from here if possible
    # Otherwise, just put the assemblers into parent classes
    # Otherwise  do a getitem function and use treeview
    # Assemble paths
    # Then, upload the workflow xml you get here and stop - Once up, render the workflow into simple xml on the server
    #  Is this enough?
    #  Add an in-path to all WorkflowElements (on the SSS side)
    #   The inpath can be written here and given like that - it should already contain workflow specific variables such as foreach
    #   Then we can use the variable filler


    def assemble_files(self,path):
        myfiles = []
        for myid,(ele,name) in enumerate(zip(self.elements,self.elementnames)):
            if ele.is_wano:
                for file in ele.wano_model.get_output_files():
                    fn = linuxjoin(name,"outputs",file)
                    myfiles.append(fn)
            else:
                for otherfile in ele.assemble_files(path=""):
                    myfiles.append(otherfile)

        return myfiles



    def save_to_disk(self,foldername):
        success = True
        self.wf_name = os.path.basename(foldername)
        self.foldername = foldername
        settings = WaNoSettingsProvider.get_instance()
        wdir = settings.get_value(SETTING_KEYS['workflows'])
        if wdir == '<embedded>':
            wdir = join(SimStackPaths.get_embedded_path(),"workflows")

        mydir = os.path.join(wdir,self.wf_name)
        try:
            os.makedirs(mydir)
        except OSError:
            pass

        root = etree.Element("root")
        #TODO revert changes in filesystem in case instantiate_in_folder fails
        for myid,(ele,name) in enumerate(zip(self.elements,self.elementnames)):
            if ele.is_wano:
                subxml = ele.get_xml()
                subxml.attrib["id"] = str(myid)
                subxml.attrib["name"] = name
                #print("Instantiating in folder: %s, wanocheat: %s"%(foldername,ele.wano[1]))
                success = ele.instantiate_in_folder(foldername)
                root.append(subxml)
                if not success:
                    break
            else:
                root.append(ele.save_to_disk(foldername))

        if success:
            xml_path = os.path.join(mydir,self.wf_name + ".xml")
            with open(xml_path,'w') as outfile:
                outfile.write(etree.tostring(root,encoding="unicode",pretty_print=True))
        else:
            print("Error while writing wano")
            raise Exception("This should be a custom exception")
        return success

    def read_from_disk(self,foldername):
        self.foldername = foldername
        self.wf_name = os.path.basename(foldername)
        xml_filename = os.path.join(foldername,os.path.basename(foldername)) + ".xml"
        tree = etree.parse(xml_filename)
        root = tree.getroot()
        for child in root:
            if child.tag == "WaNo":
                type = child.attrib["type"]
                name = child.attrib["name"]
                uuid = child.attrib["uuid"]
                myid = int(child.attrib["id"])
                #print(len(self.elements),myid)
                assert (myid == len(self.elements))
                wanofolder = os.path.join(foldername,"wanos",uuid)
                widget = WFWaNoWidget.instantiate_from_folder(wanofolder, type, parent=self.view)
                widget.setText(name)
                self.elements.append(widget)
                self.elementnames.append(name)
            elif child.tag == "WFControl":
                name = child.attrib["name"]
                type = child.attrib["type"]
                model, view = ControlFactory.construct(type, qt_parent=self.view, logical_parent=self.view,editor=self.editor,wf_root = self)
                self.elements.append(model)
                self.elementnames.append(name)
                view.setText(name)

                model.read_from_disk(full_foldername=foldername, xml_subelement=child)
        self.view.updateGeometry()

    def render(self, given_name):
        assert (self.foldername is not None)
        now = datetime.datetime.now()
        nowstr = now.strftime("%Y-%m-%d-%Hh%Mm%Ss")
        submitname = "%s-%s" %(nowstr, given_name)
        submitdir = os.path.join(self.foldername,"Submitted",submitname)
        counter = 0
        while os.path.exists(submitdir):
            time.sleep(1.1)
            now = datetime.datetime.now()
            nowstr = now.strftime("%Y-%m-%d-%Hh%Mn%Ss")
            submitname = "%s-%s" % (nowstr, given_name)
            submitdir = os.path.join(self.foldername, "Submitted", submitname)
            counter += 1
            if counter == 10:
                raise FileExistsError("Submit directory %s already exists."%submitdir)

        jobdir = os.path.join(submitdir,"workflow_data")


        try:
            os.makedirs(jobdir)
        except OSError:
            pass

        wf_xml = self.render_to_simple_wf(submitdir,jobdir)
        return SubmitType.WORKFLOW,submitdir,wf_xml

    def move_element_to_position(self, element, new_position):
        old_index = self.elements.index(element)

        if old_index != new_position:
            ele = self.elements.pop(old_index)
            ele_name = self.elementnames.pop(old_index)
            if old_index < new_position:
                new_position-=1
            self.elements.insert(new_position,ele)
            self.elementnames.insert(new_position, ele_name)

    def unique_name(self, oldbase):
        base = oldbase
        i = 1
        while base in self.elementnames:
            base = "%s_%d"%(oldbase,i)
            i+=1
        return base

    def add_element(self,element,pos = None):
        newname = self.unique_name(element.name)
        if newname != element.name:
            element.setText(newname)
        if pos is not None:
            self.elements.insert(pos,element)
            self.elementnames.insert(pos,newname)
        else:
            self.elements.append(element)
            self.elementnames.append(newname)
        element.view.show()

    def remove_element(self,element):
        myid = self.elements.index(element)
        self.elements.remove(element)
        del self.elementnames[myid]

    def openWaNoEditor(self,wanoWidget):
        self.editor.openWaNoEditor(wanoWidget)

    def removeElement(self, element):
        #print("Removing",element)
        self.remove_element(element)
        return



class SubWorkflowView(QtWidgets.QFrame):
    def __init__(self, *args, **kwargs):
        self.my_height = 50
        self.my_width = 300
        self.minimum_height = 50
        self.minimum_width = 300
        self.is_wano = False
        self.logical_parent = kwargs['logical_parent']
        parent = kwargs['qt_parent']
        super(SubWorkflowView, self).__init__(parent)
        self.setFrameStyle(QtWidgets.QFrame.Panel)
        self.setStyleSheet("""
                           QFrame {
                            border: 2px solid black;
                            border-radius: 4px;
                            padding: 2px;
                            background: %s
                            }
                                QPushButton {
                                 background-color: %s
                             }
                             QPushButton:hover {
                                 background-color: %s;

                             }


                           """ % (widgetColors['Control'],widgetColors['ButtonColor'],widgetColors['Control'])
                           )
        self.logger = logging.getLogger('WFELOG')
        self.setAcceptDrops(True)
        self.autoResize = False
        self.elementSkip = 20  # distance to skip between elements
        self.model = None
        #self.setFrameStyle(QtGui.QFrame.WinPanel | QtGui.QFrame.Sunken)
        self.setMinimumWidth(300)
        self.setMinimumWidth(100)
        self.dontplace = False
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

    def set_model(self,model):
        self.model = model

    def text(self):
        return self.model.name

    def setText(self,text):
        self.model.name = text

    def init_from_model(self):
        self.relayout()

    #Place elements places elements top down.
    def place_elements(self):
        self.my_width = self.minimum_width
        self.adjustSize()


        for model in self.model.elements:
            e = model.view
            self.my_width = max(self.my_width, e.width() + 50)

        self.adjustSize()

        dims = self.geometry()
        ypos = self.elementSkip / 2
        for model in self.model.elements:
            e = model.view
            e.setParent(self)


            e.adjustSize()
            xpos = (dims.width() - e.width()) / 2
            #xpos = dims.width()/2.0
            e.move(xpos, ypos)
            e.place_elements()
            ypos += e.height() + self.elementSkip

        self.my_height = ypos
        self.adjustSize()
        #self.setFixedHeight(max(ypos,self.parent().height()))
        if not self.dontplace:
            self.dontplace = True
            #self.logical_parent.place_elements()
        self.dontplace=False
        #if (ypos < 50):
        #    self.setFixedHeight(50)
        self.updateGeometry()
        return ypos

    def sizeHint(self):
        return QtCore.QSize(max(self.minimum_width,self.my_width),max(self.my_height,self.minimum_height))

    def relayout(self):
        self.model.get_root().view.relayout()
        #self.model.get_root().view.place_elements()
        #self.model.get_root().view.place_elements()
        #self.place_elements()

    #Manually paint the lines:
    def paintEvent(self, event):
        super(SubWorkflowView,self).paintEvent(event)

        painter = QtGui.QPainter(self)
        painter.setBrush(QtGui.QBrush(QtCore.Qt.blue))
        sy = self.elementSkip
        #print(len(self.model.elements))
        if len(self.model.elements)>1:
            e = self.model.elements[0].view
            sx = e.pos().x() + e.width()/2
            sy = e.pos().y() + e.height()
        for model in self.model.elements[1:]:
            b = model.view
            ey = b.pos().y()
            line = QtCore.QLine(sx,sy,sx,ey)
            painter.drawLine(line)
            sy = b.pos().y() + b.height()
        painter.end()

    def dragEnterEvent(self, e):
        e.accept()

    def _locate_element_above(self,position):
        ypos = 0
        if len(self.model.elements) <= 1:
            return 0
        for elenum,model in enumerate(self.model.elements):
            e = model.view
            ypos += e.height() + self.elementSkip
            if ypos > position.y():
                returnnum = elenum + 1
                if returnnum > 0:
                    return returnnum

        return len(self.model.elements)

    def dropEvent(self, e):
        position = e.pos()
        new_position = self._locate_element_above(position)
        ele = e.source()
        if isinstance(e.source(),WFWaNoWidget) or isinstance(e.source(),WFControlWithTopMiddleAndBottom):
            if e.source().parent() is self:
                self.model.move_element_to_position(e.source().model, new_position)
            else:

                sourceparent = e.source().parent()
                e.source().setParent(self)
                self.model.add_element(ele.model, new_position)
                sourceparent.removeElement(ele.model)

                ele.show()
                ele.raise_()
                ele.activateWindow()

        elif isinstance(e.source(),WFEWaNoListWidget):
            wfe = e.source()
            dropped = wfe.selectedItems()[0]
            wano = dropped.WaNo
            try:
                wd = WFWaNoWidget(wano.name,wano,self)
            except Exception as e:
                tb = traceback.format_exc().replace("\n","\n<br/>")
                messageboxtext = f"<H3>Encountered error when inserting WaNo.</H3>\n\n Error was: {e}\n <hr/>" \
                                 f"<it>Trace: {tb}</it>"
                QtWidgets.QMessageBox.about(None, "Exception in WaNo construction", messageboxtext)
                return
            self.model.add_element(wd,new_position)
            #Show required for widgets added after
            wd.show()

        elif isinstance(e.source(),WFEListWidget):
            wfe = e.source()
            dropped = wfe.selectedItems()[0]
            name = dropped.text()
            model,view = ControlFactory.construct(name,qt_parent=self,logical_parent=self,editor=self.model.editor,wf_root = self.model.wf_root)
            self.model.add_element(model,new_position)


        else:
            print("Type %s not yet accepted by dropevent, please implement"%(e.source()))
            return
        e.setDropAction(QtCore.Qt.MoveAction)
        self.relayout()
        """
        position = e.pos()
        new_position = self._locate_element_above(position)
        ele = e.source()
        if isinstance(e.source(),WFWaNoWidget) or isinstance(e.source(),WFControlWithTopMiddleAndBottom):
            if e.source().parent() is self:
                self.model.move_element_to_position(e.source().model, new_position)

            else:
                self.model.add_element(ele.model, new_position)
                ele.parent().removeElement(ele.model)
                ele.show()
                ele.raise_()
                ele.activateWindow()


        #elif isinstance(e.source(),WFControlWithTopMiddleAndBottom):
        #    self.model.move_element_to_position(e.source(), new_position)

        elif isinstance(e.source(),WFEWaNoListWidget):
            wfe = e.source()
            dropped = wfe.selectedItems()[0]
            wano = dropped.WaNo
            wd = WFWaNoWidget(wano[0],wano,self)
            ##self.model.add_element(new_position,wd)
            self.model.add_element(wd,new_position)
            #Show required for widgets added after
            wd.show()

        elif isinstance(e.source(),WFEListWidget):
            wfe = e.source()
            dropped = wfe.selectedItems()[0]
            name = dropped.text()
            model,view = ControlFactory.construct(name,qt_parent=self,logical_parent=self,editor=self.model.editor,wf_root = self.model)
            self.model.add_element(model,new_position)


        else:
            print("Type %s not yet accepted by dropevent, please implement"%(e.source()))
            return
        e.setDropAction(QtCore.Qt.MoveAction)
        self.relayout()
        """

        """
        print("In subwf drop")
        position = e.pos()
        new_position = self._locate_element_above(position)
        ele = e.source()
        if type(e.source()) is WFWaNoWidget:
            if e.source().model.parent() is self:
                self.model.move_element_to_position(e.source().model, new_position)

            else:
                #e.source().model.parent().removeElement(ele.model)
                #self.model.add_element(ele.model, new_position)
                self.model.add_element(ele.model, new_position)
                e.source().model.parent().removeElement(ele.model)
                ele.show()
                ele.raise_()
                ele.activateWindow()

        elif type(e.source()) is WFControlWithTopMiddleAndBottom:
            self.model.move_element_to_position(e.source().model, new_position)

        elif type(e.source()) is WFEWaNoListWidget:
            wfe = e.source()
            dropped = wfe.selectedItems()[0]
            wano = dropped.WaNo
            wd = WFWaNoWidget(wano[0],wano,self)
            ##self.model.add_element(new_position,wd)
            self.model.add_element(wd,new_position)
            #Show required for widgets added after
            wd.show()

        elif type(e.source()) is WFEListWidget:
            wfe = e.source()
            dropped = wfe.selectedItems()[0]
            name = dropped.text()
            model, view = ControlFactory.construct(name, qt_parent=self, logical_parent=self, editor=self.model.editor,
                                                   wf_root=self.model)
            self.model.add_element(view, new_position)
        else:
            print("Type %s not yet accepted by dropevent, please implement"%(e.source()))
            return
        e.setDropAction(QtCore.Qt.MoveAction)

        self.relayout()
        """

    def openWaNoEditor(self,wanoWidget):
        self.model.openWaNoEditor(wanoWidget)


    def removeElement(self, element):
        self.model.removeElement(element)
        self.relayout()


class WorkflowView(QtWidgets.QFrame):
    def __init__(self, *args, **kwargs):
        parent = kwargs['qt_parent']
        super(WorkflowView, self).__init__(parent)

        self.setStyleSheet("background: " + widgetColors['Base'])
        self.logger = logging.getLogger('WFELOG')
        self.setAcceptDrops(True)
        self.autoResize = False
        self.myName = "AbstractWFTabsWidget"
        self.elementSkip = 20  # distance to skip between elements
        self.model = None
        self.setFrameStyle(QtWidgets.QFrame.WinPanel | QtWidgets.QFrame.Sunken)
        self.setMinimumWidth(300)
        self.background_drawn = True
        self.enable_background(True)
        self.dont_place = False

    def enable_background(self,on):
        style_sheet_without_background = "QFrame { background-color: " + widgetColors['MainEditor'] + """ ;
            %s
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-position: center;  
            }
        """
        if on:
            self.background_drawn = True
            script_path = os.path.dirname(os.path.realpath(__file__))
            media_path = os.path.join(script_path, "..", "Media")
            imagepath = os.path.join(media_path, "Logo_NanoMatch200.png")
            imagepath = imagepath.replace("\\","/")
            background_sheet = style_sheet_without_background % "background-image: url(\"%s\") ;" % imagepath
            self.setStyleSheet(background_sheet)
        else:
            self.background_drawn = False
            self.setStyleSheet(style_sheet_without_background % "")


    def set_model(self,model):
        self.model = model

    def init_from_model(self):
        self.relayout()

    #Place elements places elements top down.
    def place_elements(self):
        if len(self.model.elements) == 0:
            self.enable_background(True)
            return

        if self.background_drawn:
            self.enable_background(False)

        self.adjustSize()
        dims = self.geometry()

        #print(dims)
        ypos = 0
        if not self.dont_place:
            self.dont_place = True
            ypos = self.elementSkip / 2
            for model in self.model.elements:
                e = model.view
                e.setParent(self)
                e.adjustSize()
                xpos = (dims.width() - e.width()) / 2
                #print("WIDTH ",e.width())
                #print("HEIGHT ", e.height())
                #print(xpos,ypos)
                e.move(xpos, ypos)
                e.place_elements()
                ypos += e.height() + self.elementSkip

            self.setFixedHeight(max(ypos,self.parent().height()))
            self.adjustSize()

        self.dont_place = False
        self.updateGeometry()
        return ypos

    def relayout(self):
        # Relayouting twice (once for the kids to specify their correct size and ones for the parents to catch up
        # This is inherently flawed, because if the recursion depth grows and grows, you need more and more updates
        #
        self.place_elements()
        self.place_elements()
        self.place_elements()
        self.updateGeometry()

        #self.place_elements()

    #Manually paint the lines:
    def paintEvent(self, event):
        super(WorkflowView,self).paintEvent(event)
        painter = QtGui.QPainter(self)
        painter.setBrush(QtGui.QBrush(QtCore.Qt.blue))
        sy = self.elementSkip
        #print(len(self.model.elements))
        if len(self.model.elements)>1:
            e = self.model.elements[0].view
            sx = e.pos().x() + e.width()/2
            sy = e.pos().y() + e.height()
        for model in self.model.elements[1:]:
            b = model.view
            ey = b.pos().y()
            line = QtCore.QLine(sx,sy,sx,ey)
            painter.drawLine(line)
            sy = b.pos().y() + b.height()
        painter.end()

    def dragEnterEvent(self, e):
        e.accept()

    def _locate_element_above(self,position):
        ypos = 0
        if len(self.model.elements) <= 1:
            return 0
        for elenum,model in enumerate(self.model.elements):
            e = model.view
            ypos += e.height() + self.elementSkip
            if ypos > position.y():
                returnnum = elenum + 1
                if returnnum > 0:
                    return returnnum

        return len(self.model.elements)

    def dropEvent(self, e):
        position = e.pos()
        new_position = self._locate_element_above(position)
        ele = e.source()
        if isinstance(e.source(),WFWaNoWidget) or isinstance(e.source(),WFControlWithTopMiddleAndBottom):
            if e.source().parent() is self:
                self.model.move_element_to_position(e.source().model, new_position)

            else:
                sourceparent = e.source().parent()
                e.source().setParent(self)
                self.model.add_element(ele.model, new_position)
                sourceparent.removeElement(ele.model)
                ele.show()
                ele.raise_()
                ele.activateWindow()

        elif isinstance(e.source(),WFEWaNoListWidget):
            wfe = e.source()
            dropped = wfe.selectedItems()[0]
            wano : WaNoListEntry = dropped.WaNo
            try:
                wd = WFWaNoWidget(wano.name,wano,self)
            except Exception as e:
                tb = traceback.format_exc().replace("\n","\n<br/>")
                messageboxtext = f"<H3>Encountered error when inserting WaNo.</H3>\n\n Error was: {e}\n <hr/>" \
                                 f"<it>Trace: {tb}</it>"
                QtWidgets.QMessageBox.about(None, "Exception in WaNo construction", messageboxtext)
                return
            ##self.model.add_element(new_position,wd)
            self.model.add_element(wd,new_position)
            #Show required for widgets added after
            wd.show()

        elif isinstance(e.source(),WFEListWidget):
            wfe = e.source()
            dropped = wfe.selectedItems()[0]
            name = dropped.text()
            model,view = ControlFactory.construct(name,qt_parent=self,logical_parent=self,editor=self.model.editor,wf_root = self.model)
            self.model.add_element(model,new_position)


        else:
            print("Type %s not yet accepted by dropevent, please implement"%(e.source()))
            return
        e.setDropAction(QtCore.Qt.MoveAction)
        self.relayout()

    def openWaNoEditor(self,wanoWidget):
        self.model.openWaNoEditor(wanoWidget)

    def removeElement(self, element):
        self.model.removeElement(element)
        self.relayout()


class WFTabsWidget(QtWidgets.QTabWidget):
    workflow_saved = Signal(bool, str, name="WorkflowSaved")
    changedFlag = False

    def __init__(self, parent):
        super(WFTabsWidget, self).__init__(parent)

        self.logger = logging.getLogger('WFELOG')

        self.acceptDrops()
        self.setAcceptDrops(True)
        #self.curFile = WFFileName()
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.closeTab)

        #WFWorkflowWidget(parent,self)

        #####self.wf.embeddedIn = self   # this is the widget that needs to be reiszed when the main layout widget resizes
        #####self.addTab(selfg.wf,self.curFile.name)
        #####self.setMinimumSize(self.wf.width()+25,600) # widget with scrollbar
        self.editor = parent

        scroll,_,_ = self.createNewEmptyWF()

        self.addTab(scroll, "Untitled")
        self.relayout()
        self.currentChanged.connect(self._tab_changed)

        ####bb = self.tabBar().tabButton(0, QtGui.QTabBar.RightSide)
        ####bb.resize(0, 0)
    def createNewEmptyWF(self):
        scroll = QtWidgets.QScrollArea(self)
        wf = WorkflowView(qt_parent=scroll)
        wf_model = WFModel(editor=self.editor,view=wf)
        wf.set_model(wf_model)
        wf.init_from_model()
        scroll.setWidget(wf)
        scroll.setMinimumWidth(300)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll.setWidgetResizable(True)
        return scroll,wf_model,wf

    def clear(self):
        #print ("Workflow has changed ? ",WFWorkflowWidget.changedFlag)
        if self.changedFlag:
            reply = QtWidgets.QMessageBox(self)
            reply.setText("The document has been modified.")
            reply.setInformativeText("Do you want to save your changes?")
            reply.setStandardButtons(QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel)
            reply.setDefaultButton(QtWidgets.QMessageBox.Save)
            ret = reply.exec_()

            if ret == QtWidgets.QMessageBox.Cancel:
                return
            if ret == QtWidgets.QMessageBox.Save:
                self.save()
        self.wf.clear()
        self.changedFlag = False
        self.tabWidget.setTabText(0,'Untitled')

    def markWFasChanged(self):
        print ("mark as changed")

    def run(self):
        name = self.tabText(self.currentIndex())
        if name == "Untitled":
            #FIXME this should be a custom exception. It should also be caught as Custom in WFEA
            raise FileNotFoundError("Please save your workflow first")

        self.save()
        #name,jobtype,directory,wf_xml = editor.run()

        jobtype,directory,workflow_xml = self.currentWidget().widget().model.render(given_name = name)
        return name,jobtype,directory,workflow_xml

    def currentTabText(self):
        myindex = self.currentIndex()
        return self.tabText(myindex)

    def save(self):
        if self.currentTabText() == 'Untitled':
            return self.saveAs()
        else:
            settings = WaNoSettingsProvider.get_instance()
            workflow_path = settings.get_value(SETTING_KEYS["workflows"])
            if workflow_path == '<embedded>':
                workflow_path = join(SimStackPaths.get_embedded_path(),"workflows")
            foldername = self.currentTabText()
            workflow_path = Path(workflow_path)
            fullpath = workflow_path / foldername
            return self.saveFile(fullpath)

    illegal_chars = r"<>|\#~*´`"
    def _contains_illegal_chars(self, wfname):

        if any((c in self.illegal_chars) for c in wfname):
            return True
        return False

    def saveAs(self):
        foldername,ok = QtWidgets.QInputDialog.getText(self, self.tr("Specify Workflow Name"),
                                     self.tr("Name"), QtWidgets.QLineEdit.Normal,
                                     "WorkflowName")

        if not ok:
            return False

        if self._contains_illegal_chars(foldername):
            messageboxtext = "Workflowname was %s. It cannot contain the following characters: %s"%(foldername,self.illegal_chars)
            QtWidgets.QMessageBox.critical(None, "Workflowname invalid", messageboxtext)
            return False


        settings = WaNoSettingsProvider.get_instance()
        workflow_path = settings.get_value(SETTING_KEYS["workflows"])
        if workflow_path == '<embedded>':
            workflow_path = join(SimStackPaths.get_embedded_path(),"workflows")
        workflow_path = Path(workflow_path)
        fullpath = workflow_path / foldername

        if fullpath.exists():
            message = QtWidgets.QMessageBox.question(self,"Path already exists", "Path %s already exists? Old contents will be removed." %fullpath,QtWidgets.QMessageBox.Yes|QtWidgets.QMessageBox.Cancel)
            if message == QtWidgets.QMessageBox.Cancel:
                return False
            else:
                pass
                #shutil.rmtree(fullpath)

        return self.saveFile(fullpath)

    def open(self):
        fileName, filtr = QtWidgets.QFileDialog(self).getOpenFileName(self,'Open Workflow','.','xml (*.xml *.xm)')
        if fileName:
            print ("Loading Workflow from File:",fileName)
            self.clear()
            self.loadFile(fileName)

    def get_index(self,name):
        for i in range(0,self.count()):
            if self.tabText(i) == name:
                return i

        return -1

    def _tab_changed(self):
        self.relayout()

    def openWorkFlow(self,workFlow):
        index   = self.get_index(workFlow.name) if not workFlow is None else -1
        #name    = self.curFile.name
        if index >= 0:
            self.setCurrentIndex(index)
            return

        scroll, model, view = self.createNewEmptyWF()
        if not workFlow is None:
            name = workFlow.name
            model.read_from_disk(workFlow.workflow)
        else:
            name = "Untitled"
        self.addTab(scroll, name)
        view.relayout()
        self.relayout()
        self.setCurrentIndex(self.count()-1)

    def closeTab(self,e):
        # this works recursively
        if self.parent().lastActive != None:
            # close wano editor
            self.parent().wanoEditor.deleteClose()
        self.removeTab(e)

    def relayout(self):
        if self.count() == 0:
            self.openWorkFlow(None)
        self.currentWidget().widget().relayout()

    # Executed everytime the widget is shown / hidden, etc.
    # Required to have correct initial layout
    def showEvent(self,event):
        super(WFTabsWidget,self).showEvent(event)
        self.relayout()

    def saveFile(self,folder):
        #widget is scroll
        success = self.currentWidget().widget().model.save_to_disk(folder)
        #self.wf_model.save_to_disk(folder)
        self.setTabText(self.currentIndex(),os.path.basename(folder))
        #print (type(self.editor.parent()))
        self.workflow_saved.emit(success, str(folder))

    #def sizeHint(self):
    #    return QtCore.QSize(500,500)


#
#  editor is the workflow editor that can open/close the WaNo editor
#
class WFFileName:
    def __init__(self):
        self.dirName = '.'
        self.name    = "Untitled"
        self.ext     = 'xml'
    def fullName(self):
        return os.path.join(self.dirName , self.name + '.' + self.ext)


class WFControlWithTopMiddleAndBottom(QtWidgets.QFrame,DragDropTargetTracker):
    def __init__(self,*args,**kwargs):
        parent = kwargs['qt_parent']
        self.logical_parent = kwargs["logical_parent"]
        super(WFControlWithTopMiddleAndBottom,self).__init__(parent)
        self.manual_init()
        #self.editor = kwargs["editor"]
        self.set_style()
        #TIMO: Try this off later, it's not required imho
        self.setAcceptDrops(False)
        self.model = None
        self.vbox = QtWidgets.QVBoxLayout(self)
        self.show()
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.initialized = False

    def _mockline(self):
        line = QtWidgets.QFrame(self)
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        line.setLineWidth(2)
        return line

    def mouseMoveEvent(self, e):
        return self.mouseMoveEvent_feature(e)

    def fill_layout(self):
        topwidget = self.get_top_widget()
        if topwidget is not None:
            self.vbox.addWidget(topwidget)
        self.middlewidget = self.get_middle_widget()
        if self.middlewidget is not None:
            self.vbox.addWidget(self.middlewidget)
        bottomlayout = self.get_bottom_layout()
        if bottomlayout is not None:
            self.vbox.addLayout(bottomlayout)

    def init_from_model(self):
        if not self.initialized:
            self.fill_layout()
            self.initialized = True
        #self.setLayout(self.vbox)

    @abc.abstractmethod
    def place_elements(self):
        pass

    @abc.abstractmethod
    def get_top_layout(self):
        return None

    @abc.abstractmethod
    def get_middle_layout(self):
        return None

    @abc.abstractmethod
    def get_bottom_layout(self):
        return None

    def set_style(self):
        self.setFrameStyle(QtWidgets.QFrame.Panel)
        self.setStyleSheet("""
                           QFrame {
                            border: 2px solid black;
                            border-radius: 4px;
                            padding: 2px;
                            background: %s;
                            }
                                QPushButton {
                                 background-color: %s
                             }
                             QPushButton:hover {
                                 background-color: %s;

                             }
                           """ % ("#FFFFFF",widgetColors['ButtonColor'],widgetColors['Control'])
                           #""" % (widgetColors['Control'],widgetColors['ButtonColor'],widgetColors['Control'])
                           )

    def set_model(self, model):
        self.model = model

    def text(self):
        return self.model.name

    def setText(self, text):
        self.model.name = text

class AdvancedForEachView(WFControlWithTopMiddleAndBottom):
    def __init__(self,*args,**kwargs):
        super(AdvancedForEachView,self).__init__(*args,**kwargs)
        self.dontplace = False
        self.is_wano = False

    def get_top_widget(self):
        self.topwidget = QtWidgets.QWidget()
        self.topLineLayout = QtWidgets.QHBoxLayout()
        self.topwidget.setLayout(self.topLineLayout)
        self._for_label = QtWidgets.QLabel("for")
        self.topLineLayout.addWidget(self._for_label)
        self._in_label = QtWidgets.QLabel("in")
        self.itername_widget = QtWidgets.QLineEdit('a,b')
        self.itername_widget.editingFinished.connect(self._on_line_edit)
        self.topLineLayout.addWidget(self.itername_widget)
        self.topLineLayout.addWidget(self._in_label)
        self.list_of_variables = QtWidgets.QLineEdit('zip([1,2,3],[4,5,6]')
        self.list_of_variables.editingFinished.connect(self.line_edited)
        self.topLineLayout.addWidget(self.list_of_variables)
        #self._global_import_button = QtWidgets.QPushButton(QtGui.QIcon.fromTheme("insert-object"), "")
        #self._global_import_button.clicked.connect(self.open_remote_importer)
        #self.topLineLayout.addWidget(self._global_import_button)
        return self.topwidget

    def open_remote_importer(self):
        varpaths = self.model.wf_root.assemble_variables("")
        mydialog = RemoteImporterDialog(varname="Import variable \"%s\" from:" % self.model.name,
                                        importlist=varpaths)
        mydialog.setModal(True)
        mydialog.exec()
        result = mydialog.result()
        if mydialog.result() == True:
            choice = mydialog.getchoice()
            self.model.set_filelist(choice)
            self.list_of_variables.setText(choice)
            self.model.set_is_file_iterator(False)
        else:
            pass

    def init_from_model(self):
        super(AdvancedForEachView,self).init_from_model()
        self.list_of_variables.setText(self.model.fileliststring)
        self.itername_widget.setText(self.model.itername)

    def _on_line_edit(self):
        self.model.itername = self.itername_widget.text().replace(" ","")

    def line_edited(self):

        files = self.list_of_variables.text()
        self.model.set_filelist(files)

    def get_middle_widget(self):
        return self.model.subwfview

    def sizeHint(self):
        if self.model is not None:
            size = self.model.subwfview.sizeHint() + QtCore.QSize(25,80)
            if size.width() < 300:
                size.setWidth(300)
            return size
        else:
            return QtCore.QSize(500,100)

    def place_elements(self):
        if not self.dontplace:
            self.dontplace = True
            if self.model is not None:
                self.init_from_model()
                self.model.subwfview.place_elements()
            self.adjustSize()
        self.dontplace=False
        self.updateGeometry()


class ForEachView(WFControlWithTopMiddleAndBottom):
    def __init__(self,*args,**kwargs):
        super(ForEachView,self).__init__(*args,**kwargs)
        self.dontplace = False
        self.is_wano = False

    def get_top_widget(self):
        self.topwidget = QtWidgets.QWidget()
        self.topLineLayout = QtWidgets.QHBoxLayout()
        self.topwidget.setLayout(self.topLineLayout)
        #b.clicked.connect(self.toggleVisible)
        self.itername_widget = QtWidgets.QLineEdit('Iterator Name')
        self.itername_widget.editingFinished.connect(self._on_line_edit)
        self.topLineLayout.addWidget(self.itername_widget)
        self.list_of_variables = QtWidgets.QLineEdit('')
        self.topLineLayout.addWidget(self.list_of_variables)
        self.open_variables = QtWidgets.QPushButton(QtGui.QIcon.fromTheme("drive-removable-media"),"")
        self.open_variables.clicked.connect(self.open_remote_importer_files)
        #self.open_variables = MultiselectDropDownList(self, text="Import")
        #self.open_variables.connect_workaround(self.load_wf_files)
        #self.open_variables.itemSelectionChanged.connect(self.on_wf_file_change)
        self._global_import_button = QtWidgets.QPushButton(QtGui.QIcon.fromTheme("insert-object"),"")
        self._global_import_button.clicked.connect(self.open_remote_importer)
        self.topLineLayout.addWidget(self._global_import_button)
        #self.open_variables.itemSelectionChanged.connect(self.onItemSelectionChange)
        #self.open_variables.connect_workaround(self._load_variables)
        self.topLineLayout.addWidget(self.open_variables)
        return self.topwidget

    def open_remote_importer(self):
        varpaths = self.model.wf_root.assemble_variables("")
        mydialog = RemoteImporterDialog(varname="Import variable \"%s\" from:" % self.model.name,
                                        importlist=varpaths)
        mydialog.setModal(True)
        mydialog.exec()
        result = mydialog.result()
        if mydialog.result() == True:
            choice = mydialog.getchoice()
            self.model.set_filelist(choice)
            self.list_of_variables.setText(choice)
            self.model.set_is_file_iterator(False)
        else:
            pass


    def open_remote_importer_files(self):
        varpaths = self.model.wf_root.assemble_files("")
        from WaNo.view.RemoteImporterDialog import RemoteImporterDialog
        mydialog = RemoteImporterDialog(varname ="Import file", importlist = varpaths, window_title="Workflow File Importer")
        mydialog.setModal(True)
        mydialog.exec_()
        result = mydialog.result()
        if mydialog.result() == True:
            choice = mydialog.getchoice()
            self.model.set_filelist(choice)
            self.list_of_variables.setText(choice)
            self.model.set_is_file_iterator(True)
        else:
            pass

    def init_from_model(self):
        super(ForEachView,self).init_from_model()
        self.list_of_variables.setText(self.model.fileliststring)
        self.itername_widget.setText(self.model.itername)

    def _on_line_edit(self):
        self.model.itername = self.itername_widget.text()

    def load_wf_files(self):
        wf = self.model.wf_root
        importable_files = wf.assemble_files("")
        self.open_variables.set_items(importable_files)
        self.model.set_is_file_iterator(True)

    def on_wf_file_change(self):
        self.list_of_variables.setText(" ".join(self.open_variables.get_selection()))
        self.line_edited()

    def line_edited(self):
        files = self.list_of_variables.text()
        self.model.set_filelist(files)

    def get_middle_widget(self):
        return self.model.subwfview

    def sizeHint(self):
        if self.model is not None:
            size = self.model.subwfview.sizeHint() + QtCore.QSize(25,80)
            if size.width() < 300:
                size.setWidth(300)
            return size
        else:
            return QtCore.QSize(200,100)

    def place_elements(self):
        if not self.dontplace:
            self.dontplace = True
            if self.model is not None:
                self.init_from_model()
                self.model.subwfview.place_elements()
            self.adjustSize()
        self.dontplace=False
        self.updateGeometry()


class ParallelView(WFControlWithTopMiddleAndBottom):
    def __init__(self,*args,**kwargs):
        super(ParallelView,self).__init__(*args,**kwargs)
        self.dontplace = False
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.is_wano = False

    def add_new(self):
        self.model.add()
        self.relayout()

    def relayout(self):
        self.model.wf_root.view.relayout()

    def delete(self):
        self.model.deletelast()
        self.relayout()

    def get_top_widget(self):
        tw = QtWidgets.QWidget()
        hor_layout = QtWidgets.QHBoxLayout()
        a = QtWidgets.QPushButton('Add additional parallel pane')
        a.clicked.connect(self.add_new)
        b = QtWidgets.QPushButton('Remove pane')
        b.clicked.connect(self.delete)
        hor_layout.addWidget(a)
        hor_layout.addWidget(b)
        tw.setLayout(hor_layout)
        return tw

    def init_from_model(self):
        super(ParallelView,self).init_from_model()
        for view in self.model.subwf_views:
            self.splitter.addWidget(view)

    def get_middle_widget(self):
        return self.splitter

    def sizeHint(self):

        if self.model is not None:
            maxheight = 0
            width = 0
            for v in self.model.subwf_views:
                sh = v.sizeHint()
                maxheight = max(maxheight,sh.height())
                width += sh.width()

            size = QtCore.QSize(width,maxheight)
            size += QtCore.QSize(50,75)
            if size.width() < 300:
                size.setWidth(300)
            return size
        else:
            return QtCore.QSize(200,100)

    def place_elements(self):
        if not self.dontplace:
            self.dontplace = True
            if self.model is not None:
                self.init_from_model()

                #self.model.subwfview.place_elements()
                for view in self.model.subwf_views:
                    view.place_elements()

            #self.parent().place_elements()
            self.dontplace=False
        self.updateGeometry()


class IfView(WFControlWithTopMiddleAndBottom):
    def __init__(self,*args,**kwargs):
        super(IfView,self).__init__(*args,**kwargs)
        self.dontplace = False
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.is_wano = False

    def add_new(self):
        self.model.add()
        self.relayout()

    def relayout(self):
        self.model.wf_root.view.relayout()

    def delete(self):
        self.model.deletelast()
        self.relayout()

    def _on_line_edit(self):
        self.model.set_condition(self.list_of_variables.text())

    def get_top_widget(self):
        self.topwidget = QtWidgets.QWidget()
        self.topLineLayout = QtWidgets.QHBoxLayout()
        self.topwidget.setLayout(self.topLineLayout)
        #b.clicked.connect(self.toggleVisible)
        self._condition = QtWidgets.QLabel("Condition")
        self.topLineLayout.addWidget(self._condition)
        self.list_of_variables = QtWidgets.QLineEdit('')
        self.list_of_variables.editingFinished.connect(self._on_line_edit)
        self.topLineLayout.addWidget(self.list_of_variables)
        self._global_import_button = QtWidgets.QPushButton(QtGui.QIcon.fromTheme("insert-object"),"")
        self._global_import_button.clicked.connect(self.open_remote_importer)
        self.topLineLayout.addWidget(self._global_import_button)
        #self.open_variables.itemSelectionChanged.connect(self.onItemSelectionChange)
        #self.open_variables.connect_workaround(self._load_variables)
        return self.topwidget

    def open_remote_importer(self):
        varpaths = self.model.wf_root.assemble_variables("")
        mydialog = RemoteImporterDialog(varname="Import variable \"%s\" from:" % self.model.name,
                                        importlist=varpaths)
        mydialog.setModal(True)
        mydialog.exec()
        result = mydialog.result()
        if mydialog.result() == True:
            choice = mydialog.getchoice()
            self.model.set_condition(choice)
            self.list_of_variables.setText(choice)
        else:
            pass

    def init_from_model(self):
        super(IfView,self).init_from_model()
        for view in self.model.subwf_views:
            self.splitter.addWidget(view)
        self.list_of_variables.setText(self.model._condition)

    def get_middle_widget(self):
        return self.splitter

    def sizeHint(self):

        if self.model is not None:
            maxheight = 0
            width = 0
            for v in self.model.subwf_views:
                sh = v.sizeHint()
                maxheight = max(maxheight,sh.height())
                width += sh.width()

            size = QtCore.QSize(width,maxheight)
            size += QtCore.QSize(50,75)
            if size.width() < 300:
                size.setWidth(300)
            return size
        else:
            return QtCore.QSize(200,100)

    def place_elements(self):
        if not self.dontplace:
            self.dontplace = True
            if self.model is not None:
                self.init_from_model()

                #self.model.subwfview.place_elements()
                for view in self.model.subwf_views:
                    view.place_elements()

            #self.parent().place_elements()
            self.dontplace=False
        self.updateGeometry()

class VariableView(WFControlWithTopMiddleAndBottom):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_wano = False
        self.dontplace = False
        self._middle_widget = QtWidgets.QWidget()

    def _on_line_edit(self):
        self.model.set_varname(self._varname_widget.text())

    def _on_varequation_line_edit(self):
        self.model.set_varequation(self._varequation_widget.text())

    def get_top_widget(self):
        self.topwidget = QtWidgets.QWidget()
        self.topLineLayout = QtWidgets.QHBoxLayout()
        self.topwidget.setLayout(self.topLineLayout)

        self._varname_widget = QtWidgets.QLineEdit('Variable Name')
        self._varname_widget.editingFinished.connect(self._on_line_edit)
        self._varequation_widget = QtWidgets.QLineEdit('Equation')
        self._varequation_widget.editingFinished.connect(self._on_varequation_line_edit)

        # We define two functors to only have a single open_remote_importer callback function.
        open_remote_importer_func_varname = lambda: self.open_remote_importer(target_function_view = self._varname_widget.setText,
                                                                             target_function_model = self.model.set_varname)
        self._varname_import_button = QtWidgets.QPushButton(QtGui.QIcon.fromTheme("insert-object"), "")
        self._varname_import_button.clicked.connect(open_remote_importer_func_varname)
        self.topLineLayout.addWidget(self._varname_widget)
        self.topLineLayout.addWidget(self._varname_import_button)

        open_remote_importer_func_varequation = lambda: self.open_remote_importer(target_function_view = self._varequation_widget.setText,
                                                target_function_model = self.model.set_varequation)
        self.topLineLayout.addWidget(self._varequation_widget)
        self._global_import_button = QtWidgets.QPushButton(QtGui.QIcon.fromTheme("insert-object"),"")
        self._global_import_button.clicked.connect(open_remote_importer_func_varequation)
        self.topLineLayout.addWidget(self._global_import_button)

        return self.topwidget

    def init_from_model(self):
        super().init_from_model()
        self._varname_widget.setText(self.model.get_varname())
        self._varequation_widget.setText(self.model.get_varequation())

    def open_remote_importer(self, target_function_view, target_function_model):
        varpaths = self.model.wf_root.assemble_variables("")
        mydialog = RemoteImporterDialog(varname="Import variable \"%s\" from:" % self.model.name,
                                        importlist=varpaths)
        mydialog.setModal(True)
        mydialog.exec()
        result = mydialog.result()

        if result:
            choice = mydialog.getchoice()
            target_function_model(choice)
            target_function_view(choice)
        else:
            pass

    def get_middle_widget(self):
        return self._middle_widget

    def sizeHint(self):

        if self.model is not None:
            maxheight = 0
            width = 0


            size = QtCore.QSize(width,maxheight)
            size += QtCore.QSize(50,75)
            if size.width() < 300:
                size.setWidth(300)
            return size
        else:
            return QtCore.QSize(200,100)

    def place_elements(self):
        if not self.dontplace:
            self.dontplace = True
            if self.model is not None:
                self.init_from_model()
            self.dontplace=False
        self.updateGeometry()


class VariableModel(WFItemModel):
    def __init__(self,*args,**kwargs):
        super().__init__(*args, **kwargs)
        self.wf_root = kwargs["wf_root"]
        self.is_wano = False
        self.editor = kwargs['editor']
        self.view = kwargs["view"]
        self.name = "Variable"
        self._varname = "Variable"
        self._varequation = "Equation"

    def set_varequation(self, varequation):
        self._varequation = varequation

    @property
    def model(self):
        return self

    def get_varequation(self):
        return self._varequation

    def set_varname(self, varname):
        self._varname = varname

    def get_varname(self):
        return self._varname

    def render_to_simple_wf(self, path_list, output_path_list, submitdir ,jobdir ,path , parent_ids):
        transitions = []
        varwfex = VariableElement(
            variable_name = self.get_varname(),
            equation = self.get_varequation()
        )
        transitions = []
        for pid in parent_ids:
            transitions.append((pid,varwfex.uid))

        elements = [("VariableElement", varwfex)]
        return elements, transitions, [varwfex.uid]

    def assemble_variables(self, path):
        myvars = [self._varname]
        return myvars

    def assemble_files(self,path):
        return []

    def save_to_disk(self, foldername):
        #view needs varname
        attributes = {"name": self.name,
                      "type": "Variable",
                      "equation": self._varequation,
                      "varname": self._varname}
        root = etree.Element("WFControl", attrib=attributes)
        return root

    def read_from_disk(self, full_foldername, xml_subelement):
        attribs = xml_subelement.attrib
        assert attribs["type"] == "Variable"
        self._varequation = attribs["equation"]
        self._varname = attribs["varname"]

class WhileView(WFControlWithTopMiddleAndBottom):
    def __init__(self,*args,**kwargs):
        super(WhileView,self).__init__(*args,**kwargs)
        self.dontplace = False
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.is_wano = False

    def add_new(self):
        self.model.add()
        self.relayout()

    def relayout(self):
        self.model.wf_root.view.relayout()

    def delete(self):
        self.model.deletelast()
        self.relayout()

    def _on_varname_line_edit(self):
        self.model.set_condition(self.list_of_variables.text())

    def _on_line_edit(self):
        self.model.set_itername(self.itername_widget.text())

    def get_top_widget(self):
        self.topwidget = QtWidgets.QWidget()
        self.topLineLayout = QtWidgets.QHBoxLayout()
        self.topwidget.setLayout(self.topLineLayout)
        #b.clicked.connect(self.toggleVisible)
        self.itername_widget = QtWidgets.QLineEdit('Iterator Name')
        self.itername_widget.editingFinished.connect(self._on_line_edit)
        self.topLineLayout.addWidget(self.itername_widget)
        self.list_of_variables = QtWidgets.QLineEdit('Condition')
        self.list_of_variables.editingFinished.connect(self._on_varname_line_edit)
        self.topLineLayout.addWidget(self.list_of_variables)
        self._global_import_button = QtWidgets.QPushButton(QtGui.QIcon.fromTheme("insert-object"),"")
        self._global_import_button.clicked.connect(self.open_remote_importer)
        self.topLineLayout.addWidget(self._global_import_button)
        #self.open_variables.itemSelectionChanged.connect(self.onItemSelectionChange)
        #self.open_variables.connect_workaround(self._load_variables)
        return self.topwidget

    def open_remote_importer(self):
        varpaths = self.model.wf_root.assemble_variables("")
        mydialog = RemoteImporterDialog(varname="Import variable \"%s\" from:" % self.model.name,
                                        importlist=varpaths)
        mydialog.setModal(True)
        mydialog.exec()
        result = mydialog.result()
        if mydialog.result() == True:
            choice = mydialog.getchoice()
            self.model.set_condition(choice)
            self.list_of_variables.setText(choice)
        else:
            pass

    def init_from_model(self):
        super(WhileView,self).init_from_model()
        for view in self.model.subwf_views:
            self.splitter.addWidget(view)
        self.list_of_variables.setText(self.model.get_condition())
        self.itername_widget.setText(self.model.get_itername())

    def get_middle_widget(self):
        return self.splitter

    def sizeHint(self):

        if self.model is not None:
            maxheight = 0
            width = 0
            for v in self.model.subwf_views:
                sh = v.sizeHint()
                maxheight = max(maxheight,sh.height())
                width += sh.width()

            size = QtCore.QSize(width,maxheight)
            size += QtCore.QSize(50,75)
            if size.width() < 300:
                size.setWidth(300)
            return size
        else:
            return QtCore.QSize(200,100)

    def place_elements(self):
        if not self.dontplace:
            self.dontplace = True
            if self.model is not None:
                self.init_from_model()

                #self.model.subwfview.place_elements()
                for view in self.model.subwf_views:
                    view.place_elements()

            #self.parent().place_elements()
            self.dontplace=False
        self.updateGeometry()

class ControlFactory(object):
    n_t_c = {
        "ForEach" : (ForEachModel,ForEachView),
        "AdvancedFor": (AdvancedForEachModel, AdvancedForEachView),
        "If": (IfModel, IfView),
        "While": (WhileModel, WhileView),
        "Variable": (VariableModel, VariableView),
        "Parallel": (ParallelModel, ParallelView),
        "SubWorkflow": (SubWFModel,SubWorkflowView)
    }
    @classmethod
    def name_to_class(cls,name):
        return cls.n_t_c[name]

    @classmethod
    def construct(cls, name, qt_parent, logical_parent, editor,wf_root):
        modelc,viewc = cls.name_to_class(name)
        view = viewc(qt_parent=qt_parent, logical_parent = logical_parent)
        model = modelc(editor=editor,view=view,wf_root = wf_root)
        view.set_model(model)
        view.init_from_model()
        return model,view
