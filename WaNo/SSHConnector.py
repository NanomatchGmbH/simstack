from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import logging
import socket
import threading
import shlex
import os
from enum import Enum
from os.path import dirname
from pprint import pprint

import paramiko
from lxml import etree

from zmq.error import Again

from Qt.QtCore import QThread, Qt
from Qt.QtCore import Slot, Signal, QObject

from SimStackServer.ClusterManager import ClusterManager
from SimStackServer.MessageTypes import ErrorCodes

from WaNo.lib.FileSystemTree import filewalker
from WaNo.lib.CallableQThread import CallableQThread
from WaNo.lib.TPCThread import TPCThread
from WaNo.lib.BetterThreadPoolExecutor import BetterThreadPoolExecutor

from WaNo.UnicoreState import UnicoreDataTransferStates
from WaNo.UnicoreState import UnicoreDataTransferDirection as Direction
from WaNo.UnicoreHelpers import extract_storage_path
from functools import wraps

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
    UPDATE_RESOURCES 
    """,
    module=__name__
)

"""
Error codes:

This extends the list of Error Codes provided by pyura with some specific
SSHConnector error codes.

.. note: The order is not guaranteed to be equal in both enum lists.
    You should not try to compare elements from one list to the other.
    Only the elements copied from the UnicoreErrorCodes list can be found with
    the same value which allows easy convertion in this direction.

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
    [e.name for e in ErrorCodes] + [
            "AUTH_SETUP_FAILED",
            "REGISTRY_NOT_CONNECTED",
            "JOB_DELETE_FAILED",
            "FILE_DELETE_FAILED",
        ],
    module=__name__
)



def eagain_catcher(f):
    @wraps(f)
    def wrapper(self, *args, **kwds):
        try:
            return f(self, *args, **kwds)
        except Again as e:
            from WaNo.view.WFViewManager import WFViewManager
            message = "Connection Error, please try reconnecting Client."
            WFViewManager.show_error(message)
        except socket.timeout as e:
            from WaNo.view.WFViewManager import WFViewManager
            message = "Caught connection exception %s: SSH socket timed out. Please try reconnecting Client." % (e)
            WFViewManager.show_error(message)
        except OSError as e:
            from WaNo.view.WFViewManager import WFViewManager
            #print(type(e))
            message = "Caught connection exception %s: %s. Try reconnecting Client."%(type(e),e)
            WFViewManager.show_error(message)
    return wrapper

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
            if isinstance(callback[1], tuple):
                args = callback[1] + args
            else:
                args = (callback[1],) + args
            kwargs = callback[2]

        cb_function(*args, **kwargs)


    @TPCThread._from_other_thread
    def connect(self, callback, username, password, base_uri, con_settings):
        print("Not used anymore")
        #self._exec_callback(callback, base_uri, err, status)

    @TPCThread._from_other_thread
    def run_workflow_job(self, submitname, dir_to_upload, xml, error_callback):
        # NOTE: error_callback already contains args (base_uri and operation)
        wf_manager = self.registry.get_workflow_manager()
        storage_manager = self.registry.get_storage_manager()

        status, err, error_message, storage = storage_manager.create(name=submitname)
        if (err != ErrorCodes.NO_ERROR or not status in range(200, 300)):
            self._exec_callback(error_callback, err, error_message)
            return

        try:
            storage_id = storage[1].get_id()
        except:
            storage_id = storage.get_id()
        

        for filename in filewalker(dir_to_upload):
            cp = os.path.commonprefix([dir_to_upload, filename])
            relpath = os.path.relpath(filename, cp)
            print("Uploading '%s'..." % filename)
            storage_manager.upload_file(filename, storage_id=storage_id, remote_filename=relpath)
            #imports.add_import(filename,relpath)

        storage_uri = storage_manager.get_base_uri()
        status, err, error_message, wf = wf_manager.create(storage_id, submitname)
        if (err != ErrorCodes.NO_ERROR or not status in range(200, 300)):
            self._exec_callback(error_callback, err, error_message)
            return

        print("err: %s\nstatus: %s\nwf: %s" % (str(err), str(status), str(wf)))

        workflow_id = wf.split("/")[-1]

        storage_management_uri = storage_manager.get_storage_management_uri()

        xmlstring = etree.tostring(xml,pretty_print=False).decode("utf-8").replace("${WORKFLOW_ID}",workflow_id)
        xmlstring = xmlstring.replace("${STORAGE_ID}","%s%s"%(storage_management_uri,storage_id))

        #with open("wf.xml",'w') as wfo:
        #    wfo.write(xmlstring)

        print("err: %s, status: %s, wf_manager: %s" % (err, status, wf))
        #### TIMO HERE
        wf_manager.run(wf.split('/')[-1], xmlstring)

    @TPCThread._from_other_thread
    def update_resources(self, callback, base_uri):
        self._logger.debug("Querying resources.")
        site_manager = self.registry.get_site_manager()
        site_manager.update_list()
        resources = site_manager.get_selected().get_resources()
        self._exec_callback(callback, base_uri, resources)

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
        if wf == None:
            #this is most probably a deletion and then update, don't do anything
            return
        wf.update()

        job_manager = self.registry.get_job_manager()
        job_manager.update_list()

        jobs = [job_manager.get_by_id(jobid) for jobid in wf.get_jobs()]
        print("jobs for wf: %s." % jobs)
        files = []
        for job in jobs:
            if job != None:
                files.append({
                    'id': job.get_id(),
                    'name': job.get_name(),
                    'type': 'j',
                    'path': job.get_working_dir(),
                    'status': job.get_status()
                })
        if len(files) == 0:
            print("No files found in workflow")

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
#        print("\t%6.2f (%6.2f / %6.2f)\t%s" % (progress / total * 100., progress,
#            total, uri))
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
        if not self._callback[0] is None:
            self._callback[0](*self._callback[1], **self._callback[2])

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

    def __init__(self, registry, transfer_state, callback=(None, (), {})):
        self._registry  = registry
        self._state     = transfer_state
        self._future    = None
        self._canceled  = False
        self._total     = 0
        self._callback  = callback

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

    def __init__(self, registry, transfer_state, callback):
        super(UnicoreDownload, self).__init__(registry, transfer_state, callback)

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

    def __init__(self, registry, transfer_state, callback):
        super(UnicoreUpload, self).__init__(registry, transfer_state, callback)


class SSHConnector(CallableQThread):
    error = Signal(str, int, int, str, name="SSHError")

    def _emit_error(self, base_uri, operation, error, message=None):
        if message is None:
            message = ""
        self.error.emit(base_uri, operation.value, error.value, message)

   
    @CallableQThread.callback
    def cb_worker_exit(self, base_uri):
        pass

    @staticmethod
    def create_basic_args(base_uri):
        return {'args': (base_uri,), 'kwargs': {}}

    @staticmethod
    def create_basic_path_args(base_uri, path):
        data = SSHConnector.create_basic_args(base_uri)
        data['args'] += (path,)
        return data

    @staticmethod
    def create_single_job_args(base_uri, wano_dir, name):
        data = SSHConnector.create_basic_args(base_uri)
        data['args'] += (wano_dir, name)
        return data

    @staticmethod
    def create_workflow_job_args(base_uri, submitname, dir_to_upload, xml):
        data = SSHConnector.create_basic_args(base_uri)
        data['args'] += (submitname, dir_to_upload, xml)
        return data

    @staticmethod
    def create_update_resources_args(base_uri):
        return SSHConnector.create_basic_args(base_uri)

    @staticmethod
    def create_update_job_list_args(base_uri):
        return SSHConnector.create_basic_args(base_uri)

    @staticmethod
    def create_update_workflow_list_args(base_uri):
        return SSHConnector.create_basic_args(base_uri)

    @staticmethod
    def create_update_workflow_job_list_args(base_uri, wfid):
        return SSHConnector.create_basic_path_args(base_uri, wfid)

    @staticmethod
    def create_update_dir_list_args(base_uri, path):
        return SSHConnector.create_basic_path_args(base_uri, path)

    @staticmethod
    def create_delete_file_args(base_uri, filename):
        return SSHConnector.create_basic_path_args(base_uri, filename)

    @staticmethod
    def create_delete_job_args(base_uri, job):
        return SSHConnector.create_basic_path_args(base_uri, job)

    @staticmethod
    def create_abort_job_args(base_uri, job):
        return SSHConnector.create_basic_path_args(base_uri, job)

    @staticmethod
    def create_delete_workflow_args(base_uri, workflow):
        return SSHConnector.create_basic_path_args(base_uri, workflow)

    @staticmethod
    def create_abort_workflow_args(base_uri, workflow):
        return SSHConnector.create_basic_path_args(base_uri, workflow)

    @staticmethod
    def create_data_transfer_args(base_uri, from_path, to_path):
        data = SSHConnector.create_basic_args(base_uri)
        data['args'] += (from_path, to_path)
        return data

    def start_server(self, registry, callback=(None, (), {})):
        cm = self._get_cm(registry)
        cm: ClusterManager
        pythonproc = registry["software_directory"] + '/V2/local_anaconda/bin/python'
        serverproc = registry["software_directory"] + '/V2/SimStackServer/SimStackServer.py'
        if not cm.exists(pythonproc):
            raise FileNotFoundError("%s pythonproc was not found. Please check, whether the software directory in Configuration->Servers is correct and postinstall.sh was run"%pythonproc)
        if not cm.exists(serverproc):
            raise FileNotFoundError("%s serverproc was not found. Please check, whether the software directory in Configuration->Servers is correct and the file exists" % serverproc)

        command = "%s %s"%(pythonproc, serverproc)
        #print(command)
        cm.connect_zmq_tunnel(command)
        return ErrorCodes.NO_ERROR

    @eagain_catcher
    def connect_registry(self, registry, callback=(None, (), {})):
        name = registry["name"]
        error = ErrorCodes.NO_ERROR
        statusmessage = ""

        #print(registry)
        if not "port" in registry:
            registry["port"] = 22

        if not name in self._clustermanagers:

            cm = ClusterManager(url = registry["baseURI"],
                                               port = registry["port"],
                                               calculation_basepath=registry["calculation_basepath"],
                                               user=registry["username"],
                                               queueing_system=registry["queueing_system"]
            )
            self._clustermanagers[name] = cm
        else:
            cm = self._clustermanagers[name]
        if not cm.is_connected():
            try:
                cm.connect()
                error = ErrorCodes.NO_ERROR
                statusmessage = "Connected."
                returncode_serverstart = self.start_server(registry)
            except paramiko.ssh_exception.SSHException as e:
                statusmessage = str(e)
                error = ErrorCodes.CONN_ERROR
                del self._clustermanagers[name]
            except Again as e:
                statusmessage = "Connection Error, please try reconnecting Client."
                error = ErrorCodes.CONN_ERROR
                del self._clustermanagers[name]
            except socket.timeout as e:
                statusmessage = "Caught connection exception %s: SSH socket timed out. Please try reconnecting Client." % (e)
                error = ErrorCodes.CONN_ERROR
                del self._clustermanagers[name]
            except FileNotFoundError as e:
                statusmessage = "Did not find file, Exception was:\n%s" % (e)
                error = ErrorCodes.CONN_ERROR
                del self._clustermanagers[name]
            except OSError as e:
                statusmessage = "Caught connection exception %s: SSH socket timed out. Please try reconnecting Client." % (e)
                error = ErrorCodes.CONN_ERROR
                del self._clustermanagers[name]
        else:
            print("Already connected, will not connect again.")
        self._exec_callback(callback, registry["baseURI"], error, statusmessage)

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

    def disconnect_registry(self, registry, callback):
        name = registry["name"]
        error = ErrorCodes.NO_ERROR
        statusmessage = ""
        if name in self._clustermanagers:
            cm = self._clustermanagers[name]
            cm.disconnect()
        self._exec_callback(callback, error, statusmessage)

    def run_single_job(self, base_uri, wano_dir, name):
        worker = self._get_error_or_fail(base_uri)
        if not worker is None:
            worker.run_single_job(
                    wano_dir,
                    name,
                    (self._emit_error, (base_uri, OPERATIONS.RUN_SINGLE_JOB), {}))

    @eagain_catcher
    def run_workflow_job(self, registry, submitname, dir_to_upload, xml, progress_callback = None, callback = None):

        cm = self._get_cm(registry)
        counter = 0


        real_submitname = submitname
        while cm.exists(real_submitname):
            counter+=1
            print("File %s already exists. This is unlikely but possible, when submitting lots of workflows. Trying a different filename." % (real_submitname))
            real_submitname = submitname + "_Nr_%d"%counter

            if counter == 15:
                raise FileExistsError("File %s already exists. Stopping to find a new file. This is highly unlikely. Please report to Nanomatch."%(real_submitname))

        submitname = real_submitname

        for filename in filewalker(dir_to_upload):
            cp = os.path.commonprefix([dir_to_upload, filename])
            relpath = os.path.relpath(filename, cp)
            submitpath = submitname + '/' + "workflow_data" + '/'+ relpath
            print("Uploading '%s' to '%s'" %(filename, submitpath))
            mydir = dirname(submitpath)
            cm.mkdir_p(mydir)
            cm.put_file(filename,submitpath)

        wf_yml_name = real_submitname + "/" + "rendered_workflow.xml"
        with cm.remote_open(wf_yml_name,'wt') as outfile:
            outfile.write(etree.tostring(xml, encoding = "utf8", pretty_print=True).decode()
                          .replace("c9m:","")
                          .replace("${STORAGE}/","")
                          .replace("${SUBMIT_NAME}",real_submitname)
                          .replace("${BASEFOLDER}",cm.get_calculation_basepath() + '/' + submitname)
                          .replace("${QUEUE}", cm.get_queueing_system())
                          )
        cm.submit_wf(wf_yml_name)


    def update_job_list(self, base_uri, callback=(None, (), {})):
        worker = self._get_error_or_fail(base_uri)
        if not worker is None:
            worker.update_job_list(callback, base_uri)

    def update_resources(self, base_uri, callback=(None, (), {})):
        worker = self._get_error_or_fail(base_uri)
        if not worker is None:
            worker.update_resources(callback, base_uri)

    @eagain_catcher
    def update_workflow_list(self, registry, callback=(None, (), {})):
        cm = self._get_cm(registry)
        workflows = cm.get_workflow_list()
        self._exec_callback(callback, registry, workflows)

    @eagain_catcher
    def update_workflow_job_list(self, registry, wfid, callback=(None, (), {})):
        cm = self._get_cm(registry)
        files = cm.get_workflow_job_list(wfid)
        self._exec_callback(callback, registry, wfid, files)

    @eagain_catcher
    def update_dir_list(self, registry, path, callback=(None, (), {})):
        cm = self._get_cm(registry)
        files = cm.list_dir(path)
        self._exec_callback(callback, registry, path, files)

    @eagain_catcher
    def delete_file(self, registry, filename, callback=(None, (), {})):
        cm = self._get_cm(registry)
        if cm.is_directory(filename):
            cm.rmtree(filename)
        else:
            cm.delete_file(filename)
        self._exec_callback(callback, registry, filename, ErrorCodes.NO_ERROR)

    def delete_job(self, base_uri, job, callback=(None, (), {})):
        worker = self._get_error_or_fail(base_uri)
        if not worker is None:
            worker.delete_job(callback, base_uri, job)

    def abort_job(self, base_uri, job, callback=(None, (), {})):
        worker = self._get_error_or_fail(base_uri)
        if not worker is None:
            worker.abort_job(callback, base_uri, job)

    @eagain_catcher
    def delete_workflow(self, registry, workflow_submitname, callback=(None, (), {})):
        cm = self._get_cm(registry)
        cm.delete_wf(workflow_submitname)
        #worker = self._get_error_or_fail(base_uri)
        #if not worker is None:
        #    worker.delete_workflow(callback, base_uri, workflow)

    @eagain_catcher
    def abort_workflow(self, registry, workflow_submitname, callback=(None, (), {})):
        cm = self._get_cm(registry)
        cm.abort_wf(workflow_submitname)
        self.logger.debug("Sending Workflow Abort message for workflows %s"%workflow_submitname)


    def _data_transfer(self, base_uri, localfile, remotefile, direction,
            callback=(None, (), {})):
        """
        Args:
            callback (function) callback that is executed when transfer completes
        """
        if not base_uri in self.workers:
            # TODO emit error
            return

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
                direction.value)
        transfer_state = self.unicore_state.get_data_transfer(
                base_uri, index)

        if (direction == Direction.UPLOAD):
            transfers[index] = UnicoreUpload(registry, transfer_state, callback)
        else:
            transfers[index] = UnicoreDownload(registry, transfer_state, callback)
        transfers[index].submit(executor)

    @eagain_catcher
    def download_file(self, registry, download_files, local_dest, progress_callback = None, callback=(None, (), {})):
        cm = self._get_cm(registry)
        todl = download_files
        if isinstance(download_files, str):
            todl = [download_files]

        for remote_file in todl:
            cm.get_file(remote_file, local_dest, progress_callback)

    def _get_cm(self, registry) -> ClusterManager:
        name = registry["name"]
        if not name in self._clustermanagers:
            raise ConnectionError("Clustermanager %s was not connected."%name)
        return self._clustermanagers[name]

    @eagain_catcher
    def upload_files(self, registry, upload_files, destination, progress_callback = None, callback=(None, (), {})):
        cm = self._get_cm(registry)
        toupload = upload_files
        if isinstance(upload_files, str):
            toupload = [upload_files]

        for local_file in toupload:
            cm.put_file(local_file, destination)

    def unicore_operation(self, operation, data, callback=(None, (), {})):
        ops = OPERATIONS

        if operation == ops.CONNECT_REGISTRY:
            self.connect_registry(data, callback = callback)
        elif operation == ops.DISCONNECT_REGISTRY:
            self.disconnect_registry(data, callback = callback)
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
            self.update_dir_list(*data, callback=callback)
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
        elif operation == ops.UPDATE_RESOURCES:
            self.update_resources(*data['args'], callback=callback)
        else:
            self.logger.error("Got unknown operation: %s" % ops(operation) \
                    if isinstance(operation, int) else str(operation))

    def run(self):
        self.cbReceiver.exec_unicore_callback_operation.connect(
                self.unicore_operation, type=Qt.QueuedConnection)
        self.cbReceiver.exec_unicore_operation.connect(
                self.unicore_operation, type=Qt.QueuedConnection)

        self.logger.debug("Started SSHConnector Thread.")
        self.exec_()


    def _exec_callback(self, callback, *args, **kwargs):
        cb_function = callback

        if isinstance(callback, tuple):
            cb_function = callback[0]
            if isinstance(callback[1], tuple):
                args = callback[1] + args
            else:
                args = (callback[1],) + args
            kwargs = callback[2]

        cb_function(*args, **kwargs)

    def __init__(self, cbReceiver, unicore_state):
        super(SSHConnector, self).__init__()
        self.logger         = logging.getLogger("SSHConnection")
        self.cbReceiver     = cbReceiver
        self._clustermanagers = {}

        self.workers        = {}

        import sys
        loglevel = logging.DEBUG
        self.logger.setLevel(loglevel)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(loglevel)
        self.logger.addHandler(ch)

