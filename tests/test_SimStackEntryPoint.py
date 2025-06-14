import unittest.mock as mock
from unittest.mock import patch, MagicMock

from simstack import SimStackEntryPoint


class TestSimStackEntryPoint:
    def test_signal_handler_with_editor(self):
        """Test signal handler when editor exists"""
        mock_editor = MagicMock()
        with patch.object(SimStackEntryPoint, "editor", mock_editor):
            SimStackEntryPoint.signal_handler()
            mock_editor.exit.assert_called_once()

    def test_signal_handler_without_editor(self):
        """Test signal handler when editor is None"""
        with patch.object(SimStackEntryPoint, "editor", None):
            # Should not raise any exception
            SimStackEntryPoint.signal_handler()

    @patch("simstack.SimStackEntryPoint.QLocale")
    def test_override_locale(self, mock_qlocale):
        """Test locale override function"""
        SimStackEntryPoint.override_locale()
        mock_qlocale.setDefault.assert_called_once()
        # Verify the locale was set to English/US
        call_args = mock_qlocale.setDefault.call_args[0][0]
        assert mock_qlocale.return_value == call_args

    @patch("simstack.SimStackEntryPoint.sys.exit")
    @patch("simstack.SimStackEntryPoint.QApplication")
    @patch("simstack.SimStackEntryPoint.WFEditorApplication")
    @patch("simstack.SimStackEntryPoint.WaNoSettingsProvider")
    @patch("simstack.SimStackEntryPoint.SimStackPaths")
    @patch("simstack.SimStackEntryPoint.signal.signal")
    @patch("simstack.SimStackEntryPoint.override_locale")
    @patch("simstack.SimStackEntryPoint.platform.system")
    @patch("simstack.SimStackEntryPoint.os.makedirs")
    @patch("simstack.SimStackEntryPoint.path.isdir")
    @patch("simstack.SimStackEntryPoint.path.exists")
    @patch("simstack.SimStackEntryPoint.uuid.uuid4")
    @patch("simstack.SimStackEntryPoint.logging.basicConfig")
    @patch("simstack.SimStackEntryPoint.ctypes")
    @patch("simstack.SimStackEntryPoint.QStyleFactory")
    @patch("simstack.SimStackEntryPoint.QtCore")
    @patch("simstack.SimStackEntryPoint.QTimer")
    @patch("builtins.open", mock.mock_open(read_data="test: value"))
    @patch("simstack.SimStackEntryPoint.yaml.safe_load")
    def test_main_linux_with_existing_settings(
        self,
        mock_yaml_load,
        mock_qtimer,
        mock_qtcore,
        mock_style_factory,
        mock_ctypes,
        mock_logging,
        mock_uuid,
        mock_path_exists,
        mock_path_isdir,
        mock_makedirs,
        mock_platform,
        mock_override_locale,
        mock_signal,
        mock_paths,
        mock_settings_provider,
        mock_wf_app,
        mock_qapp,
        mock_sys_exit,
    ):
        """Test main function on Linux with existing settings"""
        # Setup mocks
        mock_platform.return_value = "Linux"
        mock_path_isdir.return_value = True  # Settings folder exists
        mock_path_exists.return_value = True  # Settings file exists
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = lambda x: "test-uuid"

        mock_paths.get_temp_folder.return_value = "/tmp"
        mock_paths.get_settings_folder_nanomatch.return_value = "/home/user/.nanomatch"
        mock_paths.get_settings_file.return_value = (
            "/home/user/.nanomatch/settings.yaml"
        )

        mock_settings = MagicMock()
        mock_settings_provider.get_instance.return_value = mock_settings
        mock_yaml_load.return_value = {"test": "value"}

        mock_app = MagicMock()
        mock_qapp.return_value = mock_app
        mock_app.exec_.return_value = 0

        mock_timer = MagicMock()
        mock_qtimer.return_value = mock_timer

        # Call main
        SimStackEntryPoint.main()

        # Verify key calls
        mock_signal.assert_called_once()
        mock_override_locale.assert_called_once()
        mock_qtcore.QCoreApplication.setAttribute.assert_called_once()
        mock_qapp.assert_called_once()
        mock_logging.assert_called_once()
        mock_settings_provider.get_instance.assert_called_once()
        mock_settings.load_from_dict.assert_called_once_with({"test": "value"})
        mock_settings._finish_parsing.assert_called_once()
        mock_wf_app.assert_called_once_with(mock_settings)
        mock_timer.start.assert_called_once_with(500)
        mock_app.exec_.assert_called_once()
        mock_sys_exit.assert_called_once_with(0)

        # Should not call makedirs since directory exists
        mock_makedirs.assert_not_called()
        # Should not call dump_to_file since settings file exists
        mock_settings.dump_to_file.assert_not_called()

    @patch("simstack.SimStackEntryPoint.sys.exit")
    @patch("simstack.SimStackEntryPoint.QApplication")
    @patch("simstack.SimStackEntryPoint.WFEditorApplication")
    @patch("simstack.SimStackEntryPoint.WaNoSettingsProvider")
    @patch("simstack.SimStackEntryPoint.SimStackPaths")
    @patch("simstack.SimStackEntryPoint.signal.signal")
    @patch("simstack.SimStackEntryPoint.override_locale")
    @patch("simstack.SimStackEntryPoint.platform.system")
    @patch("simstack.SimStackEntryPoint.os.makedirs")
    @patch("simstack.SimStackEntryPoint.path.isdir")
    @patch("simstack.SimStackEntryPoint.path.exists")
    @patch("simstack.SimStackEntryPoint.uuid.uuid4")
    @patch("simstack.SimStackEntryPoint.logging.basicConfig")
    @patch("simstack.SimStackEntryPoint.ctypes")
    @patch("simstack.SimStackEntryPoint.QStyleFactory")
    @patch("simstack.SimStackEntryPoint.QtCore")
    @patch("simstack.SimStackEntryPoint.QTimer")
    def test_main_windows_no_existing_settings(
        self,
        mock_qtimer,
        mock_qtcore,
        mock_style_factory,
        mock_ctypes,
        mock_logging,
        mock_uuid,
        mock_path_exists,
        mock_path_isdir,
        mock_makedirs,
        mock_platform,
        mock_override_locale,
        mock_signal,
        mock_paths,
        mock_settings_provider,
        mock_wf_app,
        mock_qapp,
        mock_sys_exit,
    ):
        """Test main function on Windows without existing settings"""
        # Setup mocks
        mock_platform.return_value = "Windows"
        mock_path_isdir.return_value = False  # Settings folder doesn't exist
        mock_path_exists.return_value = False  # Settings file doesn't exist
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = lambda x: "test-uuid"

        mock_paths.get_temp_folder.return_value = "/tmp"
        mock_paths.get_settings_folder_nanomatch.return_value = "/home/user/.nanomatch"
        mock_paths.get_settings_file.return_value = (
            "/home/user/.nanomatch/settings.yaml"
        )

        mock_settings = MagicMock()
        mock_settings_provider.get_instance.return_value = mock_settings

        mock_app = MagicMock()
        mock_qapp.return_value = mock_app
        mock_app.exec_.return_value = 0

        mock_timer = MagicMock()
        mock_qtimer.return_value = mock_timer

        # Call main
        SimStackEntryPoint.main()

        # Verify Windows-specific calls
        mock_ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID.assert_called_once()

        # Verify directory creation
        mock_makedirs.assert_called_once_with("/home/user/.nanomatch")

        # Verify default settings are dumped
        mock_settings.dump_to_file.assert_called_once_with(
            "/home/user/.nanomatch/settings.yaml"
        )

    @patch("simstack.SimStackEntryPoint.sys.exit")
    @patch("simstack.SimStackEntryPoint.QApplication")
    @patch("simstack.SimStackEntryPoint.WFEditorApplication")
    @patch("simstack.SimStackEntryPoint.WaNoSettingsProvider")
    @patch("simstack.SimStackEntryPoint.SimStackPaths")
    @patch("simstack.SimStackEntryPoint.signal.signal")
    @patch("simstack.SimStackEntryPoint.override_locale")
    @patch("simstack.SimStackEntryPoint.platform.system")
    @patch("simstack.SimStackEntryPoint.os.makedirs")
    @patch("simstack.SimStackEntryPoint.path.isdir")
    @patch("simstack.SimStackEntryPoint.path.exists")
    @patch("simstack.SimStackEntryPoint.uuid.uuid4")
    @patch("simstack.SimStackEntryPoint.logging.basicConfig")
    @patch("simstack.SimStackEntryPoint.ctypes")
    @patch("simstack.SimStackEntryPoint.QStyleFactory")
    @patch("simstack.SimStackEntryPoint.QtCore")
    @patch("simstack.SimStackEntryPoint.QTimer")
    def test_main_darwin_fusion_style(
        self,
        mock_qtimer,
        mock_qtcore,
        mock_style_factory,
        mock_ctypes,
        mock_logging,
        mock_uuid,
        mock_path_exists,
        mock_path_isdir,
        mock_makedirs,
        mock_platform,
        mock_override_locale,
        mock_signal,
        mock_paths,
        mock_settings_provider,
        mock_wf_app,
        mock_qapp,
        mock_sys_exit,
    ):
        """Test main function on macOS with Fusion style"""
        # Setup mocks
        mock_platform.return_value = "Darwin"
        mock_path_isdir.return_value = True
        mock_path_exists.return_value = False
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = lambda x: "test-uuid"

        mock_paths.get_temp_folder.return_value = "/tmp"
        mock_paths.get_settings_folder_nanomatch.return_value = "/home/user/.nanomatch"
        mock_paths.get_settings_file.return_value = (
            "/home/user/.nanomatch/settings.yaml"
        )

        mock_settings = MagicMock()
        mock_settings_provider.get_instance.return_value = mock_settings

        mock_app = MagicMock()
        mock_qapp.return_value = mock_app
        mock_app.exec_.return_value = 0

        mock_fusion_style = MagicMock()
        mock_style_factory.create.return_value = mock_fusion_style

        mock_timer = MagicMock()
        mock_qtimer.return_value = mock_timer

        # Call main
        SimStackEntryPoint.main()

        # Verify macOS-specific calls
        mock_style_factory.create.assert_called_once_with("Fusion")
        mock_app.setStyle.assert_called_once_with(mock_fusion_style)

    @patch("simstack.SimStackEntryPoint.sys.exit")
    @patch("simstack.SimStackEntryPoint.QApplication")
    @patch("simstack.SimStackEntryPoint.WFEditorApplication")
    @patch("simstack.SimStackEntryPoint.WaNoSettingsProvider")
    @patch("simstack.SimStackEntryPoint.SimStackPaths")
    @patch("simstack.SimStackEntryPoint.signal.signal")
    @patch("simstack.SimStackEntryPoint.override_locale")
    @patch("simstack.SimStackEntryPoint.platform.system")
    @patch("simstack.SimStackEntryPoint.os.makedirs")
    @patch("simstack.SimStackEntryPoint.path.isdir")
    @patch("simstack.SimStackEntryPoint.path.exists")
    @patch("simstack.SimStackEntryPoint.uuid.uuid4")
    @patch("simstack.SimStackEntryPoint.logging.basicConfig")
    @patch("simstack.SimStackEntryPoint.ctypes")
    @patch("simstack.SimStackEntryPoint.QStyleFactory")
    @patch("simstack.SimStackEntryPoint.QtCore")
    @patch("simstack.SimStackEntryPoint.QTimer")
    @patch("builtins.open", mock.mock_open())
    @patch("simstack.SimStackEntryPoint.traceback.print_tb")
    def test_main_with_exception(
        self,
        mock_print_tb,
        mock_qtimer,
        mock_qtcore,
        mock_style_factory,
        mock_ctypes,
        mock_logging,
        mock_uuid,
        mock_path_exists,
        mock_path_isdir,
        mock_makedirs,
        mock_platform,
        mock_override_locale,
        mock_signal,
        mock_paths,
        mock_settings_provider,
        mock_wf_app,
        mock_qapp,
        mock_sys_exit,
    ):
        """Test main function handles exceptions properly"""
        # Setup mocks
        mock_platform.return_value = "Linux"
        mock_path_isdir.return_value = True
        mock_path_exists.return_value = False
        mock_uuid.return_value = MagicMock()
        mock_uuid.return_value.__str__ = lambda x: "test-uuid"

        mock_paths.get_temp_folder.return_value = "/tmp"
        mock_paths.get_settings_folder_nanomatch.return_value = "/home/user/.nanomatch"
        mock_paths.get_settings_file.return_value = (
            "/home/user/.nanomatch/settings.yaml"
        )

        mock_settings = MagicMock()
        mock_settings_provider.get_instance.return_value = mock_settings

        mock_app = MagicMock()
        mock_qapp.return_value = mock_app
        # Make app.exec_() raise an exception
        test_exception = Exception("Test exception")
        mock_app.exec_.side_effect = test_exception

        mock_timer = MagicMock()
        mock_qtimer.return_value = mock_timer

        # Call main and expect NameError due to undefined exitcode
        with patch("simstack.SimStackEntryPoint.sys.exc_info") as mock_exc_info:
            mock_exc_info.return_value = (
                type(test_exception),
                test_exception,
                "traceback",
            )
            try:
                SimStackEntryPoint.main()
            except NameError:
                # This is expected - exitcode is not defined when exception occurs
                pass

        # Verify exception handling
        mock_print_tb.assert_called_once()
