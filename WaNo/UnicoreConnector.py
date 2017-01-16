from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import logging
import threading
import shlex
import os
from enum import Enum
from lxml import etree



from PySide.QtCore import QThread, Qt
from PySide.QtCore import Slot, Signal, QObject

from pyura.pyura import UnicoreAPI, HTTPBasicAuthProvider
from pyura.pyura import ErrorCodes as UnicoreErrorCodes
from pyura.pyura import JobManager
from pyura.pyura import ConnectionState as UnicoreConnectionStates

from WaNo.lib.FileSystemTree import filewalker
from WaNo.lib.CallableQThread import CallableQThread
from WaNo.lib.TPCThread import TPCThread
from WaNo.lib.BetterThreadPoolExecutor import BetterThreadPoolExecutor

from WaNo.UnicoreState import UnicoreDataTransferStates
from WaNo.UnicoreState import UnicoreDataTransferDirection as Direction
from WaNo.UnicoreHelpers import extract_storage_path


""" Number of data transfer workers per regisrtry. """
MAX_DT_WORKERS_PER_REGISTRY = 3

_AUTH_TYPES = Enum("AUTH_TYPES",
    """
    HTTP
    """,
    module=__name__
)

OPERATIONS = Enum("OPERATIONS",
    """
    CONNECT_REGISTRY
    DISCONNECT_REGISTRY
    RUN_SINGLE_JOB
    RUN_WORKFLOW_JOB
    UPDATE_JOB_LIST
    UPDATE_WF_LIST
    UPDATE_WF_JOB_LIST
    UPDATE_DIR_LIST
    DELETE_FILE
    DELETE_JOB
    ABORT_JOB
    DELETE_WORKFLOW
    ABORT_WORKFLOW
    DOWNLOAD_FILE
    UPLOAD_FILE
    """,
    module=__name__
)

"""
Error codes:

* NO_ERROR
    No error occurred.
* AUTH_SETUP
    Setup of the selected authentication method failed.
* REGISTRY_NOT_CONNECTED
    The selected registry must be connected before performing this operation.
* JOB_DELETE_FAILED
    The deletion of a job has failed.
* FILE_DELETE_FAILED
    The deletion of a file has failed.
"""
ERROR = Enum("ERROR",
    """
    NO_ERROR
    AUTH_SETUP_FAILED
    REGISTRY_NOT_CONNECTED
    JOB_DELETE_FAILED
    FILE_DELETE_FAILED
    """,
    module=__name__
)



class UnicoreWorker(TPCThread):
    OPERATIONS = Enum("Operations",
            """
            DELETE
            ABORT
            """
            )
    def _exec_callback(self, callback, *args, **kwargs):
        cb_function = callback

        if isinstance(callback, tuple):
            cb_function = callback[0]
            args += callback[1]
            kwargs = callback[2]

        cb_function(*args, **kwargs)


    @TPCThread._from_other_thread
    def connect(self, callback, username, password, base_uri, con_settings):
        import platform
        import ctypes
        if platform.system() == "Linux":
            self._logger.debug("UnicoreWorker Thread ID(connect): %d\t%d" % \
                    (threading.current_thread().ident,
                    ctypes.CDLL('libc.so.6').syscall(186)))

        if not con_settings is None and 'wf_uri' in con_settings:
            print("Setting workflow uri: %s." % con_settings['wf_uri'])
            self.registry.set_workflow_base_uri(con_settings['wf_uri'])

        err, status = self.registry.connect()
        self._logger.debug("Unicore connect returns: %s, %s" % (str(err), str(status)))

        if err == UnicoreErrorCodes.NO_ERROR and status == 200:
            self._state.set_value('state', UnicoreConnectionStates.CONNECTING)

        self._exec_callback(callback, base_uri, err, status)


    @TPCThread._from_other_thread
    def run_single_job(self, wano_dir, name):
        job_manager = self.registry.get_job_manager()
        imports = JobManager.Imports()
        storage_manager = self.registry.get_storage_manager()
        execfile = os.path.join(wano_dir,"submit_command.sh")
        for filename in filewalker(wano_dir):
            relpath = os.path.relpath(filename,wano_dir)
            imports.add_import(filename,relpath)

        contents = ""
        with open(execfile) as com:
            contents = com.read()

        splitcont = shlex.split(contents.strip(" \t\n\r"))

        com = splitcont[0]
        arguments = splitcont[1:]

        err, newjob = job_manager.create(com,
                                         arguments=arguments,
                                         imports = imports,
                                         environment=[],
                                         name=name
                                         )
        #TODO error handling

        job_manager.upload_imports(newjob,storage_manager)
        wd = newjob.get_working_dir()
        job_manager.start(newjob)

    @TPCThread._from_other_thread
    def run_workflow_job(self, submitname, dir_to_upload, xml):
        #TODO error handling
        wf_manager = self.registry.get_workflow_manager()
        storage_manager = self.registry.get_storage_manager()

        storage = storage_manager.create(name=submitname)
        storage_id = storage[1].get_id()

        for filename in filewalker(dir_to_upload):
            cp = os.path.commonprefix([dir_to_upload, filename])
            relpath = os.path.relpath(filename, cp)
            print("Uploading '%s'..." % filename)
            storage_manager.upload_file(filename, storage_id=storage_id, remote_filename=relpath)
            #imports.add_import(filename,relpath)

        storage_uri = storage_manager.get_base_uri()
        err, status, wf = wf_manager.create(storage_id, submitname)
        print("err: %s\nstatus: %s\nwf: %s" % (str(err), str(status), str(wf)))

        workflow_id = wf.split("/")[-1]

        storage_management_uri = storage_manager.get_storage_management_uri()

        xmlstring = etree.tostring(xml,pretty_print=False).decode("utf-8").replace("${WORKFLOW_ID}",workflow_id)
        xmlstring = xmlstring.replace("${STORAGE_ID}","%s%s"%(storage_management_uri,storage_id))

        with open("wf.xml",'w') as wfo:
            wfo.write(xmlstring)

        print("err: %s, status: %s, wf_manager: %s" % (err, status, wf))
        #### TIMO HERE
        wf_manager.run(wf.split('/')[-1], xmlstring)

    @TPCThread._from_other_thread
    def update_job_list(self, callback, base_uri):
        self._logger.debug("Querying jobs from Unicore Registry")
        jobs = []

        job_manager = self.registry.get_job_manager()
        job_manager.update_list()
        jobs = [{
                    'id': s.get_id(),
                    'name': s.get_name(),
                    'type': 'j',
                    'path': s.get_working_dir(),
                    'status': s.get_status()
                } for s in job_manager.get_list()]

        self._exec_callback(callback, base_uri, jobs)

    @TPCThread._from_other_thread
    def update_workflow_list(self, callback, base_uri):
        self._logger.debug("Querying workflows from Unicore Registry")
        workflows = []

        wf_manager = self.registry.get_workflow_manager()
        wf_manager.update_list()
        workflows = [{
                'id': s.get_id(),
                'name': s.get_name(),
                'type': 'w',
                'path': s.get_working_dir(),
                'status': s.get_status()
                } for s in wf_manager.get_list()]

        self._exec_callback(callback, base_uri, workflows)

    @TPCThread._from_other_thread
    def update_workflow_job_list(self, callback, base_uri, wfid):
        wf_manager = self.registry.get_workflow_manager()
        wf = wf_manager.get_by_id(wfid)
        wf.update()

        job_manager = self.registry.get_job_manager()
        job_manager.update_list()

        jobs = [job_manager.get_by_id(jobid) for jobid in wf.get_jobs()]
        print("jobs for wf: %s." % jobs)

        files = [{
                    'id': job.get_id(),
                    'name': job.get_name(),
                    'type': 'j',
                    'path': job.get_working_dir(),
                    'status': job.get_status()
                } for job in jobs]

        #print("jobs:\n\n\n\n%s\n\n\n" % job_manager.get_list())
        print("Got files for wf: %s" % files)

        self._exec_callback(callback, base_uri, wfid, files)

    @TPCThread._from_other_thread
    def list_dir(self, callback, base_uri, path):
        self._logger.debug("Querying %s from Unicore Registry" % path)
        files = []

        storage, qpath = extract_storage_path(path)
        #TODO use job manager?!
        storage_manager = self.registry.get_storage_manager()
        storage_manager.update_list()
        files = storage_manager.get_file_list(storage_id=storage, path=qpath)
        self._exec_callback(callback, base_uri, path, files)

    @TPCThread._from_other_thread
    def delete_file(self, callback, base_uri, filename):
        storage, path = extract_storage_path(filename)
        storage_manager = self.registry.get_storage_manager()

        self._logger.debug("deleting %s:%s" % (storage, path))
        if not path is None and not path == "":
            status, err = storage_manager.delete_file(path, storage_id=storage)
            self._exec_callback(callback, base_uri, status, err)

    def abort_or_delete_job(self, callback, base_uri, job, operation):
        job, path = extract_storage_path(job)
        job_manager = self.registry.get_job_manager()

        if path is None or path == "":
            job_obj = job_manager.get_by_id(job)
            if operation == self.OPERATIONS.DELETE:
                self._logger.debug("deleting job: %s" % job)
                status, err, _unused = job_manager.delete(job=job_obj)
            else:
                self._logger.debug("aborting job: %s" % job)
                status, err, _unused = job_manager.abort(job=job_obj)
            self._exec_callback(callback, base_uri, status, err)

    @TPCThread._from_other_thread
    def delete_job(self, callback, base_uri, job):
        self.abort_or_delete_job(callback, base_uri, job, self.OPERATIONS.DELETE)

    @TPCThread._from_other_thread
    def abort_job(self, callback, base_uri, job):
        self.abort_or_delete_job(callback, base_uri, job, self.OPERATIONS.ABORT)

    def abort_or_delete_workflow(self, callback, base_uri, workflow, operation):
        wf, path = extract_storage_path(workflow)
        print(wf,path)
        wf_manager = self.registry.get_workflow_manager()

        if path is None or path == "":
            wf_obj = wf_manager.get_by_id(wf)
            if operation == self.OPERATIONS.DELETE:
                self._logger.debug("deleting workflow: %s" % workflow)
                status, err, _unused = wf_manager.delete(workflow=wf_obj)
            else:
                self._logger.debug("aborting workflow: %s" % workflow)
                status, err, _unused = wf_manager.abort(workflow=wf_obj)

            self._exec_callback(callback, base_uri, status, err)

    @TPCThread._from_other_thread
    def delete_workflow(self, callback, base_uri, workflow):
        self.abort_or_delete_workflow(callback, base_uri, workflow,
                self.OPERATIONS.DELETE)

    @TPCThread._from_other_thread
    def abort_workflow(self, callback, base_uri, workflow):
        self.abort_or_delete_workflow(callback, base_uri, workflow,
                self.OPERATIONS.ABORT)

                    #TODO remove, debug only
    def start(self):
        super(UnicoreWorker, self).start()
        import platform
        import ctypes
        if platform.system() == "Linux":
            self._logger.debug("UnicoreWorker Thread ID: %d\t%d" % \
                    (threading.current_thread().ident,
                    ctypes.CDLL('libc.so.6').syscall(186)))

    def __init__(self, registry, logger, reg_state):
        super(UnicoreWorker, self).__init__()
        self._logger        = logger
        self.registry       = registry
        self._state         = reg_state

class UnicoreDataTransfer(object):
    def _update_transfer_status(self, uri, localfile, progress, total):
        print("\t%6.2f (%6.2f / %6.2f)\t%s" % (progress / total * 100., progress,
            total, uri))
        self._state.get_writer_instance().set_multiple_values({
                'total': total,
                'progress': progress,
                'state': UnicoreDataTransferStates.RUNNING
            })
        self._total = total

    def run(self):
        raise NotImplementedError("Must be implemented in sub-class.")

    def _done_callback(self, result):
        last_progress = self._state.get_reader_instance().get_value('progress')
        finished = last_progress >= self._total * 0.99
        self._state.get_writer_instance().set_multiple_values({
                'total': self._total,
                'progress': self._total if finished else last_progress,
                'state': UnicoreDataTransferStates.DONE
            })

    def cancel(self):
        # TODO: concurrent.futures.Future.cancel():
        # A future cannot be cancelled if it is running or has already completed.
        #TODO lock!
        if not self._future is None:
            self._future.cancel()
        self._canceled = True

    def submit(self, executor):
        # TODO: make sure, this is started only once. Must be locked
        # TODO: make sure, this job was not cancled.
        self._future = executor.submit(self.run)
        executor.add_done_callback(self._future, self._done_callback)

    def __init__(self, registry, transfer_state):
        self._registry  = registry
        self._state     = transfer_state
        self._future    = None
        self._canceled  = False
        self._total     = 0

class UnicoreDownload(UnicoreDataTransfer):
    def run(self):
        #TODO ensure, that the registry is still connected
        #storage, path = extract_storage_path(from_path)
        storage_manager = self._registry.get_storage_manager()
        source  = None
        dest    = None
        storage = None

        with self._state.get_reader_instance() as status:
            source  = status['source']
            dest    = status['dest']
            storage = status['storage']

        ret_status, err = storage_manager.get_file(
                source,
                dest,
                storage_id=storage,
                callback=self._update_transfer_status)
        print("status: %s, err: %s" % (ret_status, err))

        #TODO handle return values and return them.
        return 0

    def __init__(self, registry, transfer_state):
        super(UnicoreDownload, self).__init__(registry, transfer_state)

class UnicoreUpload(UnicoreDataTransfer):
    def run(self):
        #storage, path = extract_storage_path(self.dest_dir)
        storage_manager = self._registry.get_storage_manager()
        source  = None
        dest    = None
        storage = None

        with self._state.get_reader_instance() as status:
            source  = status['source']
            dest    = status['dest']
            storage = status['storage']

        remote_filepath = os.path.join(
                dest,
                os.path.basename(source))

        print("uploading '%s' to %s:%s" % (
                source,
                storage,
                dest))

        ret_status, err, json = storage_manager.upload_file(
                source,
                remote_filename=remote_filepath,
                storage_id=storage,
                callback=self._update_transfer_status)
        print("status: %s, err: %s, json: %s" % (ret_status, err, json))

        #TODO handle return values and return them.
        return 0

    def __init__(self, registry, transfer_state):
        super(UnicoreUpload, self).__init__(registry, transfer_state)


class UnicoreConnector(CallableQThread):
    error = Signal(str, int, int, name="UnicoreError")

    AUTH_TYPES = _AUTH_TYPES
    def _emit_error(self, base_uri, operation, error):
        self.error.emit(base_uri, operation.value, error.value)

    def get_authprovider(self, auth_type, username, password):
        auth_provider = None

        if auth_type == UnicoreConnector.AUTH_TYPES.HTTP:
            auth_provider = HTTPBasicAuthProvider(username, password)

        return auth_provider

    @CallableQThread.callback
    def cb_worker_exit(self, base_uri):
        pass

    @staticmethod
    def create_connect_args(username, password, base_uri,
            auth_type=_AUTH_TYPES.HTTP, wf_uri=None):
        return {'args': (username, password, base_uri),
                'kwargs': {
                        'con_settings': {
                                'auth_type': auth_type,
                                'wf_uri': wf_uri
                            }
                    }
            }

    @staticmethod
    def create_basic_args(base_uri):
        return {'args': (base_uri,), 'kwargs': {}}

    @staticmethod
    def create_basic_path_args(base_uri, path):
        data = UnicoreConnector.create_basic_args(base_uri)
        data['args'] += (path,)
        return data

    @staticmethod
    def create_single_job_args(base_uri, wano_dir, name):
        data = UnicoreConnector.create_basic_args(base_uri)
        data['args'] += (wano_dir, name)
        return data

    @staticmethod
    def create_workflow_job_args(base_uri, submitname, dir_to_upload, xml):
        data = UnicoreConnector.create_basic_args(base_uri)
        data['args'] += (submitname, dir_to_upload, xml)
        return data

    @staticmethod
    def create_update_job_list_args(base_uri):
        return UnicoreConnector.create_basic_args(base_uri)

    @staticmethod
    def create_update_workflow_list_args(base_uri):
        return UnicoreConnector.create_basic_args(base_uri)

    @staticmethod
    def create_update_workflow_job_list_args(base_uri, wfid):
        return UnicoreConnector.create_basic_path_args(base_uri, wfid)

    @staticmethod
    def create_update_dir_list_args(base_uri, path):
        return UnicoreConnector.create_basic_path_args(base_uri, path)

    @staticmethod
    def create_delete_file_args(base_uri, filename):
        return UnicoreConnector.create_basic_path_args(base_uri, filename)

    @staticmethod
    def create_delete_job_args(base_uri, job):
        return UnicoreConnector.create_basic_path_args(base_uri, job)

    @staticmethod
    def create_abort_job_args(base_uri, job):
        return UnicoreConnector.create_basic_path_args(base_uri, job)

    @staticmethod
    def create_delete_workflow_args(base_uri, workflow):
        return UnicoreConnector.create_basic_path_args(base_uri, workflow)

    @staticmethod
    def create_abort_workflow_args(base_uri, workflow):
        return UnicoreConnector.create_basic_path_args(base_uri, workflow)

    @staticmethod
    def create_data_transfer_args(base_uri, from_path, to_path):
        data = UnicoreConnector.create_basic_args(base_uri)
        data['args'] += (from_path, to_path)
        return data



    def connect_registry(self, username, password, base_uri,
            callback=(None, (), {}), con_settings=None):
        # TODO what if con_settings is None?

        #TODO debug only
        import platform
        import ctypes
        if platform.system() == "Linux":
            self.logger.debug("Unicore Thread ID (slot): %d\t%d\t%s" % \
                    (threading.current_thread().ident,
                    ctypes.CDLL('libc.so.6').syscall(186),
                    str(QThread.currentThreadId())))
        ##### END TODO

        auth_provider = self.get_authprovider(
                con_settings['auth_type'], username, password)
        if auth_provider is None:
            self.logger.error("Could not get auth provider.")
            self._emit_error(
                    base_uri,
                    OPERATIONS.CONNECT_REGISTRY,
                    ERROR.AUTH_SETUP)
            return

        worker = None
        registry = None
        if base_uri in self.workers:
            #TODO worker might has died. We should check this and recreate it.
            worker = self.workers[base_uri]['worker']
            #TODO add get_registry method to UnicoreAPI, since we might want to
            # update the auth provider or something...
            registry = self.workers[base_uri]['registry']
            reg_state = self.unicore_state.get_registry_state(base_uri)
        else:
            registry = UnicoreAPI.add_registry(base_uri, auth_provider)

            reg_state = self.unicore_state.add_registry(
                    base_uri,
                    username,
                    UnicoreConnectionStates.CONNECTING)

            worker = UnicoreWorker(registry, self.logger, reg_state)
            worker.set_exit_callback(self.cb_worker_exit, base_uri)

            worker.start()
            self.logger.debug("Started worker thread for '%s'." % base_uri)

        self.workers[base_uri] = {
                'worker':                   worker,
                'registry':                 registry,
                'data_transfers':           {},
                'data_transfer_executor':   BetterThreadPoolExecutor(
                    max_workers=MAX_DT_WORKERS_PER_REGISTRY)
                }
        reg_state.set_value('state', UnicoreConnectionStates.CONNECTING)

        self.logger.debug("Handing over to worker (%s)..." % str(worker))
        worker.connect(callback, username, password,
                base_uri, con_settings=con_settings)

    def _get_error_or_fail(self, base_uri):
        worker = None
        if base_uri in self.workers:
            worker = self.workers[base_uri]['worker']
        else:
            self._emit_error(
                    base_uri,
                    OPERATIONS.RUN_SINGLE_JOB,
                    ERROR.REGISTRY_NOT_CONNECTED)
        return worker


    def disconnect_registry(self):
        #TODO
        pass

    def run_single_job(self, base_uri, wano_dir, name):
        worker = self._get_error_or_fail(base_uri)
        if not worker is None:
            worker.run_single_job(wano_dir, name)

    def run_workflow_job(self, base_uri, submitname, dir_to_upload, xml):
        worker = self._get_error_or_fail(base_uri)
        if not worker is None:
            worker.run_workflow_job(submitname, dir_to_upload, xml)

    def update_job_list(self, base_uri, callback=(None, (), {})):
        worker = self._get_error_or_fail(base_uri)
        if not worker is None:
            worker.update_job_list(callback, base_uri)

    def update_workflow_list(self, base_uri, callback=(None, (), {})):
        worker = self._get_error_or_fail(base_uri)
        if not worker is None:
            worker.update_workflow_list(callback, base_uri)

    def update_workflow_job_list(self, base_uri, wfid, callback=(None, (), {})):
        worker = self._get_error_or_fail(base_uri)
        if not worker is None:
            worker.update_workflow_job_list(callback, base_uri, wfid)

    def update_dir_list(self, base_uri, path, callback=(None, (), {})):
        worker = self._get_error_or_fail(base_uri)
        if not worker is None:
            worker.list_dir(callback, base_uri, path)

    def delete_file(self, base_uri, filename, callback=(None, (), {})):
        worker = self._get_error_or_fail(base_uri)
        if not worker is None:
            worker.delete_file(callback, base_uri, filename)

    def delete_job(self, base_uri, job, callback=(None, (), {})):
        worker = self._get_error_or_fail(base_uri)
        if not worker is None:
            worker.delete_job(callback, base_uri, job)

    def abort_job(self, base_uri, job, callback=(None, (), {})):
        worker = self._get_error_or_fail(base_uri)
        if not worker is None:
            worker.abort_job(callback, base_uri, job)

    def delete_workflow(self, base_uri, workflow, callback=(None, (), {})):
        worker = self._get_error_or_fail(base_uri)
        if not worker is None:
            worker.delete_workflow(callback, base_uri, workflow)

    def abort_workflow(self, base_uri, workflow, callback=(None, (), {})):
        worker = self._get_error_or_fail(base_uri)
        if not worker is None:
            worker.abort_workflow(callback, base_uri, workflow)

    def _data_transfer(self, base_uri, localfile, remotefile, direction,
            callback=(None, (), {})):
        if not base_uri in self.workers:
            # TODO emit error
            return

        #TODO treat callback.... required?

        storage, remote_path = extract_storage_path(remotefile)
        registry    = self.workers[base_uri]['registry']
        transfers   = self.workers[base_uri]['data_transfers']
        executor    = self.workers[base_uri]['data_transfer_executor']

        source = localfile if (direction == Direction.UPLOAD) else remote_path
        destination = remote_path if (direction == Direction.UPLOAD) else localfile

        index = self.unicore_state.add_data_transfer(
                base_uri,
                source,
                destination,
                storage,
                direction)
        transfer_state = self.unicore_state.get_data_transfer(
                base_uri, index)

        if (direction == Direction.UPLOAD):
            transfers[index] = UnicoreUpload(registry, transfer_state)
        else:
            transfers[index] = UnicoreDownload(registry, transfer_state)
        transfers[index].submit(executor)


    def download_file(self, base_uri, download, local_dest, callback=(None, (), {})):
        self._data_transfer(
                base_uri, local_dest, download, Direction.DOWNLOAD, callback)

    def upload_file(self, base_uri, upload_file, destination, callback=(None, (), {})):
        self._data_transfer(
                base_uri, upload_file, destination, Direction.UPLOAD, callback)

    def unicore_operation(self, operation, data, callback=(None, (), {})):
        ops = OPERATIONS

        if operation == ops.CONNECT_REGISTRY:
            data['kwargs']['callback'] = callback
            self.connect_registry(*data['args'], **data['kwargs'])
        elif operation == ops.DISCONNECT_REGISTRY:
            pass #TODO
        elif operation == ops.RUN_SINGLE_JOB:
            self.run_single_job(*data['args'])
        elif operation == ops.RUN_WORKFLOW_JOB:
            self.run_workflow_job(*data['args'])
        elif operation == ops.UPDATE_JOB_LIST:
            self.update_job_list(*data['args'], callback=callback)
        elif operation == ops.UPDATE_WF_LIST:
            self.update_workflow_list(*data['args'], callback=callback)
        elif operation == ops.UPDATE_WF_JOB_LIST:
            self.update_workflow_job_list(*data['args'], callback=callback)
        elif operation == ops.UPDATE_DIR_LIST:
            self.update_dir_list(*data['args'], callback=callback)
        elif operation == ops.DELETE_FILE:
            self.delete_file(*data['args'], callback=callback)
        elif operation == ops.DELETE_JOB:
            self.delete_job(*data['args'], callback=callback)
        elif operation == ops.ABORT_JOB:
            self.abort_job(*data['args'], callback=callback)
        elif operation == ops.DELETE_WORKFLOW:
            self.delete_workflow(*data['args'], callback=callback)
        elif operation == ops.ABORT_WORKFLOW:
            self.abort_workflow(*data['args'], callback=callback)
        elif operation == ops.DOWNLOAD_FILE:
            self.download_file(*data['args'], callback=callback)
        elif operation == ops.UPLOAD_FILE:
            self.upload_file(*data['args'], callback=callback)
        else:
            self.logger.error("Got unknown operation: %s" % ops(operation) \
                    if isinstance(operation, int) else str(operation))

    def run(self):
        #super(UnicoreConnector, self).run()
        #TODO debug only
        import platform
        import ctypes
        if platform.system() == "Linux":
            self.logger.debug("Unicore Thread ID: %d\t%d\t%s" % \
                    (threading.current_thread().ident,
                    ctypes.CDLL('libc.so.6').syscall(186),
                    str(QThread.currentThreadId())))
        ##### END TODO

        self.cbReceiver.exec_unicore_callback_operation.connect(
                self.unicore_operation, type=Qt.QueuedConnection)
        self.cbReceiver.exec_unicore_operation.connect(
                self.unicore_operation, type=Qt.QueuedConnection)

        self.logger.debug("Started UnicoreConnector Thread.")
        self.exec_()


    def __init__(self, cbReceiver, unicore_state):
        super(UnicoreConnector, self).__init__()
        self.registry       = None
        self.cbReceiver     = cbReceiver
        self.unicore_state  = unicore_state
        self.logger         = logging.getLogger("Unicore")
        self.workers        = {}

        import sys
        loglevel = logging.DEBUG
        self.logger.setLevel(loglevel)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(loglevel)
        self.logger.addHandler(ch)

