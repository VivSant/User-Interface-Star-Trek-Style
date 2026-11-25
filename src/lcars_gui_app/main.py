"""Entry point for the LCARS GUI application.

This module initializes the application, sets up the main window,
and starts the telemetry collection.
It uses PySide6 for the GUI and psutil for system telemetry data collection.
"""

from __future__ import annotations

import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from lcars_gui_app.models.telemetry import (
    LatestSnapshotMailbox,
    TelemetrySnapshot,
    TieredPsutilCollector,
)
from lcars_gui_app.viewmodels.telemetry_vm import TelemetryViewModel
from lcars_gui_app.views.main_window import LcarsMainWindow


def main() -> int:
    """Entry point for the LCARS GUI application."""
    app = QApplication(sys.argv)

    mailbox = LatestSnapshotMailbox()
    collector = TieredPsutilCollector(mailbox=mailbox)

    # Pass mailbox/collector into MainWindow (or your viewmodel)
    window = LcarsMainWindow(viewmodel=TelemetryViewModel())
    window.show()

    poll_timer = QTimer()
    poll_timer.setInterval(250)

    def _on_ui_tick() -> None:
        snapshot: TelemetrySnapshot | None = mailbox.consume()
        if snapshot is None:
            return
        # Update MainWindow / telemetry_vm from `snapshot`

    poll_timer.timeout.connect(_on_ui_tick)
    poll_timer.start()

    def _shutdown() -> None:
        poll_timer.stop()
        collector.stop(timeout_s=2.0)

    app.aboutToQuit.connect(_shutdown)
    collector.start()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())


# Built by referencing the official psutil & PySide6 documentation
# https://psutil.readthedocs.io/ and https://doc.qt.io/qtforpython-6/PySide6/QtCore/QTimer.html
