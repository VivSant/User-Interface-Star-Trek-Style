"""Entry point for the LCARS GUI application."""

import sys

from PySide6.QtWidgets import QApplication

from lcars_gui_app.viewmodels.telemetry_vm import TelemetryViewModel
from lcars_gui_app.views.components.file_explorer import FileExplorerPanel
from lcars_gui_app.views.components.settings_panel import SettingsPanel
from lcars_gui_app.views.layout_tokens import LCARS_QSS
from lcars_gui_app.views.main_window import LcarsMainWindow
from lcars_gui_app.views.panel_container import LcarsPanelContainer
from lcars_gui_app.views.panel_grid import LcarsPanelGrid


def main() -> int:
    """Create and run the LCARS GUI application.

    Returns:
        Application exit status code.
    """
    app = QApplication(sys.argv)
    app.setStyleSheet(LCARS_QSS)

    viewmodel = TelemetryViewModel()
    panel_grid = LcarsPanelGrid()

    explorer_panel = LcarsPanelContainer("FILE EXPLORER", panel_grid)
    explorer_panel.add_body_widget(FileExplorerPanel())
    panel_grid.add_panel(explorer_panel)

    settings_panel = LcarsPanelContainer("SYSTEM SETTINGS", panel_grid)
    settings_panel.add_body_widget(SettingsPanel(settings_panel))
    panel_grid.add_panel(settings_panel)

    window = LcarsMainWindow(viewmodel, panel_grid=panel_grid)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
