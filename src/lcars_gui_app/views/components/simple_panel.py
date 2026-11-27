"""Simple panel for displaying content in the LCARS application."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget

from lcars_gui_app.views.layout_tokens import FONT_SIZE_HEADER, LCARS_AMBER


class SimplePanel(QWidget):
    """Placeholder page that shows a centered title.

    Used as a stand-in for real pages inside the main window's page stack.
    """

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        """Initialize the panel with a centered title label.

        Args:
            title: Text shown in the middle of the panel.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel(title, self)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet(
            f"color: {LCARS_AMBER}; font-size: {FONT_SIZE_HEADER * 2}px;"
            " font-weight: bold;"
        )
        layout.addWidget(self.title_label)


# This was built by referencing PySide6 QLabel, find it here:
# https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QLabel.html
