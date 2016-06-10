from PySide.QtGui import QToolButton, QFontMetrics, QListWidgetItem, QMenu, \
        QListWidget, QAbstractItemView, QWidgetAction
from PySide.QtCore import Qt, Signal


class MultiselectDropDownList(QToolButton):
    itemSelectionChanged = Signal(name="itemSelectionChanged")

    def _on_selection_change(self):
        selected = self.get_selection()
        if len(selected) > 0:
            selected.sort()
            text = ', '.join(selected)
            fm = QFontMetrics(self.font())
            width = fm.width(text)
            shortened = fm.elidedText(
                    text,
                    Qt.ElideRight,
                    self.width() - 15) # -15 for width of the arrow
            self.setText(shortened)
        else:
            self.setText(self.text)
        self.itemSelectionChanged.emit()

    """Returns a list of strings of the selected items

    Returns:
        list of items
    """
    def get_selection(self):
        selectedItems = self._list.selectedItems()
        selected = []
        for s in selectedItems:
            selected.append(s.text())
        return selected

    """Selects items in the QListWidget according to a given list of strings.

    Args:
        items (str): List of item strings to select.
    """
    def select_items(self, items):
        for item in items:
            lwis = self._list.findItems(item, Qt.MatchFlag.MatchExactly)
            for lwi in lwis:
                lwi.setSelected(True)

    """Sets QListWidget items.

    Args:
        items (list): A list of either tuples of string and an icon types
            (QColor, QIcon or QPixmap) or strings
    """
    def set_items(self, items):
        self._list.clear()
        for item in items:
            if isinstance(item, tuple):
                lwi = QListWidgetItem(item[0])
                lwi.setData(Qt.ItemDataRole.DecorationRole, item[1])
                self._list.addItem(lwi)
            elif isinstance(item, str):
                self._list.addItem(item)
            else:
                raise TypeError("Item must be either tuple of string and \
                        an icon (QColor, QIcon or QPixmap) or string.")


    def connect_workaround(self,function):
        self.qmenu.aboutToShow.connect(function)

    """Constructs a MultiselectDropDownList.

    Args:
        parent: the parent of this Qt Gui element.
        text: the text displayed in the Button.
        autoset_text: if True, the text will be changed according to the selection
    """
    def __init__(self, parent, text="", autoset_text=False):
        QToolButton.__init__(self)
        self.setPopupMode(QToolButton.MenuButtonPopup)
        self.qmenu = QMenu(self)
        self.setMenu(self.qmenu)
        self.text = text
        self.setText(self.text)

        self._list = QListWidget(self)
        self._list.setSelectionMode(QAbstractItemView.ExtendedSelection)



        if autoset_text:
            self._list.itemSelectionChanged.connect(self._on_selection_change)
        else:
            self._list.itemSelectionChanged.connect(self.itemSelectionChanged)

        action = QWidgetAction(self)
        action.setDefaultWidget(self._list)

        self.menu().addAction(action)

if __name__ == '__main__':
    import sys
    from PySide.QtGui import QWidget, QHBoxLayout, QApplication, QFileIconProvider
    app = QApplication(sys.argv)
    window = QWidget()

    layout = QHBoxLayout(window)

    mdl = MultiselectDropDownList(window, text="foooobar", autoset_text=True)
    mdl.set_items(['foo', 'bar', ('abc', QFileIconProvider().icon(QFileIconProvider.Folder))]) 
    mdl.select_items(['foo', 'abc'])

    layout.addWidget(mdl)

    window.resize(100, 60)
    window.show()
    sys.exit(app.exec_())
