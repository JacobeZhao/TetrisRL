from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont, QPainter, QPen, QBrush
from PyQt6.QtWidgets import QSplashScreen, QWidget, QVBoxLayout, QLabel, QProgressBar, QApplication


class SplashScreen(QSplashScreen):
    """Splash screen with progress indicator for loading heavy components."""

    def __init__(self, app: QApplication) -> None:
        # Create a custom pixmap
        pixmap = QWidget().grab()
        super().__init__(pixmap)
        self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

        self._steps = [
            ("Initializing PyTorch...", 0),
            ("Loading model architecture...", 20),
            ("Initializing Tetris environment...", 40),
            ("Setting up training components...", 60),
            ("Preparing UI...", 80),
            ("Ready!", 100),
        ]
        self._current_step = 0

        # Create a custom widget for the splash content
        self._widget = QWidget()
        self._widget.setFixedSize(400, 200)
        self._widget.setStyleSheet("""
            QWidget {
                background-color: #0f1016;
                border: 2px solid #2b2d3a;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(self._widget)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title
        title = QLabel("Tetris RL")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setStyleSheet("color: #cfd2ff;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Status label
        self._status_label = QLabel("Initializing...")
        self._status_label.setFont(QFont("Arial", 10))
        self._status_label.setStyleSheet("color: #a0a3b8;")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status_label)

        # Progress bar
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #2b2d3a;
                border-radius: 6px;
                background-color: #1a1d26;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #3a7bd5;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self._progress)

        # Version info
        version = QLabel("PPO + Ray | Deep Reinforcement Learning")
        version.setFont(QFont("Arial", 9))
        version.setStyleSheet("color: #6a6d7a;")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        # Set the widget as the splash content
        self.setWidget(self._widget)

    def setWidget(self, widget: QWidget) -> None:
        """Set the widget to display."""
        if hasattr(self, '_central_widget'):
            self._central_widget.deleteLater()
        self._central_widget = widget
        self.resize(widget.size())

    def update_progress(self, step: int) -> None:
        """Update progress to the given step index."""
        if 0 <= step < len(self._steps):
            self._current_step = step
            text, value = self._steps[step]
            self._status_label.setText(text)
            self._progress.setValue(value)
            QApplication.processEvents()

    def set_status(self, text: str) -> None:
        """Set custom status text."""
        self._status_label.setText(text)
        QApplication.processEvents()

    def set_progress(self, value: int) -> None:
        """Set progress value (0-100)."""
        self._progress.setValue(max(0, min(100, value)))
        QApplication.processEvents()
