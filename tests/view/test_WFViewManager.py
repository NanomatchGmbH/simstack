import pytest
from unittest.mock import patch, MagicMock, PropertyMock
import os
from PySide6.QtCore import QObject, QFileInfo, QStandardPaths

from simstack.view.WFViewManager import WFViewManager
from simstack.view.MessageDialog import MessageDialog


class TestWFViewManager:
    """Tests for the WFViewManager class."""

    @pytest.fixture
    def view_manager(self):
        """Create a WFViewManager instance with mocked dependencies."""
        # Mock WFEditor and WFEditorMainWindow
        with patch('simstack.view.WFViewManager.WFEditor') as mock_editor_class, \
             patch('simstack.view.WFViewManager.WFEditorMainWindow') as mock_window_class:
            
            # Create mock instances
            mock_editor = MagicMock()
            mock_window = MagicMock()
            
            # Setup return values
            mock_editor_class.return_value = mock_editor
            mock_window_class.return_value = mock_window
            
            # Create manager
            manager = WFViewManager()
            
            # Store mocks for assertions
            manager._mock_editor_class = mock_editor_class
            manager._mock_window_class = mock_window_class
            
            return manager

    def test_init(self, view_manager):
        """Test initialization of WFViewManager."""
        # Verify editor and window were created
        view_manager._mock_editor_class.assert_called_once()
        view_manager._mock_window_class.assert_called_once_with(view_manager._editor)
        
        # Verify attributes were set
        assert view_manager._webengineviews == []
        assert view_manager.last_used_path == view_manager.get_homedir()

    def test_show_message_class_method(self):
        """Test show_message class method."""
        # Mock MessageDialog
        with patch('simstack.view.WFViewManager.MessageDialog') as mock_dialog:
            # Call method
            WFViewManager.show_message(MessageDialog.MESSAGE_TYPES.info, "Test message", "Test details")
            
            # Verify MessageDialog was created with correct arguments
            mock_dialog.assert_called_once_with(MessageDialog.MESSAGE_TYPES.info, "Test message", details="Test details")

    def test_show_error_class_method(self):
        """Test show_error class method."""
        # Mock show_message
        with patch.object(WFViewManager, '_show_message') as mock_show_message:
            # Call method
            WFViewManager.show_error("Test error", "Test details")
            
            # Verify _show_message was called with correct arguments
            mock_show_message.assert_called_once_with(MessageDialog.MESSAGE_TYPES.error, "Test error", "Test details")

    def test_show_info(self, view_manager):
        """Test show_info method."""
        # Mock _show_message
        with patch.object(WFViewManager, '_show_message') as mock_show_message:
            # Call method
            view_manager.show_info("Test info", "Test details")
            
            # Verify _show_message was called with correct arguments
            mock_show_message.assert_called_once_with(MessageDialog.MESSAGE_TYPES.info, "Test info", "Test details")

    def test_show_warning(self, view_manager):
        """Test show_warning method."""
        # Mock _show_message
        with patch.object(WFViewManager, '_show_message') as mock_show_message:
            # Call method
            view_manager.show_warning("Test warning", "Test details")
            
            # Verify _show_message was called with correct arguments
            mock_show_message.assert_called_once_with(MessageDialog.MESSAGE_TYPES.warning, "Test warning", "Test details")

    def test_show_critical_error(self, view_manager):
        """Test show_critical_error method."""
        # Mock _show_message
        with patch.object(WFViewManager, '_show_message') as mock_show_message:
            # Call method
            view_manager.show_critical_error("Test critical", "Test details")
            
            # Verify _show_message was called with correct arguments
            mock_show_message.assert_called_once_with(MessageDialog.MESSAGE_TYPES.critical, "Test critical", "Test details")

    def test_show_mainwindow(self, view_manager):
        """Test show_mainwindow method."""
        # Call method
        view_manager.show_mainwindow()
        
        # Verify show was called on the main window
        view_manager._mainwindow.show.assert_called_once()

    def test_show_status_message(self, view_manager):
        """Test show_status_message method."""
        # Call method
        view_manager.show_status_message("Test status", 10)
        
        # Verify show_status_message was called on the main window
        view_manager._mainwindow.show_status_message.assert_called_once_with("Test status", 10)

    def test_clear_editor(self, view_manager):
        """Test clear_editor method."""
        # Call method
        view_manager.clear_editor()
        
        # Verify clear was called on the editor
        view_manager._editor.clear.assert_called_once()

    def test_open_dialog_open_workflow(self, view_manager):
        """Test open_dialog_open_workflow method."""
        # Call method
        view_manager.open_dialog_open_workflow()
        
        # Verify open was called on the editor
        view_manager._editor.open.assert_called_once()

    def test_open_dialog_save_workflow(self, view_manager):
        """Test open_dialog_save_workflow method."""
        # Call method
        view_manager.open_dialog_save_workflow()
        
        # Verify save was called on the editor
        view_manager._editor.save.assert_called_once()

    def test_open_dialog_save_workflow_as(self, view_manager):
        """Test open_dialog_save_workflow_as method."""
        # Call method
        view_manager.open_dialog_save_workflow_as()
        
        # Verify saveAs was called on the editor
        view_manager._editor.saveAs.assert_called_once()

    def test_open_dialog_registry_settings(self, view_manager):
        """Test open_dialog_registry_settings method."""
        # Call method
        registries = ["registry1", "registry2"]
        view_manager.open_dialog_registry_settings(registries)
        
        # Verify open_dialog_registry_settings was called on the main window
        view_manager._mainwindow.open_dialog_registry_settings.assert_called_once_with(registries)

    def test_open_dialog_path_settings(self, view_manager):
        """Test open_dialog_path_settings method."""
        # Call method
        pathsettings = {"wanoRepo": "/path/to/wano", "workflows": "/path/to/workflows"}
        view_manager.open_dialog_path_settings(pathsettings)
        
        # Verify open_dialog_path_settings was called on the main window
        view_manager._mainwindow.open_dialog_path_settings.assert_called_once_with(pathsettings)

    def test_update_wano_list(self, view_manager):
        """Test update_wano_list method."""
        # Call method
        wanos = ["wano1", "wano2"]
        view_manager.update_wano_list(wanos)
        
        # Verify update_wano_list was called on the editor
        view_manager._editor.update_wano_list.assert_called_once_with(wanos)

    def test_update_saved_workflows_list(self, view_manager):
        """Test update_saved_workflows_list method."""
        # Call method
        workflows = ["workflow1", "workflow2"]
        view_manager.update_saved_workflows_list(workflows)
        
        # Verify update_saved_workflows_list was called on the editor
        view_manager._editor.update_saved_workflows_list.assert_called_once_with(workflows)

    def test_set_registry_connection_status(self, view_manager):
        """Test set_registry_connection_status method."""
        # Call method
        status = "connected"
        view_manager.set_registry_connection_status(status)
        
        # Verify set_registry_connection_status was called on the editor
        view_manager._editor.set_registry_connection_status.assert_called_once_with(status)

    def test_update_registries(self, view_manager):
        """Test update_registries method."""
        # Call method
        registries = ["registry1", "registry2"]
        selected = 1
        view_manager.update_registries(registries, selected)
        
        # Verify update_registries was called on the editor
        view_manager._editor.update_registries.assert_called_once_with(registries, selected)

    def test_update_filesystem_model(self, view_manager):
        """Test update_filesystem_model method."""
        # Call method
        path = "/path/to/files"
        files = ["file1", "file2"]
        view_manager.update_filesystem_model(path, files)
        
        # Verify update_filesystem_model was called on the editor
        view_manager._editor.update_filesystem_model.assert_called_once_with(path, files)

    def test_update_job_list(self, view_manager):
        """Test update_job_list method."""
        # Call method
        jobs = ["job1", "job2"]
        view_manager.update_job_list(jobs)
        
        # Verify update_job_list was called on the editor
        view_manager._editor.update_job_list.assert_called_once_with(jobs)

    def test_update_workflow_list(self, view_manager):
        """Test update_workflow_list method."""
        # Call method
        wfs = ["wf1", "wf2"]
        view_manager.update_workflow_list(wfs)
        
        # Verify update_workflow_list was called on the editor
        view_manager._editor.update_workflow_list.assert_called_once_with(wfs)

    def test_on_file_download(self, view_manager):
        """Test _on_file_download method."""
        # Mock QFileDialog.getSaveFileName
        filepath = "/path/to/remote/file.txt"
        local_path = "/path/to/local/file.txt"
        
        with patch('simstack.view.WFViewManager.QFileDialog.getSaveFileName') as mock_dialog, \
             patch('simstack.view.WFViewManager.QFileInfo') as mock_file_info:
            
            # Setup return values
            mock_dialog.return_value = (local_path, "")
            mock_file_info_instance = MagicMock()
            mock_file_info_instance.path.return_value = "/path/to/remote"
            mock_file_info.return_value = mock_file_info_instance
            
            # Mock download_file_to signal
            view_manager.download_file_to = MagicMock()
            
            # Call method
            view_manager._on_file_download(filepath)
            
            # Verify dialog was shown with correct arguments
            mock_dialog.assert_called_once()
            assert mock_dialog.call_args[0][0] is view_manager._editor
            assert mock_dialog.call_args[0][1] == "Download File"
            assert os.path.basename(filepath) in mock_dialog.call_args[0][2]
            
            # Verify signal was emitted
            view_manager.download_file_to.emit.assert_called_once_with(filepath, local_path)
            
            # Verify last_used_path was updated
            assert view_manager.last_used_path == "/path/to/remote"

    def test_on_file_upload(self, view_manager):
        """Test _on_file_upload method."""
        # Mock QFileDialog.getOpenFileName
        local_path = "/path/to/local/file.txt"
        remote_dir = "/path/to/remote"
        
        with patch('simstack.view.WFViewManager.QFileDialog.getOpenFileName') as mock_dialog:
            # Setup return values
            mock_dialog.return_value = (local_path, "")
            
            # Mock upload_file signal
            view_manager.upload_file = MagicMock()
            
            # Call method
            view_manager._on_file_upload(remote_dir)
            
            # Verify dialog was shown with correct arguments
            mock_dialog.assert_called_once()
            assert mock_dialog.call_args[0][0] is view_manager._editor
            assert mock_dialog.call_args[0][1] == "Select file for upload"
            
            # Verify signal was emitted
            view_manager.upload_file.emit.assert_called_once_with(local_path, remote_dir)

    def test_on_workflow_saved_success(self, view_manager):
        """Test _on_workflow_saved method with success."""
        # Mock request_saved_workflows_update signal
        view_manager.request_saved_workflows_update = MagicMock()
        
        # Call method
        folder = "/path/to/workflow"
        view_manager._on_workflow_saved(True, folder)
        
        # Verify signal was emitted
        view_manager.request_saved_workflows_update.emit.assert_called_once_with(folder)

    def test_on_workflow_saved_failure(self, view_manager):
        """Test _on_workflow_saved method with failure."""
        # Mock show_error
        view_manager.show_error = MagicMock()
        
        # Call method
        folder = "/path/to/workflow"
        view_manager._on_workflow_saved(False, folder)
        
        # Verify show_error was called
        view_manager.show_error.assert_called_once()
        assert folder in view_manager.show_error.call_args[0][0]

    def test_get_editor(self, view_manager):
        """Test get_editor method."""
        # Call method
        result = view_manager.get_editor()
        
        # Verify result
        assert result is view_manager._editor

    def test_exit(self, view_manager):
        """Test exit method."""
        # Setup webengineviews
        view1 = MagicMock()
        view2 = MagicMock()
        view_manager._webengineviews = [view1, view2]
        
        # Call method
        view_manager.exit()
        
        # Verify webengineviews were cleared
        assert view_manager._webengineviews == []

    def test_get_homedir(self):
        """Test get_homedir static method."""
        # Mock QStandardPaths.standardLocations
        with patch('simstack.view.WFViewManager.QStandardPaths.standardLocations') as mock_std_paths:
            # Setup return value
            mock_std_paths.return_value = ["/home/user"]
            
            # Call method
            result = WFViewManager.get_homedir()
            
            # Verify result
            assert result == "/home/user"
            
            # Test with single path instead of list
            mock_std_paths.return_value = "/home/user2"
            
            # Call method
            result = WFViewManager.get_homedir()
            
            # Verify result
            assert result == "/home/user2"

    def test_add_webengine_view(self, view_manager):
        """Test add_webengine_view method."""
        # Create a mock view
        view = MagicMock()
        
        # Call method
        view_manager.add_webengine_view(view)
        
        # Verify view was added
        assert view in view_manager._webengineviews

    def test_connect_signals(self, view_manager):
        """Test _connect_signals method."""
        # Create a new manager to test signal connections
        with patch('simstack.view.WFViewManager.WFEditor') as mock_editor_class, \
             patch('simstack.view.WFViewManager.WFEditorMainWindow') as mock_window_class:
            
            # Create mock instances
            mock_editor = MagicMock()
            mock_window = MagicMock()
            
            # Setup return values
            mock_editor_class.return_value = mock_editor
            mock_window_class.return_value = mock_window
            
            # Create manager
            manager = WFViewManager()
            
            # Verify signals from mainwindow were connected
            mock_window.open_file.connect.assert_called_with(manager.open_dialog_open_workflow)
            mock_window.save.connect.assert_called_with(manager.open_dialog_save_workflow)
            mock_window.save_as.connect.assert_called_with(manager.open_dialog_save_workflow_as)
            mock_window.run.connect.assert_called_with(manager.run_clicked)
            mock_window.new_file.connect.assert_called_with(manager.open_new_workflow)
            
            # Verify forwarded signals
            mock_window.save_registries.connect.assert_called_with(manager.save_registries)
            mock_window.save_paths.connect.assert_called_with(manager.save_paths)
            mock_window.open_registry_settings.connect.assert_called_with(manager.open_registry_settings)
            mock_window.open_path_settings.connect.assert_called_with(manager.open_path_settings)
            mock_window.exit_client.connect.assert_called_with(manager.exit_client)
            
            # Verify editor signals
            mock_editor.registry_changed.connect.assert_called_with(manager.registry_changed)
            mock_editor.connect_registry.connect.assert_called_with(manager.connect_registry)
            mock_editor.disconnect_registry.connect.assert_called_with(manager.disconnect_registry)
            mock_editor.request_job_list_update.connect.assert_called_with(manager.request_job_list_update)
            mock_editor.request_worflow_list_update.connect.assert_called_with(manager.request_worflow_list_update)
            mock_editor.request_job_update.connect.assert_called_with(manager.request_job_update)
            mock_editor.request_worflow_update.connect.assert_called_with(manager.request_worflow_update)
            mock_editor.request_directory_update.connect.assert_called_with(manager.request_directory_update)
            mock_editor.download_file.connect.assert_called_with(manager._on_file_download)
            mock_editor.upload_file_to.connect.assert_called_with(manager._on_file_upload)
            mock_editor.delete_job.connect.assert_called_with(manager.delete_job)
            mock_editor.abort_job.connect.assert_called_with(manager.abort_job)
            mock_editor.browse_workflow.connect.assert_called_with(manager.browse_workflow)
            mock_editor.delete_workflow.connect.assert_called_with(manager.delete_workflow)
            mock_editor.abort_workflow.connect.assert_called_with(manager.abort_workflow)
            mock_editor.delete_file.connect.assert_called_with(manager.delete_file)
            mock_editor.workflow_saved.connect.assert_called_with(manager._on_workflow_saved)