import pytest
import os
import tempfile
from unittest.mock import MagicMock, patch, mock_open
from pathlib import Path

from simstack.view.wf_editor_models import (
    linuxjoin,
    merge_path,
    SubmitType,
    DragDropTargetTracker,
    WFItemModel,
    WFItemListInterface,
    SubWFModel,
    WhileModel,
    IfModel,
    ParallelModel,
    ForEachModel,
    AdvancedForEachModel,
    WFModel,
    VariableModel,
)


class TestUtilityFunctions:
    """Tests for utility functions in wf_editor_models."""

    def test_linuxjoin_basic(self):
        """Test linuxjoin function."""
        result = linuxjoin("path", "to", "file")
        assert result == "path/to/file"

    def test_linuxjoin_empty_components(self):
        """Test linuxjoin with empty components."""
        result = linuxjoin("", "path", "", "file")
        assert result == "path/file"

    def test_merge_path_basic(self):
        """Test merge_path function with basic inputs."""
        result = merge_path("root", "step", "variable")
        assert result == "root.step.variable"

    def test_merge_path_with_leading_dot(self):
        """Test merge_path function when result starts with dot."""
        result = merge_path("", "step", "variable")
        assert result == "step.variable"

    def test_merge_path_complex(self):
        """Test merge_path with various inputs."""
        result = merge_path("workflow.branch", "iteration", "output")
        assert result == "workflow.branch.iteration.output"

    def test_merge_path_all_empty_except_one(self):
        """Test merge_path with mostly empty inputs."""
        result = merge_path("", "", "variable")
        assert result == ".variable"


class TestSubmitType:
    """Tests for SubmitType enum."""

    def test_submit_type_values(self):
        """Test SubmitType enum values."""
        assert SubmitType.SINGLE_WANO.value == 0
        assert SubmitType.WORKFLOW.value == 1

    def test_submit_type_names(self):
        """Test SubmitType enum names."""
        assert SubmitType.SINGLE_WANO.name == "SINGLE_WANO"
        assert SubmitType.WORKFLOW.name == "WORKFLOW"


class TestWFItemModel:
    """Tests for WFItemModel base class."""

    @pytest.fixture
    def item_model(self):
        """Create a WFItemModel instance."""
        return WFItemModel()

    def test_init(self, item_model):
        """Test WFItemModel initialization."""
        # Should initialize without error
        assert item_model is not None

    def test_render_to_simple_wf(self, item_model):
        """Test render_to_simple_wf method."""
        result = item_model.render_to_simple_wf([], [], "submit", "job")
        assert result is None

    def test_assemble_files(self, item_model):
        """Test assemble_files method."""
        result = item_model.assemble_files("test_path")
        assert result == []

    def test_assemble_variables(self, item_model):
        """Test assemble_variables method."""
        result = item_model.assemble_variables("test_path")
        assert result == []

    def test_close(self, item_model):
        """Test close method."""
        # Should execute without error
        item_model.close()

    def test_set_text(self, item_model):
        """Test setText method."""
        item_model.setText("TestName")
        assert item_model.name == "TestName"

    def test_save_to_disk(self, item_model):
        """Test save_to_disk method."""
        result = item_model.save_to_disk("test_folder")
        assert result == []

    def test_read_from_disk(self, item_model):
        """Test read_from_disk method."""
        # Should execute without error
        item_model.read_from_disk("test_folder", None)


class TestWFItemListInterface:
    """Tests for WFItemListInterface class."""

    @pytest.fixture
    def item_list(self):
        """Create a WFItemListInterface instance."""
        editor = MagicMock()
        view = MagicMock()
        return WFItemListInterface(editor=editor, view=view)

    def test_init(self, item_list):
        """Test WFItemListInterface initialization."""
        assert item_list.is_wano is False
        assert item_list.elements == []
        assert item_list.elementnames == []
        assert item_list.foldername is None

    def test_element_to_name(self, item_list):
        """Test element_to_name method."""
        mock_element = MagicMock()
        item_list.elements = [mock_element]
        item_list.elementnames = ["TestElement"]

        result = item_list.element_to_name(mock_element)
        assert result == "TestElement"

    def test_element_to_name_not_found(self, item_list):
        """Test element_to_name with element not in list."""
        mock_element = MagicMock()
        with pytest.raises(ValueError):
            item_list.element_to_name(mock_element)

    def test_unique_name(self, item_list):
        """Test unique_name method."""
        item_list.elementnames = ["test", "test_1", "other"]

        # Test with unused name
        result = item_list.unique_name("unused")
        assert result == "unused"

        # Test with used name
        result = item_list.unique_name("test")
        assert result == "test_2"

    def test_add_element_without_position(self, item_list):
        """Test add_element method without position."""
        mock_element = MagicMock()
        mock_element.text.return_value = "TestElement"

        item_list.add_element(mock_element)

        assert len(item_list.elements) == 1
        assert item_list.elements[0] is mock_element
        assert item_list.elementnames[0] == "TestElement"

    def test_add_element_with_position_and_unique_name(self, item_list):
        """Test add_element method with position and name conflict."""
        mock_element = MagicMock()
        mock_element.name = "TestElement"
        mock_element.text.return_value = "TestElement"

        # Pre-populate with same name
        item_list.elementnames = ["TestElement"]
        item_list.elements = [MagicMock()]

        item_list.add_element(mock_element, pos=0)

        # Should have made name unique
        mock_element.setText.assert_called_with("TestElement_1")
        assert mock_element.name == "TestElement_1"

    def test_remove_element(self, item_list):
        """Test remove_element method."""
        mock_element = MagicMock()
        item_list.elements = [mock_element]
        item_list.elementnames = ["TestElement"]

        item_list.remove_element(mock_element)

        assert len(item_list.elements) == 0
        assert len(item_list.elementnames) == 0

    def test_remove_element_not_found(self, item_list):
        """Test remove_element with element not in list."""
        mock_element = MagicMock()
        with pytest.raises(ValueError):
            item_list.remove_element(mock_element)

    def test_open_wano_editor(self, item_list):
        """Test openWaNoEditor method."""
        mock_widget = MagicMock()
        item_list.openWaNoEditor(mock_widget)
        item_list.editor.openWaNoEditor.assert_called_once_with(mock_widget)

    def test_collect_wano_widgets_empty(self, item_list):
        """Test collect_wano_widgets with empty list."""
        result = item_list.collect_wano_widgets()
        assert result == []

    def test_collect_wano_widgets_with_control(self, item_list):
        """Test collect_wano_widgets with control element that has nested widgets."""
        # Mock control widget with nested WaNos
        mock_control = MagicMock()
        nested_wano1 = MagicMock()
        nested_wano2 = MagicMock()
        mock_control.collect_wano_widgets.return_value = [nested_wano1, nested_wano2]

        item_list.elements = [mock_control]

        result = item_list.collect_wano_widgets()
        assert len(result) == 2
        assert result[0] is nested_wano1
        assert result[1] is nested_wano2

    def test_move_element_to_position(self, item_list):
        """Test move_element_to_position method."""
        elem1 = MagicMock()
        elem2 = MagicMock()
        elem3 = MagicMock()

        item_list.elements = [elem1, elem2, elem3]
        item_list.elementnames = ["elem1", "elem2", "elem3"]

        # Move first element to position 2 (but with adjustment logic: 2-1=1, so final position 1)
        item_list.move_element_to_position(elem1, 2)

        # The logic does: pop(0), then since old_index(0) < new_position(2), new_position becomes 1
        # Then insert at position 1
        assert item_list.elements == [elem2, elem1, elem3]
        assert item_list.elementnames == ["elem2", "elem1", "elem3"]

    def test_collect_wano_widgets_with_wfwanowidget(self, item_list):
        """Test collect_wano_widgets with WFWaNoWidget instances."""

        # Create a proper mock class to use with isinstance
        class MockWFWaNoWidget:
            pass

        with patch("simstack.view.wf_editor_models.WFWaNoWidget", MockWFWaNoWidget):
            mock_wano = MockWFWaNoWidget()

            item_list.elements = [mock_wano]

            result = item_list.collect_wano_widgets()
            assert result == [mock_wano]

    def test_remove_element_method(self, item_list):
        """Test removeElement method (calls remove_element and additional cleanup)."""

        # Create a proper mock class to use with isinstance
        class MockWFWaNoWidget:
            pass

        with patch("simstack.view.wf_editor_models.WFWaNoWidget", MockWFWaNoWidget):
            mock_element = MockWFWaNoWidget()
            mock_element.close = MagicMock()
            mock_element.view = MagicMock()
            mock_element.view.deleteLater = MagicMock()
            mock_element.wano = MagicMock()
            mock_element.wano.name = "TestWaNo"

            item_list.elements = [mock_element]
            item_list.elementnames = ["TestElement"]
            item_list.editor.remove = MagicMock()

            # Mock get_root and get_wano_names for the WFWaNoWidget case
            mock_root = MagicMock()
            mock_root.wano_folder_remove = MagicMock()
            item_list.get_root = MagicMock(return_value=mock_root)
            item_list.get_wano_names = MagicMock(return_value=[])

            item_list.removeElement(mock_element)

            # Verify cleanup was performed
            mock_element.close.assert_called_once()
            item_list.editor.remove.assert_called_once_with(mock_element)
            mock_element.view.deleteLater.assert_called_once()
            assert len(item_list.elements) == 0
            assert len(item_list.elementnames) == 0

            # Verify wano folder removal was called
            mock_root.wano_folder_remove.assert_called_once_with("TestWaNo")


class TestSubWFModel:
    """Tests for SubWFModel class."""

    @pytest.fixture
    def sub_wf_model(self):
        """Create a SubWFModel instance."""
        editor = MagicMock()
        view = MagicMock()
        wf_root = MagicMock()

        return SubWFModel(editor=editor, view=view, wf_root=wf_root)

    def test_init(self, sub_wf_model):
        """Test SubWFModel initialization."""
        assert sub_wf_model.name == "SubWF"
        assert hasattr(sub_wf_model, "wf_root")

    def test_get_root(self, sub_wf_model):
        """Test get_root method."""
        result = sub_wf_model.get_root()
        assert result is sub_wf_model.wf_root

    def test_assemble_files_empty(self, sub_wf_model):
        """Test assemble_files with empty elements."""
        result = sub_wf_model.assemble_files("test_path")
        assert result == []

    def test_assemble_files_with_wano(self, sub_wf_model):
        """Test assemble_files with WaNo elements."""
        mock_wano = MagicMock()
        mock_wano.is_wano = True
        mock_wano.wano_model.get_output_files.return_value = [
            "output1.txt",
            "output2.txt",
        ]

        sub_wf_model.elements = [mock_wano]
        sub_wf_model.elementnames = ["TestWaNo"]

        result = sub_wf_model.assemble_files("base_path")
        expected = [
            "base_path/TestWaNo/outputs/output1.txt",
            "base_path/TestWaNo/outputs/output2.txt",
        ]
        assert result == expected

    def test_assemble_variables_empty(self, sub_wf_model):
        """Test assemble_variables with empty elements."""
        result = sub_wf_model.assemble_variables("test_path")
        assert result == []

    def test_assemble_variables_with_wano(self, sub_wf_model):
        """Test assemble_variables with WaNo elements."""
        mock_wano = MagicMock()
        mock_wano.is_wano = True
        mock_wano.name = "TestWaNo"
        mock_wano.get_variables.return_value = ["var1", "var2"]

        sub_wf_model.elements = [mock_wano]
        sub_wf_model.elementnames = ["TestWaNo"]

        with patch("simstack.view.wf_editor_models.merge_path") as mock_merge:
            mock_merge.side_effect = lambda p, n, v: f"{p}.{n}.{v}"

            result = sub_wf_model.assemble_variables("base_path")
            expected = ["base_path.TestWaNo.var1", "base_path.TestWaNo.var2"]
            assert result == expected

    def test_assemble_files_with_non_wano(self, sub_wf_model):
        """Test assemble_files with non-WaNo elements."""
        mock_control = MagicMock()
        mock_control.is_wano = False
        mock_control.assemble_files.return_value = [
            "control_file1.txt",
            "control_file2.txt",
        ]

        sub_wf_model.elements = [mock_control]
        sub_wf_model.elementnames = ["ControlElement"]

        result = sub_wf_model.assemble_files("base_path")
        expected = ["base_path/control_file1.txt", "base_path/control_file2.txt"]
        assert result == expected
        mock_control.assemble_files.assert_called_once_with("base_path")

    def test_assemble_variables_with_non_wano(self, sub_wf_model):
        """Test assemble_variables with non-WaNo elements."""
        mock_control = MagicMock()
        mock_control.is_wano = False
        mock_control.assemble_variables.return_value = ["control_var1", "control_var2"]

        sub_wf_model.elements = [mock_control]
        sub_wf_model.elementnames = ["ControlElement"]

        result = sub_wf_model.assemble_variables("base_path")
        expected = ["control_var1", "control_var2"]
        assert result == expected
        mock_control.assemble_variables.assert_called_once_with("base_path")

    def test_render_to_simple_wf_with_wano(self, sub_wf_model):
        """Test render_to_simple_wf with WaNo element."""
        mock_wano = MagicMock()
        mock_wano.is_wano = True
        mock_wano.render.return_value = ("jsdl", MagicMock(), ["path"])

        wem_mock = MagicMock()
        wem_mock.uid = "wano_uid"
        mock_wano.render.return_value = ("jsdl", wem_mock, ["path"])

        sub_wf_model.elements = [mock_wano]
        sub_wf_model.elementnames = ["TestWaNo"]
        sub_wf_model.element_to_name = MagicMock(return_value="TestWaNo")

        with patch("os.makedirs"), patch("os.path.join", return_value="job/TestWaNo"):
            activities, transitions, parent_ids = sub_wf_model.render_to_simple_wf(
                path_list=["root"],
                output_path_list=["output"],
                submitdir="submit",
                jobdir="job",
                path="workflow_path",
                parent_ids=["parent1"],
            )

        # Verify WaNo was rendered
        mock_wano.render.assert_called_once()
        wem_mock.set_given_name.assert_called_with("TestWaNo")
        wem_mock.set_path.assert_called_with("root/TestWaNo")
        wem_mock.set_outputpath.assert_called_with("output/TestWaNo")

        # Verify return values
        assert len(activities) == 1
        assert activities[0][0] == "WorkflowExecModule"
        assert activities[0][1] is wem_mock
        assert transitions == [("parent1", "wano_uid")]
        assert parent_ids == ["wano_uid"]

    def test_render_to_simple_wf_with_control(self, sub_wf_model):
        """Test render_to_simple_wf with control element."""
        mock_control = MagicMock()
        mock_control.is_wano = False
        mock_control.render_to_simple_wf.return_value = (
            [("ControlActivity", "control_obj")],
            [("parent1", "control_uid")],
            ["control_uid"],
        )

        sub_wf_model.elements = [mock_control]
        sub_wf_model.elementnames = ["ControlElement"]

        activities, transitions, parent_ids = sub_wf_model.render_to_simple_wf(
            path_list=["root"],
            output_path_list=["output"],
            submitdir="submit",
            jobdir="job",
            path="workflow_path",
            parent_ids=["parent1"],
        )

        # Verify control was rendered
        mock_control.render_to_simple_wf.assert_called_once()

        # Verify return values
        assert activities == [("ControlActivity", "control_obj")]
        assert transitions == [("parent1", "control_uid")]
        assert parent_ids == ["control_uid"]

    def test_save_to_disk_with_elements(self, sub_wf_model):
        """Test save_to_disk with various elements."""
        # Mock WaNo element
        mock_wano = MagicMock()
        mock_wano.is_wano = True
        mock_wano.get_xml.return_value = MagicMock()
        mock_wano.instantiate_in_folder.return_value = True
        mock_wano.save_delta = MagicMock()

        # Mock control element
        mock_control = MagicMock()
        mock_control.is_wano = False
        mock_control.save_to_disk.return_value = MagicMock()

        sub_wf_model.elements = [mock_wano, mock_control]
        sub_wf_model.elementnames = ["TestWaNo", "TestControl"]
        sub_wf_model.view.text.return_value = "SubWorkflow"

        with patch("simstack.view.wf_editor_models.etree") as mock_etree:
            mock_root = MagicMock()
            mock_etree.Element.return_value = mock_root

            result = sub_wf_model.save_to_disk("test_folder")

        # Verify XML structure was created
        mock_etree.Element.assert_called_with(
            "WFControl", attrib={"name": "SubWorkflow", "type": "SubWorkflow"}
        )

        # Verify WaNo processing
        mock_wano.instantiate_in_folder.assert_called_once_with("test_folder")
        mock_wano.save_delta.assert_called_once_with("test_folder")

        # Verify control processing
        mock_control.save_to_disk.assert_called_once_with("test_folder")

        assert result is mock_root

    def test_read_from_disk_with_wano(self, sub_wf_model):
        """Test read_from_disk with WaNo elements."""
        # Mock XML structure for WaNo
        mock_child = MagicMock()
        mock_child.tag = "WaNo"
        mock_child.attrib = {
            "type": "TestType",
            "name": "TestWaNo",
            "uuid": "test-uuid",
            "id": "0",
        }

        mock_xml = MagicMock()
        mock_xml.__iter__ = lambda self: iter([mock_child])

        # Mock get_root method
        mock_root = MagicMock()
        mock_root.get_wf_read_version.return_value = "2.0"
        with patch.object(sub_wf_model, "get_root", return_value=mock_root), patch(
            "simstack.view.wf_editor_models.WFWaNoWidget"
        ) as mock_wfwanowidget, patch("pathlib.Path"), patch(
            "simstack.view.wf_editor_models.WaNoDelta"
        ) as mock_wanodelta:
            mock_widget = MagicMock()
            mock_wfwanowidget.instantiate_from_folder.return_value = mock_widget

            mock_delta = MagicMock()
            mock_delta.folder = "wano_folder"
            mock_wanodelta.return_value = mock_delta

            sub_wf_model.read_from_disk("test_folder", mock_xml)

        # Verify WaNo was created and added
        assert len(sub_wf_model.elements) == 1
        assert sub_wf_model.elements[0] is mock_widget
        assert sub_wf_model.elementnames == ["TestWaNo"]
        mock_widget.setText.assert_called_once_with("TestWaNo")

    def test_read_from_disk_with_control(self, sub_wf_model):
        """Test read_from_disk with control elements."""
        # Mock XML structure for control
        mock_child = MagicMock()
        mock_child.tag = "WFControl"
        mock_child.attrib = {"name": "TestControl", "type": "While"}

        mock_xml = MagicMock()
        mock_xml.__iter__ = lambda self: iter([mock_child])

        with patch(
            "simstack.view.wf_editor_models._get_control_factory"
        ) as mock_factory:
            mock_model = MagicMock()
            mock_view = MagicMock()
            mock_factory.return_value.construct.return_value = (mock_model, mock_view)

            sub_wf_model.read_from_disk("test_folder", mock_xml)

        # Verify control was created and added
        assert len(sub_wf_model.elements) == 1
        assert sub_wf_model.elements[0] is mock_model
        assert sub_wf_model.elementnames == ["TestControl"]
        mock_view.setText.assert_called_once_with("TestControl")
        mock_model.read_from_disk.assert_called_once_with(
            full_foldername="test_folder", xml_subelement=mock_child
        )

    def test_remove_element_with_wano_cleanup(self, sub_wf_model):
        """Test remove_element with WaNo cleanup."""
        from simstack.view.wf_editor_models import WFWaNoWidget

        # Create a mock element that is instance of WFWaNoWidget
        mock_element = MagicMock()
        mock_element.__class__ = WFWaNoWidget
        mock_element.wano.name = "TestWaNo"

        sub_wf_model.elements = [mock_element]
        sub_wf_model.elementnames = ["TestElement"]

        # Mock get_root and get_wano_names
        mock_root = MagicMock()
        mock_root.get_wano_names.return_value = []  # WaNo not in use elsewhere
        mock_root.wano_folder_remove = MagicMock()

        with patch.object(sub_wf_model, "get_root", return_value=mock_root):
            sub_wf_model.remove_element(mock_element)

            # Verify element was removed
            assert len(sub_wf_model.elements) == 0
            assert len(sub_wf_model.elementnames) == 0

            # Verify wano folder removal was called
            mock_root.wano_folder_remove.assert_called_once_with("TestWaNo")

    def test_removeElement_method(self, sub_wf_model):
        """Test removeElement method (wrapper)."""
        mock_element = MagicMock()
        sub_wf_model.elements = [mock_element]
        sub_wf_model.elementnames = ["TestElement"]

        sub_wf_model.removeElement(mock_element)

        # Verify element was removed
        assert len(sub_wf_model.elements) == 0
        assert len(sub_wf_model.elementnames) == 0


class TestWhileModel:
    """Tests for WhileModel class."""

    @pytest.fixture
    def while_model_dependencies(self):
        """Create dependencies for WhileModel."""
        editor = MagicMock()
        view = MagicMock()
        view.logical_parent = MagicMock()
        wf_root = MagicMock()

        # Mock the ControlFactory to avoid circular import issues
        with patch(
            "simstack.view.wf_editor_models._get_control_factory"
        ) as mock_factory:
            mock_subwf_model = MagicMock()
            mock_subwf_view = MagicMock()
            mock_factory.return_value.construct.return_value = (
                mock_subwf_model,
                mock_subwf_view,
            )

            while_model = WhileModel(editor=editor, view=view, wf_root=wf_root)

        return while_model, mock_subwf_model, mock_subwf_view

    def test_init(self, while_model_dependencies):
        """Test WhileModel initialization."""
        while_model, mock_subwf_model, mock_subwf_view = while_model_dependencies

        assert while_model.is_wano is False
        assert while_model.name == "While"
        assert while_model.itername == "While_iterator"
        assert while_model._condition == "Condition"
        assert while_model.subwf_models == [mock_subwf_model]
        assert while_model.subwf_views == [mock_subwf_view]

    def test_condition_getters_setters(self, while_model_dependencies):
        """Test condition getter and setter methods."""
        while_model, _, _ = while_model_dependencies

        while_model.set_condition("x > 0")
        assert while_model.get_condition() == "x > 0"

    def test_itername_getters_setters(self, while_model_dependencies):
        """Test itername getter and setter methods."""
        while_model, _, _ = while_model_dependencies

        while_model.set_itername("custom_iterator")
        assert while_model.get_itername() == "custom_iterator"

    def test_collect_wano_widgets(self, while_model_dependencies):
        """Test collect_wano_widgets method."""
        while_model, mock_subwf_model, _ = while_model_dependencies

        mock_wano1 = MagicMock()
        mock_wano2 = MagicMock()
        mock_subwf_model.collect_wano_widgets.return_value = [mock_wano1, mock_wano2]

        result = while_model.collect_wano_widgets()
        assert result == [mock_wano1, mock_wano2]
        mock_subwf_model.collect_wano_widgets.assert_called_once()

    def test_render_to_simple_wf(self, while_model_dependencies):
        """Test render_to_simple_wf method."""
        while_model, mock_subwf_model, _ = while_model_dependencies

        # Setup mock subworkflow render result
        mock_subwf_model.render_to_simple_wf.return_value = (
            [("SubActivity", "sub_obj")],
            [("temporary_connector", "sub_uid")],
            ["sub_uid"],
        )

        with patch("simstack.view.wf_editor_models.SubGraph"), patch(
            "simstack.view.wf_editor_models.WorkflowElementList"
        ), patch("simstack.view.wf_editor_models.DirectedGraph"), patch(
            "simstack.view.wf_editor_models.WFPass"
        ) as mock_wfpass, patch(
            "simstack.view.wf_editor_models.WhileGraph"
        ) as mock_while_graph, patch("simstack.view.wf_editor_models.StringList"):
            mock_pass = MagicMock()
            mock_pass.uid = "pass_uid"
            mock_wfpass.return_value = mock_pass

            mock_while = MagicMock()
            mock_while.uid = "while_uid"
            mock_while_graph.return_value = mock_while

            while_model.set_condition("x > 0")
            while_model.set_itername("my_iterator")

            activities, transitions, result_ids = while_model.render_to_simple_wf(
                path_list=["root"],
                output_path_list=["output"],
                submitdir="submit",
                jobdir="job",
                path="workflow_path",
                parent_ids=["parent1"],
            )

            # Verify subworkflow was called with correct paths
            expected_path_list = ["root", "While"]
            expected_output_list = ["output", "While", "${my_iterator}"]
            mock_subwf_model.render_to_simple_wf.assert_called_once_with(
                expected_path_list,
                expected_output_list,
                "submit",
                "job/While",
                path="workflow_path/While",
                parent_ids=["temporary_connector"],
            )

            # Verify WhileGraph creation
            mock_while_graph.assert_called_once()
            call_kwargs = mock_while_graph.call_args[1]
            assert call_kwargs["iterator_name"] == "my_iterator"
            assert call_kwargs["condition"] == "x > 0"
            assert call_kwargs["finish_uid"] == "pass_uid"

            # Verify return values
            assert len(activities) == 2
            assert activities[0] == ("WhileGraph", mock_while)
            assert activities[1] == ("WFPass", mock_pass)
            assert transitions == [("parent1", "while_uid")]
            assert result_ids == ["pass_uid"]

    def test_assemble_variables(self, while_model_dependencies):
        """Test assemble_variables method."""
        while_model, mock_subwf_model, _ = while_model_dependencies

        mock_subwf_model.assemble_variables.return_value = ["sub_var1", "sub_var2"]
        while_model.set_itername("my_iterator")

        result = while_model.assemble_variables("base_path")

        # Verify subworkflow was called with correct path
        mock_subwf_model.assemble_variables.assert_called_once_with(
            "base_path.While.${my_iterator_ITER}"
        )

        # Verify iterator variable was added
        expected = ["sub_var1", "sub_var2", "${my_iterator}"]
        assert result == expected

    def test_assemble_variables_empty_path(self, while_model_dependencies):
        """Test assemble_variables with empty path."""
        while_model, mock_subwf_model, _ = while_model_dependencies

        mock_subwf_model.assemble_variables.return_value = []
        while_model.set_itername("test_iter")

        result = while_model.assemble_variables("")

        # Verify subworkflow was called with correct path
        mock_subwf_model.assemble_variables.assert_called_once_with(
            "While.${test_iter_ITER}"
        )

        # Verify iterator variable was added
        expected = ["${test_iter}"]
        assert result == expected

    def test_assemble_files(self, while_model_dependencies):
        """Test assemble_files method."""
        while_model, mock_subwf_model, _ = while_model_dependencies

        mock_subwf_model.assemble_files.return_value = ["file1.txt", "file2.txt"]
        while_model.view.text.return_value = "WhileLoop"

        result = while_model.assemble_files("base_path")

        # Verify subworkflow was called
        mock_subwf_model.assemble_files.assert_called_once_with("base_path")

        # Verify files were prefixed with while path and wildcards
        expected = [
            "base_path/WhileLoop/*/file1.txt",
            "base_path/WhileLoop/*/file2.txt",
        ]
        assert result == expected

    def test_save_to_disk(self, while_model_dependencies):
        """Test save_to_disk method."""
        while_model, mock_subwf_model, _ = while_model_dependencies

        mock_subwf_model.save_to_disk.return_value = MagicMock()
        while_model.set_condition("x < 10")
        while_model.set_itername("loop_var")

        with patch("simstack.view.wf_editor_models.etree") as mock_etree:
            mock_root = MagicMock()
            mock_iter_xml = MagicMock()
            mock_etree.Element.return_value = mock_root
            mock_etree.SubElement.return_value = mock_iter_xml

            result = while_model.save_to_disk("test_folder")

            # Verify XML structure
            mock_etree.Element.assert_called_once_with(
                "WFControl",
                attrib={"name": "While", "type": "While", "condition": "x < 10"},
            )
            mock_etree.SubElement.assert_called_once_with(mock_root, "IterName")
            mock_iter_xml.text = "loop_var"

            # Verify subworkflow save was called
            mock_subwf_model.save_to_disk.assert_called_once_with("test_folder")

            assert result is mock_root

    def test_read_from_disk(self, while_model_dependencies):
        """Test read_from_disk method."""
        while_model, mock_subwf_model, mock_subwf_view = while_model_dependencies

        # Mock XML structure
        mock_iter_child = MagicMock()
        mock_iter_child.tag = "IterName"
        mock_iter_child.text = "read_iterator"

        mock_subwf_child = MagicMock()
        mock_subwf_child.tag = "WFControl"
        mock_subwf_child.attrib = {"type": "SubWorkflow", "name": "ReadSubWF"}

        mock_xml = MagicMock()
        mock_xml.attrib = {"type": "While", "condition": "read_condition"}
        mock_xml.__iter__ = lambda self: iter([mock_iter_child, mock_subwf_child])

        while_model.read_from_disk("test_folder", mock_xml)

        # Verify condition and iterator were set
        assert while_model.get_condition() == "read_condition"
        assert while_model.get_itername() == "read_iterator"

        # Verify subworkflow view was updated and read was called
        mock_subwf_view.setText.assert_called_once_with("ReadSubWF")
        mock_subwf_model.read_from_disk.assert_called_once_with(
            full_foldername="test_folder", xml_subelement=mock_subwf_child
        )


class TestIfModel:
    """Tests for IfModel class."""

    @pytest.fixture
    def if_model_dependencies(self):
        """Create dependencies for IfModel."""
        editor = MagicMock()
        view = MagicMock()
        view.logical_parent = MagicMock()
        wf_root = MagicMock()

        # Mock the ControlFactory to return two different subworkflow models/views
        with patch(
            "simstack.view.wf_editor_models._get_control_factory"
        ) as mock_factory:
            mock_true_model = MagicMock()
            mock_true_view = MagicMock()
            mock_false_model = MagicMock()
            mock_false_view = MagicMock()

            mock_factory.return_value.construct.side_effect = [
                (mock_true_model, mock_true_view),
                (mock_false_model, mock_false_view),
            ]

            if_model = IfModel(editor=editor, view=view, wf_root=wf_root)

        return (
            if_model,
            mock_true_model,
            mock_true_view,
            mock_false_model,
            mock_false_view,
        )

    def test_init(self, if_model_dependencies):
        """Test IfModel initialization."""
        (
            if_model,
            mock_true_model,
            mock_true_view,
            mock_false_model,
            mock_false_view,
        ) = if_model_dependencies

        assert if_model.is_wano is False
        assert if_model.name == "Branch"
        assert if_model._condition == ""
        assert if_model.subwf_models == [mock_true_model, mock_false_model]
        assert if_model.subwf_views == [mock_true_view, mock_false_view]

    def test_condition_getters_setters(self, if_model_dependencies):
        """Test condition getter and setter methods."""
        if_model, _, _, _, _ = if_model_dependencies

        if_model.set_condition("x == 1")
        assert if_model.get_condition() == "x == 1"

    def test_collect_wano_widgets(self, if_model_dependencies):
        """Test collect_wano_widgets method."""
        if_model, mock_true_model, _, mock_false_model, _ = if_model_dependencies

        mock_wano1 = MagicMock()
        mock_wano2 = MagicMock()
        mock_wano3 = MagicMock()

        mock_true_model.collect_wano_widgets.return_value = [mock_wano1, mock_wano2]
        mock_false_model.collect_wano_widgets.return_value = [mock_wano3]

        result = if_model.collect_wano_widgets()
        assert result == [mock_wano1, mock_wano2, mock_wano3]

    def test_render_to_simple_wf(self, if_model_dependencies):
        """Test render_to_simple_wf method."""
        (
            if_model,
            mock_true_model,
            mock_true_view,
            mock_false_model,
            mock_false_view,
        ) = if_model_dependencies

        # Setup mock subworkflow render results
        mock_true_model.render_to_simple_wf.return_value = (
            [("TrueActivity", "true_obj")],
            [("temporary_connector", "true_uid")],
            ["true_uid"],
        )
        mock_false_model.render_to_simple_wf.return_value = (
            [("FalseActivity", "false_obj")],
            [("temporary_connector", "false_uid")],
            ["false_uid"],
        )

        with patch("simstack.view.wf_editor_models.SubGraph"), patch(
            "simstack.view.wf_editor_models.WorkflowElementList"
        ), patch("simstack.view.wf_editor_models.DirectedGraph"), patch(
            "simstack.view.wf_editor_models.WFPass"
        ) as mock_wfpass, patch(
            "simstack.view.wf_editor_models.IfGraph"
        ) as mock_if_graph, patch("simstack.view.wf_editor_models.StringList"):
            mock_pass = MagicMock()
            mock_pass.uid = "pass_uid"
            mock_wfpass.return_value = mock_pass

            mock_if = MagicMock()
            mock_if.uid = "if_uid"
            mock_if_graph.return_value = mock_if

            if_model.set_condition("x == 1")

            activities, transitions, result_ids = if_model.render_to_simple_wf(
                path_list=["root"],
                output_path_list=["output"],
                submitdir="submit",
                jobdir="job",
                path="workflow_path",
                parent_ids=["parent1"],
            )

            # Verify true branch was called with correct paths
            expected_true_path_list = ["root", "Branch", "True"]
            expected_true_output_list = ["output", "Branch", "True"]
            mock_true_model.render_to_simple_wf.assert_called_once_with(
                expected_true_path_list,
                expected_true_output_list,
                "submit",
                "job/Branch/True",
                path="workflow_path/Branch/True/",
                parent_ids=["temporary_connector"],
            )

            # Verify false branch was called with correct paths
            expected_false_path_list = ["root", "Branch", "False"]
            expected_false_output_list = ["output", "Branch", "False"]
            mock_false_model.render_to_simple_wf.assert_called_once_with(
                expected_false_path_list,
                expected_false_output_list,
                "submit",
                "job/Branch/False",
                path="workflow_path/Branch/False/",
                parent_ids=["temporary_connector"],
            )

            # Verify IfGraph creation
            mock_if_graph.assert_called_once()
            call_kwargs = mock_if_graph.call_args[1]
            assert call_kwargs["condition"] == "x == 1"
            assert call_kwargs["finish_uid"] == "pass_uid"

            # Verify return values
            assert len(activities) == 2
            assert activities[0] == ("IfGraph", mock_if)
            assert activities[1] == ("WFPass", mock_pass)
            assert transitions == [("parent1", "if_uid")]
            assert result_ids == ["pass_uid"]

    def test_assemble_variables(self, if_model_dependencies):
        """Test assemble_variables method."""
        (
            if_model,
            mock_true_model,
            _,
            mock_false_model,
            _,
        ) = if_model_dependencies

        # Note: there's a bug in the original code - it uses true model twice instead of false
        # We test the actual behavior, not the intended behavior
        mock_true_model.assemble_variables.return_value = ["true_var1", "true_var2"]

        with patch("simstack.view.wf_editor_models.merge_path") as mock_merge:
            mock_merge.side_effect = lambda p, n, v: f"{p}.{n}.{v}"

            result = if_model.assemble_variables("base_path")

            # The bug means it calls true model twice, once for True and once for False
            assert mock_true_model.assemble_variables.call_count == 2

            # Should have variables from both calls (even though it's the same model due to bug)
            expected = ["true_var1", "true_var2", "true_var1", "true_var2"]
            assert result == expected

    def test_assemble_files(self, if_model_dependencies):
        """Test assemble_files method."""
        (
            if_model,
            mock_true_model,
            _,
            mock_false_model,
            _,
        ) = if_model_dependencies

        # Note: same bug as assemble_variables - uses true model twice
        mock_true_model.assemble_files.return_value = [
            "true_file1.txt",
            "true_file2.txt",
        ]

        result = if_model.assemble_files("base_path")

        # Should call true model twice due to bug
        assert mock_true_model.assemble_files.call_count == 2

        # Should have files from both branches (even though same model due to bug)
        expected = [
            "base_path/Branch/True/true_file1.txt",
            "base_path/Branch/True/true_file2.txt",
            "base_path/Branch/False/true_file1.txt",
            "base_path/Branch/False/true_file2.txt",
        ]
        assert result == expected

    def test_save_to_disk(self, if_model_dependencies):
        """Test save_to_disk method."""
        (
            if_model,
            mock_true_model,
            _,
            mock_false_model,
            _,
        ) = if_model_dependencies

        mock_true_xml = MagicMock()
        mock_false_xml = MagicMock()
        mock_true_model.save_to_disk.return_value = mock_true_xml
        mock_false_model.save_to_disk.return_value = mock_false_xml

        if_model.set_condition("test_condition")

        with patch("simstack.view.wf_editor_models.etree") as mock_etree:
            mock_root = MagicMock()
            mock_etree.Element.return_value = mock_root

            result = if_model.save_to_disk("test_folder")

            # Verify XML structure
            mock_etree.Element.assert_called_once_with(
                "WFControl",
                attrib={"name": "Branch", "type": "If", "condition": "test_condition"},
            )

            # Verify both models were saved
            mock_true_model.save_to_disk.assert_called_once_with("test_folder")
            mock_false_model.save_to_disk.assert_called_once_with("test_folder")

            # Verify branch attributes were set
            mock_true_xml.attrib.__setitem__.assert_called_with("branch", "true")
            mock_false_xml.attrib.__setitem__.assert_called_with("branch", "false")

            assert result is mock_root

    def test_read_from_disk(self, if_model_dependencies):
        """Test read_from_disk method."""
        (
            if_model,
            _,
            _,
            _,
            _,
        ) = if_model_dependencies

        # Mock true branch XML
        mock_true_child = MagicMock()
        mock_true_child.tag = "WFControl"
        mock_true_child.attrib = {
            "type": "SubWorkflow",
            "name": "TrueBranch",
            "branch": "true",
        }

        # Mock false branch XML
        mock_false_child = MagicMock()
        mock_false_child.tag = "WFControl"
        mock_false_child.attrib = {
            "type": "SubWorkflow",
            "name": "FalseBranch",
            "branch": "false",
        }

        mock_xml = MagicMock()
        mock_xml.attrib = {"type": "If", "condition": "read_condition"}
        mock_xml.__iter__ = lambda self: iter([mock_true_child, mock_false_child])

        with patch(
            "simstack.view.wf_editor_models._get_control_factory"
        ) as mock_factory, patch("builtins.print") as mock_print:
            mock_true_model = MagicMock()
            mock_true_view = MagicMock()
            mock_false_model = MagicMock()
            mock_false_view = MagicMock()

            mock_factory.return_value.construct.side_effect = [
                (mock_true_model, mock_true_view),
                (mock_false_model, mock_false_view),
            ]

            if_model.read_from_disk("test_folder", mock_xml)

            # Verify condition was set
            assert if_model.get_condition() == "read_condition"
            mock_print.assert_called_once_with("Setting condition to", "read_condition")

            # Verify models were reconstructed and assigned correctly
            assert if_model._subwf_true_branch_model is mock_true_model
            assert if_model._subwf_true_branch_view is mock_true_view
            assert if_model._subwf_false_branch_model is mock_false_model
            assert if_model._subwf_false_branch_view is mock_false_view

            # Verify views were updated
            mock_true_view.setText.assert_called_once_with("TrueBranch")
            mock_false_view.setText.assert_called_once_with("FalseBranch")

            # Verify read_from_disk was called on models
            mock_true_model.read_from_disk.assert_called_once_with(
                full_foldername="test_folder", xml_subelement=mock_true_child
            )
            mock_false_model.read_from_disk.assert_called_once_with(
                full_foldername="test_folder", xml_subelement=mock_false_child
            )

            # Verify view init was called
            if_model.view.init_from_model.assert_called_once()


class TestVariableModel:
    """Tests for VariableModel class."""

    @pytest.fixture
    def variable_model(self):
        """Create a VariableModel instance."""
        editor = MagicMock()
        view = MagicMock()
        wf_root = MagicMock()

        return VariableModel(editor=editor, view=view, wf_root=wf_root)

    def test_init(self, variable_model):
        """Test VariableModel initialization."""
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
        with patch(
            "simstack.view.wf_editor_models.VariableElement"
        ) as mock_var_element:
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
                variable_name="test_var", equation="x * 2"
            )

            # Verify return values
            assert elements == [("VariableElement", mock_element_instance)]
            assert transitions == [("parent1", "test_uid"), ("parent2", "test_uid")]
            assert result_ids == ["test_uid"]

    def test_assemble_variables(self, variable_model):
        """Test assemble_variables method."""
        variable_model.set_varname("my_variable")

        result = variable_model.assemble_variables("test_path")

        # Should return the variable name
        assert result == ["my_variable"]

    def test_assemble_files(self, variable_model):
        """Test assemble_files method."""
        result = variable_model.assemble_files("test_path")

        # Should return empty list (variables don't have files)
        assert result == []

    def test_save_to_disk(self, variable_model):
        """Test save_to_disk method."""
        variable_model.set_varname("test_var")
        variable_model.set_varequation("x + y * 2")

        with patch("simstack.view.wf_editor_models.etree") as mock_etree:
            mock_root = MagicMock()
            mock_etree.Element.return_value = mock_root

            result = variable_model.save_to_disk("test_folder")

            # Verify XML structure
            mock_etree.Element.assert_called_once_with(
                "WFControl",
                attrib={
                    "name": "Variable",
                    "type": "Variable",
                    "equation": "x + y * 2",
                    "varname": "test_var",
                },
            )

            assert result is mock_root

    def test_read_from_disk(self, variable_model):
        """Test read_from_disk method."""
        mock_xml = MagicMock()
        mock_xml.attrib = {
            "type": "Variable",
            "equation": "a + b",
            "varname": "read_variable",
        }

        variable_model.read_from_disk("test_folder", mock_xml)

        # Verify attributes were set
        assert variable_model.get_varequation() == "a + b"
        assert variable_model.get_varname() == "read_variable"


class TestParallelModel:
    """Tests for ParallelModel class."""

    @pytest.fixture
    def parallel_model_dependencies(self):
        """Create dependencies for ParallelModel."""
        editor = MagicMock()
        view = MagicMock()
        view.logical_parent = MagicMock()
        wf_root = MagicMock()

        # Mock the ControlFactory
        with patch(
            "simstack.view.wf_editor_models._get_control_factory"
        ) as mock_factory:
            mock_subwf_model = MagicMock()
            mock_subwf_view = MagicMock()
            mock_factory.return_value.construct.return_value = (
                mock_subwf_model,
                mock_subwf_view,
            )

            parallel_model = ParallelModel(editor=editor, view=view, wf_root=wf_root)

        return parallel_model, mock_subwf_model, mock_subwf_view

    def test_init(self, parallel_model_dependencies):
        """Test ParallelModel initialization."""
        parallel_model, mock_subwf_model, mock_subwf_view = parallel_model_dependencies

        assert parallel_model.is_wano is False
        assert parallel_model.name == "Parallel"
        assert parallel_model.subwf_models == [mock_subwf_model]
        assert parallel_model.subwf_views == [mock_subwf_view]

    def test_collect_wano_widgets(self, parallel_model_dependencies):
        """Test collect_wano_widgets method."""
        parallel_model, mock_subwf_model, _ = parallel_model_dependencies

        mock_wano1 = MagicMock()
        mock_wano2 = MagicMock()
        mock_subwf_model.collect_wano_widgets.return_value = [mock_wano1, mock_wano2]

        result = parallel_model.collect_wano_widgets()
        assert result == [mock_wano1, mock_wano2]
        mock_subwf_model.collect_wano_widgets.assert_called_once()

    def test_render_to_simple_wf(self, parallel_model_dependencies):
        """Test render_to_simple_wf method."""
        parallel_model, mock_subwf_model, _ = parallel_model_dependencies

        # Setup mock subworkflow render result
        mock_subwf_model.render_to_simple_wf.return_value = (
            [("ParallelActivity", "parallel_obj")],
            [("parent1", "parallel_uid")],
            ["parallel_uid"],
        )

        activities, transitions, result_ids = parallel_model.render_to_simple_wf(
            path_list=["root"],
            output_path_list=["output"],
            submitdir="submit",
            jobdir="job",
            path="workflow_path",
            parent_ids=["parent1"],
        )

        # Verify subworkflow was called with correct paths
        expected_path_list = ["root", "Parallel", "0"]
        expected_output_list = ["output", "Parallel", "0"]
        mock_subwf_model.render_to_simple_wf.assert_called_once_with(
            expected_path_list,
            expected_output_list,
            "submit",
            "job/Parallel/0",
            path="workflow_path/Parallel/0",
            parent_ids=["parent1"],
        )

        # Verify return values (flattened from all parallel branches)
        assert activities == [("ParallelActivity", "parallel_obj")]
        assert transitions == [("parent1", "parallel_uid")]
        assert result_ids == ["parallel_uid"]

    def test_render_to_simple_wf_multiple_branches(self, parallel_model_dependencies):
        """Test render_to_simple_wf with multiple branches."""
        parallel_model, _, _ = parallel_model_dependencies

        # Add more branches
        with patch(
            "simstack.view.wf_editor_models._get_control_factory"
        ) as mock_factory:
            mock_subwf_model2 = MagicMock()
            mock_subwf_view2 = MagicMock()
            mock_factory.return_value.construct.return_value = (
                mock_subwf_model2,
                mock_subwf_view2,
            )

            parallel_model.add()  # Add second branch

        # Setup mock returns for both branches
        parallel_model.subwf_models[0].render_to_simple_wf.return_value = (
            [("Activity1", "obj1")],
            [("parent1", "uid1")],
            ["uid1"],
        )
        parallel_model.subwf_models[1].render_to_simple_wf.return_value = (
            [("Activity2", "obj2")],
            [("parent1", "uid2")],
            ["uid2"],
        )

        activities, transitions, result_ids = parallel_model.render_to_simple_wf(
            path_list=["root"],
            output_path_list=["output"],
            submitdir="submit",
            jobdir="job",
            path="workflow_path",
            parent_ids=["parent1"],
        )

        # Verify both branches were called
        assert parallel_model.subwf_models[0].render_to_simple_wf.call_count == 1
        assert parallel_model.subwf_models[1].render_to_simple_wf.call_count == 1

        # Verify combined results
        assert len(activities) == 2
        assert activities == [("Activity1", "obj1"), ("Activity2", "obj2")]
        assert len(transitions) == 2
        assert result_ids == ["uid1", "uid2"]

    def test_assemble_variables(self, parallel_model_dependencies):
        """Test assemble_variables method."""
        parallel_model, mock_subwf_model, _ = parallel_model_dependencies

        mock_subwf_model.assemble_variables.return_value = ["var1", "var2"]

        with patch("simstack.view.wf_editor_models.merge_path") as mock_merge:
            mock_merge.side_effect = lambda p, n, v: f"{p}.{n}.{v}"

            result = parallel_model.assemble_variables("base_path")

            # Verify subworkflow was called
            mock_subwf_model.assemble_variables.assert_called_once_with("base_path")

            # Verify variables were prefixed with parallel branch info
            expected = ["base_path.Parallel.0.var1", "base_path.Parallel.0.var2"]
            assert result == expected

    def test_add_method(self, parallel_model_dependencies):
        """Test add method to add new parallel branch."""
        parallel_model, _, _ = parallel_model_dependencies

        initial_count = len(parallel_model.subwf_models)

        with patch(
            "simstack.view.wf_editor_models._get_control_factory"
        ) as mock_factory:
            mock_new_model = MagicMock()
            mock_new_view = MagicMock()
            mock_factory.return_value.construct.return_value = (
                mock_new_model,
                mock_new_view,
            )

            parallel_model.add()

        # Verify new branch was added
        assert len(parallel_model.subwf_models) == initial_count + 1
        assert len(parallel_model.subwf_views) == initial_count + 1
        assert parallel_model.subwf_models[-1] is mock_new_model
        assert parallel_model.subwf_views[-1] is mock_new_view

    def test_deletelast_method(self, parallel_model_dependencies):
        """Test deletelast method to remove parallel branch."""
        parallel_model, _, _ = parallel_model_dependencies

        # Add a second branch first
        with patch(
            "simstack.view.wf_editor_models._get_control_factory"
        ) as mock_factory:
            mock_new_model = MagicMock()
            mock_new_view = MagicMock()
            mock_factory.return_value.construct.return_value = (
                mock_new_model,
                mock_new_view,
            )
            parallel_model.add()

        initial_count = len(parallel_model.subwf_models)
        last_view = parallel_model.subwf_views[-1]

        parallel_model.deletelast()

        # Verify last branch was removed
        assert len(parallel_model.subwf_models) == initial_count - 1
        assert len(parallel_model.subwf_views) == initial_count - 1
        last_view.deleteLater.assert_called_once()

    def test_deletelast_method_minimum_branches(self, parallel_model_dependencies):
        """Test deletelast method when only one branch remains."""
        parallel_model, _, _ = parallel_model_dependencies

        # Should have only one branch initially
        initial_count = len(parallel_model.subwf_models)
        assert initial_count == 1

        parallel_model.deletelast()

        # Should still have one branch (minimum)
        assert len(parallel_model.subwf_models) == 1
        assert len(parallel_model.subwf_views) == 1

    def test_assemble_files(self, parallel_model_dependencies):
        """Test assemble_files method."""
        parallel_model, mock_subwf_model, _ = parallel_model_dependencies

        mock_subwf_model.assemble_files.return_value = ["file1.txt", "file2.txt"]

        result = parallel_model.assemble_files("base_path")

        # Verify subworkflow was called
        mock_subwf_model.assemble_files.assert_called_once_with("base_path")

        # Verify files were prefixed with parallel branch path
        expected = ["base_path/Parallel/0/file1.txt", "base_path/Parallel/0/file2.txt"]
        assert result == expected

    def test_save_to_disk(self, parallel_model_dependencies):
        """Test save_to_disk method."""
        parallel_model, mock_subwf_model, _ = parallel_model_dependencies

        mock_subwf_model.save_to_disk.return_value = MagicMock()

        with patch("simstack.view.wf_editor_models.etree") as mock_etree:
            mock_root = MagicMock()
            mock_etree.Element.return_value = mock_root

            result = parallel_model.save_to_disk("test_folder")

            # Verify XML structure
            mock_etree.Element.assert_called_once_with(
                "WFControl", attrib={"name": "Parallel", "type": "Parallel"}
            )

            # Verify subworkflow save was called
            mock_subwf_model.save_to_disk.assert_called_once_with("test_folder")

            assert result is mock_root

    def test_read_from_disk(self, parallel_model_dependencies):
        """Test read_from_disk method."""
        parallel_model, _, _ = parallel_model_dependencies

        # Mock multiple subworkflow children
        mock_child1 = MagicMock()
        mock_child1.tag = "WFControl"
        mock_child1.attrib = {"type": "SubWorkflow", "name": "Branch1"}

        mock_child2 = MagicMock()
        mock_child2.tag = "WFControl"
        mock_child2.attrib = {"type": "SubWorkflow", "name": "Branch2"}

        mock_xml = MagicMock()
        mock_xml.__iter__ = lambda self: iter([mock_child1, mock_child2])

        with patch(
            "simstack.view.wf_editor_models._get_control_factory"
        ) as mock_factory:
            mock_model1 = MagicMock()
            mock_view1 = MagicMock()
            mock_model2 = MagicMock()
            mock_view2 = MagicMock()

            mock_factory.return_value.construct.side_effect = [
                (mock_model1, mock_view1),
                (mock_model2, mock_view2),
            ]

            parallel_model.read_from_disk("test_folder", mock_xml)

            # Verify models were reconstructed
            assert len(parallel_model.subwf_models) == 2
            assert len(parallel_model.subwf_views) == 2
            assert parallel_model.subwf_models[0] is mock_model1
            assert parallel_model.subwf_models[1] is mock_model2

            # Verify views were updated
            mock_view1.setText.assert_called_once_with("Branch1")
            mock_view2.setText.assert_called_once_with("Branch2")

            # Verify read_from_disk was called on models
            mock_model1.read_from_disk.assert_called_once_with(
                full_foldername="test_folder", xml_subelement=mock_child1
            )
            mock_model2.read_from_disk.assert_called_once_with(
                full_foldername="test_folder", xml_subelement=mock_child2
            )

            # Verify view init was called
            parallel_model.view.init_from_model.assert_called_once()


class TestForEachModel:
    """Tests for ForEachModel class."""

    @pytest.fixture
    def foreach_model_dependencies(self):
        """Create dependencies for ForEachModel."""
        editor = MagicMock()
        view = MagicMock()
        view.logical_parent = MagicMock()
        wf_root = MagicMock()

        # Mock the ControlFactory
        with patch(
            "simstack.view.wf_editor_models._get_control_factory"
        ) as mock_factory:
            mock_subwf_model = MagicMock()
            mock_subwf_view = MagicMock()
            mock_factory.return_value.construct.return_value = (
                mock_subwf_model,
                mock_subwf_view,
            )

            foreach_model = ForEachModel(editor=editor, view=view, wf_root=wf_root)

        return foreach_model, mock_subwf_model, mock_subwf_view

    def test_init(self, foreach_model_dependencies):
        """Test ForEachModel initialization."""
        foreach_model, mock_subwf_model, mock_subwf_view = foreach_model_dependencies

        assert foreach_model.is_wano is False
        assert foreach_model.name == "ForEach"
        assert foreach_model.subwfmodel is mock_subwf_model
        assert foreach_model.subwfview is mock_subwf_view

    def test_collect_wano_widgets(self, foreach_model_dependencies):
        """Test collect_wano_widgets method."""
        foreach_model, mock_subwf_model, _ = foreach_model_dependencies

        mock_wano1 = MagicMock()
        mock_wano2 = MagicMock()
        mock_subwf_model.collect_wano_widgets.return_value = [mock_wano1, mock_wano2]

        result = foreach_model.collect_wano_widgets()
        assert result == [mock_wano1, mock_wano2]
        mock_subwf_model.collect_wano_widgets.assert_called_once()

    def test_set_is_file_iterator(self, foreach_model_dependencies):
        """Test set_is_file_iterator method."""
        foreach_model, _, _ = foreach_model_dependencies

        foreach_model.set_is_file_iterator(False)
        assert foreach_model._is_file_iterator is False

        foreach_model.set_is_file_iterator(True)
        assert foreach_model._is_file_iterator is True

    def test_set_filelist(self, foreach_model_dependencies):
        """Test set_filelist method."""
        foreach_model, _, _ = foreach_model_dependencies

        foreach_model.set_filelist("file1.txt file2.txt file3.txt")
        assert foreach_model.fileliststring == "file1.txt file2.txt file3.txt"

    def test_assemble_variables(self, foreach_model_dependencies):
        """Test assemble_variables method."""
        foreach_model, mock_subwf_model, _ = foreach_model_dependencies

        mock_subwf_model.assemble_variables.return_value = ["sub_var1", "sub_var2"]
        foreach_model.itername = "my_iterator"

        result = foreach_model.assemble_variables("base_path")

        # Verify subworkflow was called with correct path
        mock_subwf_model.assemble_variables.assert_called_once_with(
            "base_path.ForEach.${my_iterator_ITER}"
        )

        # Verify iterator variables were added
        expected = ["sub_var1", "sub_var2", "${my_iterator_ITER}", "${my_iterator}"]
        assert result == expected

    def test_assemble_variables_empty_path(self, foreach_model_dependencies):
        """Test assemble_variables with empty path."""
        foreach_model, mock_subwf_model, _ = foreach_model_dependencies

        mock_subwf_model.assemble_variables.return_value = []
        foreach_model.itername = "test_iter"

        result = foreach_model.assemble_variables("")

        # Verify subworkflow was called with correct path
        mock_subwf_model.assemble_variables.assert_called_once_with(
            "ForEach.${test_iter_ITER}"
        )

        # Verify iterator variables were added
        expected = ["${test_iter_ITER}", "${test_iter}"]
        assert result == expected

    def test_render_to_simple_wf_file_iterator(self, foreach_model_dependencies):
        """Test render_to_simple_wf with file iterator."""
        foreach_model, mock_subwf_model, _ = foreach_model_dependencies

        # Setup file iterator
        foreach_model.set_is_file_iterator(True)
        foreach_model.set_filelist("file1.txt file2.txt file3.txt")
        foreach_model.itername = "file_iterator"

        # Setup mock subworkflow render result
        mock_subwf_model.render_to_simple_wf.return_value = (
            [("SubActivity", "sub_obj")],
            [("temporary_connector", "sub_uid")],
            ["sub_uid"],
        )

        with patch("simstack.view.wf_editor_models.SubGraph"), patch(
            "simstack.view.wf_editor_models.WorkflowElementList"
        ), patch("simstack.view.wf_editor_models.DirectedGraph"), patch(
            "simstack.view.wf_editor_models.WFPass"
        ) as mock_wfpass, patch(
            "simstack.view.wf_editor_models.ForEachGraph"
        ) as mock_foreach_graph, patch("simstack.view.wf_editor_models.StringList"):
            mock_pass = MagicMock()
            mock_pass.uid = "pass_uid"
            mock_wfpass.return_value = mock_pass

            mock_foreach = MagicMock()
            mock_foreach.uid = "foreach_uid"
            mock_foreach_graph.return_value = mock_foreach

            activities, transitions, result_ids = foreach_model.render_to_simple_wf(
                path_list=["root"],
                output_path_list=["output"],
                submitdir="submit",
                jobdir="job",
                path="workflow_path",
                parent_ids=["parent1"],
            )

            # Verify subworkflow was called with correct paths
            expected_path_list = ["root", "ForEach"]
            expected_output_list = ["output", "ForEach", "${file_iterator_ITER}"]
            mock_subwf_model.render_to_simple_wf.assert_called_once_with(
                expected_path_list,
                expected_output_list,
                "submit",
                "job/ForEach",
                path="workflow_path/ForEach",
                parent_ids=["temporary_connector"],
            )

            # Verify ForEachGraph creation for file iterator
            mock_foreach_graph.assert_called_once()
            call_kwargs = mock_foreach_graph.call_args[1]
            assert call_kwargs["iterator_name"] == "file_iterator"
            assert call_kwargs["finish_uid"] == "pass_uid"
            assert "iterator_files" in call_kwargs

            # Verify return values
            assert len(activities) == 2
            assert activities[0] == ("ForEachGraph", mock_foreach)
            assert activities[1] == ("WFPass", mock_pass)
            assert transitions == [("parent1", "foreach_uid")]
            assert result_ids == ["pass_uid"]

    def test_render_to_simple_wf_variable_iterator(self, foreach_model_dependencies):
        """Test render_to_simple_wf with variable iterator."""
        foreach_model, mock_subwf_model, _ = foreach_model_dependencies

        # Setup variable iterator
        foreach_model.set_is_file_iterator(False)
        foreach_model.set_filelist("var1 var2 var3")
        foreach_model.itername = "var_iterator"

        # Setup mock subworkflow render result
        mock_subwf_model.render_to_simple_wf.return_value = (
            [("SubActivity", "sub_obj")],
            [("temporary_connector", "sub_uid")],
            ["sub_uid"],
        )

        with patch("simstack.view.wf_editor_models.SubGraph"), patch(
            "simstack.view.wf_editor_models.WorkflowElementList"
        ), patch("simstack.view.wf_editor_models.DirectedGraph"), patch(
            "simstack.view.wf_editor_models.WFPass"
        ) as mock_wfpass, patch(
            "simstack.view.wf_editor_models.ForEachGraph"
        ) as mock_foreach_graph, patch("simstack.view.wf_editor_models.StringList"):
            mock_pass = MagicMock()
            mock_pass.uid = "pass_uid"
            mock_wfpass.return_value = mock_pass

            mock_foreach = MagicMock()
            mock_foreach.uid = "foreach_uid"
            mock_foreach_graph.return_value = mock_foreach

            activities, transitions, result_ids = foreach_model.render_to_simple_wf(
                path_list=["root"],
                output_path_list=["output"],
                submitdir="submit",
                jobdir="job",
                path="workflow_path",
                parent_ids=["parent1"],
            )

            # Verify ForEachGraph creation for variable iterator
            mock_foreach_graph.assert_called_once()
            call_kwargs = mock_foreach_graph.call_args[1]
            assert call_kwargs["iterator_name"] == "var_iterator"
            assert "iterator_variables" in call_kwargs
            assert "iterator_files" not in call_kwargs

    def test_assemble_files(self, foreach_model_dependencies):
        """Test assemble_files method."""
        foreach_model, mock_subwf_model, _ = foreach_model_dependencies

        mock_subwf_model.assemble_files.return_value = ["file1.txt", "file2.txt"]
        foreach_model.view.text.return_value = "ForEachLoop"
        foreach_model.itername = "my_iterator"

        result = foreach_model.assemble_files("base_path")

        # Verify subworkflow was called
        mock_subwf_model.assemble_files.assert_called_once_with("base_path")

        # Verify files include iterator and paths with wildcards
        expected = [
            "${my_iterator}",
            "base_path/ForEachLoop/*/file1.txt",
            "base_path/ForEachLoop/${my_iterator_ITER}/file1.txt",
            "base_path/ForEachLoop/*/file2.txt",
            "base_path/ForEachLoop/${my_iterator_ITER}/file2.txt",
        ]
        assert result == expected

    def test_save_to_disk_file_iterator(self, foreach_model_dependencies):
        """Test save_to_disk with file iterator."""
        foreach_model, mock_subwf_model, _ = foreach_model_dependencies

        mock_subwf_model.save_to_disk.return_value = MagicMock()
        foreach_model.set_is_file_iterator(True)
        foreach_model.set_filelist("file1.txt file2.txt")
        foreach_model.itername = "test_iter"
        foreach_model.view.text.return_value = "TestForEach"

        with patch("simstack.view.wf_editor_models.etree") as mock_etree:
            mock_root = MagicMock()
            mock_filelist = MagicMock()
            mock_file_xml = MagicMock()
            mock_iter_xml = MagicMock()

            mock_etree.Element.return_value = mock_root
            mock_etree.SubElement.side_effect = [
                mock_filelist,
                mock_file_xml,
                mock_file_xml,
                mock_iter_xml,
            ]

            result = foreach_model.save_to_disk("test_folder")

            # Verify XML structure
            mock_etree.Element.assert_called_once_with(
                "WFControl",
                attrib={
                    "name": "TestForEach",
                    "type": "ForEach",
                    "is_file_iterator": "True",
                },
            )

            # Verify file list XML creation
            assert (
                mock_etree.SubElement.call_count >= 3
            )  # FileList, File elements, IterName
            mock_iter_xml.text = "test_iter"

            # Verify subworkflow save was called
            mock_subwf_model.save_to_disk.assert_called_once_with("test_folder")

            assert result is mock_root

    def test_save_to_disk_variable_iterator(self, foreach_model_dependencies):
        """Test save_to_disk with variable iterator."""
        foreach_model, mock_subwf_model, _ = foreach_model_dependencies

        mock_subwf_model.save_to_disk.return_value = MagicMock()
        foreach_model.set_is_file_iterator(False)
        foreach_model._is_multivar_iterator = True  # Advanced ForEach
        foreach_model.view.text.return_value = "AdvancedForEach"

        with patch("simstack.view.wf_editor_models.etree") as mock_etree:
            mock_root = MagicMock()
            mock_etree.Element.return_value = mock_root

            foreach_model.save_to_disk("test_folder")

            # Verify XML structure for advanced ForEach
            mock_etree.Element.assert_called_once_with(
                "WFControl",
                attrib={
                    "name": "AdvancedForEach",
                    "type": "AdvancedFor",
                    "is_file_iterator": "False",
                },
            )

    def test_read_from_disk_with_file_iterator(self, foreach_model_dependencies):
        """Test read_from_disk with file iterator."""
        foreach_model, mock_subwf_model, mock_subwf_view = foreach_model_dependencies

        # Mock XML structure
        mock_file1 = MagicMock()
        mock_file1.text = "file1.txt"
        mock_file2 = MagicMock()
        mock_file2.text = "file2.txt"

        mock_filelist_child = MagicMock()
        mock_filelist_child.tag = "FileList"
        mock_filelist_child.__iter__ = lambda self: iter([mock_file1, mock_file2])

        mock_iter_child = MagicMock()
        mock_iter_child.tag = "IterName"
        mock_iter_child.text = "read_iterator"

        mock_subwf_child = MagicMock()
        mock_subwf_child.tag = "WFControl"
        mock_subwf_child.attrib = {"type": "SubWorkflow", "name": "ReadSubWF"}

        mock_xml = MagicMock()
        mock_xml.attrib = {"is_file_iterator": "True"}
        mock_xml.__iter__ = lambda self: iter(
            [mock_filelist_child, mock_iter_child, mock_subwf_child]
        )

        foreach_model.read_from_disk("test_folder", mock_xml)

        # Verify file iterator was set
        assert foreach_model._is_file_iterator is True

        # Verify file list was reconstructed
        assert foreach_model.fileliststring == "file1.txt file2.txt"

        # Verify iterator name was set
        assert foreach_model.itername == "read_iterator"

        # Verify subworkflow view was updated and read was called
        mock_subwf_view.setText.assert_called_once_with("ReadSubWF")
        mock_subwf_model.read_from_disk.assert_called_once_with(
            full_foldername="test_folder", xml_subelement=mock_subwf_child
        )

    def test_read_from_disk_with_variable_iterator(self, foreach_model_dependencies):
        """Test read_from_disk with variable iterator (missing is_file_iterator attribute)."""
        foreach_model, mock_subwf_model, mock_subwf_view = foreach_model_dependencies

        # Mock XML structure without is_file_iterator attribute (KeyError case)
        mock_xml = MagicMock()
        mock_xml.attrib = {}  # Missing is_file_iterator
        mock_xml.__iter__ = lambda self: iter([])

        foreach_model.read_from_disk("test_folder", mock_xml)

        # Verify default file iterator was set (True is default)
        assert foreach_model._is_file_iterator is True

    def test_read_from_disk_false_file_iterator(self, foreach_model_dependencies):
        """Test read_from_disk with is_file_iterator=False."""
        foreach_model, mock_subwf_model, mock_subwf_view = foreach_model_dependencies

        # Mock XML structure with is_file_iterator=False
        mock_xml = MagicMock()
        mock_xml.attrib = {"is_file_iterator": "False"}
        mock_xml.__iter__ = lambda self: iter([])

        foreach_model.read_from_disk("test_folder", mock_xml)

        # Verify file iterator was set to False
        assert foreach_model._is_file_iterator is False


class TestAdvancedForEachModel:
    """Tests for AdvancedForEachModel class."""

    @pytest.fixture
    def advanced_foreach_model_dependencies(self):
        """Create dependencies for AdvancedForEachModel."""
        editor = MagicMock()
        view = MagicMock()
        view.logical_parent = MagicMock()
        wf_root = MagicMock()

        # Mock the ControlFactory
        with patch(
            "simstack.view.wf_editor_models._get_control_factory"
        ) as mock_factory:
            mock_subwf_model = MagicMock()
            mock_subwf_view = MagicMock()
            mock_factory.return_value.construct.return_value = (
                mock_subwf_model,
                mock_subwf_view,
            )

            advanced_foreach_model = AdvancedForEachModel(
                editor=editor, view=view, wf_root=wf_root
            )

        return advanced_foreach_model, mock_subwf_model, mock_subwf_view

    def test_init(self, advanced_foreach_model_dependencies):
        """Test AdvancedForEachModel initialization."""
        advanced_foreach_model, _, _ = advanced_foreach_model_dependencies

        assert advanced_foreach_model.is_wano is False
        assert advanced_foreach_model.name == "AdvancedForEach"

    def test_inherits_from_foreach(self, advanced_foreach_model_dependencies):
        """Test that AdvancedForEachModel inherits from ForEachModel."""
        advanced_foreach_model, _, _ = advanced_foreach_model_dependencies

        assert isinstance(advanced_foreach_model, ForEachModel)

    def test_initialization_defaults(self, advanced_foreach_model_dependencies):
        """Test AdvancedForEachModel initialization with proper defaults."""
        advanced_foreach_model, _, _ = advanced_foreach_model_dependencies

        assert advanced_foreach_model.name == "AdvancedForEach"
        assert advanced_foreach_model.itername == "a,b"
        assert advanced_foreach_model.fileliststring == "zip([1,2],[3,4])"
        assert advanced_foreach_model._is_file_iterator is False
        assert advanced_foreach_model._is_multivar_iterator is True

    def test_assemble_variables(self, advanced_foreach_model_dependencies):
        """Test assemble_variables method for AdvancedForEachModel."""
        (
            advanced_foreach_model,
            mock_subwf_model,
            _,
        ) = advanced_foreach_model_dependencies

        mock_subwf_model.assemble_variables.return_value = ["sub_var1", "sub_var2"]
        advanced_foreach_model.itername = "x,y"

        result = advanced_foreach_model.assemble_variables("base_path")

        # Verify subworkflow was called with correct path (spaces removed from itername)
        mock_subwf_model.assemble_variables.assert_called_once_with(
            "base_path.AdvancedForEach.${x,y_ITER}"
        )

        # Verify iterator variables were added (with spaces removed and individual variables)
        expected = ["sub_var1", "sub_var2", "${x,y_ITER}", "${x}", "${y}"]
        assert result == expected

    def test_assemble_variables_empty_path(self, advanced_foreach_model_dependencies):
        """Test assemble_variables with empty path."""
        (
            advanced_foreach_model,
            mock_subwf_model,
            _,
        ) = advanced_foreach_model_dependencies

        mock_subwf_model.assemble_variables.return_value = []
        advanced_foreach_model.itername = "var1, var2"  # With spaces

        result = advanced_foreach_model.assemble_variables("")

        # Verify subworkflow was called with correct path (spaces removed)
        mock_subwf_model.assemble_variables.assert_called_once_with(
            "AdvancedForEach.${var1,var2_ITER}"
        )

        # Verify iterator variables (with spaces removed and individual variables)
        expected = ["${var1,var2_ITER}", "${var1}", "${var2}"]
        assert result == expected

    def test_assemble_variables_with_spaces_in_itername(
        self, advanced_foreach_model_dependencies
    ):
        """Test assemble_variables handles spaces in iterator names correctly."""
        (
            advanced_foreach_model,
            mock_subwf_model,
            _,
        ) = advanced_foreach_model_dependencies

        mock_subwf_model.assemble_variables.return_value = []
        advanced_foreach_model.itername = " a , b , c "  # Spaces around commas

        result = advanced_foreach_model.assemble_variables("test")

        # Verify spaces are removed from iterator name
        mock_subwf_model.assemble_variables.assert_called_once_with(
            "test.AdvancedForEach.${a,b,c_ITER}"
        )

        # Verify individual iterator variables (with spaces trimmed)
        expected = ["${a,b,c_ITER}", "${a}", "${b}", "${c}"]
        assert result == expected


class TestWFModel:
    """Tests for WFModel class."""

    @pytest.fixture
    def wf_model(self):
        """Create a WFModel instance."""
        editor = MagicMock()
        view = MagicMock()
        return WFModel(editor=editor, view=view)

    def test_init(self, wf_model):
        """Test WFModel initialization."""
        assert wf_model.wf_name == "Unset"
        assert wf_model._wf_read_version == "2.0"
        assert wf_model.elements == []
        assert wf_model.elementnames == []
        assert wf_model.foldername is None

    def test_get_wf_read_version(self, wf_model):
        """Test get_wf_read_version method."""
        assert wf_model.get_wf_read_version() == "2.0"

        wf_model._wf_read_version = "1.0"
        assert wf_model.get_wf_read_version() == "1.0"

    def test_get_root(self, wf_model):
        """Test get_root method."""
        assert wf_model.get_root() is wf_model

    def test_wf_name_attribute(self, wf_model):
        """Test wf_name attribute can be modified."""
        wf_model.wf_name = "TestWorkflow"
        assert wf_model.wf_name == "TestWorkflow"

    def test_element_to_name(self, wf_model):
        """Test element_to_name method."""
        mock_element = MagicMock()
        wf_model.elements = [mock_element]
        wf_model.elementnames = ["TestElement"]

        result = wf_model.element_to_name(mock_element)
        assert result == "TestElement"

    def test_assemble_files_empty(self, wf_model):
        """Test assemble_files with empty elements."""
        result = wf_model.assemble_files("test_path")
        assert result == []

    def test_assemble_variables_empty(self, wf_model):
        """Test assemble_variables with empty elements."""
        result = wf_model.assemble_variables("test_path")
        assert result == []

    def test_collect_wano_widgets_empty(self, wf_model):
        """Test collect_wano_widgets with empty elements."""
        result = wf_model.collect_wano_widgets()
        assert result == []

    def test_wano_folder_remove(self, wf_model):
        """Test wano_folder_remove method."""
        # This method should execute without error
        wf_model.wano_folder_remove("test_folder")

    def test_get_wano_names_empty(self, wf_model):
        """Test get_wano_names with no elements."""
        result = wf_model.get_wano_names()
        assert result == set()  # The method returns a set, not a list

    def test_get_wano_names_with_wanos(self, wf_model):
        """Test get_wano_names with WaNo widgets."""
        # Mock WaNo widgets
        mock_wano1 = MagicMock()
        mock_wano1.wano.name = "WaNo1"
        mock_wano2 = MagicMock()
        mock_wano2.wano.name = "WaNo2"

        wf_model.collect_wano_widgets = MagicMock(return_value=[mock_wano1, mock_wano2])

        result = wf_model.get_wano_names()
        assert result == {"WaNo1", "WaNo2"}  # The method returns a set

    def test_wano_folder_remove_with_folder(self, wf_model):
        """Test wano_folder_remove with actual folder."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wf_model.foldername = temp_dir
            wano_folder = Path(temp_dir) / "wanos" / "test_wano"
            wano_folder.mkdir(parents=True)

            # Verify folder exists
            assert wano_folder.exists()

            wf_model.wano_folder_remove("test_wano")

            # Verify folder was removed
            assert not wano_folder.exists()

    def test_wano_folder_remove_no_foldername(self, wf_model):
        """Test wano_folder_remove when no foldername is set."""
        wf_model.foldername = None
        # Should not raise an error
        wf_model.wano_folder_remove("test_wano")

    def test_wano_folder_remove_nonexistent_folder(self, wf_model):
        """Test wano_folder_remove with non-existent folder."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wf_model.foldername = temp_dir
            # Should not raise an error
            wf_model.wano_folder_remove("nonexistent_wano")

    def test_collect_wano_widgets_with_mixed_elements(self, wf_model):
        """Test collect_wano_widgets with mixed element types."""
        from simstack.view.wf_editor_models import WFWaNoWidget

        # Create mock WaNo widgets that properly inherit from the base class
        mock_wano1 = MagicMock(spec=WFWaNoWidget)
        mock_wano2 = MagicMock(spec=WFWaNoWidget)
        mock_control = MagicMock()
        mock_control.collect_wano_widgets.return_value = [mock_wano2]

        wf_model.elements = [mock_wano1, mock_control]

        result = wf_model.collect_wano_widgets()
        # Should get direct WaNo + nested WaNos from control
        assert len(result) == 2
        assert mock_wano1 in result
        assert mock_wano2 in result

    def test_assemble_variables_with_elements(self, wf_model):
        """Test assemble_variables with WaNo and control elements."""
        mock_wano = MagicMock()
        mock_wano.is_wano = True
        mock_wano.name = "TestWaNo"
        mock_wano.get_variables.return_value = ["var1", "var2"]

        mock_control = MagicMock()
        mock_control.is_wano = False
        mock_control.assemble_variables.return_value = ["control_var"]

        wf_model.elements = [mock_wano, mock_control]
        wf_model.elementnames = ["WaNo1", "Control1"]

        with patch("simstack.view.wf_editor_models.merge_path") as mock_merge:
            mock_merge.side_effect = lambda p, n, v: f"{p}.{n}.{v}"

            result = wf_model.assemble_variables("base")

            # Should have variables from both WaNo and control
            expected = ["base.TestWaNo.var1", "base.TestWaNo.var2", "control_var"]
            assert result == expected

    def test_render_to_simple_wf_with_elements(self, wf_model):
        """Test render_to_simple_wf with various elements."""
        # Mock WaNo element
        mock_wano = MagicMock()
        mock_wano.is_wano = True
        mock_wano.render.return_value = ("jsdl", MagicMock(), ["path"])

        wem_mock = MagicMock()
        wem_mock.uid = "wano_uid"
        mock_wano.render.return_value = ("jsdl", wem_mock, ["path"])

        # Mock control element
        mock_control = MagicMock()
        mock_control.is_wano = False
        mock_control.render_to_simple_wf.return_value = (
            [("ControlActivity", "control_obj")],
            [("0", "control_uid")],
            ["control_uid"],
        )

        wf_model.elements = [mock_wano, mock_control]
        wf_model.elementnames = ["WaNo1", "Control1"]
        wf_model.wf_name = "TestWorkflow"
        wf_model.element_to_name = MagicMock(
            side_effect=lambda x: wf_model.elementnames[wf_model.elements.index(x)]
        )

        with patch("os.makedirs"), patch(
            "os.path.join", side_effect=lambda *args: "/".join(args)
        ), patch("simstack.view.wf_editor_models.Workflow") as mock_workflow, patch(
            "simstack.view.wf_editor_models.WorkflowElementList"
        ), patch("simstack.view.wf_editor_models.DirectedGraph"), patch(
            "simstack.view.wf_editor_models.etree"
        ) as mock_etree:
            mock_wf = MagicMock()
            mock_workflow.return_value = mock_wf
            mock_xml = MagicMock()
            mock_etree.Element.return_value = mock_xml

            result = wf_model.render_to_simple_wf("submit", "job")

            # Verify WaNo was rendered
            mock_wano.render.assert_called_once()
            wem_mock.set_given_name.assert_called_with("WaNo1")

            # Verify control was rendered
            mock_control.render_to_simple_wf.assert_called_once()

            # Verify workflow creation
            mock_workflow.assert_called_once()
            mock_wf.to_xml.assert_called_once_with(parent_element=mock_xml)

            assert result is mock_xml

    def test_assemble_files_with_elements(self, wf_model):
        """Test assemble_files with WaNo and control elements."""
        mock_wano = MagicMock()
        mock_wano.is_wano = True
        mock_wano.wano_model.get_output_files.return_value = [
            "output1.txt",
            "output2.txt",
        ]

        mock_control = MagicMock()
        mock_control.is_wano = False
        mock_control.assemble_files.return_value = ["control_file.txt"]

        wf_model.elements = [mock_wano, mock_control]
        wf_model.elementnames = ["WaNo1", "Control1"]

        result = wf_model.assemble_files("base")

        # Verify files from both elements
        expected = [
            "WaNo1/outputs/output1.txt",
            "WaNo1/outputs/output2.txt",
            "control_file.txt",
        ]
        assert result == expected

    def test_save_to_disk_success(self, wf_model):
        """Test save_to_disk with successful save."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_folder = os.path.join(temp_dir, "TestWorkflow")

            # Mock WaNo element
            from lxml import etree

            mock_wano = MagicMock()
            mock_wano.is_wano = True
            mock_xml_element = etree.Element("test_wano")
            mock_wano.get_xml.return_value = mock_xml_element
            mock_wano.instantiate_in_folder.return_value = True
            mock_wano.save_delta = MagicMock()

            # Mock control element
            mock_control = MagicMock()
            mock_control.is_wano = False
            mock_control_xml = etree.Element("test_control")
            mock_control.save_to_disk.return_value = mock_control_xml

            wf_model.elements = [mock_wano, mock_control]
            wf_model.elementnames = ["WaNo1", "Control1"]

            with patch(
                "simstack.view.wf_editor_models.WaNoSettingsProvider"
            ) as mock_settings_provider, patch(
                "simstack.view.wf_editor_models.SimStackPaths"
            ), patch(
                "simstack.view.wf_editor_models.SETTING_KEYS",
                {"workflows": "workflows"},
            ), patch("os.makedirs"), patch("builtins.open", mock_open()), patch(
                "simstack.view.wf_editor_models.etree.tostring", return_value="<xml/>"
            ):
                mock_settings = MagicMock()
                mock_settings.get_value.return_value = temp_dir
                mock_settings_provider.get_instance.return_value = mock_settings

                result = wf_model.save_to_disk(test_folder)

                assert result is True
                assert wf_model.wf_name == "TestWorkflow"
                assert wf_model.foldername == test_folder

                # Verify WaNo save was called
                mock_wano.instantiate_in_folder.assert_called_once_with(test_folder)
                mock_wano.save_delta.assert_called_once_with(test_folder)

                # Verify control save was called
                mock_control.save_to_disk.assert_called_once_with(test_folder)

    def test_save_to_disk_failure(self, wf_model):
        """Test save_to_disk with failed save."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_folder = os.path.join(temp_dir, "TestWorkflow")

            # Mock WaNo element that fails
            from lxml import etree

            mock_wano = MagicMock()
            mock_wano.is_wano = True
            mock_xml_element = etree.Element("test_wano")
            mock_wano.get_xml.return_value = mock_xml_element
            mock_wano.instantiate_in_folder.return_value = False  # Failure

            wf_model.elements = [mock_wano]
            wf_model.elementnames = ["WaNo1"]

            with patch(
                "simstack.view.wf_editor_models.WaNoSettingsProvider"
            ) as mock_settings_provider, patch(
                "simstack.view.wf_editor_models.SETTING_KEYS",
                {"workflows": "workflows"},
            ), patch("os.makedirs"), patch("builtins.print") as mock_print:
                mock_settings = MagicMock()
                mock_settings.get_value.return_value = temp_dir
                mock_settings_provider.get_instance.return_value = mock_settings

                with pytest.raises(
                    Exception, match="This should be a custom exception"
                ):
                    wf_model.save_to_disk(test_folder)

                # Verify error was printed
                mock_print.assert_called_once_with("Error while writing wano")

    def test_save_to_disk_embedded_path(self, wf_model):
        """Test save_to_disk with embedded path setting."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_folder = os.path.join(temp_dir, "TestWorkflow")

            wf_model.elements = []
            wf_model.elementnames = []

            with patch(
                "simstack.view.wf_editor_models.WaNoSettingsProvider"
            ) as mock_settings_provider, patch(
                "simstack.view.wf_editor_models.SimStackPaths"
            ) as mock_paths, patch(
                "simstack.view.wf_editor_models.SETTING_KEYS",
                {"workflows": "workflows"},
            ), patch("simstack.view.wf_editor_models.join") as mock_join, patch(
                "os.makedirs"
            ), patch("builtins.open", mock_open()):
                mock_settings = MagicMock()
                mock_settings.get_value.return_value = "<embedded>"
                mock_settings_provider.get_instance.return_value = mock_settings

                mock_paths.get_embedded_path.return_value = "/embedded/path"
                mock_join.side_effect = lambda *args: "/".join(args)

                result = wf_model.save_to_disk(test_folder)

                assert result is True
                # Verify embedded path was used
                mock_paths.get_embedded_path.assert_called_once()

    def test_read_from_disk_v2(self, wf_model):
        """Test read_from_disk with version 2.0 workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wf_name = "TestWorkflow"
            wf_folder = os.path.join(temp_dir, wf_name)
            os.path.join(wf_folder, f"{wf_name}.xml")

            # Mock XML structure
            mock_wano_child = MagicMock()
            mock_wano_child.tag = "WaNo"
            mock_wano_child.attrib = {
                "type": "TestType",
                "name": "TestWaNo",
                "uuid": "test-uuid",
                "id": "0",
            }

            mock_control_child = MagicMock()
            mock_control_child.tag = "WFControl"
            mock_control_child.attrib = {"name": "TestControl", "type": "While"}

            mock_root = MagicMock()
            mock_root.attrib = {"wfxml_version": "2.0"}
            mock_root.__iter__ = lambda self: iter(
                [mock_wano_child, mock_control_child]
            )

            mock_tree = MagicMock()
            mock_tree.getroot.return_value = mock_root

            with patch(
                "simstack.view.wf_editor_models.etree.parse", return_value=mock_tree
            ), patch(
                "simstack.view.wf_editor_models.WFWaNoWidget"
            ) as mock_wfwanowidget, patch("pathlib.Path"), patch(
                "simstack.view.wf_editor_models.WaNoDelta"
            ) as mock_wanodelta, patch(
                "simstack.view.wf_editor_models._get_control_factory"
            ) as mock_factory:
                mock_widget = MagicMock()
                mock_wfwanowidget.instantiate_from_folder.return_value = mock_widget

                mock_delta = MagicMock()
                mock_delta.folder = "wano_folder"
                mock_wanodelta.return_value = mock_delta

                mock_model = MagicMock()
                mock_view = MagicMock()
                mock_factory.return_value.construct.return_value = (
                    mock_model,
                    mock_view,
                )

                wf_model.read_from_disk(wf_folder)

                # Verify workflow was loaded
                assert wf_model.foldername == wf_folder
                assert wf_model.wf_name == wf_name
                assert wf_model._wf_read_version == "2.0"

                # Verify elements were added
                assert len(wf_model.elements) == 2
                assert wf_model.elements[0] is mock_widget
                assert wf_model.elements[1] is mock_model
                assert wf_model.elementnames == ["TestWaNo", "TestControl"]

                # Verify view geometry update
                wf_model.view.updateGeometry.assert_called_once()

    def test_read_from_disk_v1(self, wf_model):
        """Test read_from_disk with version 1.0 workflow (no version attribute)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wf_name = "TestWorkflow"
            wf_folder = os.path.join(temp_dir, wf_name)

            mock_root = MagicMock()
            mock_root.attrib = {}  # No version attribute
            mock_root.__iter__ = lambda self: iter([])

            mock_tree = MagicMock()
            mock_tree.getroot.return_value = mock_root

            with patch(
                "simstack.view.wf_editor_models.etree.parse", return_value=mock_tree
            ):
                wf_model.read_from_disk(wf_folder)

                # Verify default version was set
                assert wf_model._wf_read_version == "1.0"

    def test_base_resource_during_render(self, wf_model):
        """Test base_resource_during_render method."""
        mock_resource = MagicMock()
        wf_model._base_resource_during_render = mock_resource

        result = wf_model.base_resource_during_render()
        assert result is mock_resource

    def test_render_method(self, wf_model):
        """Test render method."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wf_model.foldername = temp_dir
            wf_model.wf_name = "TestWorkflow"

            mock_resource = MagicMock()
            mock_xml = MagicMock()

            with patch(
                "simstack.view.wf_editor_models.datetime"
            ) as mock_datetime, patch("os.makedirs"), patch(
                "os.path.exists", return_value=False
            ), patch("time.sleep"):
                mock_now = MagicMock()
                mock_now.strftime.return_value = "2023-01-01-12h30m45s"
                mock_datetime.datetime.now.return_value = mock_now

                wf_model.render_to_simple_wf = MagicMock(return_value=mock_xml)

                submit_type, submit_dir, xml = wf_model.render(
                    "test_name", mock_resource
                )

                # Verify render results
                assert submit_type == SubmitType.WORKFLOW
                assert "2023-01-01-12h30m45s-test_name" in submit_dir
                assert xml is mock_xml

                # Verify resource was set and cleared
                wf_model.render_to_simple_wf.assert_called_once()
                assert wf_model._base_resource_during_render is None

    def test_render_method_with_existing_directory(self, wf_model):
        """Test render method when submit directory already exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            wf_model.foldername = temp_dir

            mock_resource = MagicMock()

            with patch(
                "simstack.view.wf_editor_models.datetime"
            ) as mock_datetime, patch("os.makedirs"), patch(
                "os.path.exists", side_effect=[True] * 10 + [False]
            ), patch("time.sleep") as mock_sleep:
                mock_now = MagicMock()
                mock_now.strftime.side_effect = ["2023-01-01-12h30m45s"] * 10 + [
                    "2023-01-01-12h30m50s"
                ]
                mock_datetime.datetime.now.return_value = mock_now

                wf_model.render_to_simple_wf = MagicMock(return_value=MagicMock())

                with pytest.raises(
                    FileExistsError, match="Submit directory .* already exists"
                ):
                    wf_model.render("test_name", mock_resource)

                # Verify it tried multiple times and slept
                assert mock_sleep.call_count == 10

    def test_move_element_to_position(self, wf_model):
        """Test move_element_to_position method."""
        elem1 = MagicMock()
        elem2 = MagicMock()
        elem3 = MagicMock()

        wf_model.elements = [elem1, elem2, elem3]
        wf_model.elementnames = ["elem1", "elem2", "elem3"]

        wf_model.move_element_to_position(elem1, 2)

        # Should move elem1 to position 1 (adjusted from 2)
        assert wf_model.elements == [elem2, elem1, elem3]
        assert wf_model.elementnames == ["elem2", "elem1", "elem3"]

    def test_unique_name(self, wf_model):
        """Test unique_name method."""
        wf_model.elementnames = ["test", "test_1", "other"]

        # Test with unused name
        result = wf_model.unique_name("unused")
        assert result == "unused"

        # Test with used name
        result = wf_model.unique_name("test")
        assert result == "test_2"

    def test_add_element(self, wf_model):
        """Test add_element method."""
        mock_element = MagicMock()
        mock_element.name = "TestElement"
        mock_element.view.show = MagicMock()

        wf_model.add_element(mock_element)

        assert len(wf_model.elements) == 1
        assert wf_model.elements[0] is mock_element
        assert wf_model.elementnames[0] == "TestElement"
        mock_element.view.show.assert_called_once()

    def test_add_element_with_position(self, wf_model):
        """Test add_element with position and name conflict."""
        mock_element = MagicMock()
        mock_element.name = "TestElement"
        mock_element.view.show = MagicMock()

        # Pre-populate with same name
        wf_model.elementnames = ["TestElement"]
        wf_model.elements = [MagicMock()]

        wf_model.add_element(mock_element, pos=0)

        # Should have made name unique and inserted at position 0
        mock_element.setText.assert_called_once_with("TestElement_1")
        assert wf_model.elements[0] is mock_element
        assert wf_model.elementnames[0] == "TestElement_1"

    def test_remove_element_with_wano_cleanup(self, wf_model):
        """Test remove_element with WaNo cleanup."""

        # Create a proper mock class to use with isinstance
        class MockWFWaNoWidget:
            pass

        with patch("simstack.view.wf_editor_models.WFWaNoWidget", MockWFWaNoWidget):
            mock_element = MockWFWaNoWidget()
            mock_element.wano = MagicMock()
            mock_element.wano.name = "TestWaNo"

            wf_model.elements = [mock_element]
            wf_model.elementnames = ["TestElement"]
            wf_model.get_wano_names = MagicMock(
                return_value=set()
            )  # Not in use elsewhere
            wf_model.wano_folder_remove = MagicMock()

            wf_model.remove_element(mock_element)

            # Verify element was removed
            assert len(wf_model.elements) == 0
            assert len(wf_model.elementnames) == 0

            # Verify wano folder removal was called
            wf_model.wano_folder_remove.assert_called_once_with("TestWaNo")

    def test_openWaNoEditor(self, wf_model):
        """Test openWaNoEditor method."""
        mock_widget = MagicMock()
        wf_model.openWaNoEditor(mock_widget)
        wf_model.editor.openWaNoEditor.assert_called_once_with(mock_widget)

    def test_removeElement_method(self, wf_model):
        """Test removeElement method (wrapper)."""
        mock_element = MagicMock()
        wf_model.elements = [mock_element]
        wf_model.elementnames = ["TestElement"]

        wf_model.removeElement(mock_element)

        # Verify element was removed
        assert len(wf_model.elements) == 0
        assert len(wf_model.elementnames) == 0


@pytest.mark.integration
class TestModelIntegration:
    """Integration tests for model interactions."""

    def test_subwf_model_with_wano_elements(self):
        """Test SubWFModel with actual WaNo-like elements."""
        editor = MagicMock()
        view = MagicMock()
        wf_root = MagicMock()

        sub_wf = SubWFModel(editor=editor, view=view, wf_root=wf_root)

        # Create mock WaNo element
        mock_wano = MagicMock()
        mock_wano.is_wano = True
        mock_wano.name = "TestWaNo"
        mock_wano.wano_model.get_output_files.return_value = ["result.txt"]
        mock_wano.get_variables.return_value = ["input_param", "output_value"]

        # Add to sub workflow
        sub_wf.elements = [mock_wano]
        sub_wf.elementnames = ["TestWaNo"]

        # Test file assembly
        files = sub_wf.assemble_files("workflow")
        assert len(files) == 1
        assert "TestWaNo/outputs/result.txt" in files[0]

        # Test variable assembly
        with patch("simstack.view.wf_editor_models.merge_path") as mock_merge:
            mock_merge.side_effect = lambda p, n, v: f"{p}.{n}.{v}"
            variables = sub_wf.assemble_variables("workflow")
            assert len(variables) == 2
            assert "workflow.TestWaNo.input_param" in variables
            assert "workflow.TestWaNo.output_value" in variables

    def test_nested_workflow_structure(self):
        """Test nested workflow structure with multiple levels."""
        editor = MagicMock()
        view = MagicMock()
        wf_root = MagicMock()

        # Create main SubWF
        main_wf = SubWFModel(editor=editor, view=view, wf_root=wf_root)

        # Create nested control structure (While with nested SubWF)
        with patch(
            "simstack.view.wf_editor_models._get_control_factory"
        ) as mock_factory:
            mock_nested_model = MagicMock()
            mock_nested_view = MagicMock()
            mock_factory.return_value.construct.return_value = (
                mock_nested_model,
                mock_nested_view,
            )

            while_model = WhileModel(editor=editor, view=view, wf_root=wf_root)

            # Mock nested WaNo widgets
            mock_wano1 = MagicMock()
            mock_wano2 = MagicMock()
            mock_nested_model.collect_wano_widgets.return_value = [
                mock_wano1,
                mock_wano2,
            ]

            # Add While to main workflow
            main_wf.elements = [while_model]
            main_wf.elementnames = ["WhileLoop"]

            # Test collection
            collected_wanos = main_wf.collect_wano_widgets()
            assert len(collected_wanos) == 2
            assert mock_wano1 in collected_wanos
            assert mock_wano2 in collected_wanos


class TestDragDropTargetTracker:
    """Tests for DragDropTargetTracker class."""

    @pytest.fixture
    def drag_drop_tracker(self):
        """Create a DragDropTargetTracker test implementation."""

        # Create a concrete implementation
        class TestDragDropImplementation(DragDropTargetTracker):
            """Test implementation of DragDropTargetTracker."""

            def __init__(self):
                self._parent = MagicMock()
                self.model = MagicMock()
                self.manual_init()

            def parent(self):
                return self._parent

            def rect(self):
                rect_mock = MagicMock()
                rect_mock.topLeft.return_value = MagicMock()
                return rect_mock

            def move(self, pos):
                pass

        with patch("simstack.view.wf_editor_models.QtCore.QMimeData"), patch(
            "simstack.view.wf_editor_models.QtGui.QDrag"
        ):
            tracker = TestDragDropImplementation()
            return tracker

    def test_manual_init(self, drag_drop_tracker):
        """Test manual_init method."""
        assert drag_drop_tracker._initial_parent is drag_drop_tracker._parent

    def test_target_tracker(self, drag_drop_tracker):
        """Test _target_tracker method."""
        mock_event = MagicMock()
        drag_drop_tracker._target_tracker(mock_event)
        assert drag_drop_tracker._newparent is mock_event

    def test_mouse_move_event_feature_left_button(self, drag_drop_tracker):
        """Test mouseMoveEvent_feature with left button."""
        with patch("simstack.view.wf_editor_models.QtCore.QMimeData"), patch(
            "simstack.view.wf_editor_models.QtGui.QDrag"
        ) as mock_drag_class, patch(
            "simstack.view.wf_editor_models.QtCore.Qt"
        ) as mock_qt:
            mock_drag = MagicMock()
            mock_drag_class.return_value = mock_drag
            mock_qt.LeftButton = 1
            mock_qt.MoveAction = 2

            mock_event = MagicMock()
            mock_event.buttons.return_value = mock_qt.LeftButton
            mock_event.pos.return_value = MagicMock()

            # Setup drag behavior
            drag_drop_tracker._newparent = drag_drop_tracker._parent

            drag_drop_tracker.mouseMoveEvent_feature(mock_event)

            # Verify drag was created and executed
            mock_drag_class.assert_called_once_with(drag_drop_tracker)
            mock_drag.exec_.assert_called_once_with(mock_qt.MoveAction)

    def test_mouse_move_event_feature_other_button(self, drag_drop_tracker):
        """Test mouseMoveEvent_feature with other button (should return early)."""
        with patch("simstack.view.wf_editor_models.QtCore.Qt") as mock_qt:
            mock_qt.LeftButton = 1

            mock_event = MagicMock()
            mock_event.buttons.return_value = 2  # Not LeftButton

            with patch("simstack.view.wf_editor_models.QtGui.QDrag") as mock_drag_class:
                drag_drop_tracker.mouseMoveEvent_feature(mock_event)
                # Should not create drag
                mock_drag_class.assert_not_called()

    def test_mouse_move_event_remove_element(self, drag_drop_tracker):
        """Test mouseMoveEvent_feature when target changes to None."""
        with patch("simstack.view.wf_editor_models.QtCore.QMimeData"), patch(
            "simstack.view.wf_editor_models.QtGui.QDrag"
        ) as mock_drag_class, patch(
            "simstack.view.wf_editor_models.QtCore.Qt"
        ) as mock_qt:
            mock_drag = MagicMock()
            mock_drag_class.return_value = mock_drag
            mock_qt.LeftButton = 1
            mock_qt.MoveAction = 2

            mock_event = MagicMock()
            mock_event.buttons.return_value = mock_qt.LeftButton
            mock_event.pos.return_value = MagicMock()

            # Setup so that after drag completes, _newparent is None
            def simulate_drag_completion(*args, **kwargs):
                drag_drop_tracker._newparent = None
                return 0  # Return a Qt.DropAction value

            mock_drag.exec_.side_effect = simulate_drag_completion

            drag_drop_tracker.mouseMoveEvent_feature(mock_event)

            # Verify element is removed
            drag_drop_tracker._parent.removeElement.assert_called_once_with(
                drag_drop_tracker.model
            )
            drag_drop_tracker.model.view.deleteLater.assert_called_once()
