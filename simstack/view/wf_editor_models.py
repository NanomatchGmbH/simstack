import datetime
import pathlib
import shutil
import time
import os


import abc

from enum import Enum
from os.path import join
import posixpath
from pathlib import Path

from lxml import etree

import PySide6.QtCore as QtCore
import PySide6.QtGui as QtGui

from SimStackServer.WaNo.WaNoDelta import WaNoDelta
from SimStackServer.WorkflowModel import (
    WorkflowExecModule,
    Workflow,
    DirectedGraph,
    WorkflowElementList,
    SubGraph,
    ForEachGraph,
    StringList,
    WFPass,
    IfGraph,
    WhileGraph,
    VariableElement,
    Resources,
)
from simstack.SimStackPaths import SimStackPaths
from simstack.WaNoSettingsProvider import WaNoSettingsProvider
from simstack.Constants import SETTING_KEYS


def linuxjoin(*args, **kwargs):
    return posixpath.join(*args, **kwargs)


def merge_path(path, name, var):
    newpath = "%s.%s.%s" % (path, name, var)
    if newpath.startswith("."):
        newpath = newpath[1:]
    return newpath


class SubmitType(Enum):
    SINGLE_WANO = 0
    WORKFLOW = 1


class DragDropTargetTracker(object):
    def manual_init(self):
        self._initial_parent = self.parent()

    @abc.abstractmethod
    def parent(self):
        pass

    def _target_tracker(self, event):
        self._newparent = event

    def mouseMoveEvent_feature(self, e):
        if e.buttons() != QtCore.Qt.LeftButton:
            return

        # self.parent().removeElement(self)
        mimeData = QtCore.QMimeData()
        self.drag = QtGui.QDrag(self)
        self.drag.setMimeData(mimeData)
        self.drag.setHotSpot(e.pos() - self.rect().topLeft())
        # self.move(e.globalPos())
        self.drag.targetChanged.connect(self._target_tracker)
        self._newparent = self.parent()
        self.drag.exec_(QtCore.Qt.MoveAction)

        # In case the target of the drop changed we are outside the workflow editor
        # In that case we would like to remove ourselves
        if self._newparent is None:
            self.parent().removeElement(self.model)
            self.model.view.deleteLater()
        elif self._newparent == self._initial_parent:
            # Nothing to be done
            pass


class WFItemListInterface(object):
    def __init__(self, *args, **kwargs):
        self.is_wano = False
        self.editor = kwargs["editor"]
        self.view = kwargs["view"]
        self.elements = []  # List of Elements,Workflows, ControlElements
        # Name of the saved folder
        self.elementnames = []
        self.foldername = None

    def element_to_name(self, element):
        idx = self.elements.index(element)
        return self.elementnames[idx]

    def collect_wano_widgets(self):
        outlist = []
        for element in self.elements:
            if isinstance(element, WFWaNoWidget):
                outlist.append(element)
            elif hasattr(element, "collect_wano_widgets"):
                outlist = outlist + element.collect_wano_widgets()
        return outlist

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
        if isinstance(element, WFWaNoWidget):
            wws = self.get_wano_names()
            if element.wano.name not in wws:
                self.get_root().wano_folder_remove(element.wano.name)


class WFItemModel:
    def __init__(self, *args, **kwargs):
        pass

    def render_to_simple_wf(self, path_list, output_path_list, submitdir, jobdir):
        pass
        # wf = WFtoXML.xml_subworkflow(Transition=transitions,Activity=activities)

    # this function assembles all files relative to the workflow root
    # The files will be export to c9m:${WORKFLOW_ID}/the file name below
    def assemble_files(self, path):
        myfiles = []
        return myfiles

    def assemble_variables(self, path):
        return []

    def close(self):
        pass

    def setText(self, *args, **kwargs):
        self.name = args[0]

    def save_to_disk(self, complete_foldername):
        xml = []
        return xml

    def read_from_disk(self, full_foldername, xml_subelement):
        return


class SubWFModel(WFItemModel, WFItemListInterface):
    def __init__(self, *args, **kwargs):
        WFItemListInterface.__init__(self, *args, **kwargs)
        self.wf_root = kwargs["wf_root"]
        self.name = "SubWF"

    def get_root(self):
        return self.wf_root

    def render_to_simple_wf(
        self, path_list, output_path_list, submitdir, jobdir, path, parent_ids
    ):
        """

        :param submitdir:
        :param jobdir:
        :param path:
        :param parent_ids (list): List of parent ids, this WF has to transition from
        :return:
        """

        activities = []
        transitions = []
        basepath = path
        for myid, (ele, elename) in enumerate(zip(self.elements, self.elementnames)):
            toids = []
            if ele.is_wano:
                wano_dir = os.path.join(jobdir, self.element_to_name(ele))
                try:
                    os.makedirs(wano_dir)
                except OSError:
                    pass

                stageout_basedir = "%s/%s" % (basepath, elename)

                jsdl, wem, wem_path_list = ele.render(
                    path_list,
                    output_path_list,
                    wano_dir,
                    stageout_basedir=stageout_basedir,
                )
                wem.set_given_name(elename)
                wem: WorkflowExecModule

                wem.set_given_name(elename)
                mypath = "/".join(path_list + [elename])
                myoutputpath = "/".join(output_path_list + [elename])
                wem.set_path(mypath)
                wem.set_outputpath(myoutputpath)
                toids = [wem.uid]
                activities.append(["WorkflowExecModule", wem])
                for pid in parent_ids:
                    for toid in toids:
                        transitions.append((pid, toid))
            else:
                my_activities, my_transitions, toids = ele.render_to_simple_wf(
                    path_list,
                    output_path_list,
                    submitdir,
                    jobdir,
                    path=path,
                    parent_ids=parent_ids,
                )
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
                    myfiles.append(linuxjoin(path, otherfile))
        return myfiles

    def assemble_variables(self, path):
        myvars = []
        for myid, (ele, name) in enumerate(zip(self.elements, self.elementnames)):
            if ele.is_wano:
                for var in ele.get_variables():
                    newpath = merge_path(path, ele.name, var)
                    myvars.append(newpath)
            else:
                for myvar in ele.assemble_variables(path):
                    myvars.append(myvar)
        return myvars

    def read_from_disk(self, full_foldername, xml_subelement):
        # self.foldername = foldername
        # xml_filename = os.path.join(foldername,os.path.basename(foldername)) + ".xml"
        # tree = etree.parse(xml_filename)
        # root = tree.getroot()
        foldername_path = pathlib.Path(full_foldername)

        for child in xml_subelement:
            if child.tag == "WaNo":
                type = child.attrib["type"]
                name = child.attrib["name"]
                uuid = child.attrib["uuid"]
                myid = int(child.attrib["id"])
                # print(len(self.elements),myid)
                assert myid == len(self.elements)

                if self.get_root().get_wf_read_version() == "2.0":
                    wanofolder = foldername_path / "wano_configurations" / uuid
                    wd = WaNoDelta(wanofolder)
                    wano_folder = wd.folder
                    basewanodir = foldername_path / "wanos" / wano_folder
                else:
                    wanofolder = foldername_path / "wanos" / uuid
                    # backwards compat to v1 workflows
                    basewanodir = wanofolder
                widget = WFWaNoWidget.instantiate_from_folder(
                    basewanodir, wanofolder, type, parent=self.view
                )
                widget.setText(name)
                self.elements.append(widget)
                self.elementnames.append(name)
            elif child.tag == "WFControl":
                name = child.attrib["name"]
                type = child.attrib["type"]
                model, view = _get_control_factory().construct(
                    type,
                    qt_parent=self.view,
                    logical_parent=self.view,
                    editor=self.editor,
                    wf_root=self.wf_root,
                )
                self.elements.append(model)
                self.elementnames.append(name)
                view.setText(name)
                model.read_from_disk(
                    full_foldername=full_foldername, xml_subelement=child
                )

    def save_to_disk(self, foldername):
        success = False
        attributes = {"name": self.view.text(), "type": "SubWorkflow"}
        root = etree.Element("WFControl", attrib=attributes)

        # my_foldername = os.path.join(foldername,self.view.text())
        my_foldername = foldername
        # TODO revert changes in filesystem in case instantiate_in_folder fails
        for myid, (ele, name) in enumerate(zip(self.elements, self.elementnames)):
            if ele.is_wano:
                subxml = ele.get_xml()
                subxml.attrib["id"] = str(myid)
                subxml.attrib["name"] = name
                success = ele.instantiate_in_folder(my_foldername)
                ele.save_delta(foldername)
                root.append(subxml)
                if not success:
                    break
            else:
                root.append(ele.save_to_disk(my_foldername))
        return root

    def remove_element(self, element):
        myid = self.elements.index(element)
        self.elements.remove(element)
        del self.elementnames[myid]
        if isinstance(element, WFWaNoWidget):
            wws = self.get_root().get_wano_names()
            if element.wano.name not in wws:
                self.get_root().wano_folder_remove(element.wano.name)

    def removeElement(self, element):
        # print("subwf Removing",element)
        self.remove_element(element)
        return


class WhileModel(WFItemModel):
    def __init__(self, *args, **kwargs):
        # super().__init__(*args,**kwargs)
        super().__init__(*args, **kwargs)
        self.wf_root = kwargs["wf_root"]
        self.is_wano = False
        self.editor = kwargs["editor"]
        self.view = kwargs["view"]
        self._subwf_model, self._subwf_view = _get_control_factory().construct(
            "SubWorkflow",
            editor=self.editor,
            qt_parent=self.view,
            logical_parent=self.view.logical_parent,
            wf_root=self.wf_root,
        )
        self.subwf_models = [self._subwf_model]
        self.subwf_views = [self._subwf_view]
        self.name = "While"
        self.itername = "While_iterator"
        self._condition = "Condition"

    def set_condition(self, condition):
        self._condition = condition

    def get_condition(self):
        return self._condition

    def collect_wano_widgets(self):
        outlist = []
        for model in self.subwf_models:
            outlist += model.collect_wano_widgets()
        return outlist

    def set_itername(self, itername):
        self.itername = itername

    def get_itername(self):
        return self.itername

    def render_to_simple_wf(
        self, path_list, output_path_list, submitdir, jobdir, path, parent_ids
    ):
        transitions = []

        if jobdir == "":
            my_jobdir = self.name
        else:
            my_jobdir = "%s/%s" % (jobdir, self.name)

        if path == "":
            path = self.name
        else:
            path = "%s/%s" % (path, self.name)

        my_path_list = path_list + [self.name]
        my_output_path_list = output_path_list + [
            self.name,
            "${" + self.itername.replace(" ", "") + "}",
        ]

        (
            sub_activities,
            sub_transitions,
            sub_toids,
        ) = self._subwf_model.render_to_simple_wf(
            my_path_list,
            my_output_path_list,
            submitdir,
            my_jobdir,
            path=path,
            parent_ids=["temporary_connector"],
        )
        sg = SubGraph(
            elements=WorkflowElementList(sub_activities),
            graph=DirectedGraph(sub_transitions),
        )

        mypass = WFPass()
        finish_uid = mypass.uid
        fe = WhileGraph(
            subgraph=sg,
            finish_uid=finish_uid,
            iterator_name=self.itername,
            condition=self._condition,
            subgraph_final_ids=StringList(sub_toids),
        )

        toids = [fe.uid]
        for parent_id in parent_ids:
            transitions.append((parent_id, toids[0]))

        return (
            [("WhileGraph", fe), ("WFPass", mypass)],
            transitions,
            [finish_uid],
        )  # WFtoXML.xml_subwfforeach(IteratorName=self.itername,IterSet=filesets,SubWorkflow=swf,Id=muuid)

    def assemble_variables(self, path):
        if path == "":
            mypath = "While.${%s_ITER}" % self.itername
        else:
            mypath = "%s.While.${%s_ITER}" % (path, self.itername)
        myvars = self._subwf_model.assemble_variables(mypath)
        my_iterator = "${%s}" % self.itername
        myvars.append(my_iterator)
        return myvars

    def assemble_files(self, path):
        myfiles = []
        for otherfile in self._subwf_model.assemble_files(path):
            myfiles.append(linuxjoin(path, self.view.text(), "*", otherfile))
        return myfiles

    def save_to_disk(self, foldername):
        # view needs varname
        attributes = {"name": self.name, "type": "While", "condition": self._condition}
        root = etree.Element("WFControl", attrib=attributes)
        my_foldername = foldername
        root.append(self._subwf_model.save_to_disk(my_foldername))
        iter_xml = etree.SubElement(root, "IterName")
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

            self._subwf_view.setText(name)
            self._subwf_model.read_from_disk(
                full_foldername=full_foldername, xml_subelement=child
            )


class IfModel(WFItemModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wf_root = kwargs["wf_root"]

        self.is_wano = False
        self.editor = kwargs["editor"]
        self.view = kwargs["view"]
        (
            self._subwf_true_branch_model,
            self._subwf_true_branch_view,
        ) = _get_control_factory().construct(
            "SubWorkflow",
            editor=self.editor,
            qt_parent=self.view,
            logical_parent=self.view.logical_parent,
            wf_root=self.wf_root,
        )
        (
            self._subwf_false_branch_model,
            self._subwf_false_branch_view,
        ) = _get_control_factory().construct(
            "SubWorkflow",
            editor=self.editor,
            qt_parent=self.view,
            logical_parent=self.view.logical_parent,
            wf_root=self.wf_root,
        )
        self.subwf_models = [
            self._subwf_true_branch_model,
            self._subwf_false_branch_model,
        ]
        self.subwf_views = [self._subwf_true_branch_view, self._subwf_false_branch_view]
        self.name = "Branch"
        self._condition = ""

    def collect_wano_widgets(self):
        outlist = []
        for model in self.subwf_models:
            outlist += model.collect_wano_widgets()
        return outlist

    def set_condition(self, condition):
        self._condition = condition

    def get_condition(self):
        return self._condition

    def render_to_simple_wf(
        self, path_list, output_path_list, submitdir, jobdir, path, parent_ids
    ):
        transitions = []

        if jobdir == "":
            my_jobdir = self.name
        else:
            my_jobdir = "%s/%s" % (jobdir, self.name)

        if path == "":
            path = self.name
        else:
            path = "%s/%s" % (path, self.name)

        my_true_path_list = path_list + [self.name, "True"]
        my_false_path_list = path_list + [self.name, "False"]
        output_path_list_true = output_path_list + [self.name, "True"]
        output_path_list_false = output_path_list + [self.name, "False"]

        (
            sub_activities_true,
            sub_transitions_true,
            sub_toids_true,
        ) = self._subwf_true_branch_model.render_to_simple_wf(
            my_true_path_list,
            output_path_list_true,
            submitdir,
            my_jobdir + "/True",
            path=path + "/True/",
            parent_ids=["temporary_connector"],
        )
        (
            sub_activities_false,
            sub_transitions_false,
            sub_toids_false,
        ) = self._subwf_false_branch_model.render_to_simple_wf(
            my_false_path_list,
            output_path_list_false,
            submitdir,
            my_jobdir + "/False",
            path=path + "/False/",
            parent_ids=["temporary_connector"],
        )
        sg_true = SubGraph(
            elements=WorkflowElementList(sub_activities_true),
            graph=DirectedGraph(sub_transitions_true),
        )
        sg_false = SubGraph(
            elements=WorkflowElementList(sub_activities_false),
            graph=DirectedGraph(sub_transitions_false),
        )

        mypass = WFPass()
        finish_uid = mypass.uid

        fe = IfGraph(
            finish_uid=finish_uid,
            truegraph=sg_true,
            falsegraph=sg_false,
            true_final_ids=StringList(sub_toids_true),
            false_final_ids=StringList(sub_toids_false),
            condition=self._condition,
        )

        toids = [fe.uid]
        for parent_id in parent_ids:
            transitions.append((parent_id, toids[0]))

        # We are now generating a break in this workflow. The break will be resolved (hopefully) once the FE runs.

        return [("IfGraph", fe), ("WFPass", mypass)], transitions, [finish_uid]

    def assemble_variables(self, path):
        myvars = []
        for swfid, (swfm, truefalse) in enumerate(
            zip(
                [self._subwf_true_branch_model, self._subwf_true_branch_model],
                ["True", "False"],
            )
        ):
            truefalsepath = merge_path(path, self.name, truefalse)
            for var in swfm.assemble_variables(truefalsepath):
                myvars.append(var)
        return myvars

    def assemble_files(self, path):
        myfiles = []
        for swfid, (swfm, truefalse) in enumerate(
            zip(
                [self._subwf_true_branch_model, self._subwf_true_branch_model],
                ["True", "False"],
            )
        ):
            for otherfile in swfm.assemble_files(path):
                myfiles.append(linuxjoin(path, self.name, truefalse, otherfile))
        return myfiles

    def save_to_disk(self, foldername):
        attributes = {"name": self.name, "type": "If", "condition": self._condition}
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
            subwfmodel, subwfview = _get_control_factory().construct(
                "SubWorkflow",
                qt_parent=self.view,
                logical_parent=self.view,
                editor=self.editor,
                wf_root=self.wf_root,
            )
            name = child.attrib["name"]

            subwfview.setText(name)
            subwfmodel.read_from_disk(
                full_foldername=full_foldername, xml_subelement=child
            )
            if child.attrib["branch"] == "true":
                self._subwf_true_branch_model = subwfmodel
                self._subwf_true_branch_view = subwfview
            elif child.attrib["branch"] == "false":
                self._subwf_false_branch_model = subwfmodel
                self._subwf_false_branch_view = subwfview
        self.subwf_models = [
            self._subwf_true_branch_model,
            self._subwf_false_branch_model,
        ]
        self.subwf_views = [self._subwf_true_branch_view, self._subwf_false_branch_view]
        self.view.init_from_model()


class ParallelModel(WFItemModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wf_root = kwargs["wf_root"]

        self.is_wano = False
        self.editor = kwargs["editor"]
        self.view = kwargs["view"]
        self.numbranches = 1
        self.subwf_models = []
        self.subwf_views = []
        subwfmodel, subwfview = _get_control_factory().construct(
            "SubWorkflow",
            editor=self.editor,
            qt_parent=self.view,
            logical_parent=self.view.logical_parent,
            wf_root=self.wf_root,
        )
        self.subwf_models.append(subwfmodel)
        self.subwf_views.append(subwfview)
        self.name = "Parallel"

    def collect_wano_widgets(self):
        outlist = []
        for model in self.subwf_models:
            outlist += model.collect_wano_widgets()
        return outlist

    def render_to_simple_wf(
        self, path_list, output_path_list, submitdir, jobdir, path, parent_ids
    ):
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
        for swf_id, swfm in enumerate(self.subwf_models):
            inner_jobdir = "%s/%d" % (my_jobdir, swf_id)
            inner_path = "%s/%d" % (path, swf_id)

            new_output_path_list = output_path_list + [self.name, str(swf_id)]
            new_path_list = path_list + [self.name, str(swf_id)]

            my_activities, my_transitions, my_toids = swfm.render_to_simple_wf(
                new_path_list,
                new_output_path_list,
                submitdir,
                inner_jobdir,
                path=inner_path,
                parent_ids=parent_ids,
            )
            transitions += my_transitions
            activities += my_activities
            toids += my_toids

        return activities, transitions, toids

    def assemble_variables(self, path):
        myvars = []
        for swfid, swfm in enumerate(self.subwf_models):
            for var in swfm.assemble_variables(path):
                newpath = merge_path(path, "%s.%d" % (self.name, swfid), var)
                myvars.append(newpath)
        return myvars

    def add(self):
        subwfmodel, subwfview = _get_control_factory().construct(
            "SubWorkflow",
            editor=self.editor,
            qt_parent=self.view,
            logical_parent=self.view.logical_parent,
            wf_root=self.wf_root,
        )
        self.subwf_models.append(subwfmodel)
        self.subwf_views.append(subwfview)

    def deletelast(self):
        if len(self.subwf_views) <= 1:
            return
        self.subwf_views[-1].deleteLater()
        self.subwf_views.pop()
        self.subwf_models.pop()

    def assemble_files(self, path):
        myfiles = []
        for swfid, swfm in enumerate(self.subwf_models):
            for otherfile in swfm.assemble_files(path):
                myfiles.append(linuxjoin(path, self.name, "%d" % swfid, otherfile))
        return myfiles

    def save_to_disk(self, foldername):
        attributes = {"name": self.name, "type": "Parallel"}
        root = etree.Element("WFControl", attrib=attributes)
        # TODO revert changes in filesystem in case instantiate_in_folder fails
        # root.append(self.subwfmodel.save_to_disk(my_foldername))
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
            subwfmodel, subwfview = _get_control_factory().construct(
                "SubWorkflow",
                qt_parent=self.view,
                logical_parent=self.view,
                editor=self.editor,
                wf_root=self.wf_root,
            )
            name = child.attrib["name"]

            subwfview.setText(name)
            subwfmodel.read_from_disk(
                full_foldername=full_foldername, xml_subelement=child
            )
            self.subwf_models.append(subwfmodel)
            self.subwf_views.append(subwfview)
        self.view.init_from_model()


class ForEachModel(WFItemModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wf_root = kwargs["wf_root"]

        self.is_wano = False
        self.editor = kwargs["editor"]
        self.view = kwargs["view"]
        self.itername = "ForEach_iterator"
        self.subwfmodel, self.subwfview = _get_control_factory().construct(
            "SubWorkflow",
            editor=self.editor,
            qt_parent=self.view,
            logical_parent=self.view.logical_parent,
            wf_root=self.wf_root,
        )
        self.fileliststring = ""
        self.name = "ForEach"
        self._is_file_iterator = True
        self._is_multivar_iterator = False

    def collect_wano_widgets(self):
        return self.subwfmodel.collect_wano_widgets()

    def set_is_file_iterator(self, true_or_false):
        self._is_file_iterator = true_or_false

    def set_filelist(self, filelist):
        self.fileliststring = filelist

    def assemble_variables(self, path):
        if path == "":
            mypath = "ForEach.${%s_ITER}" % self.itername
        else:
            mypath = "%s.ForEach.${%s_ITER}" % (path, self.itername)
        myvars = self.subwfmodel.assemble_variables(mypath)
        my_iterator = "${%s_ITER}" % self.itername
        myvars.append(my_iterator)
        myvalue = "${%s}" % self.itername
        myvars.append(myvalue)
        return myvars

    def render_to_simple_wf(
        self, path_list, output_path_list, submitdir, jobdir, path, parent_ids
    ):
        filesets = []
        transitions = []

        if self._is_file_iterator:
            for myfile in self.fileliststring.split():
                gpath = "${STORAGE}/workflow_data/%s" % myfile
                # localfn = os.path.basename(myfile)
                # gpath = join(gpath,localfn)
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
            path = "%s/%s" % (path, self.name)

        my_path_list = path_list + [self.name]
        my_output_path_list = output_path_list + [
            self.name,
            "${" + self.itername.replace(" ", "") + "_ITER}",
        ]

        (
            sub_activities,
            sub_transitions,
            sub_toids,
        ) = self.subwfmodel.render_to_simple_wf(
            my_path_list,
            my_output_path_list,
            submitdir,
            my_jobdir,
            path=path,
            parent_ids=["temporary_connector"],
        )
        sg = SubGraph(
            elements=WorkflowElementList(sub_activities),
            graph=DirectedGraph(sub_transitions),
        )

        mypass = WFPass()
        finish_uid = mypass.uid

        if self._is_file_iterator:
            fe = ForEachGraph(
                subgraph=sg,
                # parent_ids=StringList(parent_ids),
                finish_uid=finish_uid,
                iterator_name=self.itername,
                iterator_files=StringList(filesets),
                subgraph_final_ids=StringList(sub_toids),
            )
        elif self._is_multivar_iterator:
            fe = ForEachGraph(
                subgraph=sg,
                # parent_ids=StringList(parent_ids),
                finish_uid=finish_uid,
                iterator_name=self.itername,
                iterator_definestring=self.fileliststring,
                subgraph_final_ids=StringList(sub_toids),
            )
        else:
            fe = ForEachGraph(
                subgraph=sg,
                # parent_ids=StringList(parent_ids),
                finish_uid=finish_uid,
                iterator_name=self.itername,
                iterator_variables=StringList(filesets),
                subgraph_final_ids=StringList(sub_toids),
            )

        toids = [fe.uid]
        for parent_id in parent_ids:
            transitions.append((parent_id, toids[0]))

        # We are now generating a break in this workflow. The break will be resolved (hopefully) once the FE runs.

        return (
            [("ForEachGraph", fe), ("WFPass", mypass)],
            transitions,
            [finish_uid],
        )  # WFtoXML.xml_subwfforeach(IteratorName=self.itername,IterSet=filesets,SubWorkflow=swf,Id=muuid)

    def assemble_files(self, path):
        myfiles = []
        myfiles.append("${%s}" % (self.itername))
        for otherfile in self.subwfmodel.assemble_files(path):
            myfiles.append(linuxjoin(path, self.view.text(), "*", otherfile))
            myfiles.append(
                linuxjoin(
                    path, self.view.text(), "${%s_ITER}" % self.itername, otherfile
                )
            )
        return myfiles

    def save_to_disk(self, foldername):
        true_false = {True: "True", False: "False"}
        mytype = "ForEach"
        if self._is_multivar_iterator:
            mytype = "AdvancedFor"
        attributes = {
            "name": self.view.text(),
            "type": mytype,
            "is_file_iterator": true_false[self._is_file_iterator],
        }
        root = etree.Element("WFControl", attrib=attributes)
        my_foldername = foldername
        # TODO revert changes in filesystem in case instantiate_in_folder fails
        root.append(self.subwfmodel.save_to_disk(my_foldername))
        filelist = etree.SubElement(root, "FileList")
        for fn in self.fileliststring.split():
            fxml = etree.SubElement(filelist, "File")
            fxml.text = fn
            filelist.append(fxml)
        iter_xml = etree.SubElement(root, "IterName")
        iter_xml.text = self.itername
        return root

    def read_from_disk(self, full_foldername, xml_subelement):
        # TODO: missing save filelist
        # TODO: missing render
        try:
            is_file_iter = xml_subelement.attrib["is_file_iterator"]
            if is_file_iter == "True":
                self._is_file_iterator = True
            else:
                self._is_file_iterator = False
        except KeyError:
            self._is_file_iterator = True
        self.fileliststring = ""
        for child in xml_subelement:
            if child.tag == "FileList":
                for xml_ss in child:
                    self.fileliststring += "%s " % xml_ss.text
                continue
            if child.tag == "IterName":
                self.itername = child.text
                continue
            if child.tag != "WFControl":
                continue
            if child.attrib["type"] != "SubWorkflow":
                continue
            # self.subwfmodel,self.subwfview = ControlFactory.construct("SubWorkflow", qt_parent=self.view, logical_parent=self.view,editor=self.editor,wf_root = self.wf_root)
            name = child.attrib["name"]

            self.subwfview.setText(name)
            self.subwfmodel.read_from_disk(
                full_foldername=full_foldername, xml_subelement=child
            )

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
            mypath = "AdvancedForEach.${%s_ITER}" % self.itername.replace(" ", "")
        else:
            mypath = "%s.AdvancedForEach.${%s_ITER}" % (
                path,
                self.itername.replace(" ", ""),
            )

        myvars = self.subwfmodel.assemble_variables(mypath)
        iterators = self.itername.replace(" ", "").split(",")
        myvars.append("${%s_ITER}" % (self.itername.replace(" ", "")))
        for it in iterators:
            myvars.append("${%s}" % it)
            # myvars.append("${%s_ITER}" % it)
        return myvars


class WFModel:
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
        self.foldername = None
        self.editor = kwargs["editor"]
        self.view = kwargs["view"]
        self.elements = []  # List of Elements,Workflows, ControlElements
        self._base_resource_during_render = None
        # Name of the saved folder
        self.elementnames = []
        self.foldername = None
        self.wf_name = "Unset"
        self._wf_read_version = "2.0"
        # Few Use Cases
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

    def get_wf_read_version(self):
        return self._wf_read_version

    def get_root(self):
        return self

    def element_to_name(self, element):
        idx = self.elements.index(element)
        return self.elementnames[idx]

    def wano_folder_remove(self, wano_name: str):
        if not self.foldername:
            # The Workflow was not saved yet, no folder to delete.
            return
        possible_folder = Path(self.foldername) / "wanos" / wano_name
        if possible_folder.is_dir():
            assert possible_folder != Path.home(), "Path cannot be home directory."
            assert (
                possible_folder != possible_folder.anchor
            ), "Path cannot be filesystem root."
            shutil.rmtree(possible_folder)

    def collect_wano_widgets(self):
        outlist = []
        for element in self.elements:
            if isinstance(element, WFWaNoWidget):
                outlist.append(element)
            elif hasattr(element, "collect_wano_widgets"):
                outlist = outlist + element.collect_wano_widgets()
        return outlist

    def assemble_variables(self, path):
        myvars = []
        for myid, (ele, name) in enumerate(zip(self.elements, self.elementnames)):
            if ele.is_wano:
                for var in ele.get_variables():
                    newpath = merge_path(path, ele.name, var)
                    myvars.append(newpath)
            else:
                for myvar in ele.assemble_variables(path):
                    myvars.append(myvar)
        return myvars

    def render_to_simple_wf(self, submitdir, jobdir):
        activities = []
        transitions = []
        # start = WFtoXML.xml_start()
        # parent_xml = etree.Element()

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
                # stageout_basedir = "wanos/%s" % (elename)
                my_path_list = path_list.copy()
                jsdl, wem, other = ele.render(
                    my_path_list, output_path_list, wano_dir, stageout_basedir=elename
                )
                wem.set_given_name(elename)
                mypath = "/".join(path_list + [elename])
                myoutputpath = "/".join(output_path_list + [elename])
                wem.set_path(mypath)
                wem.set_outputpath(myoutputpath)
                wem: WorkflowExecModule
                toids = [wem.uid]
                activities.append(["WorkflowExecModule", wem])
                for fromid in fromids:
                    for toid in toids:
                        transitions.append((fromid, toid))
            else:
                # only subworkflow remaining
                my_path_list = path_list.copy()
                my_activities, my_transitions, toids = ele.render_to_simple_wf(
                    my_path_list,
                    output_path_list,
                    submitdir,
                    jobdir,
                    path="",
                    parent_ids=fromids,
                )
                activities += my_activities
                transitions += my_transitions

            # transition = WFtoXML.xml_transition(From=fromid, To=toid)
            # print((fromid,toid))

            fromids = toids

        wf = Workflow(
            elements=WorkflowElementList(activities),
            graph=DirectedGraph(transitions),
            name=self.wf_name,
            storage="${BASEFOLDER}",
            queueing_system="${QUEUE}",
        )
        xml = etree.Element("Workflow")
        wf.to_xml(parent_element=xml)

        return xml

    # this function assembles all files relative to the workflow root
    # The files will be export to c9m:${WORKFLOW_ID}/the file name below
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

    def assemble_files(self, path):
        myfiles = []
        for myid, (ele, name) in enumerate(zip(self.elements, self.elementnames)):
            if ele.is_wano:
                for file in ele.wano_model.get_output_files():
                    fn = linuxjoin(name, "outputs", file)
                    myfiles.append(fn)
            else:
                for otherfile in ele.assemble_files(path=""):
                    myfiles.append(otherfile)

        return myfiles

    def get_wano_names(self):
        names = {wfwn.wano.name for wfwn in self.collect_wano_widgets()}
        return names

    def save_to_disk(self, foldername):
        success = True
        self.wf_name = os.path.basename(foldername)
        self.foldername = foldername
        settings = WaNoSettingsProvider.get_instance()
        wdir = settings.get_value(SETTING_KEYS["workflows"])
        if wdir == "<embedded>":
            wdir = join(SimStackPaths.get_embedded_path(), "workflows")

        mydir = os.path.join(wdir, self.wf_name)
        try:
            os.makedirs(mydir)
        except OSError:
            pass

        root = etree.Element("root")
        root.attrib["wfxml_version"] = "2.0"
        # TODO revert changes in filesystem in case instantiate_in_folder fails
        for myid, (ele, name) in enumerate(zip(self.elements, self.elementnames)):
            if ele.is_wano:
                subxml = ele.get_xml()
                subxml.attrib["id"] = str(myid)
                subxml.attrib["name"] = name
                # print("Instantiating in folder: %s, wanocheat: %s"%(foldername,ele.wano[1]))
                # This call copies everything:
                success = ele.instantiate_in_folder(foldername)
                # We also need to save the delta xml here:
                ele.save_delta(foldername)
                root.append(subxml)
                if not success:
                    break
            else:
                root.append(ele.save_to_disk(foldername))

        if success:
            xml_path = os.path.join(mydir, self.wf_name + ".xml")
            with open(xml_path, "w") as outfile:
                outfile.write(
                    etree.tostring(root, encoding="unicode", pretty_print=True)
                )
        else:
            print("Error while writing wano")
            raise Exception("This should be a custom exception")
        return success

    def read_from_disk(self, foldername):
        self.foldername = foldername
        self.wf_name = os.path.basename(foldername)
        xml_filename = os.path.join(foldername, os.path.basename(foldername)) + ".xml"
        tree = etree.parse(xml_filename)
        root = tree.getroot()
        wfxml_version = root.attrib.get("wfxml_version", "1.0")
        self._wf_read_version = wfxml_version
        foldername_path = pathlib.Path(foldername)
        for child in root:
            if child.tag == "WaNo":
                type = child.attrib["type"]
                name = child.attrib["name"]
                uuid = child.attrib["uuid"]
                myid = int(child.attrib["id"])
                # print(len(self.elements),myid)
                assert myid == len(self.elements)
                if self.get_root().get_wf_read_version() == "2.0":
                    wanofolder = foldername_path / "wano_configurations" / uuid
                    wd = WaNoDelta(wanofolder)
                    wano_folder = wd.folder
                    basewanodir = foldername_path / "wanos" / wano_folder
                else:
                    wanofolder = foldername_path / "wanos" / uuid
                    # backwards compat to v1 workflows
                    basewanodir = wanofolder

                widget = WFWaNoWidget.instantiate_from_folder(
                    basewanodir, wanofolder, type, parent=self.view
                )
                widget.setText(name)
                self.elements.append(widget)
                self.elementnames.append(name)
            elif child.tag == "WFControl":
                name = child.attrib["name"]
                type = child.attrib["type"]
                model, view = _get_control_factory().construct(
                    type,
                    qt_parent=self.view,
                    logical_parent=self.view,
                    editor=self.editor,
                    wf_root=self,
                )
                self.elements.append(model)
                self.elementnames.append(name)
                view.setText(name)

                model.read_from_disk(full_foldername=foldername, xml_subelement=child)
        self.view.updateGeometry()

    def base_resource_during_render(self):
        return self._base_resource_during_render

    def render(self, given_name, current_registry: Resources):
        self._base_resource_during_render = current_registry
        assert self.foldername is not None
        now = datetime.datetime.now()
        nowstr = now.strftime("%Y-%m-%d-%Hh%Mm%Ss")
        submitname = "%s-%s" % (nowstr, given_name)
        submitdir = os.path.join(self.foldername, "Submitted", submitname)
        counter = 0
        while os.path.exists(submitdir):
            time.sleep(1.1)
            now = datetime.datetime.now()
            nowstr = now.strftime("%Y-%m-%d-%Hh%Mn%Ss")
            submitname = "%s-%s" % (nowstr, given_name)
            submitdir = os.path.join(self.foldername, "Submitted", submitname)
            counter += 1
            if counter == 10:
                raise FileExistsError("Submit directory %s already exists." % submitdir)

        jobdir = os.path.join(submitdir, "workflow_data")
        try:
            os.makedirs(jobdir)
        except OSError:
            pass

        wf_xml = self.render_to_simple_wf(submitdir, jobdir)
        self._base_resource_during_render = None
        return SubmitType.WORKFLOW, submitdir, wf_xml

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
        newname = self.unique_name(element.name)
        if newname != element.name:
            element.setText(newname)
        if pos is not None:
            self.elements.insert(pos, element)
            self.elementnames.insert(pos, newname)
        else:
            self.elements.append(element)
            self.elementnames.append(newname)
        element.view.show()

    def remove_element(self, element):
        myid = self.elements.index(element)
        self.elements.remove(element)
        del self.elementnames[myid]
        if isinstance(element, WFWaNoWidget):
            wws = self.get_wano_names()
            if element.wano.name not in wws:
                self.get_root().wano_folder_remove(element.wano.name)

    def openWaNoEditor(self, wanoWidget):
        self.editor.openWaNoEditor(wanoWidget)

    def removeElement(self, element):
        # print("Removing",element)
        self.remove_element(element)
        return


class VariableModel(WFItemModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wf_root = kwargs["wf_root"]
        self.is_wano = False
        self.editor = kwargs["editor"]
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

    def render_to_simple_wf(
        self, path_list, output_path_list, submitdir, jobdir, path, parent_ids
    ):
        transitions = []
        varwfex = VariableElement(
            variable_name=self.get_varname(), equation=self.get_varequation()
        )
        transitions = []
        for pid in parent_ids:
            transitions.append((pid, varwfex.uid))

        elements = [("VariableElement", varwfex)]
        return elements, transitions, [varwfex.uid]

    def assemble_variables(self, path):
        myvars = [self._varname]
        return myvars

    def assemble_files(self, path):
        return []

    def save_to_disk(self, foldername):
        # view needs varname
        attributes = {
            "name": self.name,
            "type": "Variable",
            "equation": self._varequation,
            "varname": self._varname,
        }
        root = etree.Element("WFControl", attrib=attributes)
        return root

    def read_from_disk(self, full_foldername, xml_subelement):
        attribs = xml_subelement.attrib
        assert attribs["type"] == "Variable"
        self._varequation = attribs["equation"]
        self._varname = attribs["varname"]


# Note: WFWaNoWidget and ControlFactory are defined in the main WFEditorPanel.py file
# and are imported here through circular dependencies. This is a temporary solution
# until the full refactoring is complete.

# Forward declarations for classes that will need to be imported or defined elsewhere:
# - WFWaNoWidget: Widget class for WaNo components
# - ControlFactory: Factory class for creating control model/view pairs


class WFWaNoWidget:
    """Placeholder for WFWaNoWidget class - will be imported from WFEditorPanel.py"""

    pass


# ControlFactory import will be done at runtime to avoid circular imports
def _get_control_factory():
    from .wf_editor_factory import ControlFactory

    return ControlFactory
