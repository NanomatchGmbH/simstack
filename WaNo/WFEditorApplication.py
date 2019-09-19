from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import


import logging
import os

from Qt.QtCore import QObject, Signal
from Qt import QtCore,QtGui,QtWidgets
import sys
import time
import datetime

from WaNo import WaNoFactory
from pyura.pyura import UnicoreAPI
from pyura.pyura.HTTPBasicAuthProvider import HTTPBasicAuthProvider
from pyura.pyura.Constants import ErrorCodes as UnicoreErrorCodes

from pyura.pyura import JobManager

from WaNo.view.WFViewManager import WFViewManager
from WaNo.WaNoGitRevision import get_git_revision
from WaNo.Constants import SETTING_KEYS
from WaNo.UnicoreState import UnicoreStateFactory
from WaNo.SSHConnector import SSHConnector
from WaNo.SSHConnector import OPERATIONS as uops
from WaNo.SSHConnector import ERROR as uerror
from WaNo.view.WFEditorPanel import SubmitType
from WaNo.view.WaNoViews import WanoQtViewRoot

from WaNo.lib.CallableQThread import QThreadCallback, CallableQThread
from pyura.pyura.helpers import trace_to_logger

try:
    FileNotFoundError
except:
    FileNotFoundError = EnvironmentError

#TODO remove, testing only
from pyura.pyura import Storage
from collections import namedtuple

class WFEditorApplication(CallableQThread):
    exec_unicore_callback_operation = Signal(
            object, dict, object, name="ExecuteUnicoreCallbackOperation")
    exec_unicore_operation = Signal(object, dict, name="ExecuteUnicoreOperation")

    ############################################################################
    #                               Slots                                      #
    ############################################################################
    def _on_unicore_connect_error(self, base_uri, error):
        pass
    def _on_unicore_disconnect_error(self, base_uri, error):
        pass
    def _on_unicore_run_single_job_error(self, base_uri, error):
        msg_title   = "Error during job submission:\n\n"
        msg         = ""
        if error == uerror.REGISTRY_NOT_CONNECTED:
            msg = "Registry must be connected before submitting a job."
        else:
            msg = "Unknown Error."
        self._view_manager.show_error("%s%s" % (msg_title, msg))

    def _on_unicore_error(self, base_uri, operation, error, error_msg=None):
        func = None
        # Not connected error is always the same and trumps everything:
        if (error == uerror.REGISTRY_NOT_CONNECTED.value):
            msg = "Registry not connected, please connect to a UNICORE server first."
            self._view_manager.show_error("%s" % msg)
            #No logging required in this case
            return

        elif operation == uops.CONNECT_REGISTRY.value:
            func = self._on_unicore_connect_error
        elif operation == uops.DISCONNECT_REGISTRY.value:
            func = self._on_unicore_connect_error
        elif operation == uops.RUN_SINGLE_JOB.value:
            func = self._on_unicore_run_single_job_error
        elif operation in [uops.UPDATE_WF_LIST.value,uops.UPDATE_WF_JOB_LIST.value,uops.UPDATE_DIR_LIST.value,uops.RUN_WORKFLOW_JOB.value]:
             func = self._on_unicore_run_single_job_error

        if not func is None:
            func(base_uri, error)
        else:
            if error_msg is None or error_msg == "":
                error_msg = "Unicore Error for '%s' in operation '%s': %s." % \
                        (base_uri, uops(operation), uerror(error))

            self._view_manager.show_error("General Unicore Error.", error_msg)

        self._logger.error("Unicore Error for '%s' in operation '%s': %s." % \
                (base_uri, uops(operation), uerror(error)))

    def _on_save_registries(self, registriesList):
        self._logger.debug("Saving UNICORE registries.")

        # first, delete all previous settings
        self.__settings.delete_value(SETTING_KEYS['registries'])

        # second, add new registries
        for i, registry in enumerate(registriesList):
            settings_path = "%s.%d" % (SETTING_KEYS['registries'], i)
            self.__settings.set_value(
                    "%s.%s" % (settings_path, SETTING_KEYS['registry.name']),
                    registry['name']
                )
            self.__settings.set_value(
                    "%s.%s" % (settings_path, SETTING_KEYS['registry.baseURI']),
                    registry['baseURI']
                )
            self.__settings.set_value(
                    "%s.%s" % (settings_path, SETTING_KEYS['registry.username']),
                    registry['username']
                )
            self.__settings.set_value(
                    "%s.%s" % (settings_path, SETTING_KEYS['registry.is_default']),
                    registry['default']
                )


        # last, save new settings to file
        self.__settings.save()
        
        # update registry list
        self._update_saved_registries()

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

    def _on_registry_changed(self, index):
        self._logger.info("Registry changed to '%s'." % \
                self.__settings.get_value(
                    "%s.%d.name" % (SETTING_KEYS['registries'], index)
                )
            )
        self._reconnect_unicore(index)

    def _on_registry_connect(self, index):
        self._connect_unicore(index)

    def _on_registry_disconnect(self):
        self._disconnect_unicore()

    #FIXME remove
    def fake_storage_manager_get_list(self):
        print("fake_storage_manager_get_list")
        return [Storage('timo_Home'), Storage('Foo')]

    #FIXME remove
    def fake_storage_manager_get_file_list(storage_id, path):
        l = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
                "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
        import random
        random.shuffle(l)
        return [''.join(l[:random.randint(0,len(l))]) for i in range(0, random.randint(0, 6))]


    @QThreadCallback.callback
    def _on_fs_job_list_updated(self, base_uri, jobs):
        self._view_manager.update_job_list(jobs)

    def _on_fs_job_list_update_request(self):
        base_uri = self._get_current_base_uri()
        self.exec_unicore_callback_operation.emit(
                uops.UPDATE_JOB_LIST,
                SSHConnector.create_update_job_list_args(base_uri),
                (self._on_fs_job_list_updated, (), {})
            )


    @QThreadCallback.callback
    def _on_resources_updated(self, base_uri, resources):
        print(resources.get_queues())

    def _on_resources_update_request(self):
        base_uri = self._get_current_base_uri()
        self.exec_unicore_callback_operation.emit(
                uops.UPDATE_RESOURCES,
                SSHConnector.create_update_resources_args(base_uri),
                (self._on_resources_updated, (), {})
        )

    @QThreadCallback.callback
    def _on_workflow_list_updated(self, base_uri, workflows):
        self._view_manager.update_workflow_list(workflows)

    def _on_fs_worflow_list_update_request(self):
        base_uri = self._get_current_base_uri()
        self.exec_unicore_callback_operation.emit(
                uops.UPDATE_WF_LIST,
                SSHConnector.create_update_workflow_list_args(base_uri),
                (self._on_workflow_list_updated, (), {})
            )

    @QThreadCallback.callback
    def _on_fs_list_updated(self, base_uri, path, files):
        self._view_manager.update_filesystem_model(path, files)

    def _on_fs_job_update_request(self, path):
        registry = self._get_current_registry()
        self.exec_unicore_callback_operation.emit(
                uops.UPDATE_DIR_LIST,
                (registry,path),
                (self._on_fs_list_updated, (), {})
            )

    def _on_fs_worflow_update_request(self, wfid):
        self._logger.debug("Querying %s from Unicore Registry" % wfid)
        base_uri = self._get_current_base_uri()
        self.exec_unicore_callback_operation.emit(
                uops.UPDATE_WF_JOB_LIST,
                SSHConnector.create_update_workflow_job_list_args(base_uri, wfid),
                (self._on_fs_list_updated, (), {})
            )

    def _on_fs_directory_update_request(self, path):
        self._logger.debug("Querying %s from Unicore Registry" % path)
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
        registry = self._get_current_registry()
        self._unicore_connector.download_file(registry,
                                              from_path,
                                              to_path,
                                              callback=(self._view_manager.on_download_complete,
                                                        (registry, from_path, to_path)
                                                        ,{})
        )


    def _on_fs_upload(self, local_files, dest_dir):
        registry = self._get_current_registry()

        self._unicore_connector.upload_files(
            registry,
            local_files,
            dest_dir,
            (self._view_manager.on_upload_complete, (
                registry, local_files, dest_dir), {})
        )

    @QThreadCallback.callback
    def _on_file_deleted(self, base_uri, status, err, to_del=""):
        to_update = os.path.dirname(to_del)
        if err != UnicoreErrorCodes.NO_ERROR:
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
        base_uri = self._get_current_base_uri()
        self.exec_unicore_callback_operation.emit(
                uops.DELETE_FILE,
                SSHConnector.create_delete_file_args(base_uri, filename),
                (self._on_file_deleted, (), { 'to_del': filename } )
            )

    @QThreadCallback.callback
    def _on_job_deleted(self, base_uri, status, err, job=""):
        if err == UnicoreErrorCodes.NO_ERROR:
            self._on_fs_job_list_update_request()
        else:
            self._view_manager.show_error(
                    "Failed to delete job '%s'\n"\
                    "Registry returned status: %s." % \
                    (job, str(status.name))
                )


    @QThreadCallback.callback
    def _on_job_aborted(self, base_uri, status, err, job=""):
        if err == UnicoreErrorCodes.NO_ERROR:
            self._on_fs_job_list_update_request()
        else:
            self._view_manager.show_error(
                    "Failed to abort job '%s'\n"\
                    "Registry returned status: %s." % \
                    (job, str(status.name))
                )

    @QThreadCallback.callback
    def _on_workflow_deleted(self, base_uri, status, err, workflow=""):
        if err == UnicoreErrorCodes.NO_ERROR:
            self._on_fs_worflow_list_update_request()
        else:
            self._view_manager.show_error(
                "Failed to delete workflow '%s'\n" \
                "Registry returned status: %s." % \
                (workflow, str(status.name))
            )

    @QThreadCallback.callback
    def _on_workflow_aborted(self, base_uri, status, err, workflow=""):
        if err == UnicoreErrorCodes.NO_ERROR:
            self._on_fs_worflow_list_update_request()
        else:
            self._view_manager.show_error(
                "Failed to abort workflow '%s'\n" \
                "Registry returned status: %s." % \
                (workflow, str(status.name))
            )

    def _on_fs_delete_job(self, job):
        base_uri = self._get_current_base_uri()
        self.exec_unicore_callback_operation.emit(
                uops.DELETE_JOB,
                SSHConnector.create_delete_job_args(base_uri, job),
                (self._on_job_deleted, (), { 'job': job})
            )

    def _on_fs_abort_job(self, job):
        base_uri = self._get_current_base_uri()
        self.exec_unicore_callback_operation.emit(
                uops.ABORT_JOB,
                SSHConnector.create_abort_job_args(base_uri, job),
                (self._on_job_aborted, (), { 'job': job})
            )

    def _on_fs_delete_workflow(self, workflow):
        base_uri = self._get_current_base_uri()

        self.exec_unicore_callback_operation.emit(
                uops.DELETE_WORKFLOW,
                SSHConnector.create_delete_workflow_args(base_uri, workflow),
                (self._on_workflow_deleted, (), { 'workflow': workflow})
            )

    def _on_fs_abort_workflow(self, workflow):
        base_uri = self._get_current_base_uri()

        self.exec_unicore_callback_operation.emit(
                uops.ABORT_WORKFLOW,
                SSHConnector.create_abort_workflow_args(base_uri, workflow),
                (self._on_workflow_aborted, (), { 'workflow': workflow})
            )

    ############################################################################
    #                                                                          #
    ############################################################################
    def __load_wanos_from_repo(self, wano_repo_path):
        self._logger.debug("loading WaNos from %s." % wano_repo_path)

        self.wanos=[]

        try:
            for folder in os.listdir(wano_repo_path):
                fullpath = os.path.join(wano_repo_path, folder)
                if os.path.isdir(fullpath):
                    name = folder
                    iconname= "%s.png" % folder
                    xmlname = "%s.xml" % folder

                    xmlpath = os.path.join(fullpath,xmlname)
                    iconpath=os.path.join(fullpath,iconname)
                    if not os.path.isfile(xmlpath):
                        # Might be a random folder
                        continue
                    if not os.path.isfile(iconpath):
                        icon = QtWidgets.QFileIconProvider().icon(QtWidgets.QFileIconProvider.Computer)
                        wano_icon = icon.pixmap(icon.actualSize(QtCore.QSize(128, 128)))
                    else:
                        wano_icon = QtGui.QIcon(iconpath)

                    self.wanos.append([name,fullpath,xmlpath,wano_icon])
        except OSError as e:
            print("WaNo Directory not found")

        return self.wanos

    def __load_saved_workflows(self, workflow_path):
        self._logger.debug("loading Workflows from %s." % workflow_path)
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

    ############################################################################
    #                       unicore  callbacks                                 #
    ############################################################################
    @QThreadCallback.callback
    def _cb_connect(self, base_uri, error, status, registry=None):
        #print("cb_connect@WFEditorApplication: err=%s, status=%s" % (str(error), str(status)))

        if registry is None:
            self._logger.error("Callback did not get expected data.")
            return

        if error == UnicoreErrorCodes.NO_ERROR:
            self._logger.info("Connected.")
            self._set_unicore_connected()
        else:
            self._logger.error("Failed to connect to registry: %s, %s" % \
                        (str(status), str(error))
                    )
            self._view_manager.show_error(
                    "Failed to connect to registry '%s'\n"\
                    "Connection returned status: %s." % \
                    (registry[SETTING_KEYS['registry.name']], status)
                )
            self._set_unicore_disconnected()

        # TODO Status updates should be delegated to update method...
        # can we manually trigger it / expire the timer?

    ############################################################################
    #                       unicore  callbacks                                 #
    ############################################################################
    @QThreadCallback.callback
    def _cb_disconnect(self, error, status, registry=None):
        self._set_unicore_disconnected()

    ############################################################################
    #                              unicore                                     #
    ############################################################################
    # no_status_update shuld be set to true if there are multiple successive calls
    # that all would individually update the connection status.
    # This avoids flickering of the icon.
    def _disconnect_unicore(self, no_status_update=False):
        self._logger.info("Disconnecting from registry")
        #self._set_unicore_disconnected()

        registry = self._get_current_registry()
        self._unicore_connector.disconnect_registry(
            registry,
            (self._cb_disconnect,(),{'registry': registry})
        )

    def _connect_unicore(self, index, no_status_update=False):
        if not no_status_update:
            self._set_unicore_connecting()

        self._set_current_registry_index(index)
        registry = self._get_current_registry()
        self._logger.info("Connecting to registry '%s'." % \
                registry[SETTING_KEYS['registry.name']]
            )

        self._unicore_connector.connect_registry(
            registry,
            (self._cb_connect,(),{'registry': registry})
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
            name,jobtype,directory,wf_xml = editor.run()
        except FileNotFoundError as e:
            self._view_manager.show_error("Please save workflow before submit. Error was: %s"%e)

        #if jobtype == SubmitType.SINGLE_WANO:
        #    print("Running", directory)
        #    self.run_job(directory,name)
        #    self._view_manager.show_status_message("Started job: %s" % name)
        if jobtype == SubmitType.WORKFLOW or jobtype == SubmitType.SINGLE_WANO:
            #print("Running Workflows not yet implemented")
            self.run_workflow(wf_xml,directory,name)
            self._view_manager.show_status_message("Started workflow: %s" % name)
            ### TODO, HERE TIMO!

            #self.editor.execute_workflow(directory)
        else:
            # Error case...
            pass

    def run_workflow(self, xml, directory, name):
        registry= self._get_current_registry()
        now = datetime.datetime.now()
        nowstr = now.strftime("%Y-%m-%d-%H:%M:%S")
        submitname = "%s-%s" %(nowstr, name)
        to_upload = os.path.join(directory,"jobs")
        self._unicore_connector.run_workflow_job(registry,submitname,to_upload,xml)



    def run_job(self, wano_dir, name):
        base_uri = self._get_current_base_uri()
        self.exec_unicore_operation.emit(
                uops.RUN_SINGLE_JOB,
                SSHConnector.create_single_job_args(
                        base_uri,
                        wano_dir,
                        name
                    )
            )

    def _reconnect_unicore(self, registry_index):
        self._logger.info("Reconnecting to Unicore Registry.")
        self._set_unicore_connecting()
        # quietly disconnect
        self._disconnect_unicore(no_status_update = True)

        success = self._connect_unicore(registry_index)


    ############################################################################
    #                             helpers                                      #
    ############################################################################
    def _set_unicore_disconnected(self):
        self._view_manager.set_registry_connection_status(
                self._view_manager.REGISTRY_CONNECTION_STATES.disconnected
            )
    def _set_unicore_connected(self):
        self._view_manager.set_registry_connection_status(
                self._view_manager.REGISTRY_CONNECTION_STATES.connected
            )
    def _set_unicore_connecting(self):
        self._view_manager.set_registry_connection_status(
                self._view_manager.REGISTRY_CONNECTION_STATES.connecting
            )

    def _get_registry_by_index(self, index):
        registry = None
        query_str = "%s.%d" % (SETTING_KEYS['registries'], index)
        try:
            registry = self.__settings.get_value(query_str)
        except:
            pass
        return registry

    def _get_default_registry(self):
        default = 0
        registries = self.__settings.get_value(SETTING_KEYS['registries'])

        for i, r in enumerate(registries):
            if r[SETTING_KEYS['registry.is_default']]:
                default = i
                break

        return default

    def _get_registry_names(self):
        registries = self.__settings.get_value(SETTING_KEYS['registries'])
        return [r[SETTING_KEYS['registry.name']] for r in registries]

    def _set_current_registry_index(self, index):
        self._current_registry_index = index if not index is None \
                and index > 0 and index < len(self._get_registry_names()) \
                else self._get_default_registry()

    def _get_current_registry_index(self):
        return self._current_registry_index

    def _get_current_registry(self):
        idx = self._get_current_registry_index()
        return self._get_registry_by_index(idx)

    def _get_current_base_uri(self):
        registry = self._get_current_registry()
        return "" if registry is None \
                else registry[SETTING_KEYS['registry.baseURI']]

    def _get_current_workflow_uri(self):
        registry = self._get_current_registry()
        return "" if registry is None \
                else registry[SETTING_KEYS['registry.workflows']]




    ############################################################################
    #                             update                                       #
    ############################################################################
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

    ############################################################################
    #                            init                                          #
    ############################################################################
    def __start(self):
        self._view_manager.show_mainwindow()
        self._update_all()

    def _connect_signals(self):
        self._view_manager.save_registries.connect(self._on_save_registries)
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
        self._view_manager.request_worflow_update.connect(self._on_fs_worflow_update_request)
        self._view_manager.request_directory_update.connect(self._on_fs_directory_update_request)
        self._view_manager.request_saved_workflows_update.connect(self._on_saved_workflows_update_request)
        self._view_manager.download_file_to.connect(self._on_fs_download)
        self._view_manager.upload_file.connect(self._on_fs_upload)
        self._view_manager.delete_job.connect(self._on_fs_delete_job)
        self._view_manager.abort_job.connect(self._on_fs_abort_job)
        self._view_manager.delete_workflow.connect(self._on_fs_delete_workflow)
        self._view_manager.abort_workflow.connect(self._on_fs_abort_workflow)
        self._view_manager.delete_file.connect(self._on_fs_delete_file)

        self._unicore_connector.error.connect(self._on_unicore_error)

    @staticmethod
    def exec_by_time(cutoff_time):
        timestamp = int(time.time())
        if timestamp > cutoff_time:
            print("License time expired, please renew, Exiting.")
            sys.exit(45)

    @classmethod
    def license_check(cls):
        #cls.exec_by_time(1530396000)
        pass

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

        #TODO debug only
        import platform
        import ctypes
        import threading
        if platform.system() == "Linux":
            self._logger.debug("Gui Thread ID: %d\t%d" % \
                    (threading.current_thread().ident,
                    ctypes.CDLL('libc.so.6').syscall(186)))
        ##### END TODO


        self._unicore       = None # TODO pyura API

        self._unicore_connector = SSHConnector(self,
                UnicoreStateFactory.get_writer())

        self._unicore_connector.start()

        self._view_manager  = WFViewManager(UnicoreStateFactory.get_reader())

        self._current_registry_index = 0
        self.wanos = []

        UnicoreAPI.init()

        self._connect_signals()

        self.__start()
        self._logger.info("Logging Tab Enabled Version: " + get_git_revision())

