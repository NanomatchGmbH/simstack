import copy
import hashlib
import logging
import os
import traceback
import uuid
from enum import Enum
from pathlib import Path

import PySide6.QtCore as QtCore
import PySide6.QtGui as QtGui
import PySide6.QtWidgets as QtWidgets
from lxml import etree

import SimStackServer.WaNo.WaNoFactory as WaNoFactory
from SimStackServer.WaNo.AbstractWaNoModel import WaNoInstantiationError
from SimStackServer.WaNo.MiscWaNoTypes import WaNoListEntry, get_wano_xml_path
from SimStackServer.Util.FileUtilities import copytree_pathlib
from SimStackServer.WorkflowModel import WorkflowExecModule
from SimStackServer.WaNo.WaNoModels import WaNoModelRoot

from .wf_editor_base import DragDropTargetTracker, widgetColors


class SubmitType(Enum):
    SINGLE_WANO = 0
    WORKFLOW = 1


class WFWaNoWidget(QtWidgets.QToolButton, DragDropTargetTracker):
    def __init__(self, text, wano: WaNoListEntry, parent):
        super().__init__(parent)
        self.manual_init()
        self.logger = logging.getLogger("WFELOG")
        self.moved = False
        lvl = self.logger.getEffectiveLevel()  # switch off too many infos
        self.logger.setLevel(logging.ERROR)
        self.is_wano = True
        self.logger.setLevel(lvl)
        self.wf_model = parent.model.get_root()
        stylesheet = """
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

        """ % widgetColors["ButtonColor"]
        self.setStyleSheet(stylesheet)  # + widgetColors['WaNo'])
        self.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)
        self.setText(text)
        self.setIcon(QtGui.QIcon(wano.icon))
        self._wano_type = wano.name
        # self.setAutoFillBackground(True)
        # self.setColor(QtCore.Qt.lightGray)
        self.wano = copy.copy(wano)
        self.model = self
        self.view = self
        self.wano_model: WaNoModelRoot = None
        self.wano_view = None
        self.constructed = False
        self.uuid = str(uuid.uuid4())
        self.construct_wano()
        self.name = self.text()
        # today int he evening: add info on aiida node ids, while executing workflow.
        # read output and check if it actually works

    @classmethod
    def instantiate_from_folder(cls, folder, delta_wano_dir, wanotype, parent):
        folder = Path(folder)
        iconpath = folder / (wanotype + ".png")
        if not os.path.isfile(iconpath):
            icon = QtWidgets.QFileIconProvider().icon(
                QtWidgets.QFileIconProvider.Computer
            )
            wano_icon = icon.pixmap(icon.actualSize(QtCore.QSize(128, 128)))
        else:
            wano_icon = QtGui.QIcon(str(iconpath))
        uuid = delta_wano_dir.name
        wano = WaNoListEntry(name=wanotype, folder=folder, icon=wano_icon)
        # [wanotype,folder,os.path.join(folder,wanotype) + ".xml", wano_icon]
        returnobject = cls(text=wano.name, wano=wano, parent=parent)
        # overwrite old uuid
        returnobject.uuid = uuid
        try:
            returnobject._read_delta(delta_wano_dir)
        except FileNotFoundError as e:
            # This is V1 support, in this case we do not actually have a delta.
            if delta_wano_dir == folder:
                pass
            else:
                raise e from e
        return returnobject

    def save_delta(self, foldername):
        outfolder = foldername / "wano_configurations" / str(self.uuid)
        os.makedirs(outfolder, exist_ok=True)
        print(f"Saving to {outfolder}")
        if self.wano_model is not None:
            self.wano_model.save(outfolder)

    def _read_delta(self, foldername):
        self.wano_model.read(foldername)
        self.wano_model.update_views_from_models()

    def place_elements(self):
        pass

    def setText(self, *args, **kwargs):
        self.name = args[0]
        super().setText(*args, **kwargs)

    def mouseMoveEvent(self, e):
        self.mouseMoveEvent_feature(e)

    def setColor(self, color):
        p = QtGui.QPalette()
        p.setColor(QtGui.QPalette.Button, color)
        self.setPalette(p)

    def get_xml(self):
        me = etree.Element("WaNo")
        me.attrib["type"] = str(self.wano.name)
        me.attrib["uuid"] = str(self.uuid)
        return me

    def _compare_wano_equality(self, wano1: WaNoListEntry, wano2: WaNoListEntry):
        xml1 = get_wano_xml_path(wano1.folder, wano_name_override=wano1.name)
        md51 = hashlib.md5()
        with xml1.open("rb") as infile:
            md51.update(infile.read())
        md52 = hashlib.md5()
        xml2 = get_wano_xml_path(wano2.folder, wano_name_override=wano1.name)
        with xml2.open("rb") as infile:
            md52.update(infile.read())
        return md51.hexdigest() == md52.hexdigest()

    def instantiate_in_folder(self, folder):
        outfolder: Path = folder / "wanos" / self.wano.name

        folder_exists = outfolder.is_dir()
        if not folder_exists:
            os.makedirs(outfolder)
            folder_empty = True
        else:
            folder_empty = not any(outfolder.iterdir())

        if outfolder != self.wano.folder:
            # In case we did not create the folder, the wano might already be there and we need
            # to check whether the same WaNo is in the folder. Otherwise problems might occur.
            if folder_exists and not folder_empty:
                newfolderwle = copy.copy(self.wano)
                newfolderwle.folder = outfolder
                if self._compare_wano_equality(newfolderwle, self.wano):
                    self.wano.folder = outfolder
                    self.wano_model.set_wano_dir_root(outfolder)
                    # self.logger.info(f"Directory {outfolder} already instantiated with equivalent WaNo.")
                    return True
                else:
                    raise WaNoInstantiationError(
                        f"Directory {outfolder} already instantiated with different WaNo with equivalent name in folder {self.wano.folder}. Please check, if you imported two different WaNos (e.g. by porting an old version workflow)."
                    )
            try:
                print("Copying %s to %s" % (self.wano.folder, outfolder))
                copytree_pathlib(self.wano.folder, outfolder)

            except Exception as e:
                self.logger.error("Failed to copy tree: %s." % str(e))

                traceback.print_exc()
                return False

        self.wano.folder = outfolder
        self.wano_model.set_wano_dir_root(outfolder)

        # self.wano_model.save(outfolder)
        return True

    def render(self, path_list, output_path_list, basefolder, stageout_basedir=""):
        # myfolder = os.path.join(basefolder,self.uuid)
        print("rendering wano with stageout_basedir %s" % stageout_basedir)
        jsdl, wem = self.wano_model.render_and_write_input_files_newmodel(
            basefolder, stageout_basedir=stageout_basedir
        )
        wem: WorkflowExecModule
        mywem = copy.deepcopy(wem)
        mywem.resources.overwrite_unset_fields_from_default_resources(
            self.wf_model.base_resource_during_render()
        )
        mywem.set_wano_xml(self.wano_model.name + ".xml")
        return jsdl, mywem, path_list + [wem.name]

    def clear(self):
        pass

    def construct_wano(self):
        if not self.constructed:
            self.wano_model, self.wano_view = WaNoFactory.wano_constructor(self.wano)
            self.wano_model.set_parent_wf(self.wf_model)
            self.wano_model.datachanged_force()
            self.constructed = True

    def mouseDoubleClickEvent(self, e):
        if self.wano_model is None:
            self.construct_wano()
        self.parent().openWaNoEditor(self)  # pass the widget to remember it

    def get_variables(self):
        if self.wano_model is not None:
            return self.wano_model.get_all_variable_paths()
        return []


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