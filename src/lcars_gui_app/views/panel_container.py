"""Inner LCARS panel container with scroll and overflow guardrails."""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFontMetrics, QResizeEvent
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from lcars_gui_app.views.layout_tokens import (
    CONTROL_MIN_HEIGHT,
    FONT_SIZE_HEADER,
    GAP_COMPACT,
    MARGIN_COMPACT,
    PILL_RADIUS,
)


class _PanelTitleLabel(QLabel):
    """Panel header label that truncates long titles with an ellipsis."""

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        """Initialize a panel title label.

        Args:
            text: Full title text to display or truncate.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self._full_text = text
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(CONTROL_MIN_HEIGHT)
        font = self.font()
        font.setPointSize(FONT_SIZE_HEADER)
        font.setBold(True)
        self.setFont(font)
        self._refresh_text()

    def set_full_text(self, text: str) -> None:
        """Set the full panel title and refresh truncated rendering.

        Args:
            text: Full panel title text.
        """
        self._full_text = text
        self.setToolTip(text)
        self._refresh_text()

    def resizeevent(self, event: QResizeEvent) -> None:
        """Recompute truncated title text when the label width changes.

        Args:
            event: Resize event for the title label.
        """
        super().resizeEvent(event)
        if event.size().width() != event.oldSize().width():
            self._refresh_text()

    def _refresh_text(self) -> None:
        """Truncate title text with right-side ellipsis to fit available width."""
        available_width = max(self.width(), 0)
        metrics = QFontMetrics(self.font())
        super().setText(
            metrics.elidedText(
                self._full_text, Qt.TextElideMode.ElideRight, available_width
            )
        )


class LcarsPanelContainer(QFrame):
    """Modular LCARS panel frame with isolated scrolling and overflow guardrails.

    Attributes:
        body_layout: Vertical layout inside the scrollable panel body.
    """

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        """Initialize the panel header and isolated scroll area.

        Args:
            title: Header title displayed at the top of the panel.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.setObjectName("lcarsPanelContainer")
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._build_ui(title)

        # Defer initial truncation until the widget receives its first geometry
        QTimer.singleShot(0, lambda: self._title_label.set_full_text(title))

    def set_title(self, title: str) -> None:
        """Update the panel header title and tooltip.

        Args:
            title: New panel header text.
        """
        self._title_label.set_full_text(title)

    def set_body_widget(self, widget: QWidget) -> None:
        """Replace or set the main scrollable body widget inside the panel.

        Args:
            widget: Widget placed inside the vertical scroll area.
        """
        widget.setMinimumWidth(0)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        while self.body_layout.count():
            item = self.body_layout.takeAt(0)
            if item is not None and item.widget() is not None:
                item.widget().setParent(None)
        self.body_layout.addWidget(widget)

    def add_body_widget(self, widget: QWidget, stretch: int = 0) -> None:
        """Append a child widget into the scrollable panel body.

        Args:
            widget: Widget to append to the panel body.
            stretch: Layout stretch factor inside body_layout.
        """
        widget.setMinimumWidth(0)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.body_layout.addWidget(widget, stretch=stretch)

    def _build_ui(self, title: str) -> None:
        """Construct header bar and scroll-isolated body container.

        Args:
            title: Initial panel title.
        """
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(
            MARGIN_COMPACT, MARGIN_COMPACT, MARGIN_COMPACT, MARGIN_COMPACT
        )
        outer_layout.setSpacing(GAP_COMPACT)

        self._header_bar = QFrame(self)
        self._header_bar.setObjectName("lcarsPanelHeader")
        self._header_bar.setMinimumWidth(0)
        self._header_bar.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._header_bar.setStyleSheet(
            f"#lcarsPanelHeader {{ border-radius: {PILL_RADIUS}px; }}"
        )

        header_layout = QVBoxLayout(self._header_bar)
        header_layout.setContentsMargins(MARGIN_COMPACT, 2, MARGIN_COMPACT, 2)
        header_layout.setSpacing(0)

        self._title_label = _PanelTitleLabel(title, self._header_bar)
        header_layout.addWidget(self._title_label)

        self._scroll_area = QScrollArea(self)
        self._scroll_area.setObjectName("lcarsPanelScrollArea")
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setMinimumWidth(0)
        self._scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self._scroll_area.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        self._scroll_content = QWidget(self._scroll_area)
        self._scroll_content.setMinimumWidth(0)
        self._scroll_content.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )

        self.body_layout = QVBoxLayout(self._scroll_content)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(GAP_COMPACT)

        self._scroll_area.setWidget(self._scroll_content)

        outer_layout.addWidget(self._header_bar, stretch=0)
        outer_layout.addWidget(self._scroll_area, stretch=1)
