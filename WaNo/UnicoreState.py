from PySide.QtCore import QReadWriteLock, QMutex

class UnicoreStateValues:
    CONNECTION      = "connection"

class UnicoreStateFactory:
    _instance = None

    class __UnicoreState:
        def set_value(self, key, value):
            self.write_lock()
            self.values[key] = value
            self.write_unlock()

        """ Adds a new list.
        In case an initial list is given, it will be added as a copy.
        This will prevent unsave changes.
        """
        def add_list(self, key, initial_list=[]):
            rv = False
            self.listslock.lockForWrite()
            if not key in self.lists:
                l = {
                        'lock': QReadWriteLock(QReadWriteLock.NonRecursive),
                        'list': initial_list.copy()
                    }
                self.lists[key] = l
                rv = True
            self.listslock.unlock()
            return rv

        """ Savely removes and returns a list.
        """
        def remove_list(self, key):
            rv = None
            self.listslock.lockForWrite()
            if key in self.lists:
                rv = self.lists[key]
                del(self.lists[key])
            self.listslock.unlock()
            del(rv['lock'])
            return rv['list']

        def add_items_to_list(self, key, items):
            rv = False
            self.listslock.lockForRead()
            if key in self.lists:
                lock = self.lists[key]['lock']
                l    = self.lists[key]['list']
                lock.lockForWrite()
                l.extend([items] if len(items) <= 1 else items)
                lock.unlock()
                rv = True
            self.listslock.unlock()
            return rv

        def get_list_iterator(self, key):
            self.listslock.lockForRead()
            if key in self.lists:
                lock = self.lists[key]['lock']
                l    = self.lists[key]['list']
                lock.lockForRead()
                for i in l:
                    yield i
                lock.unlock()
            self.listslock.unlock()

        def get_value_no_lock(self, key):
            return self.value[key]

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
            self.lock       = QReadWriteLock(QReadWriteLock.NonRecursive)
            self.listslock  = QReadWriteLock(QReadWriteLock.NonRecursive)
            self.values     = {}
            self.lists      = {}

    class __Reader:
        def get_dl_iterator(self):
            return self._state.get_list_iterator('dls')

        def __init__(self, state):
            self._state = state

    class __Writer:
        def __init__(self, state):
            self._state = state

    @classmethod
    def __setup_instance(self, instance):
        instance.add_list('dls')
    
    @classmethod
    def __get_instance(self):
        #TODO mutex lock this!
        if UnicoreStateFactory._instance is None:
                UnicoreStateFactory._instance = UnicoreStateFactory.__UnicoreState()
                UnicoreStateFactory.__setup_instance(UnicoreStateFactory._instance)
        return UnicoreStateFactory._instance

    @classmethod
    def get_reader():
        return UnicoreStateFactory.__Reader(self.__get_instance())

    @classmethod
    def get_writer(self):
        return UnicoreStateFactory.__Writer(self.__get_instance())

