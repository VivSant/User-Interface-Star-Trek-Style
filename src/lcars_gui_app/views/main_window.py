"""Main window view for the LCARS GUI application."""

from PySide6.QtCore import Slot
from PySide6.QtWidgets import QLabel, QMainWindow, QVBoxLayout, QWidget

from lcars_gui_app.viewmodels.telemetry_vm import TelemetryViewModel
from lcars_gui_app.views.components.status_bar import StatusBar


class LcarsMainWindow(QMainWindow):
    """Declarative ui root leveraging Qt's main window framework."""

    def __init__(self, viewmodel: TelemetryViewModel):
        """Initialize the main window with its telemetry view model."""
        super().__init__()
        self._viewmodel = viewmodel

        self.setWindowTitle("LCARS Main Terminal")
        self.resize(1920, 1080)  # Target screen resolution
        self.setStyleSheet("background-color: #000000;")  # LCARS black background

        # Central layout
        container = QWidget()
        self.setCentralWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.status_bar = StatusBar()
        layout.addWidget(self.status_bar)

        self.temp_label = QLabel("CORE TEMP: OFFLINE")
        self.temp_label.setStyleSheet(
            "color: #FF9900; font-size: 24px; font-weight: bold;"
        )
        layout.addWidget(self.temp_label)

        # Strech so the content stays at the top
        layout.addStretch()

        # connect viewmodel updates
        self._viewmodel.display_temp_changed.connect(self.update_temp_display)

    @Slot(str)
    def update_temp_display(self, formatted_temp: str):
        """Update the label text when the ViewModel emits new state."""
        self.temp_label.setText(formatted_temp)


# This was built by referencing PySide6 QMainWindow, find it here:
# https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QMainWindow.html
