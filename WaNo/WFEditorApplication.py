from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import logging
import os
import shlex

from PySide.QtCore import QObject
from PySide import QtCore,QtGui

from   lxml import etree

from WaNo import WaNoFactory
from WaNo.lib.FileSystemTree import filewalker
from WaNo.lib.pyura.pyura import UnicoreAPI, HTTPBasicAuthProvider
from WaNo.lib.pyura.pyura import ErrorCodes as UnicoreErrorCodes

from WaNo.lib.pyura.pyura import JobManager

from WaNo.view import WFViewManager
from WaNo.WaNoGitRevision import get_git_revision
from WaNo.Constants import SETTING_KEYS
from WaNo.view.WFEditorPanel import SubmitType
from WaNo.view.WaNoViews import WanoQtViewRoot

#TODO remove, testing only
from WaNo.lib.pyura.pyura import Storage
from collections import namedtuple

class WFEditorApplication(QObject):
    ############################################################################
    #                               Slots                                      #
    ############################################################################
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


    def _on_fs_job_list_update_request(self):
        self._logger.debug("Querying jobs from Unicore Registry")
        ok = True
        files = []
        #TODO factor out tests
        if ok:
            #TODO use job manager?!
            job_manager = self._unicore.get_job_manager()
            job_manager.update_list()
            files = [{
                        'id': s.get_id(),
                        'name': s.get_id(),
                        'type': 'j',
                        'path': s.get_working_dir()
                    } for s in job_manager.get_list()]
            print("jobs:\n\n\n\n%s\n\n\n" % job_manager.get_list())
            print("Got files: %s" % files)
            self._view_manager.update_job_list(files)

    def _on_fs_worflow_list_update_request(self):
        self._logger.debug("Querying workflows from Unicore Registry")
        ok = True
        workflows = []
        #TODO factor out tests
        if ok:
            wf_manager = self._unicore.get_workflow_manager()
            wf_manager.update_list()
            workflows = [{
                    'id': s.get_id(),
                    'name': s.get_name(),
                    'type': 'w',
                    'path': s.get_working_dir()
                    } for s in wf_manager.get_list()]
            self._view_manager.update_workflow_list(workflows)

    def _extract_storage_path(self, path):
        storage = None
        querypath = ''
        splitted = [p for p in path.split('/') if not p is None and p != ""]

        if len(splitted) >= 1:
            storage   = splitted[0]
        if len(splitted) >= 2:
            querypath = '/'.join(splitted[1:]) if len(splitted) > 1 else ''

        return (storage, querypath)

    def _on_fs_job_update_request(self, path):
        self._logger.debug("Querying %s from Unicore Registry" % path)
        ok = True
        files = []
        #TODO factor out tests

        storage, querypath = self._extract_storage_path(path)

        if ok and not storage is None:
            #TODO use job manager?!
            storage_manager = self._unicore.get_storage_manager()
            storage_manager.update_list()
            print("Requesting %s:%s" % (storage, querypath))
            files = storage_manager.get_file_list(
                    storage_id=storage, path=querypath)
            self._view_manager.update_filesystem_model(path, files)
            print("Got files: %s" % files)

    def _on_fs_worflow_update_request(self, path):
        self._logger.debug("Querying %s from Unicore Registry" % path)
        # TODO
        print("wf update requested...")

    def _on_fs_directory_update_request(self, path):
        self._logger.debug("Querying %s from Unicore Registry" % path)
        # TODO
        self._on_fs_job_update_request(path)

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
        storage, path = self._extract_storage_path(from_path)

        storage_manager = self._unicore.get_storage_manager()

        #TODO do in future/Thread
        status, err = storage_manager.get_file(
                path,
                to_path,
                storage_id=storage,
                callback=self.__on_download_update)
        print("status: %s, err: %s" % (status, err))

    def _on_fs_upload(self, local_file, dest_dir):
        storage, path = self._extract_storage_path(dest_dir)
        storage_manager = self._unicore.get_storage_manager()
        remote_filepath = os.path.join(path, os.path.basename(local_file))

        #TODO do in future/Thread
        print("uploading '%s' to %s:%s" % (local_file, storage, path))
        status, err, json = storage_manager.upload_file(
                local_file,
                remote_filename=remote_filepath,
                storage_id=storage,
                callback=self.__on_upload_update)
        print("status: %s, err: %s, json: %s" % (status, err, json))
        #TODO request update when done

    def _on_fs_delete_file(self, filename):
        storage, path = self._extract_storage_path(filename)
        storage_manager = self._unicore.get_storage_manager()

        print("deleting %s:%s" % (storage, path))
        if not path is None and not path == "":
            status, err = storage_manager.delete_file(path, storage_id=storage)
            print("delete: status: %s, err: %s" % (status, err))

    def _on_fs_delete_job(self, job):
        job, path = self._extract_storage_path(job)
        job_manager = self._unicore.get_job_manager()

        print("deleting job: %s" % job)
        if path is None or path == "":
            status, err = job_manager.delete(job=job)
            print("delete: status: %s, err: %s" % (status, err))


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
    #                              unicore                                     #
    ############################################################################

    # no_status_update shuld be set to true if there are multiple successive calls
    # that all would individually update the connection status.
    # This avoids flickering of the icon.
    def _disconnect_unicore(self, no_status_update=False):
        self._logger.info("Disconnecting from registry")
        if not self._unicore is None:
            #TODO currently, a connection is not maintained in pyura
            #self._unicore.disconnected()
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

        idx = self._get_default_registry() \
                if index is None or index < 0 else index
        registry    = self._get_registry_by_index(idx)

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
            wfs = registry[SETTING_KEYS['registry.workflows']]
            if not wfs is None and wfs != "":
                if not self._unicore.set_workflow_base_uri(wfs):
                    self._logger.error("Could not set workflow uri.")
                else:
                    self._logger.info("foo")
            error, status = self._unicore.connect()

            if error == UnicoreErrorCodes.NO_ERROR: #TODO check if _unicore.is_connected.
                success = True
                self._logger.info("Connected.")
                print("#############\n#############")
                #self._test_wf_submit()

                """
                job_manager = reg.get_job_manager()
                if (job_manager is None):
                    logger.error("job tests: did NOT get job manager")
                else:
                    logger.info("job tests: got job manager")

                    job_manager.update_list()
                    jobs = job_manager.get_list()
                    logger.info("job tests: got %d jobs." % len(jobs))
                    ## init all objects. Do not output anything, this will spam the log anyway...
                    # for job in jobs:
                    #    try:
                    #        a = job.get_owner_dn()
                    #    except:
                    #        # This should not happen when the REST API Bugs are fixed
                    #        pass
                    logger.info("job tests: job infos:")
                    for job in jobs:
                        owner = None
                        try:
                            owner = job.get_owner_dn()
                        except:
                            # This should not happen when the REST API Bugs are fixed
                            pass
                        logger.info("   job %s from %s" % (str(job.get_id()), owner))

                    err, newjob = job_manager.create('/bin/echo',
                                                     arguments=['hallo, welt', '$FOO'],
                                                     environment=["FOO=bar"])
                    """
            else:
                self._logger.error("Failed to connect to registry: %s, %s" % \
                            (str(status), str(error))
                        )
                self._view_manager.show_error(
                        "Failed to connect to registry '%s'\n"\
                        "Connection returned status %d" % \
                        (registry[SETTING_KEYS['registry.name']], status)
                    )
        else:
            raise RuntimeError("Registry must be disconnected first.")

        if not no_status_update:
            if success:
                self._set_unicore_connected()
            else:
                self._set_unicore_disconnected()
        return success

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
        job_manager = self._unicore.get_job_manager()
        imports = JobManager.Imports()
        storage_manager = self._unicore.get_storage_manager()
        execfile = os.path.join(wano_dir,"submit_command.sh")
        for filename in filewalker(wano_dir):
            relpath = os.path.relpath(filename,wano_dir)
            imports.add_import(filename,relpath)

        contents = ""
        with open(execfile) as com:
            contents = com.readline()

        splitcont = shlex.split(contents)

        com = splitcont[0]
        arguments = splitcont[1:]

        err, newjob = job_manager.create(com,
                                         arguments=arguments,
                                         imports = imports,
                                         environment=[])

        job_manager.upload_imports(newjob,storage_manager)
        wd = newjob.get_working_dir()
        job_manager.start(newjob)

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
        query_str = "%s.%d" % (SETTING_KEYS['registries'], index)
        return self.__settings.get_value(query_str)

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
        self._view_manager.download_file_to.connect(self._on_fs_download)
        self._view_manager.upload_file.connect(self._on_fs_upload)
        self._view_manager.delete_job.connect(self._on_fs_delete_job)
        self._view_manager.delete_file.connect(self._on_fs_delete_file)


    def __init__(self, settings):
        super(WFEditorApplication, self).__init__()
        self.__settings     = settings

        self._logger        = logging.getLogger('WFELOG')
        self._view_manager  = WFViewManager()
        self._unicore       = None # TODO pyura API
        # TODO model
        self.wanos = []

        UnicoreAPI.init()

        self._connect_signals()

        self.__start()
        self._logger.info("Logging Tab Enabled Version: " + get_git_revision())

