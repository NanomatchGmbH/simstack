from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import


import logging
import os
import zipfile
from os.path import join
from pathlib import Path

from Qt.QtCore import Signal

from Qt import QtCore, QtGui, QtWidgets, Qt

import sys
import time
import datetime

from SimStackServer.MessageTypes import ErrorCodes
from SimStackServer.Settings.ClusterSettingsProvider import ClusterSettingsProvider
from SimStackServer.Util.FileUtilities import trace_to_logger
from SimStackServer.WaNo.WaNoModels import FileNotFoundErrorSimStack
from SimStackServer.WorkflowModel import Resources
from SimStack.SimStackPaths import SimStackPaths
from SimStackServer.WaNo.WaNoExceptions import WorkflowSubmitError

from SimStackServer.WaNo.MiscWaNoTypes import WaNoListEntry, get_wano_xml_path
from SimStack.lib.QtClusterSettingsProvider import QtClusterSettingsProvider

from SimStack.view.WFViewManager import WFViewManager
from SimStack.WaNoGitRevision import get_git_revision
from SimStack.Constants import SETTING_KEYS
from SimStack.EditorState import StateFactory
from SimStack.SSHConnector import SSHConnector
from SimStack.SSHConnector import OPERATIONS as uops
from SimStack.SSHConnector import ERROR as uerror

from SimStack.lib.CallableQThread import CallableQThread

try:
    FileNotFoundError
except:
    FileNotFoundError = EnvironmentError

from collections import namedtuple

class WFEditorApplication(CallableQThread):
    exec_callback_operation = Signal(
            object, dict, object, name="ExecuteCallbackOperation")
    exec_operation = Signal(object, dict, name="ExecuteOperation")

    ############################################################################
    #                               Slots                                      #
    ############################################################################
    def _on_connect_error(self, base_uri, error):
        pass
    def _on_disconnect_error(self, base_uri, error):
        pass
    def _on_run_single_job_error(self, base_uri, error):
        msg_title   = "Error during job submission:\n\n"
        msg         = ""
        if error == uerror.REGISTRY_NOT_CONNECTED:
            msg = "Registry must be connected before submitting a job."
        else:
            msg = "Unknown Error."
        self._view_manager.show_error("%s%s" % (msg_title, msg))

    def _on_error(self, base_uri, operation, error, error_msg=None):
        func = None
        # Not connected error is always the same and trumps everything:
        if (error == uerror.REGISTRY_NOT_CONNECTED.value):
            msg = "Registry not connected, please connect to a SimStackServer first."
            self._view_manager.show_error("%s" % msg)
            #No logging required in this case
            return

        elif operation == uops.CONNECT_REGISTRY.value:
            func = self._on_connect_error
        elif operation == uops.DISCONNECT_REGISTRY.value:
            func = self._on_connect_error
        elif operation == uops.RUN_SINGLE_JOB.value:
            func = self._on_run_single_job_error
        elif operation in [uops.UPDATE_WF_LIST.value,uops.UPDATE_WF_JOB_LIST.value,uops.UPDATE_DIR_LIST.value,uops.RUN_WORKFLOW_JOB.value]:
             func = self._on_run_single_job_error

        if not func is None:
            func(base_uri, error)
        else:
            if error_msg is None or error_msg == "":
                error_msg = " Error for '%s' in operation '%s': %s." % \
                        (base_uri, uops(operation), uerror(error))

            self._view_manager.show_error("General Error.", error_msg)

        self._logger.error(" Error for '%s' in operation '%s': %s." % \
                (base_uri, uops(operation), uerror(error)))


    def _on_save_paths(self,path_dict):
        self.__settings.set_path_settings(path_dict)
        self.__settings.save()
        self.update_workflow_list()
        self._update_wanos()

    def _on_open_registry_settings(self):
        self._view_manager.open_dialog_registry_settings(
                self.__settings.get_value(SETTING_KEYS['registries'])
            )

    def _on_open_path_settings(self):
        self._view_manager.open_dialog_path_settings(self.__settings.get_path_settings())

    def _on_registry_changed(self, registry_name: str):
        self._reconnect_remote(registry_name)

    def _on_registry_connect(self, registry_name):
        self._connect_remote(registry_name)

    def _on_registry_disconnect(self):
        self._disconnect_remote()

    def _on_fs_job_list_updated(self, base_uri, jobs):
        self._view_manager.update_job_list(jobs)

    def _on_fs_job_list_update_request(self):
        base_uri = self._get_current_base_uri()
        self.exec_callback_operation.emit(
                uops.UPDATE_JOB_LIST,
                SSHConnector.create_update_job_list_args(base_uri),
                (self._on_fs_job_list_updated, (), {})
            )


    def _on_resources_updated(self, base_uri, resources):
        print(resources.get_queues())

    def _on_resources_update_request(self):
        base_uri = self._get_current_base_uri()
        self.exec_callback_operation.emit(
                uops.UPDATE_RESOURCES,
                SSHConnector.create_update_resources_args(base_uri),
                (self._on_resources_updated, (), {})
        )

    #@QThreadCallback.callback
    def _on_workflow_list_updated(self, base_uri, workflows):
        self._view_manager.update_workflow_list(workflows)

    def _on_fs_worflow_list_update_request(self):
        registry_name = self._get_current_registry_name()
        self._connector.update_workflow_list(registry_name,  (self._on_workflow_list_updated, (), {}) )

    #@QThreadCallback.callback
    def _on_fs_list_updated(self, base_uri, path, files):
        self._view_manager.update_filesystem_model(path, files)

    def _on_fs_job_update_request(self, path):
        registry_name = self._get_current_registry_name()
        self._connector.update_dir_list(registry_name,path,
                (self._on_fs_list_updated, (), {})
        )


    def _on_fs_workflow_update_request(self, wfid):
        self._logger.debug("Querying %s from Registry" % wfid)
        registry_name = self._get_current_registry_name()
        self._connector.update_workflow_job_list(registry_name, wfid,
                (self._on_fs_list_updated, (), {})
        )

    def _on_fs_directory_update_request(self, path):
        self._logger.debug("Querying %s from Registry" % path)
        # TODO
        self._on_fs_job_update_request(path)

    def _on_saved_workflows_update_request(self, path):
        self._update_workflow_list()

    def __on_download_update(self, uri, localdest, progress, total):
        print("\t%6.2f (%6.2f / %6.2f)\t%s" % (progress / total * 100., progress,
            total, uri))

    def __on_upload_update(self, uri, localfile, progress, total):
        print("\t%6.2f (%6.2f / %6.2f)\t%s" % (progress / total * 100., progress,
            total, uri))
        if progress / total * 100. >= 100.:
            print("requesting update for %s" % uri)
            self._on_fs_job_update_request(uri)


    def _on_fs_download(self, from_path, to_path):
        registry_name = self._get_current_registry_name()
        self._connector.download_file(registry_name,
                                              from_path,
                                              to_path,
                                              callback=(self._view_manager.on_download_complete,
                                                        (registry_name, from_path, to_path)
                                                        ,{})
        )


    def _on_fs_upload(self, local_files, dest_dir):
        registry_name = self._get_current_registry_name()

        self._connector.upload_files(
            registry_name,
            local_files,
            dest_dir,
            (self._view_manager.on_upload_complete, (
                registry_name, local_files, dest_dir), {})
        )

    #@QThreadCallback.callback
    def _on_file_deleted(self, base_uri, status, err, to_del=""):
        to_update = os.path.dirname(to_del)
        if err != ErrorCodes.NO_ERROR:
            self._view_manager.show_error(
                    "Failed to delete job '%s'\n"\
                    "Registry returned status: %s." % \
                    (to_del, str(status.name))
                )
        else:
            if not (to_update is None or to_update == ""):
                self._logger.debug(
                        "Issuing filesystem update for '%s' after delete." % \
                                to_update)
                # TODO we need to add the to_update path to the list in the
                # view first. otherwise, there will be no update...
                self._on_fs_job_update_request(to_update)

    def _on_fs_delete_file(self, filename):
        registry_name = self._get_current_registry_name()
        self._connector.delete_file(registry_name, filename, (self._on_file_deleted, (), { 'to_del': filename } ))


    #@QThreadCallback.callback
    def _on_job_deleted(self, base_uri, status, err, job=""):
        if err == ErrorCodes.NO_ERROR:
            self._on_fs_job_list_update_request()
        else:
            self._view_manager.show_error(
                    "Failed to delete job '%s'\n"\
                    "Registry returned status: %s." % \
                    (job, str(status.name))
                )


    #@QThreadCallback.callback
    def _on_job_aborted(self, base_uri, status, err, job=""):
        if err == ErrorCodes.NO_ERROR:
            self._on_fs_job_list_update_request()
        else:
            self._view_manager.show_error(
                    "Failed to abort job '%s'\n"\
                    "Registry returned status: %s." % \
                    (job, str(status.name))
                )

    #@QThreadCallback.callback
    def _on_workflow_deleted(self, base_uri, status, err, workflow=""):
        if err == ErrorCodes.NO_ERROR:
            self._on_fs_worflow_list_update_request()
        else:
            self._view_manager.show_error(
                "Failed to delete workflow '%s'\n" \
                "Registry returned status: %s." % \
                (workflow, str(status.name))
            )

    #@QThreadCallback.callback
    def _on_workflow_aborted(self, base_uri, status, err, workflow=""):
        print("here")

        """
        if err == ErrorCodes.NO_ERROR:
            self._on_fs_worflow_list_update_request()
        else:
            self._view_manager.show_error(
                "Failed to abort workflow '%s'\n" \
                "Registry returned status: %s." % \
                (workflow, str(status.name))
            )
        """

    def _on_fs_delete_job(self, job):
        base_uri = self._get_current_base_uri()
        self.exec_callback_operation.emit(
                uops.DELETE_JOB,
                SSHConnector.create_delete_job_args(base_uri, job),
                (self._on_job_deleted, (), { 'job': job})
            )

    def _on_fs_abort_job(self, job):
        base_uri = self._get_current_base_uri()
        self.exec_callback_operation.emit(
                uops.ABORT_JOB,
                SSHConnector.create_abort_job_args(base_uri, job),
                (self._on_job_aborted, (), { 'job': job})
            )

    def _on_fs_browse_workflow(self, workflow):
        registry_name = self._get_current_registry_name()
        #print("Im workflow",workflow)
        myurl = self._connector.get_workflow_url(registry_name, workflow)
        print(myurl)
        binding = Qt.__binding__
        if binding == "PyQt5":
            from PyQt5.QtWebEngineWidgets import QWebEngineView
        elif binding == "PySide2":
            from PySide2.QtWebEngineWidgets import QWebEngineView
        else:
            raise NotImplementedError("Only backends for PyQt5 and PySide2 are implemented currently.")

        from Qt.QtCore import QUrl
        import Qt.QtCore as QtCore

        web = QWebEngineView(parent=self._view_manager.get_editor())
        self._view_manager.add_webengine_view(web)

        web.setWindowFlags(web.windowFlags() | QtCore.Qt.Window)
        web.load(QUrl(myurl))
        web.window().resize(800,600)
        web.show()

    def _on_fs_delete_workflow(self, workflow):
        registry_name = self._get_current_registry_name()
        self._connector.delete_workflow(registry_name, workflow,
                (self._on_workflow_deleted, (), { 'workflow': workflow})
        )

    def _on_fs_abort_workflow(self, workflow):
        registry_name = self._get_current_registry_name()
        self._connector.abort_workflow(registry_name, workflow,
                (self._on_workflow_aborted, (), { 'workflow': workflow})
        )

    ############################################################################
    #                                                                          #
    ############################################################################
    def __load_wanos_from_repo(self, wano_repo_path):

        if wano_repo_path == '<embedded>':
            wano_repo_path = join(SimStackPaths.get_embedded_path(),"wanos")
        self._logger.debug("loading WaNos from %s." % wano_repo_path)

        self.wanos=[]

        try:
            p = Path(wano_repo_path)
            for folder in p.iterdir():
                try:
                    myfolder = None
                    if folder.is_dir():
                        myfolder = folder
                        name = myfolder.name
                    elif str(folder).endswith(".zip"):
                        myfolder = zipfile.Path(folder)
                        name = folder.name[:-4]

                    if myfolder is None:
                        # Probably just a random file
                        continue

                    iconname= "%s.png" % name
                    xmlname = "%s.xml" % name
                    xmlpath = get_wano_xml_path(myfolder)

                    iconpath= myfolder / iconname
                    if not xmlpath.is_file():
                        # Might be a random folder
                        continue
                    else:
                        with xmlpath.open('rt'):
                            pass
                    wano_icon = None
                    if iconpath.is_file():
                        try:
                            qp = QtGui.QPixmap()
                            with iconpath.open('rb') as infile:
                                qpdata = infile.read()
                            qp.loadFromData(qpdata)
                            wano_icon = QtGui.QIcon()
                            wano_icon.addPixmap(qp)
                        except KeyError as e:
                            # Again workaround for a zipfile bug, where is_file is True, but File isn't there.
                            pass
                    if wano_icon is None:
                        icon = QtWidgets.QFileIconProvider().icon(QtWidgets.QFileIconProvider.Computer)
                        wano_icon = icon.pixmap(icon.actualSize(QtCore.QSize(128, 128)))

                    wle = WaNoListEntry(name=name, folder=myfolder, icon=wano_icon)
                    self.wanos.append(wle)
                except KeyError as e:
                    if not isinstance(myfolder, zipfile.Path):
                        print(e)
                    # In this case we are in zip mode and couldn't open something
                    pass

        except OSError as e:
            print("WaNo Directory not found")

        return self.wanos

    def __load_saved_workflows(self, workflow_path):
        self._logger.debug("loading Workflows from %s." % workflow_path)
        if workflow_path == '<embedded>':
            workflow_path = join(SimStackPaths.get_embedded_path(),"workflows")
        workflows = []
        try:
            for directory in os.listdir(workflow_path):
                fulldir = os.path.join(workflow_path,directory)
                if not os.path.isdir(fulldir):
                    continue
                xmlpath = os.path.join(fulldir,directory) + ".xml"
                if os.path.isfile(xmlpath):
                    #print(xmlpath)
                    returnclass = namedtuple("workflowlistentry","name,workflow")
                    wf = returnclass(name=directory,workflow=fulldir)
                    workflows.append(wf)
        except OSError as e:
            print("Workflow Directory not found")

        return workflows

    def _cb_connect(self, base_uri, error, status, registry_name=None):
        if registry_name is None:
            self._logger.error("Callback did not get expected data.")
            return

        if error == ErrorCodes.NO_ERROR:
            self._logger.info("Connected.")
            self._set_connected()
        else:
            self._logger.error("Failed to connect to registry: %s, %s" % \
                        (str(status), str(error))
                    )
            self._view_manager.show_error(
                    "Failed to connect to registry '%s'\n"\
                    "Connection returned status: %s." % \
                    (registry_name, status)
                )
            self._set_disconnected()


    def _cb_disconnect(self, error, status, registry_name=None):
        self._set_disconnected()


    def _disconnect_remote(self, no_status_update=False):
        self._logger.info("Disconnecting from registry")
        #self._set_disconnected()

        registry_name = self._get_current_registry_name()
        self._connector.disconnect_registry(
            registry_name,
            (self._cb_disconnect,(),{'registry_name': registry_name})
        )

    def _connect_remote(self, registry_name, no_status_update=False):
        if registry_name == "":
            message = "No server definition selected. Please define a server in the Configuration -> Servers Dialog."
            WFViewManager.show_error(message)
            return
        if not no_status_update:
            self._set_connecting()

        self._set_current_registry_name(registry_name)

        registry = self._get_current_registry()
        self._logger.info("Connecting to registry '%s'." % \
                registry_name
            )

        self._connector.connect_registry(
            registry_name,
            (self._cb_connect,(),{'registry_name': registry_name})
        )


    @trace_to_logger
    def _run(self):
        name        = None
        jobtype     = None
        directory   = None
        wf_xml      = None
        editor      = self._view_manager.get_editor()

        self._view_manager.show_status_message("Preparing data...")

        try:
            name,jobtype,directory,wf_xml = editor.run(self._get_current_registry())
        except FileNotFoundErrorSimStack as e:
            self._view_manager.show_error("File not found during Workflow rendering. Error was: %s" % e)
            return
        except FileNotFoundError as e:
            import traceback
            traceback.print_exc()
            self._view_manager.show_error("Please save workflow before submit. Error was: %s"%e)
            return
        except WorkflowSubmitError as e:
            errormessage = "Error during workflow submit. Error was:\n\n -----\n\n%s"%e
            import traceback
            traceback.print_exc()
            self._view_manager.show_error(errormessage)
            return
        except Exception as e:
            errormessage = "Error during workflow submit. Error was:\n\n -----\n\n%s"%e
            import traceback
            traceback.print_exc()
            self._view_manager.show_error(errormessage)
            return

        self.run_workflow(wf_xml,directory,name)
        self._view_manager.show_status_message("Started workflow: %s" % name)


    def run_workflow(self, xml, directory, name):
        registry_name = self._get_current_registry_name()
        now = datetime.datetime.now()
        nowstr = now.strftime("%Y-%m-%d-%Hh%Mm%Ss")
        submitname = "%s-%s" %(nowstr, name)
        to_upload = os.path.join(directory,"workflow_data")
        self._connector.run_workflow_job(registry_name,submitname,to_upload,xml)


    def _reconnect_remote(self, registry_name):
        self._logger.info("Reconnecting to Registry.")
        self._set_connecting()
        # quietly disconnect
        if self._get_current_registry_name():
            self._disconnect_remote(no_status_update = True)

        success = self._connect_remote(registry_name)

    def _set_disconnected(self):
        self._view_manager.set_registry_connection_status(
                self._view_manager.REGISTRY_CONNECTION_STATES.disconnected
            )
    def _set_connected(self):
        self._view_manager.set_registry_connection_status(
                self._view_manager.REGISTRY_CONNECTION_STATES.connected
            )
    def _set_connecting(self):
        self._view_manager.set_registry_connection_status(
                self._view_manager.REGISTRY_CONNECTION_STATES.connecting
            )

    def _get_registry_by_name(self, registry_name: str):
        return self._registries[registry_name]

    def _get_default_registry(self):
        default = 0
        """
            Default handler should be: last selected
            TODO
        """
        return default

    def _get_registry_names(self):
        registries = QtClusterSettingsProvider.get_registries()
        return [*registries.keys()]

    def _set_current_registry_name(self, registry_name: str):
        self._current_registry_name = registry_name

    def _get_current_registry_name(self):
        return self._current_registry_name

    def _get_current_registry(self) -> Resources:
        return self._registries[self._get_current_registry_name()]

    def _get_current_base_uri(self):
        registry = self._get_current_registry()
        return registry.base_URI

    def _get_current_workflow_uri(self):
        registry = self._get_current_registry()
        return "" if registry is None \
                else registry[SETTING_KEYS['registry.workflows']]


    def _update_wanos(self):
        self.__load_wanos_from_repo(
                self.__settings.get_value(SETTING_KEYS['wanoRepo'])
            )
        self._view_manager.update_wano_list(self.wanos)

    def _update_workflow_list(self):
        workflows = self.__load_saved_workflows(
                self.__settings.get_value(SETTING_KEYS['workflows'])
            )
        self._view_manager.update_saved_workflows_list(workflows)

    def update_workflow_list(self):
        self._update_workflow_list()

    def _update_saved_registries(self):
        default = self._get_default_registry()
        regList = self._get_registry_names()

        self._view_manager.update_registries(regList, selected=default)

    def _update_all(self):
        self._update_saved_registries()
        self._update_wanos()
        self._update_workflow_list()

    ############################################################################
    #                            exit                                          #
    ############################################################################
    def exit(self):
        self._view_manager.exit()
        self._connector.quit()

    ############################################################################
    #                            init                                          #
    ############################################################################
    def __start(self):
        self._view_manager.show_mainwindow()
        self._update_all()

    def _connect_signals(self):
        self._view_manager.save_paths.connect(self._on_save_paths)
        self._view_manager.open_registry_settings.connect(self._on_open_registry_settings)
        self._view_manager.open_path_settings.connect(self._on_open_path_settings)
        self._view_manager.registry_changed.connect(self._on_registry_changed)
        self._view_manager.disconnect_registry.connect(self._on_registry_disconnect)
        self._view_manager.connect_registry.connect(self._on_registry_connect)
        self._view_manager.run_clicked.connect(self._run)

        self._view_manager.request_job_list_update.connect(self._on_fs_job_list_update_request)
        self._view_manager.request_worflow_list_update.connect(self._on_fs_worflow_list_update_request)
        self._view_manager.request_job_update.connect(self._on_fs_job_update_request)
        self._view_manager.request_worflow_update.connect(self._on_fs_workflow_update_request)
        self._view_manager.request_directory_update.connect(self._on_fs_directory_update_request)
        self._view_manager.request_saved_workflows_update.connect(self._on_saved_workflows_update_request)
        self._view_manager.download_file_to.connect(self._on_fs_download)
        self._view_manager.upload_file.connect(self._on_fs_upload)
        self._view_manager.delete_job.connect(self._on_fs_delete_job)
        self._view_manager.abort_job.connect(self._on_fs_abort_job)
        self._view_manager.browse_workflow.connect(self._on_fs_browse_workflow)
        self._view_manager.delete_workflow.connect(self._on_fs_delete_workflow)
        self._view_manager.abort_workflow.connect(self._on_fs_abort_workflow)
        self._view_manager.delete_file.connect(self._on_fs_delete_file)

        self._view_manager.exit_client.connect(self._client_about_to_exit)

        self._connector.error.connect(self._on_error)

    @staticmethod
    def exec_by_time(cutoff_time):
        timestamp = int(time.time())
        if timestamp > cutoff_time:
            print("License time expired, please renew, Exiting.")
            sys.exit(45)

    @classmethod
    def license_check(cls):
        until = datetime.datetime(year=2020, month=4, day=8)
        #cls.exec_by_time(until.timestamp())
        pass

    def _client_about_to_exit(self):
        print("Exiting.")
        self.exit()

    def __init__(self, settings):
        super(WFEditorApplication, self).__init__()
        self.license_check()

        self.__settings     = settings

        self._logger        = logging.getLogger('WFELOG')
        #TODO debug only
        import sys
        loglevel = logging.DEBUG
        self._logger.setLevel(loglevel)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(loglevel)
        self._logger.addHandler(ch)
        ##### END TODO


        self._connector = SSHConnector(self,
                StateFactory.get_writer())

        self._view_manager  = WFViewManager(StateFactory.get_reader())

        self._current_registry_name = None
        self._registries = QtClusterSettingsProvider.get_registries()
        self.wanos = []

        self._connect_signals()

        self.__start()
        self._logger.info("Logging Tab Enabled Version: " + get_git_revision())





