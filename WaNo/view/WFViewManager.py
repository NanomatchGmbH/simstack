from .WFEditorMainWindow import WFEditorMainWindow
from .WFEditor import WFEditor

from PySide.QtCore import Signal, QObject
from PySide.QtGui import QMessageBox, QFileDialog

from .MessageDialog import MessageDialog

class WFViewManager(QObject):
    REGISTRY_CONNECTION_STATES = WFEditor.REGISTRY_CONNECTION_STATES
    save_registries         = Signal(list, name="SaveRegistries")
    open_registry_settings  = Signal(name="OpenRegistrySettings")
    registry_changed        = Signal(int, name="RegistryChanged")
    disconnect_registry     = Signal(name='disconnectRegistry')
    connect_registry        = Signal(int, name='connectRegistry')
    run_clicked             = Signal(name='runClicked')
    request_job_list_update     = Signal(name="requestJobListUpdate")
    request_worflow_list_update = Signal(name="requestWorkflowListUpdate")
    request_job_update          = Signal(str, name="requestJobUpdate")
    request_worflow_update      = Signal(str, name="requestWorkflowUpdate")
    request_directory_update    = Signal(str, name="requestDirectoryUpdate")
    request_saved_workflows_update = Signal(str, name="requestSavedWorkflowsUpdate")
    download_file_to            = Signal(str, str, name="downloadFileTo")
    upload_file                 = Signal(str, str, name="uploadFile")
    delete_file                 = Signal(str, name="deleetFile")
    delete_job                  = Signal(str, name="deleetJob")


    def _show_message(self, msg_type, msg):
        MessageDialog(msg_type, msg)

    def show_error(self, msg):
        self._show_message(MessageDialog.MESSAGE_TYPES.error, msg)

    def show_info(self, msg):
        self._show_message(MessageDialog.MESSAGE_TYPES.info, msg)

    def show_warning(self, msg):
        self._show_message(MessageDialog.MESSAGE_TYPES.warning, msg)

    def show_critical_error(self, msg):
        self._show_message(MessageDialog.MESSAGE_TYPES.critical, msg)

    def show_mainwindow(self):
        self._mainwindow.show()

    def clear_editor(self):
        self._editor.clear()

    def open_dialog_open_workflow(self):
        self._editor.open()
        #TODO result must be passed to controller (via signals)

    def open_dialog_save_workflow(self):
        self._editor.save()
        #TODO result must be passed to controller (via signals)

    def open_dialog_save_workflow_as(self):
        self._editor.saveAs()
        #TODO result must be passed to controller (via signals)

    def open_dialog_registry_settings(self, current_registries):
        self._mainwindow.open_dialog_registry_settings(current_registries)

    def update_wano_list(self, wanos):
        self._editor.update_wano_list(wanos)

    def update_saved_workflows_list(self, workflows):
        self._editor.update_saved_workflows_list(workflows)

    def set_registry_connection_status(self, status):
        self._editor.set_registry_connection_status(status)

    def open_new_workflow(self):
        #TODO
        pass

    def update_registries(self, registries, selected):
        self._editor.update_registries(registries, selected)

    def update_filesystem_model(self, path, files):
        self._editor.update_filesystem_model(path, files)

    def update_job_list(self, jobs):
        self._editor.update_job_list(jobs)

    def update_workflow_list(self, wfs):
        self._editor.update_workflow_list(wfs)

    def exit(self):
        if QMessageBox.question(None, '', "Are you sure you want to quit?",
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No) == QMessageBox.Yes:
            self._mainwindow.exit()

    def test(self):
        print("WFViewManager")
        self.open_registry_settings.emit()

    def _on_file_download(self, filepath):
        save_to = QFileDialog.getSaveFileName(
                self._editor,
                'Download File',
                '',
                selectedFilter=''
                )
        if save_to:
            print(save_to)
            print("Save file to: %s." % save_to[0])
            self.download_file_to.emit(filepath, save_to[0])

    def _on_file_upload(self, dirpath):
        upload = QFileDialog.getOpenFileName(
                self._editor,
                'Select file for upload',
                '',
                selectedFilter=''
                )
        if upload:
            print(upload)
            self.upload_file.emit(upload[0], dirpath)

    def _on_workflow_saved(self, success, folder):
        if not success:
            self.show_error("Could not save Workflow to folder\n%s" % folder)
        else:
            self.request_saved_workflows_update.emit(folder)
 
    def _connect_signals(self):
        self._mainwindow.open_file.connect(self.open_dialog_open_workflow)
        self._mainwindow.save.connect(self.open_dialog_save_workflow)
        self._mainwindow.save_as.connect(self.open_dialog_save_workflow_as)
        self._mainwindow.run.connect(self.run_clicked)
        self._mainwindow.new_file.connect(self.open_new_workflow)
        self._mainwindow.exit_client.connect(self.exit)

        # Forwarded signals
        self._mainwindow.save_registries.connect(self.save_registries)
        self._mainwindow.open_registry_settings.connect(self.open_registry_settings)
        self._editor.registry_changed.connect(self.registry_changed)
        self._editor.connect_registry.connect(self.connect_registry)
        self._editor.disconnect_registry.connect(self.disconnect_registry)

        self._editor.request_job_list_update.connect(self.request_job_list_update)
        self._editor.request_worflow_list_update.connect(self.request_worflow_list_update)
        self._editor.request_job_update.connect(self.request_job_update)
        self._editor.request_worflow_update.connect(self.request_worflow_update)
        self._editor.request_directory_update.connect(self.request_directory_update)
        self._editor.download_file.connect(self._on_file_download)
        self._editor.upload_file_to.connect(self._on_file_upload)
        self._editor.delete_job.connect(self.delete_job)
        self._editor.delete_file.connect(self.delete_file)
        self._editor.workflow_saved.connect(self._on_workflow_saved)

    def get_editor(self):
        return self._editor

    def __init__(self):
        super(WFViewManager, self).__init__()
        self._editor        = WFEditor()

        self._mainwindow    = WFEditorMainWindow(self._editor)

        self._connect_signals()
