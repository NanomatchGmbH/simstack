from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import os

import logging
import shutil
import uuid

from io import StringIO


from enum import Enum

from   lxml import etree

import PySide.QtCore as QtCore
import PySide.QtGui  as QtGui
from PySide.QtCore import Signal

import WaNo.WaNoFactory as WaNoFactory
from WaNo.WaNoSettingsProvider import WaNoSettingsProvider
from WaNo.Constants import SETTING_KEYS

from WaNo.view.MultiselectDropDownList import MultiselectDropDownList

from collections import OrderedDict

from WaNo.view.WFEditorWidgets import WFEWaNoListWidget, WFEListWidget
from WaNo.lib.FileSystemTree import copytree

from pyura.pyura.WorkflowXMLConverter import WFtoXML

#def mapClassToTag(name):
#    xx = name.replace('Widget','')
#    return xx[2:]
    
widgetColors = {'MainEditor' : '#F5FFF5' , 'Control': '#EBFFD6' , 'Base': '#F5FFEB' ,
               'WaNo' : '#FF00FF', 'ButtonColor':'#D4FF7F' }




class WFWaNoWidget(QtGui.QToolButton):
    def __init__(self, text, wano, parent):

        super(WFWaNoWidget, self).__init__(parent)
        self.logger = logging.getLogger('WFELOG')
        self.moved = False
        lvl = self.logger.getEffectiveLevel() # switch off too many infos
        self.logger.setLevel(logging.ERROR)
        self.is_wano = True
        self.logger.setLevel(lvl)
        self.wf_model = parent.model
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
        self.setIcon(wano[3])
        #self.setAutoFillBackground(True)
        #self.setColor(QtCore.Qt.lightGray)
        self.wano = wano
        self.model = self
        self.wano_model = None
        self.wano_view = None
        self.constructed = False
        self.newparent = self.parent()
        self.uuid = str(uuid.uuid4())
        self.construct_wano()

    @classmethod
    def instantiate_from_folder(cls,folder,wanotype, parent):
        iconpath = os.path.join(folder,wanotype) + ".png"
        if not os.path.isfile(iconpath):
            icon = QtGui.QFileIconProvider().icon(QtGui.QFileIconProvider.Computer)
            wano_icon = icon.pixmap(icon.actualSize(QtCore.QSize(128, 128)))
        else:
            wano_icon = QtGui.QIcon(iconpath)
        wano = [wanotype,folder,os.path.join(folder,wanotype) + ".xml", wano_icon]
        return cls(text=wano[0], wano=wano, parent=parent)

    def place_elements(self):
        pass

    def setColor(self,color):
        p = QtGui.QPalette()
        p.setColor(QtGui.QPalette.Button,color)
        self.setPalette(p)
        
    def get_xml(self):
        me = etree.Element("WaNo")
        me.attrib["type"] = str(self.wano[0])
        me.attrib["uuid"] = str(self.uuid)
        return me

    def instantiate_in_folder(self,folder):
        outfolder = os.path.join(folder,"wanos",self.uuid)

        try:
            os.makedirs(outfolder)
        except OSError:
            self.logger.error("Failed to create folder: %s." % outfolder)
            return False

        #print(self.wano[1],outfolder)
        if outfolder != self.wano[1]:
            try:
                copytree(self.wano[1],outfolder)
            except Exception as e:
                self.logger.error("Failed to copy tree: %s." % str(e))
                return False

        self.wano[1] = outfolder
        self.wano[2] = os.path.join(outfolder,self.wano[0]) + ".xml"
        self.wano_model.update_xml()
        return self.wano_model.save_xml(self.wano[2])

    def render(self,basefolder,stageout_basedir=""):
        #myfolder = os.path.join(basefolder,self.uuid)
        print("rendering wano with stageout_basedir %s" %stageout_basedir)
        jsdl = self.wano_model.render_and_write_input_files(basefolder,stageout_basedir=stageout_basedir)
        return jsdl

    def _target_tracker(self,event):
        self.newparent = event

    def mouseMoveEvent(self, e):
        if e.buttons() != QtCore.Qt.LeftButton:
            return

        #self.parent().removeElement(self)
        mimeData = QtCore.QMimeData()
        self.drag = QtGui.QDrag(self)
        self.drag.setMimeData(mimeData)
        self.drag.setHotSpot(e.pos() - self.rect().topLeft())
        #self.move(e.globalPos())
        self.drag.targetChanged.connect(self._target_tracker)
        self.newparent = self.parent()
        dropAction = self.drag.start(QtCore.Qt.MoveAction)

        #In case the target of the drop changed we are outside the workflow editor
        #In that case we would like to remove ourselves
        if (self.newparent != self.parent()):
            self.parent().removeElement(self)

    def clear(self):
        pass 

    def construct_wano(self):
        if not self.constructed:
            self.wano_model,self.wano_view = WaNoFactory.wano_constructor_helper(self.wano[2],None,self.wf_model)
            self.constructed = True

    def mouseDoubleClickEvent(self,e):
        if self.wano_model is None:
            self.construct_wano()
        self.parent().openWaNoEditor(self)  # pass the widget to remember it
    
    def gatherExports(self,wano,varExp,filExp,waNoNames):
        if wano == self.wano:
            return True
        if self.wano is not None:
            self.wano_instance.gatherExports(varExp,filExp,waNoNames)
        return False

class SubmitType(Enum):
    SINGLE_WANO = 1,
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
            newname = self.unique_name(element.text())
            if newname != element.text():
                element.setText(newname)
            self.elements.insert(pos, element)
            print(element)
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
        element.deleteLater()

class WFItemModel(object):
    def render_to_simple_wf(self,submitdir,jobdir):
        activities = []
        transitions = []
        wf = WFtoXML.xml_subworkflow(Transition=transitions,Activity=activities)

    #this function assembles all files relative to the workflow root
    #The files will be export to c9m:${WORKFLOW_ID}/the file name below
    def assemble_files(self):
        myfiles = []
        return myfiles

    def save_to_disk(self, complete_foldername):
        xml = []
        return xml

    def read_from_disk(self, full_foldername, xml_subelement):
        return


#Todo: hook up render, test, end
class SubWFModel(WFItemModel,WFItemListInterface):
    def __init__(self,*args,**kwargs):
        WFItemListInterface.__init__(self,*args,**kwargs)
        self.name = "SubWF"

    def render_to_simple_wf(self,submitdir,jobdir,path):
        activities = []
        transitions = []
        swfs = []
        #start = WFtoXML.xml_start()
        #activities.append(start)
        my_jobdir = os.path.join(jobdir,self.view.text())
        first = True
        if path == "":
            basepath = "%s" % self.view.text()
        else:
            basepath = "%s/%s" % (path,self.view.text())
        for myid, (ele, elename) in enumerate(zip(self.elements, self.elementnames)):

            if ele.is_wano:
                wano_dir = os.path.join(my_jobdir, self.element_to_name(ele))
                try:
                    os.makedirs(wano_dir)
                except OSError:
                    pass
                stageout_basedir = "%s/%s" %(basepath,elename)
                jsdl = ele.render(wano_dir, stageout_basedir=stageout_basedir)
                jsdl_xml = WFtoXML.xml_jsdl(jsdl=jsdl)
                toid = jsdl_xml.attrib["Id"]

                activities.append(jsdl_xml)

            else:
                # only subworkflow remaining
                swf = ele.model.render_to_simple_wf(submitdir, my_jobdir, path=basepath)
                toid = swf.attrib["Id"]
                swfs.append(swf)


            if not first:
                transition = WFtoXML.xml_transition(From=fromid, To=toid)
                transitions.append(transition)
            else:
                first = False
            fromid = toid
            # out.write(ele.uuid + "\n")

        wf = WFtoXML.xml_subworkflow(Transition=transitions, Activity=activities,SubWorkflow=swfs)
        return wf

    def assemble_files(self, path):
        # this function assembles all files relative to the workflow root
        # The files will be export to c9m:${WORKFLOW_ID}/the file name below

        myfiles = []
        for myid, (ele, name) in enumerate(zip(self.elements, self.elementnames)):
            if ele.is_wano:
                for file in ele.wano_model.get_output_files():
                    fn = os.path.join(path,self.view.text(),name, file)
                    myfiles.append(fn)
            else:
                for otherfile in ele.model.assemble_files():
                    myfiles.append(os.path.join(path,self.view.text(),otherfile))
        return myfiles

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
                model,view = ControlFactory.construct(type,qt_parent=self.view,editor=self.editor)
                self.elements.append(view)
                self.elementnames.append(name)
                view.setText(name)
                view.read_from_disk(full_foldername=full_foldername,xml_subelement=child)


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
                root.append(ele.model.save_to_disk(my_foldername))
        return root


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

    def element_to_name(self,element):
        idx = self.elements.index(element)
        return self.elementnames[idx]

    def render_to_simple_wf(self,submitdir,jobdir):
        activities = []
        transitions = []
        swfs = []
        start = WFtoXML.xml_start()
        activities.append(start)

        fromid = start.attrib["Id"]
        for myid, (ele, elename) in enumerate(zip(self.elements, self.elementnames)):
            if ele.is_wano:
                wano_dir = os.path.join(jobdir, self.element_to_name(ele))
                try:
                    os.makedirs(wano_dir)
                except OSError:
                    pass
                jsdl = ele.render(wano_dir, stageout_basedir=elename)
                jsdl_xml=WFtoXML.xml_jsdl(jsdl=jsdl)
                toid = jsdl_xml.attrib["Id"]
                activities.append(jsdl_xml)
            else:
                #only subworkflow remaining
                swf = ele.model.render_to_simple_wf(submitdir,jobdir,path ="")
                toid = swf.attrib["Id"]
                swfs.append(swf)

            transition = WFtoXML.xml_transition(From=fromid, To=toid)
            transitions.append(transition)
            fromid = toid
            #out.write(ele.uuid + "\n")

        wf = WFtoXML.xml_workflow(Transition=transitions,Activity=activities,SubWorkflow=swfs)
        return wf


    #this function assembles all files relative to the workflow root
    #The files will be export to c9m:${WORKFLOW_ID}/the file name below
    def assemble_files(self,path):
        myfiles = []
        for myid,(ele,name) in enumerate(zip(self.elements,self.elementnames)):
            if ele.is_wano:
                for file in ele.wano_model.get_output_files():
                    fn = os.path.join(name,file)
                    myfiles.append(fn)
            else:
                for otherfile in ele.model.assemble_files(path=""):
                    myfiles.append(otherfile)

        return myfiles


    def save_to_disk(self,foldername):
        success = False
        self.wf_name = os.path.basename(foldername)
        self.foldername = foldername
        settings = WaNoSettingsProvider.get_instance()
        wdir = settings.get_value(SETTING_KEYS['workflows'])

        mydir = os.path.join(self.foldername,self.wf_name)
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
                success = ele.instantiate_in_folder(foldername)
                root.append(subxml)
                if not success:
                    break
            else:
                root.append(ele.model.save_to_disk(foldername))

        if success:
            xml_path = mydir + ".xml"
            with open(xml_path,'w') as outfile:
                outfile.write(etree.tostring(root,encoding="unicode",pretty_print=True))
        return success

    def read_from_disk(self,foldername):
        self.foldername = foldername
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
                model, view = ControlFactory.construct(type, qt_parent=self.view, editor=self.editor)
                self.elements.append(view)
                self.elementnames.append(name)
                view.setText(name)
                model.read_from_disk(full_foldername=foldername, xml_subelement=child)

    def render(self):
        assert (self.foldername is not None)

        submitdir = os.path.join(self.foldername,"Submitted",str(uuid.uuid4()))
        jobdir = os.path.join(submitdir,"jobs")

        try:
            os.makedirs(jobdir)
        except OSError:
            pass

        if len(self.elements) == 1:
            ele = self.elements[0]
            if ele.is_wano:
                wano_dir = os.path.join(jobdir, self.elementnames[0])
                try:
                    os.makedirs(wano_dir)
                except OSError:
                    pass
                ele.render(wano_dir)
                return SubmitType.SINGLE_WANO,wano_dir,None

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
        newname = self.unique_name(element.text())
        if newname != element.text():
            element.setText(newname)
        if pos is not None:
            self.elements.insert(pos,element)
            self.elementnames.insert(pos,newname)
        else:
            self.elements.append(element)
            self.elementnames.append(newname)
        element.show()

    def remove_element(self,element):
        myid = self.elements.index(element)
        self.elements.remove(element)
        del self.elementnames[myid]

    def openWaNoEditor(self,wanoWidget):
        self.editor.openWaNoEditor(wanoWidget)

    def removeElement(self, element):
        # remove element both from the buttons and child list
        element.close()
        self.editor.remove(element)
        myid = self.elements.index(element)
        self.elements.remove(element)
        del self.elementnames[myid]
        element.deleteLater()


class SubWorkflowView(QtGui.QFrame):
    def __init__(self, *args, **kwargs):
        self.is_wano = False
        parent = kwargs['qt_parent']
        super(SubWorkflowView, self).__init__(parent)
        self.setFrameStyle(QtGui.QFrame.Panel)
        self.setStyleSheet("""
                           QFrame {
                            border: 2px solid green;
                            border-radius: 4px;
                            padding: 2px;
                            }
                                QPushButton {
                                 background-color: %s
                             }
                             QPushButton:hover {
                                 background-color: %s;

                             }

                           background: %s "
                           """ % (widgetColors['ButtonColor'],widgetColors['Control'],widgetColors['Control'])
                           )
        self.logger = logging.getLogger('WFELOG')
        self.setAcceptDrops(True)
        self.autoResize = False
        self.elementSkip = 20  # distance to skip between elements
        self.model = None
        #self.setFrameStyle(QtGui.QFrame.WinPanel | QtGui.QFrame.Sunken)
        self.setMinimumWidth(300)
        self.dontplace = False

    def set_model(self,model):
        self.model = model

    def text(self):
        return self.model.name

    def setText(self,text):
        self.model.name = text

    def init_from_model(self):
        self.place_elements()

    #Place elements places elements top down.
    def place_elements(self):
        self.adjustSize()
        dims = self.geometry()
        ypos = self.elementSkip / 2
        for e in self.model.elements:
            e.setParent(self)
            e.adjustSize()
            xpos = (dims.width() - e.width()) / 2
            e.move(xpos, ypos)
            e.place_elements()
            ypos += e.height() + self.elementSkip

        #self.setFixedHeight(max(ypos,self.parent().height()))
        self.adjustSize()
        if not self.dontplace:
            self.dontplace = True
            self.parent().place_elements()
        self.dontplace=False
        return ypos

    def relayout(self):
        self.place_elements()

    #Manually paint the lines:
    def paintEvent(self, event):
        super(SubWorkflowView,self).paintEvent(event)

        painter = QtGui.QPainter(self)
        painter.setBrush(QtGui.QBrush(QtCore.Qt.blue))
        sy = self.elementSkip
        #print(len(self.model.elements))
        if len(self.model.elements)>1:
            e = self.model.elements[0]
            sx = e.pos().x() + e.width()/2
            sy = e.pos().y() + e.height()
        for b in self.model.elements[1:]:
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
        for elenum,e in enumerate(self.model.elements):
            ypos += e.height() + self.elementSkip
            if ypos > position.y():
                returnnum = elenum + 1
                if returnnum > 0:
                    return returnnum

        return len(self.model.elements)

    def dropEvent(self, e):
        print("In subwf drop")
        position = e.pos()
        new_position = self._locate_element_above(position)
        if type(e.source()) is WFWaNoWidget:
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
            print("Request to instantiate WFELW: %s" % e.source())


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


class WorkflowView(QtGui.QFrame):
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
        self.setFrameStyle(QtGui.QFrame.WinPanel | QtGui.QFrame.Sunken)
        self.setMinimumWidth(300)
        self.background_drawn = True
        self.enable_background(True)

    def enable_background(self,on):
        style_sheet_without_background = "background-color: " + widgetColors['MainEditor'] + """ ;
            %s
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-position: center;  """
        if on:
            self.background_drawn = True
            script_path = os.path.dirname(os.path.realpath(__file__))
            media_path = os.path.join(script_path, "..", "Media")
            imagepath = os.path.join(media_path, "Logo_NanoMatch200.png")
            self.setStyleSheet(style_sheet_without_background % "background-image: url(%s) ;" % imagepath)
        else:
            self.background_drawn = False
            self.setStyleSheet(style_sheet_without_background % "")


    def set_model(self,model):
        self.model = model

    def init_from_model(self):
        self.place_elements()

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

        ypos = self.elementSkip / 2
        for e in self.model.elements:
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
        return ypos

    def relayout(self):
        self.place_elements()

    #Manually paint the lines:
    def paintEvent(self, event):
        super(WorkflowView,self).paintEvent(event)

        painter = QtGui.QPainter(self)
        painter.setBrush(QtGui.QBrush(QtCore.Qt.blue))
        sy = self.elementSkip
        #print(len(self.model.elements))
        if len(self.model.elements)>1:
            e = self.model.elements[0]
            sx = e.pos().x() + e.width()/2
            sy = e.pos().y() + e.height()
        for b in self.model.elements[1:]:
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
        for elenum,e in enumerate(self.model.elements):
            ypos += e.height() + self.elementSkip
            if ypos > position.y():
                returnnum = elenum + 1
                if returnnum > 0:
                    return returnnum

        return len(self.model.elements)

    def dropEvent(self, e):
        position = e.pos()
        new_position = self._locate_element_above(position)
        if type(e.source()) is WFWaNoWidget:
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
            model,view = ControlFactory.construct(name,qt_parent=self,editor=self.model.editor)
            self.model.add_element(view,new_position)


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




class WFBaseWidget(QtGui.QFrame):
    def __init__(self, editor, parent=None):
        super(WFBaseWidget, self).__init__(parent)
        self.setStyleSheet("background: " + widgetColors['Base'])
        self.logger = logging.getLogger('WFELOG')
        self.editor = editor
        self.setAcceptDrops(True)
        self.buttons = []
        self.autoResize = False
        self.topWidget = False
        self.embeddedIn = None
        self.myName = "AbstractWFTabsWidget"
        self.elementSkip = 20    # distance to skip between elements

    def clear(self):
        for e in self.buttons:
            e.clear()

        for c in self.children():
            c.deleteLater()

        self.buttons = []

    def removeElement(self,element):
        pass
        # remove element both from the buttons and child list
        try:
            element.close()
            self.buttons.remove(element)
            self.children().remove(element)
            self.placeElements()
            if len(self.buttons) == 0 and \
                hasattr(self.parent,'removePanel'):  # maybe remove the whole widget ?
                self.parent().removePanel(self)
        except IndexError:
            print ("Removing Element ",element.text()," from WFBaseWidget",self.text())

    def openWaNoEditor(self,wanoWidget):
        self.editor.openWaNoEditor(wanoWidget)

    def get_wano_variables(self):
        paths = []
        for button in self.buttons:
            #make sure everything is constructed at this point:
            #NOP for already constructed
                #if button.
            if button.is_wano:
                button.construct_wano()
        for button in self.buttons:
            if button.is_wano:
                paths.extend(button.wano_model.wano_walker_paths())

        if not self.topWidget:
            paths.extend(self.parent().get_wano_variables())
        return paths

    def sizeHint(self):
        if self.topWidget:
            s = QtCore.QSize(self.width(),self.height())
        else:
            s = QtCore.QSize(self.parent().width()-50,self.height())
        return s

    def xml(self,name="Untitled"):
        ee =  etree.Element(mapClassToTag(self.__class__.__name__),name=name)
        for e in self.buttons:
            if e.text() != "Start":
                ee.append(e.xml())
        return ee

    def remove(self,element):
        print("wff,remove")
        self.editor.remove(element)

    def dropEvent(self, e):

        super(WFBaseWidget,self).dropEvent(e)
        WFWorkflowWidget.hasChanged()
        position = e.pos()
        sender   = e.source()

        controlWidgetNames = ["While","If","ForEach","For","Parallel"]
        controlWidgetClasses = [ "WF"+a+"Widget" for a in controlWidgetNames]
        if type(sender) is WFWaNoWidget:
            sender.move(e.pos())
            sender.setParent(self)
            self.placeElementPosition(sender)
        elif type(sender).__name__ in controlWidgetClasses:
            sender.move(e.pos())
            sender.setParent(self)
            self.placeElementPosition(sender)
            sender.placeElements() # place all the buttons
        else:
            item = sender.selectedItems()[0]
            text = item.text()

            # make a new widget
            if text in controlWidgetNames:
                btn = eval("WF"+text+"Widget")(self.editor,self) #  WFWhileWidget(self)
                btn.move(e.pos())
                btn.show()
            else:
                if hasattr(item,'WaNo'):
                    btn = WFWaNoWidget(text,item.WaNo,self)
                else:
                    btn = WFWaNoWidget(text,None,self)
                btn.move(e.pos())
                btn.show()
            self.placeElementPosition(btn)
        e.accept()
        self.update()

    def parse(self,xml):
        for c in xml:
            self.logger.debug("WFBaseWidget parse" +c.tag)
            if c.tag == 'WaNo':
                w = WaNo(c)
                e = WFWaNoWidget(w.name,w,self)
            else:
                e = eval("WF"+c.tag+"Widget")(self.editor,self)
                e.parse(c)
            self.buttons.append(e)
            e.show()
        self.placeElements()


    def gatherExports(self,wano,varExp,filExp,waNoNames):
        for b in self.buttons:
            if b.gatherExports(wano,varExp,filExp,waNoNames):
                return True
        return False

    def text(self):
        return self.myName

class WFTabsWidget(QtGui.QTabWidget):
    workflow_saved = Signal(bool, str, name="WorkflowSaved")

    def __init__(self, parent):
        super(WFTabsWidget, self).__init__(parent)

        self.logger = logging.getLogger('WFELOG')

        self.acceptDrops()
        self.setAcceptDrops(True)
        self.curFile = WFFileName()
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.closeTab)

        #WFWorkflowWidget(parent,self)

        #####self.wf.embeddedIn = self   # this is the widget that needs to be reiszed when the main layout widget resizes
        #####self.addTab(selfg.wf,self.curFile.name)
        #####self.setMinimumSize(self.wf.width()+25,600) # widget with scrollbar
        self.editor = parent

        scroll,_,_ = self.createNewEmptyWF()

        self.addTab(scroll, self.curFile.name)
        self.relayout()
        self.currentChanged.connect(self._tab_changed)

        ####bb = self.tabBar().tabButton(0, QtGui.QTabBar.RightSide)
        ####bb.resize(0, 0)
    def createNewEmptyWF(self):
        scroll = QtGui.QScrollArea(self)
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
        print ("Workflow has changed ? ",WFWorkflowWidget.changedFlag)
        if WFWorkflowWidget.changedFlag:
            reply = QtGui.QMessageBox(self)
            reply.setText("The document has been modified.")
            reply.setInformativeText("Do you want to save your changes?")
            reply.setStandardButtons(QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard | QtGui.QMessageBox.Cancel)
            reply.setDefaultButton(QtGui.QMessageBox.Save)
            ret = reply.exec_()

            if ret == QtGui.QMessageBox.Cancel:
                return
            if ret == QtGui.QMessageBox.Save:
                self.save()
        self.wf.clear()
        WFWorkflowWidget.changedFlag = False
        self.tabWidget.setTabText(0,'Untitled')

    def markWFasChanged(self):
        print ("mark as changed")

    def run(self):
        name = self.tabText(self.currentIndex())
        if name == "Untitled":
            raise FileNotFoundError("Please save your workflow first")

        jobtype,directory,workflow_xml = self.currentWidget().widget().model.render()
        return name,jobtype,directory,workflow_xml

    def save(self):
        if self.curFile.name == 'Untitled':
            return self.saveAs()
        else:
            return self.saveFile(self.curFile.fullName())

    def saveAs(self):

        foldername,ok = QtGui.QInputDialog.getText(self, self.tr("Specify Workflow Name"),
                                     self.tr("Name"), QtGui.QLineEdit.Normal,
                                     "WorkflowName")

        if not ok:
            return False

        settings = WaNoSettingsProvider.get_instance()
        workflow_path = settings.get_value(SETTING_KEYS["workflows"])
        fullpath = os.path.join(workflow_path,foldername)

        if os.path.exists(fullpath):
            message = QtGui.QMessageBox.question(self,"Path already exists", "Path %s already exists? Old contents will be removed." %fullpath,QtGui.QMessageBox.Yes|QtGui.QMessageBox.Cancel)
            if message == QtGui.QMessageBox.Cancel:
                return False
            else:
                pass
                #shutil.rmtree(fullpath)

        return self.saveFile(fullpath)

    def open(self):
        fileName, filtr = QtGui.QFileDialog(self).getOpenFileName(self,'Open Workflow','.','xml (*.xml *.xm)')
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
        name    = self.curFile.name
        if index >= 0:
            self.setCurrentIndex(index)
            return

        scroll, model, view = self.createNewEmptyWF()
        if not workFlow is None:
            name = workFlow.name
            model.read_from_disk(workFlow.workflow)
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
        print (type(self.editor.parent()))
        self.workflow_saved.emit(success, folder)

    def loadFile(self,fileName):
        #missing workflow instantiation
        WFWorkflowWidget.changedFlag = False

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

class WFWorkflowWidget(WFBaseWidget):
    changedFlag     = False
    activeTabWidget = None


    def __init__(self, editor,  parent):
        super(WFWorkflowWidget, self).__init__(editor,parent)
        self.acceptDrops()
        self.topWidget  = True
        self.autoResize = True
        self.parent = parent
        self.myName = "WFWorkflowWidget"
        self.style_sheet_without_background = "background-color: " + widgetColors['MainEditor'] + """ ;
                              %s
                              background-repeat: no-repeat;
                              background-attachment: fixed;
                              background-position: center;  """
        self.background_drawn = True
        script_path = os.path.dirname(os.path.realpath(__file__))
        media_path = os.path.join(script_path,"..","Media")

        imagepath = os.path.join(media_path,"Logo_NanoMatch200.png")
        self.setStyleSheet(self.style_sheet_without_background % "background-image: url(%s) ;" %imagepath)

        self.setMinimumWidth(300)
        self.setFrameStyle(QtGui.QFrame.WinPanel | QtGui.QFrame.Sunken)

    def recPlaceElements(self):
        if self.background_drawn:
            self.setStyleSheet(self.style_sheet_without_background %"")
            self.background_drawn = False
        ypos = max(self.placeOwnButtons(), self.parent.height())
        self.setFixedHeight(ypos)

    @staticmethod
    def hasChanged():
        logger = logging.getLogger('WFELOG')
        logger.info("WorkFlow has changed")
        WFWorkflowWidget.changedFlag=True
        if WFWorkflowWidget.activeTabWidget != None:
            tt = WFWorkflowWidget.activeTabWidget.tabText(0)
            if tt[-1] != '*':
                tt += '*'
                WFWorkflowWidget.activeTabWidget.setTabText(0,tt)

    @staticmethod
    def unChanged():
        logger = logging.getLogger('WFELOG')
        logger.info("WorkFlow has changed")
        WFWorkflowWidget.changedFlag=True


class WFControlWidget(QtGui.QFrame):
    def __init__(self, editor, parent=None):
        super(WFControlWidget, self).__init__(parent) 
        self.logger = logging.getLogger('WFELOG')
        self.editor = editor
      
        self.is_wano = False
        self.setFrameStyle(QtGui.QFrame.Panel)
        self.setStyleSheet("""
                           QFrame {
                            border: 2px solid green;
                            border-radius: 4px;
                            padding: 2px;
                            }
                                QPushButton {
                                 background-color: %s
                             }
                             QPushButton:hover {
                                 background-color: %s;

                             }

                           background: %s "
                           """ % (widgetColors['ButtonColor'],widgetColors['Control'],widgetColors['Control'])
                           )
        self.setAcceptDrops(True)
        self.isVisible = True     # the subwidget are is visible
        self.layout    = QtGui.QVBoxLayout()
        
        noPar=self.makeTopLine()
        self.wf = []
        self.hidden = []
        self.bottomLayout = QtGui.QHBoxLayout()
        self.elementSkip = 0 
        for i in range(noPar):
            wf = WFBaseWidget(editor,self)
            self.elementSkip = max(self.elementSkip,wf.elementSkip)
            wf.myName = self.myName + ("WF%i" % i)
            wf.setFrameStyle(QtGui.QFrame.WinPanel | QtGui.QFrame.Sunken) 
            wf.autoResize = True
            self.wf.append(wf)
            if self.isVisible:
                self.bottomLayout.addWidget(wf)
            
        self.layout.addLayout(self.topLineLayout)
        self.layout.addLayout(self.bottomLayout)
        
        self.setLayout(self.layout)
        self.show()

    def get_wano_variables(self):
        pass
    def construct_wano(self):
        pass
    
    def clear(self):
        for w in self.wf:
            w.clear()
            w.deleteLater()
    
    def gatherExports(self,wano,varExp,filExp,waNoNames):
        self.logger.error('gather exports for control elements not implemented')
        pass
    
    def parse(self,xml):
        print ("Unknown FunctionXXX")
        pass 

    def toggleVisible(self):
        if self.isVisible: # remove widget from bottomlayout
            for w in self.wf:
                self.bottomLayout.takeAt(0)
                w.setParent(None)
            self.hidden = self.wf
            self.wf = []
        else:
            for w in self.hidden:
                self.bottomLayout.addWidget(w)
                w.show()
            self.wf = self.hidden
            self.hidden = []
          
        self.recPlaceElements()
        self.bottomLayout.update()
        self.update()
        self.isVisible = not self.isVisible
        
    def text(self):
        return self.myName 
    
    def placeElements(self):
        print ("Place Elements",self.text())
        for w in self.wf:
            w.placeElements()
        
    def recPlaceElements(self): 
        # redo your own buttons and then do the parent
        ypos = 0 
        if len(self.wf) > 0:
            for w in self.wf:
                ypos=max(ypos,w.placeOwnButtons())
            #print ("WFControlElement Child Height:",ypos)
            ypos = max(ypos,2*self.elementSkip)
            self.setFixedHeight(ypos+2.25*self.elementSkip) 
            for w in self.wf:
                w.setFixedHeight(ypos) 
        else:
            self.setFixedHeight(50)
        self.update()  
        self.parent().recPlaceElements()
                  
    def sizeHint(self):
        hh = max(self.height(),100)
        s = QtCore.QSize(self.parent().width()-50,hh) 
        return s        
    
    def mouseMoveEvent(self, e):
        if e.buttons() == QtCore.Qt.LeftButton:   
            self.parent().removeElement(self)
            mimeData = QtCore.QMimeData()
            drag = QtGui.QDrag(self)
            drag.setMimeData(mimeData)
            drag.setHotSpot(e.pos() - self.rect().topLeft())
            self.move(e.globalPos())
            dropAction = drag.start(QtCore.Qt.MoveAction)

class WFWhileWidget(WFControlWidget):
    def __init__(self, editor,  parent=None):
        super(WFWhileWidget, self).__init__(editor,  parent)      
        
    def makeTopLine(self):
        self.myName = 'While'
        self.topLineLayout = QtGui.QHBoxLayout()
        b = QtGui.QPushButton(self.myName)
        b.clicked.connect(self.toggleVisible)
        self.topLineLayout.addWidget(b)  
        self.topLineLayout.addWidget(QtGui.QLineEdit('condition'))
        return 1
    
class WFIfWidget(WFControlWidget):
    def __init__(self, editor,  parent=None):
        super(WFIfWidget, self).__init__(editor,  parent)      
        
    def makeTopLine(self):
        self.myName = 'If'
        self.topLineLayout = QtGui.QHBoxLayout()
        b = QtGui.QPushButton(self.myName)
        b.clicked.connect(self.toggleVisible)
        self.topLineLayout.addWidget(b)  
        self.topLineLayout.addWidget(QtGui.QLineEdit('condition'))
        return 2

class WFForEachWidget(WFControlWidget):
    def __init__(self, editor,  parent=None):
        super(WFForEachWidget, self).__init__(editor,  parent)      
        
    def makeTopLine(self):
        self.myName = 'ForEach'
        self.topLineLayout = QtGui.QHBoxLayout()
        b = QtGui.QPushButton(self.myName)
        b.clicked.connect(self.toggleVisible)
        self.topLineLayout.addWidget(b)   
        self.topLineLayout.addWidget(QtGui.QLineEdit('Variable Name'))
        self.list_of_variables = QtGui.QLineEdit('')
        self.topLineLayout.addWidget(self.list_of_variables)
        self.open_variables = MultiselectDropDownList(self,text="Import")
        self.open_variables.itemSelectionChanged.connect(self.onItemSelectionChange)
        self.open_variables.connect_workaround(self._load_variables)
        self.topLineLayout.addWidget(self.open_variables)
        return 1

    def _load_variables(self):
        parent = self.parent()
        while not parent.topWidget:
            parent = parent.parent()
        vars = parent.get_wano_variables()
        self.open_variables.set_items(vars)

    def onItemSelectionChange(self):
        self.list_of_variables.setText(" ".join(self.open_variables.get_selection()))


class WFParallelWidget(WFControlWidget):
    def __init__(self, editor, parent=None):
        super(WFParallelWidget, self).__init__(editor,  parent)      
        
    def makeTopLine(self):
        self.myName = 'Parallel'
        self.topLineLayout = QtGui.QHBoxLayout()
        b = QtGui.QPushButton(self.myName)
        b.clicked.connect(self.toggleVisible)
        self.topLineLayout.addWidget(b)  
        a = QtGui.QPushButton('Add')
        a.clicked.connect(self.addWF)
        self.topLineLayout.addWidget(a) 
        return 2
    
    #----------------------------------------------------------------------
    def removePanel(self,panel):
        """"""
        if self.bottomLayout.count() > 2: # 2 panels min
            print ("remove panel",panel.text())
            try:
                index = self.bottomLayout.indexOf(panel)
            except IndexError:
                print ("Error Panel not found",panel.text())
            
            print ("Index",index)
            if self.isVisible:
                self.wf.remove(panel)
            else:
                self.hidden.remove(panel)
            widget = self.bottomLayout.takeAt(index).widget()
            widget.setParent(None)
            if widget is not None: 
                # widget will be None if the item is a layout
                widget.deleteLater()
            
    
    def addWF(self):
        if not self.isVisible:
            self.toggleVisible()
        wf = WFBaseWidget(self.editor,self)
        self.elementSkip = max(self.elementSkip,wf.elementSkip)
        wf.myName = self.myName + "WF" + str(self.bottomLayout.count())
        wf.setFrameStyle(QtGui.QFrame.WinPanel | QtGui.QFrame.Sunken) 
        wf.autoResize = True
        self.wf.append(wf)       
        self.bottomLayout.addWidget(wf)
        self.placeElements()
        
 
    def parse(self,xml):
        count = 0
        for c in xml:      
            if c.tag != 'Base':
                self.logger.error("Found Tag ",c.tag, " in control block")
            else:
                if count > 2:
                    self.addWF() 
                self.wf[count].parse(c)
                count += 1
        if count != len(self.wf):
            self.logger.error("Not enough base widgets in control element")


class ControlFactory(object):
    n_t_c = {
        "ForEach" : (WFForEachWidget,None),
        "While" : (WFWhileWidget,None),
        "If": (WFIfWidget,None),
        "Parallel": (WFParallelWidget, None),
        "SubWorkflow": (SubWFModel,SubWorkflowView)
    }
    @classmethod
    def name_to_class(cls,name):
        return cls.n_t_c[name]

    @classmethod
    def construct(cls, name, qt_parent,editor):
        modelc,viewc = cls.name_to_class(name)
        view = viewc(qt_parent=qt_parent)
        model = modelc(editor=editor,view=view)
        view.set_model(model)
        view.init_from_model()
        return model,view


