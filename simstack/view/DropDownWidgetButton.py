from PySide6.QtWidgets import QToolButton, QListWidgetItem, QMenu, \
        QListWidget, QAbstractItemView, QWidgetAction, QPushButton



class _DropDownWidget(object):
    def _set_widget(self):
        self._action.setDefaultWidget(self._widget)
        self.menu().addAction(self._action)

    """Sets a widget that will be displayed in the drop down area of this
    DropDownWidgetToolButton.

    Args:
        widget: the widget to be displayed in this DropDownWidgetToolButton.
    """
    def set_widget(self, widget):
        if self._widget is None and not widget is None:
            self._widget = widget
            self._set_widget()

    def _init(self, widget=None, text=""):
        self._widget = None
        self._menu = QMenu(self)
        self.setMenu(self._menu)

        self.set_widget(widget)

        self._text = text
        self.setText(self._text)

        self._action = QWidgetAction(self)

    def __init__(self):
        pass


class DropDownWidgetToolButton(QToolButton, _DropDownWidget):

    """Constructs a DropDownWidgetToolButton.

    Args:
        parent: the parent of this Qt Gui element.
        widget: the widget to be displayed in this DropDownWidgetToolButton.
        text: the text displayed in the Button.
    """
    def __init__(self, parent, widget=None, text=""):
        super(DropDownWidgetToolButton, self).__init__()
        self.setPopupMode(QToolButton.MenuButtonPopup)
        self._init(widget, text)

class DropDownWidgetPushButton(QPushButton, _DropDownWidget):
    def __init__(self, parent, widget=None, text=""):
        super(DropDownWidgetPushButton, self).__init__()
        self._init(widget, text)

if __name__ == '__main__':
    import sys
    from PySide6.QtWidgets import QLabel, QWidget, QHBoxLayout, QApplication, QFileIconProvider
    app = QApplication(sys.argv)
    window = QWidget()
    label1 = QLabel("Test Label")
    label2 = QLabel("Test Label")

    layout = QHBoxLayout(window)

    mdl = DropDownWidgetToolButton(window, text="QToolButton")
    mdl.set_widget(label1)

    pdd = DropDownWidgetPushButton(window)
    pdd.set_widget(label2)
    pdd.setText("QPushButton")

    layout.addWidget(mdl)
    layout.addWidget(pdd)

    window.resize(100, 60)
    window.show()
    sys.exit(app.exec_())
