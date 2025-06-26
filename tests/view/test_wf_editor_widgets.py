from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from simstack.view.wf_editor_widgets import (
    SubmitType,
    WFWaNoWidget,
    WFItemListInterface,
)


class TestSubmitType:
    """Test the SubmitType enum."""

    def test_submit_type_values(self):
        """Test SubmitType enum values."""
        assert SubmitType.SINGLE_WANO.value == 0
        assert SubmitType.WORKFLOW.value == 1


class TestWFWaNoWidgetMethods:
    """Test WFWaNoWidget methods that don't require full widget instantiation."""

    def test_get_xml_structure(self):
        """Test get_xml method returns correct XML structure."""
        widget = WFWaNoWidget.__new__(WFWaNoWidget)
        widget.wano = MagicMock()
        widget.wano.name = "TestWaNo"
        widget.uuid = "test-uuid-123"

        xml = widget.get_xml()

        assert xml.tag == "WaNo"
        assert xml.attrib["type"] == "TestWaNo"
        assert xml.attrib["uuid"] == "test-uuid-123"

    def test_place_elements_does_nothing(self):
        """Test place_elements method does nothing."""
        widget = WFWaNoWidget.__new__(WFWaNoWidget)
        result = widget.place_elements()
        assert result is None

    def test_clear_does_nothing(self):
        """Test clear method does nothing."""
        widget = WFWaNoWidget.__new__(WFWaNoWidget)
        result = widget.clear()
        assert result is None

    def test_get_variables_with_model(self):
        """Test get_variables when wano_model exists."""
        widget = WFWaNoWidget.__new__(WFWaNoWidget)
        widget.wano_model = MagicMock()
        widget.wano_model.get_all_variable_paths.return_value = ["var1", "var2"]

        variables = widget.get_variables()
        assert variables == ["var1", "var2"]
        widget.wano_model.get_all_variable_paths.assert_called_once()

    def test_get_variables_no_model(self):
        """Test get_variables when wano_model is None."""
        widget = WFWaNoWidget.__new__(WFWaNoWidget)
        widget.wano_model = None

        variables = widget.get_variables()
        assert variables == []

    def test_save_delta(self):
        """Test save_delta method."""
        widget = WFWaNoWidget.__new__(WFWaNoWidget)
        widget.uuid = "test-uuid"
        widget.wano_model = MagicMock()

        test_folder = Path("/test/folder")
        expected_outfolder = test_folder / "wano_configurations" / "test-uuid"

        with patch("os.makedirs") as mock_makedirs, patch(
            "builtins.print"
        ) as mock_print:
            widget.save_delta(test_folder)

            mock_makedirs.assert_called_once_with(expected_outfolder, exist_ok=True)
            mock_print.assert_called_once()
            widget.wano_model.save.assert_called_once_with(expected_outfolder)

    def test_read_delta(self):
        """Test _read_delta method."""
        widget = WFWaNoWidget.__new__(WFWaNoWidget)
        widget.wano_model = MagicMock()

        test_folder = Path("/test/folder")
        widget._read_delta(test_folder)

        widget.wano_model.read.assert_called_once_with(test_folder)
        widget.wano_model.update_views_from_models.assert_called_once()

    @patch("simstack.view.wf_editor_widgets.copy.deepcopy")
    def test_render(self, mock_deepcopy):
        """Test render method."""
        widget = WFWaNoWidget.__new__(WFWaNoWidget)
        widget.wano_model = MagicMock()
        widget.wano_model.name = "TestWaNo"
        widget.wf_model = MagicMock()
        widget.wf_model.base_resource_during_render.return_value = "base_resources"

        # Mock render method return
        mock_wem = MagicMock()
        mock_wem.name = "test_wem"
        widget.wano_model.render_and_write_input_files_newmodel.return_value = (
            "jsdl",
            mock_wem,
        )

        # Mock deepcopy
        mock_copied_wem = MagicMock()
        mock_copied_wem.name = "copied_wem"
        mock_copied_wem.resources.overwrite_unset_fields_from_default_resources = (
            MagicMock()
        )
        mock_copied_wem.set_wano_xml = MagicMock()
        mock_deepcopy.return_value = mock_copied_wem

        path_list = ["path1", "path2"]
        output_path_list = ["out1", "out2"]
        basefolder = "/base/folder"
        stageout_basedir = "/stageout"

        with patch("builtins.print") as mock_print:
            jsdl, wem, new_path_list = widget.render(
                path_list, output_path_list, basefolder, stageout_basedir
            )

            # Verify render was called correctly
            widget.wano_model.render_and_write_input_files_newmodel.assert_called_once_with(
                basefolder, stageout_basedir=stageout_basedir
            )

            # Verify deepcopy was called
            mock_deepcopy.assert_called_once_with(mock_wem)

            # Verify resource overwrite
            mock_copied_wem.resources.overwrite_unset_fields_from_default_resources.assert_called_once_with(
                "base_resources"
            )

            # Verify XML was set
            mock_copied_wem.set_wano_xml.assert_called_once_with("TestWaNo.xml")

            # Verify return values
            assert jsdl == "jsdl"
            assert wem == mock_copied_wem
            assert new_path_list == path_list + ["test_wem"]

            # Verify print was called
            mock_print.assert_called_once()


class TestWFItemListInterface:
    """Tests for WFItemListInterface class."""

    @pytest.fixture
    def mock_editor(self):
        """Create a mock editor."""
        return MagicMock()

    @pytest.fixture
    def mock_view(self):
        """Create a mock view."""
        return MagicMock()

    @pytest.fixture
    def item_list_interface(self, mock_editor, mock_view):
        """Create a WFItemListInterface instance."""
        return WFItemListInterface(editor=mock_editor, view=mock_view)

    def test_init(self, item_list_interface, mock_editor, mock_view):
        """Test initialization of WFItemListInterface."""
        assert item_list_interface.is_wano is False
        assert item_list_interface.editor is mock_editor
        assert item_list_interface.view is mock_view
        assert item_list_interface.elements == []
        assert item_list_interface.elementnames == []
        assert item_list_interface.foldername is None

    def test_element_to_name(self, item_list_interface):
        """Test element_to_name method."""
        # Add test elements
        element1 = MagicMock()
        element2 = MagicMock()
        item_list_interface.elements = [element1, element2]
        item_list_interface.elementnames = ["name1", "name2"]

        # Test element_to_name
        assert item_list_interface.element_to_name(element1) == "name1"
        assert item_list_interface.element_to_name(element2) == "name2"

    def test_move_element_to_position_backward(self, item_list_interface):
        """Test move_element_to_position moving backward."""
        # Setup elements
        elem1, elem2, elem3 = MagicMock(), MagicMock(), MagicMock()
        item_list_interface.elements = [elem1, elem2, elem3]
        item_list_interface.elementnames = ["name1", "name2", "name3"]

        # Move element from position 2 to position 0
        item_list_interface.move_element_to_position(elem3, 0)

        # Verify new order
        assert item_list_interface.elements == [elem3, elem1, elem2]
        assert item_list_interface.elementnames == ["name3", "name1", "name2"]

    def test_move_element_to_position_same_position(self, item_list_interface):
        """Test move_element_to_position with same position."""
        # Setup elements
        elem1, elem2, elem3 = MagicMock(), MagicMock(), MagicMock()
        original_elements = [elem1, elem2, elem3]
        original_names = ["name1", "name2", "name3"]
        item_list_interface.elements = original_elements.copy()
        item_list_interface.elementnames = original_names.copy()

        # Move element to same position
        item_list_interface.move_element_to_position(elem2, 1)

        # Should remain unchanged
        assert item_list_interface.elements == original_elements
        assert item_list_interface.elementnames == original_names

    def test_unique_name_no_conflict(self, item_list_interface):
        """Test unique_name with no naming conflict."""
        item_list_interface.elementnames = ["existing1", "existing2"]

        # Test with new name
        result = item_list_interface.unique_name("newname")

        # Should return original name
        assert result == "newname"

    def test_unique_name_with_conflict(self, item_list_interface):
        """Test unique_name with naming conflict."""
        item_list_interface.elementnames = ["testname", "testname_1", "testname_3"]

        # Test with conflicting name
        result = item_list_interface.unique_name("testname")

        # Should return incremented name
        assert result == "testname_2"

    def test_add_element_with_position(self, item_list_interface):
        """Test add_element with specific position."""
        # Setup existing elements
        existing_elem = MagicMock()
        item_list_interface.elements = [existing_elem]
        item_list_interface.elementnames = ["existing"]

        # Create new element
        new_elem = MagicMock()
        new_elem.name = "newelem"
        new_elem.setText = MagicMock()

        # Add at position 0
        item_list_interface.add_element(new_elem, pos=0)

        # Verify insertion
        assert item_list_interface.elements == [new_elem, existing_elem]
        assert item_list_interface.elementnames == ["newelem", "existing"]

    def test_add_element_without_position(self, item_list_interface):
        """Test add_element without specific position."""
        # Create element
        elem = MagicMock()
        elem.text.return_value = "elemname"

        # Add element
        item_list_interface.add_element(elem)

        # Verify appended
        assert item_list_interface.elements == [elem]
        assert item_list_interface.elementnames == ["elemname"]

    def test_remove_element(self, item_list_interface):
        """Test remove_element method."""
        # Setup elements
        elem1, elem2, elem3 = MagicMock(), MagicMock(), MagicMock()
        item_list_interface.elements = [elem1, elem2, elem3]
        item_list_interface.elementnames = ["name1", "name2", "name3"]

        # Remove middle element
        item_list_interface.remove_element(elem2)

        # Verify removal
        assert item_list_interface.elements == [elem1, elem3]
        assert item_list_interface.elementnames == ["name1", "name3"]

    def test_open_wano_editor(self, item_list_interface, mock_editor):
        """Test openWaNoEditor method."""
        widget = MagicMock()

        # Call openWaNoEditor
        item_list_interface.openWaNoEditor(widget)

        # Verify editor method was called
        mock_editor.openWaNoEditor.assert_called_once_with(widget)
