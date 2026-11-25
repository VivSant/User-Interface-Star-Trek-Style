"""Outer LCARS rail, elbow, and viewport shell for responsive resizing."""

from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QResizeEvent
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from lcars_gui_app.views.layout_tokens import (
    ELBOW_RADIUS,
    GAP_COMPACT,
    GAP_MAIN,
    MARGIN_COMPACT,
    MARGIN_OUTER,
    RAIL_BOTTOM_HEIGHT,
    RAIL_LEFT_COMPACT,
    RAIL_TOP_HEIGHT,
    LayoutTier,
    left_rail_width_for_tier,
    resolve_layout_tier,
)


class LcarsOuterShell(QWidget):
    """Responsive LCARS outer frame with top/bottom rails, elbow, and side rail.

    Attributes:
        tier_changed: Emitted when the active LayoutTier changes.
    """

    tier_changed = Signal(LayoutTier)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the outer LCARS shell and layout tracks.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self._active_tier: LayoutTier | None = None
        self._rail_expanded_in_compact: bool = False

        # Avoid redundant layout passes
        self._resize_timer = QTimer(self)
        self._resize_timer.setSingleShot(True)
        self._resize_timer.setInterval(16)
        self._resize_timer.timeout.connect(self._apply_current_width_tier)

        self._build_widgets()
        self._build_layout()
        self._apply_tier(resolve_layout_tier(max(self.width(), 1024)))

    @property
    def active_tier(self) -> LayoutTier | None:
        """Return the currently applied LayoutTier."""
        return self._active_tier

    def set_content_widget(self, widget: QWidget) -> None:
        """Set the primary inner content widget inside the main viewport area.

        Args:
            widget: Content widget placed inside the central LCARS workspace.
        """
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        widget.setMinimumWidth(0)
        self._content_layout.addWidget(widget)

    def _build_widgets(self) -> None:
        """Create rail, elbow, toggle, and content container frames."""
        self._top_rail = QFrame(self)
        self._top_rail.setObjectName("lcarsTopRail")
        self._top_rail.setFixedHeight(RAIL_TOP_HEIGHT)
        self._top_rail.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

        self._elbow_corner = QFrame(self)
        self._elbow_corner.setObjectName("lcarsElbowCorner")
        self._elbow_corner.setFixedHeight(RAIL_TOP_HEIGHT)
        self._elbow_corner.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )

        self._drawer_toggle = QPushButton("RAIL", self)
        self._drawer_toggle.setObjectName("lcarsDrawerToggle")
        self._drawer_toggle.setCheckable(True)
        self._drawer_toggle.clicked.connect(self._on_toggle_compact_rail)

        self._left_rail = QFrame(self)
        self._left_rail.setObjectName("lcarsLeftRail")
        self._left_rail.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding
        )

        self._content_host = QFrame(self)
        self._content_host.setObjectName("lcarsContentHost")
        self._content_host.setMinimumWidth(0)
        self._content_host.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._content_layout = QVBoxLayout(self._content_host)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)

        self._bottom_rail = QFrame(self)
        self._bottom_rail.setObjectName("lcarsBottomRail")
        self._bottom_rail.setFixedHeight(RAIL_BOTTOM_HEIGHT)
        self._bottom_rail.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )

    def _build_layout(self) -> None:
        """Assemble the outer grid so rails and content share alignment tracks."""
        top_bar_layout = QHBoxLayout()
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        top_bar_layout.addWidget(self._drawer_toggle)
        top_bar_layout.addWidget(self._top_rail, stretch=1)

        self._grid = QGridLayout(self)
        # Column 0 = left rail / elbow arm; Column 1 = main fluid viewport
        self._grid.setColumnStretch(0, 0)
        self._grid.setColumnStretch(1, 1)
        # Row 0 = top rail/elbow; Row 1 = main body; Row 2 = bottom rail
        self._grid.setRowStretch(0, 0)
        self._grid.setRowStretch(1, 1)
        self._grid.setRowStretch(2, 0)

        self._grid.addWidget(self._elbow_corner, 0, 0)
        self._grid.addLayout(top_bar_layout, 0, 1)
        self._grid.addWidget(self._left_rail, 1, 0)
        self._grid.addWidget(self._content_host, 1, 1)
        self._grid.addWidget(self._bottom_rail, 2, 0, 1, 2)

    def resizeevent(self, event: QResizeEvent) -> None:
        """Handle outer window/shell resize events and schedule tier evaluation.

        Args:
            event: Qt resize event containing old and new widget sizes.
        """
        super().resizeEvent(event)
        if event.size().width() != event.oldSize().width():
            self._resize_timer.start()

    def _apply_current_width_tier(self) -> None:
        """Resolve and apply the layout tier for the current widget width."""
        tier = resolve_layout_tier(self.width())
        self._apply_tier(tier)

    def _on_toggle_compact_rail(self, checked: bool) -> None:
        """Toggle visibility of the left rail when in compact viewport mode.

        Args:
            checked: Whether the compact rail drawer toggle is active.
        """
        self._rail_expanded_in_compact = checked
        self._left_rail.setVisible(checked)

    def _apply_tier(self, tier: LayoutTier) -> None:
        """Apply spacing, rail dimensions, and elbow styling for tier.

        Args:
            tier: Target responsive LayoutTier to apply.
        """
        is_compact = tier == LayoutTier.COMPACT
        margin = MARGIN_COMPACT if is_compact else MARGIN_OUTER
        gap = GAP_COMPACT if is_compact else GAP_MAIN
        rail_width = left_rail_width_for_tier(tier)

        self._grid.setContentsMargins(margin, margin, margin, margin)
        self._grid.setHorizontalSpacing(gap)
        self._grid.setVerticalSpacing(gap)

        # Keep elbow width matched to left rail width so seams stay aligned
        effective_left_width = (
            rail_width
            if (not is_compact or self._rail_expanded_in_compact)
            else RAIL_LEFT_COMPACT
        )
        self._elbow_corner.setFixedWidth(effective_left_width)
        self._left_rail.setFixedWidth(rail_width)

        self._drawer_toggle.setVisible(is_compact)
        if not is_compact:
            self._rail_expanded_in_compact = False
            self._drawer_toggle.setChecked(False)
            self._left_rail.setVisible(True)
        else:
            self._left_rail.setVisible(self._rail_expanded_in_compact)

        # Keep elbow inner corner radius locked to token to prevent stretching
        self._elbow_corner.setStyleSheet(
            f"#lcarsElbowCorner {{ border-top-left-radius: {ELBOW_RADIUS}px; }}"
        )

        if tier != self._active_tier:
            self._active_tier = tier
            self.tier_changed.emit(tier)
