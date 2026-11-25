"""Settings panel widget for LCARS GUI views."""

from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget


class SettingsPanel(QWidget):
    """Placeholder settings panel widget hosted inside an LCARS panel container."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the settings panel layout and placeholder label.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.setObjectName("settingsPanel")
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        status_label = QLabel("SYSTEM SETTINGS READY", self)
        status_label.setMinimumWidth(0)
        layout.addWidget(status_label)
