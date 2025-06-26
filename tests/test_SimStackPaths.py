import os
from unittest.mock import patch, mock_open

from simstack.SimStackPaths import SimStackPaths


def test_constants():
    """Test that class constants have expected values"""
    assert SimStackPaths._SETTINGS_DIR == "NanoMatch"
    assert SimStackPaths._SETTINGS_FILE == "ssh_clientsettings.yml"


@patch("os.path.realpath")
@patch("os.path.dirname")
def test_get_main_dir(mock_dirname, mock_realpath):
    """Test get_main_dir returns the correct directory path"""
    # Setup mocks
    mock_realpath.return_value = "/path/to/main.py"
    mock_dirname.return_value = "/path/to"

    result = SimStackPaths.get_main_dir()

    # Verify
    assert result == "/path/to"


@patch.object(SimStackPaths, "get_settings_folder_nanomatch")
def test_get_local_hostfile(mock_get_settings_folder_nanomatch):
    """Test get_local_hostfile returns the correct file path"""
    # Setup mock
    mock_get_settings_folder_nanomatch.return_value = "/settings/NanoMatch"

    result = SimStackPaths.get_local_hostfile()

    # Verify
    assert result == os.path.join("/settings/NanoMatch", "local_known_hosts")


@patch("os.path.exists")
@patch("builtins.open", new_callable=mock_open)
@patch.object(SimStackPaths, "get_local_hostfile")
def test_gen_empty_local_hostfile_if_not_present_file_not_exists(
    mock_get_local_hostfile, mock_file, mock_exists
):
    """Test gen_empty_local_hostfile_if_not_present creates file when it doesn't exist"""
    # Setup mocks
    mock_get_local_hostfile.return_value = "/settings/NanoMatch/local_known_hosts"
    mock_exists.return_value = False

    result = SimStackPaths.gen_empty_local_hostfile_if_not_present()

    # Verify
    mock_exists.assert_called_once_with("/settings/NanoMatch/local_known_hosts")
    mock_file.assert_called_once_with("/settings/NanoMatch/local_known_hosts", "wt")
    assert result == "/settings/NanoMatch/local_known_hosts"


@patch("os.path.exists")
@patch("builtins.open", new_callable=mock_open)
@patch.object(SimStackPaths, "get_local_hostfile")
def test_gen_empty_local_hostfile_if_not_present_file_exists(
    mock_get_local_hostfile, mock_file, mock_exists
):
    """Test gen_empty_local_hostfile_if_not_present returns file path when file exists"""
    # Setup mocks
    mock_get_local_hostfile.return_value = "/settings/NanoMatch/local_known_hosts"
    mock_exists.return_value = True

    result = SimStackPaths.gen_empty_local_hostfile_if_not_present()

    # Verify
    mock_exists.assert_called_once_with("/settings/NanoMatch/local_known_hosts")
    mock_file.assert_not_called()
    assert result == "/settings/NanoMatch/local_known_hosts"


@patch.object(SimStackPaths, "get_main_dir")
def test_get_embedded_path(mock_get_main_dir):
    """Test get_embedded_path returns the correct path"""
    # Setup mock
    mock_get_main_dir.return_value = "/path/to/main"

    result = SimStackPaths.get_embedded_path()

    # Verify
    assert result == os.path.join("/path/to/main", "embedded")


@patch.object(SimStackPaths, "get_settings_folder_nanomatch")
def test_get_embedded_sshkey(mock_get_settings_folder_nanomatch):
    """Test get_embedded_sshkey returns the correct path"""
    # Setup mock
    mock_get_settings_folder_nanomatch.return_value = "/settings/NanoMatch"

    result = SimStackPaths.get_embedded_sshkey()

    # Verify
    assert result == os.path.join("/settings/NanoMatch", "embedded_idrsa")


@patch("PySide6.QtCore.QStandardPaths.standardLocations")
def test_get_temp_folder(mock_standard_locations):
    """Test get_temp_folder returns the correct path"""
    # Setup mock for QStandardPaths
    mock_standard_locations.return_value = ["/tmp"]

    result = SimStackPaths.get_temp_folder()

    # Verify
    mock_standard_locations.assert_called_once()
    assert result == "/tmp"


@patch("os.path.isdir")
@patch("PySide6.QtCore.QStandardPaths.standardLocations")
def test_get_settings_folder_config_dir_exists(mock_standard_locations, mock_isdir):
    """Test get_settings_folder returns 'config' when config/NanoMatch exists"""
    # Setup mocks
    mock_isdir.return_value = True

    result = SimStackPaths.get_settings_folder()

    # Verify
    mock_isdir.assert_called_once_with(os.path.join("config", "NanoMatch"))
    mock_standard_locations.assert_not_called()
    assert result == "config"


@patch("os.path.isdir")
@patch("PySide6.QtCore.QStandardPaths.standardLocations")
def test_get_settings_folder_no_config_dir(mock_standard_locations, mock_isdir):
    """Test get_settings_folder returns AppDataLocation when config/NanoMatch doesn't exist"""
    # Setup mocks
    mock_isdir.return_value = False
    mock_standard_locations.return_value = ["/app/data"]

    result = SimStackPaths.get_settings_folder()

    # Verify
    mock_isdir.assert_called_once_with(os.path.join("config", "NanoMatch"))
    mock_standard_locations.assert_called_once()
    assert result == "/app/data"


@patch.object(SimStackPaths, "get_settings_folder")
def test_get_settings_folder_nanomatch(mock_get_settings_folder):
    """Test get_settings_folder_nanomatch returns the correct path"""
    # Setup mock
    mock_get_settings_folder.return_value = "/app/data"

    result = SimStackPaths.get_settings_folder_nanomatch()

    # Verify
    assert result == os.path.join("/app/data", "NanoMatch")


@patch.object(SimStackPaths, "get_settings_folder_nanomatch")
def test_get_settings_file(mock_get_settings_folder_nanomatch):
    """Test get_settings_file returns the correct path"""
    # Setup mock
    mock_get_settings_folder_nanomatch.return_value = "/app/data/NanoMatch"

    result = SimStackPaths.get_settings_file()

    # Verify
    assert result == os.path.join("/app/data/NanoMatch", "ssh_clientsettings.yml")
