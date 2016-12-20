import time
from sys import version_info
from concurrent.futures import ThreadPoolExecutor
from threading import Lock, Thread

class BetterThreadPoolExecutor(ThreadPoolExecutor):
    def has_shutdown(self):
        """Returns True, if this BetterThreadPoolExecutor has shut down.

        Note: This function is blocking (but interruptible).
        If it is interrupted, the result is not reliable.
        """
        shutdown = False
        if self._shutdown_lock.acquire():
            shutdown = self._shutdown
            self._shutdown_lock.release()
        return shutdown

    def __done_callback(self, future):
        self._done_callbacks_lock.acquire()
        if future in self._done_callbacks.keys():
            self._done_callbacks_lock.release()

            self._done_callbacks[future]['lock'].acquire()
            while len(self._done_callbacks[future]['list']) > 0:
                callback, args, kwargs = self._done_callbacks[future]['list'].pop()
                callback(future, *args, **kwargs)
            self._done_callbacks[future]['lock'].release()

            self._done_callbacks_lock.acquire()
            # There could be a new callback added to the list. In this case, just
            # continue, we will clean up when the new done callback is triggered.
            if len(self._done_callbacks[future]['list']) == 0:
                del(self._done_callbacks[future]['lock'])
                del(self._done_callbacks[future])
            self._done_callbacks_lock.release()
        else:
            self._done_callbacks_lock.release()

    def add_done_callback(self, future, callback, *args, **kwargs):
        """Adds a callback to the given future object.

        This function adds a callback that is executed when the future finishes
        its task. The callable is called with callback(*args, **kwargs),
        therefore it can simply be parameterized.
        Callbacks are executed in the same order in which they have been added.
        """
        self._done_callbacks_lock.acquire()
        if not future in self._done_callbacks.keys():
            self._done_callbacks[future] = {'lock': Lock(), 'list': []}

        # Lock in order to prevent race conditons
        self._done_callbacks[future]['lock'].acquire()
        self._done_callbacks[future]['list'].insert(0, (callback, args, kwargs))
        self._done_callbacks[future]['lock'].release()

        self._done_callbacks_lock.release()

        # This must not be locked! It would try to acquire the same locks we 
        # have hold here.
        future.add_done_callback(self.__done_callback)

    def __task_done(self, future):
        self._work_queue.task_done()

    def submit(self, fn, *args, **kwargs):
        """Note: This is a workaround that should be in place at least for
        python versions <= 3.5
        If this still applies to version 3.6 and later depends on
        http://bugs.python.org/issue28650
        """
        future = super(BetterThreadPoolExecutor, self).submit(fn, *args, **kwargs)
        if version_info.major <= 3 and version_info.minor <= 5:
            future.add_done_callback(self.__task_done)
        return future

    def get_remaining_tasks(self):
        """Returns the number of remaining tasks in the work queue.

        Note: This function accesses the number of remaining tasks unprotected.
        It might be wrong.
        """
        return self._work_queue.unfinished_tasks

    # TODO: Function to cleanup idle threads (e.g free down to max/2, max/4, ... threads)
    #  How ? There is no way to stop single (or specific) threads, since they simply execute
    # a long running while loop....
    # This would require larger changes.


    def _adjust_thread_count(self):
        """Note: This is a workaround that should be in place at least for
        python versions <= 3.5
        If this still applies to version 3.6 and later depends on
        http://bugs.python.org/issue28650
        """
        if version_info.major <= 3 and version_info.minor <= 5:
            if self._work_queue.unfinished_tasks > len(self._threads):
                super(BetterThreadPoolExecutor, self)._adjust_thread_count()
        else:
            super(BetterThreadPoolExecutor, self)._adjust_thread_count()


    def __init__(self, max_workers=None):
        super(BetterThreadPoolExecutor, self).__init__(max_workers)
        self._done_callbacks = {}
        self._done_callbacks_lock = Lock()

if __name__ == "__main__":
    def wait(a):
        time.sleep(3)
        print("%s is done" % a)
        return a

    def done(result, *args, **kwargs):
        print("done callback: type: %s\n\t%s\n\targs: %s\n\tkwargs: %s" % (
            type(result), str(result), str(args), str(kwargs)))

    executor = BetterThreadPoolExecutor(max_workers=4)
    a = executor.submit(wait, 1)
    executor.submit(wait, 2)
    b = executor.submit(wait, 3)
    executor.add_done_callback(b, done, 'a', 'b', c='foo')
    executor.add_done_callback(b, done, 'c', 'd', c='foo')
    time.sleep(5)
    c = executor.submit(wait, 4)
    executor.add_done_callback(c, done)
    print(a.result())
    print(b.result())
    print("waiting before new submit")
    time.sleep(10)
    print("restarting with new submit")
    b.add_done_callback(done)
    executor.add_done_callback(b, done, 'another callback 4 for b', c='foo')
    executor.add_done_callback(b, done, 'another callback 3 for b', c='foo')
    executor.add_done_callback(b, done, 'another callback 2 for b', c='foo')
    executor.add_done_callback(b, done, 'another callback 1 for b', c='foo')
    executor.submit(wait, 5)
    executor.submit(wait, 6)

    #print(a.result())
    executor.shutdown(True)
    print("shutdown")

    time.sleep(5)
    print("Done.")

