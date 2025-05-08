from PySide6.QtWidgets import (
    QListWidgetItem,
    QListWidget,
    QAbstractItemView,
    QFileIconProvider,
)
from PySide6.QtGui import QFontMetrics
from PySide6.QtCore import Qt, Signal


try:
    from .DropDownWidgetButton import DropDownWidgetPushButton
except:
    from DropDownWidgetButton import DropDownWidgetPushButton


class MultiselectDropDownList(DropDownWidgetPushButton):
    itemSelectionChanged = Signal(name="itemSelectionChanged")
    menuAboutToShow = Signal(name="menuAboutToShow")

    def _on_selection_change(self):
        selected = self.get_selection()
        if len(selected) > 0:
            selected.sort()
            text = ", ".join(selected)
            fm = QFontMetrics(self.font())
            width = fm.width(text)
            shortened = fm.elidedText(
                text, Qt.ElideRight, self.width() - 15
            )  # -15 for width of the arrow
            self.setText(shortened)
        else:
            self.setText(self.text)
        self.itemSelectionChanged.emit(self)

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
                raise TypeError(
                    "Item must be either tuple of string and \
                        an icon (QColor, QIcon or QPixmap) or string."
                )

    def connect_workaround(self, function):
        self.menuAboutToShow.connect(function)

    """Constructs a MultiselectDropDownList.

    Args:
        parent: the parent of this Qt Gui element.
        text: the text displayed in the Button.
        autoset_text: if True, the text will be changed according to the selection
    """

    def __init__(self, parent, text="", autoset_text=False):
        super(MultiselectDropDownList, self).__init__(parent, text=text)
        self.text = text

        self._list = QListWidget(self)
        self._list.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self._menu.aboutToShow.connect(self.menuAboutToShow)

        if autoset_text:
            self._list.itemSelectionChanged.connect(self._on_selection_change)
        else:
            self._list.itemSelectionChanged.connect(self.itemSelectionChanged)

        self.set_widget(self._list)


if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import (
        QWidget,
        QHBoxLayout,
        QApplication,
        QLabel,
        QFileIconProvider,
    )

    app = QApplication(sys.argv)
    window = QWidget()

    layout = QHBoxLayout(window)

    mdl_autoset = MultiselectDropDownList(window, text="foooobar", autoset_text=True)
    mdl_autoset.set_items(
        ["foo", "bar", ("abc", QFileIconProvider().icon(QFileIconProvider.Folder))]
    )
    mdl_autoset.select_items(["foo", "abc"])

    mdl = MultiselectDropDownList(window, text="foooobar", autoset_text=False)
    mdl.set_items(
        [
            "foo",
            "bar",
            "test",
            ("abc", QFileIconProvider().icon(QFileIconProvider.Folder)),
        ]
    )
    mdl.select_items(["bar", "test"])

    layout.addWidget(QLabel("Autoset Text:"))
    layout.addWidget(mdl_autoset)
    layout.addWidget(QLabel("Without Autoset Text:"))
    layout.addWidget(mdl)

    window.resize(100, 60)
    window.show()
    sys.exit(app.exec_())
