"""Power Button + Misc + Release Number."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class BottomBar(QWidget):
    """Bottom bar with power button, misc, and release number."""

    power_clicked = Signal()

    def __init__(self, parent=None):
        """Initializes bottom bar with power button, misc, and release number."""
        super().__init__(parent)
        self.setFixedHeight(50)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Power Button
        self.power_btn = QPushButton("POWER")
        self.power_btn.setFixedWidth(150)
        self.power_btn.setStyleSheet(
            """QPushButton { background: transparent; color: #FF2222; font_size: 26px;
            font_weight: bold; border: none;} QPushButton:hover { color: #FF6666;}"""
        )

        self.power_btn.clicked.connect(self.power_clicked.emit)

        # Misc
        misc = QLabel("Misc")
        misc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        misc.setStyleSheet(
            "background:#6B4C6B; color:white; font-weight:bold; padding:8px;"
        )

        # Release
        release = QLabel("Release NUMBER")
        release.setAlignment(Qt.AlignmentFlag.AlignCenter)
        release.setStyleSheet(
            "background:#8B6B8B; color:white; font-weight:bold; padding:8px;"
        )

        layout.addWidget(self.power_btn)
        layout.addWidget(misc, 3)
        layout.addWidget(release, 2)
