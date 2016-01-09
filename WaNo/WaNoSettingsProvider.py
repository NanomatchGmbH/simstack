import os

from .lib.AbstractSettings import AbstractSettings
from .Constants import SETTING_KEYS

def _path(name):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), name)

class WaNoSettingsProvider(AbstractSettings):
    def __init__(self, settings_file):
        super(WaNoSettingsProvider, self)\
                .__init__("WaNoSettingsProvider", settings_file=settings_file)

    def _set_defaults(self):
        defaults = [
                (SETTING_KEYS['registries'], [], "List of registries."),
                (SETTING_KEYS['wanoRepo'], _path("WaNoRepository"), "Directory containing the WaNos."),
                (SETTING_KEYS['workflows'], _path("WorkFlows"), "Working directory for Workflows."),
            ]

        for valuename,default,explanation in defaults:
            #self._add_default(valuename,default,explanation)
            print("default: %s, type: %s" % (default, type(default)))
            self.set_value(valuename, default)

