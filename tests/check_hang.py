"""
Debug script to find what's hanging in the tests
"""

import sys
import signal
import time
import threading
import traceback
from unittest.mock import patch, MagicMock

from PySide6.QtWidgets import QApplication, QWidget

from simstack.view.WFEditorMainWindow import WFEditorMainWindow


def debug_timer():
    """Prints stack traces of all threads after 5 seconds"""
    time.sleep(5)
    print("\n*** DEBUGGING: Printing all thread stacks to diagnose hang ***")
    for th in threading.enumerate():
        print(f"\nThread {th.name}:")
        traceback.print_stack(sys._current_frames()[th.ident])

    # Force terminate after stack traces
    print("\n*** DEBUGGING: Forcibly terminating due to hang ***")
    signal.raise_signal(signal.SIGTERM)


def test_minimal_window():
    """Minimal test that creates a window to see if it hangs"""
    print("Starting minimal test...")

    # Start debug timer
    threading.Thread(target=debug_timer, daemon=True).start()

    # Create real widgets and bypass initialization
    QApplication.instance() or QApplication(sys.argv)
    editor = QWidget()

    with patch.object(WFEditorMainWindow, "_WFEditorMainWindow__init_ui"), patch(
        "simstack.view.WFEditorMainWindow.StatusMessageManager"
    ):
        print("Creating window...")
        window = WFEditorMainWindow(editor)

        # Mock what's needed
        window._status_manager = MagicMock()

        print("Window created, finishing test...")

    # If we got here, no hang occurred
    print("Test completed successfully without hanging")


if __name__ == "__main__":
    test_minimal_window()
