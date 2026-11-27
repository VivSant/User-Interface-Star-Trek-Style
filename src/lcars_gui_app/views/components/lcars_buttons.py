"""Reusable LCARS button widgets: elbow, side/bar button and button column.

Widgets:
    LcarsElbowButton: Clickable LCARS elbow (corner sweep) for any corner.
    LcarsSideButton: Clickable block, pill or end-capped bar button.
    LcarsButtonColumn: Vertical stack of LcarsSideButtons built from a list.

All shapes are drawn with QPainter, so they render identically on Fedora
(Wayland or X11) and Windows and do not depend on the desktop theme. Only the
painted shape is clickable: the black space inside an elbow's curve or around
a pill's rounded ends ignores clicks.

Example:
    from lcars_gui_app.views.components.lcars_buttons import (
        LcarsElbowButton,
        LcarsSideButton,
    )

    power = LcarsElbowButton(
        "Power", LCARS_RED, corner=LcarsElbowButton.Corner.BOTTOM_LEFT
    )
    power.clicked.connect(window.close)
    delete = LcarsSideButton(
        "Delete", LCARS_GRAY, shape=LcarsSideButton.Shape.PILL,
        text_color=LCARS_RED,
    )
"""

from collections.abc import Callable
from enum import Enum

from PySide6.QtCore import QPoint, QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QTransform
from PySide6.QtWidgets import (
    QAbstractButton,
    QButtonGroup,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

# Palette from LCARS_Framework_Design_1 (the interface blueprint).
LCARS_ORANGE = "#ff8833"
LCARS_TAN = "#ffcc99"
LCARS_WHITE_BLUE = "#ebf0ff"
LCARS_LIGHT_BLUE = "#6699ff"
LCARS_BLUE = "#2266ff"
LCARS_RED = "#da2537"
LCARS_PURPLE = "#7a506d"
LCARS_LIGHT_PURPLE = "#9d698a"
LCARS_LAVENDER = "#c082a9"
LCARS_GRAY = "#52526a"
LCARS_BLACK = "#000000"

# Narrow LCARS-like fonts first; Qt falls back down the list to whatever is
# installed (Liberation/DejaVu ship with Fedora, Arial with Windows).
LCARS_FONT_FAMILIES = [
    "Antonio",
    "Oswald",
    "Bebas Neue",
    "Arial Narrow",
    "Liberation Sans Narrow",
    "DejaVu Sans Condensed",
    "Arial",
    "Sans Serif",
]

INDICATOR_STRIPE_WIDTH = 8
INDICATOR_STRIPE_INSET = 6


def lcars_font(pixel_size: int = 15, bold: bool = True) -> QFont:
    """Build the font used for LCARS button labels.

    Args:
        pixel_size: Font height in pixels.
        bold: Whether the font is bold.

    Returns:
        A QFont that prefers narrow LCARS-style families and falls back to
        fonts available on Fedora and Windows.
    """
    font = QFont()
    font.setFamilies(LCARS_FONT_FAMILIES)
    font.setPixelSize(pixel_size)
    font.setBold(bold)
    return font


class LcarsButtonBase(QAbstractButton):
    """Shared colour, state and label handling for custom-painted buttons.

    Subclasses implement shape_path() and paintEvent(). Hover lightens the
    fill, pressing darkens it and a disabled button is drawn in gray.
    """

    def __init__(
        self,
        text: str = "",
        color: str = LCARS_LIGHT_BLUE,
        text_color: str = LCARS_BLACK,
        font_px: int = 15,
        uppercase: bool = True,
        alignment: Qt.AlignmentFlag = Qt.AlignCenter,
        parent: QWidget | None = None,
    ) -> None:
        """Initialise the shared button state.

        Args:
            text: Label text.
            color: Fill colour as a hex string.
            text_color: Label colour as a hex string.
            font_px: Label font size in pixels.
            uppercase: Whether the label is shown in upper case.
            alignment: Qt alignment flags for the label.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self._color = QColor(color)
        self._text_color = QColor(text_color)
        self._uppercase = uppercase
        self._alignment = alignment
        self.setText(text)
        self.setFont(lcars_font(font_px))
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover)  # repaint on mouse enter/leave

    def setText(self, text: str) -> None:  # noqa: N802 - Qt override
        """Set the label, upper-casing it if the button was built that way.

        Args:
            text: New label text.
        """
        super().setText(text.upper() if self._uppercase else text)

    def set_color(self, color: str) -> None:
        """Change the fill colour and repaint.

        Args:
            color: New fill colour as a hex string.
        """
        self._color = QColor(color)
        self.update()

    def set_text_color(self, color: str) -> None:
        """Change the label colour and repaint.

        Args:
            color: New label colour as a hex string.
        """
        self._text_color = QColor(color)
        self.update()

    def shape_path(self) -> QPainterPath:
        """Return the outline of the clickable, painted shape.

        Returns:
            The button outline in widget coordinates.

        Raises:
            NotImplementedError: Always; subclasses must override this.
        """
        raise NotImplementedError

    def current_fill(self) -> QColor:
        """Return the fill colour for the button's current state.

        Returns:
            Gray when disabled, darker when pressed, lighter when hovered,
            otherwise the base colour.
        """
        if not self.isEnabled():
            return QColor(LCARS_GRAY)
        if self.isDown():
            return self._color.darker(150)
        if self.underMouse():
            return self._color.lighter(120)
        return self._color

    def hitButton(self, pos: QPoint) -> bool:  # noqa: N802 - Qt override
        """Report whether a click lands on the painted shape.

        Args:
            pos: Click position in widget coordinates.

        Returns:
            True if the position is inside shape_path().
        """
        return self.shape_path().contains(QPointF(pos))

    def _draw_label(self, painter: QPainter, rect: QRectF) -> None:
        """Draw the label text inside a rectangle.

        Args:
            painter: Active painter for this widget.
            rect: Area the text is aligned within.
        """
        if not self.text():
            return
        painter.setPen(self._text_color if self.isEnabled() else QColor(LCARS_BLACK))
        painter.setFont(self.font())
        painter.drawText(rect, int(self._alignment), self.text())


class LcarsSideButton(LcarsButtonBase):
    """Reusable LCARS block button for sidebars, header bars and action pills.

    A checkable button shows a black indicator stripe while selected, which
    is how the sidebar marks the active page.
    """

    class Shape(Enum):
        """Outline styles for LcarsSideButton."""

        RECT = "rect"
        PILL = "pill"
        ROUND_LEFT = "round_left"
        ROUND_RIGHT = "round_right"

    def __init__(
        self,
        text: str = "",
        color: str = LCARS_LIGHT_BLUE,
        shape: "LcarsSideButton.Shape" = Shape.RECT,
        text_color: str = LCARS_BLACK,
        font_px: int = 15,
        uppercase: bool = True,
        alignment: Qt.AlignmentFlag = Qt.AlignCenter,
        checkable: bool = False,
        indicator_side: Qt.Edge = Qt.RightEdge,
        parent: QWidget | None = None,
    ) -> None:
        """Create a side button.

        Args:
            text: Label text.
            color: Fill colour as a hex string.
            shape: Outline style (RECT, PILL, ROUND_LEFT or ROUND_RIGHT).
            text_color: Label colour as a hex string.
            font_px: Label font size in pixels.
            uppercase: Whether the label is shown in upper case.
            alignment: Qt alignment flags for the label.
            checkable: Whether the button toggles and shows a selection stripe.
            indicator_side: Qt.RightEdge or Qt.LeftEdge for the stripe.
            parent: Optional parent widget.
        """
        super().__init__(text, color, text_color, font_px, uppercase, alignment, parent)
        self._shape = shape
        self._indicator_side = indicator_side
        self.setCheckable(checkable)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def sizeHint(self) -> QSize:  # noqa: N802 - Qt override
        """Return the preferred size.

        Returns:
            The default button size (160 x 60).
        """
        return QSize(160, 60)

    def minimumSizeHint(self) -> QSize:  # noqa: N802 - Qt override
        """Return the smallest sensible size.

        Returns:
            The minimum button size (60 x 30).
        """
        return QSize(60, 30)

    def set_shape(self, shape: "LcarsSideButton.Shape") -> None:
        """Change the outline style and repaint.

        Args:
            shape: New outline style.
        """
        self._shape = shape
        self.update()

    def _end_radius(self) -> float:
        """Return the radius used for rounded ends.

        Returns:
            Half the height, capped at half the width.
        """
        return min(self.height() / 2, self.width() / 2)

    def shape_path(self) -> QPainterPath:
        """Return the button outline for the current shape.

        Returns:
            The outline in widget coordinates.
        """
        width, height = float(self.width()), float(self.height())
        radius = self._end_radius()
        shape_enum = LcarsSideButton.Shape
        path = QPainterPath()
        if self._shape == shape_enum.PILL:
            path.addRoundedRect(QRectF(0, 0, width, height), radius, radius)
        elif self._shape == shape_enum.ROUND_LEFT:
            path.moveTo(radius, 0)
            path.lineTo(width, 0)
            path.lineTo(width, height)
            path.lineTo(radius, height)
            path.arcTo(QRectF(0, 0, 2 * radius, height), 270, -180)
            path.closeSubpath()
        elif self._shape == shape_enum.ROUND_RIGHT:
            path.moveTo(0, 0)
            path.lineTo(width - radius, 0)
            path.arcTo(QRectF(width - 2 * radius, 0, 2 * radius, height), 90, -180)
            path.lineTo(0, height)
            path.closeSubpath()
        else:
            path.addRect(QRectF(0, 0, width, height))
        return path

    def paintEvent(self, event: object) -> None:  # noqa: N802 - Qt override
        """Paint the shape, the selection stripe and the label.

        Args:
            event: The Qt paint event (unused).
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.current_fill())
        painter.drawPath(self.shape_path())

        width, height = self.width(), self.height()
        if self.isChecked():
            if self._indicator_side == Qt.RightEdge:
                stripe_x = width - INDICATOR_STRIPE_WIDTH - INDICATOR_STRIPE_INSET
            else:
                stripe_x = INDICATOR_STRIPE_INSET
            painter.setBrush(QColor(LCARS_BLACK))
            painter.drawRect(
                QRectF(
                    stripe_x,
                    INDICATOR_STRIPE_INSET,
                    INDICATOR_STRIPE_WIDTH,
                    height - 2 * INDICATOR_STRIPE_INSET,
                )
            )

        # Keep the label clear of rounded ends and the selection stripe.
        shape_enum = LcarsSideButton.Shape
        radius = self._end_radius()
        rounded_left = self._shape in (shape_enum.PILL, shape_enum.ROUND_LEFT)
        rounded_right = self._shape in (shape_enum.PILL, shape_enum.ROUND_RIGHT)
        left_pad = radius * 0.6 if rounded_left else 10
        right_pad = radius * 0.6 if rounded_right else 10
        if self.isCheckable():
            right_pad += 14
        self._draw_label(
            painter, QRectF(left_pad, 4, width - left_pad - right_pad, height - 8)
        )


class LcarsElbowButton(LcarsButtonBase):
    """Clickable LCARS elbow that joins a sidebar to a header or footer bar.

    The shape is drawn for the top-left corner and mirrored for the others.
    The label sits in the vertical arm, next to the curve.
    """

    class Corner(Enum):
        """Corner of the frame the elbow occupies."""

        TOP_LEFT = "top_left"
        TOP_RIGHT = "top_right"
        BOTTOM_LEFT = "bottom_left"
        BOTTOM_RIGHT = "bottom_right"

    def __init__(
        self,
        text: str = "",
        color: str = LCARS_TAN,
        corner: "LcarsElbowButton.Corner" = Corner.TOP_LEFT,
        sidebar_width: int = 160,
        bar_height: int = 40,
        outer_radius: float | None = None,
        inner_radius: float | None = None,
        text_color: str = LCARS_BLACK,
        font_px: int = 15,
        uppercase: bool = True,
        alignment: Qt.AlignmentFlag | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Create an elbow button.

        Args:
            text: Label text.
            color: Fill colour as a hex string.
            corner: Which corner the elbow sits in.
            sidebar_width: Thickness of the vertical arm; match the sidebar.
            bar_height: Thickness of the horizontal arm; match the bar.
            outer_radius: Radius of the outside curve. Defaults to
                min(sidebar_width, 70).
            inner_radius: Radius of the inside curve. Defaults to
                0.6 * bar_height.
            text_color: Label colour as a hex string.
            font_px: Label font size in pixels.
            uppercase: Whether the label is shown in upper case.
            alignment: Qt alignment flags for the label. Defaults to the
                inner edge of the arm, next to the curve.
            parent: Optional parent widget.
        """
        corner_enum = LcarsElbowButton.Corner
        is_top = corner in (corner_enum.TOP_LEFT, corner_enum.TOP_RIGHT)
        is_left = corner in (corner_enum.TOP_LEFT, corner_enum.BOTTOM_LEFT)
        if alignment is None:
            alignment = (Qt.AlignRight if is_left else Qt.AlignLeft) | (
                Qt.AlignBottom if is_top else Qt.AlignTop
            )
        super().__init__(text, color, text_color, font_px, uppercase, alignment, parent)
        self._corner = corner
        self.sidebar_width = sidebar_width
        self.bar_height = bar_height
        self.outer_radius = (
            outer_radius if outer_radius is not None else min(sidebar_width, 70)
        )
        self.inner_radius = (
            inner_radius if inner_radius is not None else bar_height * 0.6
        )
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFixedSize(sidebar_width + 80, int(bar_height + self.inner_radius + 50))

    def _corner_transform(self) -> QTransform:
        """Return the transform that mirrors the top-left drawing into place.

        Returns:
            A QTransform flipping horizontally and/or vertically as needed.
        """
        corner_enum = LcarsElbowButton.Corner
        width, height = self.width(), self.height()
        transform = QTransform()
        if self._corner in (corner_enum.TOP_RIGHT, corner_enum.BOTTOM_RIGHT):
            transform = transform * QTransform(-1, 0, 0, 1, width, 0)
        if self._corner in (corner_enum.BOTTOM_LEFT, corner_enum.BOTTOM_RIGHT):
            transform = transform * QTransform(1, 0, 0, -1, 0, height)
        return transform

    def shape_path(self) -> QPainterPath:
        """Return the elbow outline for the configured corner.

        Returns:
            The outline in widget coordinates.
        """
        width, height = float(self.width()), float(self.height())
        arm_width, bar_height = float(self.sidebar_width), float(self.bar_height)
        outer = min(self.outer_radius, arm_width, height)
        inner = min(self.inner_radius, width - arm_width, height - bar_height)

        path = QPainterPath()
        path.moveTo(0, height)
        path.lineTo(0, outer)
        path.arcTo(QRectF(0, 0, 2 * outer, 2 * outer), 180, -90)  # outer curve
        path.lineTo(width, 0)
        path.lineTo(width, bar_height)
        path.lineTo(arm_width + inner, bar_height)
        path.arcTo(
            QRectF(arm_width, bar_height, 2 * inner, 2 * inner), 90, 90
        )  # inner curve
        path.lineTo(arm_width, height)
        path.closeSubpath()
        return self._corner_transform().map(path)

    def paintEvent(self, event: object) -> None:  # noqa: N802 - Qt override
        """Paint the elbow and its label.

        Args:
            event: The Qt paint event (unused).
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.current_fill())
        painter.drawPath(self.shape_path())

        label_top = self.bar_height + self.inner_radius
        label_rect = QRectF(0, label_top, self.sidebar_width, self.height() - label_top)
        label_rect = (
            self._corner_transform().mapRect(label_rect).adjusted(10, 4, -10, -6)
        )
        self._draw_label(painter, label_rect)


class LcarsButtonColumn(QWidget):
    """Vertical stack of LcarsSideButtons built from a list.

    With exclusive=True the buttons behave like navigation tabs: exactly one
    stays selected and shows the indicator stripe.

    Example:
        column = LcarsButtonColumn(
            [
                ("File Manager", LCARS_LIGHT_BLUE, open_files),
                ("Settings", LCARS_ORANGE, open_settings),
            ],
            exclusive=True,
        )
    """

    def __init__(
        self,
        items: list[tuple[str, str, Callable[[], None] | None]],
        exclusive: bool = False,
        spacing: int = 6,
        parent: QWidget | None = None,
        **button_kwargs: object,
    ) -> None:
        """Build the column.

        Args:
            items: (label, colour, callback) for each button; callback may be
                None.
            exclusive: Whether the buttons act as a single-selection group.
            spacing: Gap between buttons in pixels.
            parent: Optional parent widget.
            **button_kwargs: Extra keyword arguments for every LcarsSideButton
                (for example shape=LcarsSideButton.Shape.PILL).
        """
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(spacing)

        self.group = QButtonGroup(self)
        self.group.setExclusive(exclusive)
        self.buttons: list[LcarsSideButton] = []
        for label, color, callback in items:
            button = LcarsSideButton(label, color, checkable=exclusive, **button_kwargs)
            if callback is not None:
                button.clicked.connect(callback)
            self.group.addButton(button)
            layout.addWidget(button)
            self.buttons.append(button)
