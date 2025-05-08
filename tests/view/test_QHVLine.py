from PySide6.QtWidgets import QFrame
from simstack.view.QHVLine import QHLine, QVLine


def test_qhline_creation(qtbot):
    """Test QHLine is created with correct frame properties"""
    line = QHLine()

    # Verify frame properties are set correctly
    assert line.frameShape() == QFrame.HLine
    assert line.frameShadow() == QFrame.Sunken

    # Verify it's a QFrame instance
    assert isinstance(line, QFrame)


def test_qhline_inheritance(qtbot):
    """Test QHLine inherits from QFrame"""
    line = QHLine()
    assert isinstance(line, QFrame)


def test_qvline_creation(qtbot):
    """Test QVLine is created with correct frame properties"""
    line = QVLine()

    # Verify frame properties are set correctly
    assert line.frameShape() == QFrame.VLine
    assert line.frameShadow() == QFrame.Sunken

    # Verify it's a QFrame instance
    assert isinstance(line, QFrame)


def test_qvline_inheritance(qtbot):
    """Test QVLine inherits from QFrame"""
    line = QVLine()
    assert isinstance(line, QFrame)
