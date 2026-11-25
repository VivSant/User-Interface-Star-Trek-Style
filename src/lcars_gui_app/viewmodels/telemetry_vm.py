"""Telemetry ViewModel supplying live core temp, CPU, and memory state."""

from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal


def _read_linux_core_temp_c() -> float | None:
    """Read package or highest thermal-zone temperature in Celsius on Linux.

    Returns:
        Temperature in degrees Celsius, or None if unavailable.
    """
    thermal_root = Path("/sys/class/thermal")
    if not thermal_root.is_dir():
        return None

    preferred_temps: list[float] = []
    fallback_temps: list[float] = []

    for zone in sorted(thermal_root.glob("thermal_zone*")):
        temp_path = zone / "temp"
        if not temp_path.is_file():
            continue
        try:
            raw_val = int(temp_path.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            continue

        temp_c = raw_val / 1000.0 if raw_val > 200 else float(raw_val)
        zone_type = ""
        type_path = zone / "type"
        if type_path.is_file():
            try:
                zone_type = type_path.read_text(encoding="utf-8").strip().lower()
            except OSError:
                zone_type = ""

        if any(
            tag in zone_type
            for tag in ("pkg", "cpu", "x86_pkg_temp", "k10temp", "coretemp")
        ):
            preferred_temps.append(temp_c)
        else:
            fallback_temps.append(temp_c)

    if preferred_temps:
        return max(preferred_temps)
    if fallback_temps:
        return max(fallback_temps)
    return None


def _read_proc_stat_totals() -> tuple[int, int] | None:
    """Read aggregate CPU busy and total jiffies from /proc/stat.

    Returns:
        Tuple of (busy_ticks, total_ticks), or None if unavailable.
    """
    stat_path = Path("/proc/stat")
    if not stat_path.is_file():
        return None

    try:
        for line in stat_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("cpu "):
                parts = [int(x) for x in line.split()[1:]]
                if len(parts) < 4:
                    return None
                idle = parts[3] + (parts[4] if len(parts) > 4 else 0)
                total = sum(parts)
                busy = max(0, total - idle)
                return busy, total
    except (OSError, ValueError):
        return None
    return None


def _read_memory_gib() -> tuple[float, float, float] | None:
    """Read used memory, total memory in GiB, and usage percentage from /proc/meminfo.

    Returns:
        Tuple of (used_gib, total_gib, percent_used), or None if unavailable.
    """
    meminfo_path = Path("/proc/meminfo")
    if not meminfo_path.is_file():
        return None

    values_kib: dict[str, int] = {}
    try:
        for line in meminfo_path.read_text(encoding="utf-8").splitlines():
            key, _, rest = line.partition(":")
            if key in {"MemTotal", "MemAvailable"}:
                num_str = rest.strip().split()[0]
                values_kib[key] = int(num_str)
    except (OSError, ValueError, IndexError):
        return None

    total_kib = values_kib.get("MemTotal")
    avail_kib = values_kib.get("MemAvailable")
    if not total_kib or avail_kib is None or total_kib <= 0:
        return None

    used_kib = max(0, total_kib - avail_kib)
    gib_factor = 1024.0 * 1024.0
    used_gib = used_kib / gib_factor
    total_gib = total_kib / gib_factor
    pct = (used_kib / total_kib) * 100.0
    return used_gib, total_gib, pct


class TelemetryViewModel(QObject):
    """ViewModel managing live telemetry, CPU, memory, and core temperature."""

    core_temp_changed = Signal(str)
    cpu_changed = Signal(str)
    memory_changed = Signal(str)

    def __init__(
        self,
        poll_interval_ms: int = 2000,
        parent: QObject | None = None,
    ) -> None:
        """Initialize ViewModel state and start periodic telemetry polling.

        Args:
            poll_interval_ms: Polling period in milliseconds for telemetry updates.
            parent: Optional parent QObject.
        """
        super().__init__(parent)
        self._prev_cpu_ticks: tuple[int, int] | None = _read_proc_stat_totals()

        self._core_temp_text = "CORE TEMP: OFFLINE"
        self._cpu_text = "CPU: --.-%"
        self._memory_text = "MEM: --.- / --.- GiB"

        self.refresh_telemetry()

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(poll_interval_ms)
        self._poll_timer.timeout.connect(self.refresh_telemetry)
        self._poll_timer.start()

    @property
    def core_temp_text(self) -> str:
        """Formatted core temperature readout string."""
        return self._core_temp_text

    @property
    def cpu_text(self) -> str:
        """Formatted CPU utilization readout string."""
        return self._cpu_text

    @property
    def memory_text(self) -> str:
        """Formatted memory usage readout string."""
        return self._memory_text

    def refresh_telemetry(self) -> None:
        """Sample core temperature, CPU usage, and memory usage and emit changes."""
        self.refresh_core_temp()
        self.refresh_cpu()
        self.refresh_memory()

    def refresh_core_temp(self) -> None:
        """Sample core temperature and emit core_temp_changed when updated."""
        temp_c = _read_linux_core_temp_c()
        formatted = (
            f"CORE TEMP: {temp_c:.1f}°C" if temp_c is not None else "CORE TEMP: OFFLINE"
        )
        if formatted != self._core_temp_text:
            self._core_temp_text = formatted
            self.core_temp_changed.emit(formatted)

    def refresh_cpu(self) -> None:
        """Compute delta CPU utilization and emit cpu_changed when updated."""
        current = _read_proc_stat_totals()
        if current is None:
            formatted = "CPU: OFFLINE"
        elif self._prev_cpu_ticks is None:
            self._prev_cpu_ticks = current
            return
        else:
            prev_busy, prev_total = self._prev_cpu_ticks
            curr_busy, curr_total = current
            self._prev_cpu_ticks = current
            delta_total = curr_total - prev_total
            if delta_total <= 0:
                return
            pct = ((curr_busy - prev_busy) / delta_total) * 100.0
            pct = max(0.0, min(100.0, pct))
            formatted = f"CPU: {pct:.1f}%"

        if formatted != self._cpu_text:
            self._cpu_text = formatted
            self.cpu_changed.emit(formatted)

    def refresh_memory(self) -> None:
        """Sample system memory usage and emit memory_changed when updated."""
        mem_info = _read_memory_gib()
        if mem_info is None:
            formatted = "MEM: OFFLINE"
        else:
            used_gib, total_gib, pct = mem_info
            formatted = f"MEM: {used_gib:.1f}/{total_gib:.1f} GiB ({pct:.0f}%)"

        if formatted != self._memory_text:
            self._memory_text = formatted
            self.memory_changed.emit(formatted)
