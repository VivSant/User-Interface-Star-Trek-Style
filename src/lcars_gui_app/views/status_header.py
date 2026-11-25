"""Top LCARS status bar and telemetry readout widget."""

import socket

from PySide6.QtCore import Qt, QTime, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from lcars_gui_app.viewmodels.telemetry_vm import TelemetryViewModel
from lcars_gui_app.views.layout_tokens import (
    GAP_COMPACT,
    LCARS_AMBER,
    LCARS_BG,
    LCARS_GOLD,
    LCARS_LAVENDER,
)


def _probe_network_status() -> str:
    """Check basic outbound network reachability with a short timeout.

    Returns:
        Formatted network status string for the LCARS header block.
    """
    try:
        with socket.create_connection(("1.1.1.1", 53), timeout=0.5):
            return "NETWORK: CONNECTED"
    except OSError:
        pass

    try:
        socket.gethostbyname("localhost")
        return "NETWORK: LOCAL ONLY"
    except OSError:
        return "NETWORK: OFFLINE"


class LcarsStatusHeader(QWidget):
    """Top LCARS status block strip and telemetry readout bound to ViewModel."""

    def __init__(
        self,
        viewmodel: TelemetryViewModel,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize status bar blocks, live clock, and telemetry readouts.

        Args:
            viewmodel: ViewModel supplying network, metadata, clock, and telemetry data.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.setObjectName("lcarsStatusHeader")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._viewmodel_drives_clock = False
        self._viewmodel_drives_network = False

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(GAP_COMPACT)

        blocks_row = QHBoxLayout()
        blocks_row.setContentsMargins(0, 0, 0, 0)
        blocks_row.setSpacing(GAP_COMPACT)

        self._network_block = self._make_block("NETWORK: CHECKING", "#3366ff")
        self._metadata_block = self._make_block("METADATA", "#664d66")
        self._operator_block = self._make_block("Star Commander Morris", "#886688")
        self._clock_block = self._make_block(
            QTime.currentTime().toString("HH:mm:ss"),
            LCARS_LAVENDER,
        )

        blocks_row.addWidget(self._network_block, stretch=2)
        blocks_row.addWidget(self._metadata_block, stretch=2)
        blocks_row.addWidget(self._operator_block, stretch=2)
        blocks_row.addWidget(self._clock_block, stretch=1)

        telemetry_row = QHBoxLayout()
        telemetry_row.setContentsMargins(0, 0, 0, 0)
        telemetry_row.setSpacing(12)

        self._telemetry_label = self._make_telemetry_label("CORE TEMP: OFFLINE")
        self._cpu_label = self._make_telemetry_label("CPU: --.-%")
        self._memory_label = self._make_telemetry_label("MEM: --.- / --.- GiB")

        telemetry_row.addWidget(self._telemetry_label, stretch=1)
        telemetry_row.addWidget(self._cpu_label, stretch=1)
        telemetry_row.addWidget(self._memory_label, stretch=1)

        root_layout.addLayout(blocks_row)
        root_layout.addLayout(telemetry_row)

        self._bind_viewmodel(viewmodel)
        self._setup_timers()

    def _make_block(self, text: str, fill_color: str) -> QLabel:
        """Create an LCARS-styled top status block label.

        Args:
            text: Initial text rendered inside the block.
            fill_color: Background color hex string for the block.

        Returns:
            Configured QLabel status block.
        """
        label = QLabel(text, self)
        label.setMinimumWidth(0)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFrameShape(QFrame.Shape.NoFrame)
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        label.setFixedHeight(44)
        label.setStyleSheet(
            f"background-color: {fill_color}; color: #ffffff; "
            "font-weight: bold; border-radius: 6px; padding: 0 8px;"
        )
        return label

    def _make_telemetry_label(self, text: str) -> QLabel:
        """Create an LCARS-styled telemetry readout label.

        Args:
            text: Initial readout string.

        Returns:
            Configured QLabel telemetry readout.
        """
        label = QLabel(text, self)
        label.setMinimumWidth(0)
        label.setStyleSheet(
            f"color: {LCARS_AMBER}; background-color: {LCARS_BG}; "
            "font-size: 18px; font-weight: bold; padding: 2px 0;"
        )
        return label

    def _bind_viewmodel(self, viewmodel: TelemetryViewModel) -> None:
        """Populate initial ViewModel state and connect available update signals.

        Args:
            viewmodel: Source TelemetryViewModel instance.
        """
        for attr_name in ("operator_label", "commander_name", "operator_name"):
            value = getattr(viewmodel, attr_name, None)
            if value:
                self.set_operator_label(str(value))
                break

        network_text = getattr(viewmodel, "network_status", None)
        if network_text:
            self._viewmodel_drives_network = True
            self.set_network_status(str(network_text))

        metadata_text = getattr(viewmodel, "metadata_status", None)
        if metadata_text:
            self.set_metadata_status(str(metadata_text))

        clock_text = getattr(viewmodel, "clock_text", None)
        if clock_text:
            self._viewmodel_drives_clock = True
            self.set_clock_text(str(clock_text))

        core_temp = getattr(viewmodel, "core_temp_text", None)
        if core_temp:
            self.set_core_temp(str(core_temp))

        cpu_text = getattr(viewmodel, "cpu_text", None)
        if cpu_text:
            self.set_cpu_text(str(cpu_text))

        memory_text = getattr(viewmodel, "memory_text", None)
        if memory_text:
            self.set_memory_text(str(memory_text))

        signal_map = {
            "network_status_changed": self._on_vm_network_status,
            "metadata_status_changed": self.set_metadata_status,
            "operator_label_changed": self.set_operator_label,
            "clock_text_changed": self._on_vm_clock_text,
            "core_temp_changed": self.set_core_temp,
            "cpu_changed": self.set_cpu_text,
            "memory_changed": self.set_memory_text,
        }
        for signal_name, slot in signal_map.items():
            sig = getattr(viewmodel, signal_name, None)
            if sig is not None and hasattr(sig, "connect"):
                sig.connect(slot)

    def _setup_timers(self) -> None:
        """Start periodic timers for live clock ticks and network status checks."""
        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(1000)
        self._clock_timer.timeout.connect(self._tick_clock)
        self._clock_timer.start()

        QTimer.singleShot(0, self._refresh_network_status)
        self._network_timer = QTimer(self)
        self._network_timer.setInterval(10_000)
        self._network_timer.timeout.connect(self._refresh_network_status)
        self._network_timer.start()

    def _tick_clock(self) -> None:
        """Advance the clock block every second when not driven by ViewModel."""
        if not self._viewmodel_drives_clock:
            self._clock_block.setText(QTime.currentTime().toString("HH:mm:ss"))

    def _refresh_network_status(self) -> None:
        """Refresh the network block when not driven by ViewModel."""
        if not self._viewmodel_drives_network:
            self._network_block.setText(_probe_network_status())

    def _on_vm_clock_text(self, text: str) -> None:
        """Handle explicit clock updates pushed by TelemetryViewModel.

        Args:
            text: Formatted clock string from ViewModel.
        """
        self._viewmodel_drives_clock = True
        self.set_clock_text(text)

    def _on_vm_network_status(self, text: str) -> None:
        """Handle explicit network status updates pushed by TelemetryViewModel.

        Args:
            text: Network status string from ViewModel.
        """
        self._viewmodel_drives_network = True
        self.set_network_status(text)

    def set_network_status(self, text: str) -> None:
        """Update the network status block text.

        Args:
            text: Network connection status string.
        """
        self._network_block.setText(text)

    def set_metadata_status(self, text: str) -> None:
        """Update the metadata status block text.

        Args:
            text: Metadata summary string.
        """
        self._metadata_block.setText(text)

    def set_operator_label(self, text: str) -> None:
        """Update the operator/commander status block text.

        Args:
            text: Operator display label.
        """
        self._operator_block.setText(text)

    def set_clock_text(self, text: str) -> None:
        """Update the timestamp/clock block text.

        Args:
            text: Formatted time string.
        """
        self._clock_block.setText(text)

    def set_core_temp(self, text: str) -> None:
        """Update the primary core temperature telemetry readout.

        Args:
            text: Formatted core temperature or offline status string.
        """
        self._telemetry_label.setText(text)
        has_reading = "OFFLINE" not in text.upper()
        self._telemetry_label.setStyleSheet(
            f"color: {LCARS_GOLD if has_reading else LCARS_AMBER}; "
            f"background-color: {LCARS_BG}; "
            "font-size: 18px; font-weight: bold; padding: 2px 0;"
        )

    def set_cpu_text(self, text: str) -> None:
        """Update the CPU utilization telemetry readout.

        Args:
            text: Formatted CPU utilization string.
        """
        self._cpu_label.setText(text)

    def set_memory_text(self, text: str) -> None:
        """Update the memory usage telemetry readout.

        Args:
            text: Formatted memory usage string.
        """
        self._memory_label.setText(text)
