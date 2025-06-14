from unittest.mock import MagicMock, patch
import os
from PySide6 import QtWidgets
from PySide6.QtWidgets import QWidget

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
    _get_control_factory,
)


class TestGetControlFactory:
    """Tests for the _get_control_factory utility function."""

    def test_get_control_factory(self):
        """Test that _get_control_factory returns ControlFactory."""
        factory = _get_control_factory()
        assert factory is not None
        assert hasattr(factory, "construct")
        assert hasattr(factory, "name_to_class")


class TestWFFileName:
    """Tests for WFFileName class."""

    def test_init(self):
        """Test WFFileName initialization."""
        filename = WFFileName()
        assert filename.dirName == "."
        assert filename.name == "Untitled"
        assert filename.ext == "xml"

    def test_full_name_default(self):
        """Test fullName method with default values."""
        filename = WFFileName()
        expected = os.path.join(".", "Untitled.xml")
        assert filename.fullName() == expected

    def test_full_name_custom_values(self):
        """Test fullName method with custom values."""
        filename = WFFileName()
        filename.dirName = "/custom/path"
        filename.name = "MyWorkflow"
        filename.ext = "json"

        expected = os.path.join("/custom/path", "MyWorkflow.json")
        assert filename.fullName() == expected


class TestSubWorkflowView:
    """Tests for SubWorkflowView class."""

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"Control": "#EBFFD6", "ButtonColor": "#D4FF7F"},
    )
    def test_init(self, qtbot):
        """Test SubWorkflowView initialization."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = SubWorkflowView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        assert view.my_height == 50
        assert view.my_width == 300
        assert view.minimum_height == 50
        assert view.minimum_width == 300
        assert view.is_wano is False
        assert view.logical_parent is logical_parent

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"Control": "#EBFFD6", "ButtonColor": "#D4FF7F"},
    )
    def test_init_frame_style(self, qtbot):
        """Test that SubWorkflowView sets correct frame style."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = SubWorkflowView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        assert view.frameStyle() == QtWidgets.QFrame.Panel


class TestWorkflowView:
    """Tests for WorkflowView class."""

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"Base": "#F5FFEB", "MainEditor": "#F5FFF5"},
    )
    def test_init(self, qtbot):
        """Test WorkflowView initialization."""
        parent = QWidget()
        qtbot.addWidget(parent)

        view = WorkflowView(qt_parent=parent)
        qtbot.addWidget(view)

        assert view.autoResize is False
        assert view.myName == "AbstractWFTabsWidget"
        assert view.elementSkip == 20
        assert view.model is None
        assert view.background_drawn is True
        assert view.dont_place is False

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"Base": "#F5FFEB", "MainEditor": "#F5FFF5"},
    )
    def test_init_accepts_drops(self, qtbot):
        """Test that WorkflowView accepts drops."""
        parent = QWidget()
        qtbot.addWidget(parent)

        view = WorkflowView(qt_parent=parent)
        qtbot.addWidget(view)

        assert view.acceptDrops() is True

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"Base": "#F5FFEB", "MainEditor": "#F5FFF5"},
    )
    def test_enable_background(self, qtbot):
        """Test enable_background method."""
        parent = QWidget()
        qtbot.addWidget(parent)

        view = WorkflowView(qt_parent=parent)
        qtbot.addWidget(view)

        # Test enabling background
        view.enable_background(True)
        assert view.background_drawn is True

        # Test disabling background
        view.enable_background(False)
        assert view.background_drawn is False


class TestWFTabsWidget:
    """Tests for WFTabsWidget class - simplified tests."""

    def test_signal_definition(self):
        """Test that WFTabsWidget has the workflow_saved signal."""
        assert hasattr(WFTabsWidget, "workflow_saved")

    def test_changedFlag_default(self):
        """Test that changedFlag is set to False by default."""
        assert WFTabsWidget.changedFlag is False


class TestWFControlWithTopMiddleAndBottom:
    """Tests for WFControlWithTopMiddleAndBottom class."""

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_init(self, qtbot):
        """Test WFControlWithTopMiddleAndBottom initialization."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        control = WFControlWithTopMiddleAndBottom(
            qt_parent=parent, logical_parent=logical_parent
        )
        qtbot.addWidget(control)

        assert control.logical_parent is logical_parent
        assert control.acceptDrops() is False
        assert control.model is None
        assert control.initialized is False
        assert hasattr(control, "vbox")

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_mockline(self, qtbot):
        """Test _mockline method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        control = WFControlWithTopMiddleAndBottom(
            qt_parent=parent, logical_parent=logical_parent
        )
        qtbot.addWidget(control)

        line = control._mockline()

        assert isinstance(line, QtWidgets.QFrame)
        assert line.frameShape() == QtWidgets.QFrame.HLine
        assert line.frameShadow() == QtWidgets.QFrame.Sunken

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_set_model(self, qtbot):
        """Test set_model method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        control = WFControlWithTopMiddleAndBottom(
            qt_parent=parent, logical_parent=logical_parent
        )
        qtbot.addWidget(control)

        mock_model = MagicMock()
        control.set_model(mock_model)

        assert control.model is mock_model


# Control Flow View Tests - All use the same pattern
class TestAdvancedForEachView:
    """Tests for AdvancedForEachView class."""

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_init(self, qtbot):
        """Test AdvancedForEachView initialization."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = AdvancedForEachView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        assert view.logical_parent is logical_parent
        assert hasattr(view, "vbox")


class TestForEachView:
    """Tests for ForEachView class."""

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_init(self, qtbot):
        """Test ForEachView initialization."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = ForEachView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        assert view.logical_parent is logical_parent
        assert hasattr(view, "vbox")


class TestParallelView:
    """Tests for ParallelView class."""

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_init(self, qtbot):
        """Test ParallelView initialization."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = ParallelView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        assert view.logical_parent is logical_parent
        assert hasattr(view, "vbox")


class TestIfView:
    """Tests for IfView class."""

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_init(self, qtbot):
        """Test IfView initialization."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = IfView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        assert view.logical_parent is logical_parent
        assert hasattr(view, "vbox")


class TestVariableView:
    """Tests for VariableView class."""

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_init(self, qtbot):
        """Test VariableView initialization."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = VariableView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        assert view.logical_parent is logical_parent
        assert hasattr(view, "vbox")


class TestWhileView:
    """Tests for WhileView class."""

    @patch(
        "simstack.view.wf_editor_views.widgetColors",
        {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"},
    )
    def test_init(self, qtbot):
        """Test WhileView initialization."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()

        view = WhileView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)

        assert view.logical_parent is logical_parent
        assert hasattr(view, "vbox")


class TestControlFactoryUtilityMethods:
    """Tests for simple utility methods in the file."""

    def test_wf_filename_custom_extension(self):
        """Test WFFileName with different extensions."""
        filename = WFFileName()
        filename.ext = "yaml"
        filename.name = "test"
        filename.dirName = "/tmp"
        assert filename.fullName().endswith("test.yaml")

    def test_wf_filename_empty_dir(self):
        """Test WFFileName with empty directory."""
        filename = WFFileName()
        filename.dirName = ""
        filename.name = "workflow"
        assert filename.fullName() == "workflow.xml"


class TestControlViewsSizeHints:
    """Tests for size hint methods in control views."""

    @patch("simstack.view.wf_editor_views.widgetColors", {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"})
    def test_parallel_view_size_hint(self, qtbot):
        """Test ParallelView sizeHint method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = ParallelView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        # Test size hint calculation
        size = view.sizeHint()
        assert size.width() >= 200
        assert size.height() >= 100

    @patch("simstack.view.wf_editor_views.widgetColors", {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"})
    def test_if_view_size_hint(self, qtbot):
        """Test IfView sizeHint method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = IfView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        # Test size hint calculation
        size = view.sizeHint()
        assert size.width() >= 200
        assert size.height() >= 100

    @patch("simstack.view.wf_editor_views.widgetColors", {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"})
    def test_variable_view_size_hint(self, qtbot):
        """Test VariableView sizeHint method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = VariableView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        # Test size hint calculation
        size = view.sizeHint()
        assert size.width() >= 200
        assert size.height() >= 100


class TestControlViewProperties:
    """Tests for simple property access in control views."""

    @patch("simstack.view.wf_editor_views.widgetColors", {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"})
    def test_foreach_view_line_edited(self, qtbot):
        """Test ForEachView line_edited method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = ForEachView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        # Mock the model and widgets
        view.model = MagicMock()
        view.list_of_variables = MagicMock()
        view.list_of_variables.text.return_value = "file1.txt file2.txt"
        
        # Test line_edited method
        view.line_edited()
        view.model.set_filelist.assert_called_once_with("file1.txt file2.txt")

    @patch("simstack.view.wf_editor_views.widgetColors", {"ButtonColor": "#D4FF7F", "Control": "#EBFFD6"})
    def test_foreach_view_on_line_edit(self, qtbot):
        """Test ForEachView _on_line_edit method."""
        parent = QWidget()
        qtbot.addWidget(parent)
        logical_parent = MagicMock()
        
        view = ForEachView(qt_parent=parent, logical_parent=logical_parent)
        qtbot.addWidget(view)
        
        # Mock the model and widgets
        view.model = MagicMock()
        view.itername_widget = MagicMock()
        view.itername_widget.text.return_value = "test_iterator"
        
        # Test _on_line_edit method
        view._on_line_edit()
        assert view.model.itername == "test_iterator"
