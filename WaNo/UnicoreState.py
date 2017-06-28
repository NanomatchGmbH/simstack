from PySide.QtCore import QReadWriteLock, QMutex
import copy # for ProtectedDict and ProtectedList
from enum import Enum

class UnicoreStateValues(object):
    CONNECTION      = "connection"

try:
    from pyura.pyura.Constants import ConnectionState as UnicoreConnectionStates
except:
    from lib.pyura.pyura.Constants import ConnectionState as UnicoreConnectionStates

class ProtectedValue(object):
    def __get_value(self, unlock=True):
        v = None
        self._lock.lockForWrite()
        v = self._value
        if unlock:
            self._lock.unlock()
        return v

    def get_value(self):
        return self.__get_value(unlock=True)

    def change_value(self, value):
        self._lock.lockForWrite()
        self._value = value
        self._lock.unlock()

    def __init__(self, value):
        self._lock = QReadWriteLock(QReadWriteLock.NonRecursive)
        self._value = value

class ProtectedRefCountedValue(ProtectedValue):
    def __increment_list_ref_count(self):
        self._ref_lock.lockForWrite()
        self._ref_count += 1
        self._ref_lock.unlock()

    def __decrement_list_ref_count(self):
        self._ref_lock.lockForWrite()
        self._ref_count += 1
        self._ref_lock.unlock()

    def get_value(self):
        v = super(ProtectedRefCountedValue, self).__get_value(unlock=False)
        if not v is None:
            self.__increment_list_ref_count()
        self._lock.unlock()
        return v

    def release_value(self, value):
        self._lock.lockForRead()
        # test value, just to be shure we don't do something stupide...
        if self._value == value:
            self.__decrement_list_ref_count()
        self._lock.unlock()

    def __init__(self, value):
        super(ProtectedRefCountedValue, self).__init__(value)
        self._ref_lock = QReadWriteLock(QReadWriteLock.NonRecursive)
        self._ref_count = 0

#TODO class AutoProtectedValue:
#    def __determine_required_protection(self, value):
#        if type
#    def __init__(self, value):
#        self.

class ProtectedList(object):
    def __create_list_item(self, item):
        return {'ref_count': 0, 'item': item}

    def __create_list_items(self, items):
            return [self.__create_list_item(items)] if len(items) <= 1 \
                    else [self.__create_list_item(item) for item in items]

    def get_list_index(self, listkey, index):
        rv = None
        index_in_list = False
        if index >= 0:
            self._lock.lockForRead()
            if index < len(self._list):
                rv = self._list[index]
                index_in_list = True
                self.__increment_list_ref_count(rv)
            self._lock.unlock()

        if not index_in_list:
            raise IndexError("list index out of range")
        return rv['item'] if not rv is None else None

    def release_list_item_at(self, listkey, index, item):
        done = False
        index_in_list = False
        if index >= 0:
            self._lock.lockForRead()
            if index < len(self._list):
                index_in_list = True
                if self._list[index] == item:
                    self.__decrement_list_ref_count(self._list[index])
            self._lock.unlock()

        if not index_in_list:
            raise IndexError("list index out of range")
        return done

    def add_items(self, items):
        self._lock.lockForWrite()
        self._list.extend(self.__create_list_items(items))
        self._lock.unlock()

    def __init__(self, initial_list=[]):
        """
        In case an initial list is given, it will be added as a deep copy.
        This will prevent unsave changes.
        """
        self._list = copy.deepcopy(initial_list)
        self._lock = QReadWriteLock(QReadWriteLock.NonRecursive)

class ProtectedDict(object):

    def _add_value(self, key, value):
        """ Note: _Must_ hold self._lock! """
        fail = None
        try:
            self._values[key] = value
        except Exception as e:
            fail = e
        return fail

    def set_value(self, key, value):
        self._lock.lockForWrite()
        fail = self._add_value(key, value)
        self._lock.unlock()
        if not fail is None:
            raise fail

    def set_multiple_values(self, values_dict):
        fail = None
        self._lock.lockForWrite()
        for key, value in values_dict.items():
            fail = self._add_value(key, value)
            if not fail is None:
                break
        self._lock.unlock()
        if not fail is None:
            raise fail

    def get_value(self, key):
        fail = None
        self._lock.lockForRead()
        try:
            v = self._values[key]
        except Exception as e:
            fail = e
        self._lock.unlock()
        if not fail is None:
            raise fail
        return v

    def del_value(self, key):
       """ Savely removes and returns a value. """
       rv = None
       self._lock.lockForWrite()
       if key in self._values:
           # Why is this safe? - Because we either return a reference which will
           # not be affected by del() or we return a simple build-in type which
           # will be copied on assignment.
           rv = self._values[key]
           del(self._values[key])
       self._lock.unlock()
       return rv

    def __enter__(self):
        self._lock.lockForRead()
        return self._values

    def __exit__(self, *unused):
        self._lock.unlock()

    def __iter__(self):
        self._lock.lockForRead()
        for key in self._values:
            yield key
        self._lock.unlock()

    def __init__(self, initial_dict={}):
        """
        In case an initial dict is given, it will be added as a deep copy.
        This will prevent unsave changes.
        """
        self._values = copy.deepcopy(initial_dict)
        self._lock = QReadWriteLock(QReadWriteLock.NonRecursive)

class ProtectedIndexedList(ProtectedDict):
    """ Implements a list with persistent indices that would not change, even
    if list elements are deleted or moved. """

    def __create_new_index(self):
        """Note: _Must_ hold self._lock!"""
        index = 0
        if len(self._values) >= 1:
            index = max(self._values.keys()) + 1
        return index

    def __iter__(self):
        """ Yields an index-value pair for each list element. """
        self._lock.lockForRead()
        for index, entry in self._values.items():
            yield (index, entry)
        self._lock.unlock()

    def set_value(self, value):
        fail = None
        self._lock.lockForWrite()
        index = self.__create_new_index()
        if index in self._values:
            fail = KeyError("Key collision. Keys must be unique. This should never happen...")
        else:
            fail = self._add_value(index, value)
        self._lock.unlock()
        if not fail is None:
            raise fail
        return index

    def del_value(self, index):
        rv = None
        self._lock.lockForWrite()
        if index in self._values:
            rv = self._values[index]
            del(self._values[index])
        self._lock.unlock()
        return rv

    def __init__(self, initial_dict={}):
        super(ProtectedIndexedList, self).__init__(initial_dict)

class ReaderWriterInstance(object):
    def get_reader_instance(self):
        raise NotImplementedError("Must be implemented in sub-class.")

    def get_writer_instance(self):
        raise NotImplementedError("Must be implemented in sub-class.")

    def get_reader_instance(self):
        return self._reader

    def get_writer_instance(self):
        return self._writer

    def __init__(self):
        self._writer = None
        self._reader = None


class ProtectedReaderWriterDict(ReaderWriterInstance):
    class _Reader(object):
        def get_value(self, key):
            return self._pdict_instance.get_value(key)

        def __enter__(self):
            return self._pdict_instance.__enter__()

        def __exit__(self, *unused):
            self._pdict_instance.__exit__(*unused)

        def __iter__(self):
            return self._pdict_instance.__iter__()

        def __init__(self, instance):
            self._pdict_instance = instance

    class _Writer(_Reader):
        def set_value(self, key, value):
            self._pdict_instance.set_value(key, value)

        def set_multiple_values(self, values_dict):
            self._pdict_instance.set_multiple_values(values_dict)

        def del_value(self, key):
            return self._pdict_instance.del_value(key)

        def __init__(self, instance):
            super(ProtectedReaderWriterDict._Writer, self).__init__(instance)

    def __init__(self, initial_dict={}):
        super(ProtectedReaderWriterDict, self).__init__()
        self._pdict = ProtectedDict(initial_dict)
        self._writer = ProtectedReaderWriterDict._Writer(self._pdict)
        self._reader = ProtectedReaderWriterDict._Reader(self._pdict)

class ProtectedReaderWriterIndexedList(ReaderWriterInstance):
    class _Reader(object):
        def get_value(self, key):
            return self._list_instance.get_value(key)

        def __enter__(self):
            return self._list_instance.__enter__()

        def __exit__(self, *unused):
            self._list_instance.__exit__(*unused)

        def __iter__(self):
            return self._list_instance.__iter__()

        def __init__(self, instance):
            self._list_instance = instance

    class _Writer(_Reader):
        def set_value(self, value):
            return self._list_instance.set_value(value)

        def del_value(self, key):
            return self._list_instance.del_value(value)

        def __init__(self, instance):
            super(ProtectedReaderWriterIndexedList._Writer, self).__init__(instance)

    def __init__(self, initial_dict={}):
        super(ProtectedReaderWriterIndexedList, self).__init__()
        self._list_instance = ProtectedIndexedList(initial_dict)
        self._writer = ProtectedReaderWriterIndexedList._Writer(self._list_instance)
        self._reader = ProtectedReaderWriterIndexedList._Reader(self._list_instance)

UnicoreDataTransferStates = Enum(
        "DataTransferStates",
        """
        PENDING
        RUNNING
        CANCELED
        FAILED
        DONE
        """
        )

UnicoreDataTransferDirection = Enum(
        "DataTransferDirection",
        """
        UPLOAD
        DOWNLOAD
        """
        )

class UnicoreStateFactory(object):
    _instance = None

    class __UnicoreState(object):
        def add_registry(self, base_uri, username,
                state=UnicoreConnectionStates.DISCONNECTED):
            tmp = {
                    'base_uri': base_uri,
                    'username': username,
                    'state': state,
                    'data_transfers': None,
                    }
            registry = ProtectedReaderWriterDict(tmp)

            # We _must_ create the ProtectedReaderWriterIndexedList outside of
            # the tmp dict and may not reference it there.
            # Otherwise, the ProtectedReaderWriterIndexedList will be cleaned
            # up when leaving this function's scope.
            registry.get_writer_instance().set_value('data_transfers',
                    ProtectedReaderWriterIndexedList())
            self._registries.get_writer_instance().set_value(base_uri, registry)
            #TODO will del(tmp) delete its 'ProtectedList'?
            return registry

        # NOTE: Why is returning references to dict entries ok even though the
        # lock is released imediatelly?
        #
        # This is because we return refernces to objects that are taking care
        # of locking themselfs. Even if the caller of this function would still
        # operate (they are all readers!) on these objects and the registry
        # containing these objects is deleted during the operation, the returned
        # object will not be deleted. The "Protected" classes don't do that.
        # Readers can finish on recently expired data.
        # If a caller stores the returned reference for a longer period of time,
        # it is a mistake by the caller, not ours. :-)

        def get_registry_state(self, base_uri):
            """Returns a ProtectedDict object."""
            return self._registries.get_reader_instance().get_value(base_uri)

        def get_data_transfers_for_registry(self, base_uri):
            """Returns a ProtectedReaderWriterIndexedList object."""
            return self._registries.get_reader_instance().get_value(base_uri)\
                    .get_reader_instance().get_value('data_transfers')

        def get_data_transfer(self, base_uri, index):
            return self._registries.get_reader_instance().get_value(base_uri)\
                    .get_reader_instance().get_value('data_transfers')\
                    .get_reader_instance().get_value(index)

        def data_transfer_iterator(self, base_uri=None):
            #TODO use base_uri as filter, if given.
            reg_reader = self._registries.get_reader_instance()
            for registry in reg_reader:
                for dl in reg_reader.get_value(registry)\
                        .get_reader_instance().get_value('data_transfers').get_reader_instance():
                    yield dl



        def add_data_transfer(self, base_uri, source, dest, storage, direction,
                state=UnicoreDataTransferStates.PENDING, total=-1, progress=0):
            tmp = {
                    'source': source,
                    'dest': dest,
                    'storage': storage,
                    'direction': direction,
                    'state': state, # running, canceled, pending, done, ...
                    'total': total,
                    'progress': progress,
                    }
            data_transfer = ProtectedReaderWriterDict(tmp)
            transfers = self.get_data_transfers_for_registry(base_uri)
            return transfers.get_writer_instance().set_value(data_transfer)

        def __init__(self):
            """
            self._registries                        ProtectedReaderWriterDict
                |-- registry                        ProtectedReaderWriterDict
                |   |-- data_transfers              ProtectedReaderWriterIndexedList
                |   |   |-- transfer                ProtectedReaderWriterDict
            """
            self._registries = ProtectedReaderWriterDict()
    #TODO Idea: Add __enter__ / __exit__ methods for getter methods. This prevents
    # storage of references.

    class _Reader(object):
        #TODO we should not return get_writer_instance nor get_reader_instances,
        # the _Reader should not be able to get writers, but writers might
        # decide on their own
        """Note: we do not want to catch any errors. They should be passed to the user."""

        def get_registry_state(self, base_uri):
            return self._state.get_registry_state(base_uri).get_reader_instance()

        def get_data_transfers_for_registry(self, base_uri):
            return self._state.get_data_transfers_for_registry(base_uri).get_reader_instance()

        def get_data_transfer(self, base_uri, index):
            return self._state.get_data_transfer(base_uri, index)

        def data_transfer_iterator(self, base_uri=None):
            return self._state.data_transfer_iterator(base_uri)

        def __init__(self, state):
            self._state = state

    class _Writer(_Reader):
        """Note: we do not want to catch any errors. They should be passed to the user."""

        def add_registry(self, base_uri, username, state=UnicoreConnectionStates.DISCONNECTED):
            return self._state.add_registry(base_uri, username, state).get_writer_instance()

        def add_data_transfer(self, base_uri, source, dest, storage, direction,
                state=UnicoreDataTransferStates.PENDING, total=-1, progress=0):
            return self._state.add_data_transfer(base_uri, source, dest, storage,
                direction, state, total, progress)

        def __init__(self, state):
            super(UnicoreStateFactory._Writer, self).__init__(state)

    @classmethod
    def __get_instance(self):
        #TODO mutex lock this!
        if UnicoreStateFactory._instance is None:
                UnicoreStateFactory._instance = UnicoreStateFactory.__UnicoreState()
        return UnicoreStateFactory._instance

    @classmethod
    def get_reader(self):
        return UnicoreStateFactory._Reader(self.__get_instance())

    @classmethod
    def get_writer(self):
        return UnicoreStateFactory._Writer(self.__get_instance())




if __name__ == "__main__":
    from time import sleep
    from concurrent.futures import ThreadPoolExecutor
    def print2(s):
        print("\t\t\t\t%s" % s)

    def test_1_worker():
        sleep(1)
        print2("Locking for read")
        for key in pdict.get_reader_instance():
            print2("sleeping for 2 sec.")
            sleep(2)
            print2("Got key '%s'." % key)
        print2("Unlocking")
        return 0

    def test_1_start():
        print("## Test: concurrent read.")
        w = executor.submit(test_1_worker)
        print("Locking for read")
        for key in pdict.get_reader_instance():
            print("sleeping for 5 sec.")
            sleep(5)
            print("Got key '%s'." % key)
        print("Unlocking")
        print("Waiting for worker to terminate...")
        w.result()

    def test_2_start():
        print("\n\n## Test: concurrent read and write")
        w = executor.submit(test_1_worker)
        print("Locking for read")
        for i in range(0, 5):
            print("trying to write...")
            pdict.get_writer_instance().set_value('test_%d' % i, i)
            print("writing done.")
            sleep(1)
        print("Waiting for worker to terminate...")
        w.result()



    executor = ThreadPoolExecutor(max_workers=1)
    pindexed_list = ProtectedReaderWriterIndexedList( {'foo': 'bar'} )
    plist = ProtectedList([1, 2, 3, 42])
    pdict = ProtectedReaderWriterDict({'list1': pindexed_list, 'list2': plist})

    test_1_start()
    test_2_start()

