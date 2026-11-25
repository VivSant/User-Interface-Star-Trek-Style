"""Main Window for the LCARS GUI application."""

from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from lcars_gui_app.views.components.nav_button import NavButton
from lcars_gui_app.views.components.bottom_bar import BottomBar
from lcars_gui_app.views.components.simple_panel import SimplePanel
from lcars_gui_app.viewmodels.telemetry_vm import TelemetryViewModel
from lcars_gui_app.views.layout_tokens import GAP_COMPACT, LCARS_BG, LayoutTier
from lcars_gui_app.views.outer_shell import LcarsOuterShell
from lcars_gui_app.views.panel_grid import LcarsPanelGrid
from lcars_gui_app.views.status_header import LcarsStatusHeader
from lcars_gui_app.core.boot_sequence import BootSequence
from lcars_gui_app.core.audio_engine import AudioEngine

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

        #Top status headr
        self.status_header = LcarsStatusHeader(self.viewmodel, host)
        host_layout.addWidget(self.status_header)
        
        #Middle section: Left Navigation and Main content
        middle = QHBoxLayout()
        middle.setSpacing(6)

        #Left Navigation
        nav_layout = QVBoxLayout()
        nav_layout.setSpacing(6)

        self.btn_file = NavButton("File Manager", "#4A9EFF")
        self.btn_devices = NavButton("Devices", "#E8E8F0")
        self.btn_network = NavButton("Network\nOptions", "#FFCC99")
        self.btn_settings = NavButton("Settings", "#FF9933")

        nav_layout.addWidget(self.btn_file)
        nav_layout.addWidget(self.btn_devices)
        nav_layout.addWidget(self.btn_network)
        nav_layout.addWidget(self.btn_settings)
        nav_layout.addStretch()

        middle.addLayout(nav_layout)

        self.stack = QStackedWidgets()
        self.stack.addWidget(SimplePanel("HOME / DASHBOARD"))
        self.stack.addWidget(SimplePanel("FILE MANAGER"))
        self.stack.addWidget(SimplePanel("DEVICES"))
        self.stack.addWidget(SimplePanel("NETWORK OPTIONS"))
        self.stack.addWidget(SimplePanel("SETTINGS"))

        middle.addWidget(self.stack, stretch=1)

        host_layout.addLayout(middle, stretch=1)

        #Bottom bar
        self.bottom_bar = BottomBar()
    
self.bottom_bar.power_clicked.connect(self._on_power_clicked)

        host_layout.addWidget(self.bottom_bar)

        self.setCentralWidget(host)


        self.btn_file.clicked.connect(lambda:
self.stack.setCurrentIndex(1))
        self.btn_devices.clicked.connect(lambda:
self.stack.setCurrentIndex(2))
        self.btn_network.clicked.connect(lambda:
self.stack.setCurrentIndex(3))
        self.btn_settings.clicked.connect(lambda:
self.stack.setCurrentIndex(4))

self.outer_shell.tier_changed.connect(self._on_layout_tier_changed)
        if self.outer_shell.active_tier is not None:

self.panel_grid.set_tier(self.outer_shell.active_tier)

        self.audio = AudioEngine()
        self.audio.load("boot_1", "boot_1.wav")
        self.audio.load("power", "power.wav")

        self.boot = BootSequence(self.audio)

self.boot.message_changed.connect(self._on_boot_message)
        self.boot.finished.connect(self._on_boot_finished)
        self.boot.start()

    def _on_layout_tier_changed(self, tier: LayoutTier) -> None:
        """Reflow panels when LcarsOuterShell transitions to a new tier.

        Args:
            tier: Newly active LayoutTier.
        """
        self.panel_grid.set_tier(tier)
    
    def _on_power_clicked(self):
        self.audio.play("power")
        print("POWER pressed")

    def _on_boot_message(self, message: str):
       slef.status_header.set_network_status(message)

    def _on_boot_finished(self):
        self.status_header.set_network_status("NETWORK: CONNECTED")
        print("Boot sequence complete")

# This was built by referencing PySide6 QMainWindow, find it here:
# https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QMainWindow.html