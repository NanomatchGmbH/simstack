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


# Add more tests as needed for other methods
