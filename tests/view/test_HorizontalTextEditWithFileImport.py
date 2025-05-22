from unittest.mock import MagicMock

from PySide6 import QtCore, QtWidgets

from simstack.view.HorizontalTextEditWithFileImport import (
    HorizontalTextEditWithFileImport,
)


def test_init(qtbot):
    """Test initialization of HorizontalTextEditWithFileImport"""
    widget = HorizontalTextEditWithFileImport()
    qtbot.addWidget(widget)

    # Check if UI elements are created correctly
    assert isinstance(widget._layout, QtWidgets.QHBoxLayout)
    assert isinstance(widget._textedit, QtWidgets.QLineEdit)
    assert isinstance(widget._openfilebrowser_button, QtWidgets.QPushButton)

    # Check layout properties
    assert widget._layout.contentsMargins() == QtCore.QMargins(0, 0, 0, 0)
    assert widget.layout() == widget._layout

    # Check if the home path is set as the last opened directory
    assert widget._last_opened_dir == QtCore.QDir.homePath()


def test_properties(qtbot):
    """Test properties of HorizontalTextEditWithFileImport"""
    widget = HorizontalTextEditWithFileImport()
    qtbot.addWidget(widget)

    # Test line_edit property
    assert widget.line_edit is widget._textedit

    # Test button property
    assert widget.button is widget._openfilebrowser_button


def test_connect_signals(qtbot):
    """Test signal connections of HorizontalTextEditWithFileImport"""
    widget = HorizontalTextEditWithFileImport()
    qtbot.addWidget(widget)

    # Mock the show_file_dialog method
    widget.show_file_dialog = MagicMock()

    # Simulate a button click
    qtbot.mouseClick(widget._openfilebrowser_button, QtCore.Qt.LeftButton)

    # Check if show_file_dialog was called
    widget.show_file_dialog.assert_called_once()


def test_show_file_dialog_accepted(qtbot, monkeypatch):
    """Test show_file_dialog method when a file is selected"""
    widget = HorizontalTextEditWithFileImport()
    qtbot.addWidget(widget)

    # Mock QFileDialog.getOpenFileName to return a valid file path
    test_file_path = "/path/to/test/file.txt"
    monkeypatch.setattr(
        QtWidgets.QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (test_file_path, ""),
    )

    # Mock QDir.toNativeSeparators to return the same path
    monkeypatch.setattr(QtCore.QDir, "toNativeSeparators", lambda path: path)

    # Call the method
    widget.show_file_dialog()

    # Check if the text was set correctly
    assert widget._textedit.text() == test_file_path


def test_show_file_dialog_canceled(qtbot, monkeypatch):
    """Test show_file_dialog method when dialog is canceled"""
    widget = HorizontalTextEditWithFileImport()
    qtbot.addWidget(widget)

    # Set initial text
    initial_text = "initial_text"
    widget._textedit.setText(initial_text)

    # Mock QFileDialog.getOpenFileName to return an empty path (canceled)
    monkeypatch.setattr(
        QtWidgets.QFileDialog, "getOpenFileName", lambda *args, **kwargs: ("", "")
    )

    # Call the method
    widget.show_file_dialog()

    # Check if the text remains unchanged
    assert widget._textedit.text() == initial_text
