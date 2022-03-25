from SimStackServer.Settings.ClusterSettingsProvider import ClusterSettingsProvider
from Qt.QtCore import QObject, Signal

from SimStackServer.WorkflowModel import Resources

class QtSettingsChangedWorkaround(QObject):
    settings_changed = Signal(name="SettingsChanged")
    def __init__(self):
        print("This init is actually running")
        super().__init__()

class QtClusterSettingsProvider(ClusterSettingsProvider, QtSettingsChangedWorkaround):
    def __init__(self):
        super().__init__()

    def add_resource(self, resource_name: str) -> Resources:
        new_resource = super().add_resource(resource_name=resource_name)
        self.settings_changed.emit()
        return new_resource

    def remove_resource(self, resource_name: str) -> None:
        super().remove_resource(resource_name=resource_name)
        self.settings_changed.emit()