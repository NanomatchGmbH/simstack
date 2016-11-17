from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import logging
import threading
import shlex
import os
from enum import Enum


from PySide.QtCore import QThread, Qt
from PySide.QtCore import Slot, Signal, QObject

from WaNo.lib.pyura.pyura import UnicoreAPI, HTTPBasicAuthProvider
from WaNo.lib.pyura.pyura import ErrorCodes as UnicoreErrorCodes
from WaNo.lib.pyura.pyura import JobManager

from WaNo.lib.FileSystemTree import filewalker
from WaNo.lib.CallableQThread import CallableQThread
from WaNo.lib.TPCThread import TPCThread
from WaNo.lib.BetterThreadPoolExecutor import BetterThreadPoolExecutor

from WaNo.UnicoreState import UnicoreDataTransferStates


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
    UPDATE_JOB_LIST
    UPDATE_WF_LIST
    UPDATE_DIR_LIST
    DELETE_FILE
    DELETE_JOB
    DOWNLOAD_FILE
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
    @staticmethod
    def _extract_storage_path(path):
        storage = None
        querypath = ''
        splitted = [p for p in path.split('/') if not p is None and p != ""]

        if len(splitted) >= 1:
            storage   = splitted[0]
        if len(splitted) >= 2:
            querypath = '/'.join(splitted[1:]) if len(splitted) > 1 else ''

        return (storage, querypath)


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

        err, status = self.registry.connect()
        self._logger.debug("Unicore connect returns: %s, %s" % (str(err), str(status)))

        self._exec_callback(callback, base_uri, err, status)


    @TPCThread._from_other_thread
    def run_single_job(self, wano_dir):
        job_manager = self.registry.get_job_manager()
        imports = JobManager.Imports()
        storage_manager = self.registry.get_storage_manager()
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
        #TODO error handling

        job_manager.upload_imports(newjob,storage_manager)
        wd = newjob.get_working_dir()
        job_manager.start(newjob)

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
                    'path': s.get_working_dir()
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
                'path': s.get_working_dir()
                } for s in wf_manager.get_list()]

        self._exec_callback(callback, base_uri, workflows)

    @TPCThread._from_other_thread
    def list_dir(self, callback, base_uri, path):
        self._logger.debug("Querying %s from Unicore Registry" % path)
        files = []

        storage, qpath = UnicoreWorker._extract_storage_path(path)
        #TODO use job manager?!
        storage_manager = self.registry.get_storage_manager()
        storage_manager.update_list()
        files = storage_manager.get_file_list(storage_id=storage, path=qpath)
        self._exec_callback(callback, base_uri, path, files)

    @TPCThread._from_other_thread
    def delete_file(self, callback, base_uri, filename):
        storage, path = UnicoreWorker._extract_storage_path(filename)
        storage_manager = self.registry.get_storage_manager()

        self._logger.debug("deleting %s:%s" % (storage, path))
        if not path is None and not path == "":
            status, err = storage_manager.delete_file(path, storage_id=storage)
            self._exec_callback(callback, base_uri, status, err)

    @TPCThread._from_other_thread
    def delete_job(self, callback, base_uri, job):
        job, path = UnicoreWorker._extract_storage_path(job)
        job_manager = self.registry.get_job_manager()

        self._logger.debug("deleting job: %s" % job)
        if path is None or path == "":
            status, err = job_manager.delete(job=job)
            self._exec_callback(callback, base_uri, status, err)


       #TODO remove, debug only
    def start(self):
        super(UnicoreWorker, self).start()
        import platform
        import ctypes
        if platform.system() == "Linux":
            self._logger.debug("UnicoreWorker Thread ID: %d\t%d" % \
                    (threading.current_thread().ident,
                    ctypes.CDLL('libc.so.6').syscall(186)))

    def __init__(self, registry, logger):
        super(UnicoreWorker, self).__init__()
        self._logger        = logger
        self.registry       = registry

class UnicoreUpload(threading.Thread):
    def run(self):
        #storage, path = UnicoreWorker._extract_storage_path(self.dest_dir)

        storage_manager = self._registry.get_storage_manager()
        with self._status.get_reader_instance() as status:
            path = status['dest']
            local_file = status['source']
            storage = status['storage']
            remote_filepath = os.path.join(path, os.path.basename(local_file))

            print("uploading '%s' to %s:%s" % (local_file, storage, path))
            ret_status, err, json = storage_manager.upload_file(
                    local_file,
                    remote_filename=remote_filepath,
                    storage_id=storage,
                    callback=self.__on_upload_update)
            print("status: %s, err: %s, json: %s" % (ret_status, err, json))

    def __init__(self, registry, transfer, transfer_status):
        super(UnicoreUpload, self).__init__(self, registry, transfer, transfer_status)

class UnicoreDataTransfer:
    def _update_transfer_status(self, uri, localfile, progress, total):
        print("\t%6.2f (%6.2f / %6.2f)\t%s" % (progress / total * 100., progress,
            total, uri))
        self._status.set_multiple_values({
                'total': total,
                'progress': progress,
                'state': UnicoreDataTransferStates.RUNNING
            })
        self._total = total

    def run(self):
        raise NotImplementedError("Must be implemented in sub-class.")

    def _done_callback(self, result):
        last_progress = self._status.get_value('progress')
        finished = last_progress >= total * 0.99
        self._status.set_multiple_values({
                'total': total,
                'progress': total if finished else last_progress,
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

    def __init__(self, registry, transfer, transfer_status):
        self._registry  = registry
        self._transfer  = transfer
        self._status    = status
        self._future    = None
        self._canceled  = False
        self._total     = 0

class UnicoreDownload(UnicoreDataTransfer):
    def run(self):
        #TODO ensure, that the registry is still connected
        #storage, path = UnicoreWorker._extract_storage_path(from_path)
        storage_manager = self._registry.get_storage_manager()

        with self._status.get_reader_instance() as status:
            ret_status, err = storage_manager.get_file(
                    status['source'],
                    status['dest'],
                    storage_id=status['storage'],
                    callback=self._update_transfer_status)
        print("status: %s, err: %s" % (ret_status, err))

        #TODO handle return values and return them.
        return 0

    def __init__(self, registry, transfer, transfer_status):
        super(UnicoreDownload, self).__init__(self, registry, transfer, transfer_status)

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

    def _set_connection_state(self, state):
        self.unicore_state.set_value(UnicoreStateValues.CONNECTION, state)

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
    def create_single_job_args(base_uri, wano_dir):
        data = UnicoreConnector.create_basic_args(base_uri)
        data['args'] += (wano_dir,)
        return data

    @staticmethod
    def create_update_job_list_args(base_uri):
        return UnicoreConnector.create_basic_args(base_uri)

    @staticmethod
    def create_update_workflow_list_args(base_uri):
        return UnicoreConnector.create_basic_args(base_uri)

    @staticmethod
    def create_update_dir_list_args(base_uri, path):
        return UnicoreConnector.create_single_job_args(base_uri, path)

    @staticmethod
    def create_delete_file_args(base_uri, filename):
        return UnicoreConnector.create_single_job_args(base_uri, filename)

    @staticmethod
    def create_delete_job_args(base_uri, job):
        return UnicoreConnector.create_single_job_args(base_uri, job)



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
        else:
            registry = UnicoreAPI.add_registry(base_uri, auth_provider)

            worker = UnicoreWorker(registry, self.logger)
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

        self.logger.debug("Handing over to worker (%s)..." % str(worker))
        worker.connect(callback, username, password,
                base_uri, con_settings=None)

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

    def run_single_job(self, base_uri, wano_dir):
        worker = self._get_error_or_fail(base_uri)
        if not worker is None:
            worker.run_single_job(wano_dir)

    def update_job_list(self, base_uri, callback=(None, (), {})):
        worker = self._get_error_or_fail(base_uri)
        if not worker is None:
            worker.update_job_list(callback, base_uri)

    def update_workflow_list(self, base_uri, callback=(None, (), {})):
        worker = self._get_error_or_fail(base_uri)
        if not worker is None:
            worker.update_workflow_list(callback, base_uri)

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

    def download_file(self, base_uri, download, local_dest, storage, callback=(None, (), {})):
        if not base_uri in self.workers:
            # TODO emit error
            return

        #TODO treat callback.... required?

        registry    = self.workers[base_uri]['registry']
        transfers   = self.workers[base_uri]['data_transfers']
        executor    = self.workers[base_uri]['data_transfer_executor']

        index = self._unicore_status.add_data_transfer(
                base_uri,
                download,
                local_dest,
                storage)
        transfer_status = self._unicore_status.get_data_transfer(
                base_uri, index)

        transfers[index] = UnicoreDownload(registry, transfer, transfer_status)
        transfers[index].submit(executor)

    def unicore_operation(self, operation, data, callback=(None, (), {})):
        ops = OPERATIONS

        if operation == ops.CONNECT_REGISTRY:
            #data['kwargs']['callback'] = callback
            self.connect_registry(*data['args'], **data['kwargs'],
                    callback=callback)
        elif operation == ops.DISCONNECT_REGISTRY:
            pass #TODO
        elif operation == ops.RUN_SINGLE_JOB:
            self.run_single_job(*data['args'])
        elif operation == ops.UPDATE_JOB_LIST:
            self.update_job_list(*data['args'], callback=callback)
        elif operation == ops.UPDATE_WF_LIST:
            self.update_workflow_list(*data['args'], callback=callback)
        elif operation == ops.UPDATE_DIR_LIST:
            self.update_dir_list(*data['args'], callback=callback)
        elif operation == ops.DELETE_FILE:
            self.delete_file(*data['args'], callback=callback)
        elif operation == ops.DELETE_JOB:
            self.delete_job(*data['args'], callback=callback)
        elif operation == ops.DOWNLOAD_FILE:
            self.download_file(*data['args'], callback=callback)
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

