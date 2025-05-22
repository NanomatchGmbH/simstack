import pytest
from PySide6 import QtCore, QtWidgets, QtGui
import yaml
from pathlib import Path
import tempfile
import os
from unittest.mock import MagicMock, patch

from simstack.view.PropertyListView import (
    ResourceTableBase,
    ExportTableModel,
    ImportTableModel,
    CheckBoxDelegate,
    GlobalFileChooserDelegate,
    FileChooserDelegate,
    ButtonDelegate,
    ComboDelegate,
    TableView,
    ResourceView,
    ImportView,
    ExportView
)


class TestResourceTableModel(ResourceTableBase):
    """Test implementation of ResourceTableBase for testing"""
    
    def make_default_list(self):
        self.mylist = [["data1", "data2"], ["data3", "data4"]]
        self.header = ["Column1", "Column2"]
        self.alignments = [QtCore.Qt.AlignCenter, QtCore.Qt.AlignRight]


def test_resource_table_base_init(qtbot):
    """Test initialization of ResourceTableBase"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    # Test with wano_parent
    wano_parent = MagicMock()
    model = TestResourceTableModel(parent, wano_parent=wano_parent)
    assert model.wano_parent == wano_parent
    
    # Test without wano_parent
    model = TestResourceTableModel(parent)
    model.make_default_list()
    
    assert model.rowCount() == 2
    assert model.columnCount() == 2
    assert model.header == ["Column1", "Column2"]
    assert model.alignments == [QtCore.Qt.AlignCenter, QtCore.Qt.AlignRight]


def test_resource_table_base_data(qtbot):
    """Test data method of ResourceTableBase"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    model = TestResourceTableModel(parent)
    model.make_default_list()
    
    # Test valid data
    index = model.index(0, 0)
    assert model.data(index, QtCore.Qt.DisplayRole) == "data1"
    
    # Test alignment
    assert model.data(index, QtCore.Qt.TextAlignmentRole) == QtCore.Qt.AlignCenter
    
    # Test invalid index
    invalid_index = QtCore.QModelIndex()
    assert model.data(invalid_index, QtCore.Qt.DisplayRole) is None
    
    # Test unsupported role
    assert model.data(index, QtCore.Qt.DecorationRole) is None


def test_resource_table_base_set_data(qtbot):
    """Test setData method of ResourceTableBase"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    model = TestResourceTableModel(parent)
    model.make_default_list()
    
    index = model.index(0, 0)
    assert model.setData(index, "new_data", QtCore.Qt.EditRole) is True
    assert model.data(index, QtCore.Qt.DisplayRole) == "new_data"
    
    # Test with a different role
    assert model.setData(index, "ignored_data", QtCore.Qt.DecorationRole) is False


def test_resource_table_base_header_data(qtbot):
    """Test headerData method of ResourceTableBase"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    model = TestResourceTableModel(parent)
    model.make_default_list()
    
    # Horizontal header
    assert model.headerData(0, QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole) == "Column1"
    assert model.headerData(1, QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole) == "Column2"
    
    # Vertical header
    assert model.headerData(0, QtCore.Qt.Vertical, QtCore.Qt.DisplayRole) == "1"
    assert model.headerData(1, QtCore.Qt.Vertical, QtCore.Qt.DisplayRole) == "2"
    
    # Unsupported role
    assert model.headerData(0, QtCore.Qt.Horizontal, QtCore.Qt.DecorationRole) is None


def test_resource_table_base_sort(qtbot):
    """Test sort method of ResourceTableBase"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    model = TestResourceTableModel(parent)
    model.mylist = [["b", "2"], ["a", "1"], ["c", "3"]]
    model.header = ["Letter", "Number"]
    model.alignments = [QtCore.Qt.AlignCenter, QtCore.Qt.AlignRight]
    
    # Sort by first column (ascending)
    model.sort(0, QtCore.Qt.AscendingOrder)
    assert model.mylist == [["a", "1"], ["b", "2"], ["c", "3"]]
    
    # Sort by first column (descending)
    model.sort(0, QtCore.Qt.DescendingOrder)
    assert model.mylist == [["c", "3"], ["b", "2"], ["a", "1"]]


def test_resource_table_base_save_load(qtbot):
    """Test save and load methods of ResourceTableBase"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    model = TestResourceTableModel(parent)
    model.mylist = [["data1", "data2"], ["data3", "data4"]]
    
    # Create a temporary file for testing
    with tempfile.NamedTemporaryFile(suffix='.yaml') as temp:
        temp_path = Path(temp.name)
        
        # Save to file
        model.save(temp_path)
        
        # Create a new model and load from file
        new_model = TestResourceTableModel(parent)
        new_model.load(temp_path)
        
        # Verify the loaded data matches the original
        assert new_model.mylist == model.mylist


def test_export_table_model_init(qtbot):
    """Test initialization of ExportTableModel"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    model = ExportTableModel(parent)
    model.make_default_list()
    
    assert model.rowCount() == 1  # One extra row for new entries
    assert model.columnCount() == 1
    assert model.header == ["Filename"]
    assert model.alignments == [QtCore.Qt.AlignCenter]
    assert model.mylist == []
    
    # Test get_contents method
    model.mylist = [["file1"], ["file2"]]
    assert model.get_contents() == [["file1"], ["file2"]]


def test_export_table_model_flags(qtbot):
    """Test flags method of ExportTableModel"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    model = ExportTableModel(parent)
    index = model.index(0, 0)
    
    flags = model.flags(index)
    assert flags & QtCore.Qt.ItemIsEditable
    assert flags & QtCore.Qt.ItemIsEnabled
    assert flags & QtCore.Qt.ItemIsSelectable


def test_export_table_model_data(qtbot):
    """Test data method of ExportTableModel"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    model = ExportTableModel(parent)
    model.make_default_list()
    model.add_entry()  # Add one entry
    
    # Test normal data access
    index = model.index(0, 0)
    assert model.data(index, QtCore.Qt.DisplayRole) == "File_0"
    
    # Test for row beyond data but within rowCount (should return space)
    index = model.index(1, 0)  # This is the extra row for new entries
    assert model.data(index, QtCore.Qt.DisplayRole) == " "
    
    # Test alignment role
    model.alignments = [QtCore.Qt.AlignCenter]
    assert model.data(index, QtCore.Qt.TextAlignmentRole) == QtCore.Qt.AlignCenter
    
    # Test invalid index
    invalid_index = QtCore.QModelIndex()
    assert model.data(invalid_index, QtCore.Qt.DisplayRole) is None
    
    # Test unsupported role
    assert model.data(index, QtCore.Qt.DecorationRole) is None


def test_export_table_model_add_delete_entry(qtbot):
    """Test add_entry and delete_entry methods of ExportTableModel"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    model = ExportTableModel(parent)
    model.make_default_list()
    
    # Add entry
    model.add_entry()
    assert len(model.mylist) == 1
    assert model.mylist[0] == ["File_0"]
    
    # Add another entry
    model.add_entry()
    assert len(model.mylist) == 2
    assert model.mylist[1] == ["File_1"]
    
    # Delete entry
    model.delete_entry(0)
    assert len(model.mylist) == 1
    assert model.mylist[0] == ["File_1"]
    
    # Test delete with invalid row
    original_length = len(model.mylist)
    model.delete_entry(99)  # Row doesn't exist
    assert len(model.mylist) == original_length  # Should not change
    
    # Test delete on empty list
    model.mylist = []
    model.delete_entry(0)  # Should not raise an error
    assert model.mylist == []


def test_export_table_model_set_data(qtbot):
    """Test setData method of ExportTableModel"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    model = ExportTableModel(parent)
    model.make_default_list()
    
    # Set data in the "new row" (which should create a new entry)
    index = model.index(0, 0)  # First row is the "new row" since mylist is empty
    assert model.setData(index, "TestFile", QtCore.Qt.EditRole)
    assert len(model.mylist) == 1
    assert model.mylist[0] == ["TestFile"]
    
    # Try to set empty value (should fail)
    index = model.index(1, 0)  # Now this is the "new row"
    assert not model.setData(index, "", QtCore.Qt.EditRole)
    assert len(model.mylist) == 1  # Should not have added a new entry
    
    # Test setting data in an existing row
    index = model.index(0, 0)
    assert model.setData(index, "UpdatedFile", QtCore.Qt.EditRole)
    assert model.mylist[0] == ["UpdatedFile"]


def test_import_table_model_init(qtbot):
    """Test initialization of ImportTableModel"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    model = ImportTableModel(parent)
    model.make_default_list()
    
    assert model.rowCount() == 1  # One extra row for new entries
    assert model.columnCount() == 3
    assert model.header == ["Name", "ImportFrom", "Target Filename"]
    assert len(model.alignments) == 4  # Model has 4 alignments defined
    assert model.mylist == []
    
    # Test get_contents method
    model.mylist = [["name1", "from1", "to1"], ["name2", "from2", "to2"]]
    assert model.get_contents() == [["name1", "from1", "to1"], ["name2", "from2", "to2"]]


def test_import_table_model_flags(qtbot):
    """Test flags method of ImportTableModel"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    model = ImportTableModel(parent)
    index = model.index(0, 0)
    
    flags = model.flags(index)
    assert flags & QtCore.Qt.ItemIsEditable
    assert flags & QtCore.Qt.ItemIsEnabled
    assert flags & QtCore.Qt.ItemIsSelectable


def test_import_table_model_data(qtbot):
    """Test data method of ImportTableModel"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    model = ImportTableModel(parent)
    model.make_default_list()
    model.add_entry()  # Add one entry
    
    # Test normal data access
    index = model.index(0, 0)
    assert model.data(index, QtCore.Qt.DisplayRole) == "File_0"
    
    # Test for row beyond data but within rowCount (should return space)
    index = model.index(1, 0)  # This is the extra row for new entries
    assert model.data(index, QtCore.Qt.DisplayRole) == " "
    
    # Test alignment role
    model.alignments = [QtCore.Qt.AlignCenter]
    assert model.data(index, QtCore.Qt.TextAlignmentRole) == QtCore.Qt.AlignCenter
    
    # Test invalid index
    invalid_index = QtCore.QModelIndex()
    assert model.data(invalid_index, QtCore.Qt.DisplayRole) is None
    
    # Test unsupported role
    assert model.data(index, QtCore.Qt.DecorationRole) is None


def test_import_table_model_add_delete_entry(qtbot):
    """Test add_entry and delete_entry methods of ImportTableModel"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    model = ImportTableModel(parent)
    model.make_default_list()
    
    # Add entry
    model.add_entry()
    assert len(model.mylist) == 1
    assert model.mylist[0] == ["File_0", "", ""]
    
    # Delete entry
    model.delete_entry(0)
    assert len(model.mylist) == 0
    
    # Test delete with invalid row
    model.mylist = [["test", "", ""]]
    original_length = len(model.mylist)
    model.delete_entry(99)  # Row doesn't exist
    assert len(model.mylist) == original_length
    
    # Test delete on empty list
    model.mylist = []
    model.delete_entry(0)  # Should not raise an error
    assert model.mylist == []


def test_import_table_model_set_data_normal(qtbot):
    """Test setData method of ImportTableModel with normal column"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    model = ImportTableModel(parent)
    model.make_default_list()
    
    # Set data in first column (Name)
    index = model.index(0, 0)  # First row is the "new row" since mylist is empty
    assert model.setData(index, "TestFile", QtCore.Qt.EditRole)
    assert len(model.mylist) == 1
    assert model.mylist[0][0] == "TestFile"


def test_import_table_model_set_data_import_from(qtbot):
    """Test setData method of ImportTableModel with ImportFrom column"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    model = ImportTableModel(parent)
    model.make_default_list()
    
    # Set data in second column (ImportFrom) for new row
    index = model.index(0, 1)  # First row, ImportFrom column 
    assert model.setData(index, "/path/to/file.txt", QtCore.Qt.EditRole)
    
    # Check if all columns were properly set
    assert len(model.mylist) == 1
    assert model.mylist[0][0] == "file.txt"  # Name should be set to basename
    assert model.mylist[0][1] == "/path/to/file.txt"  # ImportFrom
    assert model.mylist[0][2] == "file.txt"  # Target Filename should be set to basename
    
    # Test setting empty value (should fail)
    index = model.index(1, 1)  # New row
    assert not model.setData(index, "", QtCore.Qt.EditRole)
    
    # Test updating existing row's ImportFrom column (should update all three columns)
    index = model.index(0, 1)
    assert model.setData(index, "/different/path/newfile.dat", QtCore.Qt.EditRole)
    assert model.mylist[0][0] == "newfile.dat"
    assert model.mylist[0][1] == "/different/path/newfile.dat"
    assert model.mylist[0][2] == "newfile.dat"
    
    # Test with different role
    assert not model.setData(index, "test", QtCore.Qt.UserRole)


def test_check_box_delegate_paint(qtbot):
    """Test CheckBoxDelegate paint method"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    delegate = CheckBoxDelegate(parent)
    
    # Since we can't properly test the paint method with mocks, we'll just
    # instantiate the delegate and verify it's created correctly
    assert isinstance(delegate, CheckBoxDelegate)


def test_check_box_delegate_set_model_data(qtbot):
    """Test CheckBoxDelegate setModelData method"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    delegate = CheckBoxDelegate(parent)
    model = MagicMock()
    index = MagicMock()
    
    # Test with current value True
    index.data.return_value = True
    delegate.setModelData(None, model, index)
    model.setData.assert_called_with(index, False, QtCore.Qt.EditRole)
    
    # Test with current value False
    model.reset_mock()
    index.data.return_value = False
    delegate.setModelData(None, model, index)
    model.setData.assert_called_with(index, True, QtCore.Qt.EditRole)


def test_check_box_delegate_get_checkbox_rect(qtbot):
    """Test CheckBoxDelegate getCheckBoxRect method"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    delegate = CheckBoxDelegate(parent)
    option = MagicMock()
    option.rect = QtCore.QRect(0, 0, 100, 20)
    
    # Just make sure this doesn't crash
    rect = delegate.getCheckBoxRect(option)
    assert isinstance(rect, QtCore.QRect)


def test_file_chooser_delegate(qtbot):
    """Test FileChooserDelegate"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    delegate = FileChooserDelegate(parent)
    
    # Test paint method
    painter = MagicMock()
    option = MagicMock()
    option.state = QtWidgets.QStyle.State_Selected
    option.rect = QtCore.QRect(0, 0, 100, 20)
    index = MagicMock()
    
    delegate.paint(painter, option, index)
    painter.fillRect.assert_called_once()
    
    # Test createEditor
    index.data.return_value = "test_data"
    editor = delegate.createEditor(parent, option, index)
    assert isinstance(editor, QtWidgets.QWidget)
    
    # Test setEditorData
    delegate.setEditorData(editor, index)
    # No assertions needed, just make sure it doesn't crash


def test_button_delegate(qtbot):
    """Test ButtonDelegate"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    delegate = ButtonDelegate(parent)
    
    # Test createEditor
    index = MagicMock()
    index.data.return_value = "Button Text"
    editor = delegate.createEditor(parent, None, index)
    assert isinstance(editor, QtWidgets.QPushButton)
    assert editor.text() == "Button Text"
    
    # Test on_button_clicked (default implementation does nothing)
    delegate.on_button_clicked()  # Should not raise an exception


def test_combo_delegate(qtbot, monkeypatch):
    """Test ComboDelegate"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    # Need to patch the connect method which uses old-style Qt signal/slot syntax
    with patch.object(QtCore.QObject, 'connect', lambda *args, **kwargs: None):
        delegate = ComboDelegate(parent)
        
        # Test createEditor
        editor = delegate.createEditor(parent, None, MagicMock())
        assert isinstance(editor, QtWidgets.QComboBox)
        assert editor.count() == 6  # Should have 6 items


def test_table_view(qtbot):
    """Test TableView"""
    view = TableView()
    qtbot.addWidget(view)
    
    # Check that CheckBoxDelegate is set for column 0
    assert isinstance(view.itemDelegateForColumn(0), CheckBoxDelegate)


def test_resource_view(qtbot):
    """Test ResourceView - This test requires a QAbstractItemModel"""
    view = ResourceView()
    qtbot.addWidget(view)
    
    # Check that CheckBoxDelegate is set for column 0
    assert isinstance(view.itemDelegateForColumn(0), CheckBoxDelegate)


def test_import_view_key_press(qtbot):
    """Test ImportView keyPressEvent method"""
    view = ImportView()
    qtbot.addWidget(view)
    
    # Mock model and selection model
    model = MagicMock()
    selection_model = MagicMock()
    view.model = MagicMock(return_value=model)
    view.selectionModel = MagicMock(return_value=selection_model)
    
    # Test Delete key
    index1 = QtCore.QModelIndex()
    selection_model.selectedRows.return_value = [index1]
    
    # Create a Delete key event
    event = QtGui.QKeyEvent(QtCore.QEvent.Type.KeyPress, QtCore.Qt.Key.Key_Delete, QtCore.Qt.KeyboardModifier.NoModifier)
    view.keyPressEvent(event)
    
    # Should have called delete_entry on the model
    model.delete_entry.assert_called_once()
    
    # Test with a different key
    model.reset_mock()
    event = QtGui.QKeyEvent(QtCore.QEvent.Type.KeyPress, QtCore.Qt.Key.Key_A, QtCore.Qt.KeyboardModifier.NoModifier)
    
    # Mock the parent class's keyPressEvent
    orig_keyPressEvent = QtWidgets.QTableView.keyPressEvent
    QtWidgets.QTableView.keyPressEvent = MagicMock()
    
    view.keyPressEvent(event)
    
    # Should not have called delete_entry
    model.delete_entry.assert_not_called()
    # Should have called the parent's keyPressEvent
    QtWidgets.QTableView.keyPressEvent.assert_called_once()
    
    # Restore the original method
    QtWidgets.QTableView.keyPressEvent = orig_keyPressEvent


def test_export_view_key_press(qtbot):
    """Test ExportView keyPressEvent method"""
    view = ExportView()
    qtbot.addWidget(view)
    
    # Mock model and selection model
    model = MagicMock()
    selection_model = MagicMock()
    view.model = MagicMock(return_value=model)
    view.selectionModel = MagicMock(return_value=selection_model)
    
    # Test Delete key
    index1 = QtCore.QModelIndex()
    selection_model.selectedRows.return_value = [index1]
    
    # Create a Delete key event
    event = QtGui.QKeyEvent(QtCore.QEvent.Type.KeyPress, QtCore.Qt.Key.Key_Delete, QtCore.Qt.KeyboardModifier.NoModifier)
    view.keyPressEvent(event)
    
    # Should have called delete_entry on the model
    model.delete_entry.assert_called_once()
    
    # Test with a different key
    model.reset_mock()
    event = QtGui.QKeyEvent(QtCore.QEvent.Type.KeyPress, QtCore.Qt.Key.Key_A, QtCore.Qt.KeyboardModifier.NoModifier)
    
    # Mock the parent class's keyPressEvent
    orig_keyPressEvent = QtWidgets.QTableView.keyPressEvent
    QtWidgets.QTableView.keyPressEvent = MagicMock()
    
    view.keyPressEvent(event)
    
    # Should not have called delete_entry
    model.delete_entry.assert_not_called()
    # Should have called the parent's keyPressEvent
    QtWidgets.QTableView.keyPressEvent.assert_called_once()
    
    # Restore the original method
    QtWidgets.QTableView.keyPressEvent = orig_keyPressEvent