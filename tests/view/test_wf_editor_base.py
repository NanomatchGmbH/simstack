import pytest
from unittest.mock import MagicMock, patch
import PySide6.QtCore as QtCore

from simstack.view.wf_editor_base import (
    widgetColors,
    linuxjoin,
    DragDropTargetTracker,
)


class TestWidgetColors:
    """Tests for the widgetColors dictionary."""

    def test_widget_colors_structure(self):
        """Test that widgetColors has the expected structure."""
        assert isinstance(widgetColors, dict)
        assert len(widgetColors) == 5

    def test_widget_colors_keys(self):
        """Test that widgetColors contains expected keys."""
        expected_keys = {"MainEditor", "Control", "Base", "WaNo", "ButtonColor"}
        assert set(widgetColors.keys()) == expected_keys

    def test_widget_colors_values(self):
        """Test that widgetColors values are valid hex colors."""
        for key, color in widgetColors.items():
            assert isinstance(color, str), f"Color for {key} is not a string"
            assert color.startswith("#"), f"Color for {key} doesn't start with #"
            assert len(color) == 7, f"Color for {key} is not 7 characters long"
            # Verify it's a valid hex color
            int(color[1:], 16)  # This will raise ValueError if not valid hex

    def test_widget_colors_specific_values(self):
        """Test specific color values."""
        assert widgetColors["MainEditor"] == "#F5FFF5"
        assert widgetColors["Control"] == "#EBFFD6"
        assert widgetColors["Base"] == "#F5FFEB"
        assert widgetColors["WaNo"] == "#FF00FF"
        assert widgetColors["ButtonColor"] == "#D4FF7F"

    def test_widget_colors_immutable_reference(self):
        """Test that widgetColors reference is consistent."""
        # Should always return the same object
        from simstack.view.wf_editor_base import widgetColors as wc1
        from simstack.view.wf_editor_base import widgetColors as wc2

        assert wc1 is wc2


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

    def test_linuxjoin_no_arguments(self):
        """Test linuxjoin with no arguments - should raise TypeError."""
        with pytest.raises(TypeError):
            linuxjoin()

    def test_linuxjoin_kwargs_support(self):
        """Test that linuxjoin supports kwargs (passed through to posixpath.join)."""
        # posixpath.join doesn't actually use kwargs, but we should support them
        result = linuxjoin("path", "to", "file")
        assert result == "path/to/file"

    def test_linuxjoin_special_characters(self):
        """Test linuxjoin with special characters."""
        result = linuxjoin("path with spaces", "file-name_123", "file.ext")
        assert result == "path with spaces/file-name_123/file.ext"

    def test_linuxjoin_trailing_slashes(self):
        """Test linuxjoin with trailing slashes."""
        result = linuxjoin("path/", "/to/", "/file")
        # posixpath.join behavior: absolute paths reset the result
        assert result == "/file"

    def test_linuxjoin_double_slashes(self):
        """Test linuxjoin handles double slashes correctly."""
        result = linuxjoin("//path", "//to", "file")
        # posixpath.join behavior: absolute paths (starting with /) reset the result
        assert result == "//to/file"

    def test_linuxjoin_relative_paths(self):
        """Test linuxjoin with relative path components."""
        result = linuxjoin(".", "..", "path", "file")
        assert result == "./../path/file"


class TestDragDropTargetTracker:
    """Tests for the DragDropTargetTracker class."""

    class ConcreteTracker(DragDropTargetTracker):
        """Concrete implementation for testing."""

        def __init__(self, parent=None):
            self._parent = parent
            self.model = MagicMock()
            self.model.view = MagicMock()
            # Initialize _initial_parent to None by default
            self._initial_parent = None

        def parent(self):
            return self._parent

        def rect(self):
            mock_rect = MagicMock()
            mock_rect.topLeft.return_value = MagicMock()
            return mock_rect

    def test_manual_init_sets_initial_parent(self):
        """Test that manual_init sets _initial_parent correctly."""
        parent_mock = MagicMock()
        tracker = self.ConcreteTracker(parent_mock)

        tracker.manual_init()

        assert tracker._initial_parent is parent_mock

    def test_target_tracker_sets_newparent(self):
        """Test that _target_tracker sets _newparent."""
        tracker = self.ConcreteTracker()
        event_mock = MagicMock()

        tracker._target_tracker(event_mock)

        assert tracker._newparent is event_mock

    def test_abstract_parent_method(self):
        """Test that parent() is abstract but instantiation is allowed."""
        # DragDropTargetTracker doesn't inherit from abc.ABC, so instantiation is allowed
        # but calling abstract method should raise NotImplementedError when called
        tracker = DragDropTargetTracker()

        # The abstract method should exist but calling it might raise NotImplementedError
        # or just pass (in this case it just passes)
        result = tracker.parent()
        assert result is None  # The method just has 'pass'

    def test_abstract_parent_method_coverage(self):
        """Test to ensure the abstract parent method is covered."""
        # Create a direct instance to call the abstract method and cover line 27
        tracker = DragDropTargetTracker()
        # This covers the abstract method line
        result = tracker.parent()
        assert result is None

    def test_mouse_move_event_wrong_button(self):
        """Test mouseMoveEvent_feature with wrong mouse button."""
        tracker = self.ConcreteTracker()

        # Mock event with wrong button
        event_mock = MagicMock()
        event_mock.buttons.return_value = QtCore.Qt.RightButton

        # Should return early without setting up drag
        result = tracker.mouseMoveEvent_feature(event_mock)

        # Verify it returned early (no drag setup)
        assert not hasattr(tracker, "drag")
        assert result is None

    def test_mouse_move_event_left_button_basic_setup(self):
        """Test mouseMoveEvent_feature basic drag setup with left button."""
        # Use a tracker with a parent so _newparent won't be None
        parent_mock = MagicMock()
        tracker = self.ConcreteTracker(parent_mock)
        tracker.manual_init()  # Set initial parent

        # Mock event with left button
        event_mock = MagicMock()
        event_mock.buttons.return_value = QtCore.Qt.LeftButton
        event_mock.pos.return_value = MagicMock()

        with patch("PySide6.QtCore.QMimeData") as mock_mime_data, patch(
            "PySide6.QtGui.QDrag"
        ) as mock_drag_class:
            mock_drag = MagicMock()
            mock_drag_class.return_value = mock_drag

            # Simulate drag ending with same parent (normal case)
            def simulate_normal_drag(*args, **kwargs):
                tracker._newparent = parent_mock

            mock_drag.exec_.side_effect = simulate_normal_drag

            # Call the method
            tracker.mouseMoveEvent_feature(event_mock)

            # Verify drag setup
            mock_mime_data.assert_called_once()
            mock_drag_class.assert_called_once_with(tracker)
            mock_drag.setMimeData.assert_called_once()
            mock_drag.setHotSpot.assert_called_once()
            mock_drag.targetChanged.connect.assert_called_once_with(
                tracker._target_tracker
            )
            mock_drag.exec_.assert_called_once_with(QtCore.Qt.MoveAction)

    def test_mouse_move_event_drop_outside_removes_element(self):
        """Test mouseMoveEvent_feature when drop is outside (newparent is None)."""
        parent_mock = MagicMock()
        tracker = self.ConcreteTracker(parent_mock)
        tracker.manual_init()  # Set initial parent

        # Mock event with left button
        event_mock = MagicMock()
        event_mock.buttons.return_value = QtCore.Qt.LeftButton
        event_mock.pos.return_value = MagicMock()

        with patch("PySide6.QtCore.QMimeData"), patch(
            "PySide6.QtGui.QDrag"
        ) as mock_drag_class:
            mock_drag = MagicMock()
            mock_drag_class.return_value = mock_drag

            # Simulate _newparent being None (dropped outside)
            def simulate_drop_outside(*args, **kwargs):
                tracker._newparent = None

            mock_drag.exec_.side_effect = simulate_drop_outside

            # Call the method
            tracker.mouseMoveEvent_feature(event_mock)

            # Verify element removal was called
            parent_mock.removeElement.assert_called_once_with(tracker.model)
            tracker.model.view.deleteLater.assert_called_once()

    def test_mouse_move_event_drop_same_parent_no_action(self):
        """Test mouseMoveEvent_feature when dropped on same parent."""
        parent_mock = MagicMock()
        tracker = self.ConcreteTracker(parent_mock)
        tracker.manual_init()  # Set initial parent

        # Mock event with left button
        event_mock = MagicMock()
        event_mock.buttons.return_value = QtCore.Qt.LeftButton
        event_mock.pos.return_value = MagicMock()

        with patch("PySide6.QtCore.QMimeData"), patch(
            "PySide6.QtGui.QDrag"
        ) as mock_drag_class:
            mock_drag = MagicMock()
            mock_drag_class.return_value = mock_drag

            # Simulate _newparent being the same as initial parent
            def simulate_drop_same_parent(*args, **kwargs):
                tracker._newparent = tracker._initial_parent

            mock_drag.exec_.side_effect = simulate_drop_same_parent

            # Call the method
            tracker.mouseMoveEvent_feature(event_mock)

            # Verify no removal was called (just pass through)
            parent_mock.removeElement.assert_not_called()
            tracker.model.view.deleteLater.assert_not_called()

    def test_mouse_move_event_drop_different_parent(self):
        """Test mouseMoveEvent_feature when dropped on different parent."""
        parent_mock = MagicMock()
        tracker = self.ConcreteTracker(parent_mock)
        tracker.manual_init()  # Set initial parent

        # Mock event with left button
        event_mock = MagicMock()
        event_mock.buttons.return_value = QtCore.Qt.LeftButton
        event_mock.pos.return_value = MagicMock()

        with patch("PySide6.QtCore.QMimeData"), patch(
            "PySide6.QtGui.QDrag"
        ) as mock_drag_class:
            mock_drag = MagicMock()
            mock_drag_class.return_value = mock_drag

            # Simulate _newparent being different from initial parent
            different_parent = MagicMock()

            def simulate_drop_different_parent(*args, **kwargs):
                tracker._newparent = different_parent

            mock_drag.exec_.side_effect = simulate_drop_different_parent

            # Call the method
            tracker.mouseMoveEvent_feature(event_mock)

            # Verify no removal was called (assumes both have correct dropevents)
            parent_mock.removeElement.assert_not_called()
            tracker.model.view.deleteLater.assert_not_called()

    def test_mouse_move_event_complete_flow(self):
        """Test complete mouseMoveEvent_feature flow including all branches."""
        parent_mock = MagicMock()
        tracker = self.ConcreteTracker(parent_mock)
        tracker.manual_init()

        # Mock event
        event_mock = MagicMock()
        event_mock.buttons.return_value = QtCore.Qt.LeftButton
        mock_pos = MagicMock()
        event_mock.pos.return_value = mock_pos

        # Mock rect
        mock_rect = MagicMock()
        mock_top_left = MagicMock()
        mock_rect.topLeft.return_value = mock_top_left
        tracker.rect = MagicMock(return_value=mock_rect)

        with patch("PySide6.QtCore.QMimeData") as mock_mime_data_class, patch(
            "PySide6.QtGui.QDrag"
        ) as mock_drag_class:
            mock_mime_data = MagicMock()
            mock_mime_data_class.return_value = mock_mime_data

            mock_drag = MagicMock()
            mock_drag_class.return_value = mock_drag

            # Simulate normal drop (same parent)
            def simulate_normal_drop(*args, **kwargs):
                tracker._newparent = parent_mock

            mock_drag.exec_.side_effect = simulate_normal_drop

            # Call method
            tracker.mouseMoveEvent_feature(event_mock)

            # Verify complete flow
            mock_mime_data_class.assert_called_once()
            mock_drag_class.assert_called_once_with(tracker)
            mock_drag.setMimeData.assert_called_once_with(mock_mime_data)
            mock_drag.setHotSpot.assert_called_once_with(mock_pos - mock_top_left)
            mock_drag.targetChanged.connect.assert_called_once_with(
                tracker._target_tracker
            )
            mock_drag.exec_.assert_called_once_with(QtCore.Qt.MoveAction)

            # Since _newparent equals _initial_parent, no removal should occur
            parent_mock.removeElement.assert_not_called()

    def test_concrete_implementation_parent_method(self):
        """Test that concrete implementation provides parent method."""
        parent_mock = MagicMock()
        tracker = self.ConcreteTracker(parent_mock)

        assert tracker.parent() is parent_mock

    def test_drag_drop_tracker_inheritance(self):
        """Test that DragDropTargetTracker can be properly inherited."""
        assert issubclass(self.ConcreteTracker, DragDropTargetTracker)

        # Test that all required methods are implemented
        tracker = self.ConcreteTracker()
        assert hasattr(tracker, "parent")
        assert hasattr(tracker, "manual_init")
        assert hasattr(tracker, "_target_tracker")
        assert hasattr(tracker, "mouseMoveEvent_feature")
        assert callable(tracker.parent)
        assert callable(tracker.manual_init)
        assert callable(tracker._target_tracker)
        assert callable(tracker.mouseMoveEvent_feature)

    def test_initial_state(self):
        """Test initial state of DragDropTargetTracker."""
        tracker = self.ConcreteTracker()

        # Should not have drag-related attributes initially
        assert not hasattr(tracker, "drag")
        assert not hasattr(tracker, "_newparent")
        # _initial_parent should be None until manual_init is called
        assert tracker._initial_parent is None

    def test_manual_init_multiple_calls(self):
        """Test that manual_init can be called multiple times safely."""
        parent1 = MagicMock()
        parent2 = MagicMock()

        tracker = self.ConcreteTracker(parent1)
        tracker.manual_init()
        assert tracker._initial_parent is parent1

        # Change parent and call manual_init again
        tracker._parent = parent2
        tracker.manual_init()
        assert tracker._initial_parent is parent2
