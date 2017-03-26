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
    def __lock(self):
        self._lock.lock()

    def __unlock(self):
        self._lock.unlock()

    def add_callback(self, callback, interval):
        """ Registers a callback that will be executed with a period of interval.

        Multiple registrations for the same callback and the same interval
        will result in just one single execution of the callback.

        .. note:: The execution time of the callback must be kept as short as
        possible.

        .. note:: Blocking call.
        """
        self.__lock()
        if not interval in self._interval_list:
            self._interval_list[interval] = []

        if not callback in self._interval_list[interval]:
            self._interval_list[interval] = {callback: 1}
        else:
            self._interval_list[interval][callback] += 1

        self.__update_max_tick(interval)

        if not self._timer.isActive():
            self._base_tick = interval
            self._timer.start(self._base_tick)
        else:
            # check, if the base_tick time must be shorter to satisfy new timer
            # requirements
            gcd = self.__recalc_base_tick(interval)
            if gcd < self._base_tick:
                if self._base_tick is None:
                    self._tick_counter *= self._base_tick / gcd
                else:
                    self._tick_counter = 0
                self._base_tick = gcd
                self._timer.setInterval(self._base_tick)
        self.__unlock()

    def __recalc_base_tick(self, new_value):
        """ Lock must be held."""
        return new_value if self._base_tick is None \
                else math.gcd(self._base_tick, new_value)

    def __update_max_tick(self, new_value):
        """ Lock must be held."""
        self._tick_max = least_common_multiple(self._tick_max, new_value)

    def remove_callback(self, callback, interval):
        """ Removes a callback registered with a specified interval.

        If a callback has been registered multiple times with the same interval,
        it has to be removed multiple times, too.

        .. note:: Blocking call.
        """
        self.__lock()
        if interval in self._interval_list:
            if callback in self._interval_list[interval]:
                self._interval_list[interval][callback] -= 1

                if self._interval_list[interval][callback] <= 0:
                    del(self._interval_list[interval][callback])

            # are there any callbacks for this interval left?
            if len(self._interval_list[interval]) == 0:
                del(self._interval_list[interval])
                self._recalc   = True

        # are there any callbacks left? if not, stop timer.
        if len(self._interval_list) == 0:
            self._timer.stop()
        self.__unlock()

    def __timeout(self):
        self.__lock()
        recalc = False
        if self._recalc and (self._tick_counter == 0):
            recalc = True
            self._recalc = False
            self._tick_max = 1
            self._base_tick = None
            current_interval = 0
        else:
            current_interval = self._tick_counter * self._base_tick

        for interval in self._interval_list.keys():
            if current_interval % interval == 0:
                for callback in self._interval_list[interval]:
                    callback()
            if recalc:
                self.__update_max_tick(interval)
                self._base_tick = self.__recalc_base_tick(interval)

        if recalc:
            self._timer.setInterval(self._base_tick)

        tick_max = self._tick_max / self._base_tick

        self._tick_counter = (self._tick_counter + 1) % tick_max
        self.__unlock()

    def __init__(self):
        """ Dynamic lightweight timer with support for multiple period lengths.

        This timer dynamically adapts its timer interval to the smallest interval
        that satisfies all requested cycle times. This avoids unnecessary ticks
        that will not lead to a callback being executed.

        .. note:: The timer itself is not threaded. The timer signal handler
        as well as the callbacks are executed within the surrounding thread
        context. Keep this in mind when registering callbacks.
        """
        super(ContinuousViewTimer, self).__init__()
        self._tick_counter  = 0
        self._tick_max      = 1
        self._interval_list = {}
        self._recalc        = False
        self._timer         = QTimer(self)
        self._base_tick     = None
        self._lock          = QMutex(QMutex.NonRecursive)

        self._timer.timeout.connect(self.__timeout)

if __name__ == "__main__":
    from PySide.QtCore import QCoreApplication, QThread
    import ctypes
    ptime = 0
    count = 0

    def test(i):
        global count
        global ptime
        now = time.time()
        diff = (now - ptime)
        print("%d (%04d): %s (tid: %d)" % (i, count,
                    "%2.5f" % diff if diff > 0.005 else "       ",
                    ctypes.CDLL('libc.so.6').syscall(186)))
        ptime = now
        count = count + 1
    def test1():
        test(1)
    def test2():
        test(2)
    def test3():
        test(3)

    class APP(QCoreApplication):
        def get_ct(self):
            return self.ct
        def __init__(self):
            super(APP, self).__init__([])

            print("App (tid: %d)" % ctypes.CDLL('libc.so.6').syscall(186))
            self.ct = ContinuousViewTimer()
            self.ct.add_callback(test3, 4000)
            self.ct.add_callback(test2, 2000)

    class TestThread(QThread):
        def run(self):
            print("run (tid: %d)" % ctypes.CDLL('libc.so.6').syscall(186))
            time.sleep(7)
            self.ct.add_callback(test1, 1000)
            time.sleep(4)
            self.ct.remove_callback(test1, 1000)
            time.sleep(10)
            print("done")
            app.quit()
        def __init__(self, ct):
            super(TestThread, self).__init__()
            self.ct = ct

    print("Start (tid: %d)" % ctypes.CDLL('libc.so.6').syscall(186))
    app = APP()
    t = TestThread(app.get_ct())
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

