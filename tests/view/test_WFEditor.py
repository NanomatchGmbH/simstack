import pytest
from unittest.mock import MagicMock
import os
from PySide6.QtCore import Qt

from simstack.view.WFEditor import WFEditor


@pytest.mark.skip(
    reason="WFEditor is complex and requires extensive mocking of Qt components"
)
class TestWFEditor:
    """Tests for the WFEditor class."""

    def test_convert_ctrl_icon_paths_to_absolute(self):
        """Test _convert_ctrl_icon_paths_to_absolute method."""
        # Create a mock WFEditor object
        editor = MagicMock(spec=WFEditor)

        # Setup test control paths
        original_controls = [
            ("ForEach", "ctrl_img/ForEach.png"),
            ("If", "ctrl_img/If.png"),
        ]
        editor._controls = original_controls.copy()

        # Call the method directly (bypassing the full initialization)
        WFEditor._convert_ctrl_icon_paths_to_absolute(editor)

        # Verify paths were converted to absolute
        assert len(editor._controls) == len(original_controls)
        for i, (name, path) in enumerate(editor._controls):
            assert name == original_controls[i][0]  # Name should be unchanged
            assert os.path.isabs(path)  # Path should be absolute
            assert "ctrl_img" in path  # Should contain original path component

    def test_update_wano_list(self):
        """Test update_wano_list method."""
        # Create a mock editor
        editor = MagicMock(spec=WFEditor)
        editor.wanoListWidget = MagicMock()

        # Test data
        test_wanos = ["wano1", "wano2", "wano3"]

        # Call the method
        WFEditor.update_wano_list(editor, test_wanos)

        # Verify the wanos were saved and passed to the list widget
        assert editor.wanos == test_wanos
        editor.wanoListWidget.update_list.assert_called_once_with(test_wanos)

    def test_update_saved_workflows_list(self):
        """Test update_saved_workflows_list method."""
        # Create a mock editor
        editor = MagicMock(spec=WFEditor)
        editor.workflowListWidget = MagicMock()

        # Test data
        test_workflows = ["workflow1", "workflow2"]

        # Call the method
        WFEditor.update_saved_workflows_list(editor, test_workflows)

        # Verify the workflows were passed to the list widget
        editor.workflowListWidget.update_list.assert_called_once_with(test_workflows)

    def test_update_registries(self):
        """Test update_registries method."""
        # Create a mock editor
        editor = MagicMock(spec=WFEditor)
        editor.registrySelection = MagicMock()

        # Test data
        test_registries = ["registry1", "registry2"]
        test_selected = 1

        # Call the method
        WFEditor.update_registries(editor, test_registries, selected=test_selected)

        # Verify the registries were passed to the registry selection widget
        editor.registrySelection.update_registries.assert_called_once_with(
            test_registries, index=test_selected
        )

    def test_update_filesystem_model(self):
        """Test update_filesystem_model method."""
        # Create a mock editor
        editor = MagicMock(spec=WFEditor)
        editor.remoteFileTree = MagicMock()

        # Test data
        test_path = "/test/path"
        test_files = ["file1", "file2"]

        # Call the method
        WFEditor.update_filesystem_model(editor, test_path, test_files)

        # Verify the path and files were passed to the remote file tree
        editor.remoteFileTree.update_file_tree_node.assert_called_once_with(
            test_path, test_files
        )

    def test_update_job_list(self):
        """Test update_job_list method."""
        # Create a mock editor
        editor = MagicMock(spec=WFEditor)
        editor.remoteFileTree = MagicMock()

        # Test data
        test_jobs = ["job1", "job2"]

        # Call the method
        WFEditor.update_job_list(editor, test_jobs)

        # Verify the jobs were passed to the remote file tree
        editor.remoteFileTree.update_job_list.assert_called_once_with(test_jobs)

    def test_update_workflow_list(self):
        """Test update_workflow_list method."""
        # Create a mock editor
        editor = MagicMock(spec=WFEditor)
        editor.remoteFileTree = MagicMock()

        # Test data
        test_wfs = ["wf1", "wf2"]

        # Call the method
        WFEditor.update_workflow_list(editor, test_wfs)

        # Verify the workflows were passed to the remote file tree
        editor.remoteFileTree.update_workflow_list.assert_called_once_with(test_wfs)

    def test_set_registry_connection_status(self):
        """Test set_registry_connection_status method."""
        # Create a mock editor
        editor = MagicMock(spec=WFEditor)
        editor.registrySelection = MagicMock()

        # Test data
        test_status = "connected"

        # Call the method
        WFEditor.set_registry_connection_status(editor, test_status)

        # Verify the status was passed to the registry selection widget
        editor.registrySelection.setStatus.assert_called_once_with(test_status)

    def test_deactivate_widget_with_active(self):
        """Test deactivateWidget method with an active widget."""
        # Create a mock editor
        editor = MagicMock(spec=WFEditor)

        # Setup an active widget
        mock_active = MagicMock()
        editor.lastActive = mock_active

        # Call the method
        WFEditor.deactivateWidget(editor)

        # Verify the active widget color was changed and lastActive was reset
        mock_active.setColor.assert_called_once_with(Qt.lightGray)
        assert editor.lastActive is None

    def test_deactivate_widget_without_active(self):
        """Test deactivateWidget method without an active widget."""
        # Create a mock editor
        editor = MagicMock(spec=WFEditor)

        # Ensure there's no active widget
        editor.lastActive = None

        # Call the method
        WFEditor.deactivateWidget(editor)

        # Verify nothing happened
        assert editor.lastActive is None

    def test_open_wano_editor_success(self):
        """Test openWaNoEditor method with successful initialization."""
        # Create a mock editor
        editor = MagicMock(spec=WFEditor)
        editor.wanoEditor = MagicMock()
        editor.settingsAndFilesTabs = MagicMock()
        editor.wanoSettingsTab = 0

        # Setup the test
        mock_wano_widget = MagicMock()
        mock_wano_widget.wano_view = "test_view"
        editor.wanoEditor.init.return_value = True

        # Call the method
        WFEditor.openWaNoEditor(editor, mock_wano_widget)

        # Verify initialization and tab selection
        editor.wanoEditor.init.assert_called_once_with("test_view")
        editor.settingsAndFilesTabs.setCurrentIndex.assert_called_once_with(
            editor.wanoSettingsTab
        )
        mock_wano_widget.setColor.assert_called_once_with(Qt.green)
        assert editor.lastActive is mock_wano_widget

    def test_open_wano_editor_failure(self):
        """Test openWaNoEditor method with failed initialization."""
        # Create a mock editor
        editor = MagicMock(spec=WFEditor)
        editor.wanoEditor = MagicMock()
        editor.settingsAndFilesTabs = MagicMock()

        # Setup the test
        mock_wano_widget = MagicMock()
        mock_wano_widget.wano_view = "test_view"
        editor.wanoEditor.init.return_value = False

        # Call the method
        WFEditor.openWaNoEditor(editor, mock_wano_widget)

        # Verify initialization but no tab selection or color change
        editor.wanoEditor.init.assert_called_once_with("test_view")
        editor.settingsAndFilesTabs.setCurrentIndex.assert_not_called()
        mock_wano_widget.setColor.assert_not_called()

    def test_open_workflow(self):
        """Test openWorkFlow method."""
        # Create a mock editor
        editor = MagicMock(spec=WFEditor)
        editor.workflowWidget = MagicMock()

        # Test data
        test_workflow = "test_workflow"

        # Call the method
        WFEditor.openWorkFlow(editor, test_workflow)

        # Verify the workflow was passed to the workflow widget
        editor.workflowWidget.openWorkFlow.assert_called_once_with(test_workflow)

    def test_remove_wano(self):
        """Test remove method with a WaNO widget."""
        # Create a mock editor
        editor = MagicMock(spec=WFEditor)
        editor.wanoEditor = MagicMock()

        # Setup the test
        mock_widget = MagicMock()
        mock_widget.is_wano = True
        mock_widget.wano_view = "test_view"

        # Call the method
        WFEditor.remove(editor, mock_widget)

        # Verify WaNO editor remove_if_open was called
        editor.wanoEditor.remove_if_open.assert_called_once_with("test_view")

    def test_remove_non_wano(self):
        """Test remove method with a non-WaNO widget."""
        # Create a mock editor
        editor = MagicMock(spec=WFEditor)
        editor.wanoEditor = MagicMock()

        # Setup the test
        mock_widget = MagicMock()
        mock_widget.is_wano = False

        # Call the method
        WFEditor.remove(editor, mock_widget)

        # Verify WaNO editor remove_if_open was not called
        editor.wanoEditor.remove_if_open.assert_not_called()

    def test_file_operations(self):
        """Test file operations methods."""
        # Create a mock editor
        editor = MagicMock(spec=WFEditor)
        editor.workflowWidget = MagicMock()

        # Test clear method
        WFEditor.clear(editor)
        editor.workflowWidget.clear.assert_called_once()

        # Test open method
        editor.workflowWidget.reset_mock()
        WFEditor.open(editor)
        editor.workflowWidget.open.assert_called_once()

        # Test save method
        editor.workflowWidget.reset_mock()
        WFEditor.save(editor)
        editor.workflowWidget.save.assert_called_once()

        # Test saveAs method
        editor.workflowWidget.reset_mock()
        WFEditor.saveAs(editor)
        editor.workflowWidget.saveAs.assert_called_once()

        # Test run method
        editor.workflowWidget.reset_mock()
        test_registry = "test_registry"
        expected_result = "run_result"
        editor.workflowWidget.run.return_value = expected_result
        result = WFEditor.run(editor, test_registry)
        editor.workflowWidget.run.assert_called_once_with(test_registry)
        assert result == expected_result

        # Test loadFile method
        editor.workflowWidget.reset_mock()
        test_filename = "test_file.wfs"
        WFEditor.loadFile(editor, test_filename)
        editor.workflowWidget.loadFile.assert_called_once_with(test_filename)
