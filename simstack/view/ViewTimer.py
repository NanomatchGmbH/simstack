from PySide6.QtCore import QObject, QTimer
from PySide6.QtCore import QMutex
import time

class ViewTimer(QObject):
    def _unlock_list(self):
        self._lock.unlock()

    def _lock_list(self):
        self._lock.lock()

    def __timeout(self):
        t = int(time.time())
        self._lock_list()
        elapsed = t - self._last_timeout
        self._last_timeout = t

        if t >= self._due_time:
            if len(self._remaining_due_times) > 0:
                next_tick = self._remaining_due_times.pop()
                self._timer.setInterval(next_tick * 1000)
            else:
                self.stop()

        self._callback(int(elapsed))
        self._unlock_list()

    def __set_or_start(self, interval):
        i = interval * 1000

        if self._timer.isActive():
            self._timer.setInterval(i)
        else:
            self._timer.start(i)

    def stop(self):
        self._timer.stop()
        self._last_timeout = -1

    def update_interval(self, interval):
        print("######################################## timer update start.")
        t = int(time.time())
        self._lock_list()
        if self._timer.isActive():
            remainder = self._due_time - t - interval

            if remainder > 0:
                self._remaining_due_times.append(remainder)
                self._due_time = t + interval
                self.__set_or_start(interval)
            elif remainder < 0:
                self._remaining_due_times.insert(0, abs(remainder))
        else:
            self._due_time = t + interval
            self.__set_or_start(interval)

        if self._last_timeout < 0:
            self._last_timeout = t
        self._unlock_list()
        print("######################################## timer update finished.")

    def __init__(self, callback):
        super(ViewTimer, self).__init__()
        self._timer = QTimer(self)
        self._callback = callback
        self._remaining_due_times = []
        self._due_time = -1
        self._last_timeout = -1
        self._lock = QMutex()

        self._timer.timeout.connect(self.__timeout)

