from unittest.mock import patch

from PySide6.QtWidgets import QMessageBox
from PySide6 import QtWidgets

from simstack.view.MessageDialog import MessageDialog


def test_message_dialog_init_critical(qtbot):
    """Test initializing MessageDialog with critical type"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)

    with patch.object(MessageDialog, "exec_") as mock_exec:
        dialog = MessageDialog(
            MessageDialog.MESSAGE_TYPES.critical,
            "Test critical message",
            direct_show=True,
            parent=parent,
        )

        # Check if dialog is properly configured
        assert dialog.windowTitle() == "Critical Error"
        assert dialog.text() == "Test critical message"
        assert dialog.icon() == QMessageBox.Critical

        # Check if exec_ was called
        mock_exec.assert_called_once()


def test_message_dialog_init_error(qtbot):
    """Test initializing MessageDialog with error type"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)

    with patch.object(MessageDialog, "exec_") as mock_exec:
        dialog = MessageDialog(
            MessageDialog.MESSAGE_TYPES.error,
            "Test error message",
            direct_show=True,
            parent=parent,
        )

        # Check if dialog is properly configured
        assert dialog.windowTitle() == "Error"
        assert dialog.text() == "Test error message"
        assert dialog.icon() == QMessageBox.Critical

        # Check if exec_ was called
        mock_exec.assert_called_once()


def test_message_dialog_init_warning(qtbot):
    """Test initializing MessageDialog with warning type"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)

    with patch.object(MessageDialog, "exec_") as mock_exec:
        dialog = MessageDialog(
            MessageDialog.MESSAGE_TYPES.warning,
            "Test warning message",
            direct_show=True,
            parent=parent,
        )

        # Check if dialog is properly configured
        assert dialog.windowTitle() == "Warning"
        assert dialog.text() == "Test warning message"
        assert dialog.icon() == QMessageBox.Warning

        # Check if exec_ was called
        mock_exec.assert_called_once()


def test_message_dialog_init_info(qtbot):
    """Test initializing MessageDialog with info type"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)

    with patch.object(MessageDialog, "exec_") as mock_exec:
        dialog = MessageDialog(
            MessageDialog.MESSAGE_TYPES.info,
            "Test info message",
            direct_show=True,
            parent=parent,
        )

        # Check if dialog is properly configured
        assert dialog.windowTitle() == "Info"
        assert dialog.text() == "Test info message"
        assert dialog.icon() == QMessageBox.Information

        # Check if exec_ was called
        mock_exec.assert_called_once()


def test_message_dialog_with_details(qtbot):
    """Test MessageDialog with detailed text"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)

    with patch.object(MessageDialog, "exec_") as mock_exec:
        details = "Detailed error information here"
        dialog = MessageDialog(
            MessageDialog.MESSAGE_TYPES.error,
            "Test error message",
            direct_show=True,
            parent=parent,
            details=details,
        )

        # Check if detailed text is set correctly
        assert dialog.detailedText() == details

        # Check if exec_ was called
        mock_exec.assert_called_once()


def test_message_dialog_without_direct_show(qtbot):
    """Test MessageDialog with direct_show=False"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)

    with patch.object(MessageDialog, "exec_") as mock_exec:
        MessageDialog(
            MessageDialog.MESSAGE_TYPES.info,
            "Test info message",
            direct_show=False,
            parent=parent,
        )

        # Check if exec_ was not called
        mock_exec.assert_not_called()


def test_message_dialog_empty_details(qtbot):
    """Test MessageDialog with empty details string"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)

    with patch.object(MessageDialog, "exec_") as mock_exec:
        with patch.object(MessageDialog, "setDetailedText") as mock_set_detailed:
            MessageDialog(
                MessageDialog.MESSAGE_TYPES.warning,
                "Test warning message",
                direct_show=True,
                parent=parent,
                details="",
            )

            # Check if setDetailedText was not called
            mock_set_detailed.assert_not_called()

            # Check if exec_ was called
            mock_exec.assert_called_once()
