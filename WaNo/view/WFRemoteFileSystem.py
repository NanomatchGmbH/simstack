from PySide.QtGui import QWidget, QTreeView, QVBoxLayout, QPushButton, \
        QAbstractItemView, QMenu, QCursor
from PySide.QtCore import Signal, QModelIndex, Qt
#from ..lib.FileSystemTree import FileSystemModel, FileSystemElement
from enum import Enum

from .WFEditorTreeModels import WFEUnicoreRemoteFileSystemModel as FSModel
from .WFEditorTreeModels import WFEUnicoreFileSystemEntry


import os

class WFRemoteFileSystem(QWidget):
    request_job_list_update     = Signal(name="requestJobListUpdate")
    request_worflow_list_update = Signal(name="requestWorkflowListUpdate")
    request_job_update          = Signal(str, name="requestJobUpdate")
    request_worflow_update      = Signal(str, name="requestWorkflowUpdate")
    request_directory_update    = Signal(str, name="requestDirectoryUpdate")
    download_file               = Signal(str, name="downloadFile")
    upload_file_to              = Signal(str, name="uploadFile")
    delete_file                 = Signal(str, name="deleetFile")
    delete_job                  = Signal(str, name="deleetJob")
    _WF_PATH                    = '?wf?'
    _JOB_PATH                   = '?job?'


    def __init_ui(self):
        layout      = QVBoxLayout(self)

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
        print("new file tree nodes for path: %s:\n%s" % (path, subelements))
        filePath = path if not path == '' else 'none'

        if filePath in self.__current_requests:
            index   = self.__current_requests[filePath]
            self.__fs_model.removeSubRows(index)
            # remove request
            self.__current_requests.pop(filePath)

            if not subelements is None and len(subelements) > 0:
                subelements.sort(key=lambda k: k['name'])
                i=subelements[0]
                print("i(id=%s): %s" % (i['id'] if 'id' in i else '', i))
                entries = [WFEUnicoreFileSystemEntry.createData(
                        i['id'] if 'id' in i else i['name'],
                        i['name'],
                        os.path.basename(
                            i['name'][:-1] if i['name'].endswith('/') else i['name']
                        ),
                        "%s/%s" % (
                            path if i['type'] == 'f' or i['type'] == 'd' else '',
                            i['path']),
                        FSModel.DATA_TYPE_FILE if i['type'] == 'f' \
                                else FSModel.DATA_TYPE_DIRECTORY if i['type'] == 'd' \
                                else FSModel.DATA_TYPE_JOB if i['type'] == 'j' \
                                else FSModel.DATA_TYPE_WORKFLOW if i['type'] == 'w' \
                                else FSModel.DATA_TYPE_UNKNOWN
                        ) for i in subelements]

                self.__fs_model.insertDataRows(0, entries, index)
            print(subelements)
        else:
            print("Path '%s' not in current_requests." % filePath)

    #TODO rename
    def __got_request(self, model_index):
        update_list = []

        if model_index is None:
            indices = self.__fs_model.get_separator_indices()
            update_list = [
                    (i,
                        self._JOB_PATH if t == FSModel.HEADER_TYPE_JOB \
                                else self._WF_PATH,
                        t
                    ) for (i, t) in [(i, self.__fs_model.get_type(i)) for i in indices] \
                            if t == FSModel.HEADER_TYPE_JOB or t == FSModel.HEADER_TYPE_WORKFLOW]
        elif not model_index is None and model_index.isValid():
            index_type = self.__fs_model.get_type(model_index)

            if index_type == FSModel.HEADER_TYPE_JOB:
                abspath = self.__fs_model.get_abspath(model_index)
                #print("JP,abs", self._JOB_PATH, abspath)
                #exit(0)
            update_list = [(model_index,
                self._JOB_PATH if index_type == FSModel.HEADER_TYPE_JOB \
                        else self._WF_PATH if index_type == FSModel.HEADER_TYPE_WORKFLOW \
                        else self.__fs_model.filePath(model_index), index_type)]

        for (index, filePath, index_type) in update_list:
            self.__fs_model.loading(index, "Loading...")

            if index_type == FSModel.HEADER_TYPE_JOB or \
                    index_type == FSModel.HEADER_TYPE_WORKFLOW:
                self.__request_header_entry_update(index, filePath, index_type)
            else:
                self.__request_tree_entry_update(index, filePath, index_type)

        else:
            print("index invalid: %s, status: %s" % (model_index,
                model_index.isValid() if not model_index is None else None))
            #TODO remove

    def __request_header_entry_update(self, index, path, index_type):
        self.__current_requests.update( {path: index} )
        print("current_requests: %s" % self.__current_requests)

        print("Emitting request for %s." % path)
        if index_type == FSModel.HEADER_TYPE_JOB:
            self.request_job_list_update.emit()
        elif index_type == FSModel.HEADER_TYPE_WORKFLOW:
            self.request_worflow_list_update.emit()
        else:
            print("wrong type : %s" % index_type)

    def __request_tree_entry_update(self, index, path, index_type):
        abspath = self.__fs_model.get_abspath(index) #"%s/%s" % (self.__fs_model.get_abspath(index), path) \
                       # if index_type == FSModel.DATA_TYPE_DIRECTORY or \
                       #     index_type == FSModel.DATA_TYPE_FILE \
                       # else path




        if index_type == FSModel.DATA_TYPE_WORKFLOW:
            abspath = self.__fs_model.get_id(index)

        self.__current_requests.update({abspath: index})
        print("current_requests: %s" % self.__current_requests)

        print("Emitting request for %s." % abspath)
        if index_type == FSModel.DATA_TYPE_JOB:
            self.request_job_update.emit(abspath)
        elif index_type == FSModel.DATA_TYPE_WORKFLOW:
            wf_id = self.__fs_model.get_id(index)
            self.request_worflow_update.emit(wf_id)
        elif index_type == FSModel.DATA_TYPE_DIRECTORY:
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
        #TODO modify to handle all selected.
        index = self.__fileTree.selectedIndexes()[0]
        if not index is None \
                and self.__fs_model.get_type(index) == FSModel.DATA_TYPE_FILE:
            self.__download_file(index)

    def __on_cm_upload(self):
        index = self.__fileTree.selectedIndexes()[0]
        if not index is None:
            index_type = self.__fs_model.get_type(index)
            if index_type == FSModel.DATA_TYPE_DIRECTORY \
                    or index_type == FSModel.DATA_TYPE_JOB:
                self.__upload_file(index)

    def __on_cm_delete_file(self):
        #TODO modify to handle all selected.
        index = self.__fileTree.selectedIndexes()[0]
        if not index is None \
                and (self.__fs_model.get_type(index) == FSModel.DATA_TYPE_FILE \
                or self.__fs_model.get_type(index) == FSModel.DATA_TYPE_DIRECTORY):
            file = self.__fs_model.get_abspath(index)
            self.delete_file.emit(file)

    def __on_cm_delete_job(self):
        #TODO modify to handle all selected.
        index = self.__fileTree.selectedIndexes()[0]
        if not index is None \
                and self.__fs_model.get_type(index) == FSModel.DATA_TYPE_JOB:
            print("got id: %s" % self.__fs_model.get_id(index))
            job = self.__fs_model.get_id(index)
            self.delete_job.emit(job)

    def __create_file_context_menu(self, menu, index):
        action_1=menu.addAction("Download File")
        action_1.triggered.connect(self.__on_cm_download)

        action_2=menu.addAction("Delete File")
        action_2.triggered.connect(self.__on_cm_delete_file)

    def __create_directory_context_menu(self, menu, index):
        action_1=menu.addAction("Upload File")
        action_1.triggered.connect(self.__on_cm_upload)

        action_2=menu.addAction("Delete Directory")
        action_2.triggered.connect(self.__on_cm_delete_file)

    def __create_job_context_menu(self, menu, index):
        action_1=menu.addAction("Delete Job")
        action_1.triggered.connect(self.__on_cm_delete_job)

    def __context_menu(self, pos):
        index = self.__fileTree.indexAt(pos)

        if not index.isValid():
           return

        item = index.internalPointer()
        name = item.getText()  # The text of the node.

        menu=QMenu()
       # action=menu.addAction("Menu")
       # action=menu.addAction(name)

       # menu.addSeparator()

        #index = self.__fileTree.selectedIndexes()[0]
        index_type = self.__fs_model.get_type(index)
        if index_type == FSModel.DATA_TYPE_FILE:
            self.__create_file_context_menu(menu, index)
        elif index_type == FSModel.DATA_TYPE_DIRECTORY:
            self.__create_directory_context_menu(menu, index)
        elif index_type == FSModel.DATA_TYPE_JOB:
            self.__create_job_context_menu(menu, index)
            menu.addSeparator()
            self.__create_directory_context_menu(menu, index)
        else:
            #TODO, also include number of selected indices.
            pass

        print(QCursor.pos())
        menu.exec_(QCursor.pos())



    def __reload(self):
        self.__got_request(None)

    def __connect_signals(self):
        self.__fileTree.customContextMenuRequested.connect(self.__context_menu)
        self.__fileTree.doubleClicked.connect(self.__got_request)
        self.__fileTree.expanded.connect(self.__got_request)
        self.__btn_reload.clicked.connect(self.__reload)
    
    def __init__(self, parent=None):
        super(WFRemoteFileSystem, self).__init__(parent)
        self.__fs_model     = FSModel(self)
        self.__fileTree     = QTreeView(self)
        self.__btn_reload   = QPushButton()
        self.__init_ui()
        self.__connect_signals()
        self.__current_requests = {}
