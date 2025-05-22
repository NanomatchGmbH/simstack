import pytest
from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QWidget

from simstack.view.AbstractWaNoView import AbstractWanoView, AbstractWanoQTView


class ConcreteWaNoView(AbstractWanoView):
    """Concrete implementation of AbstractWanoView for testing."""
    
    def init_from_model(self):
        pass
    
    def set_enabled(self, enabled):
        self.enabled = enabled


class ConcreteWaNoQTView(AbstractWanoQTView):
    """Concrete implementation of AbstractWanoQTView for testing."""
    
    def __init__(self, qtbot=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label = MagicMock()
        if qtbot:
            self.actual_widget = QWidget()
            qtbot.addWidget(self.actual_widget)
        else:
            self.actual_widget = MagicMock()
        self.disabled = False
    
    def init_from_model(self):
        super().init_from_model()
    
    def set_disable(self, true_or_false):
        self.disabled = true_or_false
    
    def get_widget(self):
        return self.actual_widget
    
    def set_enabled(self, enabled):
        pass


class TestAbstractWaNoView:
    """Tests for the AbstractWanoView class."""
    
    def test_set_model(self):
        """Test setting a model on the view."""
        view = ConcreteWaNoView()
        model = MagicMock()
        
        view.set_model(model)
        
        assert view.model == model
        model.set_view.assert_called_once_with(view)


class TestAbstractWaNoQTView:
    """Tests for the AbstractWanoQTView class."""
    
    def test_set_visible(self, qtbot):
        """Test setting visibility on the view."""
        view = ConcreteWaNoQTView(qtbot)
        
        # Test with actual_widget set
        view.set_visible(True)
        assert view.actual_widget.isVisible() is True
        
        view.set_visible(False)
        assert view.actual_widget.isVisible() is False
    
    def test_set_parent_with_get_widget(self, qtbot):
        """Test setting a parent that has get_widget method."""
        view = ConcreteWaNoQTView(qtbot)
        parent_view = MagicMock()
        parent_widget = QWidget()
        qtbot.addWidget(parent_widget)
        parent_view.get_widget.return_value = parent_widget
        
        view.set_parent(parent_view)
        
        assert view._qt_parent == parent_widget
        parent_view.get_widget.assert_called_once()
    
    def test_set_parent_without_get_widget(self, qtbot):
        """Test setting a parent that doesn't have get_widget method."""
        view = ConcreteWaNoQTView(qtbot)
        parent_view = QWidget()
        qtbot.addWidget(parent_view)
        
        view.set_parent(parent_view)
        
        assert view._qt_parent == parent_view
    
    @patch('simstack.view.AbstractWaNoView.RemoteImporterDialog')
    def test_open_remote_importer_accepted(self, mock_dialog_class, qtbot):
        """Test open_remote_importer when dialog is accepted."""
        view = ConcreteWaNoQTView(qtbot)
        model = MagicMock()
        model.is_force_disabled.return_value = False
        root = MagicMock()
        parent_wf = MagicMock()
        parent_wf.assemble_variables.return_value = ["var1", "var2"]
        root.get_parent_wf.return_value = parent_wf
        model.get_root.return_value = root
        model.name = "test_name"
        view.set_model(model)
        
        # Mock the dialog
        mock_dialog = mock_dialog_class.return_value
        mock_dialog.result.return_value = True
        mock_dialog.getchoice.return_value = "var1"
        
        # Call the method
        view.open_remote_importer()
        
        # Verify the dialog was created correctly
        mock_dialog_class.assert_called_once_with(
            varname='Import variable "test_name" from:',
            importlist=["var1", "var2"]
        )
        
        # Verify dialog methods were called
        mock_dialog.setModal.assert_called_once_with(True)
        mock_dialog.exec_.assert_called_once()
        
        # Verify model methods were called
        model.set_import.assert_called_once_with("var1")
        assert view.disabled is True
    
    @patch('simstack.view.AbstractWaNoView.RemoteImporterDialog')
    def test_open_remote_importer_rejected(self, mock_dialog_class, qtbot):
        """Test open_remote_importer when dialog is rejected."""
        view = ConcreteWaNoQTView(qtbot)
        model = MagicMock()
        model.is_force_disabled.return_value = False
        root = MagicMock()
        parent_wf = MagicMock()
        parent_wf.assemble_variables.return_value = ["var1", "var2"]
        root.get_parent_wf.return_value = parent_wf
        model.get_root.return_value = root
        model.name = "test_name"
        view.set_model(model)
        
        # Mock the dialog
        mock_dialog = mock_dialog_class.return_value
        mock_dialog.result.return_value = False
        
        # Call the method
        view.open_remote_importer()
        
        # Verify model methods were called
        model.set_import.assert_called_once_with(None)
        assert view.disabled is False
    
    @patch('simstack.view.AbstractWaNoView.RemoteImporterDialog')
    def test_open_remote_importer_disabled(self, mock_dialog_class, qtbot):
        """Test open_remote_importer when model is force disabled."""
        view = ConcreteWaNoQTView(qtbot)
        model = MagicMock()
        model.is_force_disabled.return_value = True
        view.set_model(model)
        
        # Call the method
        view.open_remote_importer()
        
        # Verify dialog was not created
        mock_dialog_class.assert_not_called()
    
    def test_decommission(self, qtbot):
        """Test decommission method."""
        # Use a mock instead of a real widget to test deleteLater
        view = ConcreteWaNoQTView()
        widget_mock = MagicMock()
        view.get_widget = MagicMock(return_value=widget_mock)
        
        view.decommission()
        
        widget_mock.deleteLater.assert_called_once()
    
    def test_decommission_none_widget(self, qtbot):
        """Test decommission with None widget."""
        view = ConcreteWaNoQTView(qtbot)
        view.get_widget = MagicMock(return_value=None)
        
        # This should not raise an exception
        view.decommission()
    
    def test_init_from_model_with_tooltip(self, qtbot):
        """Test init_from_model with tooltip text."""
        view = ConcreteWaNoQTView(qtbot)
        model = MagicMock()
        model.tooltip_text = "Test tooltip"
        model.is_force_disabled.return_value = False
        view.set_model(model)
        
        view.init_from_model()
        
        view.label.setToolTip.assert_called_once_with("Test tooltip")
    
    def test_init_from_model_force_disabled(self, qtbot):
        """Test init_from_model with force disabled."""
        view = ConcreteWaNoQTView(qtbot)
        model = MagicMock()
        model.is_force_disabled.return_value = True
        view.set_model(model)
        
        view.init_from_model()
        
        assert view.disabled is True