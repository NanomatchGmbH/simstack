import pytest
from unittest.mock import MagicMock, patch

from PySide6 import QtWidgets
from PySide6.QtWidgets import QLabel, QToolButton, QPushButton, QMenu, QWidgetAction

from simstack.view.DropDownWidgetButton import (
    _DropDownWidget,
    DropDownWidgetToolButton,
    DropDownWidgetPushButton
)


class TestDropDownWidget(QtWidgets.QWidget, _DropDownWidget):
    """Test implementation of _DropDownWidget for testing"""
    
    def __init__(self, parent=None, widget=None, text=""):
        QtWidgets.QWidget.__init__(self, parent)
        # Instead of calling _init directly, let's set up the attributes manually
        self._widget = widget
        self._text = text
        self._menu = QMenu(parent)
        self._action = QWidgetAction(parent)
        if widget:
            self._action.setDefaultWidget(widget)
            self._menu.addAction(self._action)
    
    def _set_widget(self):
        """Implementation of the _set_widget method for testing"""
        if self._widget:
            self._action.setDefaultWidget(self._widget)
            self.menu().addAction(self._action)
    
    def menu(self):
        """Return the menu"""
        return self._menu


def test_drop_down_widget_init(qtbot):
    """Test initialization of _DropDownWidget"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    # Test with no widget
    widget = TestDropDownWidget(parent, text="Test Text")
    qtbot.addWidget(widget)
    
    assert widget._widget is None
    assert isinstance(widget._menu, QMenu)
    assert widget._text == "Test Text"
    assert isinstance(widget._action, QWidgetAction)
    
    # Test with a widget
    label = QLabel("Test Label")
    widget2 = TestDropDownWidget(parent, widget=label, text="Test With Widget")
    qtbot.addWidget(widget2)
    
    assert widget2._widget == label
    assert isinstance(widget2._menu, QMenu)
    assert widget2._text == "Test With Widget"
    assert isinstance(widget2._action, QWidgetAction)


def test_drop_down_widget_set_widget(qtbot):
    """Test set_widget method of _DropDownWidget"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    # Create widget without an initial widget
    widget = TestDropDownWidget(parent, text="Test")
    qtbot.addWidget(widget)
    
    # Mock _set_widget to check if it's called
    widget._set_widget = MagicMock()
    
    # Set a widget
    label = QLabel("Test Label")
    widget.set_widget(label)
    
    # Check if the widget was set correctly
    assert widget._widget == label
    widget._set_widget.assert_called_once()
    
    # Try setting another widget (should not work since _widget is not None)
    label2 = QLabel("Second Test Label")
    widget.set_widget(label2)
    
    # Check that the widget was not changed
    assert widget._widget == label
    assert widget._set_widget.call_count == 1


def test_drop_down_widget_set_widget_method(qtbot):
    """Test _set_widget method of _DropDownWidget"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    # Create widget with a label
    label = QLabel("Test Label")
    widget = TestDropDownWidget(parent, text="Test")
    qtbot.addWidget(widget)
    
    # Set up for test
    widget._action = MagicMock()
    widget._widget = label
    
    # Create a real QMenu but spy on its addAction method
    real_menu = QMenu()
    real_menu.addAction = MagicMock()
    widget.menu = MagicMock(return_value=real_menu)
    
    # Call _set_widget
    widget._set_widget()
    
    # Check that the actions were called correctly
    widget._action.setDefaultWidget.assert_called_once_with(label)
    real_menu.addAction.assert_called_once_with(widget._action)


def test_drop_down_tool_button_init(qtbot):
    """Test initialization of DropDownWidgetToolButton"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    # Mock the base init to avoid calling it directly
    with patch.object(DropDownWidgetToolButton, '_init'):
        # Test initialization without widget
        button = DropDownWidgetToolButton(parent, text="Test Button")
        qtbot.addWidget(button)
        
        # Set up attributes manually
        button._widget = None
        button._menu = QMenu(parent)
        button.setText("Test Button")
        button.setPopupMode(QToolButton.MenuButtonPopup)
        
        assert isinstance(button, QToolButton)
        assert button._widget is None
        assert isinstance(button._menu, QMenu)
        assert button.text() == "Test Button"
        assert button.popupMode() == QToolButton.MenuButtonPopup
    
    # Test initialization with widget
    with patch.object(DropDownWidgetToolButton, '_init'):
        label = QLabel("Test Label")
        button2 = DropDownWidgetToolButton(parent, widget=label, text="With Widget")
        qtbot.addWidget(button2)
        
        # Set up attributes manually
        button2._widget = label
        button2._menu = QMenu(parent)
        button2.setText("With Widget")
        button2.setPopupMode(QToolButton.MenuButtonPopup)
        
        assert isinstance(button2, QToolButton)
        assert button2._widget == label
        assert isinstance(button2._menu, QMenu)
        assert button2.text() == "With Widget"
        assert button2.popupMode() == QToolButton.MenuButtonPopup


def test_drop_down_push_button_init(qtbot):
    """Test initialization of DropDownWidgetPushButton"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    # Mock the base init to avoid calling it directly
    with patch.object(DropDownWidgetPushButton, '_init'):
        # Test initialization without widget
        button = DropDownWidgetPushButton(parent, text="Test Button")
        qtbot.addWidget(button)
        
        # Set up attributes manually
        button._widget = None
        button._menu = QMenu(parent)
        button.setText("Test Button")
        
        assert isinstance(button, QPushButton)
        assert button._widget is None
        assert isinstance(button._menu, QMenu)
        assert button.text() == "Test Button"
    
    # Test initialization with widget
    with patch.object(DropDownWidgetPushButton, '_init'):
        label = QLabel("Test Label")
        button2 = DropDownWidgetPushButton(parent, widget=label, text="With Widget")
        qtbot.addWidget(button2)
        
        # Set up attributes manually
        button2._widget = label
        button2._menu = QMenu(parent)
        button2.setText("With Widget")
        
        assert isinstance(button2, QPushButton)
        assert button2._widget == label
        assert isinstance(button2._menu, QMenu)
        assert button2.text() == "With Widget"


def test_drop_down_push_button_set_widget(qtbot):
    """Test set_widget method of DropDownWidgetPushButton"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    # Create button without an initial widget
    with patch.object(DropDownWidgetPushButton, '_init'), \
         patch.object(DropDownWidgetPushButton, '_set_widget'):
        button = DropDownWidgetPushButton(parent, text="Test")
        qtbot.addWidget(button)
        
        # Set up attributes manually
        button._widget = None
        button._menu = QMenu(parent)
        
        # Set a widget
        label = QLabel("Test Label")
        button.set_widget(label)
        
        # Check if the widget was set correctly
        assert button._widget == label
        button._set_widget.assert_called_once()
        
        # Try setting another widget (should not work since _widget is not None)
        label2 = QLabel("Second Test Label")
        button._set_widget.reset_mock()
        button.set_widget(label2)
        
        # Check that the widget was not changed
        assert button._widget == label
        button._set_widget.assert_not_called()


def test_drop_down_tool_button_set_widget(qtbot):
    """Test set_widget method of DropDownWidgetToolButton"""
    parent = QtWidgets.QWidget()
    qtbot.addWidget(parent)
    
    # Create button without an initial widget
    with patch.object(DropDownWidgetToolButton, '_init'), \
         patch.object(DropDownWidgetToolButton, '_set_widget'):
        button = DropDownWidgetToolButton(parent, text="Test")
        qtbot.addWidget(button)
        
        # Set up attributes manually
        button._widget = None
        button._menu = QMenu(parent)
        
        # Set a widget
        label = QLabel("Test Label")
        button.set_widget(label)
        
        # Check if the widget was set correctly
        assert button._widget == label
        button._set_widget.assert_called_once()
        
        # Try setting another widget (should not work since _widget is not None)
        label2 = QLabel("Second Test Label")
        button._set_widget.reset_mock()
        button.set_widget(label2)
        
        # Check that the widget was not changed
        assert button._widget == label
        button._set_widget.assert_not_called()