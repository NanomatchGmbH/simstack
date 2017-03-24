from __future__ import division
from PySide.QtCore import QObject, QTimer
from PySide.QtCore import QMutex
import time
import math
import sys

def least_common_multiple(a, b):
    return a * b // math.gcd(a, b)

def write_output(text):
    sys.stdout.write("\r%s" % text);
    sys.stdout.flush()

class ContinuousViewTimer(QObject):
    def add_callback(self, callback, interval):
        print("nrdnrd")
        interval = math.ceil(interval / self._base_tick)
        if not interval in self._interval_list:
            self._interval_list[interval] = []

        if not callback in self._interval_list[interval]:
            self._interval_list[interval] = {callback: 1}
            print("new list entry: %d" % interval)
        else:
            self._interval_list[interval][callback] += 1

        self.__update_max_tick(interval)

        if not self._timer.isActive():
            print("start timer")
            self._timer.start(self._base_tick)
        else:
            print("timerself._timer.isActive()")
            print(self._timer.isActive())

    def __update_max_tick(self, new_value):
        self._tick_max = least_common_multiple(self._tick_max, new_value)
        print("new max: %d" % self._tick_max)

    def remove_callback(self, interval, callback):
        if interval in self._interval_list:
            if callback in self._interval_list[interval]:
                self._interval_list[interval][callback] -= 1

                if self._interval_list[interval][callback] <= 0:
                    del(self._interval_list[interval][callback])

            # are there any callbacks for this interval left?
            if len(self._interval_list[interval]) == 0:
                del(self._interval_list[interval])
                self._recalc_max_tick=True

        # are there any callbacks left? if not, stop timer.
        if len(self._interval_list):
            self._timer.stop()


    def __timeout(self):
        print("timeout")
        recalc = False
        if self._recalc_max_tick and (self._tick_counter == 0):
            recalc = True
            self._tick_max = 1

        for freq in self._interval_list.keys():
            if self._tick_counter % freq == 0:
                for callback in self._interval_list[freq]:
                    callback()
            if recalc:
                self.__update_max_tick(freq)

        self._tick_counter = (self._tick_counter + 1) % self._tick_max

    def __init__(self, base_tick=100):
        super(ContinuousViewTimer, self).__init__()
        # must be locked:
        self._tick_counter=0
        self._tick_max=1
        self._interval_list={}
        self._recalc_max_tick = False
        ####

        self._timer = QTimer(self)
        self._base_tick=base_tick# * 10
        self._timer.timeout.connect(self.__timeout)
        self._timer.start(100)

#               #
# - - - - - - - - - - - - -
# |   |   |   |   |   |   |
# X       X       X       X
# *           *           *


if __name__ == "__main__":
    from PySide.QtCore import QCoreApplication, QThread
    import time

    def test1():
        print("1")
    def test2():
        print("2")

    def test3():
        print("3")

    class APP(QCoreApplication):
        def __init__(self):
            super(APP, self).__init__([])

            #self.timer = QTimer()
            #self.timer.timeout.connect(foo)
            #self.timer.start(1000)
            self.ct = ContinuousViewTimer()
            self.ct.add_callback(test1, 1000)
            self.ct.add_callback(test2, 2000)
            self.ct.add_callback(test3, 3000)
            super(APP, self).quit()

            print("App")
    class TestThread(QThread):
        def run(self):
            time.sleep(10)
            print("done")
            app.quit()

    app = APP()
    t = TestThread()
    t.start()
    sys.exit(app.exec_())

class ViewTimer(QObject):
    def __timeout(self):
        t = int(time.time())
        self._lock.lock()
        elapsed = t - self._last_timeout
        self._last_timeout = t

        if t >= self._due_time:
            if len(self._remaining_due_times) > 0:
                next_tick = self._remaining_due_times.pop()
                self._timer.setInterval(next_tick * 1000)
            else:
                self.stop()

        self._callback(int(elapsed))
        self._lock.unlock()

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
        t = int(time.time())
        self._lock.lock()
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
        self._lock.unlock()

    def __init__(self, callback):
        super(ViewTimer, self).__init__()
        self._timer = QTimer(self)
        self._callback = callback
        self._remaining_due_times = []
        self._due_time = -1
        self._last_timeout = -1
        self._lock = QMutex(QMutex.NonRecursive)

        self._timer.timeout.connect(self.__timeout)

