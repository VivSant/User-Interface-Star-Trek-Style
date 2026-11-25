"""Resizable split pane and resize observer helpers for LCARS readouts."""

from PySide6.QtCore import QEvent, QObject, QSize, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from lcars_gui_app.views.layout_tokens import (
    GAP_COMPACT,
    GAP_MAIN,
    LayoutTier,
)


class _ReadoutResizeObserver(QObject):
    """Observes target widget geometry changes and emits debounced size updates.

    Attributes:
        size_changed: Emitted with (width, height) when size changes.
    """

    size_changed = Signal(int, int)

    def __init__(
        self,
        target: QWidget,
        debounce_ms: int = 16,
        parent: QObject | None = None,
    ) -> None:
        """Initialize the resize observer for a target widget.

        Args:
            target: Widget whose size changes are monitored.
            debounce_ms: Coalescing delay in milliseconds before emitting changes.
            parent: Optional parent QObject.
        """
        super().__init__(parent or target)
        self._target = target
        self._last_size = QSize(-1, -1)
        self._pending_size = QSize(-1, -1)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(max(debounce_ms, 0))
        self._timer.timeout.connect(self._flush_size_change)

        self._target.installEventFilter(self)

    def eventfilter(self, watched: QObject, event: QEvent) -> bool:
        """Capture Resize and LayoutRequest events on the observed widget.

        Args:
            watched: Object receiving the event.
            event: Event being processed.

        Returns:
            False so normal Qt event propagation continues uninterrupted.
        """
        if watched is self._target and event.type() == QEvent.Type.Resize:
            current_size = self._target.size()
            if current_size != self._pending_size and current_size != self._last_size:
                self._pending_size = QSize(current_size)
                if self._timer.interval() == 0:
                    self._flush_size_change()
                else:
                    self._timer.start()
        return super().eventFilter(watched, event)

    def _flush_size_change(self) -> None:
        """Emit size_changed once per distinct size to prevent resize loops."""
        if not self._pending_size.isValid():
            return
        next_size = QSize(self._pending_size)
        if next_size == self._last_size:
            return
        self._last_size = next_size
        self.size_changed.emit(next_size.width(), next_size.height())


class LcarsDynamicReadoutHost(QFrame):
    """Container for custom charts, canvases, or readouts with resize observation.

    Attributes:
        readout_resized: Emitted with (width, height) when the host resizes.
    """

    readout_resized = Signal(int, int)

    def __init__(self, readout_widget: QWidget, parent: QWidget | None = None) -> None:
        """Initialize the readout host and attach its resize observer.

        Args:
            readout_widget: Custom readout, chart, or canvas widget to host.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.setObjectName("lcarsDynamicReadoutHost")
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        readout_widget.setMinimumWidth(0)
        readout_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(readout_widget)

        self._observer = _ReadoutResizeObserver(self, debounce_ms=16, parent=self)
        self._observer.size_changed.connect(self._on_observed_resize)

    def _on_observed_resize(self, width: int, height: int) -> None:
        """Forward dimensions to listeners without changing host geometry.

        Args:
            width: Updated width in pixels.
            height: Updated height in pixels.
        """
        self.readout_resized.emit(width, height)


class LcarsSplitPane(QSplitter):
    """Resizable LCARS split container that adapts orientation across layout tiers.

    Attributes:
        splitter_moved: Emitted with (sizes) when the user drags a divider.
    """

    splitter_moved = Signal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize a responsive QSplitter for LCARS panels.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.setObjectName("lcarsSplitPane")
        self.setChildrenCollapsible(False)
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setHandleWidth(GAP_MAIN)
        self.splitterMoved.connect(self._on_splitter_moved)

    def add_pane(self, widget: QWidget, stretch: int = 1) -> None:
        """Add a child panel or readout host with zero width shrink safety.

        Args:
            widget: Child widget placed inside the split pane.
            stretch: Stretch factor applied to the pane index.
        """
        widget.setMinimumWidth(0)
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.addWidget(widget)
        index = self.count() - 1
        self.setStretchFactor(index, max(stretch, 0))

    def set_tier(self, tier: LayoutTier) -> None:
        """Adjust split orientation and handle spacing for tier.

        Args:
            tier: Target responsive LayoutTier.
        """
        if tier in (LayoutTier.COMPACT, LayoutTier.SPLIT):
            self.setOrientation(self.orientation().__class__.Vertical)
            self.setHandleWidth(GAP_COMPACT)
        else:
            self.setOrientation(self.orientation().__class__.Horizontal)
            self.setHandleWidth(GAP_MAIN)

    def _on_splitter_moved(self, pos: int, index: int) -> None:
        """Emit current pane sizes when a splitter handle moves.

        Args:
            pos: New splitter handle coordinate.
            index: Index of the handle that moved.
        """
        _ = (pos, index)
        self.splitter_moved.emit(self.sizes())
