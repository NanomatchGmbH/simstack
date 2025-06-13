"""Advanced tests for wf_editor_views.py targeting complex methods and remaining coverage gaps."""

from unittest.mock import MagicMock, patch, Mock, call
import pytest
import os
from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import QRect, QSize

from simstack.view.wf_editor_views import (
    SubWorkflowView,
    WorkflowView,
    WFTabsWidget,
    WFFileName,
    WFControlWithTopMiddleAndBottom,
    AdvancedForEachView,
    ForEachView,
    ParallelView,
    IfView,
    VariableView,
    WhileView,
)


class TestSubWorkflowViewAdvanced:
    """Advanced tests for SubWorkflowView covering complex methods."""
    
    @patch('simstack.view.wf_editor_views.widgetColors', {'Control': '#EBFFD6', 'ButtonColor': '#D4FF7F'})
    def test_place_elements_with_elements(self, qtbot):
        """Test place_elements method with actual elements."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = SubWorkflowView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model with elements
        mock_model = MagicMock()
        mock_element1 = MagicMock()
        mock_element2 = MagicMock()
        
        # Mock element views
        mock_view1 = MagicMock()
        mock_view1.width.return_value = 200
        mock_view1.height.return_value = 100
        mock_element1.view = mock_view1
        
        mock_view2 = MagicMock()
        mock_view2.width.return_value = 250
        mock_view2.height.return_value = 120
        mock_element2.view = mock_view2
        
        mock_model.elements = [mock_element1, mock_element2]
        view.model = mock_model
        
        # Mock geometry to provide dimensions
        view.geometry = MagicMock(return_value=QRect(0, 0, 400, 300))
        
        result = view.place_elements()
        
        # Verify calls were made
        mock_view1.setParent.assert_called_with(view)
        mock_view2.setParent.assert_called_with(view)
        mock_view1.adjustSize.assert_called()
        mock_view2.adjustSize.assert_called()
        mock_view1.move.assert_called()
        mock_view2.move.assert_called()
        mock_view1.place_elements.assert_called()
        mock_view2.place_elements.assert_called()
        
        # Check return value is an integer (ypos)
        assert isinstance(result, int)
        
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)

    @patch('simstack.view.wf_editor_views.widgetColors', {'Control': '#EBFFD6', 'ButtonColor': '#D4FF7F'})
    def test_place_elements_width_calculation(self, qtbot):
        """Test place_elements width calculation logic."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = SubWorkflowView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        view.minimum_width = 300
        
        # Mock model with wide element
        mock_model = MagicMock()
        mock_element = MagicMock()
        mock_view = MagicMock()
        mock_view.width.return_value = 400  # Wide element
        mock_view.height.return_value = 100
        mock_element.view = mock_view
        mock_model.elements = [mock_element]
        view.model = mock_model
        
        view.geometry = MagicMock(return_value=QRect(0, 0, 500, 300))
        
        view.place_elements()
        
        # Should update my_width to accommodate wide element
        assert view.my_width == 450  # 400 + 50
        
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)

    @patch('simstack.view.wf_editor_views.widgetColors', {'Control': '#EBFFD6', 'ButtonColor': '#D4FF7F'})
    def test_paint_event_with_elements(self, qtbot):
        """Test paintEvent method with elements."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = SubWorkflowView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        
        # Mock model with multiple elements
        mock_model = MagicMock()
        mock_element1 = MagicMock()
        mock_element2 = MagicMock()
        
        # Mock element views with positions
        mock_view1 = MagicMock()
        mock_view1.pos.return_value = QtCore.QPoint(100, 50)
        mock_view1.width.return_value = 200
        mock_view1.height.return_value = 100
        mock_element1.view = mock_view1
        
        mock_view2 = MagicMock()
        mock_view2.pos.return_value = QtCore.QPoint(100, 200)
        mock_view2.width.return_value = 200
        mock_view2.height.return_value = 100
        mock_element2.view = mock_view2
        
        mock_model.elements = [mock_element1, mock_element2]
        view.model = mock_model
        
        # Create a real QPaintEvent
        paint_event = QtGui.QPaintEvent(QtCore.QRect(0, 0, 400, 300))
        
        # Mock QPainter to avoid actual painting
        with patch('simstack.view.wf_editor_views.QtGui.QPainter') as mock_painter_class:
            mock_painter = MagicMock()
            mock_painter_class.return_value = mock_painter
            
            view.paintEvent(paint_event)
            
            # Verify painter was created and used
            mock_painter_class.assert_called_with(view)
            mock_painter.setBrush.assert_called()
            mock_painter.drawLine.assert_called()
            mock_painter.end.assert_called()
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)

    @patch('simstack.view.wf_editor_views.widgetColors', {'Control': '#EBFFD6', 'ButtonColor': '#D4FF7F'})
    def test_paint_event_single_element(self, qtbot):
        """Test paintEvent with single element (no lines drawn)."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = SubWorkflowView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        
        # Mock model with single element
        mock_model = MagicMock()
        mock_element = MagicMock()
        mock_view = MagicMock()
        mock_element.view = mock_view
        mock_model.elements = [mock_element]
        view.model = mock_model
        
        # Create a real QPaintEvent
        paint_event = QtGui.QPaintEvent(QtCore.QRect(0, 0, 400, 300))
        
        with patch('simstack.view.wf_editor_views.QtGui.QPainter') as mock_painter_class:
            mock_painter = MagicMock()
            mock_painter_class.return_value = mock_painter
            
            view.paintEvent(paint_event)
            
            # With single element, no lines should be drawn
            mock_painter.drawLine.assert_not_called()
        
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)

    @patch('simstack.view.wf_editor_views.widgetColors', {'Control': '#EBFFD6', 'ButtonColor': '#D4FF7F'})
    def test_locate_element_above_multiple_elements(self, qtbot):
        """Test _locate_element_above with multiple elements."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = SubWorkflowView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        
        # Mock model with multiple elements
        mock_model = MagicMock()
        mock_element1 = MagicMock()
        mock_element2 = MagicMock()
        mock_element3 = MagicMock()
        
        # Mock element views with heights
        mock_view1 = MagicMock()
        mock_view1.height.return_value = 100
        mock_element1.view = mock_view1
        
        mock_view2 = MagicMock()
        mock_view2.height.return_value = 100  
        mock_element2.view = mock_view2
        
        mock_view3 = MagicMock()
        mock_view3.height.return_value = 100
        mock_element3.view = mock_view3
        
        mock_model.elements = [mock_element1, mock_element2, mock_element3]
        view.model = mock_model
        view.elementSkip = 20
        
        # Test position in middle
        mock_position = MagicMock()
        mock_position.y.return_value = 150  # Should be after second element
        
        result = view._locate_element_above(mock_position)
        assert result == 2

        # Test position at end
        mock_position.y.return_value = 400  # Should be after all elements
        result = view._locate_element_above(mock_position)
        assert result == 3
        
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)

globalview = None
class TestWorkflowViewAdvanced:
    """Advanced tests for WorkflowView covering complex methods."""
    @patch('simstack.view.wf_editor_views.widgetColors', {'Base': '#F5FFEB', 'MainEditor': '#F5FFF5'})
    def test_place_elements_with_background_logic(self, qtbot):
        """Test place_elements background enabling/disabling logic."""
        parent = QWidget()
        qtbot.addWidget(parent)
        
        view = WorkflowView(qt_parent=parent)
        qtbot.addWidget(view)
        
        
        # Mock enable_background method
        view.enable_background = MagicMock()
        
        # Test with empty elements - should enable background
        mock_model = MagicMock()
        mock_model.elements = []
        view.model = mock_model
        
        result = view.place_elements()
        view.enable_background.assert_called_with(True)
        
        # Test with elements and background_drawn=True - should disable background
        view.enable_background.reset_mock()
        view.background_drawn = True
        mock_element = MagicMock()
        mock_view = MagicMock()
        mock_view.height.return_value = 100
        mock_element.view = mock_view
        mock_model.elements = [mock_element]
        
        # Mock parent height
        mock_parent = MagicMock()
        mock_parent.height.return_value = 600
        view.parent = MagicMock(return_value=mock_parent)
        view.geometry = MagicMock(return_value=QRect(0, 0, 400, 300))
        
        view.place_elements()
        view.enable_background.assert_called_with(False)
        
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)

    @patch('simstack.view.wf_editor_views.widgetColors', {'Base': '#F5FFEB', 'MainEditor': '#F5FFF5'})
    def test_place_elements_complex_layout(self, qtbot):
        """Test place_elements with complex element layout."""
        parent = QWidget()
        qtbot.addWidget(parent)

        global view
        view = WorkflowView(qt_parent=parent)
        qtbot.addWidget(view)
        
        # Mock model with elements
        mock_model = MagicMock()
        mock_element1 = MagicMock()
        mock_element2 = MagicMock()
        
        # Mock element views
        mock_view1 = MagicMock()
        mock_view1.width.return_value = 200
        mock_view1.height.return_value = 100
        mock_element1.view = mock_view1
        
        mock_view2 = MagicMock()
        mock_view2.width.return_value = 250
        mock_view2.height.return_value = 120
        mock_element2.view = mock_view2
        
        mock_model.elements = [mock_element1, mock_element2]
        view.model = mock_model
        
        # Mock parent and geometry
        mock_parent = MagicMock()
        mock_parent.height.return_value = 600
        view.parent = MagicMock(return_value=mock_parent)
        view.geometry = MagicMock(return_value=QRect(0, 0, 400, 300))
        view.enable_background = MagicMock()
        
        result = view.place_elements()
        
        # Verify element positioning
        mock_view1.setParent.assert_called_with(view)
        mock_view2.setParent.assert_called_with(view)
        mock_view1.move.assert_called()
        mock_view2.move.assert_called()
        
        assert isinstance(result, int)
        
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)

    @patch('simstack.view.wf_editor_views.widgetColors', {'Base': '#F5FFEB', 'MainEditor': '#F5FFF5'})
    def test_relayout_multiple_calls(self, qtbot):
        """Test relayout method calls place_elements multiple times."""
        parent = QWidget()
        qtbot.addWidget(parent)
        
        view = WorkflowView(qt_parent=parent)
        qtbot.addWidget(view)
        
        # Mock place_elements
        view.place_elements = MagicMock(return_value=200)
        
        view.relayout()
        
        # Should call place_elements 3 times
        assert view.place_elements.call_count == 3
        
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)

    @patch('simstack.view.wf_editor_views.widgetColors', {'Base': '#F5FFEB', 'MainEditor': '#F5FFF5'})
    def test_paint_event_workflow(self, qtbot):
        """Test paintEvent for WorkflowView."""
        parent = QWidget()
        qtbot.addWidget(parent)

        view = WorkflowView(qt_parent=parent)
        qtbot.addWidget(view)
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)
        # Mock model with elements
        mock_model = MagicMock()
        mock_element1 = MagicMock()
        mock_element2 = MagicMock()
        
        mock_view1 = MagicMock()
        mock_view1.pos.return_value = QtCore.QPoint(100, 50)
        mock_view1.width.return_value = 200
        mock_view1.height.return_value = 100
        mock_element1.view = mock_view1
        
        mock_view2 = MagicMock()
        mock_view2.pos.return_value = QtCore.QPoint(100, 200)
        mock_element2.view = mock_view2
        
        mock_model.elements = [mock_element1, mock_element2]
        view.model = mock_model
        
        # Create a real QPaintEvent
        paint_event = QtGui.QPaintEvent(QtCore.QRect(0, 0, 400, 300))
        
        with patch('simstack.view.wf_editor_views.QtGui.QPainter') as mock_painter_class:
            mock_painter = MagicMock()
            mock_painter_class.return_value = mock_painter
            view.paintEvent(paint_event)
            
            mock_painter.drawLine.assert_called()
            mock_painter.end.assert_called()


class TestWFTabsWidgetAdvanced:
    """Advanced tests for WFTabsWidget methods."""
    
    @patch('simstack.view.wf_editor_views.WFModel')
    @patch('simstack.view.wf_editor_views.WorkflowView')
    def test_contains_illegal_chars(self, mock_workflow_view, mock_wf_model):
        """Test _contains_illegal_chars method."""
        mock_parent = MagicMock()
        mock_parent.editor = MagicMock()
        
        # Create a minimal WFTabsWidget instance
        tabs = WFTabsWidget.__new__(WFTabsWidget)
        tabs.illegal_chars = r"<>|\\#~*´`"
        tabs._contains_illegal_chars = WFTabsWidget._contains_illegal_chars.__get__(tabs, WFTabsWidget)
        
        # Test with illegal characters
        assert tabs._contains_illegal_chars("test<file") is True
        assert tabs._contains_illegal_chars("test>file") is True
        assert tabs._contains_illegal_chars("test|file") is True
        assert tabs._contains_illegal_chars("test#file") is True
        
        # Test with legal characters
        assert tabs._contains_illegal_chars("testfile") is False
        assert tabs._contains_illegal_chars("test_file") is False
        assert tabs._contains_illegal_chars("test-file") is False

    @patch('simstack.view.wf_editor_views.WFModel')
    @patch('simstack.view.wf_editor_views.WorkflowView')
    def test_current_tab_text(self, mock_workflow_view, mock_wf_model):
        """Test currentTabText method."""
        mock_parent = MagicMock()
        mock_parent.editor = MagicMock()
        
        # Create minimal instance
        tabs = WFTabsWidget.__new__(WFTabsWidget)
        tabs.currentIndex = MagicMock(return_value=0)
        tabs.tabText = MagicMock(return_value="TestTab")
        tabs.currentTabText = WFTabsWidget.currentTabText.__get__(tabs, WFTabsWidget)
        
        result = tabs.currentTabText()
        
        tabs.currentIndex.assert_called_once()
        tabs.tabText.assert_called_once_with(0)
        assert result == "TestTab"

    @patch('simstack.view.wf_editor_views.WFModel')
    @patch('simstack.view.wf_editor_views.WorkflowView')
    def test_get_index(self, mock_workflow_view, mock_wf_model):
        """Test get_index method."""
        mock_parent = MagicMock()
        mock_parent.editor = MagicMock()
        
        # Create minimal instance
        tabs = WFTabsWidget.__new__(WFTabsWidget)
        tabs.count = MagicMock(return_value=3)
        tabs.tabText = MagicMock(side_effect=["Tab1", "Tab2", "Target"])
        tabs.get_index = WFTabsWidget.get_index.__get__(tabs, WFTabsWidget)
        
        # Test finding existing tab
        result = tabs.get_index("Target")
        assert result == 2
        
        # Test not finding tab
        tabs.tabText.side_effect = ["Tab1", "Tab2", "Tab3"]
        result = tabs.get_index("NotFound")
        assert result == -1


class TestControlViewsAdvanced:
    """Advanced tests for control flow views."""
    
    @patch('simstack.view.wf_editor_views.widgetColors', {'ButtonColor': '#D4FF7F', 'Control': '#EBFFD6'})
    def test_parallel_view_size_hint_complex(self, qtbot):
        """Test ParallelView sizeHint with multiple subviews."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = ParallelView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        # Mock model with multiple subwf_views
        mock_model = MagicMock()
        mock_view1 = MagicMock()
        mock_view1.sizeHint.return_value = QSize(200, 150)
        mock_view2 = MagicMock()
        mock_view2.sizeHint.return_value = QSize(300, 200)
        mock_view3 = MagicMock()
        mock_view3.sizeHint.return_value = QSize(250, 100)
        
        mock_model.subwf_views = [mock_view1, mock_view2, mock_view3]
        view.model = mock_model
        
        size_hint = view.sizeHint()
        
        # Total width should be sum of all widths + padding
        expected_width = 200 + 300 + 250 + 50  # 800
        expected_height = 200 + 75  # max height + padding = 275
        
        assert size_hint.width() == expected_width
        assert size_hint.height() == expected_height
        
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)

    @patch('simstack.view.wf_editor_views.widgetColors', {'ButtonColor': '#D4FF7F', 'Control': '#EBFFD6'})
    def test_parallel_view_place_elements(self, qtbot):
        """Test ParallelView place_elements method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = ParallelView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        # Mock model with subwf_views
        mock_model = MagicMock()
        mock_view1 = MagicMock()
        mock_view2 = MagicMock()
        mock_model.subwf_views = [mock_view1, mock_view2]
        view.model = mock_model
        
        # Mock init_from_model
        view.init_from_model = MagicMock()
        
        view.place_elements()
        
        # Should initialize and call place_elements on subviews
        view.init_from_model.assert_called_once()
        mock_view1.place_elements.assert_called_once()
        mock_view2.place_elements.assert_called_once()
        
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)

    @patch('simstack.view.wf_editor_views.widgetColors', {'ButtonColor': '#D4FF7F', 'Control': '#EBFFD6'})
    def test_if_view_size_hint_with_views(self, qtbot):
        """Test IfView sizeHint with subwf_views."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = IfView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        # Mock model with subwf_views
        mock_model = MagicMock()
        mock_view1 = MagicMock()
        mock_view1.sizeHint.return_value = QSize(250, 180)
        mock_view2 = MagicMock()
        mock_view2.sizeHint.return_value = QSize(220, 160)
        
        mock_model.subwf_views = [mock_view1, mock_view2]
        view.model = mock_model
        
        size_hint = view.sizeHint()
        
        # Width should be sum, height should be max
        expected_width = 250 + 220 + 50  # 520
        expected_height = 180 + 75  # 255
        
        assert size_hint.width() == expected_width
        assert size_hint.height() == expected_height

    @patch('simstack.view.wf_editor_views.widgetColors', {'ButtonColor': '#D4FF7F', 'Control': '#EBFFD6'})
    def test_if_view_place_elements(self, qtbot):
        """Test IfView place_elements method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = IfView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        # Mock model
        mock_model = MagicMock()
        mock_view1 = MagicMock()
        mock_view2 = MagicMock()
        mock_model.subwf_views = [mock_view1, mock_view2]
        view.model = mock_model
        
        # Mock init_from_model
        view.init_from_model = MagicMock()
        
        view.place_elements()
        
        view.init_from_model.assert_called_once()
        mock_view1.place_elements.assert_called_once()
        mock_view2.place_elements.assert_called_once()
        
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)

    @patch('simstack.view.wf_editor_views.widgetColors', {'ButtonColor': '#D4FF7F', 'Control': '#EBFFD6'})
    def test_while_view_size_hint_complex(self, qtbot):
        """Test WhileView sizeHint calculation."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = WhileView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        # Mock model with subwf_views
        mock_model = MagicMock()
        mock_view1 = MagicMock()
        mock_view1.sizeHint.return_value = QSize(180, 120)
        mock_model.subwf_views = [mock_view1]
        view.model = mock_model
        
        size_hint = view.sizeHint()
        
        expected_width = 300  # minimum enforced
        expected_height = 120 + 75  # 195
        
        assert size_hint.width() == expected_width
        assert size_hint.height() == expected_height
        
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)

    @patch('simstack.view.wf_editor_views.widgetColors', {'ButtonColor': '#D4FF7F', 'Control': '#EBFFD6'})
    def test_while_view_place_elements(self, qtbot):
        """Test WhileView place_elements method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = WhileView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        # Mock model
        mock_model = MagicMock()
        mock_view1 = MagicMock()
        mock_model.subwf_views = [mock_view1]
        view.model = mock_model
        
        view.init_from_model = MagicMock()
        
        view.place_elements()
        
        view.init_from_model.assert_called_once()
        mock_view1.place_elements.assert_called_once()
        
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)

    @patch('simstack.view.wf_editor_views.widgetColors', {'ButtonColor': '#D4FF7F', 'Control': '#EBFFD6'})
    def test_variable_view_place_elements(self, qtbot):
        """Test VariableView place_elements method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = VariableView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        # Mock model
        mock_model = MagicMock()
        view.model = mock_model
        
        view.init_from_model = MagicMock()
        
        view.place_elements()
        
        view.init_from_model.assert_called_once()
        
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)

    @patch('simstack.view.wf_editor_views.widgetColors', {'ButtonColor': '#D4FF7F', 'Control': '#EBFFD6'})
    def test_foreach_view_place_elements(self, qtbot):
        """Test ForEachView place_elements method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = ForEachView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        
        # Mock model
        mock_model = MagicMock()
        mock_subwf_view = MagicMock()
        mock_subwf_view.sizeHint.return_value = QSize(400, 200)
        mock_model.subwfview = mock_subwf_view
        view.model = mock_model
        
        view.init_from_model = MagicMock()
        
        view.place_elements()
        
        view.init_from_model.assert_called_once()
        mock_subwf_view.place_elements.assert_called_once()
        
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)

    @patch('simstack.view.wf_editor_views.widgetColors', {'ButtonColor': '#D4FF7F', 'Control': '#EBFFD6'})
    def test_advanced_foreach_view_place_elements(self, qtbot):
        """Test AdvancedForEachView place_elements method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = AdvancedForEachView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        
        # Mock model
        mock_model = MagicMock()
        mock_subwf_view = MagicMock()
        mock_subwf_view.sizeHint.return_value = QSize(400, 200)
        mock_model.subwfview = mock_subwf_view
        view.model = mock_model
        
        view.init_from_model = MagicMock()
        
        view.place_elements()
        
        view.init_from_model.assert_called_once()
        mock_subwf_view.place_elements.assert_called_once()
        
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)


class TestWidgetCreationMethods:
    """Test widget creation and layout methods."""
    
    @patch('simstack.view.wf_editor_views.widgetColors', {'ButtonColor': '#D4FF7F', 'Control': '#EBFFD6'})
    def test_advanced_foreach_get_middle_widget(self, qtbot):
        """Test AdvancedForEachView get_middle_widget method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = AdvancedForEachView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        # Mock model
        mock_model = MagicMock()
        mock_subwf_view = MagicMock()
        mock_model.subwfview = mock_subwf_view
        view.model = mock_model
        
        result = view.get_middle_widget()
        assert result is mock_subwf_view
        
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)

    @patch('simstack.view.wf_editor_views.widgetColors', {'ButtonColor': '#D4FF7F', 'Control': '#EBFFD6'})
    def test_advanced_foreach_get_bottom_layout(self, qtbot):
        """Test AdvancedForEachView get_bottom_layout method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = AdvancedForEachView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        result = view.get_bottom_layout()
        assert result is None
        
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)

    @patch('simstack.view.wf_editor_views.widgetColors', {'ButtonColor': '#D4FF7F', 'Control': '#EBFFD6'})
    def test_foreach_get_middle_widget(self, qtbot):
        """Test ForEachView get_middle_widget method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = ForEachView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        # Mock model
        mock_model = MagicMock()
        mock_subwf_view = MagicMock()
        mock_model.subwfview = mock_subwf_view
        view.model = mock_model
        
        result = view.get_middle_widget()
        assert result is mock_subwf_view
        
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)

    @patch('simstack.view.wf_editor_views.widgetColors', {'ButtonColor': '#D4FF7F', 'Control': '#EBFFD6'})
    def test_foreach_get_bottom_layout(self, qtbot):
        """Test ForEachView get_bottom_layout method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = ForEachView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        result = view.get_bottom_layout()
        assert result is None
        
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)

    @patch('simstack.view.wf_editor_views.widgetColors', {'ButtonColor': '#D4FF7F', 'Control': '#EBFFD6'})
    def test_parallel_get_middle_widget(self, qtbot):
        """Test ParallelView get_middle_widget method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = ParallelView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        result = view.get_middle_widget()
        assert result is view.splitter
        
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)

    @patch('simstack.view.wf_editor_views.widgetColors', {'ButtonColor': '#D4FF7F', 'Control': '#EBFFD6'})
    def test_parallel_get_bottom_layout(self, qtbot):
        """Test ParallelView get_bottom_layout method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = ParallelView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        result = view.get_bottom_layout()
        assert result is None
        
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)

    @patch('simstack.view.wf_editor_views.widgetColors', {'ButtonColor': '#D4FF7F', 'Control': '#EBFFD6'})
    def test_if_get_middle_widget(self, qtbot):
        """Test IfView get_middle_widget method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = IfView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        result = view.get_middle_widget()
        assert result is view.splitter
        
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)

    @patch('simstack.view.wf_editor_views.widgetColors', {'ButtonColor': '#D4FF7F', 'Control': '#EBFFD6'})
    def test_if_get_bottom_layout(self, qtbot):
        """Test IfView get_bottom_layout method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = IfView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        result = view.get_bottom_layout()
        assert result is None
        
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)

    @patch('simstack.view.wf_editor_views.widgetColors', {'ButtonColor': '#D4FF7F', 'Control': '#EBFFD6'})
    def test_while_get_middle_widget(self, qtbot):
        """Test WhileView get_middle_widget method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = WhileView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        result = view.get_middle_widget()
        assert result is view.splitter
        
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)

    @patch('simstack.view.wf_editor_views.widgetColors', {'ButtonColor': '#D4FF7F', 'Control': '#EBFFD6'})
    def test_while_get_bottom_layout(self, qtbot):
        """Test WhileView get_bottom_layout method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = WhileView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        result = view.get_bottom_layout()
        assert result is None
        
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)

    @patch('simstack.view.wf_editor_views.widgetColors', {'ButtonColor': '#D4FF7F', 'Control': '#EBFFD6'})
    def test_variable_get_middle_widget(self, qtbot):
        """Test VariableView get_middle_widget method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = VariableView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        result = view.get_middle_widget()
        assert result is view._middle_widget
        
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)

    @patch('simstack.view.wf_editor_views.widgetColors', {'ButtonColor': '#D4FF7F', 'Control': '#EBFFD6'})
    def test_variable_get_bottom_layout(self, qtbot):
        """Test VariableView get_bottom_layout method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = VariableView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        result = view.get_bottom_layout()
        assert result is None
        
        qtbot._widgets_to_keep = getattr(qtbot, '_widgets_to_keep', [])
        qtbot._widgets_to_keep.append(view)
        qtbot._widgets_to_keep.append(parent)