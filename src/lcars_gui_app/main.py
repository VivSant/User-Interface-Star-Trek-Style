"""Initialize and launch the LCARS-style telemetry application."""

import sys

from PySide6.QtWidgets import QApplication, QHBoxLayout, QWidget

# mvvm components
from lcars_gui_app.models.telemetry import TelemetryModel
from lcars_gui_app.viewmodels.telemetry_vm import TelemetryViewModel

# qt components
from lcars_gui_app.views.components.file_explorer import FileExplorerPanel
from lcars_gui_app.views.main_window import LcarsMainWindow


def main():
    """Initialize the application and launch the main window."""
    app = QApplication(sys.argv)

    # mvvm initialization
    telemetry_model = TelemetryModel()
    telemetry_vm = TelemetryViewModel(telemetry_model)

    # ui initialization
    main_window = LcarsMainWindow(telemetry_vm)
    file_explorer = FileExplorerPanel()

    # combine for proof of concept
    central_widget = QWidget()
    layout = QHBoxLayout(central_widget)
    layout.addWidget(file_explorer)
    layout.addWidget(main_window.centralWidget())
    main_window.setCentralWidget(central_widget)

    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()


# This was built by referencing PySide6 QApplication Initialization, find it here:
# https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QApplication.html
