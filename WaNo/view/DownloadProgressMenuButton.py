from Qt.QtWidgets import QWidget, QHBoxLayout, QPushButton, QProgressBar

try:
    from .DropDownWidgetButton import DropDownWidgetPushButton
    from .DownloadProgressWidget import DownloadProgressWidget
except:
    from DropDownWidgetButton import DropDownWidgetPushButton
    from DownloadProgressWidget import DownloadProgressWidget

class DownloadProgressMenuButton(DropDownWidgetPushButton):
    def __reset(self):
        self.progress.setMaximum(100)
        self.progress.setMinimum(0)
        self.set_progress_value(0)

    def __init__(self, parent, dlpw):
        super(DownloadProgressMenuButton, self).__init__(parent)
        self.progress = QProgressBar(self)

        self.__reset()

        # Enable / Disable progress Text
        #self.progress.setTextVisible(False)
        # Set margin to 0px, to move progress text over progress bar
        # self.progress.setStyleSheet('margin: 0px;')

        self._init_ui(dlpw)

    def _init_ui(self, dlpw):
        self.dlpw = dlpw

        self.setFlat(True)
        self.setStyleSheet(''
                'QPushButton::menu-indicator { image:  url(none.jpg); }' \
                'QPushButton { border: none; margin: 0px; padding: 0px; }'
                )

        self.layout = QHBoxLayout()
        self.layout.addWidget(self.progress)
        self.setLayout(self.layout)

        self.layout.setContentsMargins(0, 0, 0, 0)

        self.resize(self.sizeHint())
        self.set_widget(dlpw)

    def update(self):
        progress, total = self.dlpw.update()
        if total > 0:
            self.progress.setMaximum(total)
            self.set_progress_value(progress)
        else:
            self.__reset()

    def set_progress_value(self, value):
        self.progress.setValue(value)

if __name__ == '__main__':
    from Qt.QtWidgets import QApplication, QMainWindow
    import sys
    import os
    sys.path.append(os.path.join(os.path.abspath(os.path.curdir), 'WaNo'))

    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = os.path.abspath(os.path.join(dir_path,"../../external"))

    if not dir_path in sys.path:
        sys.path.append(dir_path)

    print(sys.path)
    from UnicoreState import UnicoreStateFactory
    from UnicoreState import UnicoreDataTransferStates
    from UnicoreState import UnicoreDataTransferDirection as Direction
    class DummyDlStatus(object):
        def get_list_iterator(self, key):
            if key in self.lists:
                l    = self.lists[key]['list']
                for i in l:
                    yield i

        def __init__(self, l=[]):
            self.lists = {'dl': {'list': l}}


    app = QApplication(sys.argv)
    window = QMainWindow()
    w = QWidget()
    layout = QHBoxLayout(w)

    dlstatus = UnicoreStateFactory.get_writer()
    dlstatus.add_registry(
            'testbase',
            'nouser',
            1)

    index = dlstatus.add_data_transfer(
            'testbase',
            'source1',
            'destination1',
            'storage',
            Direction.UPLOAD.value)
    transfer_state = dlstatus.get_data_transfer(
            'testbase', index)
    transfer_state.get_writer_instance().set_multiple_values({
            'total': 123,
            'progress': 0.7,
            'state': UnicoreDataTransferStates.RUNNING
        })
    #dlstatus.add_data_transfer(
    #        'testbase',
    #        'source2',
    #        'destination2',
    #        'storage',
    #        2)
    #dlstatus.add_data_transfer(
    #        'testbase',
    #        'source3',
    #        'destination3',
    #        'storage',
    #        0)

    w.setLayout(layout)
    window.setCentralWidget(w)


    window.statusBar().showMessage('Ready')

    dlpw = DownloadProgressWidget(window, dlstatus)

    b = DownloadProgressMenuButton(w, dlpw)
    b.set_progress_value(20)

    dlpw.update()

    window.statusBar().addPermanentWidget(b)

    window.resize(100, 60)
    window.show()
    sys.exit(app.exec_())
