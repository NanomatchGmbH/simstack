import pytest
from unittest.mock import MagicMock, patch, call

from simstack.view.wf_editor_factory import ControlFactory


class TestControlFactory:
    """Tests for the ControlFactory class."""

    def test_n_t_c_mapping_completeness(self):
        """Test that n_t_c mapping contains all expected control types."""
        expected_controls = {
            "ForEach",
            "AdvancedFor",
            "If",
            "While",
            "Variable",
            "Parallel",
            "SubWorkflow",
        }

        assert set(ControlFactory.n_t_c.keys()) == expected_controls

        # Verify each entry has model and view classes
        for name, (model_class, view_class) in ControlFactory.n_t_c.items():
            assert model_class is not None, f"Model class missing for {name}"
            assert view_class is not None, f"View class missing for {name}"
            assert hasattr(model_class, "__name__"), f"Model class invalid for {name}"
            assert hasattr(view_class, "__name__"), f"View class invalid for {name}"

    def test_n_t_c_mapping_correct_classes(self):
        """Test that n_t_c mapping contains correct model/view pairs."""
        # Test ForEach mapping
        model_class, view_class = ControlFactory.n_t_c["ForEach"]
        assert model_class.__name__ == "ForEachModel"
        assert view_class.__name__ == "ForEachView"

        # Test AdvancedFor mapping
        model_class, view_class = ControlFactory.n_t_c["AdvancedFor"]
        assert model_class.__name__ == "AdvancedForEachModel"
        assert view_class.__name__ == "AdvancedForEachView"

        # Test If mapping
        model_class, view_class = ControlFactory.n_t_c["If"]
        assert model_class.__name__ == "IfModel"
        assert view_class.__name__ == "IfView"

        # Test While mapping
        model_class, view_class = ControlFactory.n_t_c["While"]
        assert model_class.__name__ == "WhileModel"
        assert view_class.__name__ == "WhileView"

        # Test Variable mapping
        model_class, view_class = ControlFactory.n_t_c["Variable"]
        assert model_class.__name__ == "VariableModel"
        assert view_class.__name__ == "VariableView"

        # Test Parallel mapping
        model_class, view_class = ControlFactory.n_t_c["Parallel"]
        assert model_class.__name__ == "ParallelModel"
        assert view_class.__name__ == "ParallelView"

        # Test SubWorkflow mapping
        model_class, view_class = ControlFactory.n_t_c["SubWorkflow"]
        assert model_class.__name__ == "SubWFModel"
        assert view_class.__name__ == "SubWorkflowView"

    def test_name_to_class_valid_names(self):
        """Test name_to_class method with valid control names."""
        for name in ControlFactory.n_t_c.keys():
            model_class, view_class = ControlFactory.name_to_class(name)
            expected_model, expected_view = ControlFactory.n_t_c[name]
            assert model_class is expected_model
            assert view_class is expected_view

    def test_name_to_class_invalid_name(self):
        """Test name_to_class method with invalid control name."""
        with pytest.raises(KeyError):
            ControlFactory.name_to_class("NonExistentControl")

        with pytest.raises(KeyError):
            ControlFactory.name_to_class("")

        with pytest.raises(KeyError):
            ControlFactory.name_to_class("InvalidName")

    def test_name_to_class_case_sensitivity(self):
        """Test that name_to_class is case sensitive."""
        with pytest.raises(KeyError):
            ControlFactory.name_to_class("foreach")  # lowercase

        with pytest.raises(KeyError):
            ControlFactory.name_to_class("FOREACH")  # uppercase

    def test_construct_invalid_name(self):
        """Test construct method with invalid control name."""
        qt_parent = MagicMock()
        logical_parent = MagicMock()
        editor = MagicMock()
        wf_root = MagicMock()

        with pytest.raises(KeyError):
            ControlFactory.construct(
                "InvalidControlName", qt_parent, logical_parent, editor, wf_root
            )

    def test_factory_is_class_method(self):
        """Test that factory methods are class methods, not instance methods."""
        # Should be able to call without instantiating
        assert callable(ControlFactory.name_to_class)
        assert callable(ControlFactory.construct)

        # Verify they are class methods (bound to class, not instance)
        assert hasattr(ControlFactory.name_to_class, "__self__")
        assert ControlFactory.name_to_class.__self__ is ControlFactory
        assert hasattr(ControlFactory.construct, "__self__")
        assert ControlFactory.construct.__self__ is ControlFactory

    def test_n_t_c_immutability(self):
        """Test that n_t_c mapping should not be modified."""
        original_mapping = ControlFactory.n_t_c.copy()

        # Get the mapping
        mapping = ControlFactory.n_t_c

        # Verify it's a dict and has expected content
        assert isinstance(mapping, dict)
        assert len(mapping) == 7
        assert mapping == original_mapping

    def test_construct_calls_name_to_class(self):
        """Test that construct method calls name_to_class internally."""
        with patch.object(ControlFactory, "name_to_class") as mock_name_to_class:
            # Setup mock return values
            mock_view_class = MagicMock()
            mock_model_class = MagicMock()
            mock_name_to_class.return_value = (mock_model_class, mock_view_class)

            # Setup mock instances
            mock_view = MagicMock()
            mock_model = MagicMock()
            mock_view_class.return_value = mock_view
            mock_model_class.return_value = mock_model

            # Call construct
            ControlFactory.construct("TestControl", None, None, None, None)

            # Verify name_to_class was called
            mock_name_to_class.assert_called_once_with("TestControl")

    def test_construct_flow_with_mocks(self):
        """Test the complete construct flow using mocks."""
        # Create mock arguments
        qt_parent = MagicMock()
        logical_parent = MagicMock()
        editor = MagicMock()
        wf_root = MagicMock()

        # Create mock classes
        mock_view_class = MagicMock()
        mock_model_class = MagicMock()

        # Create mock instances
        mock_view = MagicMock()
        mock_model = MagicMock()

        # Setup class constructors to return our mock instances
        mock_view_class.return_value = mock_view
        mock_model_class.return_value = mock_model

        # Patch name_to_class to return our mock classes
        with patch.object(
            ControlFactory,
            "name_to_class",
            return_value=(mock_model_class, mock_view_class),
        ):
            result_model, result_view = ControlFactory.construct(
                "TestControl", qt_parent, logical_parent, editor, wf_root
            )

            # Verify view was created with correct arguments
            mock_view_class.assert_called_once_with(
                qt_parent=qt_parent, logical_parent=logical_parent
            )

            # Verify model was created with correct arguments
            mock_model_class.assert_called_once_with(
                editor=editor, view=mock_view, wf_root=wf_root
            )

            # Verify view methods were called
            mock_view.set_model.assert_called_once_with(mock_model)
            mock_view.init_from_model.assert_called_once()

            # Verify return values
            assert result_model is mock_model
            assert result_view is mock_view

    def test_construct_return_tuple(self):
        """Test that construct returns a tuple."""
        with patch.object(ControlFactory, "name_to_class") as mock_name_to_class:
            mock_view_class = MagicMock()
            mock_model_class = MagicMock()
            mock_view = MagicMock()
            mock_model = MagicMock()

            mock_view_class.return_value = mock_view
            mock_model_class.return_value = mock_model
            mock_name_to_class.return_value = (mock_model_class, mock_view_class)

            result = ControlFactory.construct("Test", None, None, None, None)

            assert isinstance(result, tuple)
            assert len(result) == 2
            assert result[0] is mock_model
            assert result[1] is mock_view

    def test_construct_method_call_order(self):
        """Test that construct calls methods in the correct order."""
        with patch.object(ControlFactory, "name_to_class") as mock_name_to_class:
            mock_view_class = MagicMock()
            mock_model_class = MagicMock()
            mock_view = MagicMock()
            mock_model = MagicMock()

            # Create a list to track call order - attach before making calls
            manager = MagicMock()
            manager.attach_mock(mock_view_class, "view_class")
            manager.attach_mock(mock_model_class, "model_class")
            manager.attach_mock(mock_view.set_model, "set_model")
            manager.attach_mock(mock_view.init_from_model, "init_from_model")

            mock_view_class.return_value = mock_view
            mock_model_class.return_value = mock_model
            mock_name_to_class.return_value = (mock_model_class, mock_view_class)

            ControlFactory.construct("Test", None, None, None, None)

            # The expected call order is:
            # 1. view creation
            # 2. model creation
            # 3. view.set_model
            # 4. view.init_from_model
            expected_calls = [
                call.view_class(qt_parent=None, logical_parent=None),
                call.model_class(editor=None, view=mock_view, wf_root=None),
                call.set_model(mock_model),
                call.init_from_model(),
            ]

            assert manager.mock_calls == expected_calls

    def test_all_mapping_entries_are_tuples(self):
        """Test that all entries in n_t_c are tuples of length 2."""
        for name, entry in ControlFactory.n_t_c.items():
            assert isinstance(entry, tuple), f"Entry for {name} is not a tuple"
            assert len(entry) == 2, f"Entry for {name} does not have exactly 2 elements"

    def test_mapping_entries_are_classes(self):
        """Test that all entries in n_t_c contain actual classes."""
        for name, (model_class, view_class) in ControlFactory.n_t_c.items():
            assert isinstance(model_class, type), f"Model for {name} is not a class"
            assert isinstance(view_class, type), f"View for {name} is not a class"

    def test_name_to_class_returns_same_as_direct_access(self):
        """Test that name_to_class returns the same as direct dictionary access."""
        for name in ControlFactory.n_t_c.keys():
            direct_access = ControlFactory.n_t_c[name]
            method_access = ControlFactory.name_to_class(name)
            assert direct_access == method_access

    def test_n_t_c_dictionary_structure(self):
        """Test the structure and content of the n_t_c dictionary."""
        # Test it's a dictionary
        assert isinstance(ControlFactory.n_t_c, dict)

        # Test it has the expected number of entries
        assert len(ControlFactory.n_t_c) == 7

        # Test all keys are strings
        for key in ControlFactory.n_t_c.keys():
            assert isinstance(key, str)

        # Test all values are tuples
        for value in ControlFactory.n_t_c.values():
            assert isinstance(value, tuple)
            assert len(value) == 2
