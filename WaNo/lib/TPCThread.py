import threading
from queue import Queue
from functools import wraps

class TPCThread(threading.Thread):
    @classmethod
    def _from_other_thread(cls, f):
        @wraps(f)
        def wrapper(self, *args, **kwargs):
            args = (self, ) + args
            self.command_queue.put(
                (f, args, kwargs)
            )
        return wrapper

    def on_exit(self):
        pass

    def on_command_executed(self, command, args, kwargs):
        pass

    def _check_stop_when_empty(self):
        return (self.stop_when_empty.isSet() and self.command_queue.empty)

    def run(self):
        while not self.stoprequest.isSet():
            command, args, kwargs = (None, None, None)
            exit = self._check_stop_when_empty()

            if not exit:
                try:
                    command, args, kwargs = self.command_queue.get(
                            block=True,
                            timeout=self.exit_timeout
                            )
                except Queue.Empty:
                    pass

            if not command is None and not exit:
                    command(*args, **kwargs)
                    self.on_command_executed(command, args, kwargs)
                    self.command_queue.task_done()
            try:
                if not exit:
                    command, args, kwargs = self.command_queue.get(
                            block=True,
                            timeout=self.exit_timeout
                            )
            except Queue.Empty:
                if not exit:
                    continue

        if not self.exit_callback is None:
            self.exit_callback[0](*self.exit_callback[1], *self.exit_callback[2])

    def join(self, timeout=None):
        self.stoprequest.set()
        # now we need to add something to the command queue.
        # otherwise the thread might wait for ever to do something...
        self.command_queue.put((self.on_exit, (), {}))
        super(TPCThread, self).join(timeout)

    def set_stop_when_empty(self):
        self.stop_when_empty.set()

    def set_exit_callback(self, callback, *args, **kwargs):
        self.exit_callback = (callback, args, kwargs)

    def set_exit_timeout(self, timeout):
        self.exit_timeout = timeout

    def __init__(self, exit_timeout=None):
        super(TPCThread, self).__init__()
        self.command_queue = Queue()

        self.exit_timeout = exit_timeout
        self.exit_callback = None
        self.daemon = True
        self.stoprequest = threading.Event()
        self.stop_when_empty = threading.Event()

