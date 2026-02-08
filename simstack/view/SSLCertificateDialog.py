"""
SSL Certificate Trust Dialog for PySide6.

This module provides an interactive workflow for handling self-signed SSL certificates
when connecting to FastAPI servers with HTTPS.
"""

from pathlib import Path
from typing import Optional, Tuple
import time

import requests
from PySide6.QtWidgets import (
    QMessageBox,
    QDialog,
    QVBoxLayout,
    QLabel,
    QTextEdit,
    QDialogButtonBox,
    QPushButton,
)
from PySide6.QtCore import Qt

from fastapilocalhttps import (
    HTTPSClient,
    CertificateInfo,
    CertificateRetrievalError,
)


class SSLCertificateError(Exception):
    """Exception raised when SSL certificate verification fails."""
    pass


class ConnectionFailedError(Exception):
    """Exception raised when connection to server fails (timeout, refused, etc)."""
    pass


class CertificateInfoDialog(QDialog):
    """Dialog to display SSL certificate information."""

    def __init__(self, cert_info: CertificateInfo, parent=None):
        super().__init__(parent)
        self.cert_info = cert_info
        self.setWindowTitle("SSL Certificate Information")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self._setup_ui()

    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("<h2>SSL Certificate Information</h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Certificate details in a text edit
        cert_details = self._format_certificate_info()
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(cert_details)
        layout.addWidget(text_edit)

        # Warning message
        warning = QLabel(
            "<b>⚠ This is a self-signed certificate from a local development server.</b><br>"
            "Self-signed certificates are not trusted by default and will cause SSL warnings."
        )
        warning.setWordWrap(True)
        warning.setStyleSheet("color: orange; padding: 10px;")
        layout.addWidget(warning)

        # Button box with custom buttons
        button_box = QDialogButtonBox()

        trust_btn = QPushButton("Trust Certificate")
        trust_btn.setDefault(True)
        trust_btn.clicked.connect(self.accept)

        reject_btn = QPushButton("Reject")
        reject_btn.clicked.connect(self.reject)

        info_btn = QPushButton("More Info")
        info_btn.clicked.connect(self._show_additional_info)

        button_box.addButton(trust_btn, QDialogButtonBox.AcceptRole)
        button_box.addButton(reject_btn, QDialogButtonBox.RejectRole)
        button_box.addButton(info_btn, QDialogButtonBox.HelpRole)

        layout.addWidget(button_box)

    def _format_certificate_info(self) -> str:
        """Format certificate information for display."""
        info = []
        info.append("=" * 60)
        info.append("CERTIFICATE DETAILS")
        info.append("=" * 60)
        info.append(f"Subject: {self.cert_info.subject}")
        info.append(f"Issuer: {self.cert_info.issuer}")
        info.append(f"Serial Number: {self.cert_info.serial_number}")
        info.append(f"Valid From: {self.cert_info.not_valid_before}")
        info.append(f"Valid Until: {self.cert_info.not_valid_after}")
        info.append(f"Self-Signed: {'Yes' if self.cert_info.is_self_signed else 'No'}")
        info.append(f"SHA256 Fingerprint: {self.cert_info.fingerprint}")

        if self.cert_info.san_names:
            info.append("\nSubject Alternative Names:")
            for name in self.cert_info.san_names:
                info.append(f"  • {name}")

        info.append("=" * 60)
        return "\n".join(info)

    def _show_additional_info(self):
        """Show additional information about trusting certificates."""
        msg = QMessageBox(self)
        msg.setWindowTitle("About Trusting Certificates")
        msg.setIcon(QMessageBox.Information)
        msg.setText("<b>Trusting this certificate will:</b>")
        msg.setInformativeText(
            "• Allow secure connections to this server without SSL warnings\n"
            "• Add the certificate to your local trust store\n"
            "• Only affect connections to this specific server\n"
            "• Can be revoked later if needed\n\n"
            "This is safe for local development servers that you control."
        )
        msg.exec()


class SSLCertificateHandler:
    """
    Handles SSL certificate trust workflow for FastAPI HTTPS connections.

    This class provides an interactive PySide6-based workflow for:
    1. Testing HTTPS connections
    2. Retrieving and displaying certificate information
    3. Prompting user to trust certificates
    4. Storing trusted certificates locally
    """

    def __init__(self, server_url: str, parent=None):
        """
        Initialize SSL certificate handler.

        Args:
            server_url: URL of the FastAPI server (e.g., "https://127.0.0.1:8443")
            parent: Parent QWidget for dialog positioning
        """
        self.server_url = server_url
        self.parent = parent
        self.client = HTTPSClient(server_url)
        self.cert_path: Optional[Path] = None

        # Check if certificate is already stored
        self._check_stored_certificate()

    def _check_stored_certificate(self) -> None:
        """Check if a certificate is already stored for this server."""
        try:
            stored_cert_path = self.client.get_certificate_path()
            if stored_cert_path and stored_cert_path.exists():
                self.cert_path = stored_cert_path
        except Exception:
            # If checking fails, cert_path remains None
            pass

    def test_connection(
        self,
        verify_ssl: bool = True,
        cert_path: Optional[Path] = None,
        max_retries: int = 1,
        retry_delay: float = 5.0
    ) -> None:
        """
        Test connection to the server.

        Args:
            verify_ssl: Whether to verify SSL certificate
            cert_path: Path to certificate file to use for verification
            max_retries: Maximum number of retry attempts for connection failures (default: 1)
            retry_delay: Delay in seconds between retry attempts (default: 5.0)

        Raises:
            SSLCertificateError: If SSL certificate verification fails
            ConnectionFailedError: If connection to server fails after retries
        """
        session = requests.Session()

        if cert_path:
            # Use the provided certificate for verification
            session.verify = str(cert_path)
        elif not verify_ssl:
            session.verify = False
            # Suppress SSL warnings
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        for attempt in range(max_retries + 1):
            try:
                response = session.get(self.server_url, timeout=10)
                response.raise_for_status()
                # Connection successful
                return

            except requests.exceptions.SSLError as e:
                # SSL error - certificate validation failed
                # Don't retry for SSL errors, raise immediately
                raise SSLCertificateError(f"SSL certificate verification failed: {str(e)}") from e

            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.ConnectTimeout
            ) as e:
                # Connection failure - server not responding
                if attempt < max_retries:
                    # Wait before retrying
                    time.sleep(retry_delay)
                    continue
                else:
                    # All retries exhausted
                    raise ConnectionFailedError(
                        f"Failed to connect to server after {max_retries + 1} attempt(s): {str(e)}"
                    ) from e

            except requests.exceptions.RequestException as e:
                # Other request errors (HTTP errors, etc.)
                raise ConnectionFailedError(f"Request failed: {str(e)}") from e

    def handle_ssl_certificate_trust(self) -> Tuple[bool, Optional[str]]:
        """
        Handle the complete SSL certificate trust workflow.

        This method:
        1. Checks if certificate is already stored and trusted
        2. Tests normal HTTPS connection
        3. If SSL error, retrieves certificate and prompts user
        4. If user trusts, stores certificate
        5. Tests connection with stored certificate

        Returns:
            Tuple of (success: bool, message: Optional[str])
        """
        # Step 1: Check if we already have a stored certificate
        if self.cert_path and self.cert_path.exists():
            # Try connection with stored certificate
            try:
                self.test_connection(verify_ssl=True, cert_path=self.cert_path)
                return True, f"Connected successfully using stored certificate: {self.cert_path}"
            except (SSLCertificateError, ConnectionFailedError) as e:
                # Stored certificate exists but connection failed - ask user what to do
                reply = QMessageBox.question(
                    self.parent,
                    "Stored Certificate Failed",
                    f"A certificate for this server is already stored at:\n{self.cert_path}\n\n"
                    f"However, connection using this certificate failed:\n{str(e)}\n\n"
                    "Would you like to retrieve and trust a new certificate?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                if reply != QMessageBox.Yes:
                    return False, "Connection failed with stored certificate, user declined to update."

        # Step 2: Try normal connection first (without stored cert)
        try:
            self.test_connection(verify_ssl=True)
            return True, "Server is using a trusted certificate."
        except SSLCertificateError as e:
            # SSL certificate error - show dialog to inspect certificate
            reply = QMessageBox.question(
                self.parent,
                "SSL Certificate Error",
                f"Could not establish a secure connection to the server:\n\n{str(e)}\n\n"
                "This is likely because the server is using a self-signed certificate.\n\n"
                "Would you like to inspect and potentially trust this certificate?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )

            if reply != QMessageBox.Yes:
                return False, "User declined to inspect certificate."
        except ConnectionFailedError as e:
            # Connection failed - server not responding
            QMessageBox.critical(
                self.parent,
                "Connection Failed",
                f"Failed to connect to the server:\n\n{str(e)}\n\n"
                "Please verify that:\n"
                "• The server is running\n"
                "• The URL is correct\n"
                "• Network connectivity is available"
            )
            return False, f"Connection failed: {str(e)}"

        # Step 3: Retrieve and inspect certificate
        try:
            cert = self.client.retrieve_certificate()
            cert_info = self.client.inspect_certificate(cert)
        except CertificateRetrievalError as e:
            QMessageBox.critical(
                self.parent,
                "Certificate Retrieval Failed",
                f"Failed to retrieve certificate from server:\n\n{str(e)}"
            )
            return False, f"Certificate retrieval failed: {str(e)}"

        # Step 4: Show certificate info and ask for trust
        dialog = CertificateInfoDialog(cert_info, self.parent)
        if dialog.exec() != QDialog.Accepted:
            return False, "User declined to trust certificate."

        # Step 5: Store certificate locally
        try:
            self.cert_path = self.client.store_certificate(cert)

            # Step 6: Verify connection works with the stored certificate
            try:
                self.test_connection(verify_ssl=True, cert_path=self.cert_path)
                QMessageBox.information(
                    self.parent,
                    "Certificate Stored and Verified",
                    f"Certificate has been stored and verified successfully:\n\n"
                    f"• System trust store: {self.cert_path}\n"
                    "✓ Connection test successful!\n"
                    "You can now connect to this server securely."
                )
                return True, f"Certificate stored at: {self.cert_path}"
            except (SSLCertificateError, ConnectionFailedError) as test_error:
                QMessageBox.warning(
                    self.parent,
                    "Certificate Stored (Verification Failed)",
                    f"Certificate has been stored at:\n{self.cert_path}\n\n"
                    f"However, connection test failed:\n{str(test_error)}\n\n"
                    "The certificate may still work depending on your configuration."
                )
                return True, f"Certificate stored but verification failed: {str(test_error)}"

        except Exception as e:
            QMessageBox.critical(
                self.parent,
                "Certificate Storage Failed",
                f"Failed to store certificate:\n\n{str(e)}"
            )
            return False, f"Certificate storage failed: {str(e)}"

    def get_certificate_path(self) -> Optional[Path]:
        """
        Get the path to the stored certificate.

        Returns:
            Path to certificate file, or None if not stored
        """
        return self.cert_path

    def has_stored_certificate(self) -> bool:
        """
        Check if a certificate is stored for this server.

        Returns:
            True if certificate exists, False otherwise
        """
        return self.cert_path is not None and self.cert_path.exists()

    def get_certificate_info(self) -> Optional[CertificateInfo]:
        """
        Get information about the stored certificate.

        Returns:
            CertificateInfo object if certificate is stored, None otherwise
        """
        if not self.has_stored_certificate() or self.cert_path is None:
            return None

        try:
            # Read and inspect the stored certificate
            with open(self.cert_path, "rb") as f:
                cert_pem = f.read()
            return self.client.inspect_certificate(cert_pem)
        except Exception:
            return None

    def revoke_certificate(self) -> Tuple[bool, str]:
        """
        Revoke (delete) the stored certificate.

        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.has_stored_certificate() or self.cert_path is None:
            return False, "No certificate stored for this server."

        try:
            # Delete the stored certificate
            old_path = str(self.cert_path)
            if self.cert_path.exists():
                self.cert_path.unlink()

            # Also try to delete the user reference copy
            home_cert_file = (
                Path.home()
                / f"fastapilocalhttps-{self.client.host}-{self.client.port}.crt"
            )
            if home_cert_file.exists():
                home_cert_file.unlink()

            self.cert_path = None

            return True, f"Certificate revoked: {old_path}"

        except Exception as e:
            return False, f"Failed to revoke certificate: {str(e)}"
