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
