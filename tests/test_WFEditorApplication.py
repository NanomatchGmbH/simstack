import pytest
from unittest.mock import patch, MagicMock

from simstack.WFEditorApplication import WFEditorApplication
from simstack.Constants import SETTING_KEYS
from simstack.SSHConnector import OPERATIONS as uops
from simstack.SSHConnector import ERROR as uerror
from SimStackServer.MessageTypes import ErrorCodes


class TestWFEditorApplication:
    """Tests for the WFEditorApplication class."""

    @pytest.fixture
    def app(self):
        """Create a WFEditorApplication instance with mocked dependencies."""
        # Mock dependencies
        with patch(
            "simstack.WFEditorApplication.WFViewManager"
        ) as mock_view_manager_class, patch(
            "simstack.WFEditorApplication.QtClusterSettingsProvider"
        ) as mock_settings_class, patch(
            "simstack.WFEditorApplication.SSHConnector"
        ) as mock_connector_class, patch("simstack.WFEditorApplication.logging"):
            # Create mock instances
            mock_view_manager = MagicMock()
            mock_settings = MagicMock()
            mock_connector = MagicMock()

            # Setup return values
            mock_view_manager_class.return_value = mock_view_manager
            mock_settings_class.get_instance.return_value = mock_settings
            mock_connector_class.return_value = mock_connector

            # Create application (but mock __init__)
            with patch.object(WFEditorApplication, "__init__", lambda self: None):
                app = WFEditorApplication()

                # Set attributes manually
                app._view_manager = mock_view_manager
                app._WFEditorApplication__settings = (
                    mock_settings  # Fix: use proper name mangling
                )
                app._connector = mock_connector
                app._logger = MagicMock()
                app.exec_callback_operation = MagicMock()
                app.exec_operation = MagicMock()
                app.wanos = []

                # Store mocks for assertions
                app._mock_view_manager_class = mock_view_manager_class
                app._mock_settings_class = mock_settings_class
                app._mock_connector_class = mock_connector_class

                return app

    def test_on_save_paths(self, app):
        """Test _on_save_paths method."""
        # Mock methods
        app.update_workflow_list = MagicMock()
        app._update_wanos = MagicMock()

        # Create test path dictionary
        path_dict = {
            "wanoRepo": "/path/to/wano_repo",
            "workflows": "/path/to/workflows",
        }

        # Call method
        app._on_save_paths(path_dict)

        # Verify settings were updated
        app._WFEditorApplication__settings.set_path_settings.assert_called_once_with(
            path_dict
        )
        app._WFEditorApplication__settings.save.assert_called_once()

        # Verify workflow list and WaNos were updated
        app.update_workflow_list.assert_called_once()
        app._update_wanos.assert_called_once()

    def test_on_open_registry_settings(self, app):
        """Test _on_open_registry_settings method."""
        # Mock get_value to return registry settings
        registry_settings = ["registry1", "registry2"]
        app._WFEditorApplication__settings.get_value.return_value = registry_settings

        # Call method
        app._on_open_registry_settings()

        # Verify settings key was requested
        app._WFEditorApplication__settings.get_value.assert_called_once_with(
            SETTING_KEYS["registries"]
        )

        # Verify dialog was opened with correct settings
        app._view_manager.open_dialog_registry_settings.assert_called_once_with(
            registry_settings
        )

    def test_on_open_path_settings(self, app):
        """Test _on_open_path_settings method."""
        # Mock get_path_settings to return path settings
        path_settings = {
            "wanoRepo": "/path/to/wano_repo",
            "workflows": "/path/to/workflows",
        }
        app._WFEditorApplication__settings.get_path_settings.return_value = (
            path_settings
        )

        # Call method
        app._on_open_path_settings()

        # Verify path settings were requested
        app._WFEditorApplication__settings.get_path_settings.assert_called_once()

        # Verify dialog was opened with correct settings
        app._view_manager.open_dialog_path_settings.assert_called_once_with(
            path_settings
        )

    def test_on_error_not_connected(self, app):
        """Test _on_error method with REGISTRY_NOT_CONNECTED error."""
        # Call method with REGISTRY_NOT_CONNECTED error
        app._on_error(
            "registry", uops.CONNECT_REGISTRY.value, uerror.REGISTRY_NOT_CONNECTED.value
        )

        # Verify show_error was called with correct message
        app._view_manager.show_error.assert_called_once()
        assert "not connected" in app._view_manager.show_error.call_args[0][0]

        # Verify logger was not called
        app._logger.error.assert_not_called()

    def test_on_error_connect(self, app):
        """Test _on_error method with CONNECT_REGISTRY operation."""
        # Mock _on_connect_error
        app._on_connect_error = MagicMock()

        # Call method with any error value (using NO_ERROR as a placeholder)
        app._on_error("registry", uops.CONNECT_REGISTRY.value, uerror.NO_ERROR.value)

        # Verify _on_connect_error was called
        app._on_connect_error.assert_called_once_with("registry", uerror.NO_ERROR.value)

        # Verify logger was called
        app._logger.error.assert_called_once()

    def test_on_error_run_single_job(self, app):
        """Test _on_error method with RUN_SINGLE_JOB operation."""
        # Mock _on_run_single_job_error
        app._on_run_single_job_error = MagicMock()

        # Call method
        app._on_error("registry", uops.RUN_SINGLE_JOB.value, uerror.NO_ERROR.value)

        # Verify _on_run_single_job_error was called
        app._on_run_single_job_error.assert_called_once_with(
            "registry", uerror.NO_ERROR.value
        )

        # Verify logger was called
        app._logger.error.assert_called_once()

    def test_on_error_generic(self, app):
        """Test _on_error method with generic error."""
        # Call method with a recognized operation but custom error message
        app._on_error(
            "registry",
            uops.DELETE_FILE.value,
            uerror.NO_ERROR.value,
            "Custom error message",
        )

        # Verify show_error was called with correct arguments
        app._view_manager.show_error.assert_called_once_with(
            "General Error.", "Custom error message"
        )

        # Verify logger was called
        app._logger.error.assert_called_once()

    def test_on_run_single_job_error_not_connected(self, app):
        """Test _on_run_single_job_error with REGISTRY_NOT_CONNECTED error."""
        # Call method
        app._on_run_single_job_error("registry", uerror.REGISTRY_NOT_CONNECTED)

        # Verify show_error was called with correct message
        app._view_manager.show_error.assert_called_once()
        assert (
            "Registry must be connected" in app._view_manager.show_error.call_args[0][0]
        )

    def test_on_run_single_job_error_unknown(self, app):
        """Test _on_run_single_job_error with unknown error."""
        # Call method
        app._on_run_single_job_error("registry", uerror.NO_ERROR)

        # Verify show_error was called with correct message
        app._view_manager.show_error.assert_called_once()
        assert "Unknown Error" in app._view_manager.show_error.call_args[0][0]

    def test_on_fs_job_list_updated(self, app):
        """Test _on_fs_job_list_updated method."""
        # Create test jobs
        jobs = ["job1", "job2"]

        # Call method
        app._on_fs_job_list_updated("registry", jobs)

        # Verify view manager was updated
        app._view_manager.update_job_list.assert_called_once_with(jobs)

    @patch("simstack.WFEditorApplication.SSHConnector")
    def test_on_fs_job_list_update_request(self, mock_ssh_connector, app):
        """Test _on_fs_job_list_update_request method."""
        # Mock _get_current_base_uri
        app._get_current_base_uri = MagicMock(return_value="registry")

        # Mock create_update_job_list_args
        args = {"arg1": "value1"}
        mock_ssh_connector.create_update_job_list_args.return_value = args

        # Call method
        app._on_fs_job_list_update_request()

        # Verify exec_callback_operation was called
        app.exec_callback_operation.emit.assert_called_once()

        # Verify operation
        assert app.exec_callback_operation.emit.call_args[0][0] == uops.UPDATE_JOB_LIST

        # Verify callback
        callback = app.exec_callback_operation.emit.call_args[0][2]
        assert callback[0] == app._on_fs_job_list_updated

    def test_on_workflow_list_updated(self, app):
        """Test _on_workflow_list_updated method."""
        # Create test workflows
        workflows = ["workflow1", "workflow2"]

        # Call method
        app._on_workflow_list_updated("registry", workflows)

        # Verify view manager was updated
        app._view_manager.update_workflow_list.assert_called_once_with(workflows)

    def test_on_fs_list_updated(self, app):
        """Test _on_fs_list_updated method."""
        # Create test files
        path = "/path/to/files"
        files = ["file1", "file2"]

        # Call method
        app._on_fs_list_updated("registry", path, files)

        # Verify view manager was updated
        app._view_manager.update_filesystem_model.assert_called_once_with(path, files)

    def test_on_fs_job_update_request(self, app):
        """Test _on_fs_job_update_request method."""
        # Mock _get_current_registry_name
        app._get_current_registry_name = MagicMock(return_value="registry")

        # Create test path
        path = "/path/to/job"

        # Call method
        app._on_fs_job_update_request(path)

        # Verify connector was called
        app._connector.update_dir_list.assert_called_once()

        # Verify registry name
        assert app._connector.update_dir_list.call_args[0][0] == "registry"

        # Verify path
        assert app._connector.update_dir_list.call_args[0][1] == path

        # Verify callback
        callback = app._connector.update_dir_list.call_args[0][2]
        assert callback[0] == app._on_fs_list_updated

    def test_on_fs_workflow_update_request(self, app):
        """Test _on_fs_workflow_update_request method."""
        # Mock _get_current_registry_name
        app._get_current_registry_name = MagicMock(return_value="registry")

        # Create test workflow ID
        wfid = "workflow1"

        # Call method
        app._on_fs_workflow_update_request(wfid)

        # Verify connector was called
        app._connector.update_workflow_job_list.assert_called_once()

        # Verify registry name
        assert app._connector.update_workflow_job_list.call_args[0][0] == "registry"

        # Verify workflow ID
        assert app._connector.update_workflow_job_list.call_args[0][1] == wfid

        # Verify callback
        callback = app._connector.update_workflow_job_list.call_args[0][2]
        assert callback[0] == app._on_fs_list_updated

    def test_on_fs_directory_update_request(self, app):
        """Test _on_fs_directory_update_request method."""
        # Mock _on_fs_job_update_request
        app._on_fs_job_update_request = MagicMock()

        # Create test path
        path = "/path/to/directory"

        # Call method
        app._on_fs_directory_update_request(path)

        # Verify _on_fs_job_update_request was called
        app._on_fs_job_update_request.assert_called_once_with(path)

    def test_on_file_deleted_success(self, app):
        """Test _on_file_deleted method with success."""
        # Mock _on_fs_job_update_request
        app._on_fs_job_update_request = MagicMock()

        # Create test file
        file_to_delete = "/path/to/directory/file.txt"

        # Call method with success
        app._on_file_deleted(
            "registry", MagicMock(), ErrorCodes.NO_ERROR, to_del=file_to_delete
        )

        # Verify _on_fs_job_update_request was called with directory path
        app._on_fs_job_update_request.assert_called_once_with("/path/to/directory")

        # Verify logger was called
        app._logger.debug.assert_called_once()


    def test_on_job_deleted_success(self, app):
        """Test _on_job_deleted method with success."""
        # Mock _on_fs_job_list_update_request
        app._on_fs_job_list_update_request = MagicMock()

        # Create test job
        job = "job1"

        # Call method with success
        app._on_job_deleted("registry", MagicMock(), ErrorCodes.NO_ERROR, job=job)

        # Verify _on_fs_job_list_update_request was called
        app._on_fs_job_list_update_request.assert_called_once()


    @patch("simstack.WFEditorApplication.SSHConnector")
    def test_on_fs_delete_job(self, mock_ssh_connector, app):
        """Test _on_fs_delete_job method."""
        # Mock _get_current_base_uri
        app._get_current_base_uri = MagicMock(return_value="registry")

        # Mock create_delete_job_args
        args = {"arg1": "value1"}
        mock_ssh_connector.create_delete_job_args.return_value = args

        # Create test job
        job = "job1"

        # Call method
        app._on_fs_delete_job(job)

        # Verify exec_callback_operation was called
        app.exec_callback_operation.emit.assert_called_once()

        # Verify operation
        assert app.exec_callback_operation.emit.call_args[0][0] == uops.DELETE_JOB

        # Verify callback
        callback = app.exec_callback_operation.emit.call_args[0][2]
        assert callback[0] == app._on_job_deleted
        assert callback[2]["job"] == job
