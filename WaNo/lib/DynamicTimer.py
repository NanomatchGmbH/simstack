from __future__ import division
from PySide.QtCore import QObject, QTimer, QThread, Signal
from PySide.QtCore import QMutex
try:
    from .CallableQThread import CallableQThread
except:
    from CallableQThread import CallableQThread

from enum import Enum
import time
import math
import sys
import logging

# TODO Debug only
import ctypes
import threading

def least_common_multiple(a, b):
    return a * b // math.gcd(a, b)

def write_output(text):
    sys.stdout.write("\r%s" % text);
    sys.stdout.flush()

class DynamicTimer(QObject):
    OPS = Enum("OPS",
        """
        START
        STOP
        TERMINATE
        """,
        module=__name__
    )

    class TimerThread(CallableQThread):
        def timer_command(self, operation, tick=0):
            if operation == DynamicTimer.OPS.START:
                self._timer.start(tick)
            if operation == DynamicTimer.OPS.STOP:
                self._timer.stop()
            elif operation == DynamicTimer.OPS.TERMINATE:
                self._timer.stop()
                #TODO exit.
                self.quit()

        def run(self):
            self.exec_()

        def start(self):
            super(DynamicTimer.TimerThread, self).start()
            self._timer.moveToThread(self)

        def setInterval(self, interval):
            if not self._timer is None:
                self._timer.setInterval(interval)

        def isActive(self):
            return False if self._timer is None else self._timer.isActive()

        # NOTE: do not make this function "private" (leading __) or call the
        # DynamicTimer callback direct. For some reason, this will make Qt execute
        # the function outside the thread's context... -.-
        def _trigger_timeout_callback(self):
            self._timerout()

        def __init__(self, timeout_cb):
            super(DynamicTimer.TimerThread, self).__init__()
            self._timer = QTimer(None)
            self._timer.timeout.connect(self._trigger_timeout_callback)
            self._timerout = timeout_cb

    _timer_command = Signal(object, int, name="TimerCommand")

    def __lock(self):
        self._lock.lock()

    def __unlock(self):
        self._lock.unlock()

    def _start_timer(self, base_tick):
        if not self._timer_thread.isRunning():
            self._timer_thread.start()
        self._timer_command.emit(DynamicTimer.OPS.START, base_tick)

    def _stop_timer(self):
        self._timer_command.emit(DynamicTimer.OPS.STOP, 0)

    def _terminate_timer_thread(self):
        self._timer_command.emit(DynamicTimer.OPS.TERMINATE, 0)
        self._timer_thread.wait()
        self._logger.debug("Timer Thread terminated.")

    def quit(self):
        self._terminate_timer_thread()

    def add_callback(self, callback, interval):
        """ Registers a callback that will be executed with a period of interval.

        Multiple registrations for the same callback and the same interval
        will result in just one single execution of the callback.

        .. note:: The execution time of the callback must be kept as short as
        possible.

        .. note:: Blocking call.

        Args:
            callback (function) callback to execute periodically.
            interval (int) period time in ms.
        """
        self.__lock()
        if not interval in self._interval_list:
            self._interval_list[interval] = []

        if not callback in self._interval_list[interval]:
            self._interval_list[interval] = {callback: 1}
        else:
            self._interval_list[interval][callback] += 1

        self.__update_max_tick(interval)

        if not self._timer_thread.isActive():
            self._base_tick = interval
            self._start_timer(self._base_tick)
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
                self._timer_thread.setInterval(self._base_tick)
        self.__unlock()

    def __recalc_base_tick(self, new_value):
        """ Lock must be held."""
        return new_value if self._base_tick is None \
                else math.gcd(self._base_tick, new_value)

    def __update_max_tick(self, new_value):
        """ Lock must be held."""
        self._tick_max = least_common_multiple(self._tick_max, new_value)

    def remove_callback(self, callback, interval):
        """ Schedules a callback registered with a specified interval for lazy remove.

        Removal is done by decrementing the usage counter of the callback.
        Therefore, if this callback with this exact interval has been registered
        multiple times, it might persist this operation unless this function is
        called as many times as the callback has been inserted.

        .. note:: Removal will take place before the next timer event for this
            interval. However, if the interval this callback belongs to is
            currently being executed, the callback might be executed once more.
        .. note:: This call might block until all callbacks of the currently
            active intervall have been executed.

        Args:
            callback (function) callback to remove.
            interval (int) previously configured period time in ms.
        """

        cb_tuple = (callback, interval)

        self._delete_list_lock.lock()
        # Note: we abuse the dict's hash function to store our callback + interval
        # pairs. This allows for loockups in O(1) in average - yay!
        if cb_tuple in self._delete_list:
            self._delete_list[(callback, interval)] += 1
        else:
            self._delete_list[(callback, interval)] = 1
        self._delete_list_lock.unlock()

    def __remove_callbacks(self, del_list):
        """ .. note:: self._lock must be held."""
        self._logger.debug("DynamicTimer: __remove_callbacks: %d" %
                (ctypes.CDLL('libc.so.6').syscall(186)))
        for interval in del_list.keys():
            if interval in self._interval_list:
                for callback, count in del_list[interval]:
                    if callback in self._interval_list[interval]:
                        self._logger.debug("Decrementing cb usage counter by %d." % count)
                        # decrement usage counter
                        self._interval_list[interval][callback] -= count

                        # delete callback if unused
                        if self._interval_list[interval][callback] <= 0:
                            self._logger.debug("Removing cb, unused.")
                            del(self._interval_list[interval][callback])

                # are there any callbacks for this interval left?
                if len(self._interval_list[interval]) == 0:
                    self._logger.debug("Removing interval, unused.")
                    del(self._interval_list[interval])
                    self._recalc   = True
        # are there any callbacks left? if not, stop timer.
        if len(self._interval_list) == 0:
            self._logger.debug("Stopping timer, unused.")
            self._stop_timer()



    def __timeout(self):
        self._logger.debug("__timeout: %d" % (ctypes.CDLL('libc.so.6').syscall(186)))
        self.__lock()
        recalc = False
        del_list = {}
        del_count = 0 # stores the decrement for the ref counter of a callback scheduled for removal

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
                self._delete_list_lock.lock()

                for callback in self._interval_list[interval]:
                    del_count = 0
                    if (callback, interval) in self._delete_list:
                        del_count = self._delete_list[(callback, interval)]
                        if not interval in del_list:
                            del_list[interval] = [(callback, del_count)]
                        else:
                            del_list[interval].append((callback, del_count))

                        # TODO maybe set to 0?!
                        del(self._delete_list[(callback, interval)])

                    # will there be any instances left after removal?
                    # In that case, we can execute again
                    if self._interval_list[interval][callback] > del_count:
                        callback()

                self._delete_list_lock.unlock()
            if recalc:
                self.__update_max_tick(interval)
                self._base_tick = self.__recalc_base_tick(interval)

        if recalc:
            self._timer_thread.setInterval(self._base_tick)

        tick_max = self._tick_max / self._base_tick

        self._tick_counter = (self._tick_counter + 1) % tick_max

        self.__remove_callbacks(del_list)

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
        super(DynamicTimer, self).__init__()
        self._tick_counter  = 0
        self._tick_max      = 1
        self._interval_list = {}
        self._recalc        = False
        self._base_tick     = None
        self._lock          = QMutex(QMutex.NonRecursive)
        self._delete_list   = {}
        self._delete_list_lock = QMutex(QMutex.NonRecursive)
        self._timer_thread  = DynamicTimer.TimerThread(self.__timeout)

        self._timer_command.connect(self._timer_thread.timer_command)

        self._logger         = logging.getLogger("DynamicTimer")
        loglevel = logging.DEBUG
        self._logger.setLevel(loglevel)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(loglevel)
        self._logger.addHandler(ch)

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
        def get_timer(self):
            return self.dyntimer
        def __init__(self):
            super(APP, self).__init__([])

            print("App (tid: %d)" % ctypes.CDLL('libc.so.6').syscall(186))
            self.dyntimer = DynamicTimer()
            self.dyntimer.add_callback(test3, 4000)
            self.dyntimer.add_callback(test2, 2000)

    class TestThread(QThread):
        def run(self):
            print("run (tid: %d)" % ctypes.CDLL('libc.so.6').syscall(186))
            time.sleep(7)
            self.dyntimer.add_callback(test1, 1000)
            time.sleep(4)
            self.dyntimer.remove_callback(test1, 1000)
            time.sleep(10)
            print("done")
            self.dyntimer.quit()
            app.quit()
        def __init__(self, dyntimer):
            super(TestThread, self).__init__()
            self.dyntimer = dyntimer

    print("Start (tid: %d)" % ctypes.CDLL('libc.so.6').syscall(186))
    app = APP()
    t = TestThread(app.get_timer())
    t.start()
    sys.exit(app.exec_())


