from unittest.mock import MagicMock, patch
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QSize

from simstack.view.wf_editor_views import (
    SubWorkflowView,
    WorkflowView,
    WFTabsWidget,
    AdvancedForEachView,
    ForEachView,
    ParallelView,
    IfView,
    VariableView,
    WhileView,
)


class TestInitFromModelMethods:
    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_advanced_foreach_init_from_model(self, qtbot):
        """Test AdvancedForEachView init_from_model method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = AdvancedForEachView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model
        mock_model = MagicMock()
        mock_model.fileliststring = "test_files"
        mock_model.itername = "test_iter"
        view.model = mock_model

        # Mock widgets that would be created in get_top_widget
        view.list_of_variables = MagicMock()
        view.itername_widget = MagicMock()

        # Call parent's init_from_model first
        with patch.object(type(view).__bases__[0], "init_from_model") as mock_super:
            view.init_from_model()
            mock_super.assert_called_once()

        # Check that widgets are set
        view.list_of_variables.setText.assert_called_with("test_files")
        view.itername_widget.setText.assert_called_with("test_iter")

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_foreach_init_from_model(self, qtbot):
        """Test ForEachView init_from_model method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = ForEachView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model
        mock_model = MagicMock()
        mock_model.fileliststring = "foreach_files"
        mock_model.itername = "foreach_iter"
        view.model = mock_model

        # Mock widgets
        view.list_of_variables = MagicMock()
        view.itername_widget = MagicMock()

        # Call parent's init_from_model first
        with patch.object(type(view).__bases__[0], "init_from_model") as mock_super:
            view.init_from_model()
            mock_super.assert_called_once()

        view.list_of_variables.setText.assert_called_with("foreach_files")
        view.itername_widget.setText.assert_called_with("foreach_iter")

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_if_init_from_model(self, qtbot):
        """Test IfView init_from_model method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = IfView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model
        mock_model = MagicMock()
        mock_model._condition = "test_condition"
        mock_model.subwf_views = [MagicMock(), MagicMock()]
        view.model = mock_model

        # Mock widgets and splitter
        view.list_of_variables = MagicMock()
        view.splitter = MagicMock()

        # Call parent's init_from_model first
        with patch.object(type(view).__bases__[0], "init_from_model") as mock_super:
            view.init_from_model()
            mock_super.assert_called_once()

        # Check splitter widget addition
        assert view.splitter.addWidget.call_count == 2
        view.list_of_variables.setText.assert_called_with("test_condition")

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_while_init_from_model(self, qtbot):
        """Test WhileView init_from_model method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = WhileView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model
        mock_model = MagicMock()
        mock_model.get_condition.return_value = "while_condition"
        mock_model.get_itername.return_value = "while_iter"
        mock_model.subwf_views = [MagicMock()]
        view.model = mock_model

        # Mock widgets
        view.list_of_variables = MagicMock()
        view.itername_widget = MagicMock()
        view.splitter = MagicMock()

        # Call parent's init_from_model first
        with patch.object(type(view).__bases__[0], "init_from_model") as mock_super:
            view.init_from_model()
            mock_super.assert_called_once()

        view.splitter.addWidget.assert_called_once()
        view.list_of_variables.setText.assert_called_with("while_condition")
        view.itername_widget.setText.assert_called_with("while_iter")

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_variable_init_from_model(self, qtbot):
        """Test VariableView init_from_model method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = VariableView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model
        mock_model = MagicMock()
        mock_model.get_varname.return_value = "variable_name"
        mock_model.get_varequation.return_value = "variable_equation"
        view.model = mock_model

        # Mock widgets
        view._varname_widget = MagicMock()
        view._varequation_widget = MagicMock()

        # Call parent's init_from_model first
        with patch.object(type(view).__bases__[0], "init_from_model") as mock_super:
            view.init_from_model()
            mock_super.assert_called_once()

        view._varname_widget.setText.assert_called_with("variable_name")
        view._varequation_widget.setText.assert_called_with("variable_equation")

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_parallel_init_from_model(self, qtbot):
        """Test ParallelView init_from_model method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = ParallelView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model
        mock_model = MagicMock()
        mock_view1 = MagicMock()
        mock_view2 = MagicMock()
        mock_model.subwf_views = [mock_view1, mock_view2]
        view.model = mock_model

        # Mock splitter
        view.splitter = MagicMock()

        # Call parent's init_from_model first
        with patch.object(type(view).__bases__[0], "init_from_model") as mock_super:
            view.init_from_model()
            mock_super.assert_called_once()

        # Check that all subwf_views are added to splitter
        assert view.splitter.addWidget.call_count == 2
        view.splitter.addWidget.assert_any_call(mock_view1)
        view.splitter.addWidget.assert_any_call(mock_view2)


class TestDragEnterMethods:
    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"Base": "#F5FFEB", "MainEditor": "#F5FFF5"},
    )
    def test_workflow_drag_enter_event(self, qtbot):
        """Test WorkflowView dragEnterEvent method."""
        parent = QWidget()
        qtbot.addWidget(parent)

        view = WorkflowView(qt_parent=parent)
        qtbot.addWidget(view)

        # Mock drag enter event
        mock_event = MagicMock()
        view.dragEnterEvent(mock_event)

        # Should accept the event
        mock_event.accept.assert_called_once()

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"Control": "#EBFFD6", "ButtonColor": "#D4FF7F"},
    )
    def test_subworkflow_drag_enter_event(self, qtbot):
        """Test SubWorkflowView dragEnterEvent method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = SubWorkflowView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock drag enter event
        mock_event = MagicMock()
        view.dragEnterEvent(mock_event)

        # Should accept the event
        mock_event.accept.assert_called_once()


class TestWorkflowLocateElement:
    """Test WorkflowView _locate_element_above method."""

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"Base": "#F5FFEB", "MainEditor": "#F5FFF5"},
    )
    def test_workflow_locate_element_above_empty(self, qtbot):
        """Test WorkflowView _locate_element_above with empty model."""
        parent = QWidget()
        qtbot.addWidget(parent)

        view = WorkflowView(qt_parent=parent)
        qtbot.addWidget(view)

        # Mock model with empty elements
        mock_model = MagicMock()
        mock_model.elements = []
        view.model = mock_model

        mock_position = MagicMock()
        mock_position.y.return_value = 100

        result = view._locate_element_above(mock_position)
        assert result == 0

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"Base": "#F5FFEB", "MainEditor": "#F5FFF5"},
    )
    def test_workflow_locate_element_above_multiple(self, qtbot):
        """Test WorkflowView _locate_element_above with multiple elements."""
        parent = QWidget()
        qtbot.addWidget(parent)

        view = WorkflowView(qt_parent=parent)
        qtbot.addWidget(view)

        # Mock model with multiple elements
        mock_model = MagicMock()
        elements = []
        for i in range(3):
            element = MagicMock()
            element_view = MagicMock()
            element_view.height.return_value = 100
            element.view = element_view
            elements.append(element)

        mock_model.elements = elements
        view.model = mock_model
        view.elementSkip = 20

        # Test position in middle
        mock_position = MagicMock()
        mock_position.y.return_value = 150

        result = view._locate_element_above(mock_position)
        assert result == 2

        # Test position at end
        mock_position.y.return_value = 400
        result = view._locate_element_above(mock_position)
        assert result == 3


class TestSimpleMethodCalls:
    @patch("simstack.view.wf_editor_views.WFModel")
    @patch("simstack.view.wf_editor_views.WorkflowView")
    def test_wf_tabs_mark_changed(self, mock_workflow_view, mock_wf_model):
        """Test WFTabsWidget markWFasChanged method."""
        with patch("builtins.print") as mock_print:
            tabs = WFTabsWidget.__new__(WFTabsWidget)
            tabs.markWFasChanged = WFTabsWidget.markWFasChanged.__get__(
                tabs, WFTabsWidget
            )

            tabs.markWFasChanged()
            mock_print.assert_called_once_with("mark as changed")


class TestSizeHintEdgeCases:
    """Test sizeHint edge cases."""

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_variable_size_hint_no_model(self, qtbot):
        """Test VariableView sizeHint with no model."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = VariableView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        view.model = None

        size_hint = view.sizeHint()
        assert size_hint == QSize(200, 100)

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_variable_size_hint_with_model(self, qtbot):
        """Test VariableView sizeHint with model."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = VariableView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        mock_model = MagicMock()
        view.model = mock_model

        size_hint = view.sizeHint()
        # Should enforce minimum width of 300
        assert size_hint.width() == 300
        assert size_hint.height() == 75

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_parallel_size_hint_no_model(self, qtbot):
        """Test ParallelView sizeHint with no model."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = ParallelView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        view.model = None

        size_hint = view.sizeHint()
        assert size_hint == QSize(200, 100)

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_if_size_hint_no_model(self, qtbot):
        """Test IfView sizeHint with no model."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = IfView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        view.model = None

        size_hint = view.sizeHint()
        assert size_hint == QSize(200, 100)

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_while_size_hint_no_model(self, qtbot):
        """Test WhileView sizeHint with no model."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = WhileView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        view.model = None

        size_hint = view.sizeHint()
        assert size_hint == QSize(200, 100)

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_foreach_size_hint_small_width(self, qtbot):
        """Test ForEachView sizeHint with small width subview."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = ForEachView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model with small subwfview
        mock_model = MagicMock()
        mock_subwf = MagicMock()
        mock_subwf.sizeHint.return_value = QSize(250, 150)  # Small width
        mock_model.subwfview = mock_subwf
        view.model = mock_model

        size_hint = view.sizeHint()

        # Should enforce minimum width of 300
        assert size_hint.width() == 300
        assert size_hint.height() == 230  # 150 + 80
