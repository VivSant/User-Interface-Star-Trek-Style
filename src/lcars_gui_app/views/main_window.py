"""Main Window for the LCARS GUI application."""

from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from lcars_gui_app.viewmodels.telemetry_vm import TelemetryViewModel
from lcars_gui_app.views.layout_tokens import GAP_COMPACT, LCARS_BG, LayoutTier
from lcars_gui_app.views.outer_shell import LcarsOuterShell
from lcars_gui_app.views.panel_grid import LcarsPanelGrid
from lcars_gui_app.views.status_header import LcarsStatusHeader


class LcarsMainWindow(QMainWindow):
    """Main LCARS application window bound to TelemetryViewModel."""

    def __init__(
        self,
        viewmodel: TelemetryViewModel,
        panel_grid: LcarsPanelGrid | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize the main window with the ViewModel and outer LCARS shell.

        Args:
            viewmodel: ViewModel supplying telemetry and UI state.
            panel_grid: Optional responsive panel grid hosted inside the shell.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle("LCARS Main Terminal")
        self.setStyleSheet(f"background-color: {LCARS_BG};")

        self.viewmodel = viewmodel
        self.panel_grid = panel_grid or LcarsPanelGrid(self)
        self.outer_shell = LcarsOuterShell(self)
        self.outer_shell.set_content_widget(self.panel_grid)

        host = QWidget(self)
        host.setObjectName("lcarsWindowHost")
        host.setStyleSheet(f"background-color: {LCARS_BG};")

        host_layout = QVBoxLayout(host)
        host_layout.setContentsMargins(0, 0, 0, 0)
        host_layout.setSpacing(GAP_COMPACT)

        self.status_header = LcarsStatusHeader(self.viewmodel, host)
        host_layout.addWidget(self.status_header)
        host_layout.addWidget(self.outer_shell, stretch=1)
        self.setCentralWidget(host)

        self.outer_shell.tier_changed.connect(self._on_layout_tier_changed)
        if self.outer_shell.active_tier is not None:
            self.panel_grid.set_tier(self.outer_shell.active_tier)

    def _on_layout_tier_changed(self, tier: LayoutTier) -> None:
        """Reflow panels when LcarsOuterShell transitions to a new tier.

        Args:
            tier: Newly active LayoutTier.
        """
        self.panel_grid.set_tier(tier)


# This was built by referencing PySide6 QMainWindow, find it here:
# https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QMainWindow.html
