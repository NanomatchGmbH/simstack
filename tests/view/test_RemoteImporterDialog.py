import pytest
from unittest.mock import MagicMock
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QCompleter, QLineEdit, QLabel

from simstack.view.RemoteImporterDialog import RemoteImporterDialog


class TestRemoteImporterDialog:
    """Tests for the RemoteImporterDialog class."""
    
    @pytest.fixture
    def dialog_with_default_title(self, qtbot):
        """Create a RemoteImporterDialog with default title."""
        test_importlist = ["var1", "var2", "var3"]
        test_varname = "Select variable:"
        dialog = RemoteImporterDialog(importlist=test_importlist, varname=test_varname)
        qtbot.addWidget(dialog)
        return dialog
    
    @pytest.fixture
    def dialog_with_custom_title(self, qtbot):
        """Create a RemoteImporterDialog with custom title."""
        test_importlist = ["var1", "var2", "var3"]
        test_varname = "Select variable:"
        dialog = RemoteImporterDialog(
            importlist=test_importlist, 
            varname=test_varname, 
            window_title="Custom Title"
        )
        qtbot.addWidget(dialog)
        return dialog
    
    def test_init_default_title(self, dialog_with_default_title):
        """Test initialization with default title."""
        dialog = dialog_with_default_title
        
        # Check it's a QDialog
        assert isinstance(dialog, QDialog)
        
        # Check window title
        assert dialog.windowTitle() == "Import Workflow Variable"
        
        # Check minimum size
        assert dialog.minimumWidth() == 800
        assert dialog.minimumHeight() == 120
    
    def test_init_custom_title(self, dialog_with_custom_title):
        """Test initialization with custom title."""
        dialog = dialog_with_custom_title
        
        # Check window title
        assert dialog.windowTitle() == "Custom Title"
    
    def test_completer_setup(self, dialog_with_default_title):
        """Test that the completer is correctly set up."""
        dialog = dialog_with_default_title
        
        # Get the private completer
        completer = dialog._completer
        
        # Check it's a QCompleter
        assert isinstance(completer, QCompleter)
        
        # Check completer properties
        assert completer.completionMode() == QCompleter.UnfilteredPopupCompletion
        assert completer.caseSensitivity() == Qt.CaseInsensitive
        
        # Check the completer model has the correct items
        model = completer.model()
        assert model.rowCount() == 3
        assert model.data(model.index(0, 0)) == "var1"
        assert model.data(model.index(1, 0)) == "var2"
        assert model.data(model.index(2, 0)) == "var3"
    
    def test_line_edit_setup(self, dialog_with_default_title):
        """Test that the line edit is correctly set up."""
        dialog = dialog_with_default_title
        
        # Get the private line edit
        line_edit = dialog._mylineedit
        
        # Check it's a QLineEdit
        assert isinstance(line_edit, QLineEdit)
        
        # Check the completer is correctly set
        assert line_edit.completer() == dialog._completer
    
    def test_button_box_setup(self, dialog_with_default_title):
        """Test that the button box is correctly set up."""
        dialog = dialog_with_default_title
        
        # Get the private button box
        button_box = dialog._buttonBox
        
        # Check it's a QDialogButtonBox
        assert isinstance(button_box, QDialogButtonBox)
        
        # Check it has the correct buttons
        assert button_box.standardButtons() == (QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    
    def test_signal_connections(self, dialog_with_default_title, qtbot):
        """Test that the signals are connected correctly."""
        dialog = dialog_with_default_title
        
        # Mock the accept and reject methods
        dialog.accept = MagicMock()
        dialog.reject = MagicMock()
        
        # Trigger the signals
        dialog._buttonBox.accepted.emit()
        dialog._buttonBox.rejected.emit()
        
        # Check the methods were called
        dialog.accept.assert_called_once()
        dialog.reject.assert_called_once()
    
    def test_getchoice(self, dialog_with_default_title):
        """Test getchoice method."""
        dialog = dialog_with_default_title
        
        # Set text in the line edit
        dialog._mylineedit.setText("test_value")
        
        # Check getchoice returns the correct value
        assert dialog.getchoice() == "test_value"