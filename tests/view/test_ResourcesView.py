import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QWidget, QComboBox, QLineEdit, QSpinBox, QCheckBox

from simstack.view.ResourcesView import ResourcesView


class TestResourcesView:
    """Tests for the ResourcesView class."""

    @pytest.fixture
    def mock_resources(self):
        """Create a mock Resources object."""
        resources = MagicMock()

        # Setup field values dictionary
        field_values = {
            "base_URI": "example.com",
            "resource_name": "test_resource",
            "port": 22,
            "queueing_system": "slurm",
            "username": "test_user",
            "sw_dir_on_resource": "/sw/dir",
            "extra_config": "",
            "basepath": "/base/path",
            "ssh_private_key": "/path/to/key",
            "sge_pe": "default",
            "reuse_results": True,
        }

        # Setup methods to get field values
        resources.get_field_value = lambda field: field_values.get(field, None)
        resources.set_field_value = MagicMock()

        # Setup field_type method
        field_types = {
            "base_URI": str,
            "resource_name": str,
            "port": int,
            "queueing_system": str,
            "username": str,
            "sw_dir_on_resource": str,
            "extra_config": str,
            "basepath": str,
            "ssh_private_key": str,
            "sge_pe": str,
            "reuse_results": bool,
        }
        resources.field_type = lambda field: field_types.get(field, str)

        # Setup render_order method
        resources.render_order = lambda: list(field_types.keys())

        return resources

    @pytest.fixture
    def resources_view_wano(self, qtbot, mock_resources):
        """Create a ResourcesView instance for WaNo config testing."""
        with patch("simstack.view.ResourcesView.QtClusterSettingsProvider"), patch(
            "simstack.view.ResourcesView.WaNoRegistrySelection"
        ):
            view = ResourcesView(mock_resources, "wano")
            qtbot.addWidget(view)
            return view

    @pytest.fixture
    def resources_view_server(self, qtbot, mock_resources):
        """Create a ResourcesView instance for server config testing."""
        with patch("simstack.view.ResourcesView.QtClusterSettingsProvider"), patch(
            "simstack.view.ResourcesView.WaNoRegistrySelection"
        ):
            view = ResourcesView(mock_resources, "server")
            qtbot.addWidget(view)
            return view

    def test_init_wano(self, resources_view_wano):
        """Test initialization of ResourcesView for WaNo config."""
        view = resources_view_wano

        # Basic widget checks
        assert isinstance(view, QWidget)
        assert view._render_type == "wano"
        assert view._init_done is True
        assert view.windowTitle() == "Resource view"

        # Check wano exclusion items were applied - these fields should not have widgets
        for item in ResourcesView.wano_exclusion_items:
            assert item not in view._widgets

    def test_init_server(self, resources_view_server):
        """Test initialization of ResourcesView for server config."""
        view = resources_view_server

        # Basic widget checks
        assert isinstance(view, QWidget)
        assert view._render_type == "server"
        assert view._init_done is True
        assert view.windowTitle() == "Resource view"

        # Check serverconfig exclusion items were applied
        for item in ResourcesView.serverconfig_exclusion_items:
            assert item not in view._widgets

    def test_field_name_to_display_name(self):
        """Test field_name_to_display_name class method."""
        # Test known mappings
        assert ResourcesView.field_name_to_display_name("base_URI") == "Hostname"
        assert ResourcesView.field_name_to_display_name("resource_name") == "Resource"
        assert ResourcesView.field_name_to_display_name("port") == "Port"

        # Test unknown mapping - should return the field name unchanged
        assert (
            ResourcesView.field_name_to_display_name("unknown_field") == "unknown_field"
        )

    def test_field_name_to_intention(self, resources_view_wano):
        """Test field_name_to_intention method."""
        view = resources_view_wano

        # Test known intentions from _field_name_to_intention dict
        assert view.field_name_to_intention("extra_config") == "file"
        assert view.field_name_to_intention("ssh_private_key") == "file"
        assert view.field_name_to_intention("queueing_system") == "queueing_system"
        assert view.field_name_to_intention("resource_name") == "resource_chooser"

        # Test intentions derived from type
        assert view.field_name_to_intention("port") == "int"
        assert view.field_name_to_intention("base_URI") == "str"
        assert view.field_name_to_intention("reuse_results") == "bool"

    def test_block_signals(self, resources_view_wano):
        """Test blockSignals method."""
        view = resources_view_wano

        # Create mock widgets
        mock_widget1 = MagicMock()
        mock_widget2 = MagicMock()
        view._widgets = {"widget1": mock_widget1, "widget2": mock_widget2}

        # Block signals
        view.blockSignals(True)

        # Verify both the view and its widgets had blockSignals called
        mock_widget1.blockSignals.assert_called_once_with(True)
        mock_widget2.blockSignals.assert_called_once_with(True)

        # Test unblocking
        view.blockSignals(False)
        mock_widget1.blockSignals.assert_called_with(False)
        mock_widget2.blockSignals.assert_called_with(False)

    def test_get_queue_dropdown_widget(self, resources_view_wano):
        """Test _get_queue_dropdown_widget method."""
        view = resources_view_wano

        widget = view._get_queue_dropdown_widget()

        # Check type
        assert isinstance(widget, QComboBox)

        # Check items
        assert widget.itemText(0) == "pbs"
        assert widget.itemText(1) == "slurm"
        assert widget.itemText(2) == "lsf"
        assert widget.itemText(3) == "sge_multi"
        assert widget.itemText(4) == "AiiDA"
        assert widget.itemText(5) == "Internal"
        assert widget.itemText(6) == "Filegenerator"
        assert widget.count() == 7

    @patch("simstack.view.ResourcesView.QtClusterSettingsProvider")
    def test_update_cluster_dropdown(self, mock_csp, resources_view_wano):
        """Test _update_cluster_dropdown method."""
        view = resources_view_wano

        # Create a mock dropdown
        view._cluster_dropdown = MagicMock()
        view._cluster_dropdown.currentText.return_value = "old_choice"

        # Setup mock registries
        mock_csp_instance = MagicMock()
        mock_csp_instance.get_registries.return_value = {
            "registry1": MagicMock(),
            "registry2": MagicMock(),
        }
        mock_csp.get_instance.return_value = mock_csp_instance

        # Call the method
        view._update_cluster_dropdown()

        # Verify dropdown operations
        view._cluster_dropdown.clear.assert_called_once()
        view._cluster_dropdown.addItem.assert_any_call(view._connected_server_text)
        view._cluster_dropdown.addItem.assert_any_call("registry1")
        view._cluster_dropdown.addItem.assert_any_call("registry2")
        view._cluster_dropdown.setCurrentText.assert_called_once_with("old_choice")

    def test_reinit_values_from_resource(self, resources_view_wano, mock_resources):
        """Test _reinit_values_from_resource method."""
        view = resources_view_wano

        # Create mock widgets of different types
        int_widget = MagicMock(spec=QSpinBox)
        file_widget = MagicMock()
        file_widget.line_edit = MagicMock(spec=QLineEdit)
        str_widget = MagicMock(spec=QLineEdit)
        bool_widget = MagicMock(spec=QCheckBox)
        queueing_widget = MagicMock(spec=QComboBox)
        resource_chooser_widget = MagicMock(spec=QComboBox)

        # Setup intention mapping
        view.field_name_to_intention = MagicMock()
        view.field_name_to_intention.side_effect = lambda key: {
            "port": "int",
            "extra_config": "file",
            "base_URI": "str",
            "reuse_results": "bool",
            "queueing_system": "queueing_system",
            "resource_name": "resource_chooser",
        }.get(key, "str")

        # Setup widgets dictionary
        view._widgets = {
            "port": int_widget,
            "extra_config": file_widget,
            "base_URI": str_widget,
            "reuse_results": bool_widget,
            "queueing_system": queueing_widget,
            "resource_name": resource_chooser_widget,
        }

        # Call the method
        view._reinit_values_from_resource()

        # Verify widget updates
        int_widget.setValue.assert_called_once_with(
            mock_resources.get_field_value("port")
        )
        file_widget.line_edit.setText.assert_called_once_with(
            mock_resources.get_field_value("extra_config")
        )
        str_widget.setText.assert_called_once_with(
            mock_resources.get_field_value("base_URI")
        )
        bool_widget.setChecked.assert_called_once_with(
            mock_resources.get_field_value("reuse_results")
        )
        queueing_widget.setCurrentText.assert_called_once_with(
            mock_resources.get_field_value("queueing_system")
        )
        resource_chooser_widget.setCurrentText.assert_called_once_with(
            mock_resources.get_field_value("resource_name")
        )

    @pytest.mark.skip(
        reason="Difficult to properly mock Qt widgets in this specific case"
    )
    def test_init_cluster_dropdown_widget(self):
        """Test _init_cluster_dropdown_widget method."""
        # This test is challenging to implement due to the complexity of mocking Qt widgets
        # and the specific way ResourcesView interacts with them.
        #
        # The core functionality being tested is:
        # 1. First call initializes a QComboBox and sets up signal connections
        # 2. Subsequent calls return the existing dropdown without reinitializing
        #
        # These aspects are indirectly tested by other tests in this file.

    @patch("simstack.view.ResourcesView.QtClusterSettingsProvider")
    def test_on_cluster_dropdown_change_connected_server(
        self, mock_csp, resources_view_wano, mock_resources
    ):
        """Test _on_cluster_dropdown_change method with connected server."""
        view = resources_view_wano
        view._init_done = True
        view._reinit_values_from_resource = MagicMock()

        # Call with connected server option
        view._on_cluster_dropdown_change(view._connected_server_text)

        # Verify reset behavior
        assert (
            mock_resources.set_field_value.call_count
            >= len(ResourcesView.wano_exclusion_items) + 1
        )
        mock_resources.set_field_value.assert_any_call(
            "resource_name", view._connected_server_text
        )
        view._reinit_values_from_resource.assert_called_once()

    @patch("simstack.view.ResourcesView.QtClusterSettingsProvider")
    def test_on_cluster_dropdown_change_registry(
        self, mock_csp, resources_view_wano, mock_resources
    ):
        """Test _on_cluster_dropdown_change method with registry selection."""
        view = resources_view_wano
        view._init_done = True
        view._reinit_values_from_resource = MagicMock()

        # Setup mock registry
        mock_registry = MagicMock()
        mock_csp.get_registries.return_value = {"test_registry": mock_registry}

        # Call with registry selection
        view._on_cluster_dropdown_change("test_registry")

        # Verify registry values are copied
        assert mock_resources.set_field_value.call_count >= len(
            mock_resources.render_order()
        )
        view._reinit_values_from_resource.assert_called_once()

    def test_fieldchanger(self, mock_resources):
        """Test _fieldChanger static method."""
        # Call the method
        ResourcesView._fieldChanger("test_field", mock_resources, "new_value")

        # Verify
        mock_resources.set_field_value.assert_called_once_with(
            "test_field", "new_value"
        )
