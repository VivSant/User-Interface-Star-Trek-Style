"""Responsive multi-panel grid layout that reflows across LayoutTier changes."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QSizePolicy, QWidget

from lcars_gui_app.views.layout_tokens import (
    GAP_COMPACT,
    GAP_MAIN,
    LayoutTier,
)
from lcars_gui_app.views.panel_container import LcarsPanelContainer


class LcarsPanelGrid(QWidget):
    """Reflowing grid container for LcarsPanelContainer panels across layout tiers.

    Attributes:
        grid_layout: Underlying QGridLayout managing panel positions and stretches.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the responsive panel grid.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.setObjectName("lcarsPanelGrid")
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._panels: list[LcarsPanelContainer] = []
        self._current_tier: LayoutTier = LayoutTier.STANDARD

        self.grid_layout = QGridLayout(self)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setHorizontalSpacing(GAP_MAIN)
        self.grid_layout.setVerticalSpacing(GAP_MAIN)

    def add_panel(self, panel: LcarsPanelContainer) -> None:
        """Register a panel and reflow the grid for the active layout tier.

        Args:
            panel: LcarsPanelContainer instance to include in the grid.
        """
        panel.setMinimumWidth(0)
        panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._panels.append(panel)
        self._reflow(self._current_tier)

    def set_tier(self, tier: LayoutTier) -> None:
        """Reflow panels and spacing to match a new LayoutTier.

        Args:
            tier: Target responsive LayoutTier.
        """
        self._current_tier = tier
        self._reflow(tier)

    def _columns_for_tier(self, tier: LayoutTier) -> int:
        """Return target column count for tier.

        Args:
            tier: Active responsive LayoutTier.

        Returns:
            Number of grid columns to arrange panels into.
        """
        match tier:
            case LayoutTier.COMPACT | LayoutTier.SPLIT:
                return 1
            case LayoutTier.STANDARD:
                return 2
            case LayoutTier.WIDE:
                return 3

    def _clear_grid_positions(self) -> None:
        """Detach panel widgets from grid cells without deleting the widgets."""
        for panel in self._panels:
            self.grid_layout.removeWidget(panel)

        # Reset prior row/column stretch factors so stale counts do not linger
        for col in range(self.grid_layout.columnCount()):
            self.grid_layout.setColumnStretch(col, 0)
        for row in range(self.grid_layout.rowCount()):
            self.grid_layout.setRowStretch(row, 0)

    def _reflow(self, tier: LayoutTier) -> None:
        """Recompute grid cells, spacing, and stretches for tier.

        Args:
            tier: Target LayoutTier for reflowing panels.
        """
        gap = GAP_COMPACT if tier == LayoutTier.COMPACT else GAP_MAIN
        self.grid_layout.setHorizontalSpacing(gap)
        self.grid_layout.setVerticalSpacing(gap)

        self._clear_grid_positions()
        if not self._panels:
            return

        columns = max(self._columns_for_tier(tier), 1)
        total_panels = len(self._panels)
        rows = (total_panels + columns - 1) // columns

        for index, panel in enumerate(self._panels):
            row = index // columns
            col = index % columns

            # Span remaining columns on the final row when panel count is odd
            is_last_panel = index == total_panels - 1
            remaining_cols = columns - col
            col_span = remaining_cols if (is_last_panel and col > 0) else 1

            self.grid_layout.addWidget(
                panel,
                row,
                col,
                1,
                col_span,
                alignment=Qt.AlignmentFlag(),
            )

        for col in range(columns):
            self.grid_layout.setColumnStretch(col, 1)
        for row in range(rows):
            self.grid_layout.setRowStretch(row, 1)
