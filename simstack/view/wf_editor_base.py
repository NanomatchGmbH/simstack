import abc
import posixpath

import PySide6.QtCore as QtCore
import PySide6.QtGui as QtGui


widgetColors = {
    "MainEditor": "#F5FFF5",
    "Control": "#EBFFD6",
    "Base": "#F5FFEB",
    "WaNo": "#FF00FF",
    "ButtonColor": "#D4FF7F",
}


def linuxjoin(*args, **kwargs):
    return posixpath.join(*args, **kwargs)


class DragDropTargetTracker(object):
    def manual_init(self):
        self._initial_parent = self.parent()

    @abc.abstractmethod
    def parent(self):
        pass

    def _target_tracker(self, event):
        self._newparent = event

    def mouseMoveEvent_feature(self, e):
        if e.buttons() != QtCore.Qt.LeftButton:
            return

        # self.parent().removeElement(self)
        mimeData = QtCore.QMimeData()
        self.drag = QtGui.QDrag(self)
        self.drag.setMimeData(mimeData)
        self.drag.setHotSpot(e.pos() - self.rect().topLeft())
        # self.move(e.globalPos())
        self.drag.targetChanged.connect(self._target_tracker)
        self._newparent = self.parent()
        self.drag.exec_(QtCore.Qt.MoveAction)

        # In case the target of the drop changed we are outside the workflow editor
        # In that case we would like to remove ourselves
        if self._newparent is None:
            self.parent().removeElement(self.model)
            self.model.view.deleteLater()
        elif self._newparent == self._initial_parent:
            # Nothing to be done
            pass
        else:
            # In this case we assume both types have "correct" dropevents
            # print("Passing")
            pass