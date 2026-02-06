"""
Rope Roller Maker - Desktop Application
Entry point for the PyQt6-based desktop app.

This is the "hello world" version - just opens a window to verify
that Python and PyQt6 are working correctly.
"""

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtCore import Qt


class RopeRollerWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # Window setup
        self.setWindowTitle("Rope Roller Maker")
        self.setMinimumSize(800, 600)

        # Simple centered label to confirm everything works
        label = QLabel("Rope Roller Maker\n\nPyQt6 is working!")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            font-size: 24px;
            color: #d4521f;
            font-weight: bold;
        """)

        # Set the label as the central widget
        # (Later this will be replaced with the real UI layout)
        self.setCentralWidget(label)


def main():
    """Launch the application."""
    app = QApplication(sys.argv)
    window = RopeRollerWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
