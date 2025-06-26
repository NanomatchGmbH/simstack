import pytest
from unittest.mock import patch, MagicMock

from simstack.SSHConnector import SSHConnector, OPERATIONS, ERROR


# Skip the eagain_catcher tests as they require more complex mocking
# In a real environment, we would use a more targeted approach
# by importing WFViewManager directly and mocking it at the module level


@pytest.fixture
def mock_qtcluster_provider():
    with patch("simstack.SSHConnector.QtClusterSettingsProvider") as mock:
        # Setup registry mock
        registry = MagicMock()
        registry.base_URI = "test_uri"
        registry.ssh_private_key = "test_key"
        registry.extra_config = {}
        registry.queueing_system = "test_queue"
        registry.queue = "default_queue"
        registry.basepath = "/test/path"
        registry.username = "test_user"
        registry.port = 22

        # Setup get_registries to return a dict with our registry
        mock.get_registries.return_value = {"test_registry": registry}
        yield mock


@pytest.fixture
def mock_clustermanager():
    with patch("simstack.SSHConnector.ClusterManager") as mock:
        # Setup a mock cluster manager instance
        cm_instance = MagicMock()
        cm_instance.is_connected.return_value = True
        cm_instance.get_workflow_list.return_value = []

        # Make the constructor return our mock instance
        mock.return_value = cm_instance
        yield mock, cm_instance


@pytest.fixture
def mock_local_clustermanager():
    with patch("simstack.SSHConnector.LocalClusterManager") as mock:
        # Setup a mock cluster manager instance
        cm_instance = MagicMock()
        cm_instance.is_connected.return_value = True
        cm_instance.get_workflow_list.return_value = []

        # Make the constructor return our mock instance
        mock.return_value = cm_instance
        yield mock, cm_instance


@pytest.fixture
def ssh_connector(mock_qtcluster_provider):
    with patch("simstack.SSHConnector.logging"):
        connector = SSHConnector()
        yield connector


class TestSSHConnector:
    """Test the SSHConnector class."""

    def test_init(self, ssh_connector, mock_qtcluster_provider):
        """Test initialization of SSHConnector."""
        assert (
            ssh_connector._registries
            == mock_qtcluster_provider.get_registries.return_value
        )
        assert ssh_connector._clustermanagers == {}
        assert ssh_connector.workers == {}

    def test_emit_error(self, ssh_connector):
        """Test _emit_error method."""
        # Setup mock for the error signal
        ssh_connector.error = MagicMock()

        # Call the method
        ssh_connector._emit_error(
            "base_uri", OPERATIONS.CONNECT_REGISTRY, ERROR.AUTH_SETUP_FAILED
        )

        # Verify the signal was emitted with correct parameters
        ssh_connector.error.emit.assert_called_once_with(
            "base_uri",
            OPERATIONS.CONNECT_REGISTRY.value,
            ERROR.AUTH_SETUP_FAILED.value,
            "",
        )

    def test_emit_error_with_message(self, ssh_connector):
        """Test _emit_error method with custom message."""
        # Setup mock for the error signal
        ssh_connector.error = MagicMock()

        # Call the method
        ssh_connector._emit_error(
            "base_uri",
            OPERATIONS.CONNECT_REGISTRY,
            ERROR.AUTH_SETUP_FAILED,
            "Error message",
        )

        # Verify the signal was emitted with correct parameters
        ssh_connector.error.emit.assert_called_once_with(
            "base_uri",
            OPERATIONS.CONNECT_REGISTRY.value,
            ERROR.AUTH_SETUP_FAILED.value,
            "Error message",
        )

    @patch("simstack.SSHConnector.SimStackPaths")
    def test_connect_registry_disconnects_if_connected(
        self, mock_paths, ssh_connector, mock_clustermanager
    ):
        """Test connect_registry disconnects first if already connected."""
        # Setup
        cm_class, cm_instance = mock_clustermanager
        ssh_connector._clustermanagers = {"test_registry": cm_instance}
        callback = MagicMock()

        # Call the method
        with patch.object(ssh_connector, "start_server"):
            ssh_connector.connect_registry("test_registry", callback)

        # Verify - the implementation does disconnect first if already connected
        callback.assert_called_once()
        cm_instance.disconnect.assert_called_once()

    @patch("simstack.SSHConnector.SimStackPaths")
    def test_connect_registry_new_connection(
        self, mock_paths, ssh_connector, mock_clustermanager
    ):
        """Test connect_registry for a new connection."""
        # Setup
        cm_class, cm_instance = mock_clustermanager
        # Replace the _clustermanagers to ensure we're testing a new connection
        ssh_connector._clustermanagers = {}
        callback = MagicMock()

        # This test requires more complex patching as the code
        # interacts with multiple modules during connection
        with patch.object(ssh_connector, "start_server"), patch.object(
            cm_instance, "load_extra_host_keys"
        ), patch.object(cm_instance, "connect"):
            # Call the method
            ssh_connector.connect_registry("test_registry", callback)

            # Verify callback was called
            callback.assert_called_once()

    @patch("simstack.SSHConnector.SimStackPaths")
    @patch("simstack.SSHConnector.QMessageBox")
    def test_connect_registry_raises_without_callback(
        self, mock_qmessagebox, mock_paths, ssh_connector, mock_clustermanager
    ):
        """Test connect_registry raises exception without a callback."""
        # Setup - No callback provided
        with pytest.raises(TypeError):
            ssh_connector.connect_registry("test_registry")

    def test_disconnect_registry(self, ssh_connector, mock_clustermanager):
        """Test disconnect_registry method."""
        # Setup
        cm_class, cm_instance = mock_clustermanager
        ssh_connector._clustermanagers = {"test_registry": cm_instance}
        callback = MagicMock()

        # Call the method
        ssh_connector.disconnect_registry("test_registry", callback)

        # Verify
        cm_instance.disconnect.assert_called_once()
        callback.assert_called_once()

    def test_exit(self, ssh_connector, mock_clustermanager):
        """Test exit method."""
        # Setup
        cm_class, cm_instance = mock_clustermanager
        ssh_connector._clustermanagers = {"test_registry": cm_instance}

        # Call the method
        ssh_connector.exit()

        # Verify
        cm_instance.disconnect.assert_called_once()

    def test_update_workflow_list(self, ssh_connector, mock_clustermanager):
        """Test update_workflow_list method."""
        # Setup
        cm_class, cm_instance = mock_clustermanager
        ssh_connector._clustermanagers = {"test_registry": cm_instance}

        # Configure get_workflow_list to return test data
        cm_instance.get_workflow_list.return_value = ["workflow1", "workflow2"]

        # Create mock callback
        callback = MagicMock()

        # Call the method
        ssh_connector.update_workflow_list("test_registry", callback)

        # Verify
        cm_instance.get_workflow_list.assert_called_once()
        callback.assert_called_once_with("test_registry", ["workflow1", "workflow2"])

    def test_get_cm_not_connected(self, ssh_connector):
        """Test _get_cm method when not connected."""
        # Call the method with non-existent registry
        with pytest.raises(ConnectionError) as excinfo:
            ssh_connector._get_cm("nonexistent_registry")

        # Verify
        assert "Clustermanager nonexistent_registry was not connected" in str(
            excinfo.value
        )

    def test_get_cm_connected(self, ssh_connector, mock_clustermanager):
        """Test _get_cm method when connected."""
        # Setup
        cm_class, cm_instance = mock_clustermanager
        ssh_connector._clustermanagers = {"test_registry": cm_instance}

        # Call the method
        result = ssh_connector._get_cm("test_registry")

        # Verify
        assert result == cm_instance

    def test_exec_callback_simple(self, ssh_connector):
        """Test _exec_callback with simple function."""
        # Setup
        callback = MagicMock()

        # Call the method
        ssh_connector._exec_callback(callback, "arg1", "arg2", kwarg1="value1")

        # Verify
        callback.assert_called_once_with("arg1", "arg2", kwarg1="value1")

    def test_exec_callback_tuple(self, ssh_connector):
        """Test _exec_callback with tuple format."""
        # Setup
        callback_func = MagicMock()
        callback = (callback_func, ("cb_arg1", "cb_arg2"), {"cb_kwarg": "cb_value"})

        # Call the method
        ssh_connector._exec_callback(callback, "arg1", "arg2")

        # Verify
        callback_func.assert_called_once_with(
            "cb_arg1", "cb_arg2", "arg1", "arg2", cb_kwarg="cb_value"
        )

    def test_quit(self, ssh_connector):
        """Test quit method."""
        # Mock exit
        ssh_connector.exit = MagicMock()

        # Call method
        ssh_connector.quit()

        # Verify exit was called
        ssh_connector.exit.assert_called_once()

    @patch("simstack.SSHConnector.os.path.dirname")
    @patch("simstack.SSHConnector.os.path.realpath")
    def test_get_main_par_dir(self, mock_realpath, mock_dirname, ssh_connector):
        """Test _get_main_par_dir method."""
        # Mock the path operations
        mock_realpath.return_value = "/test/path/main.py"
        mock_dirname.return_value = "/test/path"

        # Call method
        result = ssh_connector._get_main_par_dir()

        # Verify result
        assert result == "/test/path"

    def test_get_error_or_fail_registry_not_connected(self, ssh_connector):
        """Test _get_error_or_fail when registry not connected."""
        # Setup empty workers
        ssh_connector.workers = {}

        # Mock _emit_error
        ssh_connector._emit_error = MagicMock()

        # Call method
        result = ssh_connector._get_error_or_fail("test_uri")

        # Verify error was emitted and None returned
        ssh_connector._emit_error.assert_called_once_with(
            "test_uri", OPERATIONS.RUN_SINGLE_JOB, ERROR.REGISTRY_NOT_CONNECTED
        )
        assert result is None

    def test_get_error_or_fail_connected(self, ssh_connector):
        """Test _get_error_or_fail when registry is connected."""
        # Setup mock worker
        mock_worker = MagicMock()
        ssh_connector.workers = {"test_uri": {"worker": mock_worker}}

        # Call method
        result = ssh_connector._get_error_or_fail("test_uri")

        # Verify worker was returned
        assert result == mock_worker

    def test_start_server(self, ssh_connector, mock_clustermanager):
        """Test start_server method."""
        # Setup
        cm_class, cm_instance = mock_clustermanager
        ssh_connector._clustermanagers = {"test_registry": cm_instance}

        # Mock registry with sw_dir_on_resource
        registry = MagicMock()
        registry.sw_dir_on_resource = "/test/sw/dir"
        ssh_connector._registries = {"test_registry": registry}

        # Mock cluster manager methods
        cm_instance.get_server_command_from_software_directory.return_value = (
            "test_command"
        )

        # Call method
        result = ssh_connector.start_server("test_registry")

        # Verify
        cm_instance.get_server_command_from_software_directory.assert_called_once_with(
            "/test/sw/dir"
        )
        cm_instance.connect_zmq_tunnel.assert_called_once_with("test_command")
        assert result.name == "NO_ERROR"  # ErrorCodes.NO_ERROR

    def test_update_job_list(self, ssh_connector):
        """Test update_job_list method."""
        # Setup mock worker
        mock_worker = MagicMock()
        ssh_connector.workers = {"test_uri": {"worker": mock_worker}}

        callback = MagicMock()

        # Call method
        ssh_connector.update_job_list("test_uri", callback)

        # Verify worker method was called
        mock_worker.update_job_list.assert_called_once_with(callback, "test_uri")

    def test_update_job_list_not_connected(self, ssh_connector):
        """Test update_job_list when not connected."""
        # Setup empty workers
        ssh_connector.workers = {}
        ssh_connector._emit_error = MagicMock()

        callback = MagicMock()

        # Call method
        ssh_connector.update_job_list("test_uri", callback)

        # Verify error was emitted
        ssh_connector._emit_error.assert_called_once_with(
            "test_uri", OPERATIONS.RUN_SINGLE_JOB, ERROR.REGISTRY_NOT_CONNECTED
        )

    def test_update_resources(self, ssh_connector):
        """Test update_resources method."""
        # Setup mock worker
        mock_worker = MagicMock()
        ssh_connector.workers = {"test_uri": {"worker": mock_worker}}

        callback = MagicMock()

        # Call method
        ssh_connector.update_resources("test_uri", callback)

        # Verify worker method was called
        mock_worker.update_resources.assert_called_once_with(callback, "test_uri")

    def test_update_resources_not_connected(self, ssh_connector):
        """Test update_resources when not connected."""
        # Setup empty workers
        ssh_connector.workers = {}
        ssh_connector._emit_error = MagicMock()

        callback = MagicMock()

        # Call method
        ssh_connector.update_resources("test_uri", callback)

        # Verify error was emitted
        ssh_connector._emit_error.assert_called_once_with(
            "test_uri", OPERATIONS.RUN_SINGLE_JOB, ERROR.REGISTRY_NOT_CONNECTED
        )

    def test_update_workflow_job_list(self, ssh_connector, mock_clustermanager):
        """Test update_workflow_job_list method."""
        # Setup
        cm_class, cm_instance = mock_clustermanager
        ssh_connector._clustermanagers = {"test_registry": cm_instance}

        # Configure get_workflow_job_list to return test data
        cm_instance.get_workflow_job_list.return_value = ["job1", "job2"]

        callback = MagicMock()

        # Call method
        ssh_connector.update_workflow_job_list("test_registry", "workflow1", callback)

        # Verify
        cm_instance.get_workflow_job_list.assert_called_once_with("workflow1")
        callback.assert_called_once_with("test_registry", "workflow1", ["job1", "job2"])

    def test_update_dir_list(self, ssh_connector, mock_clustermanager):
        """Test update_dir_list method."""
        # Setup
        cm_class, cm_instance = mock_clustermanager
        ssh_connector._clustermanagers = {"test_registry": cm_instance}

        # Configure list_dir to return test data
        cm_instance.list_dir.return_value = ["file1", "file2"]

        callback = MagicMock()

        # Call method
        ssh_connector.update_dir_list("test_registry", "/test/path", callback)

        # Verify
        cm_instance.list_dir.assert_called_once_with("/test/path")
        callback.assert_called_once_with(
            "test_registry", "/test/path", ["file1", "file2"]
        )

    def test_delete_file_directory(self, ssh_connector, mock_clustermanager):
        """Test delete_file method for directory."""
        # Setup
        cm_class, cm_instance = mock_clustermanager
        ssh_connector._clustermanagers = {"test_registry": cm_instance}

        # Configure is_directory to return True
        cm_instance.is_directory.return_value = True

        callback = MagicMock()

        # Call method
        ssh_connector.delete_file("test_registry", "/test/directory", callback)

        # Verify
        cm_instance.is_directory.assert_called_once_with("/test/directory")
        cm_instance.rmtree.assert_called_once_with("/test/directory")
        callback.assert_called_once()

    def test_delete_file_regular_file(self, ssh_connector, mock_clustermanager):
        """Test delete_file method for regular file."""
        # Setup
        cm_class, cm_instance = mock_clustermanager
        ssh_connector._clustermanagers = {"test_registry": cm_instance}

        # Configure is_directory to return False
        cm_instance.is_directory.return_value = False

        callback = MagicMock()

        # Call method
        ssh_connector.delete_file("test_registry", "/test/file.txt", callback)

        # Verify
        cm_instance.is_directory.assert_called_once_with("/test/file.txt")
        cm_instance.delete_file.assert_called_once_with("/test/file.txt")
        callback.assert_called_once()

    def test_delete_job(self, ssh_connector):
        """Test delete_job method."""
        # Setup mock worker
        mock_worker = MagicMock()
        ssh_connector.workers = {"test_uri": {"worker": mock_worker}}

        callback = MagicMock()

        # Call method
        ssh_connector.delete_job("test_uri", "job1", callback)

        # Verify worker method was called
        mock_worker.delete_job.assert_called_once_with(callback, "test_uri", "job1")

    def test_delete_job_not_connected(self, ssh_connector):
        """Test delete_job when not connected."""
        # Setup empty workers
        ssh_connector.workers = {}
        ssh_connector._emit_error = MagicMock()

        callback = MagicMock()

        # Call method
        ssh_connector.delete_job("test_uri", "job1", callback)

        # Verify error was emitted
        ssh_connector._emit_error.assert_called_once_with(
            "test_uri", OPERATIONS.RUN_SINGLE_JOB, ERROR.REGISTRY_NOT_CONNECTED
        )

    def test_abort_job(self, ssh_connector):
        """Test abort_job method."""
        # Setup mock worker
        mock_worker = MagicMock()
        ssh_connector.workers = {"test_uri": {"worker": mock_worker}}

        callback = MagicMock()

        # Call method
        ssh_connector.abort_job("test_uri", "job1", callback)

        # Verify worker method was called
        mock_worker.abort_job.assert_called_once_with(callback, "test_uri", "job1")

    def test_abort_job_not_connected(self, ssh_connector):
        """Test abort_job when not connected."""
        # Setup empty workers
        ssh_connector.workers = {}
        ssh_connector._emit_error = MagicMock()

        callback = MagicMock()

        # Call method
        ssh_connector.abort_job("test_uri", "job1", callback)

        # Verify error was emitted
        ssh_connector._emit_error.assert_called_once_with(
            "test_uri", OPERATIONS.RUN_SINGLE_JOB, ERROR.REGISTRY_NOT_CONNECTED
        )

    def test_get_workflow_url(self, ssh_connector, mock_clustermanager):
        """Test get_workflow_url method."""
        # Setup
        cm_class, cm_instance = mock_clustermanager
        ssh_connector._clustermanagers = {"test_registry": cm_instance}

        # Configure get_url_for_workflow to return test URL
        cm_instance.get_url_for_workflow.return_value = "http://test.url/workflow1"

        # Call method
        result = ssh_connector.get_workflow_url("test_registry", "workflow1")

        # Verify
        cm_instance.get_url_for_workflow.assert_called_once_with("workflow1")
        assert result == "http://test.url/workflow1"

    def test_delete_workflow(self, ssh_connector, mock_clustermanager):
        """Test delete_workflow method."""
        # Setup
        cm_class, cm_instance = mock_clustermanager
        ssh_connector._clustermanagers = {"test_registry": cm_instance}

        callback = MagicMock()

        # Call method
        ssh_connector.delete_workflow("test_registry", "workflow1", callback)

        # Verify
        cm_instance.delete_wf.assert_called_once_with("workflow1")

    def test_abort_workflow(self, ssh_connector, mock_clustermanager):
        """Test abort_workflow method."""
        # Setup
        cm_class, cm_instance = mock_clustermanager
        ssh_connector._clustermanagers = {"test_registry": cm_instance}

        # Mock logger
        ssh_connector.logger = MagicMock()

        callback = MagicMock()

        # Call method
        ssh_connector.abort_workflow("test_registry", "workflow1", callback)

        # Verify
        cm_instance.abort_wf.assert_called_once_with("workflow1")
        ssh_connector.logger.debug.assert_called_once()

    def test_download_file_single_file(self, ssh_connector, mock_clustermanager):
        """Test download_file method with single file."""
        # Setup
        cm_class, cm_instance = mock_clustermanager
        ssh_connector._clustermanagers = {"test_registry": cm_instance}

        callback = MagicMock()
        progress_callback = MagicMock()

        # Call method
        ssh_connector.download_file(
            "test_registry",
            "/remote/file.txt",
            "/local/dest",
            progress_callback,
            callback,
        )

        # Verify
        cm_instance.get_file.assert_called_once_with(
            "/remote/file.txt", "/local/dest", progress_callback
        )

    def test_download_file_multiple_files(self, ssh_connector, mock_clustermanager):
        """Test download_file method with multiple files."""
        # Setup
        cm_class, cm_instance = mock_clustermanager
        ssh_connector._clustermanagers = {"test_registry": cm_instance}

        callback = MagicMock()
        progress_callback = MagicMock()
        files = ["/remote/file1.txt", "/remote/file2.txt"]

        # Call method
        ssh_connector.download_file(
            "test_registry", files, "/local/dest", progress_callback, callback
        )

        # Verify get_file was called for each file
        assert cm_instance.get_file.call_count == 2
        cm_instance.get_file.assert_any_call(
            "/remote/file1.txt", "/local/dest", progress_callback
        )
        cm_instance.get_file.assert_any_call(
            "/remote/file2.txt", "/local/dest", progress_callback
        )

    def test_upload_files_single_file(self, ssh_connector, mock_clustermanager):
        """Test upload_files method with single file."""
        # Setup
        cm_class, cm_instance = mock_clustermanager
        ssh_connector._clustermanagers = {"test_registry": cm_instance}

        callback = MagicMock()
        progress_callback = MagicMock()

        # Call method
        ssh_connector.upload_files(
            "test_registry",
            "/local/file.txt",
            "/remote/dest",
            progress_callback,
            callback,
        )

        # Verify
        cm_instance.put_file.assert_called_once_with("/local/file.txt", "/remote/dest")

    def test_upload_files_multiple_files(self, ssh_connector, mock_clustermanager):
        """Test upload_files method with multiple files."""
        # Setup
        cm_class, cm_instance = mock_clustermanager
        ssh_connector._clustermanagers = {"test_registry": cm_instance}

        callback = MagicMock()
        progress_callback = MagicMock()
        files = ["/local/file1.txt", "/local/file2.txt"]

        # Call method
        ssh_connector.upload_files(
            "test_registry", files, "/remote/dest", progress_callback, callback
        )

        # Verify put_file was called for each file
        assert cm_instance.put_file.call_count == 2
        cm_instance.put_file.assert_any_call("/local/file1.txt", "/remote/dest")
        cm_instance.put_file.assert_any_call("/local/file2.txt", "/remote/dest")

    def test_run(self, ssh_connector):
        """Test run method."""
        # Mock exec_
        ssh_connector.exec_ = MagicMock()

        # Call method
        ssh_connector.run()

        # Verify exec_ was called
        ssh_connector.exec_.assert_called_once()

    @patch("simstack.SSHConnector.getpass")
    def test_connect_registry_embedded_key(
        self, mock_getpass, ssh_connector, mock_local_clustermanager
    ):
        """Test connect_registry with embedded key."""
        # Setup
        cm_class, cm_instance = mock_local_clustermanager
        ssh_connector._clustermanagers = {}

        # Setup registry with embedded key
        registry = ssh_connector._registries["test_registry"]
        registry.ssh_private_key = "<embedded>"
        registry.queueing_system = "Filegenerator"

        # Mock SimStackPaths
        with patch("simstack.SSHConnector.SimStackPaths") as mock_paths:
            mock_paths.get_embedded_sshkey.return_value = "/test/embedded/key"
            mock_paths.get_local_hostfile.return_value = "/test/hostfile"

            # Mock os.path.isfile to return True
            with patch("simstack.SSHConnector.os.path.isfile", return_value=True):
                # Mock start_server
                with patch.object(ssh_connector, "start_server"):
                    # Call method
                    callback = MagicMock()
                    ssh_connector.connect_registry("test_registry", callback)

                    # Verify callback was called
                    callback.assert_called_once()

    @patch("simstack.SSHConnector.getpass")
    def test_connect_registry_localhost_same_user(
        self, mock_getpass, ssh_connector, mock_local_clustermanager
    ):
        """Test connect_registry with localhost and same user."""
        # Setup
        cm_class, cm_instance = mock_local_clustermanager
        ssh_connector._clustermanagers = {}
        mock_getpass.getuser.return_value = "test_user"

        # Setup registry for localhost
        registry = ssh_connector._registries["test_registry"]
        registry.base_URI = "localhost"
        registry.username = "test_user"
        registry.ssh_private_key = "/test/key"

        with patch("simstack.SSHConnector.SimStackPaths") as mock_paths:
            mock_paths.get_local_hostfile.return_value = "/test/hostfile"

            # Mock start_server
            with patch.object(ssh_connector, "start_server"):
                # Call method
                callback = MagicMock()
                ssh_connector.connect_registry("test_registry", callback)

                # Verify LocalClusterManager was used
                cm_class.assert_called_once()
                callback.assert_called_once()

    @patch("simstack.SSHConnector.filewalker")
    @patch("simstack.SSHConnector.etree")
    @patch("simstack.SSHConnector.os")
    def test_run_workflow_job(
        self, mock_os, mock_etree, mock_filewalker, ssh_connector, mock_clustermanager
    ):
        """Test run_workflow_job method."""
        # Setup
        cm_class, cm_instance = mock_clustermanager
        ssh_connector._clustermanagers = {"test_registry": cm_instance}

        # Mock file operations
        mock_filewalker.return_value = [
            "/upload/dir/file1.txt",
            "/upload/dir/file2.txt",
        ]
        mock_os.path.commonprefix.return_value = "/upload/dir"
        mock_os.path.relpath.side_effect = ["file1.txt", "file2.txt"]
        mock_os.path.dirname.side_effect = [
            "test_submitname/workflow_data",
            "test_submitname/workflow_data",
        ]

        # Mock cluster manager methods
        cm_instance.exists.return_value = False
        mock_remote_file = MagicMock()
        cm_instance.remote_open.return_value.__enter__.return_value = mock_remote_file
        cm_instance.get_calculation_basepath.return_value = "/calc/base"
        cm_instance.get_queueing_system.return_value = "test_queue"
        cm_instance.get_default_queue.return_value = "default"

        # Mock XML processing
        mock_xml = MagicMock()
        mock_etree.tostring.return_value = b"<workflow>test</workflow>"

        # Call method
        ssh_connector.run_workflow_job(
            "test_registry", "test_submitname", "/upload/dir", mock_xml
        )

        # Verify key operations
        cm_instance.exists.assert_called_once_with("test_submitname")
        assert cm_instance.mkdir_p.call_count == 2
        assert cm_instance.put_file.call_count == 2
        cm_instance.remote_open.assert_called_once()
        cm_instance.submit_wf.assert_called_once()

    def test_run_workflow_job_file_exists(self, ssh_connector, mock_clustermanager):
        """Test run_workflow_job when file exists."""
        # Setup
        cm_class, cm_instance = mock_clustermanager
        ssh_connector._clustermanagers = {"test_registry": cm_instance}

        # Mock exists to return True then False
        cm_instance.exists.side_effect = [True, False]

        with patch("simstack.SSHConnector.filewalker", return_value=[]):
            with patch("simstack.SSHConnector.etree") as mock_etree:
                mock_etree.tostring.return_value = b"<workflow>test</workflow>"
                mock_remote_file = MagicMock()
                cm_instance.remote_open.return_value.__enter__.return_value = (
                    mock_remote_file
                )
                cm_instance.get_calculation_basepath.return_value = "/calc/base"
                cm_instance.get_queueing_system.return_value = "test_queue"
                cm_instance.get_default_queue.return_value = "default"

                mock_xml = MagicMock()

                # Call method
                ssh_connector.run_workflow_job(
                    "test_registry", "test_submitname", "/upload/dir", mock_xml
                )

                # Verify exists was called twice
                assert cm_instance.exists.call_count == 2

    def test_exec_callback_tuple_with_single_arg(self, ssh_connector):
        """Test _exec_callback with tuple format with single arg instead of tuple."""
        # Setup
        callback_func = MagicMock()
        callback = (callback_func, "single_arg", {"cb_kwarg": "cb_value"})

        # Call method
        ssh_connector._exec_callback(callback, "arg1", "arg2")

        # Verify
        callback_func.assert_called_once_with(
            "single_arg", "arg1", "arg2", cb_kwarg="cb_value"
        )

    def test_connect_registry_already_connected(
        self, ssh_connector, mock_clustermanager
    ):
        """Test connect_registry when already connected."""
        # Setup
        cm_class, cm_instance = mock_clustermanager
        cm_instance.is_connected.return_value = True  # Already connected
        ssh_connector._clustermanagers = {"test_registry": cm_instance}

        with patch("simstack.SSHConnector.SimStackPaths"):
            with patch.object(ssh_connector, "start_server"):
                callback = MagicMock()

                # Call method
                ssh_connector.connect_registry("test_registry", callback)

                # Verify callback was called
                callback.assert_called_once()

    def test_disconnect_registry_not_connected(self, ssh_connector):
        """Test disconnect_registry when not connected."""
        # Setup - no cluster managers
        ssh_connector._clustermanagers = {}

        callback = MagicMock()

        # Call method
        ssh_connector.disconnect_registry("test_registry", callback)

        # Verify callback was still called
        callback.assert_called_once()


# Add more tests as needed for other methods
