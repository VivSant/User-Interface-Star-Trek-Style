"""Generate randomized telemetry data for demonstration purposes.

This module provides the TelemetryModel, which periodically emits simulated
warp core temperature readings.
"""

import random

from PySide6.QtCore import QObject, QTimer, Signal


class TelemetryModel(QObject):
    """Handles background polling of raw telemetry data."""

    raw_warp_core_temp_changed = Signal(float)

    def __init__(self):
        """Initialize the model and start periodic telemetry polling."""
        super().__init__()
        # polling every 1 second (1000 ms) for demonstration purposes
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._poll_hardware)
        self._timer.start(1000)

    def _poll_hardware(self):
        """Simulate reading a raw sensor value."""
        raw_temp = random.uniform(1000.0, 5000.0)
        self.raw_warp_core_temp_changed.emit(raw_temp)


# This was built by referencing PySide6 Signals and Slots, find it here:
# https://doc.qt.io/qtforpython-6/tutorials/basictutorial/signals_and_slots.html
