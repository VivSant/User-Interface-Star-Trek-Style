"""Utility functions for the LCARS GUI application."""

from PySide6.QtCore import QObject, Signal, Slot

from lcars_gui_app.models.telemetry import TelemetryModel


class TelemetryViewModel(QObject):
    """Transforms raw telemetry into LCARS-formatted UI states."""

    display_temp_changed = Signal(str)

    def __init__(self, model: TelemetryModel):
        """Initialize the view model and connect telemetry updates from the model."""
        super().__init__()
        self._model = model
        # get raw data
        self._model.raw_warp_core_temp_changed.connect(self.on_raw_temp_received)

    @Slot(float)
    def on_raw_temp_received(self, raw_temp: float):
        """Format the raw sensor data for sci-fi display."""
        # e.g., convert 3456.789 to "CORE TEMP: 3456.8 K"
        formatted_string = f"CORE TEMP: {raw_temp:.1f} K"
        self.display_temp_changed.emit(formatted_string)


# This was built by referencing PySide6 Signals and Slots, find it here:
# https://doc.qt.io/qtforpython-6/tutorials/basictutorial/signals_and_slots.html
