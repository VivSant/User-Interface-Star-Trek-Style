"""Audio playback engine (QMediaPlayer) with selectable output device."""

import os
from pathlib import Path

from PySide6.QtCore import QObject, QUrl
from PySide6.QtMultimedia import QAudioDevice, QAudioOutput, QMediaDevices, QMediaPlayer

# Optional environment override, e.g. LCARS_AUDIO_OUTPUT=E7
AUDIO_OUTPUT_ENV_VAR = "LCARS_AUDIO_OUTPUT"


class _Sound:
    """One loaded sound: a media player wired to its own audio output.

    QMediaPlayer is used instead of QSoundEffect because QSoundEffect reports
    playing but stays silent on some Linux/PipeWire setups (Qt 6.12).
    """

    def __init__(self, path: Path, device: QAudioDevice, parent: QObject) -> None:
        """Create the player and output for one sound file.

        Args:
            path: Absolute path to the sound file.
            device: Output device to play on.
            parent: Qt parent that owns the player and output.
        """
        self.output = QAudioOutput(device, parent)
        self.player = QMediaPlayer(parent)
        self.player.setAudioOutput(self.output)
        self.player.setSource(QUrl.fromLocalFile(str(path)))


class AudioEngine(QObject):
    """Simple sound manager that plays named effects on a chosen output device.

    By default sounds follow the system's default output. A preferred output
    can be chosen by name (set_output_by_name), by device
    (set_output_device), or with the LCARS_AUDIO_OUTPUT environment
    variable. When devices are plugged in or removed, every loaded sound is
    moved to the best available output.
    """

    def __init__(
        self,
        preferred_output: str | None = None,
        parent: QObject | None = None,
    ) -> None:
        """Initialize the audio engine.

        Args:
            preferred_output: Part of an output device's name to prefer (case
                insensitive). Falls back to the LCARS_AUDIO_OUTPUT environment
                variable, then to the system default output.
            parent: Optional Qt parent object.
        """
        super().__init__(parent)
        self._effects: dict[str, _Sound] = {}
        # Goes up from core/ -> lcars_gui_app/ -> src/ -> project root
        self._sounds_dir = Path(__file__).resolve().parents[3] / "assets" / "sounds"

        self._preferred_name = preferred_output or os.environ.get(AUDIO_OUTPUT_ENV_VAR)
        self._preferred_device: QAudioDevice | None = None

        # An instance is needed to receive device change notifications
        self._media_devices = QMediaDevices(self)
        self._media_devices.audioOutputsChanged.connect(self._on_outputs_changed)

        self._current_device = self._resolve_device()
        print(f"[AudioEngine] Output: {self._current_device.description()}")

    @staticmethod
    def output_devices() -> list[QAudioDevice]:
        """Return every audio output device Qt can currently use.

        Returns:
            Available output devices, for example to fill a settings dropdown.
        """
        return list(QMediaDevices.audioOutputs())

    def current_output(self) -> QAudioDevice:
        """Return the output device sounds are currently sent to.

        Returns:
            The active QAudioDevice.
        """
        return self._current_device

    def set_output_device(self, device: QAudioDevice | None) -> None:
        """Send all sounds to a specific device.

        Args:
            device: Device from output_devices(), or None to follow the
                system default output.
        """
        self._preferred_device = device
        self._preferred_name = None
        self._apply_device(self._resolve_device())

    def set_output_by_name(self, name_fragment: str) -> bool:
        """Send all sounds to the first device whose name contains the text.

        Args:
            name_fragment: Part of the device description, e.g. "E7".

        Returns:
            True if a matching device was found and selected.
        """
        device = self._find_by_name(name_fragment)
        if device is None:
            return False
        self.set_output_device(device)
        return True

    def load(self, name: str, filename: str, volume: float = 0.65) -> None:
        """Load a sound file into the engine.

        Args:
            name: Key used later with play.
            filename: File name inside assets/sounds.
            volume: Playback volume from 0.0 to 1.0.
        """
        path = self._sounds_dir / filename

        if not path.exists():
            print(f"[AudioEngine] Warning: sound file not found -> {path}")
            return

        sound = _Sound(path, self._current_device, self)
        sound.output.setVolume(max(0.0, min(1.0, volume)))

        self._effects[name] = sound

    def play(self, name: str) -> None:
        """Play a previously loaded sound.

        Args:
            name: Key the sound was loaded under.
        """
        sound = self._effects.get(name)
        if sound is not None:
            # Restart from the beginning so fast repeated clicks stay clean
            sound.player.setPosition(0)
            sound.player.play()
        else:
            print(f"[AudioEngine] Sound '{name}' is not loaded")

    def stop(self, name: str) -> None:
        """Stop a playing sound.

        Args:
            name: Key the sound was loaded under.
        """
        sound = self._effects.get(name)
        if sound is not None:
            sound.player.stop()

    def set_volume(self, name: str, volume: float) -> None:
        """Change the volume of an already loaded sound.

        Args:
            name: Key the sound was loaded under.
            volume: New volume from 0.0 to 1.0.
        """
        sound = self._effects.get(name)
        if sound is not None:
            sound.output.setVolume(max(0.0, min(1.0, volume)))

    def is_loaded(self, name: str) -> bool:
        """Check if a sound is loaded.

        Args:
            name: Key to look up.

        Returns:
            True if a sound was loaded under that key.
        """
        return name in self._effects

    def _find_by_name(self, name_fragment: str) -> QAudioDevice | None:
        """Return the first output whose description contains the text.

        Args:
            name_fragment: Case-insensitive text to search for.

        Returns:
            The matching device, or None if nothing matches.
        """
        wanted = name_fragment.casefold()
        for device in self.output_devices():
            if wanted in device.description().casefold():
                return device
        return None

    def _resolve_device(self) -> QAudioDevice:
        """Pick the best output: chosen device, then name match, then default.

        Returns:
            The device sounds should play on right now.
        """
        if self._preferred_device is not None:
            for device in self.output_devices():
                if device.id() == self._preferred_device.id():
                    return device

        if self._preferred_name:
            device = self._find_by_name(self._preferred_name)
            if device is not None:
                return device

        return QMediaDevices.defaultAudioOutput()

    def _apply_device(self, device: QAudioDevice) -> None:
        """Move every loaded sound to the given output device.

        Args:
            device: Output device to use.
        """
        self._current_device = device
        for sound in self._effects.values():
            sound.player.stop()
            sound.output.setDevice(device)
        print(f"[AudioEngine] Output: {device.description()}")

    def _on_outputs_changed(self) -> None:
        """Re-pick the output when devices are added, removed or changed."""
        device = self._resolve_device()
        if device.id() != self._current_device.id():
            self._apply_device(device)


# This was built by referencing the following Qt documentation:
# QMediaPlayer, find it here:
# https://doc.qt.io/qtforpython-6/PySide6/QtMultimedia/QMediaPlayer.html
# QAudioOutput, find it here:
# https://doc.qt.io/qtforpython-6/PySide6/QtMultimedia/QAudioOutput.html
# QMediaDevices, find it here:
# https://doc.qt.io/qtforpython-6/PySide6/QtMultimedia/QMediaDevices.html
