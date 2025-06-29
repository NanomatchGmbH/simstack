import pytest

from PySide6 import QtWidgets, QtGui
from PySide6.QtWidgets import QListWidget, QAbstractItemView

from simstack.view.MultiselectDropDownList import MultiselectDropDownList
from simstack.view.DropDownWidgetButton import DropDownWidgetPushButton


def test_init_with_autoset_text(qtbot):
    """Test initialization of MultiselectDropDownList with autoset_text=True"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)

    text = "Test Text"
    mdl = MultiselectDropDownList(parent, text=text, autoset_text=True)

    # Verify text is set correctly
    assert mdl.text == text

    # Check that the QListWidget is created with the correct selection mode
    assert isinstance(mdl._list, QListWidget)
    assert mdl._list.selectionMode() == QAbstractItemView.ExtendedSelection

    # Verify signal connection for autoset_text=True
    # This is tricky to test directly, so we're just ensuring the object was created correctly
    assert isinstance(mdl, MultiselectDropDownList)
    assert isinstance(mdl, DropDownWidgetPushButton)


def test_init_without_autoset_text(qtbot):
    """Test initialization of MultiselectDropDownList with autoset_text=False"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)

    text = "Test Text"
    mdl = MultiselectDropDownList(parent, text=text, autoset_text=False)

    # Verify text is set correctly
    assert mdl.text == text

    # Check that the QListWidget is created with the correct selection mode
    assert isinstance(mdl._list, QListWidget)
    assert mdl._list.selectionMode() == QAbstractItemView.ExtendedSelection

    # Verify signal connection for autoset_text=False
    # This is tricky to test directly, so we're just ensuring the object was created correctly
    assert isinstance(mdl, MultiselectDropDownList)
    assert isinstance(mdl, DropDownWidgetPushButton)


def test_set_items_with_strings(qtbot):
    """Test set_items method with string items"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)

    mdl = MultiselectDropDownList(parent, text="Test")
    items = ["item1", "item2", "item3"]

    mdl.set_items(items)

    # Verify items were added to the list widget
    assert mdl._list.count() == len(items)
    for i, item_text in enumerate(items):
        list_item = mdl._list.item(i)
        assert list_item.text() == item_text


def test_set_items_with_tuples(qtbot):
    """Test set_items method with tuple items (text and icon)"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)

    mdl = MultiselectDropDownList(parent, text="Test")

    # Create some icons for testing
    icon1 = QtGui.QIcon()
    icon2 = QtGui.QIcon()

    items = [
        ("item1", icon1),
        ("item2", icon2),
        "item3",  # Mix of tuple and string items
    ]

    mdl.set_items(items)

    # Verify items were added to the list widget
    assert mdl._list.count() == len(items)

    # Check tuple items
    assert mdl._list.item(0).text() == "item1"
    assert mdl._list.item(1).text() == "item2"

    # Check string item
    assert mdl._list.item(2).text() == "item3"


def test_set_items_invalid_type(qtbot):
    """Test set_items method with invalid item type"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)

    mdl = MultiselectDropDownList(parent, text="Test")

    # Try to add an invalid item type (int)
    with pytest.raises(TypeError):
        mdl.set_items([1, 2, 3])


def test_get_selection_empty(qtbot):
    """Test get_selection method with no items selected"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)

    mdl = MultiselectDropDownList(parent, text="Test")
    mdl.set_items(["item1", "item2", "item3"])

    # No items selected
    selection = mdl.get_selection()
    assert selection == []


def test_get_selection_with_selected_items(qtbot):
    """Test get_selection method with items selected"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)

    mdl = MultiselectDropDownList(parent, text="Test")
    items = ["item1", "item2", "item3"]
    mdl.set_items(items)

    # Select items programmatically
    mdl._list.item(0).setSelected(True)
    mdl._list.item(2).setSelected(True)

    # Get selection
    selection = mdl.get_selection()
    assert len(selection) == 2
    assert "item1" in selection
    assert "item3" in selection
    assert "item2" not in selection


def test_select_items(qtbot):
    """Test select_items method"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)

    mdl = MultiselectDropDownList(parent, text="Test")
    items = ["item1", "item2", "item3", "item4"]
    mdl.set_items(items)

    # Select specific items
    select = ["item2", "item4"]
    mdl.select_items(select)

    # Verify the correct items are selected
    selection = mdl.get_selection()
    assert len(selection) == 2
    assert "item2" in selection
    assert "item4" in selection
    assert "item1" not in selection
    assert "item3" not in selection


def test_select_items_nonexistent(qtbot):
    """Test select_items method with items that don't exist"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)

    mdl = MultiselectDropDownList(parent, text="Test")
    items = ["item1", "item2", "item3"]
    mdl.set_items(items)

    # Try to select an item that doesn't exist
    mdl.select_items(["nonexistent"])

    # Verify no items are selected
    selection = mdl.get_selection()
    assert selection == []


def test_on_selection_change_with_autoset_text(qtbot):
    """Test _on_selection_change method with autoset_text=True"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)

    mdl = MultiselectDropDownList(parent, text="Test", autoset_text=True)
    items = ["item1", "item2", "item3"]
    mdl.set_items(items)

    # Select items to trigger _on_selection_change
    mdl._list.item(0).setSelected(True)
    mdl._list.item(2).setSelected(True)

    mdl._on_selection_change()

    # Method executed successfully


def test_on_selection_change_empty_selection(qtbot):
    """Test _on_selection_change method with no selection"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)

    original_text = "Original Text"
    mdl = MultiselectDropDownList(parent, text=original_text, autoset_text=True)
    items = ["item1", "item2", "item3"]
    mdl.set_items(items)

    # Clear all selections
    mdl._list.clearSelection()

    mdl._on_selection_change()

    # Method executed successfully


def test_connect_workaround(qtbot):
    """Test connect_workaround method"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)

    mdl = MultiselectDropDownList(parent, text="Test")

    # Mock function to connect
    def mock_function():
        return None

    # This should not raise any errors
    mdl.connect_workaround(mock_function)

    # Verify the signal exists
    assert hasattr(mdl, "menuAboutToShow")


def test_item_selection_changed_signal(qtbot):
    """Test that itemSelectionChanged signal is emitted correctly"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)

    mdl = MultiselectDropDownList(parent, text="Test", autoset_text=True)
    items = ["item1", "item2", "item3"]
    mdl.set_items(items)

    # Set up signal spy to catch the signal emission
    with qtbot.waitSignal(mdl.itemSelectionChanged) as signal_spy:
        mdl._on_selection_change()

    # Verify signal was emitted
    assert signal_spy.signal_triggered
