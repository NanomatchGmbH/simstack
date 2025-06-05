import pathlib
import shutil
import os

import logging
import traceback

import abc

from os.path import join
from pathlib import Path


import PySide6.QtCore as QtCore
import PySide6.QtGui as QtGui
import PySide6.QtWidgets as QtWidgets
from PySide6.QtCore import Signal

from SimStackServer.WorkflowModel import (
    Resources,
)
from SimStackServer.WaNo.MiscWaNoTypes import WaNoListEntry
from simstack.SimStackPaths import SimStackPaths
from simstack.WaNoSettingsProvider import WaNoSettingsProvider
from simstack.Constants import SETTING_KEYS

from simstack.view.RemoteImporterDialog import RemoteImporterDialog
from simstack.view.WFEditorWidgets import WFEWaNoListWidget, WFEListWidget

from .wf_editor_base import DragDropTargetTracker, widgetColors
from .wf_editor_widgets import WFWaNoWidget
from .wf_editor_models import (
    WFModel,
)


# ControlFactory import will be done at runtime to avoid circular imports
def _get_control_factory():
    from .wf_editor_factory import ControlFactory

    return ControlFactory


class SubWorkflowView(QtWidgets.QFrame):
    def __init__(self, *args, **kwargs):
        self.my_height = 50
        self.my_width = 300
        self.minimum_height = 50
        self.minimum_width = 300
        self.is_wano = False
        self.logical_parent = kwargs["logical_parent"]
        parent = kwargs["qt_parent"]
        super().__init__(parent)
        self.setFrameStyle(QtWidgets.QFrame.Panel)
        self.setStyleSheet(
            """
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


                           """
            % (
                widgetColors["Control"],
                widgetColors["ButtonColor"],
                widgetColors["Control"],
            )
        )
        self.logger = logging.getLogger("WFELOG")
        self.setAcceptDrops(True)
        self.autoResize = False
        self.elementSkip = 20  # distance to skip between elements
        self.model = None
        # self.setFrameStyle(QtGui.QFrame.WinPanel | QtGui.QFrame.Sunken)
        self.setMinimumWidth(300)
        self.setMinimumWidth(100)
        self.dontplace = False
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )

    def set_model(self, model):
        self.model = model

    def text(self):
        return self.model.name

    def setText(self, text):
        self.model.name = text

    def init_from_model(self):
        self.relayout()

    def set_minimum_width(self, minimum_width):
        self.minimum_width = minimum_width

    # Place elements places elements top down.
    def place_elements(self):
        self.my_width = self.minimum_width
        self.adjustSize()

        for model in self.model.elements:
            e = model.view
            self.my_width = max(self.my_width, e.width() + 50)

        self.adjustSize()

        dims = self.geometry()
        ypos = int(self.elementSkip // 2)
        for model in self.model.elements:
            e = model.view
            e.setParent(self)

            e.adjustSize()
            xpos = int((dims.width() - e.width()) // 2)
            # xpos = dims.width()/2.0
            e.move(xpos, ypos)
            e.place_elements()
            ypos += e.height() + self.elementSkip

        self.my_height = ypos
        self.adjustSize()
        # self.setFixedHeight(max(ypos,self.parent().height()))
        if not self.dontplace:
            self.dontplace = True
            # self.logical_parent.place_elements()
        self.dontplace = False
        # if (ypos < 50):
        #    self.setFixedHeight(50)
        self.updateGeometry()
        return ypos

    def sizeHint(self):
        return QtCore.QSize(
            max(self.minimum_width, self.my_width),
            max(self.my_height, self.minimum_height),
        )

    def relayout(self):
        self.model.get_root().view.relayout()
        # self.model.get_root().view.place_elements()
        # self.model.get_root().view.place_elements()
        # self.place_elements()

    # Manually paint the lines:
    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QtGui.QPainter(self)
        painter.setBrush(QtGui.QBrush(QtCore.Qt.blue))
        sy = self.elementSkip
        # print(len(self.model.elements))
        if len(self.model.elements) > 1:
            e = self.model.elements[0].view
            sx = int(e.pos().x() + e.width() // 2)
            sy = e.pos().y() + e.height()
        for model in self.model.elements[1:]:
            b = model.view
            ey = b.pos().y()
            line = QtCore.QLine(sx, sy, sx, ey)
            painter.drawLine(line)
            sy = b.pos().y() + b.height()
        painter.end()

    def dragEnterEvent(self, e):
        e.accept()

    def _locate_element_above(self, position):
        ypos = 0
        if len(self.model.elements) <= 1:
            return 0
        for elenum, model in enumerate(self.model.elements):
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
        if isinstance(e.source(), WFWaNoWidget) or isinstance(
            e.source(), WFControlWithTopMiddleAndBottom
        ):
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

        elif isinstance(e.source(), WFEWaNoListWidget):
            wfe = e.source()
            dropped = wfe.selectedItems()[0]
            wano = dropped.WaNo
            try:
                wd = WFWaNoWidget(wano.name, wano, self)
            except Exception as e:
                tb = traceback.format_exc().replace("\n", "\n<br/>")
                messageboxtext = (
                    f"<H3>Encountered error when inserting WaNo.</H3>\n\n Error was: {e}\n <hr/>"
                    f"<it>Trace: {tb}</it>"
                )
                QtWidgets.QMessageBox.about(
                    None, "Exception in WaNo construction", messageboxtext
                )
                return
            self.model.add_element(wd, new_position)
            # Show required for widgets added after
            wd.show()

        elif isinstance(e.source(), WFEListWidget):
            wfe = e.source()
            dropped = wfe.selectedItems()[0]
            name = dropped.text()
            model, view = _get_control_factory().construct(
                name,
                qt_parent=self,
                logical_parent=self,
                editor=self.model.editor,
                wf_root=self.model.wf_root,
            )
            self.model.add_element(model, new_position)

        else:
            print(
                "Type %s not yet accepted by dropevent, please implement" % (e.source())
            )
            return
        e.setDropAction(QtCore.Qt.MoveAction)
        self.relayout()

    def openWaNoEditor(self, wanoWidget):
        self.model.openWaNoEditor(wanoWidget)

    def removeElement(self, element):
        self.model.removeElement(element)
        self.relayout()


class WorkflowView(QtWidgets.QFrame):
    def __init__(self, *args, **kwargs):
        parent = kwargs["qt_parent"]
        super().__init__(parent)

        self.setStyleSheet("background: " + widgetColors["Base"])
        self.logger = logging.getLogger("WFELOG")
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

    def enable_background(self, on):
        style_sheet_without_background = (
            "QFrame { background-color: "
            + widgetColors["MainEditor"]
            + """ ;
            %s
            background-repeat: no-repeat;
            background-attachment: fixed;
            background-position: center;
            }
        """
        )
        if on:
            self.background_drawn = True
            script_path = os.path.dirname(os.path.realpath(__file__))
            media_path = os.path.join(script_path, "..", "Media")
            imagepath = os.path.join(media_path, "Logo_NanoMatch200.png")
            imagepath = imagepath.replace("\\", "/")
            background_sheet = (
                style_sheet_without_background
                % 'background-image: url("%s") ;'
                % imagepath
            )
            self.setStyleSheet(background_sheet)
        else:
            self.background_drawn = False
            self.setStyleSheet(style_sheet_without_background % "")

    def set_model(self, model):
        self.model = model

    def init_from_model(self):
        self.relayout()

    # Place elements places elements top down.
    def place_elements(self):
        if len(self.model.elements) == 0:
            self.enable_background(True)
            return

        if self.background_drawn:
            self.enable_background(False)

        self.adjustSize()
        dims = self.geometry()

        # print(dims)
        ypos = 0
        if not self.dont_place:
            self.dont_place = True
            ypos = int(self.elementSkip // 2)
            for model in self.model.elements:
                e = model.view
                e.setParent(self)
                e.adjustSize()
                xpos = int((dims.width() - e.width()) // 2)
                # print("WIDTH ",e.width())
                # print("HEIGHT ", e.height())
                # print(xpos,ypos)
                e.move(xpos, ypos)
                e.place_elements()
                ypos += e.height() + self.elementSkip

            self.setFixedHeight(max(ypos, self.parent().height()))
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

        # self.place_elements()

    # Manually paint the lines:
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QtGui.QPainter(self)
        painter.setBrush(QtGui.QBrush(QtCore.Qt.blue))
        sy = self.elementSkip
        # print(len(self.model.elements))
        if len(self.model.elements) > 1:
            e = self.model.elements[0].view
            sx = int(e.pos().x() + e.width() // 2)
            sy = e.pos().y() + e.height()
        for model in self.model.elements[1:]:
            b = model.view
            ey = b.pos().y()
            line = QtCore.QLine(sx, sy, sx, ey)
            painter.drawLine(line)
            sy = b.pos().y() + b.height()
        painter.end()

    def dragEnterEvent(self, e):
        e.accept()

    def _locate_element_above(self, position):
        ypos = 0
        if len(self.model.elements) <= 1:
            return 0
        for elenum, model in enumerate(self.model.elements):
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
        if isinstance(e.source(), WFWaNoWidget) or isinstance(
            e.source(), WFControlWithTopMiddleAndBottom
        ):
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

        elif isinstance(e.source(), WFEWaNoListWidget):
            wfe = e.source()
            dropped = wfe.selectedItems()[0]
            wano: WaNoListEntry = dropped.WaNo
            try:
                wd = WFWaNoWidget(wano.name, wano, self)
            except Exception as e:
                tb = traceback.format_exc().replace("\n", "\n<br/>")
                messageboxtext = (
                    f"<H3>Encountered error when inserting WaNo.</H3>\n\n Error was: {e}\n <hr/>"
                    f"<it>Trace: {tb}</it>"
                )
                QtWidgets.QMessageBox.about(
                    None, "Exception in WaNo construction", messageboxtext
                )
                return
            ##self.model.add_element(new_position,wd)
            self.model.add_element(wd, new_position)
            # Show required for widgets added after
            wd.show()

        elif isinstance(e.source(), WFEListWidget):
            wfe = e.source()
            dropped = wfe.selectedItems()[0]
            name = dropped.text()
            model, view = _get_control_factory().construct(
                name,
                qt_parent=self,
                logical_parent=self,
                editor=self.model.editor,
                wf_root=self.model,
            )
            self.model.add_element(model, new_position)

        else:
            print(
                "Type %s not yet accepted by dropevent, please implement" % (e.source())
            )
            return
        e.setDropAction(QtCore.Qt.MoveAction)
        self.relayout()

    def openWaNoEditor(self, wanoWidget):
        self.model.openWaNoEditor(wanoWidget)

    def removeElement(self, element):
        self.model.removeElement(element)
        self.relayout()


class WFTabsWidget(QtWidgets.QTabWidget):
    workflow_saved = Signal(bool, str, name="WorkflowSaved")
    changedFlag = False

    def __init__(self, parent):
        super().__init__(parent)

        self.logger = logging.getLogger("WFELOG")

        self.acceptDrops()
        self.setAcceptDrops(True)
        # self.curFile = WFFileName()
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.closeTab)

        # WFWorkflowWidget(parent,self)

        #####self.wf.embeddedIn = self   # this is the widget that needs to be reiszed when the main layout widget resizes
        #####self.addTab(selfg.wf,self.curFile.name)
        #####self.setMinimumSize(self.wf.width()+25,600) # widget with scrollbar
        self.editor = parent

        scroll, _, _ = self.createNewEmptyWF()

        self.addTab(scroll, "Untitled")
        self.relayout()
        self.currentChanged.connect(self._tab_changed)

        ####bb = self.tabBar().tabButton(0, QtGui.QTabBar.RightSide)
        ####bb.resize(0, 0)

    def createNewEmptyWF(self):
        scroll = QtWidgets.QScrollArea(self)
        wf = WorkflowView(qt_parent=scroll)
        wf_model = WFModel(editor=self.editor, view=wf)
        wf.set_model(wf_model)
        wf.init_from_model()
        scroll.setWidget(wf)
        scroll.setMinimumWidth(300)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll.setWidgetResizable(True)
        return scroll, wf_model, wf

    def clear(self):
        # print ("Workflow has changed ? ",WFWorkflowWidget.changedFlag)
        if self.changedFlag:
            reply = QtWidgets.QMessageBox(self)
            reply.setText("The document has been modified.")
            reply.setInformativeText("Do you want to save your changes?")
            reply.setStandardButtons(
                QtWidgets.QMessageBox.Save
                | QtWidgets.QMessageBox.Discard
                | QtWidgets.QMessageBox.Cancel
            )
            reply.setDefaultButton(QtWidgets.QMessageBox.Save)
            ret = reply.exec_()

            if ret == QtWidgets.QMessageBox.Cancel:
                return
            if ret == QtWidgets.QMessageBox.Save:
                self.save()
        self.wf.clear()
        self.changedFlag = False
        self.tabWidget.setTabText(0, "Untitled")

    def markWFasChanged(self):
        print("mark as changed")

    def run(self, current_registry: Resources):
        name = self.tabText(self.currentIndex())
        if name == "Untitled":
            # FIXME this should be a custom exception. It should also be caught as Custom in WFEA
            raise FileNotFoundError("Please save your workflow first")

        self.save()
        # name,jobtype,directory,wf_xml = editor.run()

        jobtype, directory, workflow_xml = (
            self.currentWidget()
            .widget()
            .model.render(given_name=name, current_registry=current_registry)
        )
        return name, jobtype, directory, workflow_xml

    def currentTabText(self):
        myindex = self.currentIndex()
        return self.tabText(myindex)

    def save(self):
        if self.currentTabText() == "Untitled":
            return self.saveAs()
        else:
            settings = WaNoSettingsProvider.get_instance()
            workflow_path = settings.get_value(SETTING_KEYS["workflows"])
            if workflow_path == "<embedded>":
                workflow_path = join(SimStackPaths.get_embedded_path(), "workflows")
            foldername = self.currentTabText()
            workflow_path = Path(workflow_path)
            fullpath = workflow_path / foldername
            return self.saveFile(fullpath)

    illegal_chars = r"<>|\#~*´`"

    def _contains_illegal_chars(self, wfname):
        if any((c in self.illegal_chars) for c in wfname):
            return True
        return False

    def _remove_wf_contents(self, foldername: pathlib.Path):
        fullpath_path = Path(foldername)
        assert fullpath_path.is_dir(), "Given path has to be directory."
        assert (
            fullpath_path / "wanos"
        ).is_dir(), "When overwriting an old workflow, the old directory has to include a wanos directory."
        assert fullpath_path != Path.home(), "Path cannot be home directory."
        assert fullpath_path != fullpath_path.anchor, "Path cannot be filesystem root."
        wanodir = fullpath_path / "wanos"
        wanoconfigdir = fullpath_path / "wano_configurations"
        xmlpath = fullpath_path / f"{fullpath_path.name}.xml"
        shutil.rmtree(wanodir)
        if wanoconfigdir.is_dir():
            shutil.rmtree(wanoconfigdir)
        os.unlink(xmlpath)

    def saveAs(self):
        foldername, ok = QtWidgets.QInputDialog.getText(
            self,
            self.tr("Specify Workflow Name"),
            self.tr("Name"),
            QtWidgets.QLineEdit.Normal,
            "WorkflowName",
        )

        if not ok:
            return False

        if self._contains_illegal_chars(foldername):
            messageboxtext = (
                "Workflowname was %s. It cannot contain the following characters: %s"
                % (foldername, self.illegal_chars)
            )
            QtWidgets.QMessageBox.critical(None, "Workflowname invalid", messageboxtext)
            return False

        settings = WaNoSettingsProvider.get_instance()
        workflow_path = settings.get_value(SETTING_KEYS["workflows"])
        if workflow_path == "<embedded>":
            workflow_path = join(SimStackPaths.get_embedded_path(), "workflows")
        workflow_path = Path(workflow_path)
        fullpath = workflow_path / foldername

        if fullpath.exists():
            curtab = self.currentTabText()
            if curtab != "Untitled":
                if curtab == foldername:
                    messageboxtext = f"Chosen workflow directory {foldername} is the same as already save workflow with name {curtab}. Cannot overwrite a workflow with itself. Please choose a different directory."
                    QtWidgets.QMessageBox.critical(
                        None, "Workflowname invalid", messageboxtext
                    )
                    return False

            message = QtWidgets.QMessageBox.question(
                self,
                "Path already exists",
                "Path %s already exists? Old contents will be removed." % fullpath,
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel,
            )
            if message == QtWidgets.QMessageBox.Cancel:
                return False
            else:
                self._remove_wf_contents(fullpath)

        return self.saveFile(fullpath)

    def open(self):
        fileName, filtr = QtWidgets.QFileDialog(self).getOpenFileName(
            self, "Open Workflow", ".", "xml (*.xml *.xm)"
        )
        if fileName:
            print("Loading Workflow from File:", fileName)
            self.clear()
            self.loadFile(fileName)

    def get_index(self, name):
        for i in range(0, self.count()):
            if self.tabText(i) == name:
                return i

        return -1

    def _tab_changed(self):
        self.relayout()

    def openWorkFlow(self, workFlow):
        index = self.get_index(workFlow.name) if workFlow is not None else -1
        # name    = self.curFile.name
        if index >= 0:
            self.setCurrentIndex(index)
            return

        scroll, model, view = self.createNewEmptyWF()
        if workFlow is not None:
            name = workFlow.name
            model.read_from_disk(workFlow.workflow)
        else:
            name = "Untitled"
        self.addTab(scroll, name)
        view.relayout()
        self.relayout()
        self.setCurrentIndex(self.count() - 1)

    def closeTab(self, e):
        # this works recursively
        if self.parent().lastActive is not None:
            # close wano editor
            self.parent().wanoEditor.deleteClose()
        self.removeTab(e)

    def relayout(self):
        if self.count() == 0:
            self.openWorkFlow(None)
        self.currentWidget().widget().relayout()

    # Executed everytime the widget is shown / hidden, etc.
    # Required to have correct initial layout
    def showEvent(self, event):
        super().showEvent(event)
        self.relayout()

    def saveFile(self, folder):
        # widget is scroll
        success = self.currentWidget().widget().model.save_to_disk(folder)
        # self.wf_model.save_to_disk(folder)
        self.setTabText(self.currentIndex(), os.path.basename(folder))
        # print (type(self.editor.parent()))
        self.workflow_saved.emit(success, str(folder))

    # def sizeHint(self):
    #    return QtCore.QSize(500,500)


#
#  editor is the workflow editor that can open/close the WaNo editor
#
class WFFileName:
    def __init__(self):
        self.dirName = "."
        self.name = "Untitled"
        self.ext = "xml"

    def fullName(self):
        return os.path.join(self.dirName, self.name + "." + self.ext)


class WFControlWithTopMiddleAndBottom(QtWidgets.QFrame, DragDropTargetTracker):
    def __init__(self, *args, **kwargs):
        parent = kwargs["qt_parent"]
        self.logical_parent = kwargs["logical_parent"]
        super().__init__(parent)
        self.manual_init()
        # self.editor = kwargs["editor"]
        self.set_style()
        self.setAcceptDrops(False)
        self.model = None
        self.vbox = QtWidgets.QVBoxLayout(self)
        self.show()
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
        )
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
        # self.setLayout(self.vbox)

    @abc.abstractmethod
    def place_elements(self):
        pass

    @abc.abstractmethod
    def get_top_widget(self):
        return None

    @abc.abstractmethod
    def get_middle_widget(self):
        return None

    @abc.abstractmethod
    def get_bottom_layout(self):
        return None

    def set_style(self):
        self.setFrameStyle(QtWidgets.QFrame.Panel)
        self.setStyleSheet(
            """
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
                           """
            % ("#FFFFFF", widgetColors["ButtonColor"], widgetColors["Control"])
            # """ % (widgetColors['Control'],widgetColors['ButtonColor'],widgetColors['Control'])
        )

    def set_model(self, model):
        self.model = model

    def text(self):
        return self.model.name

    def setText(self, text):
        self.model.name = text


class AdvancedForEachView(WFControlWithTopMiddleAndBottom):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dontplace = False
        self.is_wano = False

    def get_top_widget(self):
        self.topwidget = QtWidgets.QWidget()
        self.topLineLayout = QtWidgets.QHBoxLayout()
        self.topwidget.setLayout(self.topLineLayout)
        self._for_label = QtWidgets.QLabel("for")
        self.topLineLayout.addWidget(self._for_label)
        self._in_label = QtWidgets.QLabel("in")
        self.itername_widget = QtWidgets.QLineEdit("a,b")
        self.itername_widget.editingFinished.connect(self._on_line_edit)
        self.topLineLayout.addWidget(self.itername_widget)
        self.topLineLayout.addWidget(self._in_label)
        self.list_of_variables = QtWidgets.QLineEdit("zip([1,2,3],[4,5,6]")
        self.list_of_variables.editingFinished.connect(self.line_edited)
        self.topLineLayout.addWidget(self.list_of_variables)
        self._open_variables = QtWidgets.QPushButton(
            QtGui.QIcon.fromTheme("drive-removable-media"), ""
        )
        self._open_variables.clicked.connect(self.open_remote_importer)
        self.topLineLayout.addWidget(self._open_variables)
        return self.topwidget

    def open_remote_importer(self):
        varpaths = self.model.wf_root.assemble_variables("")
        mydialog = RemoteImporterDialog(
            varname='Import variable "%s" from:' % self.model.name, importlist=varpaths
        )
        mydialog.setModal(True)
        mydialog.exec()
        if mydialog.result() is True:
            cursor_now = self.list_of_variables.cursorPosition()
            choice = mydialog.getchoice()
            previous_text = self.list_of_variables.text()
            nowtext = (
                f"{previous_text[0:cursor_now]} {choice} {previous_text[cursor_now:]}"
            )
            self.model.set_filelist(nowtext)
            self.list_of_variables.setText(nowtext)
        else:
            pass

    def init_from_model(self):
        super().init_from_model()
        self.list_of_variables.setText(self.model.fileliststring)
        self.itername_widget.setText(self.model.itername)

    def _on_line_edit(self):
        self.model.itername = self.itername_widget.text().replace(" ", "")

    def line_edited(self):
        files = self.list_of_variables.text()
        self.model.set_filelist(files)

    def get_middle_widget(self):
        return self.model.subwfview

    def get_bottom_layout(self):
        return None

    def sizeHint(self):
        minwidth = 500
        if self.model is not None:
            size = self.model.subwfview.sizeHint() + QtCore.QSize(25, 80)
            if size.width() < minwidth:
                size.setWidth(minwidth)
                self.model.subwfview.set_minimum_width(minwidth)
            return size
        else:
            return QtCore.QSize(500, 500)

    def place_elements(self):
        if not self.dontplace:
            self.dontplace = True
            if self.model is not None:
                self.init_from_model()
                self.model.subwfview.place_elements()
            self.adjustSize()
        self.dontplace = False
        self.updateGeometry()


class ForEachView(WFControlWithTopMiddleAndBottom):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dontplace = False
        self.is_wano = False

    def get_top_widget(self):
        self.topwidget = QtWidgets.QWidget()
        self.topLineLayout = QtWidgets.QHBoxLayout()
        self.topwidget.setLayout(self.topLineLayout)
        # b.clicked.connect(self.toggleVisible)
        self.itername_widget = QtWidgets.QLineEdit("Iterator Name")
        self.itername_widget.editingFinished.connect(self._on_line_edit)
        self.topLineLayout.addWidget(self.itername_widget)
        self.list_of_variables = QtWidgets.QLineEdit("")
        self.topLineLayout.addWidget(self.list_of_variables)
        self.open_variables = QtWidgets.QPushButton(
            QtGui.QIcon.fromTheme("drive-removable-media"), ""
        )
        self.open_variables.clicked.connect(self.open_remote_importer_files)
        # self.open_variables = MultiselectDropDownList(self, text="Import")
        # self.open_variables.connect_workaround(self.load_wf_files)
        # self.open_variables.itemSelectionChanged.connect(self.on_wf_file_change)
        self._global_import_button = QtWidgets.QPushButton(
            QtGui.QIcon.fromTheme("insert-object"), ""
        )
        self._global_import_button.clicked.connect(self.open_remote_importer)
        self.topLineLayout.addWidget(self._global_import_button)
        # self.open_variables.itemSelectionChanged.connect(self.onItemSelectionChange)
        # self.open_variables.connect_workaround(self._load_variables)
        self.topLineLayout.addWidget(self.open_variables)
        return self.topwidget

    def open_remote_importer(self):
        varpaths = self.model.wf_root.assemble_variables("")
        mydialog = RemoteImporterDialog(
            varname='Import variable "%s" from:' % self.model.name, importlist=varpaths
        )
        mydialog.setModal(True)
        mydialog.exec()
        if mydialog.result() is True:
            choice = mydialog.getchoice()
            self.model.set_filelist(choice)
            self.list_of_variables.setText(choice)
            self.model.set_is_file_iterator(False)
        else:
            pass

    def open_remote_importer_files(self):
        varpaths = self.model.wf_root.assemble_files("")
        from simstack.view.RemoteImporterDialog import RemoteImporterDialog

        mydialog = RemoteImporterDialog(
            varname="Import file",
            importlist=varpaths,
            window_title="Workflow File Importer",
        )
        mydialog.setModal(True)
        mydialog.exec_()
        if mydialog.result() is True:
            choice = mydialog.getchoice()
            self.model.set_filelist(choice)
            self.list_of_variables.setText(choice)
            self.model.set_is_file_iterator(True)
        else:
            pass

    def init_from_model(self):
        super().init_from_model()
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

    def get_bottom_layout(self):
        return None

    def sizeHint(self):
        if self.model is not None:
            size = self.model.subwfview.sizeHint() + QtCore.QSize(25, 80)
            if size.width() < 300:
                size.setWidth(300)
            return size
        else:
            return QtCore.QSize(200, 100)

    def place_elements(self):
        if not self.dontplace:
            self.dontplace = True
            if self.model is not None:
                self.init_from_model()
                self.model.subwfview.place_elements()
            self.adjustSize()
        self.dontplace = False
        self.updateGeometry()


class ParallelView(WFControlWithTopMiddleAndBottom):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        a = QtWidgets.QPushButton("Add additional parallel pane")
        a.clicked.connect(self.add_new)
        b = QtWidgets.QPushButton("Remove pane")
        b.clicked.connect(self.delete)
        hor_layout.addWidget(a)
        hor_layout.addWidget(b)
        tw.setLayout(hor_layout)
        return tw

    def init_from_model(self):
        super().init_from_model()
        for view in self.model.subwf_views:
            self.splitter.addWidget(view)

    def get_middle_widget(self):
        return self.splitter

    def get_bottom_layout(self):
        return None

    def sizeHint(self):
        if self.model is not None:
            maxheight = 0
            width = 0
            for v in self.model.subwf_views:
                sh = v.sizeHint()
                maxheight = max(maxheight, sh.height())
                width += sh.width()

            size = QtCore.QSize(width, maxheight)
            size += QtCore.QSize(50, 75)
            if size.width() < 300:
                size.setWidth(300)
            return size
        else:
            return QtCore.QSize(200, 100)

    def place_elements(self):
        if not self.dontplace:
            self.dontplace = True
            if self.model is not None:
                self.init_from_model()

                # self.model.subwfview.place_elements()
                for view in self.model.subwf_views:
                    view.place_elements()

            # self.parent().place_elements()
            self.dontplace = False
        self.updateGeometry()


class IfView(WFControlWithTopMiddleAndBottom):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        # b.clicked.connect(self.toggleVisible)
        self._condition = QtWidgets.QLabel("Condition")
        self.topLineLayout.addWidget(self._condition)
        self.list_of_variables = QtWidgets.QLineEdit("")
        self.list_of_variables.editingFinished.connect(self._on_line_edit)
        self.topLineLayout.addWidget(self.list_of_variables)
        self._global_import_button = QtWidgets.QPushButton(
            QtGui.QIcon.fromTheme("insert-object"), ""
        )
        self._global_import_button.clicked.connect(self.open_remote_importer)
        self.topLineLayout.addWidget(self._global_import_button)
        # self.open_variables.itemSelectionChanged.connect(self.onItemSelectionChange)
        # self.open_variables.connect_workaround(self._load_variables)
        return self.topwidget

    def open_remote_importer(self):
        varpaths = self.model.wf_root.assemble_variables("")
        mydialog = RemoteImporterDialog(
            varname='Import variable "%s" from:' % self.model.name, importlist=varpaths
        )
        mydialog.setModal(True)
        mydialog.exec()
        if mydialog.result() is True:
            choice = mydialog.getchoice()
            self.model.set_condition(choice)
            self.list_of_variables.setText(choice)
        else:
            pass

    def init_from_model(self):
        super().init_from_model()
        for view in self.model.subwf_views:
            self.splitter.addWidget(view)
        self.list_of_variables.setText(self.model._condition)

    def get_middle_widget(self):
        return self.splitter

    def get_bottom_layout(self):
        return None

    def sizeHint(self):
        if self.model is not None:
            maxheight = 0
            width = 0
            for v in self.model.subwf_views:
                sh = v.sizeHint()
                maxheight = max(maxheight, sh.height())
                width += sh.width()

            size = QtCore.QSize(width, maxheight)
            size += QtCore.QSize(50, 75)
            if size.width() < 300:
                size.setWidth(300)
            return size
        else:
            return QtCore.QSize(200, 100)

    def place_elements(self):
        if not self.dontplace:
            self.dontplace = True
            if self.model is not None:
                self.init_from_model()

                # self.model.subwfview.place_elements()
                for view in self.model.subwf_views:
                    view.place_elements()

            # self.parent().place_elements()
            self.dontplace = False
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

        self._varname_widget = QtWidgets.QLineEdit("Variable Name")
        self._varname_widget.editingFinished.connect(self._on_line_edit)
        self._varequation_widget = QtWidgets.QLineEdit("Equation")
        self._varequation_widget.editingFinished.connect(self._on_varequation_line_edit)

        # We define two functors to only have a single open_remote_importer callback function.
        def open_remote_importer_func_varname():
            return self.open_remote_importer(
                target_function_view=self._varname_widget.setText,
                target_function_model=self.model.set_varname,
            )

        self._varname_import_button = QtWidgets.QPushButton(
            QtGui.QIcon.fromTheme("insert-object"), ""
        )
        self._varname_import_button.clicked.connect(open_remote_importer_func_varname)
        self.topLineLayout.addWidget(self._varname_widget)
        self.topLineLayout.addWidget(self._varname_import_button)

        def open_remote_importer_func_varequation():
            return self.open_remote_importer(
                target_function_view=self._varequation_widget.setText,
                target_function_model=self.model.set_varequation,
            )

        self.topLineLayout.addWidget(self._varequation_widget)
        self._global_import_button = QtWidgets.QPushButton(
            QtGui.QIcon.fromTheme("insert-object"), ""
        )
        self._global_import_button.clicked.connect(
            open_remote_importer_func_varequation
        )
        self.topLineLayout.addWidget(self._global_import_button)

        return self.topwidget

    def init_from_model(self):
        super().init_from_model()
        self._varname_widget.setText(self.model.get_varname())
        self._varequation_widget.setText(self.model.get_varequation())

    def open_remote_importer(self, target_function_view, target_function_model):
        varpaths = self.model.wf_root.assemble_variables("")
        mydialog = RemoteImporterDialog(
            varname='Import variable "%s" from:' % self.model.name, importlist=varpaths
        )
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

    def get_bottom_layout(self):
        return None

    def sizeHint(self):
        if self.model is not None:
            maxheight = 0
            width = 0

            size = QtCore.QSize(width, maxheight)
            size += QtCore.QSize(50, 75)
            if size.width() < 300:
                size.setWidth(300)
            return size
        else:
            return QtCore.QSize(200, 100)

    def place_elements(self):
        if not self.dontplace:
            self.dontplace = True
            if self.model is not None:
                self.init_from_model()
            self.dontplace = False
        self.updateGeometry()


class WhileView(WFControlWithTopMiddleAndBottom):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        # b.clicked.connect(self.toggleVisible)
        self.itername_widget = QtWidgets.QLineEdit("Iterator Name")
        self.itername_widget.editingFinished.connect(self._on_line_edit)
        self.topLineLayout.addWidget(self.itername_widget)
        self.list_of_variables = QtWidgets.QLineEdit("Condition")
        self.list_of_variables.editingFinished.connect(self._on_varname_line_edit)
        self.topLineLayout.addWidget(self.list_of_variables)
        self._global_import_button = QtWidgets.QPushButton(
            QtGui.QIcon.fromTheme("insert-object"), ""
        )
        self._global_import_button.clicked.connect(self.open_remote_importer)
        self.topLineLayout.addWidget(self._global_import_button)
        # self.open_variables.itemSelectionChanged.connect(self.onItemSelectionChange)
        # self.open_variables.connect_workaround(self._load_variables)
        return self.topwidget

    def open_remote_importer(self):
        varpaths = self.model.wf_root.assemble_variables("")
        mydialog = RemoteImporterDialog(
            varname='Import variable "%s" from:' % self.model.name, importlist=varpaths
        )
        mydialog.setModal(True)
        mydialog.exec()
        if mydialog.result() is True:
            choice = mydialog.getchoice()
            self.model.set_condition(choice)
            self.list_of_variables.setText(choice)
        else:
            pass

    def init_from_model(self):
        super().init_from_model()
        for view in self.model.subwf_views:
            self.splitter.addWidget(view)
        self.list_of_variables.setText(self.model.get_condition())
        self.itername_widget.setText(self.model.get_itername())

    def get_middle_widget(self):
        return self.splitter

    def get_bottom_layout(self):
        return None

    def sizeHint(self):
        if self.model is not None:
            maxheight = 0
            width = 0
            for v in self.model.subwf_views:
                sh = v.sizeHint()
                maxheight = max(maxheight, sh.height())
                width += sh.width()

            size = QtCore.QSize(width, maxheight)
            size += QtCore.QSize(50, 75)
            if size.width() < 300:
                size.setWidth(300)
            return size
        else:
            return QtCore.QSize(200, 100)

    def place_elements(self):
        if not self.dontplace:
            self.dontplace = True
            if self.model is not None:
                self.init_from_model()

                # self.model.subwfview.place_elements()
                for view in self.model.subwf_views:
                    view.place_elements()

            # self.parent().place_elements()
            self.dontplace = False
        self.updateGeometry()
