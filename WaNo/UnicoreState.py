from PySide.QtCore import QReadWriteLock

class UnicoreStateValues:
    CONNECTION      = "connection"

class UnicoreStateFactory:
    _instance = None

    class __UnicoreState:
        def set_value(self, key, value):
            self.write_lock()
            self.values[key] = value
            self.write_unlock()

        def get_value(self, key):
            self.read_lock()
            v = self.value[key]
            self.read_unlock()
            return v

        def read_lock(self):
            self.lock.lockForRead()
    
        def read_unlock(self):
            self.lock.unlock()
    
        def write_lock(self):
            self.lock.lockForWrite()
    
        def write_unlock(self):
            self.lock.unlock()
    
        def get_lock(self):
            return self.lock
    
        def __init__(self):
            self.lock   = QReadWriteLock(QReadWriteLock.NonRecursive)
            self.values = {}
    
    @classmethod
    def get_instance(self):
        if UnicoreStateFactory._instance is None:
                UnicoreStateFactory._instance = UnicoreStateFactory.__UnicoreState()
        return UnicoreStateFactory._instance

