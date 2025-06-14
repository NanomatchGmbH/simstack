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

    def test_on_registry_changed(self, app):
        """Test _on_registry_changed method."""
        # Mock _reconnect_remote
        app._reconnect_remote = MagicMock()

        # Call method
        registry_name = "test_registry"
        app._on_registry_changed(registry_name)

        # Verify _reconnect_remote was called
        app._reconnect_remote.assert_called_once_with(registry_name)

    def test_on_registry_connect(self, app):
        """Test _on_registry_connect method."""
        # Mock _connect_remote
        app._connect_remote = MagicMock()

        # Call method
        registry_name = "test_registry"
        app._on_registry_connect(registry_name)

        # Verify _connect_remote was called
        app._connect_remote.assert_called_once_with(registry_name)

    def test_on_registry_disconnect(self, app):
        """Test _on_registry_disconnect method."""
        # Mock _disconnect_remote
        app._disconnect_remote = MagicMock()

        # Call method
        app._on_registry_disconnect()

        # Verify _disconnect_remote was called
        app._disconnect_remote.assert_called_once()

    def test_on_resources_updated(self, app):
        """Test _on_resources_updated method."""
        # Create mock resources
        mock_resources = MagicMock()
        mock_resources.get_queues.return_value = ["queue1", "queue2"]

        # Call method (should just print queues)
        app._on_resources_updated("registry", mock_resources)

        # Verify get_queues was called
        mock_resources.get_queues.assert_called_once()

    @patch("simstack.WFEditorApplication.SSHConnector")
    def test_on_resources_update_request(self, mock_ssh_connector, app):
        """Test _on_resources_update_request method."""
        # Mock _get_current_base_uri
        app._get_current_base_uri = MagicMock(return_value="registry")

        # Mock create_update_resources_args
        args = {"arg1": "value1"}
        mock_ssh_connector.create_update_resources_args.return_value = args

        # Call method
        app._on_resources_update_request()

        # Verify exec_callback_operation was called
        app.exec_callback_operation.emit.assert_called_once()

        # Verify operation
        assert app.exec_callback_operation.emit.call_args[0][0] == uops.UPDATE_RESOURCES

        # Verify callback
        callback = app.exec_callback_operation.emit.call_args[0][2]
        assert callback[0] == app._on_resources_updated

    def test_on_fs_worflow_list_update_request(self, app):
        """Test _on_fs_worflow_list_update_request method."""
        # Mock _get_current_registry_name
        app._get_current_registry_name = MagicMock(return_value="registry")

        # Call method
        app._on_fs_worflow_list_update_request()

        # Verify connector was called
        app._connector.update_workflow_list.assert_called_once()

        # Verify registry name
        assert app._connector.update_workflow_list.call_args[0][0] == "registry"

        # Verify callback
        callback = app._connector.update_workflow_list.call_args[0][1]
        assert callback[0] == app._on_workflow_list_updated

    def test_on_saved_workflows_update_request(self, app):
        """Test _on_saved_workflows_update_request method."""
        # Mock _update_workflow_list
        app._update_workflow_list = MagicMock()

        # Call method
        app._on_saved_workflows_update_request("/path")

        # Verify _update_workflow_list was called
        app._update_workflow_list.assert_called_once()

    def test_on_fs_download(self, app):
        """Test _on_fs_download method."""
        # Mock _get_current_registry_name
        app._get_current_registry_name = MagicMock(return_value="registry")

        # Create test paths
        from_path = "/remote/file.txt"
        to_path = "/local/file.txt"

        # Call method
        app._on_fs_download(from_path, to_path)

        # Verify connector was called
        app._connector.download_file.assert_called_once()

        # Verify registry name
        assert app._connector.download_file.call_args[0][0] == "registry"

        # Verify paths
        assert app._connector.download_file.call_args[0][1] == from_path
        assert app._connector.download_file.call_args[0][2] == to_path

    def test_on_fs_upload(self, app):
        """Test _on_fs_upload method."""
        # Mock _get_current_registry_name
        app._get_current_registry_name = MagicMock(return_value="registry")

        # Create test data
        local_files = ["/local/file1.txt", "/local/file2.txt"]
        dest_dir = "/remote/directory"

        # Call method
        app._on_fs_upload(local_files, dest_dir)

        # Verify connector was called
        app._connector.upload_files.assert_called_once()

        # Verify registry name
        assert app._connector.upload_files.call_args[0][0] == "registry"

        # Verify files and destination
        assert app._connector.upload_files.call_args[0][1] == local_files
        assert app._connector.upload_files.call_args[0][2] == dest_dir

    def test_on_file_deleted_error(self, app):
        """Test _on_file_deleted method with error."""
        # Create mock status
        mock_status = MagicMock()
        mock_status.name = "ERROR_STATUS"

        # Create test file
        file_to_delete = "/path/to/file.txt"

        # Call method with error
        app._on_file_deleted(
            "registry", mock_status, ErrorCodes.CONN_ERROR, to_del=file_to_delete
        )

        # Verify show_error was called
        app._view_manager.show_error.assert_called_once()
        assert "Failed to delete job" in app._view_manager.show_error.call_args[0][0]

    def test_on_job_deleted_error(self, app):
        """Test _on_job_deleted method with error."""
        # Create mock status
        mock_status = MagicMock()
        mock_status.name = "ERROR_STATUS"

        # Create test job
        job = "job1"

        # Call method with error
        app._on_job_deleted("registry", mock_status, ErrorCodes.CONN_ERROR, job=job)

        # Verify show_error was called
        app._view_manager.show_error.assert_called_once()
        assert "Failed to delete job" in app._view_manager.show_error.call_args[0][0]

    def test_on_job_aborted_success(self, app):
        """Test _on_job_aborted method with success."""
        # Mock _on_fs_job_list_update_request
        app._on_fs_job_list_update_request = MagicMock()

        # Create test job
        job = "job1"

        # Call method with success
        app._on_job_aborted("registry", MagicMock(), ErrorCodes.NO_ERROR, job=job)

        # Verify _on_fs_job_list_update_request was called
        app._on_fs_job_list_update_request.assert_called_once()

    def test_on_job_aborted_error(self, app):
        """Test _on_job_aborted method with error."""
        # Create mock status
        mock_status = MagicMock()
        mock_status.name = "ERROR_STATUS"

        # Create test job
        job = "job1"

        # Call method with error
        app._on_job_aborted("registry", mock_status, ErrorCodes.CONN_ERROR, job=job)

        # Verify show_error was called
        app._view_manager.show_error.assert_called_once()
        assert "Failed to abort job" in app._view_manager.show_error.call_args[0][0]

    @patch("simstack.WFEditorApplication.SSHConnector")
    def test_on_fs_abort_job(self, mock_ssh_connector, app):
        """Test _on_fs_abort_job method."""
        # Mock _get_current_base_uri
        app._get_current_base_uri = MagicMock(return_value="registry")

        # Mock create_abort_job_args
        args = {"arg1": "value1"}
        mock_ssh_connector.create_abort_job_args.return_value = args

        # Create test job
        job = "job1"

        # Call method
        app._on_fs_abort_job(job)

        # Verify exec_callback_operation was called
        app.exec_callback_operation.emit.assert_called_once()

        # Verify operation
        assert app.exec_callback_operation.emit.call_args[0][0] == uops.ABORT_JOB

        # Verify callback
        callback = app.exec_callback_operation.emit.call_args[0][2]
        assert callback[0] == app._on_job_aborted
        assert callback[2]["job"] == job

    @patch("simstack.WFEditorApplication.webbrowser")
    def test_on_fs_browse_workflow(self, mock_webbrowser, app):
        """Test _on_fs_browse_workflow method."""
        # Mock _get_current_registry_name
        app._get_current_registry_name = MagicMock(return_value="registry")

        # Mock get_workflow_url
        mock_url = "http://example.com/workflow/workflow1"
        app._connector.get_workflow_url.return_value = mock_url

        # Create test workflow
        workflow = "workflow1"

        # Call method
        app._on_fs_browse_workflow(workflow)

        # Verify connector was called
        app._connector.get_workflow_url.assert_called_once_with("registry", workflow)

        # Verify webbrowser was called
        mock_webbrowser.open_new_tab.assert_called_once_with(mock_url)

    def test_on_fs_delete_workflow(self, app):
        """Test _on_fs_delete_workflow method."""
        # Mock _get_current_registry_name
        app._get_current_registry_name = MagicMock(return_value="registry")

        # Create test workflow
        workflow = "workflow1"

        # Call method
        app._on_fs_delete_workflow(workflow)

        # Verify connector was called
        app._connector.delete_workflow.assert_called_once()

        # Verify registry name
        assert app._connector.delete_workflow.call_args[0][0] == "registry"

        # Verify workflow
        assert app._connector.delete_workflow.call_args[0][1] == workflow

        # Verify callback
        callback = app._connector.delete_workflow.call_args[0][2]
        assert callback[0] == app._on_workflow_deleted
        assert callback[2]["workflow"] == workflow

    def test_on_fs_abort_workflow(self, app):
        """Test _on_fs_abort_workflow method."""
        # Mock _get_current_registry_name
        app._get_current_registry_name = MagicMock(return_value="registry")

        # Create test workflow
        workflow = "workflow1"

        # Call method
        app._on_fs_abort_workflow(workflow)

        # Verify connector was called
        app._connector.abort_workflow.assert_called_once()

        # Verify registry name
        assert app._connector.abort_workflow.call_args[0][0] == "registry"

        # Verify workflow
        assert app._connector.abort_workflow.call_args[0][1] == workflow

        # Verify callback
        callback = app._connector.abort_workflow.call_args[0][2]
        assert callback[0] == app._on_workflow_aborted
        assert callback[2]["workflow"] == workflow

    def test_on_workflow_deleted_success(self, app):
        """Test _on_workflow_deleted method with success."""
        # Mock _on_fs_worflow_list_update_request
        app._on_fs_worflow_list_update_request = MagicMock()

        # Create test workflow
        workflow = "workflow1"

        # Call method with success
        app._on_workflow_deleted(
            "registry", MagicMock(), ErrorCodes.NO_ERROR, workflow=workflow
        )

        # Verify _on_fs_worflow_list_update_request was called
        app._on_fs_worflow_list_update_request.assert_called_once()

    def test_on_workflow_deleted_error(self, app):
        """Test _on_workflow_deleted method with error."""
        # Create mock status
        mock_status = MagicMock()
        mock_status.name = "ERROR_STATUS"

        # Create test workflow
        workflow = "workflow1"

        # Call method with error
        app._on_workflow_deleted(
            "registry", mock_status, ErrorCodes.CONN_ERROR, workflow=workflow
        )

        # Verify show_error was called
        app._view_manager.show_error.assert_called_once()
        assert (
            "Failed to delete workflow" in app._view_manager.show_error.call_args[0][0]
        )

    def test_on_fs_delete_file(self, app):
        """Test _on_fs_delete_file method."""
        # Mock _get_current_registry_name
        app._get_current_registry_name = MagicMock(return_value="registry")

        # Create test filename
        filename = "/path/to/file.txt"

        # Call method
        app._on_fs_delete_file(filename)

        # Verify connector was called
        app._connector.delete_file.assert_called_once()

        # Verify registry name
        assert app._connector.delete_file.call_args[0][0] == "registry"

        # Verify filename
        assert app._connector.delete_file.call_args[0][1] == filename

        # Verify callback
        callback = app._connector.delete_file.call_args[0][2]
        assert callback[0] == app._on_file_deleted
        assert callback[2]["to_del"] == filename

    def test_set_current_registry_name(self, app):
        """Test _set_current_registry_name method."""
        registry_name = "test_registry"

        # Call method
        app._set_current_registry_name(registry_name)

        # Verify internal state
        assert app._current_registry_name == registry_name

    def test_get_current_registry_name(self, app):
        """Test _get_current_registry_name method."""
        # Set internal state
        registry_name = "test_registry"
        app._current_registry_name = registry_name

        # Call method
        result = app._get_current_registry_name()

        # Verify result
        assert result == registry_name

    def test_get_current_registry(self, app):
        """Test _get_current_registry method."""
        # Set up mocks
        registry_name = "test_registry"
        mock_registry = MagicMock()
        app._registries = {registry_name: mock_registry}
        app._get_current_registry_name = MagicMock(return_value=registry_name)

        # Call method
        result = app._get_current_registry()

        # Verify result
        assert result == mock_registry

    def test_get_current_base_uri(self, app):
        """Test _get_current_base_uri method."""
        # Set up mocks
        mock_registry = MagicMock()
        mock_registry.base_URI = "http://example.com"
        app._get_current_registry = MagicMock(return_value=mock_registry)

        # Call method
        result = app._get_current_base_uri()

        # Verify result
        assert result == "http://example.com"

    @patch("simstack.WFEditorApplication.QtClusterSettingsProvider")
    def test_get_registry_names(self, mock_settings_provider, app):
        """Test _get_registry_names method."""
        # Mock get_registries
        mock_registries = {"reg1": {}, "reg2": {}}
        mock_settings_provider.get_registries.return_value = mock_registries

        # Call method
        result = app._get_registry_names()

        # Verify result
        assert result == ["reg1", "reg2"]

    def test_get_default_registry(self, app):
        """Test _get_default_registry method."""
        # Call method
        result = app._get_default_registry()

        # Verify result (should be 0)
        assert result == 0

    def test_update_workflow_list(self, app):
        """Test update_workflow_list method."""
        # Mock _update_workflow_list
        app._update_workflow_list = MagicMock()

        # Call method
        app.update_workflow_list()

        # Verify _update_workflow_list was called
        app._update_workflow_list.assert_called_once()

    def test_client_about_to_exit(self, app):
        """Test _client_about_to_exit method."""
        # Mock exit
        app.exit = MagicMock()

        # Call method
        app._client_about_to_exit()

        # Verify exit was called
        app.exit.assert_called_once()

    def test_exit(self, app):
        """Test exit method."""
        # Call method
        app.exit()

        # Verify view manager and connector exit were called
        app._view_manager.exit.assert_called_once()
        app._connector.quit.assert_called_once()

    def test_set_disconnected(self, app):
        """Test _set_disconnected method."""
        # Call method
        app._set_disconnected()

        # Verify view_manager was called with correct status
        app._view_manager.set_registry_connection_status.assert_called_once_with(
            app._view_manager.REGISTRY_CONNECTION_STATES.disconnected
        )

    def test_set_connected(self, app):
        """Test _set_connected method."""
        # Call method
        app._set_connected()

        # Verify view_manager was called with correct status
        app._view_manager.set_registry_connection_status.assert_called_once_with(
            app._view_manager.REGISTRY_CONNECTION_STATES.connected
        )

    def test_set_connecting(self, app):
        """Test _set_connecting method."""
        # Call method
        app._set_connecting()

        # Verify view_manager was called with correct status
        app._view_manager.set_registry_connection_status.assert_called_once_with(
            app._view_manager.REGISTRY_CONNECTION_STATES.connecting
        )

    def test_cb_connect_success(self, app):
        """Test _cb_connect method with success."""
        # Mock _set_connected
        app._set_connected = MagicMock()

        registry_name = "test_registry"

        # Call method with success
        app._cb_connect(
            "base_uri", ErrorCodes.NO_ERROR, "status", registry_name=registry_name
        )

        # Verify logger was called
        app._logger.info.assert_called_once_with("Connected.")

        # Verify _set_connected was called
        app._set_connected.assert_called_once()

    def test_cb_connect_error(self, app):
        """Test _cb_connect method with error."""
        # Mock _set_disconnected
        app._set_disconnected = MagicMock()

        registry_name = "test_registry"

        # Call method with error
        app._cb_connect(
            "base_uri", ErrorCodes.CONN_ERROR, "status", registry_name=registry_name
        )

        # Verify logger was called
        app._logger.error.assert_called_once()

        # Verify show_error was called
        app._view_manager.show_error.assert_called_once()
        assert "Failed to connect" in app._view_manager.show_error.call_args[0][0]

        # Verify _set_disconnected was called
        app._set_disconnected.assert_called_once()

    def test_cb_connect_no_registry_name(self, app):
        """Test _cb_connect method without registry name."""
        # Call method without registry name
        app._cb_connect("base_uri", ErrorCodes.NO_ERROR, "status")

        # Verify logger error was called
        app._logger.error.assert_called_once_with("Callback did not get expected data.")

    def test_cb_disconnect(self, app):
        """Test _cb_disconnect method."""
        # Mock _set_disconnected
        app._set_disconnected = MagicMock()

        # Call method
        app._cb_disconnect(ErrorCodes.NO_ERROR, "status", registry_name="test_registry")

        # Verify _set_disconnected was called
        app._set_disconnected.assert_called_once()

    def test_disconnect_remote(self, app):
        """Test _disconnect_remote method."""
        # Mock methods
        app._get_current_registry_name = MagicMock(return_value="test_registry")

        # Call method
        app._disconnect_remote()

        # Verify logger was called
        app._logger.info.assert_called_once_with("Disconnecting from registry")

        # Verify connector was called
        app._connector.disconnect_registry.assert_called_once()

        # Verify callback
        callback = app._connector.disconnect_registry.call_args[0][1]
        assert callback[0] == app._cb_disconnect
        assert callback[2]["registry_name"] == "test_registry"

    @patch("simstack.WFEditorApplication.WFViewManager")
    def test_connect_remote_empty_registry(self, mock_view_manager_class, app):
        """Test _connect_remote method with empty registry name."""
        # Call method with empty registry name
        app._connect_remote("")

        # Verify show_error was called
        mock_view_manager_class.show_error.assert_called_once()
        assert (
            "No server definition" in mock_view_manager_class.show_error.call_args[0][0]
        )

    def test_connect_remote_success(self, app):
        """Test _connect_remote method with valid registry."""
        # Mock methods
        app._set_connecting = MagicMock()
        app._set_current_registry_name = MagicMock()
        app._get_current_registry = MagicMock()

        registry_name = "test_registry"

        # Call method
        app._connect_remote(registry_name)

        # Verify _set_connecting was called
        app._set_connecting.assert_called_once()

        # Verify registry name was set
        app._set_current_registry_name.assert_called_once_with(registry_name)

        # Verify _get_current_registry was called
        app._get_current_registry.assert_called_once()

        # Verify logger was called
        app._logger.info.assert_called_once()
        assert "Connecting to registry" in app._logger.info.call_args[0][0]

        # Verify connector was called
        app._connector.connect_registry.assert_called_once()

    def test_reconnect_remote(self, app):
        """Test _reconnect_remote method."""
        # Mock methods
        app._set_connecting = MagicMock()
        app._get_current_registry_name = MagicMock(return_value="old_registry")
        app._disconnect_remote = MagicMock()
        app._connect_remote = MagicMock()

        registry_name = "new_registry"

        # Call method
        app._reconnect_remote(registry_name)

        # Verify logger was called
        app._logger.info.assert_called_once_with("Reconnecting to Registry.")

        # Verify _set_connecting was called
        app._set_connecting.assert_called_once()

        # Verify disconnect was called
        app._disconnect_remote.assert_called_once_with(no_status_update=True)

        # Verify connect was called
        app._connect_remote.assert_called_once_with(registry_name)

    @patch("simstack.WFEditorApplication.datetime")
    def test_run_workflow(self, mock_datetime, app):
        """Test run_workflow method."""
        # Mock datetime
        mock_now = MagicMock()
        mock_now.strftime.return_value = "2023-01-01-12h30m45s"
        mock_datetime.datetime.now.return_value = mock_now

        # Mock _get_current_registry_name
        app._get_current_registry_name = MagicMock(return_value="test_registry")

        # Create test data
        xml = "<workflow>test</workflow>"
        directory = "/test/directory"
        name = "test_workflow"

        # Call method
        app.run_workflow(xml, directory, name)

        # Verify connector was called
        app._connector.run_workflow_job.assert_called_once()

        # Verify parameters
        args = app._connector.run_workflow_job.call_args[0]
        assert args[0] == "test_registry"
        assert args[1] == "2023-01-01-12h30m45s-test_workflow"
        assert args[2] == "/test/directory/workflow_data"
        assert args[3] == xml

    @patch("simstack.WFEditorApplication.os.path.join")
    def test_run_workflow_with_path_join(self, mock_join, app):
        """Test run_workflow method with path joining."""
        # Mock path join
        mock_join.return_value = "/test/directory/workflow_data"

        # Mock other dependencies
        with patch("simstack.WFEditorApplication.datetime") as mock_datetime:
            mock_now = MagicMock()
            mock_now.strftime.return_value = "2023-01-01-12h30m45s"
            mock_datetime.datetime.now.return_value = mock_now

            app._get_current_registry_name = MagicMock(return_value="test_registry")

            # Create test data
            xml = "<workflow>test</workflow>"
            directory = "/test/directory"
            name = "test_workflow"

            # Call method
            app.run_workflow(xml, directory, name)

            # Verify path join was called
            mock_join.assert_called_once_with(directory, "workflow_data")

    def test_get_registry_by_name(self, app):
        """Test _get_registry_by_name method."""
        # Set up mock registries
        registry_name = "test_registry"
        mock_registry = MagicMock()
        app._registries = {registry_name: mock_registry}

        # Call method
        result = app._get_registry_by_name(registry_name)

        # Verify result
        assert result == mock_registry

    @patch("simstack.WFEditorApplication.SETTING_KEYS")
    def test_get_current_workflow_uri(self, mock_setting_keys, app):
        """Test _get_current_workflow_uri method."""
        # Mock setting keys
        mock_setting_keys.__getitem__.return_value = "registry.workflows"

        # Set up mock registry
        mock_registry = MagicMock()
        mock_registry.__getitem__.return_value = "http://example.com/workflows"
        app._get_current_registry = MagicMock(return_value=mock_registry)

        # Call method
        result = app._get_current_workflow_uri()

        # Verify result
        assert result == "http://example.com/workflows"

    def test_get_current_workflow_uri_none_registry(self, app):
        """Test _get_current_workflow_uri method with None registry."""
        # Set up None registry
        app._get_current_registry = MagicMock(return_value=None)

        # Call method
        result = app._get_current_workflow_uri()

        # Verify result
        assert result == ""

    def test_update_wanos(self, app):
        """Test _update_wanos method."""

        # Mock methods - note that the method assigns to self.wanos directly
        def mock_load_wanos(path):
            app.wanos = ["wano1", "wano2"]
            return ["wano1", "wano2"]

        app._WFEditorApplication__load_wanos_from_repo = MagicMock(
            side_effect=mock_load_wanos
        )
        app._WFEditorApplication__settings.get_value.return_value = "/path/to/wanos"

        # Call method
        app._update_wanos()

        # Verify settings were accessed
        app._WFEditorApplication__settings.get_value.assert_called_once()

        # Verify load was called
        app._WFEditorApplication__load_wanos_from_repo.assert_called_once_with(
            "/path/to/wanos"
        )

        # Verify view manager was updated with self.wanos
        app._view_manager.update_wano_list.assert_called_once_with(["wano1", "wano2"])

    def test_update_workflow_list_internal(self, app):
        """Test _update_workflow_list method."""
        # Mock methods
        app._WFEditorApplication__load_saved_workflows = MagicMock(
            return_value=["wf1", "wf2"]
        )
        app._WFEditorApplication__settings.get_value.return_value = "/path/to/workflows"

        # Call method
        app._update_workflow_list()

        # Verify settings were accessed
        app._WFEditorApplication__settings.get_value.assert_called_once()

        # Verify load was called
        app._WFEditorApplication__load_saved_workflows.assert_called_once_with(
            "/path/to/workflows"
        )

        # Verify view manager was updated
        app._view_manager.update_saved_workflows_list.assert_called_once_with(
            ["wf1", "wf2"]
        )

    def test_update_saved_registries(self, app):
        """Test _update_saved_registries method."""
        # Mock methods
        app._get_default_registry = MagicMock(return_value=0)
        app._get_registry_names = MagicMock(return_value=["reg1", "reg2"])

        # Call method
        app._update_saved_registries()

        # Verify view manager was updated
        app._view_manager.update_registries.assert_called_once_with(
            ["reg1", "reg2"], selected=0
        )

    def test_update_all(self, app):
        """Test _update_all method."""
        # Mock methods
        app._update_saved_registries = MagicMock()
        app._update_wanos = MagicMock()
        app._update_workflow_list = MagicMock()

        # Call method
        app._update_all()

        # Verify all update methods were called
        app._update_saved_registries.assert_called_once()
        app._update_wanos.assert_called_once()
        app._update_workflow_list.assert_called_once()
