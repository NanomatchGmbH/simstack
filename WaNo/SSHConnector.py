from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import logging
import socket
import threading
import shlex
import os
from io import StringIO
import traceback
from enum import Enum
from os.path import dirname, join
from pprint import pprint

import paramiko

from lxml import etree
from paramiko import BadHostKeyException

from zmq.error import Again

from Qt.QtCore import QThread, Qt
from Qt.QtCore import Slot, Signal, QObject
from Qt.QtWidgets import QMessageBox

from SimStackServer.ClusterManager import ClusterManager
from SimStackServer.MessageTypes import ErrorCodes
from SimStackServer.Settings.ClusterSettingsProvider import ClusterSettingsProvider
from SimStackServer.WorkflowModel import Resources
from WaNo.SimStackPaths import SimStackPaths

from SimStackServer.Util.FileUtilities import filewalker
from WaNo.lib.CallableQThread import CallableQThread

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



class SSHConnector(CallableQThread):
    error = Signal(str, int, int, str, name="SSHError")

    def _emit_error(self, base_uri, operation, error, message=None):
        if message is None:
            message = ""
        self.error.emit(base_uri, operation.value, error.value, message)

    def start_server(self, registry_name :str, callback=(None, (), {})):
        cm = self._get_cm(registry_name)
        cm: ClusterManager
        registry : Resources= self._registries[registry_name]
        software_dir = registry.sw_dir_on_resource
        VDIR = cm.get_newest_version_directory(software_dir)
        if VDIR == "V2":
            raise NotImplementedError("V2 connection capability removed from SimStack client. Please upgrade to V4.")
        elif VDIR == "V3":
            raise NotImplementedError("V3 connection capability removed from SimStack client. Please upgrade to V4.")
        elif VDIR != "V4":
            print("Found a newer server installation than this client supports (Found: %s). Please upgrade your client. Trying to connect with V4."%VDIR)
        VDIR = "V4"
        software_dir += '/' + VDIR
        myenv = "simstack_server"
        if registry.queueing_system == "AiiDA":
            myenv = "aiida"
            pythonproc = software_dir + '/local_anaconda/envs/%s/bin/python' %myenv
            execproc = "source %s/local_anaconda/etc/profile.d/conda.sh; conda activate %s; %s" % (
            software_dir, myenv, pythonproc)
        else:
            pythonproc = software_dir + '/local_anaconda/envs/%s/bin/python' % myenv
            execproc = "source %s/local_anaconda/etc/profile.d/conda.sh; conda activate %s; %s"%(software_dir, myenv, pythonproc)
        serverproc = software_dir + '/SimStackServer/SimStackServer.py'
        if not cm.exists(pythonproc):
            raise FileNotFoundError("%s pythonproc was not found. Please check, whether the software directory in Configuration->Servers is correct and postinstall.sh was run"%pythonproc)
        if not cm.exists(serverproc):
            raise FileNotFoundError("%s serverproc was not found. Please check, whether the software directory in Configuration->Servers is correct and the file exists" % serverproc)

        command = "%s %s"%(execproc, serverproc)
        cm.connect_zmq_tunnel(command)
        return ErrorCodes.NO_ERROR

    def _get_main_par_dir(self):
        import __main__
        maindir = os.path.dirname(os.path.realpath(__main__.__file__))
        return maindir

    @eagain_catcher
    def connect_registry(self, registry_name: str, callback=(None, (), {})):
        name = registry_name
        error = ErrorCodes.NO_ERROR
        statusmessage = ""
        registry = self._registries[name]
        try:
            # We disconnect in case of reconnect
            if name in self._clustermanagers:
                cm = self._clustermanagers[name]
                if cm.is_connected():
                    cm.disconnect()
        except ConnectionError as e:
            pass

        private_key = registry.ssh_private_key
        if private_key == "<embedded>":
            pkfile = SimStackPaths.get_embedded_sshkey()
            if os.path.isfile(pkfile):
                private_key = pkfile
            else:
                raise FileNotFoundError("Could not find private key at path <%s>"%pkfile)
        extra_config = registry.extra_config
        cm = ClusterManager(url=registry.base_URI, port=registry.port,
                            calculation_basepath=registry.basepath, user=registry.username,
                            sshprivatekey=private_key,
                            extra_config=extra_config,
                            queueing_system=registry.queueing_system, default_queue=registry.queue)
        self._clustermanagers[name] = cm

        if not cm.is_connected():
            try:
                local_hostkey_file = SimStackPaths.get_local_hostfile()
                try:
                    # We read the known hosts at the last time:
                    cm.load_extra_host_keys(local_hostkey_file)
                    cm.connect()
                except paramiko.ssh_exception.SSHException as e:
                    exstr = str(e)
                    if exstr.endswith("not found in known_hosts"):
                        reply = QMessageBox.question(None, 'SSH HostKey unknown',

                            'An unknown hostkey was encountered, when connecting to %s. If this is your first time connecting, this is expected. Add the Host to your local hostkeys?'%name, QMessageBox.Yes, QMessageBox.No)
                        if reply == QMessageBox.Yes:
                            if hasattr(cm, "set_connect_to_unknown_hosts"):
                                #This is backwards compatibility for horeka
                                cm.set_connect_to_unknown_hosts(True)
                                cm.connect()
                            else:
                                cm.connect(connect_to_unknown_hosts=True)
                            cm.save_hostkeyfile(local_hostkey_file)
                        else:
                            raise e from e
                    else:
                        raise e from e
                error = ErrorCodes.NO_ERROR
                statusmessage = "Connected."
                returncode_serverstart = self.start_server(registry_name)
            except paramiko.ssh_exception.SSHException as e:
                statusmessage = str(e)
                traceback.print_exc()
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
                traceback_out = StringIO()
                traceback.print_exc(file=traceback_out)
                statusmessage = "Did not find file, Exception was:\n%s  \nException occured in relation to File <%s>\n\n ----- Traceback -----\n %s" % (e, e.filename, traceback_out.getvalue())

                error = ErrorCodes.CONN_ERROR
                del self._clustermanagers[name]
            except OSError as e:
                statusmessage = "Caught generic exception %s. Please reconnect and try again and if it reappears report to Nanomatch" % (e)
                error = ErrorCodes.CONN_ERROR
                del self._clustermanagers[name]
        else:
            print("Already connected, will not connect again.")
        self._exec_callback(callback, registry.base_URI, error, statusmessage)

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

    def disconnect_registry(self, registry_name, callback):
        name = registry_name
        error = ErrorCodes.NO_ERROR
        statusmessage = ""
        if name in self._clustermanagers:
            cm = self._clustermanagers[name]
            cm.disconnect()
        self._exec_callback(callback, error, statusmessage)

    @eagain_catcher
    def run_workflow_job(self, registry_name, submitname, dir_to_upload, xml, progress_callback = None, callback = None):

        cm = self._get_cm(registry_name)
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
            mydir = dirname(submitpath).replace('\\','/')
            cm.mkdir_p(mydir)
            cm.put_file(filename,submitpath.replace('\\','/'))

        wf_yml_name = real_submitname + "/" + "rendered_workflow.xml"
        with cm.remote_open(wf_yml_name,'wt') as outfile:
            outfile.write(etree.tostring(xml, encoding = "utf8", pretty_print=True).decode()
                          .replace("c9m:","")
                          .replace("${STORAGE}/","")
                          .replace("${SUBMIT_NAME}",real_submitname)
                          .replace("${BASEFOLDER}",cm.get_calculation_basepath() + '/' + submitname)
                          .replace("${QUEUE}", cm.get_queueing_system())
                          .replace("${QUEUE_NAME}",cm.get_default_queue())
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
    def update_workflow_list(self, registry_name, callback=(None, (), {})):
        cm = self._get_cm(registry_name)
        workflows = cm.get_workflow_list()
        self._exec_callback(callback, registry_name, workflows)

    def exit(self):
        for cm in self._clustermanagers.values():
            cm.disconnect()

    @eagain_catcher
    def update_workflow_job_list(self, registry_name, wfid, callback=(None, (), {})):
        cm = self._get_cm(registry_name)
        files = cm.get_workflow_job_list(wfid)
        self._exec_callback(callback, registry_name, wfid, files)

    @eagain_catcher
    def update_dir_list(self, registry_name, path, callback=(None, (), {})):
        cm = self._get_cm(registry_name)
        files = cm.list_dir(path)
        self._exec_callback(callback, registry_name, path, files)

    @eagain_catcher
    def delete_file(self, registry_name, filename, callback=(None, (), {})):
        cm = self._get_cm(registry_name)
        if cm.is_directory(filename):
            cm.rmtree(filename)
        else:
            cm.delete_file(filename)
        self._exec_callback(callback, registry_name, filename, ErrorCodes.NO_ERROR)

    def delete_job(self, base_uri, job, callback=(None, (), {})):
        worker = self._get_error_or_fail(base_uri)
        if not worker is None:
            worker.delete_job(callback, base_uri, job)

    def abort_job(self, base_uri, job, callback=(None, (), {})):
        worker = self._get_error_or_fail(base_uri)
        if not worker is None:
            worker.abort_job(callback, base_uri, job)

    def get_workflow_url(self, registry_name, workflow):
        cm = self._get_cm(registry_name)
        return cm.get_url_for_workflow(workflow)

    @eagain_catcher
    def delete_workflow(self, registry_name, workflow_submitname, callback=(None, (), {})):
        cm = self._get_cm(registry_name)
        cm.delete_wf(workflow_submitname)

    @eagain_catcher
    def abort_workflow(self, registry_name, workflow_submitname, callback=(None, (), {})):
        cm = self._get_cm(registry_name)
        cm.abort_wf(workflow_submitname)
        self.logger.debug("Sending Workflow Abort message for workflows %s"%workflow_submitname)

    @eagain_catcher
    def download_file(self, registry_name, download_files, local_dest, progress_callback = None, callback=(None, (), {})):
        cm = self._get_cm(registry_name)
        todl = download_files
        if isinstance(download_files, str):
            todl = [download_files]

        for remote_file in todl:
            cm.get_file(remote_file, local_dest, progress_callback)

    def _get_cm(self, registry_name) -> ClusterManager:
        name = registry_name
        if not name in self._clustermanagers:
            raise ConnectionError("Clustermanager %s was not connected."%name)
        return self._clustermanagers[name]

    @eagain_catcher
    def upload_files(self, registry_name, upload_files, destination, progress_callback = None, callback=(None, (), {})):
        cm = self._get_cm(registry_name)
        toupload = upload_files
        if isinstance(upload_files, str):
            toupload = [upload_files]

        for local_file in toupload:
            cm.put_file(local_file, destination)


    def run(self):
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

    def quit(self):
        self.exit()
        super().quit()

    def __init__(self, cbReceiver, unicore_state):
        super(SSHConnector, self).__init__()
        self.logger         = logging.getLogger("SSHConnection")
        self.cbReceiver     = cbReceiver
        self._registries = ClusterSettingsProvider.get_registries()
        self._clustermanagers = {}

        self.workers        = {}

        import sys
        loglevel = logging.DEBUG
        self.logger.setLevel(loglevel)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(loglevel)
        self.logger.addHandler(ch)

