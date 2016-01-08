from .lib.AbstractSettings import AbstractSettings
from .Constants import SETTING_KEYS

class WaNoSettingsProvider(AbstractSettings):
    def __init__(self, settings_file):
        super(WaNoSettingsProvider, self)\
                .__init__("WaNoSettingsProvider", settings_file=settings_file)

    def _set_defaults(self):
        defaults = [
                (SETTING_KEYS['registries'], [], "List of registries."),
            ]

        for valuename,default,explanation in defaults:
            #self._add_default(valuename,default,explanation)
            print("default: %s, type: %s" % (default, type(default)))
            self.set_value(valuename, default)

