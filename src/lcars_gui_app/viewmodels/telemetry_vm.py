"""Telemetry ViewModel for LCARS GUI application."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, Signal

from lcars_gui_app.models.telemetry import (
    LatestSnapshotMailbox,
    TelemetrySnapshot,
    TieredPsutilCollector,
)


class TelemetryViewModel(QObject):
    """Bridges coalesced psutil snapshots to LCARS UI state."""

    display_temp_changed = Signal(str)

    def __init__(
        self,
        mailbox: Optional[LatestSnapshotMailbox] = None,
        collector: Optional[TieredPsutilCollector] = None,
        parent: Optional[QObject] = None,
    ) -> None:
        """Initialize the ViewModel with optional mailbox and collector."""
        super().__init__(parent)
        self.mailbox = mailbox or LatestSnapshotMailbox()
        self.collector = collector or TieredPsutilCollector(mailbox=self.mailbox)
        self.latest_snapshot: Optional[TelemetrySnapshot] = None

    def start(self) -> None:
        """Start the telemetry collector."""
        self.collector.start()

    def stop(self, timeout_s: float = 2.0) -> None:
        """Stop the telemetry collector with an optional timeout."""
        self.collector.stop(timeout_s=timeout_s)

    def refresh(self) -> Optional[TelemetrySnapshot]:
        """Fetch the latest telemetry snapshot and emit display updates."""
        snap = self.mailbox.consume()
        if snap is not None:
            self.latest_snapshot = snap
            temp_c = snap.sensors.max_temp_c
            formatted = f"{temp_c:.1f} °C" if temp_c is not None else "N/A"
            self.display_temp_changed.emit(formatted)
        return self.latest_snapshot


# Built by referencing the PySide6 Signal & Slot official documentation
# https://doc.qt.io/qtforpython-6/PySide6/QtCore/Signal.html
