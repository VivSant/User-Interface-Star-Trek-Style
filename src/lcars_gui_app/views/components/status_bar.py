"""Top status bar: Network | Metadata | Device Name | Time."""

from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from lcars_gui_app.models.network_status import ConnectionState, NetworkStatus


class StatusBar(QWidget):
    """Top LCARS status bar displaying network state, metadata, device, and clock."""

    def __init__(self, parent=None):
        """Initialize status bar labels, layout, and update timers."""
        super().__init__(parent)
        self.setFixedHeight(42)

        self.network_status = NetworkStatus()

        # Labels
        self.network_lbl = QLabel("Network: Checking...")
        self.meta_lbl = QLabel("Metadata")
        self.device_lbl = QLabel("Star Commander Morris")
        self.time_lbl = QLabel("--:--:--")

        for lbl in (self.network_lbl, self.meta_lbl, self.device_lbl, self.time_lbl):
            lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        # Layout (created once outside the loop)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self.network_lbl, 3)
        layout.addWidget(self.meta_lbl, 2)
        layout.addWidget(self.device_lbl, 2)
        layout.addWidget(self.time_lbl, 2)

        self._apply_base_styles()

        # Timers (clock every 1s, network every 5s)
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)

        self.network_timer = QTimer(self)
        self.network_timer.timeout.connect(self._update_network)
        self.network_timer.start(5000)

        # Initial update
        self._update_clock()
        self._update_network()

    def _apply_base_styles(self) -> None:
        self.meta_lbl.setStyleSheet(
            "background:#6B4C6B; color:white; padding:6px; "
            "border-radius:3px; font-weight:bold;"
        )
        self.device_lbl.setStyleSheet(
            "background:#8B6B8B; color:white; padding:6px; "
            "border-radius:3px; font-weight:bold;"
        )
        self.time_lbl.setStyleSheet(
            "background:#C08BC0; color:white; padding:6px; "
            "border-radius:3px; font-weight:bold;"
        )

    def _update_clock(self) -> None:
        """Update the displayed local time."""
        self.time_lbl.setText(datetime.now().strftime("%H:%M:%S"))

    def _update_network(self) -> None:
        """Refresh and render current network connection status."""
        self.network_status.refresh()

        if self.network_status.state == ConnectionState.CONNECTED:
            text = "Network: Connected"
            if self.network_status.local_ip:
                text += f"  ({self.network_status.local_ip})"
            style = (
                "background:#1E6BFF; color:white; font-weight:bold; "
                "padding:6px; border-radius:3px;"
            )
        else:
            text = "Network: Disconnected"
            style = (
                "background:#AA2222; color:white; font-weight:bold; "
                "padding:6px; border-radius:3px;"
            )

        self.network_lbl.setText(text)
        self.network_lbl.setStyleSheet(style)

    def force_network_check(self) -> None:
        """Trigger an immediate network status check."""
        self._update_network()


# Built by referencing PySide6 QHBoxLayout & QTimer official documentation
# https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QHBoxLayout.html and
# https://doc.qt.io/qtforpython-6/PySide6/QtCore/QTimer.html
