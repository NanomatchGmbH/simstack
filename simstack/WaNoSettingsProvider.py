import os

from .lib.AbstractSettings import AbstractSettings
from .Constants import SETTING_KEYS


def _path(name):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), name)

class NotInstancedError(Exception):
    pass

class WaNoSettingsProvider(AbstractSettings):
    instance = None
    def __init__(self, settings_file):
        super(WaNoSettingsProvider, self)\
                .__init__("WaNoSettingsProvider", settings_file=settings_file)

    @classmethod
    def get_instance(cls, settings_file = None):
        if cls.instance is None and settings_file is None:
            raise NotInstancedError()
        if cls.instance is None:
            cls.instance = WaNoSettingsProvider(settings_file)
        return cls.instance

    #just a convenience accessor:
    def get_path_settings(self):
        settings = {
            "wanoRepo" : self.get_value(SETTING_KEYS['wanoRepo']),
            "workflows": self.get_value(SETTING_KEYS['workflows'])
        }
        return settings

    def set_path_settings(self,pathsettings):
        self.set_value(SETTING_KEYS['wanoRepo'],pathsettings["wanoRepo"])
        self.set_value(SETTING_KEYS['workflows'], pathsettings["workflows"])

    def _set_defaults(self):
        mypath = os.path.join(os.path.dirname(os.path.realpath(__file__)))
        pp = os.pardir
        pardirpardir = os.path.join(mypath,pp,pp)
        defaults = [
                (SETTING_KEYS['registries'], [], "List of registries."),
                (SETTING_KEYS['wanoRepo'], os.path.join(pardirpardir,"wanos"), "Directory containing the WaNos."),
                (SETTING_KEYS['workflows'], os.path.join(pardirpardir,"workflows"), "Working directory for Workflows.")
            ]

        for valuename,default,explanation in defaults:
            #self._add_default(valuename,default,explanation)
            self.set_value(valuename, default)

