from PySide6.QtWidgets import (
    QWidget,
    QTreeView,
    QVBoxLayout,
    QPushButton,
    QAbstractItemView,
    QMenu,
    QApplication,
)
from PySide6.QtGui import QCursor
from PySide6.QtCore import Signal, Qt

from .WFEditorTreeModels import WFERemoteFileSystemModel as FSModel
from .WFEditorTreeModels import WFERemoteFileSystemEntry


import os


class WFRemoteFileSystem(QWidget):
    request_job_list_update = Signal(name="requestJobListUpdate")
    request_worflow_list_update = Signal(name="requestWorkflowListUpdate")
    request_job_update = Signal(str, name="requestJobUpdate")
    request_worflow_update = Signal(str, name="requestWorkflowUpdate")
    request_directory_update = Signal(str, name="requestDirectoryUpdate")
    download_file = Signal(str, name="downloadFile")
    upload_file_to = Signal(str, name="uploadFile")
    delete_file = Signal(str, name="deleteFile")
    delete_job = Signal(str, name="deleteJob")
    abort_job = Signal(str, name="abortJob")
    browse = Signal(str, str, name="browse")
    delete_workflow = Signal(str, name="deleteWorkflow")
    abort_workflow = Signal(str, name="abortWorkflow")
    _WF_PATH = "?wf?"
    _JOB_PATH = "?job?"

    def __init_ui(self):
        layout = QVBoxLayout(self)

        self.__fileTree.setModel(self.__fs_model)
        self.__fileTree.setHeaderHidden(True)
        self.__fileTree.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.__fileTree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.__btn_reload.setText("Reload")

        layout.addWidget(self.__fileTree)
        layout.addWidget(self.__btn_reload)

    def update_job_list(self, jobs):
        self.update_file_tree_node(self._JOB_PATH, jobs)

    def update_workflow_list(self, wfs):
        self.update_file_tree_node(self._WF_PATH, wfs)

    def update_file_tree_node(self, path, subelements):
        # print("new file tree nodes for path: %s:\n%s" % (path, subelements))
        filePath = path if not path == "" else "none"

        if filePath in self.__current_requests:
            index = self.__current_requests[filePath]
            self.__fs_model.removeSubRows(index)
            # remove request
            self.__current_requests.pop(filePath)

            if subelements is not None and len(subelements) > 0:
                if filePath == "?wf?":
                    subelements.sort(key=lambda k: k["name"], reverse=True)
                else:
                    subelements.sort(key=lambda k: k["name"])
                # print("i(id=%s): %s" % (i['id'] if 'id' in i else '', i))
                # print(path,i['path'],i['name'])

                entries = [
                    WFERemoteFileSystemEntry.createData(
                        i["id"] if "id" in i else i["name"],
                        i["name"],
                        os.path.basename(
                            i["name"][:-1] if i["name"].endswith("/") else i["name"]
                        ),
                        "%s/%s"
                        % (
                            path if i["type"] == "f" or i["type"] == "d" else "",
                            i["path"]
                            if i["type"] != "f" and i["type"] != "d"
                            else i["name"],
                        ),
                        FSModel.DATA_TYPE_FILE
                        if i["type"] == "f"
                        else FSModel.DATA_TYPE_DIRECTORY
                        if i["type"] == "d"
                        else FSModel.DATA_TYPE_JOB
                        if i["type"] == "j"
                        else FSModel.DATA_TYPE_WORKFLOW
                        if i["type"] == "w"
                        else FSModel.DATA_TYPE_UNKNOWN,
                        status=i["status"] if "status" in i else None,
                        original_result_directory=i["original_result_directory"]
                        if "original_result_directory" in i
                        else None,
                    )
                    for i in subelements
                ]

                self.__fs_model.insertDataRows(0, entries, index)
            # print(subelements)
        else:
            print("Path '%s' not in current_requests." % filePath)

    # TODO rename
    def __got_request(self, model_index):
        update_list = []

        if model_index is None:
            indices = self.__fs_model.get_separator_indices()
            update_list = [
                (
                    i,
                    self._JOB_PATH if t == FSModel.HEADER_TYPE_JOB else self._WF_PATH,
                    t,
                )
                for (i, t) in [(i, self.__fs_model.get_type(i)) for i in indices]
                if t == FSModel.HEADER_TYPE_JOB or t == FSModel.HEADER_TYPE_WORKFLOW
            ]
        elif model_index is not None and model_index.isValid():
            index_type = self.__fs_model.get_type(model_index)

            update_list = [
                (
                    model_index,
                    self._JOB_PATH
                    if index_type == FSModel.HEADER_TYPE_JOB
                    else self._WF_PATH
                    if index_type == FSModel.HEADER_TYPE_WORKFLOW
                    else self.__fs_model.filePath(model_index),
                    index_type,
                )
            ]

        for index, filePath, index_type in update_list:
            self.__fs_model.loading(index, "Loading...")

            if (
                index_type == FSModel.HEADER_TYPE_JOB
                or index_type == FSModel.HEADER_TYPE_WORKFLOW
            ):
                self.__request_header_entry_update(index, filePath, index_type)
            else:
                self.__request_tree_entry_update(index, filePath, index_type)

        else:
            pass
            # print("index invalid: %s, status: %s" % (model_index,
            #    model_index.isValid() if not model_index is None else None))

    def __request_header_entry_update(self, index, path, index_type):
        self.__current_requests.update({path: index})
        # print("current_requests: %s" % self.__current_requests)

        # print("Emitting request for %s." % path)
        if index_type == FSModel.HEADER_TYPE_JOB:
            self.request_job_list_update.emit()
        elif index_type == FSModel.HEADER_TYPE_WORKFLOW:
            self.request_worflow_list_update.emit()
        elif index_type == FSModel.HEADER_TYPE_DIRECTORY:
            # self.request_directory_update(path).emit()
            self.__request_tree_entry_update(index, path, index_type)
        else:
            print("wrong type : %s" % index_type)

    def __request_tree_entry_update(self, index, path, index_type):
        abspath = self.__fs_model.get_abspath(
            index
        )  # "%s/%s" % (self.__fs_model.get_abspath(index), path) \
        # if index_type == FSModel.DATA_TYPE_DIRECTORY or \
        #     index_type == FSModel.DATA_TYPE_FILE \
        # else path

        if index_type == FSModel.DATA_TYPE_WORKFLOW:
            abspath = self.__fs_model.get_id(index)

        self.__current_requests.update({abspath: index})
        # print("current_requests: %s" % self.__current_requests)

        # print("Emitting request for %s." % abspath)
        if index_type == FSModel.DATA_TYPE_JOB:
            self.request_job_update.emit(abspath)
        elif index_type == FSModel.DATA_TYPE_WORKFLOW:
            wf_id = self.__fs_model.get_id(index)
            self.request_worflow_update.emit(wf_id)
        elif index_type == FSModel.DATA_TYPE_DIRECTORY:
            self.request_directory_update.emit(abspath)
        elif index_type == FSModel.HEADER_TYPE_DIRECTORY:
            self.request_directory_update.emit(abspath)
        elif index_type == FSModel.DATA_TYPE_FILE:
            # We don't need to remember this one.
            # TODO optimize
            self.__current_requests.pop(abspath)
            self.__download_file(index)
        else:
            print("wrong type : %s" % index_type)

    def __download_file(self, index):
        abspath = self.__fs_model.get_abspath(index)
        self.download_file.emit(abspath)

    def __upload_file(self, index):
        abspath = self.__fs_model.get_abspath(index)
        self.upload_file_to.emit(abspath)

    def __on_cm_download(self):
        # TODO modify to handle all selected.
        index = self.__fileTree.selectedIndexes()[0]
        if (
            index is not None
            and self.__fs_model.get_type(index) == FSModel.DATA_TYPE_FILE
        ):
            self.__download_file(index)

    def __on_cm_upload(self):
        index = self.__fileTree.selectedIndexes()[0]
        if index is not None:
            index_type = self.__fs_model.get_type(index)
            if (
                index_type == FSModel.DATA_TYPE_DIRECTORY
                or index_type == FSModel.DATA_TYPE_JOB
            ):
                self.__upload_file(index)

    def __on_cm_delete_file(self):
        # TODO modify to handle all selected.
        index = self.__fileTree.selectedIndexes()[0]
        if index is not None and (
            self.__fs_model.get_type(index) == FSModel.DATA_TYPE_FILE
            or self.__fs_model.get_type(index) == FSModel.DATA_TYPE_DIRECTORY
        ):
            file = self.__fs_model.get_abspath(index)
            self.delete_file.emit(file)

    def __on_cm_delete_job(self):
        # TODO modify to handle all selected.
        index = self.__fileTree.selectedIndexes()[0]
        if (
            index is not None
            and self.__fs_model.get_type(index) == FSModel.DATA_TYPE_JOB
        ):
            # print("got id: %s" % self.__fs_model.get_id(index))
            job = self.__fs_model.get_id(index)
            self.delete_job.emit(job)

    def __on_jobid_copy(self):
        # TODO modify to handle all selected.
        index = self.__fileTree.selectedIndexes()[0]
        if (
            index is not None
            and self.__fs_model.get_type(index) == FSModel.DATA_TYPE_JOB
        ):
            job = self.__fs_model.get_id(index)
            cb = QApplication.clipboard()
            cb.clear(mode=cb.Clipboard)
            cb.clear(mode=cb.Selection)
            cb.setText("%s" % job, mode=cb.Clipboard)
            cb.setText("%s" % job, mode=cb.Selection)

    def __on_cm_abort_job(self):
        # TODO modify to handle all selected.
        index = self.__fileTree.selectedIndexes()[0]
        if (
            index is not None
            and self.__fs_model.get_type(index) == FSModel.DATA_TYPE_JOB
        ):
            job = self.__fs_model.get_id(index)
            self.abort_job.emit(job)

    def __on_cm_browse(self):
        index = self.__fileTree.selectedIndexes()[0]
        if (
            index is not None
            and self.__fs_model.get_type(index) == FSModel.DATA_TYPE_WORKFLOW
            or self.__fs_model.get_type(index) == FSModel.DATA_TYPE_DIRECTORY
        ):
            # Workflow and directory treatment is equivalent
            workflow = self.__fs_model.get_id(index)
            self.browse.emit(workflow, "")
        elif (
            index is not None
            and self.__fs_model.get_type(index) == FSModel.DATA_TYPE_JOB
        ):
            wfindex = self.__fs_model.get_parent_workflow(index)
            workflow = self.__fs_model.getNodeByIndex(wfindex)
            jobnode = self.__fs_model.getNodeByIndex(index)
            self.browse.emit(jobnode.getAbsolutePath(), "")

    def __on_cm_show_report(self):
        index = self.__fileTree.selectedIndexes()[0]
        if (
            index is not None
            and self.__fs_model.get_type(index) == FSModel.DATA_TYPE_WORKFLOW
            or self.__fs_model.get_type(index) == FSModel.DATA_TYPE_DIRECTORY
        ):
            # Workflow and directory treatment is equivalent
            # print("got id: %s" % self.__fs_model.get_id(index))
            workflow = self.__fs_model.get_id(index)
            self.browse.emit(workflow + "/workflow_report.html", "")

    def __on_cm_delete_workflow(self):
        index = self.__fileTree.selectedIndexes()[0]
        if (
            index is not None
            and self.__fs_model.get_type(index) == FSModel.DATA_TYPE_WORKFLOW
        ):
            # print("got id: %s" % self.__fs_model.get_id(index))
            workflow = self.__fs_model.get_id(index)
            self.delete_workflow.emit(workflow)

    def __on_cm_abort_workflow(self):
        index = self.__fileTree.selectedIndexes()[0]
        if (
            index is not None
            and self.__fs_model.get_type(index) == FSModel.DATA_TYPE_WORKFLOW
        ):
            workflow = self.__fs_model.get_id(index)
            self.abort_workflow.emit(workflow)

    def __create_file_context_menu(self, menu, index):
        action_1 = menu.addAction("Download File")
        action_1.triggered.connect(self.__on_cm_download)

        action_2 = menu.addAction("Delete File")
        action_2.triggered.connect(self.__on_cm_delete_file)

    def __create_directory_context_menu(self, menu, index):
        action_1 = menu.addAction("Browse Directory")
        action_1.triggered.connect(self.__on_cm_browse)

        action_2 = menu.addAction("Upload File")
        action_2.triggered.connect(self.__on_cm_upload)

        action_3 = menu.addAction("Delete Directory")
        action_3.triggered.connect(self.__on_cm_delete_file)

    def __create_workflow_context_menu(self, menu, index, success):
        action_1 = menu.addAction("Browse Workflow")
        action_1.triggered.connect(self.__on_cm_browse)
        if success:
            action_1 = menu.addAction("Show Report")
            action_1.triggered.connect(self.__on_cm_show_report)
        action_1 = menu.addAction("Delete Workflow")
        action_1.triggered.connect(self.__on_cm_delete_workflow)
        action_1 = menu.addAction("Abort Workflow")
        action_1.triggered.connect(self.__on_cm_abort_workflow)

    def __create_job_context_menu(self, menu, index):
        action_1 = menu.addAction("Delete Job")
        action_1.triggered.connect(self.__on_cm_delete_job)
        action_2 = menu.addAction("Abort Job")
        action_2.triggered.connect(self.__on_cm_abort_job)
        action_2 = menu.addAction("Copy JobID to clipboard")
        action_2.triggered.connect(self.__on_jobid_copy)

    def __context_menu(self, pos):
        index = self.__fileTree.indexAt(pos)

        if not index.isValid():
            return

        index.internalPointer()

        menu = QMenu()
        # action=menu.addAction("Menu")
        # action=menu.addAction(name)

        # menu.addSeparator()

        # index = self.__fileTree.selectedIndexes()[0]
        index_type = self.__fs_model.get_type(index)
        if index_type == FSModel.DATA_TYPE_FILE:
            self.__create_file_context_menu(menu, index)
        elif index_type == FSModel.DATA_TYPE_DIRECTORY:
            self.__create_directory_context_menu(menu, index)
        elif index_type == FSModel.DATA_TYPE_JOB:
            self.__create_directory_context_menu(menu, index)
        elif index_type == FSModel.DATA_TYPE_WORKFLOW:
            jobnode = self.__fs_model.getNodeByIndex(index)
            successful = (
                jobnode.getIconType() == FSModel.DATA_TYPE_WORKFLOW.WF_SUCCESSFUL
            )
            self.__create_workflow_context_menu(menu, index, successful)
        else:
            # TODO, also include number of selected indices.
            pass
        menu.exec_(QCursor.pos())

    def __reload(self):
        self.__got_request(None)

    def __connect_signals(self):
        self.__fileTree.customContextMenuRequested.connect(self.__context_menu)
        self.__fileTree.doubleClicked.connect(self.__got_request)
        self.__fileTree.expanded.connect(self.__got_request)
        self.__btn_reload.clicked.connect(self.__reload)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__fs_model = FSModel(self)
        self.__fileTree = QTreeView(self)
        self.__btn_reload = QPushButton()
        self.__init_ui()
        self.__connect_signals()
        self.__current_requests = {}
