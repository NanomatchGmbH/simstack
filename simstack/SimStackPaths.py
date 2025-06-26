import os
from os.path import join

from PySide6.QtCore import QStandardPaths


class SimStackPaths:
    _SETTINGS_DIR = "NanoMatch"
    _SETTINGS_FILE = "ssh_clientsettings.yml"

    @classmethod
    def get_main_dir(cls):
        import __main__

        maindir = os.path.dirname(os.path.realpath(__main__.__file__))
        return maindir

    @classmethod
    def get_local_hostfile(cls):
        return join(cls.get_settings_folder_nanomatch(), "local_known_hosts")

    @classmethod
    def gen_empty_local_hostfile_if_not_present(cls):
        lhosts = cls.get_local_hostfile()
        if not os.path.exists(lhosts):
            with open(lhosts, "wt"):
                pass
        return lhosts

    @classmethod
    def get_embedded_path(cls):
        return join(cls.get_main_dir(), "embedded")

    @classmethod
    def get_embedded_sshkey(cls):
        return join(cls.get_settings_folder_nanomatch(), "embedded_idrsa")

    @classmethod
    def get_temp_folder(cls):
        rtp = QStandardPaths.standardLocations(
            QStandardPaths.StandardLocation.TempLocation
        )
        if isinstance(rtp, list):
            rtp = rtp[0]

        return rtp

    @classmethod
    def get_settings_folder(cls):
        if os.path.isdir(os.path.join("config", cls._SETTINGS_DIR)):
            return "config"

        rtp = QStandardPaths.standardLocations(
            QStandardPaths.StandardLocation.AppDataLocation
        )
        if isinstance(rtp, list):
            rtp = rtp[0]

        return rtp

    @classmethod
    def get_settings_folder_nanomatch(cls):
        return join(cls.get_settings_folder(), cls._SETTINGS_DIR)

    @classmethod
    def get_settings_file(cls):
        return join(cls.get_settings_folder_nanomatch(), cls._SETTINGS_FILE)
