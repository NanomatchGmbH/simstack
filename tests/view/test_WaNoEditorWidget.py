import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QWidget, QMessageBox

from simstack.view.WaNoEditorWidget import WaNoEditor


class TestWaNoEditor:
    """Tests for the WaNoEditor class."""

    @pytest.fixture
    def editor(self, qtbot):
        """Create a WaNoEditor instance with mocked dependencies."""
        # Mock editor
        main_editor = MagicMock()

        # Create editor
        with patch("simstack.view.WaNoEditorWidget.logging"):
            widget = WaNoEditor(main_editor)
            qtbot.addWidget(widget)
            return widget

    def test_init(self, editor):
        """Test initialization of WaNoEditor."""
        # Verify properties were set
        assert editor.activeTabs == []
        assert editor.editor is not None
        assert editor.changedFlag is False
        assert editor.tabWidget is editor

        # Verify widget properties
        assert editor.isTabsClosable() is True
        assert editor.minimumWidth() == 400
        assert editor.minimumHeight() == 300

        # Verify signals are connected
        assert editor.tabCloseRequested.isConnected()

    def test_close_tab(self, editor):
        """Test closeTab method."""
        # Mock removeTab
        editor.removeTab = MagicMock()

        # Call method
        editor.closeTab(2)

        # Verify removeTab was called
        editor.removeTab.assert_called_once_with(2)

    def test_paint_event_empty(self, editor):
        """Test paintEvent method with no tabs."""
        # Mock count
        editor.count = MagicMock(return_value=0)

        # Mock QPainter
        with patch(
            "simstack.view.WaNoEditorWidget.QtGui.QPainter"
        ) as mock_painter_class:
            # Mock painter instance
            mock_painter = MagicMock()
            mock_painter_class.return_value = mock_painter

            # Mock event
            mock_event = MagicMock()

            # Call method
            editor.paintEvent(mock_event)

            # Verify painter methods were called
            mock_painter.begin.assert_called_once_with(editor)
            mock_painter.setFont.assert_called_once()
            mock_painter.drawText.assert_called_once()
            mock_painter.end.assert_called_once()

            # Verify event was accepted
            mock_event.accept.assert_called_once()

    def test_paint_event_with_tabs(self, editor):
        """Test paintEvent method with tabs."""
        # Mock count
        editor.count = MagicMock(return_value=2)

        # Mock super.paintEvent
        with patch("PySide6.QtWidgets.QTabWidget.paintEvent") as mock_super_paint:
            # Mock event
            mock_event = MagicMock()

            # Call method
            editor.paintEvent(mock_event)

            # Verify super.paintEvent was called
            mock_super_paint.assert_called_once()

            # Verify event was not accepted
            mock_event.accept.assert_not_called()

    def test_has_changed(self):
        """Test hasChanged method."""
        # Reset class variable
        WaNoEditor.changedFlag = False

        # Call method
        with patch("simstack.view.WaNoEditorWidget.logging"):
            WaNoEditor.hasChanged()

        # Verify changed flag was set
        assert WaNoEditor.changedFlag is True

    def test_init_new_wano(self, editor):
        """Test init method with new WaNo."""
        # Reset changed flag
        WaNoEditor.changedFlag = False

        # Mock wano
        mock_wano = MagicMock()
        mock_wano.model.name = "TestWaNo"
        mock_wano.get_widget.return_value = QWidget()
        mock_wano.get_resource_widget.return_value = QWidget()
        mock_wano.get_import_widget.return_value = QWidget()
        mock_wano.get_export_widget.return_value = QWidget()

        # Mock clear
        editor.clear = MagicMock()

        # Mock addTab
        editor.tabWidget.addTab = MagicMock()

        # Call method
        result = editor.init(mock_wano)

        # Verify result
        assert result is True

        # Verify clear was called
        editor.clear.assert_called_once()

        # Verify wano was set
        assert editor.wano is mock_wano

        # Verify tabs were added
        assert editor.tabWidget.addTab.call_count == 4
        editor.tabWidget.addTab.assert_any_call(
            mock_wano.get_widget(), mock_wano.model.name
        )
        editor.tabWidget.addTab.assert_any_call(
            mock_wano.get_resource_widget(), "Resources"
        )
        editor.tabWidget.addTab.assert_any_call(
            mock_wano.get_import_widget(), "Imports"
        )
        editor.tabWidget.addTab.assert_any_call(
            mock_wano.get_export_widget(), "Exports"
        )

        # Verify changed flag was reset
        assert WaNoEditor.changedFlag is False

    def test_init_with_changed_flag(self, editor):
        """Test init method with changed flag set."""
        # Set changed flag
        WaNoEditor.changedFlag = True

        # Set activeTabs
        editor.activeTabs = [MagicMock(), MagicMock()]

        # Mock closeAction
        editor.closeAction = MagicMock(return_value=QMessageBox.Discard)

        # Mock wano
        mock_wano = MagicMock()
        mock_wano.model.name = "TestWaNo"
        mock_wano.get_widget.return_value = QWidget()
        mock_wano.get_resource_widget.return_value = QWidget()
        mock_wano.get_import_widget.return_value = QWidget()
        mock_wano.get_export_widget.return_value = QWidget()

        # Mock clear and addTab
        editor.clear = MagicMock()
        editor.tabWidget.addTab = MagicMock()

        # Call method
        result = editor.init(mock_wano)

        # Verify result
        assert result is True

        # Verify closeAction was called
        editor.closeAction.assert_called_once()

        # Verify clear was called
        assert (
            editor.clear.call_count == 2
        )  # Called once before checking changedFlag and once after

    def test_init_with_cancel(self, editor):
        """Test init method with cancel from closeAction."""
        # Set changed flag
        WaNoEditor.changedFlag = True

        # Set activeTabs
        editor.activeTabs = [MagicMock(), MagicMock()]

        # Mock closeAction
        editor.closeAction = MagicMock(return_value=QMessageBox.Cancel)

        # Call method
        result = editor.init(MagicMock())

        # Verify result
        assert result is False

    def test_remove_if_open_match(self, editor):
        """Test remove_if_open method with matching WaNo."""
        # Mock wano
        mock_wano = MagicMock()
        widget = QWidget()
        mock_wano.get_widget.return_value = widget

        # Mock tabWidget
        editor.tabWidget.widget = MagicMock(return_value=widget)
        editor.tabWidget.count = MagicMock(return_value=4)
        editor.tabWidget.closeTab = MagicMock()

        # Call method
        editor.remove_if_open(mock_wano)

        # Verify closeTab was called for each tab (in reverse order)
        assert editor.tabWidget.closeTab.call_count == 4
        editor.tabWidget.closeTab.assert_any_call(3)
        editor.tabWidget.closeTab.assert_any_call(2)
        editor.tabWidget.closeTab.assert_any_call(1)
        editor.tabWidget.closeTab.assert_any_call(0)

    def test_remove_if_open_no_match(self, editor):
        """Test remove_if_open method with non-matching WaNo."""
        # Mock wano
        mock_wano = MagicMock()
        widget1 = QWidget()
        widget2 = QWidget()  # Different widget
        mock_wano.get_widget.return_value = widget1

        # Mock tabWidget
        editor.tabWidget.widget = MagicMock(return_value=widget2)
        editor.tabWidget.closeTab = MagicMock()

        # Call method
        editor.remove_if_open(mock_wano)

        # Verify closeTab was not called
        editor.tabWidget.closeTab.assert_not_called()

    def test_delete_close_no_change(self, editor):
        """Test deleteClose method with no changes."""
        # Reset changed flag
        WaNoEditor.changedFlag = False

        # Call method
        editor.deleteClose()

        # Verify deactivateWidget was called
        editor.editor.deactivateWidget.assert_called_once()

        # Verify clear was called
        editor.clear.assert_called_once()

    def test_delete_close_with_save(self, editor):
        """Test deleteClose method with changes and save."""
        # Set changed flag
        WaNoEditor.changedFlag = True

        # Mock closeAction
        editor.closeAction = MagicMock(return_value=QMessageBox.Save)

        # Mock copyContent
        editor.copyContent = MagicMock()

        # Call method
        with patch("simstack.view.WaNoEditorWidget.WFWorkflowWidget") as mock_wf_widget:
            editor.deleteClose()

            # Verify hasChanged was called
            mock_wf_widget.hasChanged.assert_called_once()

        # Verify copyContent was called
        editor.copyContent.assert_called_once()

        # Verify deactivateWidget was called
        editor.editor.deactivateWidget.assert_called_once()

        # Verify clear was called
        editor.clear.assert_called_once()

    def test_delete_close_with_cancel(self, editor):
        """Test deleteClose method with changes and cancel."""
        # Set changed flag
        WaNoEditor.changedFlag = True

        # Mock closeAction
        editor.closeAction = MagicMock(return_value=QMessageBox.Cancel)

        # Call method
        editor.deleteClose()

        # Verify deactivateWidget was not called
        editor.editor.deactivateWidget.assert_not_called()

        # Verify clear was not called
        editor.clear.assert_not_called()

    def test_save_close(self, editor):
        """Test saveClose method."""
        # Mock copyContent
        editor.copyContent = MagicMock()

        # Mock deleteClose
        editor.deleteClose = MagicMock()

        # Call method with changed flag
        WaNoEditor.changedFlag = True
        with patch("simstack.view.WaNoEditorWidget.WFWorkflowWidget") as mock_wf_widget:
            editor.saveClose()

            # Verify hasChanged was called
            mock_wf_widget.hasChanged.assert_called_once()

        # Call method without changed flag
        WaNoEditor.changedFlag = False
        editor.copyContent.reset_mock()
        with patch("simstack.view.WaNoEditorWidget.WFWorkflowWidget") as mock_wf_widget:
            editor.saveClose()

            # Verify hasChanged was not called
            mock_wf_widget.hasChanged.assert_not_called()

        # Verify copyContent was called both times
        assert editor.copyContent.call_count == 2

        # Verify deleteClose was called both times
        assert editor.deleteClose.call_count == 2

    def test_copy_content(self, editor):
        """Test copyContent method."""
        # Create mock active tabs
        tab1 = MagicMock()
        tab2 = MagicMock()
        editor.activeTabs = [tab1, tab2]

        # Set changed flag
        WaNoEditor.changedFlag = True

        # Call method
        editor.copyContent()

        # Verify copyContent was called on each tab
        tab1.copyContent.assert_called_once()
        tab2.copyContent.assert_called_once()

        # Verify changed flag was reset
        assert WaNoEditor.changedFlag is False

    def test_close_action(self, editor):
        """Test closeAction method."""
        # Mock QMessageBox
        with patch(
            "simstack.view.WaNoEditorWidget.QtWidgets.QMessageBox"
        ) as mock_msg_box:
            # Mock message box instance
            mock_instance = MagicMock()
            mock_msg_box.return_value = mock_instance

            # Mock exec return value
            mock_instance.exec_.return_value = QMessageBox.Save

            # Call method
            result = editor.closeAction()

            # Verify message box was created with correct parameters
            mock_msg_box.assert_called_once_with(editor)
            mock_instance.setText.assert_called_once_with(
                "The Workflow Active Node Data has changed."
            )
            mock_instance.setInformativeText.assert_called_once_with(
                "Do you want to save your changes?"
            )
            mock_instance.setStandardButtons.assert_called_once()
            mock_instance.setDefaultButton.assert_called_once_with(QMessageBox.Save)

            # Verify result
            assert result == QMessageBox.Save

            # Mock copyContent
            editor.copyContent = MagicMock()

            # Call method again
            result = editor.closeAction()

            # Verify copyContent was called
            editor.copyContent.assert_called_once()

            # Test with Cancel
            mock_instance.exec_.return_value = QMessageBox.Cancel

            # Call method again
            result = editor.closeAction()

            # Verify result
            assert result == QMessageBox.Cancel
