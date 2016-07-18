from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

from PySide.QtCore import QThread
from PySide.QtCore import Slot, Signal

class CallableQThread(QThread):
    pseudo_signal = Signal(object, object, object, name="pseudosignal")

    @Slot(object, object, object, name='pseudosignal')
    def pseudo_slot(self, function, args, kwargs):
        function(*args, *kwargs)

    @classmethod
    def callback(cls, a):
        def decorator(f):
            @wraps(f)
            def wrapper(self, *args, **kwargs):
                args = (self, ) + args
                self.pseudo_signal.emit(f, args, kwargs)
            return wrapper
        return decorator

    def start(self):
        super(CallableQThread, self).start()
        # This is crucial for slots of the Thread to be invoked in the thread's
        # context and not in the context of the emitting thread.
        self.moveToThread(self)

    def __init__(self):
        super(CallableQThread, self).__init__()
        self.pseudo_signal.connect(self.pseudo_slot)
