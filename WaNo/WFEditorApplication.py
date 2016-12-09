from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import logging
import os

from PySide.QtCore import QObject, Signal
from PySide import QtCore,QtGui

from   lxml import etree

from WaNo import WaNoFactory
from WaNo.lib.pyura.pyura import UnicoreAPI, HTTPBasicAuthProvider
from WaNo.lib.pyura.pyura import ErrorCodes as UnicoreErrorCodes

from WaNo.lib.pyura.pyura import JobManager

from WaNo.view import WFViewManager
from WaNo.WaNoGitRevision import get_git_revision
from WaNo.Constants import SETTING_KEYS
from WaNo.UnicoreState import UnicoreStateFactory
from WaNo.UnicoreConnector import UnicoreConnector
from WaNo.UnicoreConnector import OPERATIONS as uops
from WaNo.UnicoreConnector import ERROR as uerror
from WaNo.view.WFEditorPanel import SubmitType
from WaNo.view.WaNoViews import WanoQtViewRoot

from WaNo.lib.CallableQThread import QThreadCallback

#TODO remove, testing only
from WaNo.lib.pyura.pyura import Storage
from collections import namedtuple

class WFEditorApplication(QThreadCallback):
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

    def _on_unicore_error(self, base_uri, operation, error):
        func = None

        if operation == uops.CONNECT_REGISTRY:
            func = self._on_unicore_connect_error
        elif operation == uops.DISCONNECT_REGISTRY:
            func = self._on_unicore_connect_error
        elif operation == uops.RUN_SINGLE_JOB:
            func = self._on_unicore_run_single_job_error

        if not func is None:
            func(base_uri, error)
        else:
            self._view_manager.show_error("General Unicore Error.")

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
                    "%s.%s" % (settings_path, SETTING_KEYS['registry.password']),
                    registry['password']
                )
            self.__settings.set_value(
                    "%s.%s" % (settings_path, SETTING_KEYS['registry.workflows']),
                    registry['workflows']
                )
            self.__settings.set_value(
                    "%s.%s" % (settings_path, SETTING_KEYS['registry.is_default']),
                    registry['default']
                )


        # last, save new settings to file
        self.__settings.save()
        
        # update registry list
        self._update_saved_registries()

    def _on_open_registry_settings(self):
        self._view_manager.open_dialog_registry_settings(
                self.__settings.get_value(SETTING_KEYS['registries'])
            )

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
                UnicoreConnector.create_update_job_list_args(base_uri),
                (self._on_fs_job_list_updated, (), {})
            )

    @QThreadCallback.callback
    def _on_workflow_list_updated(self, base_uri, workflows):
        self._view_manager.update_workflow_list(workflows)

    def _on_fs_worflow_list_update_request(self):
        base_uri = self._get_current_base_uri()
        self.exec_unicore_callback_operation.emit(
                uops.UPDATE_WF_LIST,
                UnicoreConnector.create_update_workflow_list_args(base_uri),
                (self._on_workflow_list_updated, (), {})
            )

    @QThreadCallback.callback
    def _on_fs_list_updated(self, base_uri, path, files):
        self._view_manager.update_filesystem_model(path, files)

    def _on_fs_job_update_request(self, path):
        base_uri = self._get_current_base_uri()
        self.exec_unicore_callback_operation.emit(
                uops.UPDATE_DIR_LIST,
                UnicoreConnector.create_update_dir_list_args(base_uri, path),
                (self._on_fs_list_updated, (), {})
            )

    def _on_fs_worflow_update_request(self, path):
        self._logger.debug("Querying %s from Unicore Registry" % path)
        # TODO
        print("wf update requested...")

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
        base_uri = self._get_current_base_uri()
        self.exec_unicore_callback_operation.emit(
                uops.DOWNLOAD_FILE,
                UnicoreConnector.create_data_transfer_args(
                        base_uri,
                        from_path,
                        to_path),
                (None, (), {})
            )

    def _on_fs_upload(self, local_file, dest_dir):
        base_uri = self._get_current_base_uri()
        self.exec_unicore_callback_operation.emit(
                uops.UPLOAD_FILE,
                UnicoreConnector.create_data_transfer_args(
                        base_uri,
                        local_file,
                        dest_dir),
                (None, (), {})
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
                UnicoreConnector.create_delete_file_args(base_uri, filename),
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

    def _on_fs_delete_job(self, job):
        base_uri = self._get_current_base_uri()
        self.exec_unicore_callback_operation.emit(
                uops.DELETE_JOB,
                UnicoreConnector.create_delete_job_args(base_uri, job),
                (self._on_job_deleted, (), { 'job': job})
            )


    ############################################################################
    #                                                                          #
    ############################################################################
    def __load_wanos_from_repo(self, wano_repo_path):
        self._logger.debug("loading WaNos from %s." % wano_repo_path)

        self.wanos=[]

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
                    icon = QtGui.QFileIconProvider().icon(QtGui.QFileIconProvider.Computer)
                    wano_icon = icon.pixmap(icon.actualSize(QtCore.QSize(128, 128)))
                else:
                    wano_icon = QtGui.QIcon(iconpath)

                self.wanos.append([name,fullpath,xmlpath,wano_icon])

        return self.wanos

    def __load_saved_workflows(self, workflow_path):
        self._logger.debug("loading Workflows from %s." % workflow_path)
        workflows = []
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
        return workflows

    ############################################################################
    #                       unicore  callbacks                                 #
    ############################################################################
    @QThreadCallback.callback
    def _cb_connect(self, base_uri, error, status, registry=None):
        #TODO debug only
        print("cb_connect@WFEditorApplication: err=%s, status=%s" % (str(error), str(status)))
        import platform
        import ctypes
        import threading
        from PySide.QtCore import QThread
        if platform.system() == "Linux":
            self._logger.debug("Unicore Thread ID (WFEditorApplication): %d\t%d\t%s" % \
                    (threading.current_thread().ident,
                    ctypes.CDLL('libc.so.6').syscall(186),
                    str(QThread.currentThreadId())))
        ### END TODO

        if registry is None:
            self._logger.error("Callback did not get expected data.")
            return

        if error == UnicoreErrorCodes.NO_ERROR:
            self._logger.info("Connected.")
            connected = True
            self._set_unicore_connected()
        else:
            self._logger.error("Failed to connect to registry: %s, %s" % \
                        (str(status), str(error))
                    )
            self._view_manager.show_error(
                    "Failed to connect to registry '%s'\n"\
                    "Connection returned status: %s." % \
                    (registry[SETTING_KEYS['registry.name']], str(status.name))
                )
            self._set_unicore_disconnected()

        # TODO Status updates should be delegated to update method...
        # can we manually trigger it / expire the timer?

    ############################################################################
    #                              unicore                                     #
    ############################################################################
    # no_status_update shuld be set to true if there are multiple successive calls
    # that all would individually update the connection status.
    # This avoids flickering of the icon.
    def _disconnect_unicore(self, no_status_update=False):
        self._logger.info("Disconnecting from registry")
        if not no_status_update:
            self._set_unicore_connecting()

        if not self._unicore is None:
            #TODO currently, a connection is not maintained in pyura
            #self._unicore.disconnected()
            UnicoreAPI.remove_registry(self._unicore)
            self._unicore.disconnect()
            self._unicore = None
            self._logger.debug("Disconnected from registry")
            if not no_status_update:
                self._set_unicore_disconnected()

    def _test_wf_submit(self):
        wf_manager = self._unicore.get_workflow_manager()
        err, status, wf = wf_manager.create('test_storage')
        print("err: %s, status: %s, wf_manager: %s" % (err, status, wf))
        if not wf is None and not wf == '':
            print("\n\nsending xml\n\n")
            xml = '<s:Workflow xmlns:s="http://www.chemomentum.org/workflow/simple"' + \
                '          xmlns:jsdl="http://schemas.ggf.org/jsdl/2005/11/jsdl" Id="TestWorkflow" >' + \
                '' + \
                '  <s:Documentation>' + \
                '    <s:Comment>Simple diamond graph</s:Comment>' + \
                '  </s:Documentation>' + \
                '' + \
                '  <s:Activity Id="date1" Type="JSDL">' + \
                '   <s:JSDL>' + \
                '      <jsdl:JobDescription>' + \
                '        <jsdl:Application>' + \
                '          <jsdl:ApplicationName>Date</jsdl:ApplicationName>' + \
                '          <jsdl:ApplicationVersion>1.0</jsdl:ApplicationVersion>' + \
                '        </jsdl:Application>' + \
                '       <jsdl:DataStaging>' + \
                '         <jsdl:FileName>stdout</jsdl:FileName>' + \
                '         <jsdl:CreationFlag>overwrite</jsdl:CreationFlag>' + \
                '         <jsdl:Target>' + \
                '           <jsdl:URI>c9m:${WORKFLOW_ID}/date1.out</jsdl:URI>' + \
                '         </jsdl:Target>' + \
                '         </jsdl:DataStaging>' + \
                '      </jsdl:JobDescription>' + \
                '    </s:JSDL>' + \
                '   </s:Activity>' + \
                '' + \
                '  <Activity Id="split" Type="Split"/>' + \
                '' + \
                '  <s:Activity Id="date2a" Type="JSDL">' + \
                '   <s:JSDL>' + \
                '      <jsdl:JobDescription>' + \
                '        <jsdl:Application>' + \
                '         <jsdl:ApplicationName>Date</jsdl:ApplicationName>' + \
                '        </jsdl:Application>' + \
                '       <jsdl:DataStaging>' + \
                '         <jsdl:FileName>stdout</jsdl:FileName>' + \
                '         <jsdl:CreationFlag>overwrite</jsdl:CreationFlag>' + \
                '         <jsdl:Target>' + \
                '           <jsdl:URI>c9m:${WORKFLOW_ID}/date2a.out</jsdl:URI>' + \
                '         </jsdl:Target>' + \
                '         </jsdl:DataStaging>' + \
                '      </jsdl:JobDescription>' + \
                '    </s:JSDL>' + \
                '   </s:Activity>' + \
                '' + \
                '  <s:Activity Id="date2b" Type="JSDL">' + \
                '   <s:JSDL>' + \
                '      <jsdl:JobDescription>' + \
                '        <jsdl:Application>' + \
                '         <jsdl:ApplicationName>Date</jsdl:ApplicationName>' + \
                '        </jsdl:Application>' + \
                '       <jsdl:DataStaging>' + \
                '         <jsdl:FileName>stdout</jsdl:FileName>' + \
                '         <jsdl:CreationFlag>overwrite</jsdl:CreationFlag>' + \
                '         <jsdl:Target>' + \
                '           <jsdl:URI>c9m:${WORKFLOW_ID}/date2b.out</jsdl:URI>' + \
                '         </jsdl:Target>' + \
                '         </jsdl:DataStaging>' + \
                '      </jsdl:JobDescription>' + \
                '    </s:JSDL>' + \
                '   </s:Activity>' + \
                '' + \
                '  <s:Activity Id="date3" Type="JSDL">' + \
                '   <s:JSDL>' + \
                '      <jsdl:JobDescription>' + \
                '        <jsdl:Application>' + \
                '         <jsdl:ApplicationName>Date</jsdl:ApplicationName>' + \
                '        </jsdl:Application>' + \
                '       <jsdl:DataStaging>' + \
                '         <jsdl:FileName>stdout</jsdl:FileName>' + \
                '         <jsdl:CreationFlag>overwrite</jsdl:CreationFlag>' + \
                '         <jsdl:Target>' + \
                '           <jsdl:URI>c9m:${WORKFLOW_ID}/date3.out</jsdl:URI>' + \
                '         </jsdl:Target>' + \
                '         </jsdl:DataStaging>' + \
                '      </jsdl:JobDescription>' + \
                '    </s:JSDL>' + \
                '   </s:Activity>' + \
                '' + \
                '  <s:Transition Id="date1-split" From="date1" To="split"/>' + \
                '  <s:Transition Id="split-date2a" From="split" To="date2a"/>' + \
                '  <s:Transition Id="split-date2b" From="split" To="date2b"/>' + \
                '  <s:Transition Id="date2b-date3" From="date2b" To="date3"/>' + \
                '  <s:Transition Id="date2a-date3" From="date2a" To="date3"/>' + \
                '' + \
                '</s:Workflow>'
            wf_manager.run(wf.split('/')[-1], xml)

    def _connect_unicore(self, index, no_status_update=False):
        success = False
        if not no_status_update:
            self._set_unicore_connecting()

        self._set_current_registry_index(index)
        registry    = self._get_current_registry()

        self._logger.info("Connecting to registry '%s'." % \
                registry[SETTING_KEYS['registry.name']]
            )

        if self._unicore is None:
            auth_provider = HTTPBasicAuthProvider(
                    registry[SETTING_KEYS['registry.username']],
                    registry[SETTING_KEYS['registry.password']]
                )
            self._unicore = UnicoreAPI.add_registry(
                    registry[SETTING_KEYS['registry.baseURI']],
                    auth_provider
                )

        self.exec_unicore_callback_operation.emit(
                uops.CONNECT_REGISTRY,
                UnicoreConnector.create_connect_args(
                        registry[SETTING_KEYS['registry.username']],
                        registry[SETTING_KEYS['registry.password']],
                        registry[SETTING_KEYS['registry.baseURI']],
                        wf_uri = registry[SETTING_KEYS['registry.workflows']]
                    ),
                (self._cb_connect, (), {'registry': registry})
            )

    def _run(self):
        editor = self._view_manager.get_editor()
        jobtype,directory = editor.run()
        if jobtype == SubmitType.SINGLE_WANO:
            print("Running", directory)
            self.run_job(directory)
        else:
            print("Running Workflows not yet implemented")
            #self.editor.execute_workflow(directory)

    def run_job(self, wano_dir):
        registry = self._get_current_registry()
        base_uri = self._get_current_base_uri(self)
        self.exec_unicore_operation.emit(
                uops.RUN_SINGLE_JOB,
                UnicoreConnector.create_single_job_args(
                        registry[SETTING_KEYS['registry.baseURI']],
                        wano_dir
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
        self._view_manager.open_registry_settings.connect(self._on_open_registry_settings)
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
        self._view_manager.delete_file.connect(self._on_fs_delete_file)

        self._unicore_connector.error.connect(self._on_unicore_error)


    def __init__(self, settings):
        super(WFEditorApplication, self).__init__()

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


        self._view_manager  = WFViewManager()
        self._unicore       = None # TODO pyura API

        self._unicore_connector = UnicoreConnector(self,
                UnicoreStateFactory.get_writer())

        self._unicore_connector.start()

        self._current_registry_index = 0

	# TODO model
        self.wanos = []

        UnicoreAPI.init()

        self._connect_signals()

        self.__start()
        self._logger.info("Logging Tab Enabled Version: " + get_git_revision())

