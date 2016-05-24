from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import logging
import os

from PySide.QtCore import QObject
from PySide import QtCore,QtGui

from   lxml import etree

from WaNo import WaNoFactory
from WaNo.lib.pyura.pyura import UnicoreAPI, HTTPBasicAuthProvider
from WaNo.lib.pyura.pyura import ErrorCodes as UnicoreErrorCodes

from WaNo.view import WFViewManager
from WaNo.WaNoGitRevision import get_git_revision
from WaNo.Constants import SETTING_KEYS
from WaNo.view.WaNoViews import WanoQtViewRoot


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

    def _on_fs_model_update_request(self, path):
        self._logger.debug("Querying %s from Unicore Registry" % path)
        print("Querying %s from Unicore Registry" % path)
        ok = True
        if self._unicore is None:
            self._view_manager.show_error("No registry selected.")
            ok = False
        #TODO implement in pyura upstream....
        #if not self._unicore.is_connected:
        #    self._view_manager.show_error("Registry not connected.")
        #    ok = False
        if ok:
            storage_manager = self._unicore.get_storage_manager()
            storage_manager.update_list()
            if path == "":
                files = [s.get_id() for s in storage_manager.get_list()]
            else:
                files = storage_manager.get_file_list(path=path)
            files = [s.get_id() for s in storage_manager.get_list()]
            self._view_manager.update_filesystem_model(path, files)


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

                self.wanos.append((name,fullpath,xmlpath,wano_icon))

        return self.wanos


    def __load_saved_workflows(self, workflow_path):
        self._logger.debug("loading Workflows from %s." % workflow_path)
        workflows = []
        return workflows
        #TODO: Implement tomorrow

        files = [f for f in os.listdir(workflow_path) if f.endswith(".xml")]
        for infile in files:
            try:
                pass
                #parse workflow model
            except Exception as e:
                self._logger.error(
                        "Error when trying to parse file '%s'\n\n%s" % \
                            (xxi, e)
                    )
                self._view_manager.show_error(
                        "Error when trying to parse file '%s'\n\n%s" % \
                            (xxi, e)
                    )
                self._logger.critical('Loading Workflows: no workflow in file ' + xxi)
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
            error, status = self._unicore.connect()
            if error == UnicoreErrorCodes.NO_ERROR and status == 200:
                success = True
                self._logger.info("Connected.")
            else:
                self._logger.error("Failed to connect to registry: %d, %s" % \
                            (status, str(error))
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
        self._view_manager.request_fs_model_update.connect(self._on_fs_model_update_request)

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

