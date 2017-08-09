from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

from Qt.QtCore import QThread, QObject
from Qt.QtCore import Slot, Signal

from functools import wraps

class QThreadCallback(QObject):
    pseudo_signal = Signal(object, object, object, name="pseudosignal")

    @Slot(object, object, object, name='pseudosignal')
    def pseudo_slot(self, function, args, kwargs):
        function(*args, **kwargs)

    @classmethod
    def callback(cls, f):
        @wraps(f)
        def wrapper(self, *args, **kwargs):
            args = (self, ) + args
            self.pseudo_signal.emit(f, args, kwargs)
        return wrapper

    def __init__(self):
        super(QThreadCallback, self).__init__()
        self.pseudo_signal.connect(self.pseudo_slot)



class CallableQThread(QThreadCallback):
    def start(self):
        self.mythread.start()
        # This is crucial for slots of the Thread to be invoked in the thread's
        # context and not in the context of the emitting thread.
        self.moveToThread(self.mythread)

    def __init__(self):
        super(CallableQThread,self).__init__()
        self.mythread=QThread()

if __name__ == '__main__':
    aaa = QThreadCallback()
    bbb = CallableQThread()
