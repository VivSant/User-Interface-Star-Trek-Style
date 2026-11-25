"""Generate randomized telemetry data for demonstration purposes.

This module provides the TelemetryModel, which periodically emits status readings.
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

import psutil  # type: ignore[reportMissingModuleSource]

# Tiered Telemetry Payload Schema
# Format display units (GiB, MB/s, uptime strings) in the LCARS view layer.

SCHEMA_VERSION = "1.0.0"


@dataclass(frozen=True)
class CpuTelemetry:
    """CPU telemetry data, including total and per-core usage, frequency, etc."""

    total_percent: Optional[float] = None
    per_core_percent: tuple[float, ...] = ()
    freq_mhz: Optional[float] = None
    load_avg_1m: Optional[float] = None
    load_avg_5m: Optional[float] = None
    load_avg_15m: Optional[float] = None


@dataclass(frozen=True)
class MemoryTelemetry:
    """Memory telemetry data, including virtual and swap usage."""

    virtual_total_bytes: Optional[int] = None
    virtual_used_bytes: Optional[int] = None
    virtual_available_bytes: Optional[int] = None
    virtual_percent: Optional[float] = None
    swap_total_bytes: Optional[int] = None
    swap_used_bytes: Optional[int] = None
    swap_percent: Optional[float] = None


@dataclass(frozen=True)
class StorageMountTelemetry:
    """Telemetry data for a single storage mount point."""

    mountpoint: str
    device: str
    total_bytes: Optional[int] = None
    used_bytes: Optional[int] = None
    percent: Optional[float] = None


@dataclass(frozen=True)
class StorageTelemetry:
    """Storage telemetry data, including mount points and I/O rates."""

    mounts: tuple[StorageMountTelemetry, ...] = ()
    read_bytes_per_sec: Optional[float] = None
    write_bytes_per_sec: Optional[float] = None


@dataclass(frozen=True)
class NetworkTelemetry:
    """Network telemetry data, including I/O rates and active interfaces."""

    rx_bytes_per_sec: Optional[float] = None
    tx_bytes_per_sec: Optional[float] = None
    active_interfaces: tuple[str, ...] = ()


@dataclass(frozen=True)
class SensorTelemetry:
    """Sensor telemetry data, including temperature, battery, and uptime."""

    max_temp_c: Optional[float] = None
    battery_percent: Optional[float] = None
    power_plugged: Optional[bool] = None
    uptime_seconds: Optional[float] = None


@dataclass(frozen=True)
class TelemetrySnapshot:
    """A snapshot of all telemetry data at a specific point in time."""

    schema_version: str = SCHEMA_VERSION
    timestamp_unix_s: float = 0.0
    seq: int = 0
    cpu: CpuTelemetry = field(default_factory=CpuTelemetry)
    memory: MemoryTelemetry = field(default_factory=MemoryTelemetry)
    storage: StorageTelemetry = field(default_factory=StorageTelemetry)
    network: NetworkTelemetry = field(default_factory=NetworkTelemetry)
    sensors: SensorTelemetry = field(default_factory=SensorTelemetry)
    errors: tuple[str, ...] = ()


# Latest value collection.


class LatestSnapshotMailbox:
    """Holds only the newest snapshot so slow UI frames drop stale backlog."""

    def __init__(self) -> None:
        """Thread-safe mailbox for the latest telemetry snapshot."""
        self._lock = threading.Lock()
        self._latest: Optional[TelemetrySnapshot] = None

    def publish(self, snapshot: TelemetrySnapshot) -> None:
        """Publish a new snapshot, replacing any previous one."""
        with self._lock:
            self._latest = snapshot

    def consume(self) -> Optional[TelemetrySnapshot]:
        """Consume and return the latest snapshot, or None if none available."""
        with self._lock:
            snap = self._latest
            self._latest = None
            return snap


# Background collection.


class TieredPsutilCollector:
    """Polls psutil on fast (1s), medium (3s), and slow (20s) tiers."""

    def __init__(
        self,
        mailbox: LatestSnapshotMailbox,
        on_snapshot: Optional[Callable[[TelemetrySnapshot], None]] = None,
        fast_interval_s: float = 1.0,
        medium_interval_s: float = 3.0,
        slow_interval_s: float = 20.0,
    ) -> None:
        """Initialize the collector."""
        self._mailbox = mailbox
        self._on_snapshot = on_snapshot
        self._fast_interval_s = fast_interval_s
        self._medium_interval_s = medium_interval_s
        self._slow_interval_s = slow_interval_s

        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # Running by default
        self._thread: Optional[threading.Thread] = None

        self._seq = 0
        self._last_net_counters: Optional[Any] = None
        self._last_net_time: Optional[float] = None
        self._last_disk_counters: Optional[Any] = None
        self._last_disk_time: Optional[float] = None

        # Cached tier slices merged into each published snapshot
        self._cpu_slice = CpuTelemetry()
        self._mem_slice = MemoryTelemetry()
        self._storage_slice = StorageTelemetry()
        self._net_slice = NetworkTelemetry()
        self._sensor_slice = SensorTelemetry()

    def start(self) -> None:
        """Start the background collection thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._prime_counters()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="lcars-psutil-collector",
            daemon=True,
        )
        self._thread.start()

    def stop(self, timeout_s: float = 2.0) -> None:
        """Stop the background collection thread."""
        self._stop_event.set()
        self._pause_event.set()  # Unblock wait if paused
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout_s)

    def set_paused(self, paused: bool) -> None:
        """Pause or resume the background collection thread."""
        if paused:
            self._pause_event.clear()
        else:
            self._pause_event.set()

    def _prime_counters(self) -> None:
        # Per psutil docs, the first cpu_percent(..., interval=None) call returns a
        # baseline/meaningless 0.0 and seeds the per-thread sample state.
        now = time.monotonic()
        try:
            psutil.cpu_percent(interval=None)
            psutil.cpu_percent(interval=None, percpu=True)
        except Exception:
            pass
        try:
            self._last_net_counters = psutil.net_io_counters()
            self._last_net_time = now
        except Exception:
            self._last_net_counters = None
        try:
            self._last_disk_counters = psutil.disk_io_counters()
            self._last_disk_time = now
        except Exception:
            self._last_disk_counters = None

    @staticmethod
    def _delta_rate(
        current_val: Optional[int],
        prev_val: Optional[int],
        dt_s: float,
    ) -> Optional[float]:
        if current_val is None or prev_val is None or dt_s <= 0:
            return None
        if current_val < prev_val:
            return None
        return (current_val - prev_val) / dt_s

    def _poll_fast(self, now: float, errors: list[str]) -> None:
        total_pct: Optional[float] = None
        freq_mhz: Optional[float] = None
        load_1m = load_5m = load_15m = None

        try:
            total_pct = float(psutil.cpu_percent(interval=None))
        except Exception as exc:
            errors.append(f"cpu_percent:{exc}")

        try:
            freq = psutil.cpu_freq()
            if freq is not None:
                freq_mhz = float(freq.current)
        except Exception:
            pass

        if hasattr(os, "getloadavg"):
            try:
                load_1m, load_5m, load_15m = os.getloadavg()
            except Exception:
                pass

        self._cpu_slice = CpuTelemetry(
            total_percent=total_pct,
            per_core_percent=self._cpu_slice.per_core_percent,
            freq_mhz=freq_mhz,
            load_avg_1m=load_1m,
            load_avg_5m=load_5m,
            load_avg_15m=load_15m,
        )

        rx_rate: Optional[float] = None
        tx_rate: Optional[float] = None
        active_ifaces: tuple[str, ...] = ()

        try:
            net_io = psutil.net_io_counters()
            if (
                net_io is not None
                and self._last_net_counters is not None
                and self._last_net_time is not None
            ):
                dt = now - self._last_net_time
                rx_rate = self._delta_rate(
                    net_io.bytes_recv, self._last_net_counters.bytes_recv, dt
                )
                tx_rate = self._delta_rate(
                    net_io.bytes_sent, self._last_net_counters.bytes_sent, dt
                )
            self._last_net_counters = net_io
            self._last_net_time = now
        except Exception as exc:
            errors.append(f"net_io:{exc}")

        try:
            stats = psutil.net_if_stats()
            active_ifaces = tuple(
                sorted(name for name, st in stats.items() if st.isup and name != "lo")
            )
        except Exception:
            pass

        self._net_slice = NetworkTelemetry(
            rx_bytes_per_sec=rx_rate,
            tx_bytes_per_sec=tx_rate,
            active_interfaces=active_ifaces,
        )

    def _poll_medium(self, errors: list[str]) -> None:
        try:
            cores = tuple(
                float(v) for v in psutil.cpu_percent(interval=None, percpu=True)
            )
            self._cpu_slice = CpuTelemetry(
                total_percent=self._cpu_slice.total_percent,
                per_core_percent=cores,
                freq_mhz=self._cpu_slice.freq_mhz,
                load_avg_1m=self._cpu_slice.load_avg_1m,
                load_avg_5m=self._cpu_slice.load_avg_5m,
                load_avg_15m=self._cpu_slice.load_avg_15m,
            )
        except Exception as exc:
            errors.append(f"percpu:{exc}")

        try:
            vm = psutil.virtual_memory()
            sw = psutil.swap_memory()
            self._mem_slice = MemoryTelemetry(
                virtual_total_bytes=int(vm.total),
                virtual_used_bytes=int(vm.used),
                virtual_available_bytes=int(vm.available),
                virtual_percent=float(vm.percent),
                swap_total_bytes=int(sw.total),
                swap_used_bytes=int(sw.used),
                swap_percent=float(sw.percent),
            )
        except Exception as exc:
            errors.append(f"memory:{exc}")

    def _poll_slow(self, now: float, errors: list[str]) -> None:
        mounts_list: list[StorageMountTelemetry] = []
        try:
            for part in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    mounts_list.append(
                        StorageMountTelemetry(
                            mountpoint=part.mountpoint,
                            device=part.device,
                            total_bytes=int(usage.total),
                            used_bytes=int(usage.used),
                            percent=float(usage.percent),
                        )
                    )
                except (PermissionError, OSError):
                    continue
        except Exception as exc:
            errors.append(f"disk_partitions:{exc}")

        read_rate: Optional[float] = None
        write_rate: Optional[float] = None
        try:
            disk_io = psutil.disk_io_counters()
            if (
                disk_io is not None
                and self._last_disk_counters is not None
                and self._last_disk_time is not None
            ):
                dt = now - self._last_disk_time
                read_rate = self._delta_rate(
                    disk_io.read_bytes, self._last_disk_counters.read_bytes, dt
                )
                write_rate = self._delta_rate(
                    disk_io.write_bytes, self._last_disk_counters.write_bytes, dt
                )
            self._last_disk_counters = disk_io
            self._last_disk_time = now
        except Exception as exc:
            errors.append(f"disk_io:{exc}")

        self._storage_slice = StorageTelemetry(
            mounts=tuple(mounts_list),
            read_bytes_per_sec=read_rate,
            write_bytes_per_sec=write_rate,
        )

        max_temp: Optional[float] = None
        if hasattr(psutil, "sensors_temperatures"):
            try:
                temps = psutil.sensors_temperatures(fahrenheit=False) or {}
                readings = [
                    float(entry.current)
                    for entries in temps.values()
                    for entry in entries
                    if entry.current is not None
                ]
                if readings:
                    max_temp = max(readings)
            except Exception:
                pass

        battery_pct: Optional[float] = None
        plugged: Optional[bool] = None
        if hasattr(psutil, "sensors_battery"):
            try:
                bat = psutil.sensors_battery()
                if bat is not None:
                    battery_pct = float(bat.percent)
                    plugged = bool(bat.power_plugged)
            except Exception:
                pass

        uptime_s: Optional[float] = None
        try:
            uptime_s = max(0.0, time.time() - float(psutil.boot_time()))
        except Exception:
            pass

        self._sensor_slice = SensorTelemetry(
            max_temp_c=max_temp,
            battery_percent=battery_pct,
            power_plugged=plugged,
            uptime_seconds=uptime_s,
        )

    def _run_loop(self) -> None:
        next_fast = time.monotonic()
        next_medium = next_fast
        next_slow = next_fast

        while not self._stop_event.is_set():
            self._pause_event.wait(timeout=0.25)
            if self._stop_event.is_set():
                break

            now = time.monotonic()
            errors: list[str] = []
            did_poll = False

            if now >= next_slow:
                self._poll_slow(now, errors)
                next_slow = now + self._slow_interval_s
                did_poll = True

            if now >= next_medium:
                self._poll_medium(errors)
                next_medium = now + self._medium_interval_s
                did_poll = True

            if now >= next_fast:
                self._poll_fast(now, errors)
                next_fast = now + self._fast_interval_s
                did_poll = True

            if did_poll:
                self._seq += 1
                snapshot = TelemetrySnapshot(
                    timestamp_unix_s=time.time(),
                    seq=self._seq,
                    cpu=self._cpu_slice,
                    memory=self._mem_slice,
                    storage=self._storage_slice,
                    network=self._net_slice,
                    sensors=self._sensor_slice,
                    errors=tuple(errors),
                )
                self._mailbox.publish(snapshot)
                if self._on_snapshot is not None:
                    try:
                        self._on_snapshot(snapshot)
                    except Exception:
                        pass

            wake_at = min(next_fast, next_medium, next_slow)
            sleep_for = max(0.05, min(0.5, wake_at - time.monotonic()))
            self._stop_event.wait(timeout=sleep_for)


# Built by referencing the psutil official documentation
# https://psutil.readthedocs.io/ and https://psutil.io/api/
