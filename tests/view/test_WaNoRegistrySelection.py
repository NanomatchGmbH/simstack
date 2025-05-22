import pytest
from unittest.mock import patch, MagicMock
import os
from PySide6.QtWidgets import QWidget, QComboBox, QPushButton

from simstack.view.WaNoRegistrySelection import WaNoRegistrySelection


@pytest.mark.skip(
    reason="WaNoRegistrySelection tests need to be completely rewritten to use proper mocks"
)
class TestWaNoRegistrySelection:
    """Tests for the WaNoRegistrySelection class."""

    @pytest.fixture
    def registry_selection(self, qtbot):
        """Create a WaNoRegistrySelection instance with mocked dependencies."""
        # Reset the singleton instance
        WaNoRegistrySelection.instance = None

        # Mock path operations
        with patch(
            "simstack.view.WaNoRegistrySelection.QtClusterSettingsProvider"
        ) as mock_provider, patch(
            "simstack.view.WaNoRegistrySelection.os.path.dirname"
        ) as mock_dirname, patch(
            "simstack.view.WaNoRegistrySelection.os.path.realpath"
        ) as mock_realpath, patch(
            "simstack.view.WaNoRegistrySelection.os.path.join"
        ) as mock_join:
            # Setup mock instance
            mock_instance = MagicMock()
            mock_provider.get_instance.return_value = mock_instance

            # Setup mock registries
            mock_provider.get_registries.return_value = {
                "registry1": MagicMock(),
                "registry2": MagicMock(),
            }

            # Set up mock return values for paths
            mock_dirname.return_value = "/mock/path"
            mock_realpath.return_value = "/mock/path/file"
            mock_join.side_effect = lambda *args: "/".join(args)

            # Create widget with init patched
            with patch.object(
                WaNoRegistrySelection, "_WaNoRegistrySelection__init_ui"
            ), patch.object(
                WaNoRegistrySelection, "_WaNoRegistrySelection__connect_signals"
            ), patch.object(WaNoRegistrySelection, "setStatus"), patch.object(
                WaNoRegistrySelection, "_WaNoRegistrySelection__update_status"
            ):
                parent = QWidget()
                qtbot.addWidget(parent)
                widget = WaNoRegistrySelection(parent)

                # Set up test attributes manually
                widget.registryComboBox = QComboBox()
                widget.isConnectedIcon = QPushButton()
                widget._WaNoRegistrySelection__status = (
                    WaNoRegistrySelection.CONNECTION_STATES.disconnected
                )
                widget._WaNoRegistrySelection__emit_signal = True

                # Add signals to the mocks
                widget.registrySelectionChanged = MagicMock()
                widget.connect_registry = MagicMock()
                widget.disconnect_registry = MagicMock()

                qtbot.addWidget(widget)
                return widget

    def test_init(self, registry_selection):
        """Test initialization of WaNoRegistrySelection."""
        # Verify singleton instance
        assert WaNoRegistrySelection.instance is registry_selection

        # Verify UI components
        assert isinstance(registry_selection.registryComboBox, QComboBox)
        assert isinstance(registry_selection.isConnectedIcon, QPushButton)

        # Verify initial state
        assert registry_selection._WaNoRegistrySelection__emit_signal is True
        assert (
            registry_selection._WaNoRegistrySelection__status
            == WaNoRegistrySelection.CONNECTION_STATES.disconnected
        )

    def test_get_instance(self, registry_selection):
        """Test get_instance class method."""
        # Verify get_instance returns the singleton instance
        assert WaNoRegistrySelection.get_instance() is registry_selection

    def test_get_iconpath(self, registry_selection):
        """Test get_iconpath method."""
        # Call method
        path = registry_selection.get_iconpath("test.png")

        # Verify path is constructed correctly
        expected_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
            "Media",
            "icons",
            "test.png",
        )
        assert path.replace("\\", "/") == expected_path.replace("\\", "/")

    def test_set_status_connected(self, registry_selection):
        """Test setStatus method with connected status."""
        # Mock QPixmap and QIcon
        with patch("simstack.view.WaNoRegistrySelection.QPixmap") as mock_pixmap, patch(
            "simstack.view.WaNoRegistrySelection.QIcon"
        ) as mock_icon:
            # Mock pixmap and icon instances
            pixmap_instance = MagicMock()
            mock_pixmap.return_value = pixmap_instance

            icon_instance = MagicMock()
            mock_icon.return_value = icon_instance

            # Set status to connected
            registry_selection.setStatus(
                WaNoRegistrySelection.CONNECTION_STATES.connected
            )

            # Verify status was updated
            assert (
                registry_selection._WaNoRegistrySelection__status
                == WaNoRegistrySelection.CONNECTION_STATES.connected
            )

            # Verify icon was updated
            mock_pixmap.assert_called_once()
            mock_icon.assert_called_once_with(pixmap_instance)
            registry_selection.isConnectedIcon.setIcon.assert_called_once_with(
                icon_instance
            )

            # Verify text was updated
            registry_selection.isConnectedIcon.setText.assert_called_once_with(
                "Disconnect"
            )

    def test_set_status_connecting(self, registry_selection):
        """Test setStatus method with connecting status."""
        # Mock QPixmap and QIcon
        with patch("simstack.view.WaNoRegistrySelection.QPixmap"), patch(
            "simstack.view.WaNoRegistrySelection.QIcon"
        ):
            # Set status to connecting
            registry_selection.setStatus(
                WaNoRegistrySelection.CONNECTION_STATES.connecting
            )

            # Verify status was updated
            assert (
                registry_selection._WaNoRegistrySelection__status
                == WaNoRegistrySelection.CONNECTION_STATES.connecting
            )

            # Verify text was updated
            registry_selection.isConnectedIcon.setText.assert_called_once_with(
                "[Connecting]"
            )

    def test_set_status_disconnected(self, registry_selection):
        """Test setStatus method with disconnected status."""
        # Mock QPixmap and QIcon
        with patch("simstack.view.WaNoRegistrySelection.QPixmap"), patch(
            "simstack.view.WaNoRegistrySelection.QIcon"
        ):
            # Set status to disconnected
            registry_selection.setStatus(
                WaNoRegistrySelection.CONNECTION_STATES.disconnected
            )

            # Verify status was updated
            assert (
                registry_selection._WaNoRegistrySelection__status
                == WaNoRegistrySelection.CONNECTION_STATES.disconnected
            )

            # Verify text was updated
            registry_selection.isConnectedIcon.setText.assert_called_once_with(
                "Connect"
            )

    def test_select_registry(self, registry_selection):
        """Test select_registry method."""
        # Mock setCurrentIndex
        registry_selection.registryComboBox.setCurrentIndex = MagicMock()

        # Call method
        registry_selection.select_registry(1)

        # Verify setCurrentIndex was called
        registry_selection.registryComboBox.setCurrentIndex.assert_called_once_with(1)

    def test_update_registries(self, registry_selection):
        """Test update_registries method."""
        # Mock methods
        registry_selection.registryComboBox.clear = MagicMock()
        registry_selection.registryComboBox.addItem = MagicMock()
        registry_selection.select_registry = MagicMock()

        # Call method
        registries = ["registry1", "registry2", "registry3"]
        registry_selection.update_registries(registries, index=2)

        # Verify emit signal was disabled during update
        assert (
            registry_selection._WaNoRegistrySelection__emit_signal is True
        )  # Should be reset to True after update

        # Verify methods were called
        registry_selection.registryComboBox.clear.assert_called_once()
        assert registry_selection.registryComboBox.addItem.call_count == 3
        registry_selection.select_registry.assert_called_once_with(2)

    def test_new_update_registries(self, registry_selection):
        """Test _new_update_registries method."""
        # Mock methods
        registry_selection.registryComboBox.currentText = MagicMock(
            return_value="registry1"
        )
        registry_selection.registryComboBox.clear = MagicMock()
        registry_selection.registryComboBox.addItem = MagicMock()
        registry_selection.registryComboBox.setCurrentText = MagicMock()

        # Call method
        with patch(
            "simstack.view.WaNoRegistrySelection.QtClusterSettingsProvider"
        ) as mock_provider:
            mock_provider.get_registries.return_value = {
                "registry1": MagicMock(),
                "registry2": MagicMock(),
                "registry3": MagicMock(),
            }

            registry_selection._new_update_registries()

        # Verify emit signal was disabled during update
        assert (
            registry_selection._WaNoRegistrySelection__emit_signal is True
        )  # Should be reset to True after update

        # Verify methods were called
        registry_selection.registryComboBox.currentText.assert_called_once()
        registry_selection.registryComboBox.clear.assert_called_once()
        assert registry_selection.registryComboBox.addItem.call_count == 3
        registry_selection.registryComboBox.setCurrentText.assert_called_once_with(
            "registry1"
        )

    def test_on_selection_changed(self, registry_selection, qtbot):
        """Test __on_selection_changed method."""
        # Call method directly
        registry_selection._WaNoRegistrySelection__on_selection_changed("new_registry")

        # Verify signal was emitted with correct argument
        registry_selection.registrySelectionChanged.emit.assert_called_once_with(
            "new_registry"
        )

        # Test with emit_signal disabled
        registry_selection._WaNoRegistrySelection__emit_signal = False
        registry_selection.registrySelectionChanged.emit.reset_mock()

        # Call with emit disabled
        registry_selection._WaNoRegistrySelection__on_selection_changed(
            "another_registry"
        )

        # Verify signal was not emitted
        registry_selection.registrySelectionChanged.emit.assert_not_called()

    def test_on_button_clicked_connected(self, registry_selection, qtbot):
        """Test __on_button_clicked method with connected status."""
        # Set status to connected
        registry_selection._WaNoRegistrySelection__status = (
            WaNoRegistrySelection.CONNECTION_STATES.connected
        )

        # Call method directly
        registry_selection._WaNoRegistrySelection__on_button_clicked()

        # Verify disconnect signal was emitted
        registry_selection.disconnect_registry.emit.assert_called_once()

    def test_on_button_clicked_disconnected(self, registry_selection, qtbot):
        """Test __on_button_clicked method with disconnected status."""
        # Set status to disconnected
        registry_selection._WaNoRegistrySelection__status = (
            WaNoRegistrySelection.CONNECTION_STATES.disconnected
        )

        # Mock current registry
        registry_selection.registryComboBox.currentText = MagicMock(
            return_value="current_registry"
        )

        # Call method directly
        registry_selection._WaNoRegistrySelection__on_button_clicked()

        # Verify connect signal was emitted with correct argument
        registry_selection.connect_registry.emit.assert_called_once_with(
            "current_registry"
        )

    def test_on_button_clicked_connecting(self, registry_selection, qtbot):
        """Test __on_button_clicked method with connecting status."""
        # Set status to connecting
        registry_selection._WaNoRegistrySelection__status = (
            WaNoRegistrySelection.CONNECTION_STATES.connecting
        )

        # Call method directly
        registry_selection._WaNoRegistrySelection__on_button_clicked()

        # No signals should be emitted in this state
        registry_selection.connect_registry.emit.assert_not_called()
        registry_selection.disconnect_registry.emit.assert_not_called()
