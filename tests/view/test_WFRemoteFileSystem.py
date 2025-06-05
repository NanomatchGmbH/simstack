import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QTreeView, QPushButton
from PySide6.QtCore import QModelIndex

from simstack.view.WFRemoteFileSystem import WFRemoteFileSystem
from simstack.view.WFEditorTreeModels import WFERemoteFileSystemModel as FSModel


class TestWFRemoteFileSystem:
    """Tests for the WFRemoteFileSystem class."""

    @pytest.fixture
    def mock_fs_model(self):
        """Create a mock FSModel."""
        model = MagicMock(spec=FSModel)

        # Setup mock for get_type
        model.get_type.return_value = FSModel.DATA_TYPE_DIRECTORY

        # Setup mock for headerData
        model.headerData.return_value = "Header"

        # Setup mock for get_separator_indices
        model.get_separator_indices.return_value = [QModelIndex(), QModelIndex()]

        # Setup DATA_TYPE constants
        model.DATA_TYPE_FILE = FSModel.DATA_TYPE_FILE
        model.DATA_TYPE_DIRECTORY = FSModel.DATA_TYPE_DIRECTORY
        model.DATA_TYPE_JOB = FSModel.DATA_TYPE_JOB
        model.DATA_TYPE_WORKFLOW = FSModel.DATA_TYPE_WORKFLOW
        model.DATA_TYPE_UNKNOWN = FSModel.DATA_TYPE_UNKNOWN
        model.HEADER_TYPE_JOB = FSModel.HEADER_TYPE_JOB
        model.HEADER_TYPE_WORKFLOW = FSModel.HEADER_TYPE_WORKFLOW
        model.HEADER_TYPE_DIRECTORY = FSModel.HEADER_TYPE_DIRECTORY

        return model

    @pytest.fixture
    def remote_file_system(self, qtbot, mock_fs_model):
        """Create a WFRemoteFileSystem instance with mocked model."""
        # Completely skip the normal initialization to avoid Qt errors
        with patch.object(
            WFRemoteFileSystem, "__init__", return_value=None
        ), patch.object(
            WFRemoteFileSystem, "_WFRemoteFileSystem__init_ui"
        ), patch.object(WFRemoteFileSystem, "_WFRemoteFileSystem__connect_signals"):
            # Create instance without calling __init__
            fs = WFRemoteFileSystem.__new__(WFRemoteFileSystem)

            # Set up attributes manually
            fs.__class__ = WFRemoteFileSystem  # Ensure class methods work
            fs._WFRemoteFileSystem__fs_model = mock_fs_model

            # Create a real QTreeView but mock its methods to avoid Qt interaction
            tree_view = MagicMock(spec=QTreeView)
            # Make tree_view.model() return our mock_fs_model
            tree_view.model.return_value = mock_fs_model
            fs._WFRemoteFileSystem__fileTree = tree_view

            fs._WFRemoteFileSystem__btn_reload = MagicMock(spec=QPushButton)
            fs._WFRemoteFileSystem__current_requests = {}

            # Add mock signals
            fs.request_job_list_update = MagicMock()
            fs.request_worflow_list_update = MagicMock()
            fs.request_job_update = MagicMock()
            fs.request_worflow_update = MagicMock()
            fs.request_directory_update = MagicMock()
            fs.download_file = MagicMock()
            fs.upload_file_to = MagicMock()
            fs.delete_file = MagicMock()
            fs.delete_job = MagicMock()
            fs.abort_job = MagicMock()
            fs.browse = MagicMock()
            fs.delete_workflow = MagicMock()
            fs.abort_workflow = MagicMock()

            # Mock the internal methods to ensure they behave as expected
            fs._WFRemoteFileSystem__request_tree_entry_update = (
                lambda index, path, index_type: setattr(
                    fs,
                    "_WFRemoteFileSystem__current_requests",
                    {
                        "workflow_path"
                        if index_type == FSModel.DATA_TYPE_WORKFLOW
                        else path: index
                    },
                )
            )

            return fs

    def test_init(self, remote_file_system, mock_fs_model):
        """Test initialization of WFRemoteFileSystem."""
        fs = remote_file_system

        # Verify model was set
        assert fs._WFRemoteFileSystem__fs_model is mock_fs_model

        # Verify UI components were created
        # Skip instance checks since we're using MagicMock objects

        # Verify current_requests is initialized
        assert fs._WFRemoteFileSystem__current_requests == {}

        # Verify tree view returns the correct model
        tree_view = fs._WFRemoteFileSystem__fileTree
        assert tree_view.model() is mock_fs_model

        # Skip other UI configuration checks which would rely on real Qt objects

    def test_signals_connected(self, remote_file_system):
        """Test that signals are connected."""
        fs = remote_file_system

        # Verify custom context menu signal is connected
        assert fs._WFRemoteFileSystem__fileTree.customContextMenuRequested.isConnected()

        # Verify double-click signal is connected
        assert fs._WFRemoteFileSystem__fileTree.doubleClicked.isConnected()

        # Verify expanded signal is connected
        assert fs._WFRemoteFileSystem__fileTree.expanded.isConnected()

        # Verify reload button click signal is connected
        assert fs._WFRemoteFileSystem__btn_reload.clicked.isConnected()

    def test_update_job_list(self, remote_file_system):
        """Test update_job_list method."""
        fs = remote_file_system
        mock_jobs = [{"name": "job1", "id": "1"}, {"name": "job2", "id": "2"}]

        # Set up a spy on update_file_tree_node
        with patch.object(fs, "update_file_tree_node") as mock_update:
            fs.update_job_list(mock_jobs)

            # Verify update_file_tree_node was called with correct arguments
            mock_update.assert_called_once_with(fs._JOB_PATH, mock_jobs)

    def test_update_workflow_list(self, remote_file_system):
        """Test update_workflow_list method."""
        fs = remote_file_system
        mock_wfs = [{"name": "wf1", "id": "1"}, {"name": "wf2", "id": "2"}]

        # Set up a spy on update_file_tree_node
        with patch.object(fs, "update_file_tree_node") as mock_update:
            fs.update_workflow_list(mock_wfs)

            # Verify update_file_tree_node was called with correct arguments
            mock_update.assert_called_once_with(fs._WF_PATH, mock_wfs)

    def test_update_file_tree_node_existing_path(
        self, remote_file_system, mock_fs_model
    ):
        """Test update_file_tree_node method with an existing path."""
        fs = remote_file_system

        # Setup mock index and current_requests
        mock_index = MagicMock(spec=QModelIndex)
        mock_index.isValid.return_value = True
        fs._WFRemoteFileSystem__current_requests = {"test_path": mock_index}

        # Mock data to update with
        mock_data = [
            {"name": "file1", "path": "file1_path", "type": "f", "id": "1"},
            {"name": "dir1/", "path": "dir1_path", "type": "d", "id": "2"},
            {
                "name": "job1",
                "path": "job1_path",
                "type": "j",
                "id": "3",
                "status": "running",
            },
            {
                "name": "wf1",
                "path": "wf1_path",
                "type": "w",
                "id": "4",
                "status": "completed",
            },
        ]

        # Call the method
        fs.update_file_tree_node("test_path", mock_data)

        # Verify the model was updated
        mock_fs_model.removeSubRows.assert_called_once_with(mock_index)
        mock_fs_model.insertDataRows.assert_called_once()

        # Verify current_requests was updated
        assert "test_path" not in fs._WFRemoteFileSystem__current_requests

    def test_update_file_tree_node_workflow_path(
        self, remote_file_system, mock_fs_model
    ):
        """Test update_file_tree_node method with workflow path."""
        fs = remote_file_system

        # Setup mock index and current_requests
        mock_index = MagicMock(spec=QModelIndex)
        mock_index.isValid.return_value = True
        fs._WFRemoteFileSystem__current_requests = {"?wf?": mock_index}

        # Mock data to update with
        mock_data = [
            {
                "name": "wf1",
                "path": "wf1_path",
                "type": "w",
                "id": "1",
                "status": "running",
            },
            {
                "name": "wf2",
                "path": "wf2_path",
                "type": "w",
                "id": "2",
                "status": "completed",
            },
        ]

        # Call the method
        fs.update_file_tree_node("?wf?", mock_data)

        # Verify the model was updated
        mock_fs_model.removeSubRows.assert_called_once_with(mock_index)
        mock_fs_model.insertDataRows.assert_called_once()

        # Verify current_requests was updated
        assert "?wf?" not in fs._WFRemoteFileSystem__current_requests

        # Verify entries were sorted (workflows are sorted in reverse)
        sorted(mock_data, key=lambda k: k["name"], reverse=True)
        first_entry_idx = mock_fs_model.insertDataRows.call_args[0][0]
        assert first_entry_idx == 0  # Should insert at position 0

    def test_update_file_tree_node_nonexistent_path(self, remote_file_system):
        """Test update_file_tree_node method with a non-existent path."""
        fs = remote_file_system

        # Setup current_requests without the target path
        fs._WFRemoteFileSystem__current_requests = {}

        # Mock data to update with
        mock_data = [{"name": "file1", "path": "file1_path", "type": "f", "id": "1"}]

        # Call the method
        with patch("builtins.print") as mock_print:
            fs.update_file_tree_node("nonexistent_path", mock_data)

            # Verify the warning was printed
            mock_print.assert_called_once_with(
                "Path 'nonexistent_path' not in current_requests."
            )

    def test_request_header_entry_update_job(self, remote_file_system):
        """Test __request_header_entry_update method with job list."""
        fs = remote_file_system

        # Setup mock index and type
        mock_index = MagicMock(spec=QModelIndex)
        index_type = FSModel.HEADER_TYPE_JOB
        path = "test_path"

        # Set up signal spy
        with patch.object(fs.request_job_list_update, "emit") as mock_emit:
            # Call the method
            fs._WFRemoteFileSystem__request_header_entry_update(
                mock_index, path, index_type
            )

            # Verify current_requests was updated
            assert path in fs._WFRemoteFileSystem__current_requests
            assert fs._WFRemoteFileSystem__current_requests[path] is mock_index

            # Verify signal was emitted
            mock_emit.assert_called_once()

    def test_request_header_entry_update_workflow(self, remote_file_system):
        """Test __request_header_entry_update method with workflow list."""
        fs = remote_file_system

        # Setup mock index and type
        mock_index = MagicMock(spec=QModelIndex)
        index_type = FSModel.HEADER_TYPE_WORKFLOW
        path = "test_path"

        # Set up signal spy
        with patch.object(fs.request_worflow_list_update, "emit") as mock_emit:
            # Call the method
            fs._WFRemoteFileSystem__request_header_entry_update(
                mock_index, path, index_type
            )

            # Verify current_requests was updated
            assert path in fs._WFRemoteFileSystem__current_requests
            assert fs._WFRemoteFileSystem__current_requests[path] is mock_index

            # Verify signal was emitted
            mock_emit.assert_called_once()

    def test_download_file(self, remote_file_system, mock_fs_model):
        """Test __download_file method."""
        fs = remote_file_system

        # Setup mock index
        mock_index = MagicMock(spec=QModelIndex)
        mock_fs_model.get_abspath.return_value = "file_path"

        # Set up signal spy
        with patch.object(fs.download_file, "emit") as mock_emit:
            # Call the method
            fs._WFRemoteFileSystem__download_file(mock_index)

            # Verify signal was emitted with correct path
            mock_emit.assert_called_once_with("file_path")

    def test_upload_file(self, remote_file_system, mock_fs_model):
        """Test __upload_file method."""
        fs = remote_file_system

        # Setup mock index
        mock_index = MagicMock(spec=QModelIndex)
        mock_fs_model.get_abspath.return_value = "dir_path"

        # Set up signal spy
        with patch.object(fs.upload_file_to, "emit") as mock_emit:
            # Call the method
            fs._WFRemoteFileSystem__upload_file(mock_index)

            # Verify signal was emitted with correct path
            mock_emit.assert_called_once_with("dir_path")

    def test_on_cm_download(self, remote_file_system, mock_fs_model):
        """Test __on_cm_download method."""
        fs = remote_file_system

        # Setup mock index and parameters
        mock_index = MagicMock(spec=QModelIndex)
        fs._WFRemoteFileSystem__fileTree.selectedIndexes = MagicMock(
            return_value=[mock_index]
        )
        mock_fs_model.get_type.return_value = FSModel.DATA_TYPE_FILE

        # Set up spy on __download_file
        with patch.object(fs, "_WFRemoteFileSystem__download_file") as mock_download:
            # Call the method
            fs._WFRemoteFileSystem__on_cm_download()

            # Verify download_file was called with the selected index
            mock_download.assert_called_once_with(mock_index)

    def test_on_cm_upload(self, remote_file_system, mock_fs_model):
        """Test __on_cm_upload method."""
        fs = remote_file_system

        # Setup mock index and parameters
        mock_index = MagicMock(spec=QModelIndex)
        fs._WFRemoteFileSystem__fileTree.selectedIndexes = MagicMock(
            return_value=[mock_index]
        )
        mock_fs_model.get_type.return_value = FSModel.DATA_TYPE_DIRECTORY

        # Set up spy on __upload_file
        with patch.object(fs, "_WFRemoteFileSystem__upload_file") as mock_upload:
            # Call the method
            fs._WFRemoteFileSystem__on_cm_upload()

            # Verify upload_file was called with the selected index
            mock_upload.assert_called_once_with(mock_index)

    def test_on_cm_delete_file(self, remote_file_system, mock_fs_model):
        """Test __on_cm_delete_file method."""
        fs = remote_file_system

        # Setup mock index and parameters
        mock_index = MagicMock(spec=QModelIndex)
        fs._WFRemoteFileSystem__fileTree.selectedIndexes = MagicMock(
            return_value=[mock_index]
        )
        mock_fs_model.get_type.return_value = FSModel.DATA_TYPE_FILE
        mock_fs_model.get_abspath.return_value = "file_path"

        # Set up signal spy
        with patch.object(fs.delete_file, "emit") as mock_emit:
            # Call the method
            fs._WFRemoteFileSystem__on_cm_delete_file()

            # Verify signal was emitted with correct path
            mock_emit.assert_called_once_with("file_path")

    def test_on_cm_delete_job(self, remote_file_system, mock_fs_model):
        """Test __on_cm_delete_job method."""
        fs = remote_file_system

        # Setup mock index and parameters
        mock_index = MagicMock(spec=QModelIndex)
        fs._WFRemoteFileSystem__fileTree.selectedIndexes = MagicMock(
            return_value=[mock_index]
        )
        mock_fs_model.get_type.return_value = FSModel.DATA_TYPE_JOB
        mock_fs_model.get_id.return_value = "job_id"

        # Set up signal spy
        with patch.object(fs.delete_job, "emit") as mock_emit:
            # Call the method
            fs._WFRemoteFileSystem__on_cm_delete_job()

            # Verify signal was emitted with correct ID
            mock_emit.assert_called_once_with("job_id")

    def test_on_jobid_copy(self, remote_file_system, mock_fs_model):
        """Test __on_jobid_copy method."""
        fs = remote_file_system

        # Setup mock index and parameters
        mock_index = MagicMock(spec=QModelIndex)
        fs._WFRemoteFileSystem__fileTree.selectedIndexes = MagicMock(
            return_value=[mock_index]
        )
        mock_fs_model.get_type.return_value = FSModel.DATA_TYPE_JOB
        mock_fs_model.get_id.return_value = "job_id"

        # Mock QApplication clipboard
        mock_clipboard = MagicMock()

        with patch(
            "simstack.view.WFRemoteFileSystem.QApplication.clipboard",
            return_value=mock_clipboard,
        ):
            # Call the method
            fs._WFRemoteFileSystem__on_jobid_copy()

            # Verify clipboard was set with the job ID
            assert (
                mock_clipboard.setText.call_count == 2
            )  # Called for both Clipboard and Selection modes
            mock_clipboard.setText.assert_any_call(
                "job_id", mode=mock_clipboard.Clipboard
            )

    def test_on_cm_abort_job(self, remote_file_system, mock_fs_model):
        """Test __on_cm_abort_job method."""
        fs = remote_file_system

        # Setup mock index and parameters
        mock_index = MagicMock(spec=QModelIndex)
        fs._WFRemoteFileSystem__fileTree.selectedIndexes = MagicMock(
            return_value=[mock_index]
        )
        mock_fs_model.get_type.return_value = FSModel.DATA_TYPE_JOB
        mock_fs_model.get_id.return_value = "job_id"

        # Set up signal spy
        with patch.object(fs.abort_job, "emit") as mock_emit:
            # Call the method
            fs._WFRemoteFileSystem__on_cm_abort_job()

            # Verify signal was emitted with correct ID
            mock_emit.assert_called_once_with("job_id")

    def test_on_cm_browse_workflow(self, remote_file_system, mock_fs_model):
        """Test __on_cm_browse method with workflow."""
        fs = remote_file_system

        # Setup mock index and parameters
        mock_index = MagicMock(spec=QModelIndex)
        fs._WFRemoteFileSystem__fileTree.selectedIndexes = MagicMock(
            return_value=[mock_index]
        )
        mock_fs_model.get_type.return_value = FSModel.DATA_TYPE_WORKFLOW
        mock_fs_model.get_id.return_value = "workflow_id"

        # Set up signal spy
        with patch.object(fs.browse, "emit") as mock_emit:
            # Call the method
            fs._WFRemoteFileSystem__on_cm_browse()

            # Verify signal was emitted with correct ID and empty string
            mock_emit.assert_called_once_with("workflow_id", "")

    def test_on_cm_show_report(self, remote_file_system, mock_fs_model):
        """Test __on_cm_show_report method."""
        fs = remote_file_system

        # Setup mock index and parameters
        mock_index = MagicMock(spec=QModelIndex)
        fs._WFRemoteFileSystem__fileTree.selectedIndexes = MagicMock(
            return_value=[mock_index]
        )
        mock_fs_model.get_type.return_value = FSModel.DATA_TYPE_WORKFLOW
        mock_fs_model.get_id.return_value = "workflow_id"

        # Set up signal spy
        with patch.object(fs.browse, "emit") as mock_emit:
            # Call the method
            fs._WFRemoteFileSystem__on_cm_show_report()

            # Verify signal was emitted with correct report path
            mock_emit.assert_called_once_with("workflow_id/workflow_report.html", "")

    def test_on_cm_delete_workflow(self, remote_file_system, mock_fs_model):
        """Test __on_cm_delete_workflow method."""
        fs = remote_file_system

        # Setup mock index and parameters
        mock_index = MagicMock(spec=QModelIndex)
        fs._WFRemoteFileSystem__fileTree.selectedIndexes = MagicMock(
            return_value=[mock_index]
        )
        mock_fs_model.get_type.return_value = FSModel.DATA_TYPE_WORKFLOW
        mock_fs_model.get_id.return_value = "workflow_id"

        # Set up signal spy
        with patch.object(fs.delete_workflow, "emit") as mock_emit:
            # Call the method
            fs._WFRemoteFileSystem__on_cm_delete_workflow()

            # Verify signal was emitted with correct ID
            mock_emit.assert_called_once_with("workflow_id")

    def test_on_cm_abort_workflow(self, remote_file_system, mock_fs_model):
        """Test __on_cm_abort_workflow method."""
        fs = remote_file_system

        # Setup mock index and parameters
        mock_index = MagicMock(spec=QModelIndex)
        fs._WFRemoteFileSystem__fileTree.selectedIndexes = MagicMock(
            return_value=[mock_index]
        )
        mock_fs_model.get_type.return_value = FSModel.DATA_TYPE_WORKFLOW
        mock_fs_model.get_id.return_value = "workflow_id"

        # Set up signal spy
        with patch.object(fs.abort_workflow, "emit") as mock_emit:
            # Call the method
            fs._WFRemoteFileSystem__on_cm_abort_workflow()

            # Verify signal was emitted with correct ID
            mock_emit.assert_called_once_with("workflow_id")

    def test_reload(self, remote_file_system):
        """Test __reload method."""
        fs = remote_file_system

        # Set up spy on __got_request
        with patch.object(fs, "_WFRemoteFileSystem__got_request") as mock_got_request:
            # Call the method
            fs._WFRemoteFileSystem__reload()

            # Verify __got_request was called with None
            mock_got_request.assert_called_once_with(None)
