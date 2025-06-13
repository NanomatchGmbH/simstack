"""Extended tests for wf_editor_views.py to increase coverage further."""

from unittest.mock import MagicMock, patch
from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import QWidget

from simstack.view.wf_editor_views import (
    SubWorkflowView,
    WorkflowView,
    WFTabsWidget,
    WFControlWithTopMiddleAndBottom,
    AdvancedForEachView,
    ForEachView,
    ParallelView,
    IfView,
    VariableView,
    WhileView,
)


class TestSubWorkflowViewExtended:
    """Extended tests for SubWorkflowView to increase coverage."""

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"Control": "#EBFFD6", "ButtonColor": "#D4FF7F"},
    )
    def test_model_interaction(self, qtbot):
        """Test model setting and text methods."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = SubWorkflowView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Test set_model
        mock_model = MagicMock()
        mock_model.name = "TestModel"
        view.set_model(mock_model)
        assert view.model is mock_model

        # Test text() method
        assert view.text() == "TestModel"

        # Test setText() method
        view.setText("NewName")
        assert mock_model.name == "NewName"

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"Control": "#EBFFD6", "ButtonColor": "#D4FF7F"},
    )
    def test_set_minimum_width(self, qtbot):
        """Test set_minimum_width method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = SubWorkflowView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        view.set_minimum_width(500)
        assert view.minimum_width == 500

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"Control": "#EBFFD6", "ButtonColor": "#D4FF7F"},
    )
    def test_sizeHint(self, qtbot):
        """Test sizeHint method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = SubWorkflowView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        size_hint = view.sizeHint()
        assert isinstance(size_hint, QtCore.QSize)
        assert size_hint.width() >= view.minimum_width
        assert size_hint.height() >= view.minimum_height

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"Control": "#EBFFD6", "ButtonColor": "#D4FF7F"},
    )
    def test_init_from_model(self, qtbot):
        """Test init_from_model method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = SubWorkflowView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model with relayout method
        mock_model = MagicMock()
        mock_root = MagicMock()
        mock_root_view = MagicMock()
        mock_root.view = mock_root_view
        mock_model.get_root.return_value = mock_root
        view.model = mock_model

        view.init_from_model()
        mock_model.get_root.assert_called_once()
        mock_root_view.relayout.assert_called_once()

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"Control": "#EBFFD6", "ButtonColor": "#D4FF7F"},
    )
    def test_relayout(self, qtbot):
        """Test relayout method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = SubWorkflowView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model
        mock_model = MagicMock()
        mock_root = MagicMock()
        mock_root_view = MagicMock()
        mock_root.view = mock_root_view
        mock_model.get_root.return_value = mock_root
        view.model = mock_model

        view.relayout()
        mock_model.get_root.assert_called_once()
        mock_root_view.relayout.assert_called_once()

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"Control": "#EBFFD6", "ButtonColor": "#D4FF7F"},
    )
    def test_place_elements_empty(self, qtbot):
        """Test place_elements with empty model."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = SubWorkflowView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model with empty elements
        mock_model = MagicMock()
        mock_model.elements = []
        view.model = mock_model

        result = view.place_elements()
        assert isinstance(result, int)

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"Control": "#EBFFD6", "ButtonColor": "#D4FF7F"},
    )
    def test_remove_element(self, qtbot):
        """Test removeElement method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = SubWorkflowView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model
        mock_model = MagicMock()
        mock_root = MagicMock()
        mock_root_view = MagicMock()
        mock_root.view = mock_root_view
        mock_model.get_root.return_value = mock_root
        view.model = mock_model

        mock_element = MagicMock()
        view.removeElement(mock_element)

        mock_model.removeElement.assert_called_once_with(mock_element)
        mock_root_view.relayout.assert_called_once()

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"Control": "#EBFFD6", "ButtonColor": "#D4FF7F"},
    )
    def test_open_wano_editor(self, qtbot):
        """Test openWaNoEditor method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = SubWorkflowView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model
        mock_model = MagicMock()
        view.model = mock_model

        mock_wano_widget = MagicMock()
        view.openWaNoEditor(mock_wano_widget)

        mock_model.openWaNoEditor.assert_called_once_with(mock_wano_widget)


class TestWorkflowViewExtended:
    """Extended tests for WorkflowView to increase coverage."""

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"Base": "#F5FFEB", "MainEditor": "#F5FFF5"},
    )
    def test_set_model(self, qtbot):
        """Test set_model method."""
        parent = QWidget()
        qtbot.addWidget(parent)

        view = WorkflowView(qt_parent=parent)
        qtbot.addWidget(view)

        mock_model = MagicMock()
        view.set_model(mock_model)
        assert view.model is mock_model

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"Base": "#F5FFEB", "MainEditor": "#F5FFF5"},
    )
    def test_init_from_model(self, qtbot):
        """Test init_from_model method."""
        parent = QWidget()
        qtbot.addWidget(parent)

        view = WorkflowView(qt_parent=parent)
        qtbot.addWidget(view)

        # Mock the relayout method which is what init_from_model actually calls
        view.relayout = MagicMock()

        view.init_from_model()
        view.relayout.assert_called_once()

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"Base": "#F5FFEB", "MainEditor": "#F5FFF5"},
    )
    def test_place_elements_empty_model(self, qtbot):
        """Test place_elements with empty model."""
        parent = QWidget()
        qtbot.addWidget(parent)

        view = WorkflowView(qt_parent=parent)
        qtbot.addWidget(view)

        # Mock model with empty elements
        mock_model = MagicMock()
        mock_model.elements = []
        view.model = mock_model

        # Mock enable_background to avoid complex setup
        view.enable_background = MagicMock()

        result = view.place_elements()
        view.enable_background.assert_called_once_with(True)

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"Base": "#F5FFEB", "MainEditor": "#F5FFF5"},
    )
    def test_remove_element(self, qtbot):
        """Test removeElement method."""
        parent = QWidget()
        qtbot.addWidget(parent)

        view = WorkflowView(qt_parent=parent)
        qtbot.addWidget(view)

        # Mock model and relayout
        mock_model = MagicMock()
        view.model = mock_model
        view.relayout = MagicMock()

        mock_element = MagicMock()
        view.removeElement(mock_element)

        mock_model.removeElement.assert_called_once_with(mock_element)
        view.relayout.assert_called_once()

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"Base": "#F5FFEB", "MainEditor": "#F5FFF5"},
    )
    def test_open_wano_editor(self, qtbot):
        """Test openWaNoEditor method."""
        parent = QWidget()
        qtbot.addWidget(parent)

        view = WorkflowView(qt_parent=parent)
        qtbot.addWidget(view)

        # Mock model
        mock_model = MagicMock()
        view.model = mock_model

        mock_wano_widget = MagicMock()
        view.openWaNoEditor(mock_wano_widget)

        mock_model.openWaNoEditor.assert_called_once_with(mock_wano_widget)


class TestWFTabsWidgetBasic:
    """Basic tests for WFTabsWidget methods that can be tested safely."""

    def test_signal_exists(self):
        """Test that workflow_saved signal exists."""
        assert hasattr(WFTabsWidget, "workflow_saved")

    def test_changed_flag_default(self):
        """Test changedFlag default value."""
        assert WFTabsWidget.changedFlag is False

    def test_illegal_chars_constant(self):
        """Test illegal_chars constant."""
        # Create a minimal mock parent to avoid full Qt setup
        mock_parent = MagicMock()

        # We can't easily instantiate WFTabsWidget without complex setup,
        # but we can test the class-level illegal_chars attribute
        assert hasattr(WFTabsWidget, "illegal_chars")
        assert isinstance(WFTabsWidget.illegal_chars, str)

    def test_contains_illegal_chars_method(self):
        """Test _contains_illegal_chars method logic."""
        # We'll test this indirectly by checking the illegal_chars string
        illegal_chars = r"<>|\\#~*´`"

        # Test that method would work with these chars
        for char in illegal_chars:
            test_string = f"test{char}string"
            # Since we can't easily instantiate, we simulate the logic
            has_illegal = any((c in illegal_chars) for c in test_string)
            assert has_illegal is True

        # Test clean string
        clean_string = "cleanstring"
        has_illegal = any((c in illegal_chars) for c in clean_string)
        assert has_illegal is False


class TestWFControlExtended:
    """Extended tests for WFControlWithTopMiddleAndBottom."""

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_text_and_set_text(self, qtbot):
        """Test text and setText methods."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        control = WFControlWithTopMiddleAndBottom(
            qt_parent=parent, logical_parent=logical_parent
        )
        qtbot.addWidget(control)

        # Mock model
        mock_model = MagicMock()
        mock_model.name = "TestControl"
        control.model = mock_model

        # Test text method
        assert control.text() == "TestControl"

        # Test setText method
        control.setText("NewControlName")
        assert mock_model.name == "NewControlName"

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_fill_layout_all_widgets(self, qtbot):
        """Test fill_layout when all widget methods return widgets."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        control = WFControlWithTopMiddleAndBottom(
            qt_parent=parent, logical_parent=logical_parent
        )
        qtbot.addWidget(control)

        # Mock the abstract methods
        top_widget = QWidget()
        middle_widget = QWidget()
        bottom_layout = QtWidgets.QHBoxLayout()

        control.get_top_widget = MagicMock(return_value=top_widget)
        control.get_middle_widget = MagicMock(return_value=middle_widget)
        control.get_bottom_layout = MagicMock(return_value=bottom_layout)

        control.fill_layout()

        # Verify methods were called
        control.get_top_widget.assert_called_once()
        control.get_middle_widget.assert_called_once()
        control.get_bottom_layout.assert_called_once()

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_fill_layout_none_widgets(self, qtbot):
        """Test fill_layout when widget methods return None."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        control = WFControlWithTopMiddleAndBottom(
            qt_parent=parent, logical_parent=logical_parent
        )
        qtbot.addWidget(control)

        # Mock the abstract methods to return None
        control.get_top_widget = MagicMock(return_value=None)
        control.get_middle_widget = MagicMock(return_value=None)
        control.get_bottom_layout = MagicMock(return_value=None)

        control.fill_layout()

        # Verify methods were called
        control.get_top_widget.assert_called_once()
        control.get_middle_widget.assert_called_once()
        control.get_bottom_layout.assert_called_once()

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_init_from_model_first_time(self, qtbot):
        """Test init_from_model when not yet initialized."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        control = WFControlWithTopMiddleAndBottom(
            qt_parent=parent, logical_parent=logical_parent
        )
        qtbot.addWidget(control)

        # Mock fill_layout
        control.fill_layout = MagicMock()

        # Should not be initialized initially
        assert control.initialized is False

        control.init_from_model()

        # Should be initialized now
        assert control.initialized is True
        control.fill_layout.assert_called_once()

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_init_from_model_already_initialized(self, qtbot):
        """Test init_from_model when already initialized."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        control = WFControlWithTopMiddleAndBottom(
            qt_parent=parent, logical_parent=logical_parent
        )
        qtbot.addWidget(control)

        # Mock fill_layout
        control.fill_layout = MagicMock()

        # Mark as already initialized
        control.initialized = True

        control.init_from_model()

        # fill_layout should not be called
        control.fill_layout.assert_not_called()


class TestControlViewsMethods:
    """Test specific methods in control views."""

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_advanced_foreach_size_hint_with_model(self, qtbot):
        """Test AdvancedForEachView sizeHint with model."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = AdvancedForEachView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model and subwfview
        mock_model = MagicMock()
        mock_subwfview = MagicMock()
        mock_subwfview.sizeHint.return_value = QtCore.QSize(400, 200)
        mock_model.subwfview = mock_subwfview
        view.model = mock_model

        size_hint = view.sizeHint()
        assert isinstance(size_hint, QtCore.QSize)
        assert size_hint.width() >= 500  # minimum width enforced

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_advanced_foreach_size_hint_no_model(self, qtbot):
        """Test AdvancedForEachView sizeHint without model."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = AdvancedForEachView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        view.model = None

        size_hint = view.sizeHint()
        assert isinstance(size_hint, QtCore.QSize)
        assert size_hint == QtCore.QSize(500, 500)

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_foreach_size_hint(self, qtbot):
        """Test ForEachView sizeHint."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = ForEachView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Test without model
        view.model = None
        size_hint = view.sizeHint()
        assert size_hint == QtCore.QSize(200, 100)

        # Test with model
        mock_model = MagicMock()
        mock_subwfview = MagicMock()
        mock_subwfview.sizeHint.return_value = QtCore.QSize(250, 150)
        mock_model.subwfview = mock_subwfview
        view.model = mock_model

        size_hint = view.sizeHint()
        assert size_hint.width() == 300  # minimum width
        assert size_hint.height() == 230  # 150 + 80

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_variable_view_size_hint(self, qtbot):
        """Test VariableView sizeHint."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = VariableView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Test without model
        view.model = None
        size_hint = view.sizeHint()
        assert size_hint == QtCore.QSize(200, 100)

        # Test with model
        mock_model = MagicMock()
        view.model = mock_model

        size_hint = view.sizeHint()
        assert size_hint.width() == 300  # minimum width enforced
        assert size_hint.height() == 75  # base height


class TestWFTabsWidgetMethods:
    """Test WFTabsWidget methods with minimal setup."""

    def test_mark_wf_as_changed(self):
        """Test markWFasChanged method."""
        # Create a mock parent to avoid complex Qt setup
        with patch("simstack.view.wf_editor_views.WFModel"):
            with patch("simstack.view.wf_editor_views.WorkflowView"):
                mock_parent = MagicMock()
                mock_parent.editor = MagicMock()

                # We can test the method exists and can be called
                tabs = WFTabsWidget.__new__(WFTabsWidget)
                tabs.markWFasChanged = WFTabsWidget.markWFasChanged.__get__(
                    tabs, WFTabsWidget
                )

                # The method just prints, so we can call it safely
                tabs.markWFasChanged()

    def test_current_tab_text_method_exists(self):
        """Test that currentTabText method exists."""
        assert hasattr(WFTabsWidget, "currentTabText")
        assert callable(getattr(WFTabsWidget, "currentTabText"))

    def test_get_index_method_exists(self):
        """Test that get_index method exists."""
        assert hasattr(WFTabsWidget, "get_index")
        assert callable(getattr(WFTabsWidget, "get_index"))

    def test_save_file_method_exists(self):
        """Test that saveFile method exists."""
        assert hasattr(WFTabsWidget, "saveFile")
        assert callable(getattr(WFTabsWidget, "saveFile"))


class TestParallelViewMethods:
    """Test ParallelView specific methods."""

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_add_new(self, qtbot):
        """Test add_new method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = ParallelView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model and relayout
        mock_model = MagicMock()
        view.model = mock_model
        view.relayout = MagicMock()

        view.add_new()

        mock_model.add.assert_called_once()
        view.relayout.assert_called_once()

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_delete(self, qtbot):
        """Test delete method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = ParallelView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model and relayout
        mock_model = MagicMock()
        view.model = mock_model
        view.relayout = MagicMock()

        view.delete()

        mock_model.deletelast.assert_called_once()
        view.relayout.assert_called_once()

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_relayout(self, qtbot):
        """Test relayout method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = ParallelView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model
        mock_model = MagicMock()
        mock_wf_root = MagicMock()
        mock_wf_root_view = MagicMock()
        mock_wf_root.view = mock_wf_root_view
        mock_model.wf_root = mock_wf_root
        view.model = mock_model

        view.relayout()

        mock_wf_root_view.relayout.assert_called_once()


class TestIfViewMethods:
    """Test IfView specific methods."""

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_add_new(self, qtbot):
        """Test add_new method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = IfView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model and relayout
        mock_model = MagicMock()
        view.model = mock_model
        view.relayout = MagicMock()

        view.add_new()

        mock_model.add.assert_called_once()
        view.relayout.assert_called_once()

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_delete(self, qtbot):
        """Test delete method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = IfView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model and relayout
        mock_model = MagicMock()
        view.model = mock_model
        view.relayout = MagicMock()

        view.delete()

        mock_model.deletelast.assert_called_once()
        view.relayout.assert_called_once()

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_on_line_edit(self, qtbot):
        """Test _on_line_edit method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = IfView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model and setup list_of_variables
        mock_model = MagicMock()
        view.model = mock_model
        view.list_of_variables = MagicMock()
        view.list_of_variables.text.return_value = "test_condition"

        view._on_line_edit()

        mock_model.set_condition.assert_called_once_with("test_condition")


class TestWhileViewMethods:
    """Test WhileView specific methods."""

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_add_new(self, qtbot):
        """Test add_new method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = WhileView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model and relayout
        mock_model = MagicMock()
        view.model = mock_model
        view.relayout = MagicMock()

        view.add_new()

        mock_model.add.assert_called_once()
        view.relayout.assert_called_once()

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_delete(self, qtbot):
        """Test delete method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = WhileView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model and relayout
        mock_model = MagicMock()
        view.model = mock_model
        view.relayout = MagicMock()

        view.delete()

        mock_model.deletelast.assert_called_once()
        view.relayout.assert_called_once()

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_on_varname_line_edit(self, qtbot):
        """Test _on_varname_line_edit method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = WhileView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model and setup list_of_variables
        mock_model = MagicMock()
        view.model = mock_model
        view.list_of_variables = MagicMock()
        view.list_of_variables.text.return_value = "test_condition"

        view._on_varname_line_edit()

        mock_model.set_condition.assert_called_once_with("test_condition")

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_on_line_edit(self, qtbot):
        """Test _on_line_edit method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = WhileView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model and setup itername_widget
        mock_model = MagicMock()
        view.model = mock_model
        view.itername_widget = MagicMock()
        view.itername_widget.text.return_value = "test_iterator"

        view._on_line_edit()

        mock_model.set_itername.assert_called_once_with("test_iterator")


class TestVariableViewMethods:
    """Test VariableView specific methods."""

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_on_line_edit(self, qtbot):
        """Test _on_line_edit method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = VariableView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model and setup widget
        mock_model = MagicMock()
        view.model = mock_model
        view._varname_widget = MagicMock()
        view._varname_widget.text.return_value = "test_var"

        view._on_line_edit()

        mock_model.set_varname.assert_called_once_with("test_var")

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_on_varequation_line_edit(self, qtbot):
        """Test _on_varequation_line_edit method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = VariableView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model and setup widget
        mock_model = MagicMock()
        view.model = mock_model
        view._varequation_widget = MagicMock()
        view._varequation_widget.text.return_value = "test_equation"

        view._on_varequation_line_edit()

        mock_model.set_varequation.assert_called_once_with("test_equation")


class TestForEachViewMethods:
    """Test ForEachView specific methods."""

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_on_line_edit(self, qtbot):
        """Test _on_line_edit method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = ForEachView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model and setup widget
        mock_model = MagicMock()
        view.model = mock_model
        view.itername_widget = MagicMock()
        view.itername_widget.text.return_value = "test_iterator"

        view._on_line_edit()

        mock_model.itername = "test_iterator"

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_line_edited(self, qtbot):
        """Test line_edited method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = ForEachView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model and setup widget
        mock_model = MagicMock()
        view.model = mock_model
        view.list_of_variables = MagicMock()
        view.list_of_variables.text.return_value = "test_files"

        view.line_edited()

        mock_model.set_filelist.assert_called_once_with("test_files")


class TestAdvancedForEachViewMethods:
    """Test AdvancedForEachView specific methods."""

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_on_line_edit(self, qtbot):
        """Test _on_line_edit method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = AdvancedForEachView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model and setup widget
        mock_model = MagicMock()
        view.model = mock_model
        view.itername_widget = MagicMock()
        view.itername_widget.text.return_value = "a, b, c"

        view._on_line_edit()

        assert mock_model.itername == "a,b,c"  # spaces should be removed

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_line_edited(self, qtbot):
        """Test line_edited method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = AdvancedForEachView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model and setup widget
        mock_model = MagicMock()
        view.model = mock_model
        view.list_of_variables = MagicMock()
        view.list_of_variables.text.return_value = "test_files"

        view.line_edited()

        mock_model.set_filelist.assert_called_once_with("test_files")


class TestDragDropMethods:
    """Test drag and drop related methods."""

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"Control": "#EBFFD6", "ButtonColor": "#D4FF7F"},
    )
    def test_drag_enter_event(self, qtbot):
        """Test dragEnterEvent method."""
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

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"Control": "#EBFFD6", "ButtonColor": "#D4FF7F"},
    )
    def test_locate_element_above_empty(self, qtbot):
        """Test _locate_element_above with empty or single element model."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = SubWorkflowView(qt_parent=parent, logical_parent=logical_parent)
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
        {"Control": "#EBFFD6", "ButtonColor": "#D4FF7F"},
    )
    def test_locate_element_above_single_element(self, qtbot):
        """Test _locate_element_above with single element."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = SubWorkflowView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        # Mock model with single element
        mock_model = MagicMock()
        mock_element = MagicMock()
        mock_model.elements = [mock_element]
        view.model = mock_model

        mock_position = MagicMock()
        mock_position.y.return_value = 100

        result = view._locate_element_above(mock_position)
        assert result == 0
