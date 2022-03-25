from os import path

from .WFEditorMainWindow import WFEditorMainWindow
from .WFEditor import WFEditor

import Qt
from Qt.QtCore import Signal, QObject, QMutex, QFileInfo
from Qt.QtWidgets import QMessageBox, QFileDialog

from .MessageDialog import MessageDialog
from .DownloadProgressWidget import DownloadProgressWidget
from .DownloadProgressMenuButton import DownloadProgressMenuButton
from ..lib.DynamicTimer import DynamicTimer

# TODO Debug only
import ctypes

class WFViewManager(QObject):
    REGISTRY_CONNECTION_STATES = WFEditor.REGISTRY_CONNECTION_STATES
    save_registries         = Signal(list, name="SaveRegistries")
    save_paths = Signal(dict,name="SavePaths")
    open_registry_settings  = Signal(name="OpenRegistrySettings")
    open_path_settings = Signal(name="OpenPathSettings")
    registry_changed        = Signal(str, name="RegistryChanged")
    disconnect_registry     = Signal(name='disconnectRegistry')
    connect_registry        = Signal(str, name='connectRegistry')
    run_clicked             = Signal(name='runClicked')
    exit_client             = Signal(name='exitClient')
    request_job_list_update     = Signal(name="requestJobListUpdate")
    request_worflow_list_update = Signal(name="requestWorkflowListUpdate")
    request_job_update          = Signal(str, name="requestJobUpdate")
    request_worflow_update      = Signal(str, name="requestWorkflowUpdate")
    request_directory_update    = Signal(str, name="requestDirectoryUpdate")
    request_saved_workflows_update = Signal(str, name="requestSavedWorkflowsUpdate")
    download_file_to            = Signal(str, str, name="downloadFileTo")
    upload_file                 = Signal(str, str, name="uploadFile")
    delete_file                 = Signal(str, name="deleteFile")
    delete_job                  = Signal(str, name="deleteJob")
    abort_job                   = Signal(str, name="abortJob")
    browse_workflow             = Signal(str, name="browseWorkflow")
    delete_workflow             = Signal(str, name="deleteWorkflow")
    abort_workflow              = Signal(str, name="abortWorkflow")
    # for internal use only
    _update_timeout             = Signal(name="updateTimeout")

    @classmethod
    def show_message(cls, msg_type, msg, details=None):
        MessageDialog(msg_type, msg, details=details)

    @classmethod
    def _show_message(cls, msg_type, msg, details=None):
        return cls.show_message(msg_type, msg, details=details)

    @classmethod
    def show_error(cls, msg, details=None):
        cls._show_message(MessageDialog.MESSAGE_TYPES.error, msg, details)

    def show_info(self, msg, details=None):
        self._show_message(MessageDialog.MESSAGE_TYPES.info, msg, details)

    def show_warning(self, msg, details=None):
        self._show_message(MessageDialog.MESSAGE_TYPES.warning, msg, details)

    def show_critical_error(self, msg, details=None):
        self._show_message(MessageDialog.MESSAGE_TYPES.critical, msg, details)

    def show_mainwindow(self):
        self._mainwindow.show()

    def show_status_message(self, message, duration=5):
        self._mainwindow.show_status_message(message, duration)

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

    def open_dialog_path_settings(self,pathsettings):
        self._mainwindow.open_dialog_path_settings(pathsettings)

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

    def test(self):
        print("WFViewManager")
        self.open_registry_settings.emit()

    def _on_file_download(self, filepath):
        mybase = path.basename(filepath)
        #print(filepath)
        save_to = QFileDialog.getSaveFileName(
                self._editor,
                'Download File',
                path.join(self.last_used_path,mybase)
                )
        if save_to[0]:
            self.last_used_path = QFileInfo(filepath).path()
            #print("Save file to: %s." % save_to[0])
            self.download_file_to.emit(filepath, save_to[0])
            #self._view_timer.add_callback(self._update_timeout.emit,
            #        self._dl_update_interval)

    def _on_file_upload(self, dirpath):
        upload = QFileDialog.getOpenFileName(
                self._editor,
                'Select file for upload',
                ''
                )
        if upload[0]:
            print("Going to upload: %s" % str(upload))
            self.upload_file.emit(upload[0], dirpath)
            #self._view_timer.add_callback(self._update_timeout.emit,
            #        self._dl_update_interval)

    def _on_workflow_saved(self, success, folder):
        if not success:
            self.show_error("Could not save Workflow to folder\n%s" % folder)
        else:
            self.request_saved_workflows_update.emit(folder)

    def _release_dl_progress_callbacks(self):
        """ .. note:: self._dl_callback_delete["lock"] must be held. """
        for i in range(0, self._dl_callback_delete["to_delete"]):
            self._view_timer.remove_callback(self._update_timeout.emit,
                    self._dl_update_interval)
        self._dl_callback_delete["to_delete"] = 0

    def _on_view_update(self):
        #TODO might take too long for a DynamicTimer callback
        #self._dl_progress_widget.update()
        self._dl_progress_bar.update()

        #print("WFViewManager -> update: %d" % (ctypes.CDLL('libc.so.6').syscall(186)))

        # Note: This is required to have at least one additional view update
        # after a transfer has completed.
        self._dl_callback_delete["lock"].lock()
        if self._dl_callback_delete["to_delete"] > 0:
            self._release_dl_progress_callbacks()
        self._dl_callback_delete["lock"].unlock()

        print("######################### view update")


    def _remove_dl_progress_callback(self):
        self._dl_callback_delete["lock"].lock()
        self._dl_callback_delete["to_delete"] += 1
        self._dl_callback_delete["lock"].unlock()

    def on_download_complete(self, base_uri, from_path, to_path):
        self._remove_dl_progress_callback()

    def on_upload_complete(self, base_uri, from_path, to_path):
        self._remove_dl_progress_callback()
 
    def _connect_signals(self):
        self._mainwindow.open_file.connect(self.open_dialog_open_workflow)
        self._mainwindow.save.connect(self.open_dialog_save_workflow)
        self._mainwindow.save_as.connect(self.open_dialog_save_workflow_as)
        self._mainwindow.run.connect(self.run_clicked)
        self._mainwindow.new_file.connect(self.open_new_workflow)

        # Forwarded signals
        self._mainwindow.save_registries.connect(self.save_registries)
        self._mainwindow.save_paths.connect(self.save_paths)
        self._mainwindow.open_registry_settings.connect(self.open_registry_settings)
        self._mainwindow.open_path_settings.connect(self.open_path_settings)
        self._mainwindow.exit_client.connect(self.exit_client)
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
        self._editor.abort_job.connect(self.abort_job)
        self._editor.browse_workflow.connect(self.browse_workflow)
        self._editor.delete_workflow.connect(self.delete_workflow)
        self._editor.abort_workflow.connect(self.abort_workflow)
        self._editor.delete_file.connect(self.delete_file)
        self._editor.workflow_saved.connect(self._on_workflow_saved)

        self._update_timeout.connect(self._on_view_update)

    def get_editor(self):
        return self._editor

    def exit(self):
        #Placeholder for ViewManager teardowns
        #Due to bug https://bugreports.qt.io/browse/QTBUG-57228 we have to teardown all webengineviews explicitly:
        try:
            while(True):
                wev = self._webengineviews.pop()
                del wev
        except IndexError:
            pass

    def _init_dl_progressbar(self, unicore_state):
        self._dl_progress_widget = DownloadProgressWidget(self._mainwindow, unicore_state)
        self._dl_progress_bar    = DownloadProgressMenuButton(
                self._mainwindow.statusBar(),
                self._dl_progress_widget)
        self._dl_progress_bar.setMaximumWidth(150)
        self._dl_progress_bar.setMinimumWidth(75)
        self._mainwindow.statusBar().addPermanentWidget(self._dl_progress_bar)

    @staticmethod
    def get_homedir():
        if Qt.IsPySide:
            from PySide.QtGui import QDesktopServices
            return QDesktopServices.storageLocation(QDesktopServices.HomeLocation)

        import importlib
        qc = importlib.import_module("%s.QtCore" % Qt.__binding__)
        rtp = qc.QStandardPaths.standardLocations(qc.QStandardPaths.HomeLocation)
        if isinstance(rtp, list):
            rtp = rtp[0]
        return rtp


    def add_webengine_view(self, wev):
        self._webengineviews.append(wev)

    def __init__(self, unicore_state):
        super(WFViewManager, self).__init__()
        self._editor        = WFEditor()
        self._webengineviews = []

        self._mainwindow    = WFEditorMainWindow(self._editor)
        self._init_dl_progressbar(unicore_state)
        self._view_timer    = DynamicTimer()
        self._dl_update_interval =  200
        self._dl_callback_delete = { # used to schedule dl progress callbacks for deletion
                "lock": QMutex(),
                "to_delete": 0
            }
        self.last_used_path = self.get_homedir()

        self._connect_signals()
