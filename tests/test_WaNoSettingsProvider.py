import os
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock

from simstack.WaNoSettingsProvider import WaNoSettingsProvider, NotInstancedError, _path
from simstack.Constants import SETTING_KEYS


class TestWaNoSettingsProvider:
    """Tests for WaNoSettingsProvider class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def settings_file(self, temp_dir):
        """Create a temporary settings file."""
        return os.path.join(temp_dir, "test_settings.yaml")

    @pytest.fixture
    def settings_provider(self, settings_file):
        """Create a WaNoSettingsProvider instance for testing."""
        # Reset the singleton instance before each test
        WaNoSettingsProvider.instance = None
        provider = WaNoSettingsProvider(settings_file)
        return provider

    def test_path_function(self):
        """Test the _path helper function."""
        # The _path function appends to the directory of the simstack module
        test_path = _path("test")
        # We only test that it returns a path with "test" as the basename
        assert os.path.basename(test_path) == "test"
        # And that the directory exists and is absolute
        assert os.path.isabs(os.path.dirname(test_path))
        assert "simstack" in test_path

    def test_init(self, settings_provider, settings_file):
        """Test initialization of WaNoSettingsProvider."""
        assert settings_provider.name == "WaNoSettingsProvider"
        assert settings_provider.settings_file == settings_file

    def test_get_instance_not_instanced(self):
        """Test get_instance without prior initialization and no settings file."""
        WaNoSettingsProvider.instance = None
        with pytest.raises(NotInstancedError):
            WaNoSettingsProvider.get_instance()

    def test_get_instance_with_settings_file(self, settings_file):
        """Test get_instance with settings file."""
        WaNoSettingsProvider.instance = None
        provider = WaNoSettingsProvider.get_instance(settings_file)
        assert provider is not None
        assert provider.settings_file == settings_file

        # Should return the same instance
        provider2 = WaNoSettingsProvider.get_instance()
        assert provider2 is provider

    def test_get_path_settings(self, settings_provider):
        """Test get_path_settings method."""
        # Mock get_value to return test values
        settings_provider.get_value = MagicMock()
        settings_provider.get_value.side_effect = lambda key: f"test_{key}"

        path_settings = settings_provider.get_path_settings()

        assert path_settings["wanoRepo"] == f"test_{SETTING_KEYS['wanoRepo']}"
        assert path_settings["workflows"] == f"test_{SETTING_KEYS['workflows']}"

        # Verify get_value was called with the correct keys
        settings_provider.get_value.assert_any_call(SETTING_KEYS["wanoRepo"])
        settings_provider.get_value.assert_any_call(SETTING_KEYS["workflows"])

    def test_set_path_settings(self, settings_provider):
        """Test set_path_settings method."""
        # Mock set_value
        settings_provider.set_value = MagicMock()

        # Test data
        path_settings = {"wanoRepo": "/test/wano/repo", "workflows": "/test/workflows"}

        settings_provider.set_path_settings(path_settings)

        # Verify set_value was called with the correct arguments
        settings_provider.set_value.assert_any_call(
            SETTING_KEYS["wanoRepo"], "/test/wano/repo"
        )
        settings_provider.set_value.assert_any_call(
            SETTING_KEYS["workflows"], "/test/workflows"
        )

    def test_set_defaults(self, settings_provider):
        """Test _set_defaults method."""
        with patch.object(settings_provider, "set_value") as mock_set_value:
            settings_provider._set_defaults()

            # Verify set_value was called 3 times (for the three defaults)
            assert mock_set_value.call_count == 3

            # Check the calls for each default setting
            mock_set_value.assert_any_call(SETTING_KEYS["registries"], [])

            # We don't check the exact path values as they depend on the OS and directory structure
            # Instead, we check that the keys were set
            calls = [call[0][0] for call in mock_set_value.call_args_list]
            assert SETTING_KEYS["wanoRepo"] in calls
            assert SETTING_KEYS["workflows"] in calls

    def test_actual_defaults(self, settings_provider, temp_dir):
        """Test the actual default values set."""
        # Create a real provider and set defaults
        real_provider = WaNoSettingsProvider(
            os.path.join(temp_dir, "real_settings.yaml")
        )
        real_provider._set_defaults()

        # Verify registries is an empty list
        assert real_provider.get_value(SETTING_KEYS["registries"]) == []

        # Verify wanoRepo and workflows paths are properly set
        # These paths will depend on the actual directory structure
        # Just check that they are strings and not empty
        assert isinstance(real_provider.get_value(SETTING_KEYS["wanoRepo"]), str)
        assert isinstance(real_provider.get_value(SETTING_KEYS["workflows"]), str)
        assert real_provider.get_value(SETTING_KEYS["wanoRepo"]) != ""
        assert real_provider.get_value(SETTING_KEYS["workflows"]) != ""
