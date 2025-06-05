import pytest
from unittest.mock import MagicMock, patch

from simstack.view.wf_editor_models import (
    linuxjoin,
    merge_path,
    SubmitType,
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
