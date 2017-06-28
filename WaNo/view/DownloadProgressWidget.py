#from WaNo.lib.DropDownWidgetToolButton import DropDownWidgetToolButton

from PySide.QtGui import QWidget, QGridLayout, QProgressBar, QLabel, QIcon, \
        QFrame, QSizePolicy, QPalette, QListWidget, QListWidgetItem, \
		QHBoxLayout, QPalette, QColor
from PySide.QtCore import QSize, Qt

from enum import Enum
from os.path import basename

from ..UnicoreState import UnicoreDataTransferStates

class Download(QWidget):
    DIRECTION = Enum("DLDirection",
            """
            UP
            DOWN
            """)
    DONE_THRESHOLD = 0.98

    def _get_icon(self):
        icon = None
        if (self._direction == self.DIRECTION.UP):
            icon = QIcon.fromTheme('network-transmit',
                    QIcon('./WaNo/Media/icons/upload.png'))
        else:
            icon = QIcon.fromTheme('network-transmit-receive',
                    QIcon('./WaNo/Media/icons/download.png'))
        return icon

    def _set_done(self):
        icon = self._get_icon()
        self._icon.setPixmap(icon.pixmap(self._size, QIcon.Disabled, QIcon.On))
        self._progressbar.setEnabled(False)

        palette = QPalette(self._progressbar.palette())
        palette.setColor(QPalette.Highlight, QColor(Qt.gray))
        self._progressbar.setPalette(palette)

        self._progressbar.setValue(self._total)
        self._done = True

    def is_done(self):
        return self._done

    def set_progress(self, progress, total=None):
        """ Sets the transfer progress.

        The optional total parameter can be used to correct the total value
        set in the constructor. This is usefull in cases when the widget is
        constructed before the total is known.
        Only values larger than the previously set ones are allowed.

        Args:
            progress (float): current progress of the transfer.
            total (float):    total file size.
        """
        self._progress = progress
        if not total is None and total > self._total:
            self._total = total
            self._progressbar.setMaximum(self._total)

        if self._progress >= self._total * self.DONE_THRESHOLD:
            self._set_done()
        else:
            self._progressbar.setValue(self._progress)

    def _init_ui(self):
        self._layout    = QGridLayout(self)

        self._progressbar = QProgressBar(self)
        self._progressbar.setMaximum(self._total)
        # Explicitly setting value, so '0%' is displayed initially.
        self._progressbar.setValue(0)

        self._label     = QLabel(basename(self._to_path), self)
        self._icon      = QLabel()
        self._icon.setAlignment(Qt.AlignCenter)
        self._icon.setFrameShape(QFrame.Box)
        self._icon.setBackgroundRole(QPalette.Base)
        self._icon.setAutoFillBackground(True)

        self._size = QSize(32, 32)

        self._icon.setMinimumSize(self._size)
        self._icon.setMaximumSize(self._size)

        icon = self._get_icon()
        self._icon.setPixmap(icon.pixmap(self._size, QIcon.Active, QIcon.On))

        self._layout.addWidget(self._icon, 0, 0, 2, 1)
        self._layout.addWidget(self._label, 0, 1)
        self._layout.addWidget(self._progressbar, 1, 1)

        self.setToolTip(
                '<table>' \
                '<tr><td><b>From:</b></td><td>%s</td></tr>' \
                '<tr><td><b>To:</b></td><td>%s</td></tr>'\
                '<tr><td><b>File size:</b></td><td>%d</td></tr>' \
                '<tr><td><b>Direction:</b></td><td>%s</td></tr>' \
                '</table>' % \
                (self._from_path, self._to_path, self._total, self._direction.name))

    def __init__(self, from_path, to_path, total, direction):
        super(Download, self).__init__()
        
        self._from_path = from_path
        if not to_path is None and not to_path == "":
            self._to_path = to_path
        else:
            self._to_path = basename(from_path)
        self._direction = direction
        self._total     = total
        self._done      = False
        self._progress  = 0

        self._init_ui()


class DownloadProgressWidget(QWidget):
    def _create_add_widget(self, index, dl):
        widget = Download(
                dl['source'],
                dl['dest'],
                dl['total'],
                Download.DIRECTION(dl['direction']))
        item = QListWidgetItem()
        item.setSizeHint(widget.sizeHint())
        self._list.addItem(item)
        self._list.setItemWidget(item, widget)
        self._downloads[index] = {'widget': widget, 'item': item}
        return widget

    def _sort(self):
        #TODO why is this not working???
        first_done = None
        for i, dlk in enumerate(self._downloads.keys()):
            item = self._downloads[dlk]['item']
            widget = self._downloads[dlk]['widget']
            if widget.is_done() and first_done is None:
                first_done = i
                print('first done: %d' % i)
                item = self._list.takeItem(i)
                self._list.insertItem(2, item)
            else:
                if not first_done is None:
                    print('moving %d to %d' % (i, first_done - 1))
                    item = self._list.takeItem(i)
                    new = first_done
                    tmp  = self._list.takeItem(new)
                    self._list.insertItem(new, item)
                    self._list.insertItem(i, tmp)

    @staticmethod
    def _dl_active(dl):
        """ Returns True, if the transfer is active (state is running) """
        return (dl['state'] == UnicoreDataTransferStates.RUNNING)

    @staticmethod
    def _dl_ended(dl):
        """ Returs True, if the transfer has ended (state is done, failed or
        canceled)."""
        return (not DownloadProgressWidget._dl_active(dl)
                and dl['state'] != UnicoreDataTransferStates.PENDING)

    def update(self):
        active_total       = 0
        active_progress    = 0
        #TODO protect from concurent runs.
        if not self.download_status is None:
            for (index, download) in self.download_status.data_transfer_iterator():
                print("index %d, download: %s" % (index, str(download)))
                with download.get_reader_instance() as dl:

                    widget = None
                    if index in self._downloads:
                        widget = self._downloads[index]['widget']
                    else:
                        widget = self._create_add_widget(index, dl)

                    # only update if the transfer is active or about to end.
                    # Pending transfers do not need updates.
                    if not widget is None \
                            and (DownloadProgressWidget._dl_active(dl) \
                                or (DownloadProgressWidget._dl_ended(dl) \
                                    and not widget.is_done())) :
                        widget.set_progress(dl['progress'], dl['total'])
                        active_total       += dl['total'] if dl['total'] >= 0 else 0
                        active_progress    += dl['progress']
            #TODO self._sort()
        return (active_progress, active_total)

    def set_download_status(self, download_status):
        if not download_status is None:
            self.download_status = download_status

    def _init_ui(self):
        self._layout = QHBoxLayout(self)
        self._list.resize(self._list.sizeHint())
        self._layout.addWidget(self._list)

    def __init__(self, parent, download_status=None):
        QWidget.__init__(self, parent)
        self.set_download_status(download_status)
        self._downloads = {}
        self._list = QListWidget(self)
        self._init_ui()

if __name__ == '__main__':
    import sys
    from PySide.QtGui import QWidget, QHBoxLayout, QApplication, QFileIconProvider
    class DummyDlStatus(object):
        def get_list_iterator(self, key):
            if key in self.lists:
                l    = self.lists[key]['list']
                for i in l:
                    yield i

        def __init__(self, l=[]):
            self.lists = {'dl': {'list': l}}

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
                'id': 13,
                'from': 'from/testtest',
                'to': 'to/to/testtest',
                'total': 2432,
                'progress': 2300,
                'direction': 1
            }
    ])
    app = QApplication(sys.argv)
    window = QWidget()
    layout = QHBoxLayout(window)

    #w = Download("from_path", "to_path", 324, Download.DIRECTION.UP)
    #layout.addWidget(w)

    l = DownloadProgressWidget(window, dlstatus)
    layout.addWidget(l)
    l.update()

    window.resize(100, 60)
    window.show()
    sys.exit(app.exec_())
