import os
from os.path import join


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
        return join(cls.get_settings_folder_nanomatch(),"local_known_hosts")

    @classmethod
    def gen_empty_local_hostfile_if_not_present(cls):
        lhosts = cls.get_local_hostfile()
        if not os.path.exists(lhosts):
            with open(lhosts, 'wt') as outfile:
                pass
        return lhosts

    @classmethod
    def get_embedded_path(cls):
        return join(cls.get_main_dir(),"embedded")

    @classmethod
    def get_temp_folder(cls):
        import Qt

        if Qt.IsPySide:
            from PySide.QtGui import QDesktopServices
            return QDesktopServices.storageLocation(QDesktopServices.TempLocation)

        import importlib
        qc = importlib.import_module("%s.QtCore" % Qt.__binding__)
        rtp = qc.QStandardPaths.standardLocations(qc.QStandardPaths.TempLocation)
        if isinstance(rtp, list):
            rtp = rtp[0]
        return rtp

    @classmethod
    def get_settings_folder(cls):
        import Qt
        if os.path.isdir(os.path.join("config", cls._SETTINGS_DIR)):
            return "config"
        if Qt.IsPySide:
            from PySide.QtGui import QDesktopServices
            return QDesktopServices.storageLocation(QDesktopServices.DataLocation)

        import importlib
        qc = importlib.import_module("%s.QtCore" % Qt.__binding__)
        rtp = qc.QStandardPaths.standardLocations(qc.QStandardPaths.DataLocation)
        if isinstance(rtp, list):
            rtp = rtp[0]

        return rtp

    @classmethod
    def get_settings_folder_nanomatch(cls):
        return join(cls.get_settings_folder(),cls._SETTINGS_DIR)

    @classmethod
    def get_settings_file(cls):
        return join(cls.get_settings_folder_nanomatch(), cls._SETTINGS_FILE)


