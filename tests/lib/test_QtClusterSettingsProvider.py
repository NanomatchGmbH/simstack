import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtCore import QObject

from simstack.lib.QtClusterSettingsProvider import QtClusterSettingsProvider, QtSettingsChangedWorkaround


class TestQtSettingsChangedWorkaround:
    """Tests for QtSettingsChangedWorkaround class."""
    
    def test_init(self):
        """Test initialization of QtSettingsChangedWorkaround."""
        workaround = QtSettingsChangedWorkaround()
        assert isinstance(workaround, QObject)
        assert hasattr(workaround, "settings_changed")


class TestQtClusterSettingsProvider:
    """Tests for QtClusterSettingsProvider class."""
    
    @pytest.fixture
    def provider(self):
        """Create a QtClusterSettingsProvider with mocked parent classes."""
        with patch('simstack.lib.QtClusterSettingsProvider.ClusterSettingsProvider'):
            provider = QtClusterSettingsProvider()
            # Mock the settings_changed signal
            provider.settings_changed = MagicMock()
            return provider
    
    def test_init(self, provider):
        """Test initialization of QtClusterSettingsProvider."""
        assert isinstance(provider, QtClusterSettingsProvider)
        assert isinstance(provider, QtSettingsChangedWorkaround)
    
    def test_add_resource(self, provider):
        """Test add_resource method emits signal."""
        # Setup mock for parent class add_resource
        mock_resource = MagicMock()
        provider.add_resource.__self__.__class__.__bases__[0].add_resource = MagicMock(return_value=mock_resource)
        
        # Call the method
        result = provider.add_resource("test_resource")
        
        # Verify
        assert result == mock_resource
        provider.settings_changed.emit.assert_called_once()
        provider.add_resource.__self__.__class__.__bases__[0].add_resource.assert_called_once_with(resource_name="test_resource")
    
    def test_remove_resource(self, provider):
        """Test remove_resource method emits signal."""
        # Setup mock for parent class remove_resource
        provider.remove_resource.__self__.__class__.__bases__[0].remove_resource = MagicMock()
        
        # Call the method
        provider.remove_resource("test_resource")
        
        # Verify
        provider.settings_changed.emit.assert_called_once()
        provider.remove_resource.__self__.__class__.__bases__[0].remove_resource.assert_called_once_with(resource_name="test_resource")
    
    @patch('simstack.lib.QtClusterSettingsProvider.ClusterSettingsProvider.get_registries')
    def test_get_registries(self, mock_get_registries):
        """Test get_registries class method."""
        # Setup
        expected_registries = {"registry1": MagicMock(), "registry2": MagicMock()}
        mock_get_registries.return_value = expected_registries
        
        # Call the method
        result = QtClusterSettingsProvider.get_registries()
        
        # Verify
        assert result == expected_registries
        mock_get_registries.assert_called_once()