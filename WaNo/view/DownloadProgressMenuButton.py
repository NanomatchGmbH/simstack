from PySide.QtGui import QWidget, QHBoxLayout, QPushButton, QProgressBar

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
        self.progress = QProgressBar()

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
    from PySide.QtGui import QApplication, QMainWindow
    import sys
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

    dlstatus = DummyDlStatus([
            {
                'id': 1,
                'from': 'from/test123',
                'to': 'to/to/test123',
                'total': 321,
                'progress': 23,
                'direction': 2
            },
            {
                'id': 3,
                'from': 'fooo',
                'to': 'bar',
                'total': 723,
                'progress': 723 * 0.982,
                'direction': 1
            },
            {
                'id': 13,
                'from': 'from/testtest',
                'to': 'to/to/testtest',
                'total': 2432,
                'progress': 2300,
                'direction': 1
            },
    ])

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
