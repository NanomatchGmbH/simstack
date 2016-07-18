from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import logging
import threading
from enum import Enum


from PySide.QtCore import QThread, Qt
from PySide.QtCore import Slot, Signal, QObject

from WaNo.lib.pyura.pyura import UnicoreAPI, HTTPBasicAuthProvider
from WaNo.lib.pyura.pyura import ErrorCodes as UnicoreErrorCodes

from WaNo.lib.CallableQThread import CallableQThread
from WaNo.lib.TPCThread import TPCThread


_AUTH_TYPES = Enum("AUTH_TYPES",
    """
    HTTP
    """,
    module=__name__
)

class UnicoreWorker(TPCThread):

    @TPCThread._from_other_thread
    def connect(self, callback, username, password, base_uri, con_settings):
        import platform
        import ctypes
        if platform.system() == "Linux":
            self.logger.debug("UnicoreWorker Thread ID(connect): %d\t%d" % \
                    (threading.current_thread().ident,
                    ctypes.CDLL('libc.so.6').syscall(186)))

        err, status = self.registry.connect()
        callback(base_uri, err, status)

    #TODO remove, debug only
    def start(self):
        super(UnicoreWorker, self).start()
        import platform
        import ctypes
        if platform.system() == "Linux":
            self.logger.debug("UnicoreWorker Thread ID: %d\t%d" % \
                    (threading.current_thread().ident,
                    ctypes.CDLL('libc.so.6').syscall(186)))

    def __init__(self, registry, logger):
        super(UnicoreWorker, self).__init__()
        self.logger         = logger
        self.registry       = registry

class UnicoreConnector(CallableQThread):
    error = Signal(str, int, name="UnicoreError")

    AUTH_TYPES = _AUTH_TYPES

    ERROR = Enum("ERROR",
        """
        NO_ERROR
        AUTH_SETUP
        """,
        module=__name__
    )


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
    def create_connect_args(auth_type=_AUTH_TYPES.HTTP, wf_uri=None):
        return {'auth_type': auth_type,
                'wf_uri': wf_uri
            }

    #@Slot(str, str, str, dict, name="ConnectRegistry")
    def connect_registry(self, username, password, base_uri, callback=None,
            con_settings=None):
        # TODO what if con_settings is None?

        #TODO debug only
        import platform
        import ctypes
        if platform.system() == "Linux":
            self.logger.debug("Unicore Thread ID (slot): %d\t%d\t%s" % \
                    (threading.current_thread().ident,
                    ctypes.CDLL('libc.so.6').syscall(186),
                    str(QThread.currentThreadId())))
        stime = 4
        self.logger.debug("Going to sleep for %d sec. @connect_registry" % stime)
        import time
        time.sleep(stime)
        self.logger.debug("Waking up again.")
        ##### END TODO


        if base_uri in self.workers:
            return

        auth_provider = self.get_authprovider(
                con_settings['auth_type'], username, password)
        if auth_provider is None:
            self.error.emit(base_uri, UnicoreConnector.ERROR.AUTH_SETUP)
            return

        #TODO add get_registry method to UnicoreAPI
        registry = UnicoreAPI.add_registry(base_uri, auth_provider)

        worker = UnicoreWorker(registry, self.logger)
        worker.set_exit_callback(self.cb_worker_exit, base_uri)

        worker.start()
        self.logger.debug("Started worker thread for '%s'." % base_uri)

        self.workers[base_uri] = {'worker': worker, 'registry': registry}

        worker.connect(callback, username, password,
                base_uri, con_settings=None)

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

        self.cbReceiver.connect_registry.connect(self.test.connect_registry, type=Qt.QueuedConnection)

        self.logger.debug("Started UnicoreConnector Thread.")
        self.exec_()


    def __init__(self, cbReceiver, unicore_state):
        super(UnicoreConnector, self).__init__()
        self.registry       = None
        self.cbReceiver     = cbReceiver
        self.unicore_state  = unicore_state
        self.logger         = logging.getLogger("Unicore")
        self.workers        = {}

        #self.connect_registry.connect(self._unicore_connector.connect_registry)

        import sys
        loglevel = logging.DEBUG
        self.logger.setLevel(loglevel)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(loglevel)
        self.logger.addHandler(ch)

        self.test           = self #Test(self.logger)
