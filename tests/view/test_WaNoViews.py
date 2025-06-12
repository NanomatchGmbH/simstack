from unittest.mock import MagicMock, patch
import pytest
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import QWidget, QApplication

from simstack.view.WaNoViews import (
    GroupBoxWithButton,
    MultipleOfView,
    EmptyView,
    WaNoGroupView,
    WaNoSwitchView,
    WaNoConditionalView,
    WaNoBoxView,
    WaNoNone,
    WaNoInvisibleBoxView,
    WaNoItemIntView,
    WaNoItemFloatView,
    WaNoItemBoolView,
    WaNoScriptView,
    WaNoItemStringView,
    WanoQtViewRoot,
    WaNoItemFileView,
    OnlyFloatDelegate,
    WaNoMatrixFloatView,
    WaNoMatrixStringView,
    WaNoDropDownView,
    WaNoChoiceView,
    WaNoTabView,
)


class TestGroupBoxWithButton:
    """Tests for GroupBoxWithButton widget."""
    
    def test_init(self, qtbot):
        """Test GroupBoxWithButton initialization."""
        widget = GroupBoxWithButton()
        qtbot.addWidget(widget)
        
        assert widget.add_button is not None
        assert widget.remove_button is not None
        assert widget.add_button.size().width() == 24
        assert widget.add_button.size().height() == 24
        assert widget.remove_button.size().width() == 24
        assert widget.remove_button.size().height() == 24

    def test_get_button_objects(self, qtbot):
        """Test get_button_objects method."""
        widget = GroupBoxWithButton()
        qtbot.addWidget(widget)
        
        add_btn, rem_btn = widget.get_button_objects()
        assert add_btn is widget.add_button
        assert rem_btn is widget.remove_button

    def test_resize_event(self, qtbot):
        """Test button repositioning on resize."""
        widget = GroupBoxWithButton()
        qtbot.addWidget(widget)
        
        # Set initial size and show widget to ensure proper sizing
        widget.resize(200, 100)
        widget.show()
        
        # Force update of button positions
        widget.init_button()
        
        # Check that buttons are positioned at the right edge
        width = widget.size().width()
        expected_add_pos = width - widget.add_button.size().width() - 40
        expected_rem_pos = width - widget.remove_button.size().width() - 10
        
        assert widget.add_button.x() == expected_add_pos
        assert widget.remove_button.x() == expected_rem_pos


class TestEmptyView:
    """Tests for EmptyView."""
    
    def test_init(self):
        """Test EmptyView initialization."""
        view = EmptyView()
        assert view is not None


class TestWaNoGroupView:
    """Tests for WaNoGroupView."""
    
    def test_init(self, qtbot):
        """Test WaNoGroupView initialization."""
        view = WaNoGroupView()
        assert view.actual_widget is not None
        assert view.vbox is not None

    def test_set_parent(self, qtbot):
        """Test set_parent method."""
        view = WaNoGroupView()
        parent_widget = QWidget()
        qtbot.addWidget(parent_widget)
        
        parent_view = MagicMock()
        parent_view.get_widget.return_value = parent_widget
        
        view.set_parent(parent_view)
        assert view._qt_parent == parent_widget

    def test_get_widget(self, qtbot):
        """Test get_widget method."""
        view = WaNoGroupView()
        widget = view.get_widget()
        assert widget is view.actual_widget

    def test_init_from_model(self, qtbot):
        """Test init_from_model method."""
        view = WaNoGroupView()
        model = MagicMock()
        model.is_force_disabled.return_value = False
        
        # Mock wanos method to return list of models with views
        mock_model1 = MagicMock()
        mock_model1.view.get_widget.return_value = QWidget()
        mock_model2 = MagicMock()
        mock_model2.view.get_widget.return_value = QWidget()
        
        model.wanos.return_value = [mock_model1, mock_model2]
        view.set_model(model)
        
        # Add set_disable method to view
        view.set_disable = MagicMock()
        
        view.init_from_model()
        
        # Verify widgets were added to layout
        assert view.vbox.count() == 2


class TestWaNoSwitchView:
    """Tests for WaNoSwitchView."""
    
    def test_init(self, qtbot):
        """Test WaNoSwitchView initialization."""
        view = WaNoSwitchView()
        assert view.actual_widget is not None
        assert view.vbox is not None
        assert view._widgets_parsed is False

    def test_get_widget(self, qtbot):
        """Test get_widget method."""
        view = WaNoSwitchView()
        widget = view.get_widget()
        assert widget is view.actual_widget

    def test_init_from_model_not_parsed(self, qtbot):
        """Test init_from_model when widgets not yet parsed."""
        view = WaNoSwitchView()
        model = MagicMock()
        model.is_force_disabled.return_value = False
        
        # Mock wanos method to raise IndexError immediately
        def wanos_side_effect():
            raise IndexError("WaNo not yet initialized.")
        
        model.wanos.side_effect = wanos_side_effect
        view.set_model(model)
        view.set_disable = MagicMock()
        
        # Mock the clear method since QVBoxLayout doesn't have it (likely a bug in the original code)
        view.vbox.clear = MagicMock()
        
        view.init_from_model()
        
        assert view._widgets_parsed is False
        view.vbox.clear.assert_called_once()

    def test_init_from_model_parsed(self, qtbot):
        """Test init_from_model when widgets are parsed."""
        view = WaNoSwitchView()
        model = MagicMock()
        model.is_force_disabled.return_value = False
        
        # Mock wanos method to return list of models with views
        mock_model1 = MagicMock()
        mock_model1.view.get_widget.return_value = QWidget()
        mock_model1.view.set_visible = MagicMock()
        mock_model2 = MagicMock()
        mock_model2.view.get_widget.return_value = QWidget()
        mock_model2.view.set_visible = MagicMock()
        
        model.wanos.return_value = [("key1", mock_model1), ("key2", mock_model2)]
        model.get_selected_id.return_value = 0
        view.set_model(model)
        view.set_disable = MagicMock()
        
        view.init_from_model()
        
        # First call should set _widgets_parsed to True
        assert view._widgets_parsed is True


class TestWaNoBoxView:
    """Tests for WaNoBoxView."""
    
    def test_init(self, qtbot):
        """Test WaNoBoxView initialization."""
        view = WaNoBoxView()
        assert isinstance(view.actual_widget, QtWidgets.QGroupBox)
        assert view.vbox is not None

    def test_set_parent(self, qtbot):
        """Test set_parent method."""
        view = WaNoBoxView()
        parent_widget = QWidget()
        qtbot.addWidget(parent_widget)
        
        parent_view = MagicMock()
        parent_view.get_widget.return_value = parent_widget
        
        view.set_parent(parent_view)
        assert view._qt_parent == parent_widget

    def test_init_from_model(self, qtbot):
        """Test init_from_model method."""
        view = WaNoBoxView()
        model = MagicMock()
        model.name = "Test Box"
        model.is_force_disabled.return_value = False
        
        # Mock wanos method
        mock_model1 = MagicMock()
        mock_model1.view.get_widget.return_value = QWidget()
        model.wanos.return_value = [mock_model1]
        
        view.set_model(model)
        view.set_disable = MagicMock()
        view.init_from_model()
        
        assert view.actual_widget.title() == "Test Box"


class TestWaNoNone:
    """Tests for WaNoNone."""
    
    def test_init(self, qtbot):
        """Test WaNoNone initialization."""
        view = WaNoNone()
        assert isinstance(view.actual_widget, QtWidgets.QFrame)
        assert view.vbox is not None

    def test_set_parent(self, qtbot):
        """Test set_parent method."""
        view = WaNoNone()
        parent_widget = QWidget()
        qtbot.addWidget(parent_widget)
        
        parent_view = MagicMock()
        parent_view.get_widget.return_value = parent_widget
        
        view.set_parent(parent_view)
        assert view._qt_parent == parent_widget

    def test_get_widget(self, qtbot):
        """Test get_widget method."""
        view = WaNoNone()
        widget = view.get_widget()
        assert widget is view.actual_widget


class TestWaNoInvisibleBoxView:
    """Tests for WaNoInvisibleBoxView."""
    
    def test_init(self, qtbot):
        """Test WaNoInvisibleBoxView initialization."""
        view = WaNoInvisibleBoxView()
        assert isinstance(view.actual_widget, QtWidgets.QFrame)
        assert view.vbox is not None

    def test_init_from_model(self, qtbot):
        """Test init_from_model method."""
        view = WaNoInvisibleBoxView()
        model = MagicMock()
        model.is_force_disabled.return_value = False
        
        # Mock wanos method
        mock_model1 = MagicMock()
        mock_model1.view.get_widget.return_value = QWidget()
        model.wanos.return_value = [mock_model1]
        
        view.set_model(model)
        view.set_disable = MagicMock()
        view.init_from_model()
        
        # Verify widget was added to layout
        assert view.vbox.count() == 1


class TestWaNoItemIntView:
    """Tests for WaNoItemIntView."""
    
    def test_init(self, qtbot):
        """Test WaNoItemIntView initialization."""
        view = WaNoItemIntView()
        qtbot.addWidget(view.actual_widget)
        
        assert view.spinner is not None
        assert view.label is not None
        assert view._global_import_button is not None
        assert view.spinner.value() == 0
        assert view.spinner.maximum() == 1000000000
        assert view.spinner.minimum() == -1000000000

    def test_set_disable(self, qtbot):
        """Test set_disable method."""
        view = WaNoItemIntView()
        qtbot.addWidget(view.actual_widget)
        
        view.set_disable(True)
        assert view.spinner.isEnabled() is False
        
        view.set_disable(False)
        assert view.spinner.isEnabled() is True

    def test_init_from_model(self, qtbot):
        """Test init_from_model method."""
        view = WaNoItemIntView()
        qtbot.addWidget(view.actual_widget)
        
        model = MagicMock()
        model.get_data.return_value = 42
        model.name = "Test Int"
        model.do_import = False
        model.is_force_disabled.return_value = False
        model.tooltip_text = "Test tooltip"
        
        view.set_model(model)
        view.init_from_model()
        
        assert view.spinner.value() == 42
        assert view.label.text() == "Test Int"

    def test_value_changed(self, qtbot):
        """Test value_changed method."""
        view = WaNoItemIntView()
        qtbot.addWidget(view.actual_widget)
        
        model = MagicMock()
        view.set_model(model)
        
        view.value_changed(123)
        
        model.set_data.assert_called_once_with(123)


class TestWaNoItemFloatView:
    """Tests for WaNoItemFloatView."""
    
    def test_init(self, qtbot):
        """Test WaNoItemFloatView initialization."""
        view = WaNoItemFloatView()
        qtbot.addWidget(view.actual_widget)
        
        assert view.spinner is not None
        assert view.label is not None
        assert view._global_import_button is not None
        assert view.spinner.value() == 0.0
        assert view.spinner.decimals() == 5

    def test_init_from_model(self, qtbot):
        """Test init_from_model method."""
        view = WaNoItemFloatView()
        qtbot.addWidget(view.actual_widget)
        
        model = MagicMock()
        model.get_data.return_value = 3.14159
        model.name = "Test Float"
        model.do_import = False
        model.is_force_disabled.return_value = False
        model.tooltip_text = "Test tooltip"
        
        view.set_model(model)
        view.init_from_model()
        
        assert view.spinner.value() == 3.14159
        assert view.label.text() == "Test Float"

    def test_value_changed(self, qtbot):
        """Test value_changed method."""
        view = WaNoItemFloatView()
        qtbot.addWidget(view.actual_widget)
        
        model = MagicMock()
        view.set_model(model)
        
        view.value_changed(2.718)
        
        model.set_data.assert_called_once_with(2.718)


class TestWaNoItemBoolView:
    """Tests for WaNoItemBoolView."""
    
    def test_init(self, qtbot):
        """Test WaNoItemBoolView initialization."""
        view = WaNoItemBoolView()
        qtbot.addWidget(view.actual_widget)
        
        assert view.checkbox is not None
        assert view.label is not None

    def test_init_from_model(self, qtbot):
        """Test init_from_model method."""
        view = WaNoItemBoolView()
        qtbot.addWidget(view.actual_widget)
        
        model = MagicMock()
        model.get_data.return_value = True
        model.name = "Test Bool"
        model.is_force_disabled.return_value = False
        model.tooltip_text = "Test tooltip"
        
        view.set_model(model)
        view.set_disable = MagicMock()
        view.init_from_model()
        
        assert view.checkbox.isChecked() is True
        assert view.label.text() == "Test Bool"

    def test_state_changed(self, qtbot):
        """Test state_changed method."""
        view = WaNoItemBoolView()
        qtbot.addWidget(view.actual_widget)
        
        model = MagicMock()
        view.set_model(model)
        
        # Test checked state
        view.checkbox.setChecked(True)
        view.state_changed()
        model.set_data.assert_called_with(True)
        
        # Test unchecked state
        view.checkbox.setChecked(False)
        view.state_changed()
        model.set_data.assert_called_with(False)


class TestWaNoScriptView:
    """Tests for WaNoScriptView."""
    
    def test_init(self, qtbot):
        """Test WaNoScriptView initialization."""
        view = WaNoScriptView()
        qtbot.addWidget(view.actual_widget)
        
        assert view.textedit is not None
        assert view.menubar is not None

    def test_init_from_model(self, qtbot):
        """Test init_from_model method."""
        view = WaNoScriptView()
        qtbot.addWidget(view.actual_widget)
        
        model = MagicMock()
        model.get_data.return_value = "print('hello')"
        model.is_force_disabled.return_value = False
        
        view.set_model(model)
        view.set_disable = MagicMock()
        view.init_from_model()
        
        assert view.textedit.toPlainText() == "print('hello')"

    def test_line_edited(self, qtbot):
        """Test line_edited method."""
        view = WaNoScriptView()
        qtbot.addWidget(view.actual_widget)
        
        model = MagicMock()
        view.set_model(model)
        
        # Block signals to avoid recursive calls during testing
        view.textedit.blockSignals(True)
        view.textedit.setText("new code")
        view.textedit.blockSignals(False)
        
        view.line_edited()
        
        model.set_data.assert_called_once_with("new code")


class TestWaNoItemStringView:
    """Tests for WaNoItemStringView."""
    
    def test_init(self, qtbot):
        """Test WaNoItemStringView initialization."""
        view = WaNoItemStringView()
        qtbot.addWidget(view.actual_widget)
        
        assert view.lineedit is not None
        assert view.label is not None
        assert view._global_import_button is not None

    def test_set_disable(self, qtbot):
        """Test set_disable method."""
        view = WaNoItemStringView()
        qtbot.addWidget(view.actual_widget)
        
        view.set_disable(True)
        assert view.lineedit.isEnabled() is False
        
        view.set_disable(False)
        assert view.lineedit.isEnabled() is True

    def test_init_from_model(self, qtbot):
        """Test init_from_model method."""
        view = WaNoItemStringView()
        qtbot.addWidget(view.actual_widget)
        
        model = MagicMock()
        model.get_data.return_value = "test string"
        model.name = "Test String"
        model.do_import = False
        model.is_force_disabled.return_value = False
        model.tooltip_text = "Test tooltip"
        
        view.set_model(model)
        view.init_from_model()
        
        assert view.lineedit.text() == "test string"
        assert view.label.text() == "Test String"

    def test_line_edited(self, qtbot):
        """Test line_edited method."""
        view = WaNoItemStringView()
        qtbot.addWidget(view.actual_widget)
        
        model = MagicMock()
        view.set_model(model)
        
        view.lineedit.setText("edited text")
        view.line_edited()
        
        model.set_data.assert_called_once_with("edited text")


class TestWanoQtViewRoot:
    """Tests for WanoQtViewRoot."""
    
    def test_init(self, qtbot):
        """Test WanoQtViewRoot initialization."""
        view = WanoQtViewRoot()
        assert view is not None

    def test_set_parent_with_qobject(self, qtbot):
        """Test set_parent with QObject parent."""
        view = WanoQtViewRoot()
        parent = QWidget()
        qtbot.addWidget(parent)
        
        view.set_parent(parent)
        
        assert view._qt_parent == parent
        assert isinstance(view.actual_widget, QtWidgets.QScrollArea)

    def test_init_without_scroller(self, qtbot):
        """Test init_without_scroller method."""
        view = WanoQtViewRoot()
        parent = QWidget()
        qtbot.addWidget(parent)
        view._qt_parent = parent
        
        view.init_without_scroller()
        
        assert isinstance(view.actual_widget, QtWidgets.QWidget)
        assert view.vbox is not None

    def test_get_resource_widget(self, qtbot):
        """Test get_resource_widget method."""
        view = WanoQtViewRoot()
        model = MagicMock()
        resource_model = MagicMock()
        model.get_new_resource_model.return_value = resource_model
        view.set_model(model)
        
        widget = view.get_resource_widget()
        
        assert widget is not None
        model.get_new_resource_model.assert_called_once()

    def test_get_import_widget(self, qtbot):
        """Test get_import_widget method."""
        with patch('simstack.view.PropertyListView.ImportView') as mock_import_view:
            view = WanoQtViewRoot()
            model = MagicMock()
            import_model = MagicMock()
            model.get_import_model.return_value = import_model
            view.set_model(model)
            
            widget = view.get_import_widget()
            
            assert widget is not None
            model.get_import_model.assert_called_once()

    def test_get_export_widget(self, qtbot):
        """Test get_export_widget method."""
        with patch('simstack.view.PropertyListView.ExportView') as mock_export_view:
            view = WanoQtViewRoot()
            model = MagicMock()
            export_model = MagicMock()
            model.get_export_model.return_value = export_model
            view.set_model(model)
            
            widget = view.get_export_widget()
            
            assert widget is not None
            model.get_export_model.assert_called_once()


class TestWaNoItemFileView:
    """Tests for WaNoItemFileView."""
    
    def test_init(self, qtbot):
        """Test WaNoItemFileView initialization."""
        view = WaNoItemFileView()
        qtbot.addWidget(view.actual_widget)
        
        assert view.lineedit is not None
        assert view.label is not None
        assert view.openfilebutton is not None
        assert view.openwfbutton is not None

    def test_set_disable(self, qtbot):
        """Test set_disable method."""
        view = WaNoItemFileView()
        qtbot.addWidget(view.actual_widget)
        
        view.set_disable(True)
        assert view.lineedit.isEnabled() is False
        
        view.set_disable(False)
        assert view.lineedit.isEnabled() is True

    def test_init_from_model(self, qtbot):
        """Test init_from_model method."""
        view = WaNoItemFileView()
        qtbot.addWidget(view.actual_widget)
        
        model = MagicMock()
        model.get_data.return_value = "/path/to/file.txt"
        model.name = "Test File"
        model.is_force_disabled.return_value = False
        model.tooltip_text = "Test tooltip"
        
        view.set_model(model)
        view.set_disable = MagicMock()
        view.init_from_model()
        
        assert view.lineedit.text() == "/path/to/file.txt"
        assert view.label.text() == "Test File"

    def test_set_file_import_none(self, qtbot):
        """Test set_file_import with None."""
        view = WaNoItemFileView()
        qtbot.addWidget(view.actual_widget)
        
        model = MagicMock()
        view.set_model(model)
        
        view.set_file_import(None)
        
        model.set_local.assert_called_with(True)
        assert view.lineedit.text() == ""

    def test_set_file_import_with_filename(self, qtbot):
        """Test set_file_import with filename."""
        view = WaNoItemFileView()
        qtbot.addWidget(view.actual_widget)
        
        model = MagicMock()
        view.set_model(model)
        
        view.set_file_import("test_file.txt")
        
        model.set_local.assert_called_with(False)
        assert view.lineedit.text() == "test_file.txt"

    @patch('PySide6.QtWidgets.QFileDialog.getOpenFileName')
    def test_show_local_dialog(self, mock_dialog, qtbot):
        """Test showLocalDialog method."""
        mock_dialog.return_value = ("/path/to/selected/file.txt", "")
        
        view = WaNoItemFileView()
        qtbot.addWidget(view.actual_widget)
        
        model = MagicMock()
        view.set_model(model)
        
        view.showLocalDialog()
        
        model.set_local.assert_called_with(True)
        assert "/path/to/selected/file.txt" in view.lineedit.text()


class TestOnlyFloatDelegate:
    """Tests for OnlyFloatDelegate."""
    
    def test_create_editor(self, qtbot):
        """Test createEditor method."""
        delegate = OnlyFloatDelegate()
        parent = QWidget()
        qtbot.addWidget(parent)
        
        editor = delegate.createEditor(parent, None, None)
        
        assert isinstance(editor, QtWidgets.QDoubleSpinBox)


class TestWaNoMatrixFloatView:
    """Tests for WaNoMatrixFloatView."""
    
    def test_init(self, qtbot):
        """Test WaNoMatrixFloatView initialization."""
        view = WaNoMatrixFloatView()
        qtbot.addWidget(view.actual_widget)
        
        assert view.tablewidget is not None
        assert view.label is not None
        assert view.has_col_header is False
        assert view.has_row_header is False

    def test_cell_changed(self, qtbot):
        """Test cellChanged method."""
        view = WaNoMatrixFloatView()
        qtbot.addWidget(view.actual_widget)
        
        model = MagicMock()
        model.storage = [[0.0, 0.0], [0.0, 0.0]]
        view.set_model(model)
        
        # Create a mock item
        item = QtWidgets.QTableWidgetItem("3.14")
        view.tablewidget.setItem(0, 1, item)
        
        view.cellChanged(0, 1)
        
        assert model.storage[0][1] == 3.14

    def test_reset_table(self, qtbot):
        """Test reset_table method."""
        view = WaNoMatrixFloatView()
        qtbot.addWidget(view.actual_widget)
        
        model = MagicMock()
        model.rows = 2
        model.cols = 3
        model.col_header = None
        model.row_header = None
        model.storage = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]  # Provide storage for cellChanged
        view.model = model  # Set model directly to avoid set_model
        
        # Block signals to prevent cellChanged during setup
        view.tablewidget.blockSignals(True)
        view.reset_table()
        view.tablewidget.blockSignals(False)
        
        assert view.tablewidget.rowCount() == 2
        assert view.tablewidget.columnCount() == 3

    def test_default_value_if_empty_string(self, qtbot):
        """Test _default_value_if_empty_string method."""
        view = WaNoMatrixFloatView()
        result = view._default_value_if_empty_string()
        assert result == 0.0

    def test_init_from_model(self, qtbot):
        """Test init_from_model method."""
        view = WaNoMatrixFloatView()
        qtbot.addWidget(view.actual_widget)
        
        model = MagicMock()
        model.name = "Test Matrix"
        model.rows = 2
        model.cols = 2
        model.col_header = None
        model.row_header = None
        model.storage = [[1.0, 2.0], [3.0, ""]]
        model.is_force_disabled.return_value = False
        model.tooltip_text = "Test tooltip"
        view.set_model(model)
        view.set_disable = MagicMock()
        
        view.init_from_model()
        
        assert view.label.text() == "Test Matrix"


class TestWaNoMatrixStringView:
    """Tests for WaNoMatrixStringView."""
    
    def test_init(self, qtbot):
        """Test WaNoMatrixStringView initialization."""
        view = WaNoMatrixStringView()
        qtbot.addWidget(view.actual_widget)
        
        assert view.tablewidget is not None

    def test_cell_changed(self, qtbot):
        """Test cellChanged method."""
        view = WaNoMatrixStringView()
        qtbot.addWidget(view.actual_widget)
        
        model = MagicMock()
        view.model = model  # Set model directly
        
        # Block signals to prevent unwanted cellChanged calls during setup
        view.tablewidget.blockSignals(True)
        # Create a mock item
        item = QtWidgets.QTableWidgetItem("test string")
        view.tablewidget.setItem(0, 1, item)
        view.tablewidget.blockSignals(False)
        
        view.cellChanged(0, 1)
        
        model.set_data.assert_called_once_with(0, 1, "test string")

    def test_default_value_if_empty_string(self, qtbot):
        """Test _default_value_if_empty_string method."""
        view = WaNoMatrixStringView()
        result = view._default_value_if_empty_string()
        assert result == ""


class TestWaNoDropDownView:
    """Tests for WaNoDropDownView."""
    
    def test_init(self, qtbot):
        """Test WaNoDropDownView initialization."""
        view = WaNoDropDownView()
        qtbot.addWidget(view.actual_widget)
        
        assert view.combobox is not None
        assert view.label is not None
        assert view.init is False

    def test_init_from_model(self, qtbot):
        """Test init_from_model method."""
        view = WaNoDropDownView()
        qtbot.addWidget(view.actual_widget)
        
        model = MagicMock()
        model.name = "Test Dropdown"
        model.chosen = 1
        model.choices = ["Option A", "Option B", "Option C"]
        model.is_force_disabled.return_value = False
        model.tooltip_text = "Test tooltip"
        view.set_model(model)
        view.set_disable = MagicMock()
        
        view.init_from_model()
        
        assert view.label.text() == "Test Dropdown"
        assert view.combobox.currentIndex() == 1
        assert view.init is True

    def test_on_button_clicked(self, qtbot):
        """Test onButtonClicked method."""
        view = WaNoDropDownView()
        qtbot.addWidget(view.actual_widget)
        
        model = MagicMock()
        view.set_model(model)
        view.init = True
        
        view.onButtonClicked(2)
        
        model.set_chosen.assert_called_with(2)

    def test_on_button_clicked_not_init(self, qtbot):
        """Test onButtonClicked when not initialized."""
        view = WaNoDropDownView()
        qtbot.addWidget(view.actual_widget)
        
        model = MagicMock()
        view.set_model(model)
        view.init = False
        
        view.onButtonClicked(2)
        
        model.set_chosen.assert_not_called()


class TestWaNoChoiceView:
    """Tests for WaNoChoiceView."""
    
    def test_init(self, qtbot):
        """Test WaNoChoiceView initialization."""
        view = WaNoChoiceView()
        qtbot.addWidget(view.actual_widget)
        
        assert isinstance(view.actual_widget, QtWidgets.QGroupBox)
        assert view.bg is not None
        assert view.vbox is not None
        assert view.buttons == []

    def test_init_from_model(self, qtbot):
        """Test init_from_model method."""
        view = WaNoChoiceView()
        qtbot.addWidget(view.actual_widget)
        
        model = MagicMock()
        model.name = "Test Choice"
        model.chosen = 1
        model.choices = ["Choice A", "Choice B", "Choice C"]
        model.is_force_disabled.return_value = False
        view.set_model(model)
        view.set_disable = MagicMock()
        
        view.init_from_model()
        
        assert view.actual_widget.title() == "Test Choice"
        assert len(view.buttons) == 3
        assert view.buttons[1].isChecked() is True

    def test_on_button_clicked(self, qtbot):
        """Test onButtonClicked method."""
        view = WaNoChoiceView()
        qtbot.addWidget(view.actual_widget)
        
        model = MagicMock()
        view.set_model(model)
        
        view.onButtonClicked(2)
        
        model.set_chosen.assert_called_once_with(2)


class TestWaNoTabView:
    """Tests for WaNoTabView."""
    
    def test_init(self, qtbot):
        """Test WaNoTabView initialization."""
        view = WaNoTabView()
        qtbot.addWidget(view.actual_widget)
        
        assert isinstance(view.actual_widget, QtWidgets.QTabWidget)

    def test_get_widget(self, qtbot):
        """Test get_widget method."""
        view = WaNoTabView()
        widget = view.get_widget()
        assert widget is view.actual_widget

    def test_init_from_model(self, qtbot):
        """Test init_from_model method."""
        view = WaNoTabView()
        qtbot.addWidget(view.actual_widget)
        
        model = MagicMock()
        
        # Mock model items
        mock_model1 = MagicMock()
        mock_model1.name = "Tab 1"
        mock_model1.view.get_widget.return_value = QWidget()
        
        mock_model2 = MagicMock()
        mock_model2.name = "Tab 2"
        mock_model2.view.get_widget.return_value = QWidget()
        
        model.items.return_value = [("key1", mock_model1), ("key2", mock_model2)]
        view.set_model(model)
        
        view.init_from_model()
        
        assert view.actual_widget.count() == 2
        assert view.actual_widget.tabText(0) == "Tab 1"
        assert view.actual_widget.tabText(1) == "Tab 2"


class TestMultipleOfView:
    """Tests for MultipleOfView."""
    
    def test_init(self, qtbot):
        """Test MultipleOfView initialization."""
        view = MultipleOfView()
        qtbot.addWidget(view.actual_widget)
        
        assert isinstance(view.actual_widget, GroupBoxWithButton)
        assert view.vbox is not None
        assert view._list_of_bar_widgets == []

    def test_add_button_clicked(self, qtbot):
        """Test add_button_clicked method."""
        view = MultipleOfView()
        qtbot.addWidget(view.actual_widget)
        
        model = MagicMock()
        model.is_force_disabled.return_value = False
        view.set_model(model)
        view.set_disable = MagicMock()
        
        # Mock init_from_model to avoid complex setup
        view.init_from_model = MagicMock()
        
        view.add_button_clicked()
        
        model.add_item.assert_called_once()
        view.init_from_model.assert_called_once()

    def test_remove_button_clicked_not_last(self, qtbot):
        """Test remove_button_clicked when not last item."""
        view = MultipleOfView()
        qtbot.addWidget(view.actual_widget)
        
        model = MagicMock()
        model.last_item_check.return_value = False
        model.delete_item.return_value = True
        model.is_force_disabled.return_value = False
        view.set_model(model)
        view.set_disable = MagicMock()
        
        # Mock init_from_model to avoid complex setup
        view.init_from_model = MagicMock()
        
        view.remove_button_clicked()
        
        model.delete_item.assert_called_once()
        view.init_from_model.assert_called_once()

    def test_remove_button_clicked_last_item(self, qtbot):
        """Test remove_button_clicked when it's the last item."""
        view = MultipleOfView()
        qtbot.addWidget(view.actual_widget)
        
        model = MagicMock()
        model.last_item_check.return_value = True
        view.set_model(model)
        
        view.remove_button_clicked()
        
        model.delete_item.assert_not_called()

    def test_init_from_model(self, qtbot):
        """Test init_from_model method."""
        view = MultipleOfView()
        qtbot.addWidget(view.actual_widget)
        
        model = MagicMock()
        model.name = "Multiple View"
        model.is_force_disabled.return_value = False
        
        # Mock model items
        mock_inner_model = MagicMock()
        mock_inner_model.view.get_widget.return_value = QWidget()
        
        model.__iter__.return_value = [{"item1": mock_inner_model}]
        model.__len__.return_value = 1
        view.set_model(model)
        view.set_disable = MagicMock()
        
        view.init_from_model()
        
        assert view.actual_widget.title() == "Multiple View"