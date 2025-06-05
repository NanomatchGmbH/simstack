import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QPushButton, QToolButton
from PySide6.QtCore import Qt

from simstack.view.WaNoSettings import (
    WaNoPathSettings,
    WaNoTabButtonsWidget,
)


class TestWaNoPathSettings:
    """Tests for the WaNoPathSettings class."""

    @pytest.fixture
    def path_settings_dialog(self, qtbot):
        """Create a WaNoPathSettings instance."""
        # Create test path settings
        path_settings = {
            "wanoRepo": "/path/to/wano_repo",
            "workflows": "/path/to/workflows",
        }

        # Create dialog
        dialog = WaNoPathSettings(path_settings, None)
        qtbot.addWidget(dialog)
        return dialog

    def test_init(self, path_settings_dialog):
        """Test initialization of WaNoPathSettings."""
        # Verify window title
        assert path_settings_dialog.windowTitle() == "Select Paths"

        # Verify path fields were initialized with settings
        assert path_settings_dialog.wanopath.text() == "/path/to/wano_repo"
        assert path_settings_dialog.workflowpath.text() == "/path/to/workflows"

        # Verify buttons were created
        assert isinstance(path_settings_dialog.wanopicker, QPushButton)
        assert isinstance(path_settings_dialog.workflowpicker, QPushButton)
        assert isinstance(path_settings_dialog.save, QPushButton)
        assert isinstance(path_settings_dialog.cancel, QPushButton)

    def test_show_dialog_workflow(self, path_settings_dialog, qtbot):
        """Test __showLocalDialogWorkflow method."""
        # Mock QFileDialog.getExistingDirectory
        with patch(
            "simstack.view.WaNoSettings.QFileDialog.getExistingDirectory"
        ) as mock_dialog:
            mock_dialog.return_value = "/new/workflow/path"

            # Trigger the dialog
            qtbot.mouseClick(path_settings_dialog.workflowpicker, Qt.LeftButton)

            # Verify dialog was called with correct arguments
            mock_dialog.assert_called_once()
            assert mock_dialog.call_args[0][1] == "Choose Directory"

            # Verify text was updated
            assert path_settings_dialog.workflowpath.text() == "/new/workflow/path"

    def test_show_dialog_wano(self, path_settings_dialog, qtbot):
        """Test __showLocalDialogWaNo method."""
        # Mock QFileDialog.getExistingDirectory
        with patch(
            "simstack.view.WaNoSettings.QFileDialog.getExistingDirectory"
        ) as mock_dialog:
            mock_dialog.return_value = "/new/wano/path"

            # Trigger the dialog
            qtbot.mouseClick(path_settings_dialog.wanopicker, Qt.LeftButton)

            # Verify dialog was called with correct arguments
            mock_dialog.assert_called_once()
            assert mock_dialog.call_args[0][1] == "Choose Directory"

            # Verify text was updated
            assert path_settings_dialog.wanopath.text() == "/new/wano/path"

    def test_show_dialog_canceled(self, path_settings_dialog, qtbot):
        """Test dialog cancellation."""
        # Mock QFileDialog.getExistingDirectory to return empty string (canceled)
        with patch(
            "simstack.view.WaNoSettings.QFileDialog.getExistingDirectory"
        ) as mock_dialog:
            mock_dialog.return_value = ""

            # Trigger the dialog
            qtbot.mouseClick(path_settings_dialog.wanopicker, Qt.LeftButton)

            # Verify text was not updated
            assert path_settings_dialog.wanopath.text() == "/path/to/wano_repo"

    def test_get_settings(self, path_settings_dialog):
        """Test get_settings method."""
        # Set new paths
        path_settings_dialog.wanopath.setText("/new/wano/path")
        path_settings_dialog.workflowpath.setText("/new/workflow/path")

        # Get settings
        settings = path_settings_dialog.get_settings()

        # Verify settings
        assert settings == {
            "wanoRepo": "/new/wano/path",
            "workflows": "/new/workflow/path",
        }

    def test_on_save(self, path_settings_dialog, qtbot):
        """Test _on_save method."""
        # Mock accept
        path_settings_dialog.accept = MagicMock()

        # Trigger save
        qtbot.mouseClick(path_settings_dialog.save, Qt.LeftButton)

        # Verify accept was called
        path_settings_dialog.accept.assert_called_once()

    def test_on_cancel(self, path_settings_dialog, qtbot):
        """Test _on_cancel method."""
        # Mock reject
        path_settings_dialog.reject = MagicMock()

        # Trigger cancel
        qtbot.mouseClick(path_settings_dialog.cancel, Qt.LeftButton)

        # Verify reject was called
        path_settings_dialog.reject.assert_called_once()


class TestWaNoTabButtonsWidget:
    """Tests for the WaNoTabButtonsWidget class."""

    @pytest.fixture
    def tab_buttons(self, qtbot):
        """Create a WaNoTabButtonsWidget instance."""
        widget = WaNoTabButtonsWidget(None)
        qtbot.addWidget(widget)
        return widget

    def test_init(self, tab_buttons):
        """Test initialization of WaNoTabButtonsWidget."""
        # Verify buttons were created
        add_btn = tab_buttons._WaNoTabButtonsWidget__btn_addRegistry
        remove_btn = tab_buttons._WaNoTabButtonsWidget__btn_removeRegistry

        assert isinstance(add_btn, QToolButton)
        assert isinstance(remove_btn, QToolButton)

        # Verify button text
        assert add_btn.text() == "+"
        assert remove_btn.text() == "-"

        # Verify tooltips
        assert add_btn.toolTip() == "Add Registry"
        assert remove_btn.toolTip() == "Remove Registry"

    def test_signals_connected(self, tab_buttons):
        """Test signals are connected."""
        # Verify signals are connected
        add_btn = tab_buttons._WaNoTabButtonsWidget__btn_addRegistry
        remove_btn = tab_buttons._WaNoTabButtonsWidget__btn_removeRegistry

        assert add_btn.clicked.isConnected()
        assert remove_btn.clicked.isConnected()

    def test_disable_remove(self, tab_buttons):
        """Test disable_remove method."""
        # Get remove button
        remove_btn = tab_buttons._WaNoTabButtonsWidget__btn_removeRegistry

        # Enable button
        remove_btn.setEnabled(True)

        # Call method
        tab_buttons.disable_remove()

        # Verify button is disabled
        assert not remove_btn.isEnabled()

    def test_enable_remove(self, tab_buttons):
        """Test enable_remove method."""
        # Get remove button
        remove_btn = tab_buttons._WaNoTabButtonsWidget__btn_removeRegistry

        # Disable button
        remove_btn.setEnabled(False)

        # Call method
        tab_buttons.enable_remove()

        # Verify button is enabled
        assert remove_btn.isEnabled()

    def test_signals_emitted(self, tab_buttons, qtbot):
        """Test signals are emitted when buttons are clicked."""
        # Set up signal spy
        with qtbot.waitSignal(tab_buttons.addClicked) as add_spy:
            # Click add button
            qtbot.mouseClick(
                tab_buttons._WaNoTabButtonsWidget__btn_addRegistry, Qt.LeftButton
            )

        # Verify add signal was emitted
        assert add_spy.signal_triggered

        # Set up signal spy
        with qtbot.waitSignal(tab_buttons.removeClicked) as remove_spy:
            # Click remove button
            qtbot.mouseClick(
                tab_buttons._WaNoTabButtonsWidget__btn_removeRegistry, Qt.LeftButton
            )

        # Verify remove signal was emitted
        assert remove_spy.signal_triggered
