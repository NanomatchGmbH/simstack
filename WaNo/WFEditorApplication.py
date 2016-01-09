import logging
import os

from PySide.QtCore import QObject
from   lxml import etree

from WaNo.view import WFViewManager
from .WaNoRepository import WaNoRepository
from .WaNoGitRevision import get_git_revision
from .Constants import SETTING_KEYS


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
        print("open_registry_settings")
        self._view_manager.open_dialog_registry_settings(
                self.__settings.get_value(SETTING_KEYS['registries'])
            )

    def _on_registry_changed(self, index):
        self._logger.info("Registry changed to '%s'." % \
                self.__settings.get_value(
                    "%s.%d.name" % (SETTING_KEYS['registries'], index)
                )
            )
        #TODO

    ############################################################################
    #                                                                          #
    ############################################################################
    def __load_wanos_from_repo(self, wano_repo_path):
        print("loading WaNos from %s." % wano_repo_path)
        self._logger.debug("loading WaNos from %s." % wano_repo_path)

        wanoRep = WaNoRepository()
        wanos = []

        files = [f for f in os.listdir(wano_repo_path) if f.endswith(".xml")]
        
        for infile in files:
            name = infile.split(".")[0]
            xxi = os.path.join(wano_repo_path, wano_repo_path+"/{0}".format(infile))
            element = wanoRep.parse_xml_file(xxi) 

            wanos.append((name, element))

        return wanos


    def __load_saved_workflows(self, workflow_path):
        print("loading Workflows from %s." % workflow_path)
        self._logger.debug("loading Workflows from %s." % workflow_path)

        files = [f for f in os.listdir(workflow_path) if f.endswith(".xml")]
        workflows = []

        for infile in files:
            xxi = os.path.join(workflow_path, infile)
            parsed = False

            try:
                inputData = etree.parse(xxi)
            except Exception as e:
                self._logger.error(
                        "Error when trying to parse file '%s'\n\n%s" % \
                            (xxi, e)
                    )
                self._view_manager.show_error(
                        "Error when trying to parse file '%s'\n\n%s" % \
                            (xxi, e)
                    )
            if parsed:
                r = inputData.getroot()
                if r.tag == "Workflow":
                    element = WorkFlow(r)
                    workflows.append(element)
                else:
                    self._logger.critical('Loading Workflows: no workflow in file ' + xxi)
        return workflows


    ############################################################################
    #                             update                                       #
    ############################################################################
    def _update_wanos(self):
        wanos = self.__load_wanos_from_repo(
                self.__settings.get_value(SETTING_KEYS['wanoRepo'])
            )
        self._view_manager.update_wano_list(wanos)

    def _update_workflow_list(self):
        workflows = self.__load_saved_workflows(
                self.__settings.get_value(SETTING_KEYS['workflows'])
            )
        self._view_manager.update_saved_workflows_list(workflows)

    def _update_saved_registries(self):
        default = 0
        regList = []

        registries = self.__settings.get_value(SETTING_KEYS['registries'])

        for i, r in enumerate(registries):
            regList.append(r[SETTING_KEYS['registry.name']])
            if r[SETTING_KEYS['registry.is_default']]:
                default = i

        self._view_manager.update_registries(regList, selected=default)

    def _update_all(self):
        self._update_saved_registries()
        self._update_wanos()
        self._update_workflow_list()

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

    def __init__(self, settings):
        super(WFEditorApplication, self).__init__()
        self.__settings     = settings

        self._logger        = logging.getLogger('WFELOG')
        self._view_manager  = WFViewManager()
        self._unicore       = None # TODO pyura API
        # TODO model

        self._connect_signals()

        self.__start()
        self._logger.info("Logging Tab Enabled Version: " + get_git_revision())

