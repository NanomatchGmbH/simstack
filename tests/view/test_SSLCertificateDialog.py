"""
Unit tests for SSL Certificate Dialog.

Tests the PySide6-based SSL certificate trust workflow.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from PySide6.QtWidgets import QMessageBox

from simstack.view.SSLCertificateDialog import (
    SSLCertificateHandler,
    CertificateInfoDialog,
)


class TestSSLCertificateHandler:
    """Test the SSL certificate handler."""

    def test_handler_initialization(self):
        """Test handler can be initialized."""
        handler = SSLCertificateHandler("https://127.0.0.1:8443", "secret")
        assert handler.server_url == "https://127.0.0.1:8443"
        assert handler.cert_path is None

    @patch("simstack.view.SSLCertificateDialog.requests.Session")
    def test_successful_connection_with_trusted_cert(self, mock_session):
        """Test successful connection when certificate is already trusted."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.return_value.get.return_value = mock_response

        handler = SSLCertificateHandler("https://127.0.0.1:8443", "secret")
        # test_connection raises on failure; returning normally means success
        handler.test_connection(verify_ssl=True)

    @patch("simstack.view.SSLCertificateDialog.requests.Session")
    def test_ssl_error_connection(self, mock_session):
        """Test connection failure with SSL error."""
        import requests
        from simstack.view.SSLCertificateDialog import SSLCertificateError

        # Mock SSL error
        mock_session.return_value.get.side_effect = requests.exceptions.SSLError(
            "SSL certificate verify failed"
        )

        handler = SSLCertificateHandler("https://127.0.0.1:8443", "secret")
        with pytest.raises(SSLCertificateError) as exc_info:
            handler.test_connection(verify_ssl=True)

        assert "SSL" in str(exc_info.value)

    @patch("simstack.view.SSLCertificateDialog.requests.Session")
    def test_connection_without_ssl_verification(self, mock_session):
        """Test connection without SSL verification."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.return_value.get.return_value = mock_response

        handler = SSLCertificateHandler("https://127.0.0.1:8443", "secret")
        handler.test_connection(verify_ssl=False)

        # Verify SSL verification was disabled
        assert mock_session.return_value.verify is False

    def test_get_certificate_path_before_storage(self):
        """Test getting certificate path when none is stored."""
        handler = SSLCertificateHandler("https://127.0.0.1:8443", "secret")
        assert handler.get_certificate_path() is None

    def test_has_stored_certificate_initially_false(self):
        """Test that initially no certificate is stored."""
        handler = SSLCertificateHandler("https://127.0.0.1:8443", "secret")
        assert handler.has_stored_certificate() is False

    @patch.object(Path, "exists")
    def test_has_stored_certificate_when_exists(self, mock_exists):
        """Test detection of existing certificate."""
        mock_exists.return_value = True
        handler = SSLCertificateHandler("https://127.0.0.1:8443", "secret")
        # Manually set cert_path for testing
        handler.cert_path = Path("/fake/path/cert.pem")
        assert handler.has_stored_certificate() is True

    def test_get_certificate_info_when_none_stored(self):
        """Test getting certificate info when none is stored."""
        handler = SSLCertificateHandler("https://127.0.0.1:8443", "secret")
        assert handler.get_certificate_info() is None

    def test_revoke_certificate_when_none_stored(self):
        """Test revoking certificate when none is stored."""
        handler = SSLCertificateHandler("https://127.0.0.1:8443", "secret")
        success, message = handler.revoke_certificate()
        assert success is False
        assert "No certificate" in message


class TestCertificateInfoDialog:
    """Test the certificate information dialog."""

    @pytest.fixture
    def mock_cert_info(self):
        """Create a mock certificate info object."""
        from datetime import datetime

        # Use Mock instead of real CertificateInfo to avoid dependencies
        cert_info = Mock()
        cert_info.subject = "CN=localhost"
        cert_info.issuer = "CN=localhost"
        cert_info.serial_number = "12345"
        cert_info.not_valid_before = datetime(2024, 1, 1)
        cert_info.not_valid_after = datetime(2025, 1, 1)
        cert_info.is_self_signed = True
        cert_info.fingerprint = "AA:BB:CC:DD:EE:FF"
        cert_info.san_names = ["localhost", "127.0.0.1"]

        return cert_info

    def test_dialog_initialization(self, qtbot, mock_cert_info):
        """Test dialog can be initialized."""
        dialog = CertificateInfoDialog(mock_cert_info)
        qtbot.addWidget(dialog)

        assert dialog.windowTitle() == "SSL Certificate Information"
        assert dialog.cert_info == mock_cert_info

    def test_certificate_info_formatting(self, qtbot, mock_cert_info):
        """Test certificate information is formatted correctly."""
        dialog = CertificateInfoDialog(mock_cert_info)
        qtbot.addWidget(dialog)

        formatted = dialog._format_certificate_info()

        assert "CN=localhost" in formatted
        assert "12345" in formatted
        assert "Self-Signed: Yes" in formatted
        assert "AA:BB:CC:DD:EE:FF" in formatted
        assert "localhost" in formatted
        assert "127.0.0.1" in formatted

    def test_dialog_buttons(self, qtbot, mock_cert_info):
        """Test dialog has the expected buttons."""
        from PySide6.QtWidgets import QPushButton

        dialog = CertificateInfoDialog(mock_cert_info)
        qtbot.addWidget(dialog)

        # Find all push buttons in the dialog
        buttons = dialog.findChildren(QPushButton)
        button_texts = [btn.text() for btn in buttons]

        # Should have Trust, Reject, and More Info buttons
        assert any(
            "Trust" in text for text in button_texts
        ), f"Available buttons: {button_texts}"
        assert any(
            "Reject" in text for text in button_texts
        ), f"Available buttons: {button_texts}"
        assert any(
            "Info" in text for text in button_texts
        ), f"Available buttons: {button_texts}"

    @patch("simstack.view.SSLCertificateDialog.QMessageBox")
    def test_show_additional_info(self, mock_msgbox, qtbot, mock_cert_info):
        """Test showing additional information."""
        dialog = CertificateInfoDialog(mock_cert_info)
        qtbot.addWidget(dialog)

        dialog._show_additional_info()

        # Verify QMessageBox was called
        mock_msgbox.assert_called_once()


class TestSSLCertificateWorkflow:
    """Integration tests for the full SSL certificate workflow."""

    @patch("simstack.view.SSLCertificateDialog.QMessageBox.question")
    @patch("simstack.view.SSLCertificateDialog.requests.Session")
    def test_workflow_when_cert_already_trusted(
        self, mock_session, mock_question, qtbot
    ):
        """Test workflow when certificate is already trusted."""
        # Mock successful connection
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.return_value.get.return_value = mock_response

        handler = SSLCertificateHandler("https://127.0.0.1:8443", "secret")
        success, message = handler.handle_ssl_certificate_trust()

        # Should succeed without showing any dialogs
        assert success is True
        assert message is not None
        assert "trusted certificate" in message.lower()
        mock_question.assert_not_called()

    @patch("simstack.view.SSLCertificateDialog.QMessageBox.question")
    @patch("simstack.view.SSLCertificateDialog.requests.Session")
    def test_workflow_user_declines_inspection(
        self, mock_session, mock_question, qtbot
    ):
        """Test workflow when user declines to inspect certificate."""
        import requests

        # Mock SSL error
        mock_session.return_value.get.side_effect = requests.exceptions.SSLError(
            "SSL error"
        )

        # User declines to inspect
        mock_question.return_value = QMessageBox.No

        handler = SSLCertificateHandler("https://127.0.0.1:8443", "secret")
        success, message = handler.handle_ssl_certificate_trust()

        assert success is False
        assert message is not None
        assert "declined" in message.lower()

    @patch("simstack.view.SSLCertificateDialog.requests.Session")
    @patch.object(Path, "exists")
    def test_workflow_with_stored_certificate_success(
        self, mock_exists, mock_session, qtbot
    ):
        """Test workflow when certificate is already stored and works."""
        # Mock successful connection
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.return_value.get.return_value = mock_response

        handler = SSLCertificateHandler("https://127.0.0.1:8443", "secret")

        # Set up stored certificate
        handler.cert_path = Path("/fake/cert.pem")
        mock_exists.return_value = True

        success, message = handler.handle_ssl_certificate_trust()

        assert success is True
        assert message is not None
        assert "stored certificate" in message.lower()

    @patch("simstack.view.SSLCertificateDialog.QMessageBox.question")
    @patch("simstack.view.SSLCertificateDialog.requests.Session")
    @patch.object(Path, "exists")
    def test_workflow_with_stored_certificate_failure(
        self, mock_exists, mock_session, mock_question, qtbot
    ):
        """Test workflow when stored certificate fails."""
        import requests

        # Mock SSL error
        mock_session.return_value.get.side_effect = requests.exceptions.SSLError(
            "SSL error"
        )

        # User declines to update certificate
        mock_question.return_value = QMessageBox.No

        handler = SSLCertificateHandler("https://127.0.0.1:8443", "secret")

        # Set up stored certificate
        handler.cert_path = Path("/fake/cert.pem")
        mock_exists.return_value = True

        success, message = handler.handle_ssl_certificate_trust()

        assert success is False
        assert message is not None
        assert "declined to update" in message.lower()


# Note: Full integration tests with certificate retrieval and storage
# are skipped as they require a running FastAPI server with SSL.
# These should be tested manually using ssl_certificate_demo.py
