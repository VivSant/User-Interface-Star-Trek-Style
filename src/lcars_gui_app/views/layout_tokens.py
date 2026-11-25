"""Layout tokens (constants) and responsive breakpoint rules for the LCARS GUI views."""

from enum import Enum

LCARS_BG = "#000000"
LCARS_AMBER = "#ff9900"
LCARS_GOLD = "#ffcc66"
LCARS_LAVENDER = "#cc99cc"
LCARS_SURFACE_DARK = "#111111"
LCARS_HEADER_BG = "#1a1a1a"

LCARS_QSS = f"""
QMainWindow, QWidget#lcarsOuterShell, QWidget#lcarsPanelGrid {{
    background-color: {LCARS_BG};
    color: {LCARS_AMBER};
}}

QFrame#lcarsPanelContainer {{
    background-color: {LCARS_BG};
    border: 2px solid {LCARS_LAVENDER};
    border-radius: 12px;
}}

QLabel {{
    color: {LCARS_AMBER};
    background-color: transparent;
}}

QTreeView, QListView {{
    background-color: {LCARS_BG};
    color: {LCARS_AMBER};
    border: none;
}}

QHeaderView::section {{
    background-color: {LCARS_HEADER_BG};
    color: {LCARS_GOLD};
    border: 1px solid #333333;
    padding: 4px;
    font-weight: bold;
}}

QScrollBar:vertical, QScrollBar:horizontal {{
    background-color: {LCARS_SURFACE_DARK};
    border: none;
}}

QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
    background-color: {LCARS_AMBER};
    min-height: 24px;
    min-width: 24px;
    border-radius: 4px;
}}
"""


class LayoutTier(str, Enum):
    """Responsive viewport tiers based on main window width in pixels."""

    COMPACT = "compact"
    SPLIT = "split"
    STANDARD = "standard"
    WIDE = "wide"


# Breakpoint thresholds (window width in pixels)
BREAKPOINT_COMPACT_MAX: int = 639
BREAKPOINT_SPLIT_MAX: int = 1023
BREAKPOINT_STANDARD_MAX: int = 1599

# Base spacing, margins, and gaps (pixels)
SPACE_UNIT: int = 4
MARGIN_OUTER: int = 12
MARGIN_COMPACT: int = 8
GAP_MAIN: int = 8
GAP_COMPACT: int = 4

# Outer LCARS rail and elbow geometry tokens (pixels)
RAIL_LEFT_COMPACT: int = 72
RAIL_LEFT_SPLIT: int = 96
RAIL_LEFT_STANDARD: int = 160
RAIL_LEFT_WIDE: int = 184
RAIL_TOP_HEIGHT: int = 44
RAIL_BOTTOM_HEIGHT: int = 28
ELBOW_RADIUS: int = 24
PILL_RADIUS: int = 16

# Typography and interactive control bounds (pixels / points)
FONT_SIZE_MIN: int = 11
FONT_SIZE_BODY: int = 13
FONT_SIZE_HEADER: int = 16
CONTROL_MIN_HEIGHT: int = 36
CONTROL_TOUCH_MIN_HEIGHT: int = 44


def resolve_layout_tier(window_width: int) -> LayoutTier:
    """Resolve the active LCARS layout tier from a main window width.

    Args:
        window_width: Current width of the main window in pixels.

    Returns:
        The matching LayoutTier for the given viewport width.
    """
    if window_width <= BREAKPOINT_COMPACT_MAX:
        return LayoutTier.COMPACT
    if window_width <= BREAKPOINT_SPLIT_MAX:
        return LayoutTier.SPLIT
    if window_width <= BREAKPOINT_STANDARD_MAX:
        return LayoutTier.STANDARD
    return LayoutTier.WIDE


def left_rail_width_for_tier(tier: LayoutTier) -> int:
    """Return the target left LCARS rail width for a given layout tier.

    Args:
        tier: Active responsive LayoutTier.

    Returns:
        Target left rail width in pixels.
    """
    rail_widths: dict[LayoutTier, int] = {
        LayoutTier.COMPACT: RAIL_LEFT_COMPACT,
        LayoutTier.SPLIT: RAIL_LEFT_SPLIT,
        LayoutTier.STANDARD: RAIL_LEFT_STANDARD,
        LayoutTier.WIDE: RAIL_LEFT_WIDE,
    }
    return rail_widths[tier]
