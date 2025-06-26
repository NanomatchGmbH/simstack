import pytest
from unittest.mock import MagicMock, patch

from simstack.view.WFEditor import WFEditor


class TestWFEditorClassAttributes:
    """Tests for WFEditor class attributes and simple static functionality."""

    def test_class_constants(self):
        """Test class constants are properly defined."""
        # Test _controls constant
        assert isinstance(WFEditor._controls, list)
        assert len(WFEditor._controls) == 6

        # Test each control has name and icon path
        for control in WFEditor._controls:
            assert isinstance(control, tuple)
            assert len(control) == 2
            assert isinstance(control[0], str)  # Control name
            assert isinstance(control[1], str)  # Icon path
            assert control[1].endswith(".png")

        # Test registry connection states
        assert hasattr(WFEditor, "REGISTRY_CONNECTION_STATES")

    def test_signals_defined(self):
        """Test that all expected signals are defined as class attributes."""
        # Verify all signals exist
        assert hasattr(WFEditor, "registry_changed")
        assert hasattr(WFEditor, "disconnect_registry")
        assert hasattr(WFEditor, "connect_registry")
        assert hasattr(WFEditor, "request_job_list_update")
        assert hasattr(WFEditor, "request_worflow_list_update")
        assert hasattr(WFEditor, "request_job_update")
        assert hasattr(WFEditor, "request_worflow_update")
        assert hasattr(WFEditor, "request_directory_update")
        assert hasattr(WFEditor, "download_file")
        assert hasattr(WFEditor, "upload_file_to")
        assert hasattr(WFEditor, "delete_file")
        assert hasattr(WFEditor, "delete_job")
        assert hasattr(WFEditor, "abort_job")
        assert hasattr(WFEditor, "browse_workflow")
        assert hasattr(WFEditor, "delete_workflow")
        assert hasattr(WFEditor, "abort_workflow")


class TestWFEditorMethods:
    """Tests for WFEditor methods that can be tested without full Qt initialization."""

    @pytest.fixture
    def mock_editor_instance(self):
        """Create a mock WFEditor instance with required attributes."""
        editor = MagicMock(spec=WFEditor)

        # Add required attributes for delegation methods
        editor.wanoListWidget = MagicMock()
        editor.workflowListWidget = MagicMock()
        editor.registrySelection = MagicMock()
        editor.remoteFileTree = MagicMock()
        editor.workflowWidget = MagicMock()
        editor.wanoEditor = MagicMock()
        editor.wanos = []

        return editor

    def test_convert_ctrl_icon_paths_to_absolute(self):
        """Test _convert_ctrl_icon_paths_to_absolute static method logic."""
        original_controls = [
            ("ForEach", "ctrl_img/ForEach.png"),
            ("If", "ctrl_img/If.png"),
        ]

        with patch.object(WFEditor, "_controls", original_controls):
            with patch("os.path.dirname") as mock_dirname, patch(
                "os.path.join"
            ) as mock_join:
                mock_dirname.return_value = "/app/directory"
                mock_join.side_effect = lambda *args: "/".join(args)

                # Create instance without calling __init__ to avoid Qt setup
                editor = WFEditor.__new__(WFEditor)
                editor._convert_ctrl_icon_paths_to_absolute()

                # Verify os.path.join was called for each control
                assert mock_join.call_count == len(original_controls)

    def test_update_wano_list(self, mock_editor_instance):
        """Test update_wano_list method using real implementation."""
        wanos = ["wano1", "wano2", "wano3"]

        # Use the real method implementation
        WFEditor.update_wano_list(mock_editor_instance, wanos)

        # Verify delegation
        mock_editor_instance.wanoListWidget.update_list.assert_called_once_with(wanos)
        # Verify attribute assignment
        assert mock_editor_instance.wanos == wanos

    def test_update_saved_workflows_list(self, mock_editor_instance):
        """Test update_saved_workflows_list method."""
        workflows = ["workflow1", "workflow2"]

        WFEditor.update_saved_workflows_list(mock_editor_instance, workflows)

        mock_editor_instance.workflowListWidget.update_list.assert_called_once_with(
            workflows
        )

    def test_update_registries(self, mock_editor_instance):
        """Test update_registries method."""
        registries = {"registry1": "config1", "registry2": "config2"}
        selected_index = 1

        WFEditor.update_registries(
            mock_editor_instance, registries, selected=selected_index
        )

        mock_editor_instance.registrySelection.update_registries.assert_called_once_with(
            registries, index=selected_index
        )

    def test_update_registries_default_selected(self, mock_editor_instance):
        """Test update_registries with default selected parameter."""
        registries = {"registry1": "config1"}

        WFEditor.update_registries(mock_editor_instance, registries)

        mock_editor_instance.registrySelection.update_registries.assert_called_once_with(
            registries, index=0
        )

    def test_update_filesystem_model(self, mock_editor_instance):
        """Test update_filesystem_model method."""
        path = "/remote/path"
        files = ["file1.txt", "file2.txt"]

        WFEditor.update_filesystem_model(mock_editor_instance, path, files)

        mock_editor_instance.remoteFileTree.update_file_tree_node.assert_called_once_with(
            path, files
        )

    def test_update_job_list(self, mock_editor_instance):
        """Test update_job_list method."""
        jobs = ["job1", "job2", "job3"]

        WFEditor.update_job_list(mock_editor_instance, jobs)

        mock_editor_instance.remoteFileTree.update_job_list.assert_called_once_with(
            jobs
        )

    def test_update_workflow_list(self, mock_editor_instance):
        """Test update_workflow_list method."""
        workflows = ["wf1", "wf2"]

        WFEditor.update_workflow_list(mock_editor_instance, workflows)

        mock_editor_instance.remoteFileTree.update_workflow_list.assert_called_once_with(
            workflows
        )

    def test_set_registry_connection_status(self, mock_editor_instance):
        """Test set_registry_connection_status method."""
        status = "connected"

        WFEditor.set_registry_connection_status(mock_editor_instance, status)

        mock_editor_instance.registrySelection.setStatus.assert_called_once_with(status)

    def test_deactivateWidget_with_wano_editor(self, mock_editor_instance):
        """Test deactivateWidget method when lastActive exists."""
        mock_lastActive = MagicMock()
        mock_editor_instance.lastActive = mock_lastActive

        with patch("PySide6.QtCore.Qt.lightGray", 128):
            WFEditor.deactivateWidget(mock_editor_instance)

        # Verify lastActive.setColor was called
        mock_lastActive.setColor.assert_called_once_with(128)
        # Verify lastActive is set to None
        assert mock_editor_instance.lastActive is None

    def test_deactivateWidget_without_wano_editor(self, mock_editor_instance):
        """Test deactivateWidget method when lastActive is None."""
        mock_editor_instance.lastActive = None

        # Should not raise an error when lastActive is None
        WFEditor.deactivateWidget(mock_editor_instance)

    def test_openWorkFlow(self, mock_editor_instance):
        """Test openWorkFlow method."""
        workflow = MagicMock()

        WFEditor.openWorkFlow(mock_editor_instance, workflow)

        mock_editor_instance.workflowWidget.openWorkFlow.assert_called_once_with(
            workflow
        )

    def test_remove_with_wano_widget(self, mock_editor_instance):
        """Test remove method when wfwanowidget is a WaNo."""
        mock_wano_widget = MagicMock()
        mock_wano_widget.is_wano = True
        mock_wano_widget.wano_view = MagicMock()
        mock_editor_instance.wanoEditor = MagicMock()

        WFEditor.remove(mock_editor_instance, mock_wano_widget)

        # Verify remove_if_open was called
        mock_editor_instance.wanoEditor.remove_if_open.assert_called_once_with(
            mock_wano_widget.wano_view
        )

    def test_remove_with_different_widget(self, mock_editor_instance):
        """Test remove method when wfwanowidget is not a WaNo."""
        mock_editor_instance.wanoEditor = MagicMock()
        non_wano_widget = MagicMock()
        non_wano_widget.is_wano = False

        WFEditor.remove(mock_editor_instance, non_wano_widget)

        # Verify remove_if_open was not called since is_wano is False
        mock_editor_instance.wanoEditor.remove_if_open.assert_not_called()

    def test_clear(self, mock_editor_instance):
        """Test clear method."""
        WFEditor.clear(mock_editor_instance)

        mock_editor_instance.workflowWidget.clear.assert_called_once()

    def test_open(self, mock_editor_instance):
        """Test open method."""
        WFEditor.open(mock_editor_instance)

        mock_editor_instance.workflowWidget.open.assert_called_once()

    def test_save(self, mock_editor_instance):
        """Test save method."""
        WFEditor.save(mock_editor_instance)

        mock_editor_instance.workflowWidget.save.assert_called_once()

    def test_saveAs(self, mock_editor_instance):
        """Test saveAs method."""
        WFEditor.saveAs(mock_editor_instance)

        mock_editor_instance.workflowWidget.saveAs.assert_called_once()

    def test_run(self, mock_editor_instance):
        """Test run method."""
        current_registry = "test_registry"
        expected_result = "run_result"
        mock_editor_instance.workflowWidget.run.return_value = expected_result

        result = WFEditor.run(mock_editor_instance, current_registry)

        mock_editor_instance.workflowWidget.run.assert_called_once_with(
            current_registry
        )
        assert result == expected_result

    def test_loadFile(self, mock_editor_instance):
        """Test loadFile method."""
        filename = "test_workflow.xml"

        WFEditor.loadFile(mock_editor_instance, filename)

        mock_editor_instance.workflowWidget.loadFile.assert_called_once_with(filename)
