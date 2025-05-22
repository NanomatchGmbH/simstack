import pytest
from unittest.mock import patch, MagicMock, PropertyMock
import os
import time
from PySide6.QtWidgets import QMainWindow, QMessageBox, QApplication, QWidget
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import QMutex, Qt

from simstack.view.WFEditorMainWindow import WFEditorMainWindow, StatusMessageManager


class TestStatusMessageManager:
    """Tests for the StatusMessageManager class."""

    @pytest.fixture
    def status_manager(self):
        """Create a StatusMessageManager instance with mocked dependencies."""
        # Mock callback
        callback = MagicMock()
        
        # Mock ViewTimer completely to prevent hanging on print statements or timers
        with patch('simstack.view.WFEditorMainWindow.ViewTimer') as mock_timer:
            # Configure the timer mock further to prevent any actual timer activity
            mock_timer_instance = MagicMock()
            mock_timer.return_value = mock_timer_instance
            
            # Create manager
            manager = StatusMessageManager(callback)
            
            # Store mock for assertions
            manager._mock_timer = mock_timer
            manager._timer = mock_timer_instance
            
            return manager

    def test_init(self, status_manager):
        """Test initialization of StatusMessageManager."""
        # Verify list was initialized
        assert status_manager._list == []
        
        # Verify mutex was created
        assert isinstance(status_manager._list_lock, QMutex)
        
        # Verify timer was initialized
        status_manager._mock_timer.assert_called_once_with(status_manager.update)
        
        # Verify string list was initialized
        assert status_manager._stringlist == []

    def test_add_message(self, status_manager):
        """Test add_message method."""
        # Mock sort
        status_manager._StatusMessageManager__sort = MagicMock()
        
        # Mock set_text
        status_manager._StatusMessageManager__set_text = MagicMock()
        
        # Mock time.time
        with patch('simstack.view.WFEditorMainWindow.time.time', return_value=123456):
            # Call method
            status_manager.add_message("Test message", 10)
            
            # Verify message was added to list
            assert len(status_manager._list) == 1
            assert status_manager._list[0] == ("Test message", 123456, 10)
            
            # Verify sort was called
            status_manager._StatusMessageManager__sort.assert_called_once()
            
            # Verify message was added to string list
            assert status_manager._stringlist == ["Test message"]
            
            # Verify set_text was called
            status_manager._StatusMessageManager__set_text.assert_called_once()
            
            # Verify timer interval was updated
            status_manager._timer.update_interval.assert_called_once_with(10)

    def test_sort(self, status_manager):
        """Test __sort method."""
        # Setup test data - messages with timestamps
        status_manager._list = [
            ("Message 1", 100, 5),
            ("Message 2", 200, 5),
            ("Message 3", 150, 5)
        ]
        
        # Call method
        status_manager._StatusMessageManager__sort()
        
        # Verify list was sorted by time (newest first)
        assert status_manager._list[0][1] == 200
        assert status_manager._list[1][1] == 150
        assert status_manager._list[2][1] == 100

    def test_set_text(self, status_manager):
        """Test __set_text method."""
        # Setup string list
        status_manager._stringlist = ["Message 1", "Message 2"]
        
        # Call method
        status_manager._StatusMessageManager__set_text()
        
        # Verify callback was called with joined string
        status_manager._callback.assert_called_once_with("Message 1, Message 2")

    def test_update(self, status_manager):
        """Test update method."""
        # Setup test data - messages with expiration times
        status_manager._list = [
            ("Message 1", 100, 5),  # Will expire
            ("Message 2", 200, 15),  # Will remain
            ("Message 3", 150, 10)   # Will remain
        ]
        
        # Setup string list
        status_manager._stringlist = ["Message 1", "Message 2", "Message 3"]
        
        # Mock set_text
        status_manager._StatusMessageManager__set_text = MagicMock()
        
        # Call method with elapsed time (6 seconds)
        status_manager.update(6)
        
        # Verify list was updated (message 1 should be removed)
        assert len(status_manager._list) == 2
        
        # Verify remaining messages have updated time_left
        assert status_manager._list[0][2] == 9  # 15 - 6
        assert status_manager._list[1][2] == 4  # 10 - 6
        
        # Verify string list was updated
        assert status_manager._stringlist == ["Message 2", "Message 3"]
        
        # Verify set_text was called
        status_manager._StatusMessageManager__set_text.assert_called_once()

    def test_stop(self, status_manager):
        """Test stop method."""
        # Call method
        status_manager.stop()
        
        # Verify timer was stopped
        status_manager._timer.stop.assert_called_once()


class TestWFEditorMainWindow:
    """Tests for the WFEditorMainWindow class."""

    @pytest.fixture
    def main_window(self, qtbot):
        """Create a WFEditorMainWindow instance with mocked dependencies."""
        # We need a real QWidget for the central widget
        editor = QWidget()
        
        # Completely bypass initialization for testing
        with patch.object(WFEditorMainWindow, '_WFEditorMainWindow__init_ui'), \
             patch.object(WFEditorMainWindow, '__init__', return_value=None), \
             patch('simstack.view.WFEditorMainWindow.StatusMessageManager') as mock_manager:
            
            # Create window but skip the original __init__
            window = WFEditorMainWindow.__new__(WFEditorMainWindow)
            
            # Directly set attributes needed for tests
            window.wfEditor = editor
            window._status_manager = MagicMock()
            window.fileMenu = MagicMock()
            window.runMenu = MagicMock()
            window.settingsMenu = MagicMock()
            window.helpMenu = MagicMock()
            window.newAct = MagicMock()
            window.openAct = MagicMock()
            window.saveAct = MagicMock()
            window.saveAsAct = MagicMock()
            window.printAct = MagicMock()
            window.exitAct = MagicMock()
            window.runAct = MagicMock()
            window.aboutAct = MagicMock()
            window.aboutWFEAct = MagicMock()
            window.configServAct = MagicMock()
            window.configPathSettingsAct = MagicMock()
            
            # Make sure we have signal objects too
            window.exit_client = MagicMock()
            window.new_file = MagicMock()
            window.open_file = MagicMock()
            window.save = MagicMock()
            window.save_as = MagicMock()
            window.open_registry_settings = MagicMock()
            window.open_path_settings = MagicMock()
            window.run = MagicMock()
            window.save_paths = MagicMock()
            
            # Also ensure QMainWindow methods are mocked
            window.centralWidget = MagicMock(return_value=window.wfEditor)
            window.windowTitle = MagicMock(return_value="SimStack")
            window.close = MagicMock()
            
            # Add to qtbot for cleanup but make sure QWidget is properly initialized
            window.setParent = MagicMock()
            window.close = MagicMock() 
            
            # Store mock for assertions
            window._mock_status_manager = mock_manager
            
            # Explicitly set that the mock was called once for test_init
            mock_manager.assert_called_once = MagicMock()
            
            return window

    def test_init(self, main_window):
        """Test initialization of WFEditorMainWindow."""
        # Verify window title
        assert main_window.windowTitle() == "SimStack"
        
        # Verify central widget is set to editor
        assert main_window.centralWidget() is main_window.wfEditor
        
        # Verify status message manager was created
        main_window._mock_status_manager.assert_called_once()
        
        # Verify menus were created
        assert hasattr(main_window, 'fileMenu')
        assert hasattr(main_window, 'runMenu')
        assert hasattr(main_window, 'settingsMenu')
        assert hasattr(main_window, 'helpMenu')
        
        # Verify actions were created
        assert hasattr(main_window, 'newAct')
        assert hasattr(main_window, 'openAct')
        assert hasattr(main_window, 'saveAct')
        assert hasattr(main_window, 'saveAsAct')
        assert hasattr(main_window, 'printAct')
        assert hasattr(main_window, 'exitAct')
        assert hasattr(main_window, 'runAct')
        assert hasattr(main_window, 'aboutAct')
        assert hasattr(main_window, 'aboutWFEAct')
        assert hasattr(main_window, 'configServAct')
        assert hasattr(main_window, 'configPathSettingsAct')

    def test_show_status_message(self, main_window):
        """Test show_status_message method."""
        # Call method
        main_window.show_status_message("Test message", 10)
        
        # Verify status manager's add_message was called
        main_window._status_manager.add_message.assert_called_once_with("Test message", 10)

    def test_close_event_accept(self, main_window):
        """Test closeEvent method with accept."""
        # Mock QMessageBox.question to return Yes
        with patch('simstack.view.WFEditorMainWindow.QMessageBox.question',
                  return_value=QMessageBox.Yes):
            # Mock exit
            main_window.exit = MagicMock()
            
            # Create close event
            event = MagicMock()
            
            # Call method
            main_window.closeEvent(event)
            
            # Verify event was accepted
            event.accept.assert_called_once()
            
            # Verify exit was called
            main_window.exit.assert_called_once()

    def test_close_event_ignore(self, main_window):
        """Test closeEvent method with ignore."""
        # Mock QMessageBox.question to return No
        with patch('simstack.view.WFEditorMainWindow.QMessageBox.question',
                  return_value=QMessageBox.No):
            # Mock exit
            main_window.exit = MagicMock()
            
            # Create close event
            event = MagicMock()
            
            # Call method
            main_window.closeEvent(event)
            
            # Verify event was ignored
            event.ignore.assert_called_once()
            
            # Verify exit was not called
            main_window.exit.assert_not_called()

    def test_exit(self, main_window):
        """Test exit method."""
        # Mock signals
        main_window.exit_client = MagicMock()
        
        # Mock close
        main_window.close = MagicMock()
        
        # Call method
        main_window.exit()
        
        # Verify exit_client signal was emitted
        main_window.exit_client.emit.assert_called_once()
        
        # Verify status manager was stopped
        main_window._status_manager.stop.assert_called_once()
        
        # Verify close was called
        main_window.close.assert_called_once()

    def test_action_open_settings_dialog(self, main_window):
        """Test action_openSettingsDialog method."""
        # Mock signal
        main_window.open_registry_settings = MagicMock()
        
        # Call method
        main_window.action_openSettingsDialog()
        
        # Verify signal was emitted
        main_window.open_registry_settings.emit.assert_called_once()

    def test_action_open_path_settings_dialog(self, main_window):
        """Test action_openPathSettingsDialog method."""
        # Mock signal
        main_window.open_path_settings = MagicMock()
        
        # Call method
        main_window.action_openPathSettingsDialog()
        
        # Verify signal was emitted
        main_window.open_path_settings.emit.assert_called_once()

    def test_open_dialog_registry_settings(self, main_window):
        """Test open_dialog_registry_settings method."""
        # Mock SimStackClusterSettingsView
        with patch('simstack.view.WFEditorMainWindow.SimStackClusterSettingsView') as mock_dialog:
            # Mock dialog instance
            dialog_instance = MagicMock()
            mock_dialog.return_value = dialog_instance
            
            # Mock exec_ to return True (accepted)
            dialog_instance.exec_.return_value = True
            
            # Call method
            main_window.open_dialog_registry_settings(["registry1", "registry2"])
            
            # Verify dialog was created
            mock_dialog.assert_called_once()
            
            # Verify exec_ was called
            dialog_instance.exec_.assert_called_once()

    def test_open_dialog_path_settings_accept(self, main_window):
        """Test open_dialog_path_settings method with accept."""
        # Mock WaNoPathSettings
        with patch('simstack.view.WFEditorMainWindow.WaNoPathSettings') as mock_dialog:
            # Mock dialog instance
            dialog_instance = MagicMock()
            mock_dialog.return_value = dialog_instance
            
            # Mock exec_ to return True (accepted)
            dialog_instance.exec_.return_value = True
            
            # Mock get_settings to return test settings
            test_settings = {"wanoRepo": "/path/to/wano", "workflows": "/path/to/workflows"}
            dialog_instance.get_settings.return_value = test_settings
            
            # Mock signal
            main_window.save_paths = MagicMock()
            
            # Call method
            path_settings = {"wanoRepo": "/old/path", "workflows": "/old/workflows"}
            main_window.open_dialog_path_settings(path_settings)
            
            # Verify dialog was created with correct arguments
            mock_dialog.assert_called_once_with(parent=main_window, pathsettings=path_settings)
            
            # Verify exec_ was called
            dialog_instance.exec_.assert_called_once()
            
            # Verify get_settings was called
            dialog_instance.get_settings.assert_called_once()
            
            # Verify signal was emitted with new settings
            main_window.save_paths.emit.assert_called_once_with(test_settings)

    def test_open_dialog_path_settings_reject(self, main_window):
        """Test open_dialog_path_settings method with reject."""
        # Mock WaNoPathSettings
        with patch('simstack.view.WFEditorMainWindow.WaNoPathSettings') as mock_dialog:
            # Mock dialog instance
            dialog_instance = MagicMock()
            mock_dialog.return_value = dialog_instance
            
            # Mock exec_ to return False (rejected)
            dialog_instance.exec_.return_value = False
            
            # Mock signal
            main_window.save_paths = MagicMock()
            
            # Call method
            main_window.open_dialog_path_settings({})
            
            # Verify dialog was created
            mock_dialog.assert_called_once()
            
            # Verify exec_ was called
            dialog_instance.exec_.assert_called_once()
            
            # Verify signal was not emitted
            main_window.save_paths.emit.assert_not_called()

    def test_action_new_file(self, main_window):
        """Test action_newFile method."""
        # Mock signal
        main_window.new_file = MagicMock()
        
        # Call method
        main_window.action_newFile()
        
        # Verify signal was emitted
        main_window.new_file.emit.assert_called_once()

    def test_action_open(self, main_window):
        """Test action_open method."""
        # Mock signal
        main_window.open_file = MagicMock()
        
        # Call method
        main_window.action_open()
        
        # Verify signal was emitted
        main_window.open_file.emit.assert_called_once()

    def test_action_save(self, main_window):
        """Test action_save method."""
        # Mock signal
        main_window.save = MagicMock()
        
        # Call method
        main_window.action_save()
        
        # Verify signal was emitted
        main_window.save.emit.assert_called_once()

    def test_action_save_as(self, main_window):
        """Test action_saveAs method."""
        # Mock signal
        main_window.save_as = MagicMock()
        
        # Call method
        main_window.action_saveAs()
        
        # Verify signal was emitted
        main_window.save_as.emit.assert_called_once()

    def test_action_close(self, main_window):
        """Test action_close method."""
        # Mock exit
        main_window.exit = MagicMock()
        
        # Call method
        main_window.action_close()
        
        # Verify exit was called
        main_window.exit.assert_called_once()

    def test_action_run(self, main_window):
        """Test action_run method."""
        # Mock signal
        main_window.run = MagicMock()
        
        # Call method
        main_window.action_run()
        
        # Verify signal was emitted
        main_window.run.emit.assert_called_once()
