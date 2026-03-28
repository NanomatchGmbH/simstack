"""
Example integration of SSL certificate trust workflow.

This demonstrates how to integrate the SSLCertificateHandler into
the existing SimStack application connection flow.
"""

from typing import Optional
from PySide6.QtWidgets import QApplication, QMessageBox
from simstack.view.SSLCertificateDialog import SSLCertificateHandler


def connect_to_fastapi_server(
    server_url: str, parent=None
) -> tuple[bool, Optional[str]]:
    """
    Connect to a FastAPI server with SSL certificate handling.

    This is an example function showing how to integrate the SSL certificate
    handler into your connection workflow. You would call this from your
    connection logic (e.g., in SSHConnector or a new REST connector).

    Args:
        server_url: URL of the FastAPI server (e.g., "https://127.0.0.1:8443")
        parent: Parent widget for dialogs

    Returns:
        Tuple of (success: bool, message: Optional[str])

    Example:
        >>> success, msg = connect_to_fastapi_server("https://127.0.0.1:8443")
        >>> if success:
        >>>     print("Connected successfully!")
        >>> else:
        >>>     print(f"Connection failed: {msg}")
    """
    handler = SSLCertificateHandler(server_url, parent)

    # Handle the SSL certificate trust workflow
    success, message = handler.handle_ssl_certificate_trust()

    if success:
        # Connection successful - you can now make requests to the server
        # Example: Initialize your REST client with the trusted certificate
        cert_path = handler.get_certificate_path()
        if cert_path:
            print(f"Using certificate at: {cert_path}")

        # TODO: Initialize your REST API client here
        # e.g., self._api_client = FastAPIClient(server_url, cert_path)

    return success, message


def example_connection_flow():
    """
    Example connection flow showing the SSL certificate workflow.

    This demonstrates how you might integrate this into WFEditorApplication
    or SSHConnector for REST API connections.
    """
    import sys

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Example server URL - this would come from your settings/registry
    server_url = "https://127.0.0.1:8443"

    # Connect with SSL certificate handling
    success, message = connect_to_fastapi_server(server_url)

    if success:
        QMessageBox.information(
            None,
            "Connection Successful",
            f"Successfully connected to server:\n{server_url}\n\n{message}",
        )
    else:
        QMessageBox.warning(
            None,
            "Connection Failed",
            f"Failed to connect to server:\n{server_url}\n\n{message}",
        )

    return success


# Integration point for WFEditorApplication or SSHConnector
# --------------------------------------------------------
#
# To integrate this into your application:
#
# 1. In SSHConnector or a new RestConnector class, add a method like:
#
#    def _connect_to_rest_api(self, registry_name: str):
#        registry = self._registries[registry_name]
#        server_url = registry.api_url  # or however you store the REST API URL
#
#        handler = SSLCertificateHandler(server_url, parent=self.parent)
#        success, message = handler.handle_ssl_certificate_trust()
#
#        if not success:
#            self._logger.error(f"SSL certificate error: {message}")
#            self._view_manager.show_error(
#                f"Failed to establish secure connection to {registry_name}:\n\n{message}"
#            )
#            return False
#
#        # Initialize your REST client with the certificate
#        cert_path = handler.get_certificate_path()
#        self._init_rest_client(server_url, cert_path)
#        return True
#
# 2. Call this method when connecting to a registry that uses REST API
#
# 3. Store the certificate path for subsequent requests


if __name__ == "__main__":
    example_connection_flow()
