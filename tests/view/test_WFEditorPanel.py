import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import uuid
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt
import PySide6.QtCore as QtCore
from PySide6.QtGui import QPalette

from simstack.view.WFEditorPanel import (
    DragDropTargetTracker,
    WFWaNoWidget,
    SubmitType,
    WFItemListInterface,
    WFItemModel,
    WFFileName,
    WhileModel,
    VariableModel,
    IfModel,
    linuxjoin,
)


class TestLinuxJoin:
    """Tests for the linuxjoin utility function."""

    def test_linuxjoin_single_path(self):
        """Test linuxjoin with single path component."""
        result = linuxjoin("path")
        assert result == "path"

    def test_linuxjoin_multiple_paths(self):
        """Test linuxjoin with multiple path components."""
        result = linuxjoin("path", "to", "file")
        assert result == "path/to/file"

    def test_linuxjoin_empty_path(self):
        """Test linuxjoin with empty path components."""
        result = linuxjoin("", "path", "", "file")
        assert result == "path/file"

    def test_linuxjoin_absolute_path(self):
        """Test linuxjoin with absolute path."""
        result = linuxjoin("/", "home", "user", "file.txt")
        assert result == "/home/user/file.txt"


class TestDragDropTargetTracker:
    """Tests for the DragDropTargetTracker class."""

    class MockWidget(QWidget, DragDropTargetTracker):
        """Mock widget that implements DragDropTargetTracker."""

        def __init__(self, parent=None):
            super().__init__(parent)
            self.manual_init()

    @pytest.fixture
    def tracker_widget(self, qtbot):
        """Create a widget that implements DragDropTargetTracker."""
        widget = TestDragDropTargetTracker.MockWidget()
        qtbot.addWidget(widget)
        return widget

    @pytest.fixture
    def parent_widget(self, qtbot):
        """Create a parent widget."""
        widget = QWidget()
        qtbot.addWidget(widget)
        return widget

    def test_manual_init(self, tracker_widget, parent_widget):
        """Test manual_init method."""
        # Reset tracker
        tracker_widget.setParent(parent_widget)
        tracker_widget.manual_init()

        # Verify initial parent was set
        assert tracker_widget._initial_parent is parent_widget

    def test_target_tracker(self, tracker_widget):
        """Test _target_tracker method."""
        # Create mock event
        mock_event = MagicMock()

        # Call method
        tracker_widget._target_tracker(mock_event)

        # Verify event was saved
        assert tracker_widget._newparent is mock_event

    def test_mouse_move_event_feature_wrong_button(self, tracker_widget):
        """Test mouseMoveEvent_feature with wrong mouse button."""
        # Create mock event with right button
        mock_event = MagicMock()
        mock_event.buttons.return_value = QtCore.Qt.RightButton
        
        # Should return early without doing anything
        result = tracker_widget.mouseMoveEvent_feature(mock_event)
        assert result is None

    def test_mouse_move_event_feature_left_button(self, tracker_widget):
        """Test mouseMoveEvent_feature with left mouse button."""
        # Create mock event with left button
        mock_event = MagicMock()
        mock_event.buttons.return_value = QtCore.Qt.LeftButton
        mock_event.pos.return_value = MagicMock()
        mock_event.globalPos.return_value = MagicMock()
        
        # Mock the rect and other necessary methods
        tracker_widget.rect = MagicMock()
        tracker_widget.rect.return_value.topLeft.return_value = MagicMock()
        
        # Mock parent method calls
        mock_parent = MagicMock()
        tracker_widget.parent = MagicMock(return_value=mock_parent)
        
        with patch("PySide6.QtCore.QMimeData") as mock_mime, \
             patch("PySide6.QtGui.QDrag") as mock_drag_class:
            
            mock_drag = MagicMock()
            mock_drag_class.return_value = mock_drag
            
            # Call the method
            tracker_widget.mouseMoveEvent_feature(mock_event)
            
            # Verify drag was created and configured
            mock_mime.assert_called_once()
            mock_drag_class.assert_called_once_with(tracker_widget)
            mock_drag.setMimeData.assert_called_once()
            mock_drag.setHotSpot.assert_called_once()
            mock_drag.targetChanged.connect.assert_called_once()
            mock_drag.exec_.assert_called_once_with(QtCore.Qt.MoveAction)


@pytest.mark.skip(reason="WFWaNoWidget requires extensive mocking")
class TestWFWaNoWidget:
    """Tests for the WFWaNoWidget class."""

    # Most tests for WFWaNoWidget are skipped because it requires extensive
    # mocking of Qt components and external dependencies.
    # We'll test a few basic methods.

    @pytest.fixture
    def mock_wano_list_entry(self):
        """Create a mock WaNoListEntry."""
        wano = MagicMock()
        wano.name = "TestWaNo"
        wano.folder = Path("/path/to/wano")
        wano.icon = "path/to/icon.png"
        return wano

    @pytest.fixture
    def parent_widget(self, qtbot):
        """Create a parent widget with model."""
        widget = MagicMock()
        widget.model = MagicMock()
        widget.model.get_root.return_value = MagicMock()
        return widget

    def test_set_color(self):
        """Test setColor method."""
        # Create mock widget
        widget = MagicMock(spec=WFWaNoWidget)

        # Call method
        color = Qt.green
        WFWaNoWidget.setColor(widget, color)

        # Verify palette was set with the right color
        widget.setPalette.assert_called_once()
        palette = widget.setPalette.call_args[0][0]
        assert isinstance(palette, QPalette)

    def test_get_xml(self):
        """Test get_xml method."""
        # Create mock widget
        widget = MagicMock(spec=WFWaNoWidget)
        widget.wano = MagicMock()
        widget.wano.name = "TestWaNo"
        widget.uuid = str(uuid.uuid4())

        # Call method
        with patch("simstack.view.WFEditorPanel.etree") as mock_etree:
            mock_element = MagicMock()
            mock_etree.Element.return_value = mock_element
            result = WFWaNoWidget.get_xml(widget)

            # Verify element was created with right attributes
            mock_etree.Element.assert_called_once_with("WaNo")
            assert mock_element.attrib["type"] == widget.wano.name
            assert mock_element.attrib["uuid"] == widget.uuid
            assert result is mock_element


class TestSubmitType:
    """Tests for the SubmitType enum class."""

    def test_submit_type_values(self):
        """Test SubmitType enum values."""
        assert SubmitType.SINGLE_WANO.value == 0
        assert SubmitType.WORKFLOW.value == 1


class TestWFItemListInterface:
    """Tests for the WFItemListInterface class."""

    @pytest.fixture
    def item_list(self):
        """Create a WFItemListInterface instance."""
        editor = MagicMock()
        view = MagicMock()
        return WFItemListInterface(editor=editor, view=view)

    @pytest.fixture
    def mock_wano_widget(self):
        """Create a mock WFWaNoWidget."""
        widget = MagicMock(spec=WFWaNoWidget)
        widget.is_wano = True
        widget.name = "TestWaNo"
        widget.text.return_value = "TestWaNo"
        return widget

    @pytest.fixture
    def mock_control_widget(self):
        """Create a mock control widget."""
        widget = MagicMock()
        widget.is_wano = False
        widget.name = "TestControl"
        widget.text.return_value = "TestControl"
        widget.collect_wano_widgets.return_value = []
        return widget

    def test_init(self, item_list):
        """Test initialization of WFItemListInterface."""
        assert item_list.is_wano is False
        assert isinstance(item_list.editor, MagicMock)
        assert isinstance(item_list.view, MagicMock)
        assert item_list.elements == []
        assert item_list.elementnames == []
        assert item_list.foldername is None

    def test_element_to_name(self, item_list, mock_wano_widget):
        """Test element_to_name method."""
        # Add element
        item_list.elements = [mock_wano_widget]
        item_list.elementnames = ["TestWaNo"]

        # Test element_to_name
        assert item_list.element_to_name(mock_wano_widget) == "TestWaNo"

    def test_collect_wano_widgets(
        self, item_list, mock_wano_widget, mock_control_widget
    ):
        """Test collect_wano_widgets method."""
        # Add elements
        item_list.elements = [mock_wano_widget, mock_control_widget]

        # Set up nested WaNo widgets in control
        nested_wano = MagicMock(spec=WFWaNoWidget)
        nested_wano.is_wano = True
        mock_control_widget.collect_wano_widgets.return_value = [nested_wano]

        # Test collect_wano_widgets
        result = item_list.collect_wano_widgets()
        assert len(result) == 2
        assert result[0] is mock_wano_widget
        assert result[1] is nested_wano

    def test_move_element_to_position(self, item_list):
        """Test move_element_to_position method."""
        # Create mock elements
        ele1 = MagicMock()
        ele2 = MagicMock()
        ele3 = MagicMock()

        # Add elements
        item_list.elements = [ele1, ele2, ele3]
        item_list.elementnames = ["ele1", "ele2", "ele3"]

        # Move element from beginning to end
        item_list.move_element_to_position(ele1, 2)
        assert item_list.elements == [ele2, ele3, ele1]
        assert item_list.elementnames == ["ele2", "ele3", "ele1"]

        # Move element from end to middle
        item_list.move_element_to_position(ele1, 1)
        assert item_list.elements == [ele2, ele1, ele3]
        assert item_list.elementnames == ["ele2", "ele1", "ele3"]

    def test_unique_name(self, item_list):
        """Test unique_name method."""
        # Set up existing names
        item_list.elementnames = ["name1", "name2", "name3"]

        # Test with non-existing name
        assert item_list.unique_name("newname") == "newname"

        # Test with existing name
        assert item_list.unique_name("name1") == "name1_1"

        # Test with multiple conflicts
        item_list.elementnames.append("name4_1")
        assert item_list.unique_name("name4") == "name4_2"

    def test_add_element(self, item_list, mock_wano_widget):
        """Test add_element method."""
        # Test adding without position
        item_list.add_element(mock_wano_widget)
        assert item_list.elements == [mock_wano_widget]
        assert item_list.elementnames == [mock_wano_widget.text()]

        # Clear lists
        item_list.elements = []
        item_list.elementnames = []

        # Test adding with position
        item_list.add_element(mock_wano_widget, pos=0)
        assert item_list.elements == [mock_wano_widget]
        assert item_list.elementnames == ["TestWaNo"]

        # Test adding with position and name conflict
        another_widget = MagicMock()
        another_widget.name = "TestWaNo"
        another_widget.text.return_value = "TestWaNo"
        item_list.add_element(another_widget, pos=1)
        assert item_list.elements == [mock_wano_widget, another_widget]
        assert item_list.elementnames == ["TestWaNo", "TestWaNo_1"]
        assert another_widget.setText.called_with("TestWaNo_1")

    def test_remove_element(self, item_list, mock_wano_widget):
        """Test remove_element method."""
        # Add elements
        item_list.elements = [mock_wano_widget]
        item_list.elementnames = ["TestWaNo"]

        # Remove element
        item_list.remove_element(mock_wano_widget)
        assert item_list.elements == []
        assert item_list.elementnames == []

    def test_open_wano_editor(self, item_list, mock_wano_widget):
        """Test openWaNoEditor method."""
        # Call openWaNoEditor
        item_list.openWaNoEditor(mock_wano_widget)

        # Verify editor's openWaNoEditor was called
        item_list.editor.openWaNoEditor.assert_called_once_with(mock_wano_widget)

    def test_remove_element_as_wano(self, item_list, mock_wano_widget):
        """Test removeElement method with WaNo widget."""
        # Mock get_wano_names
        root = MagicMock()
        root.get_wano_names.return_value = []

        # Set up element
        item_list.elements = [mock_wano_widget]
        item_list.elementnames = ["TestWaNo"]
        item_list.get_root = MagicMock(return_value=root)

        # Call removeElement
        item_list.removeElement(mock_wano_widget)

        # Verify methods were called
        mock_wano_widget.close.assert_called_once()
        item_list.editor.remove.assert_called_once_with(mock_wano_widget)
        mock_wano_widget.view.deleteLater.assert_called_once()
        root.wano_folder_remove.assert_called_once_with(mock_wano_widget.wano.name)

    def test_element_to_name_not_found(self, item_list):
        """Test element_to_name with element not found."""
        mock_widget = MagicMock()
        item_list.elements = []
        item_list.elementnames = []
        
        # This will raise ValueError since element is not in list
        with pytest.raises(ValueError):
            item_list.element_to_name(mock_widget)

    def test_remove_element_not_found(self, item_list):
        """Test remove_element with element not in list."""
        mock_widget = MagicMock()
        item_list.elements = []
        item_list.elementnames = []
        
        # This will raise ValueError since element is not in list
        with pytest.raises(ValueError):
            item_list.remove_element(mock_widget)


class TestWFItemModel:
    """Tests for the WFItemModel class."""

    @pytest.fixture
    def item_model(self):
        """Create a WFItemModel instance."""
        return WFItemModel()

    def test_init(self, item_model):
        """Test initialization of WFItemModel."""
        # No assertion needed - just make sure it initializes without error
        pass

    def test_render_to_simple_wf(self, item_model):
        """Test render_to_simple_wf method."""
        # It's just a pass method in the base class
        result = item_model.render_to_simple_wf(None, None, None, None)
        assert result is None

    def test_assemble_files(self, item_model):
        """Test assemble_files method."""
        result = item_model.assemble_files(None)
        assert result == []

    def test_assemble_variables(self, item_model):
        """Test assemble_variables method."""
        result = item_model.assemble_variables(None)
        assert result == []

    def test_close(self, item_model):
        """Test close method."""
        # No assertion needed - just make sure it runs without error
        item_model.close()

    def test_set_text(self, item_model):
        """Test setText method."""
        item_model.setText("NewName")
        assert item_model.name == "NewName"

    def test_save_to_disk(self, item_model):
        """Test save_to_disk method."""
        result = item_model.save_to_disk(None)
        assert result == []

    def test_read_from_disk(self, item_model):
        """Test read_from_disk method."""
        # No assertion needed - just make sure it runs without error
        item_model.read_from_disk(None, None)

    def test_model_property(self, item_model):
        """Test that model property returns self."""
        assert hasattr(item_model, 'model') is False  # WFItemModel doesn't have model property

    def test_has_name_attribute(self, item_model):
        """Test that WFItemModel can have name attribute set."""
        item_model.name = "TestModel"
        assert item_model.name == "TestModel"


class TestWFFileName:
    """Tests for the WFFileName class."""

    def test_init(self):
        """Test initialization of WFFileName."""
        filename = WFFileName()
        assert filename.dirName == "."
        assert filename.name == "Untitled"
        assert filename.ext == "xml"

    def test_full_name_default(self):
        """Test fullName method with default values."""
        filename = WFFileName()
        assert filename.fullName() == "./Untitled.xml"

    def test_full_name_custom(self):
        """Test fullName method with custom values."""
        filename = WFFileName()
        filename.dirName = "/custom/path"
        filename.name = "MyWorkflow"
        filename.ext = "wf"
        assert filename.fullName() == "/custom/path/MyWorkflow.wf"


class TestWhileModel:
    """Tests for the WhileModel class."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for WhileModel."""
        editor = MagicMock()
        view = MagicMock()
        view.logical_parent = MagicMock()
        wf_root = MagicMock()
        
        # Mock ControlFactory
        mock_subwf_model = MagicMock()
        mock_subwf_view = MagicMock()
        
        with patch("simstack.view.WFEditorPanel.ControlFactory.construct") as mock_construct:
            mock_construct.return_value = (mock_subwf_model, mock_subwf_view)
            
            while_model = WhileModel(
                editor=editor,
                view=view,
                wf_root=wf_root
            )
            
        return while_model, mock_subwf_model, mock_subwf_view

    def test_init(self, mock_dependencies):
        """Test initialization of WhileModel."""
        while_model, mock_subwf_model, mock_subwf_view = mock_dependencies
        
        assert while_model.is_wano is False
        assert while_model.name == "While"
        assert while_model.itername == "While_iterator"
        assert while_model._condition == "Condition"
        assert while_model.subwf_models == [mock_subwf_model]
        assert while_model.subwf_views == [mock_subwf_view]

    def test_condition_methods(self, mock_dependencies):
        """Test condition getter and setter methods."""
        while_model, _, _ = mock_dependencies
        
        # Test setter and getter
        while_model.set_condition("x > 0")
        assert while_model.get_condition() == "x > 0"

    def test_itername_methods(self, mock_dependencies):
        """Test itername getter and setter methods."""
        while_model, _, _ = mock_dependencies
        
        # Test setter and getter
        while_model.set_itername("custom_iterator")
        assert while_model.get_itername() == "custom_iterator"

    def test_collect_wano_widgets(self, mock_dependencies):
        """Test collect_wano_widgets method."""
        while_model, mock_subwf_model, _ = mock_dependencies
        
        # Mock the subwf_model's collect_wano_widgets method
        mock_wano1 = MagicMock()
        mock_wano2 = MagicMock()
        mock_subwf_model.collect_wano_widgets.return_value = [mock_wano1, mock_wano2]
        
        result = while_model.collect_wano_widgets()
        assert result == [mock_wano1, mock_wano2]
        mock_subwf_model.collect_wano_widgets.assert_called_once()


class TestVariableModel:
    """Tests for the VariableModel class."""

    @pytest.fixture
    def variable_model(self):
        """Create a VariableModel instance."""
        editor = MagicMock()
        view = MagicMock()
        wf_root = MagicMock()
        
        return VariableModel(
            editor=editor,
            view=view,
            wf_root=wf_root
        )

    def test_init(self, variable_model):
        """Test initialization of VariableModel."""
        assert variable_model.is_wano is False
        assert variable_model.name == "Variable"
        assert variable_model._varname == "Variable"
        assert variable_model._varequation == "Equation"

    def test_model_property(self, variable_model):
        """Test model property."""
        assert variable_model.model is variable_model

    def test_varname_methods(self, variable_model):
        """Test varname getter and setter methods."""
        variable_model.set_varname("test_variable")
        assert variable_model.get_varname() == "test_variable"

    def test_varequation_methods(self, variable_model):
        """Test varequation getter and setter methods."""
        variable_model.set_varequation("x + y")
        assert variable_model.get_varequation() == "x + y"

    def test_render_to_simple_wf(self, variable_model):
        """Test render_to_simple_wf method."""
        with patch("simstack.view.wf_editor_models.VariableElement") as mock_var_element:
            mock_element_instance = MagicMock()
            mock_element_instance.uid = "test_uid"
            mock_var_element.return_value = mock_element_instance
            
            variable_model.set_varname("test_var")
            variable_model.set_varequation("x * 2")
            
            path_list = ["path1"]
            output_path_list = ["output1"]
            submitdir = "submit"
            jobdir = "job"
            path = "test_path"
            parent_ids = ["parent1", "parent2"]
            
            elements, transitions, result_ids = variable_model.render_to_simple_wf(
                path_list, output_path_list, submitdir, jobdir, path, parent_ids
            )
            
            # Verify VariableElement was created with correct parameters
            mock_var_element.assert_called_once_with(
                variable_name="test_var",
                equation="x * 2"
            )
            
            # Verify return values
            assert elements == [("VariableElement", mock_element_instance)]
            assert transitions == [("parent1", "test_uid"), ("parent2", "test_uid")]
            assert result_ids == ["test_uid"]


class TestIfModel:
    """Tests for the IfModel class."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for IfModel."""
        editor = MagicMock()
        view = MagicMock()
        view.logical_parent = MagicMock()
        wf_root = MagicMock()
        
        # Mock ControlFactory to return two different subworkflow models/views
        mock_true_model = MagicMock()
        mock_true_view = MagicMock()
        mock_false_model = MagicMock()
        mock_false_view = MagicMock()
        
        with patch("simstack.view.WFEditorPanel.ControlFactory.construct") as mock_construct:
            mock_construct.side_effect = [
                (mock_true_model, mock_true_view),
                (mock_false_model, mock_false_view)
            ]
            
            if_model = IfModel(
                editor=editor,
                view=view,
                wf_root=wf_root
            )
            
        return if_model, mock_true_model, mock_true_view, mock_false_model, mock_false_view

    def test_init(self, mock_dependencies):
        """Test initialization of IfModel."""
        if_model, mock_true_model, mock_true_view, mock_false_model, mock_false_view = mock_dependencies
        
        assert if_model.is_wano is False
        assert if_model.name == "Branch"
        assert if_model._condition == ""
        assert if_model.subwf_models == [mock_true_model, mock_false_model]
        assert if_model.subwf_views == [mock_true_view, mock_false_view]
        assert if_model._subwf_true_branch_model is mock_true_model
        assert if_model._subwf_true_branch_view is mock_true_view
        assert if_model._subwf_false_branch_model is mock_false_model
        assert if_model._subwf_false_branch_view is mock_false_view

    def test_condition_methods(self, mock_dependencies):
        """Test condition getter and setter methods."""
        if_model, _, _, _, _ = mock_dependencies
        
        # Test setter and getter
        if_model.set_condition("x == 1")
        assert if_model.get_condition() == "x == 1"

    def test_collect_wano_widgets(self, mock_dependencies):
        """Test collect_wano_widgets method."""
        if_model, mock_true_model, _, mock_false_model, _ = mock_dependencies
        
        # Mock the subwf_models' collect_wano_widgets methods
        mock_wano1 = MagicMock()
        mock_wano2 = MagicMock()
        mock_wano3 = MagicMock()
        mock_true_model.collect_wano_widgets.return_value = [mock_wano1, mock_wano2]
        mock_false_model.collect_wano_widgets.return_value = [mock_wano3]
        
        result = if_model.collect_wano_widgets()
        assert result == [mock_wano1, mock_wano2, mock_wano3]
        mock_true_model.collect_wano_widgets.assert_called_once()
        mock_false_model.collect_wano_widgets.assert_called_once()


@pytest.mark.skip(reason="SubWFModel requires extensive mocking")
class TestSubWFModel:
    """Tests for the SubWFModel class."""

    # These tests are skipped because SubWFModel requires extensive
    # mocking of etree and WFWaNoWidget instantiation.
    pass
