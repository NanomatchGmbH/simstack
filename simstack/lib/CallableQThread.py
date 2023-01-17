from Qt.QtCore import QThread, QObject
from Qt.QtCore import Slot, Signal

from functools import wraps
import sys

class QThreadCallback(QThread):
    pseudo_signal = Signal(object, object, object, name="pseudosignal")

    @Slot(object, object, object, name='pseudosignal')
    def pseudo_slot(self, function, args, kwargs):
        function(*args, **kwargs)

    def __init__(self):
        super(QThreadCallback, self).__init__()
        self.pseudo_signal.connect(self.pseudo_slot)

    def run(self):
        try:
            super(QThreadCallback,self).run()
        except NameError as exc:
            sys.stderr.write( "Name Error\n",exc );
        except:
            (type, value, traceback) = sys.exc_info()
            sys.excepthook(type, value, traceback)


class CallableQThread(QThreadCallback):
    def start(self):
        super(CallableQThread,self).start()
        # This is crucial for slots of the Thread to be invoked in the thread's
        # context and not in the context of the emitting thread.
        self.moveToThread(self)

    def __init__(self):
        super(CallableQThread,self).__init__()

if __name__ == '__main__':
    aaa = QThreadCallback()
    bbb = CallableQThread()
