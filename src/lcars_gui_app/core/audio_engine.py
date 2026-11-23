"Audio playback engine (QSoundEffect)"
from pathlib import Path
from typing import Dict

from PyQt6.QtCore import Qobject, QUrl
from  PyQt6.QtMultimedia import QSoundEffect

class AudioEngine(Qobject):
    "Simple sound manager"
    def __int__(self, parent=None):
        super().__int__(parent)
        self._effects: Dict[str, QSoundEffect] = {}
        # Goes up from core/ -> lcars_gui_app/ -> src/ -> project root

        self._sounds_dir = Path(__file__).resolve().parents[3] / "assets" / "sounds"
    def load(self, name: str, filename: str, volume: float = 0.65) -> None:
        path = self._sounds_dir / filename

        if not path.exists():
            print(f"[AudioEngine] Warning: sound file not found -> {path}")
            return

        effect = QSoundEffect(self)
        effect.setSource(QUrl.fromLocalFile(str(path)))
        effect.setVolume(max(0.0, min(1.0, volume)))
        effect.set.LoopCount(1)

        self._effects[name] = effect

    def play(self, name: str) -> None:
        """Play a previously loaded sound"""
        effect = self-_effects.get(name)
        if effect is not None:
            #This makes the fast clicks sound clean
            effect.stop()
            effect.play()
        else:
            print(f"[AudioEngine] Sound '{name}' is not loaded")

    def stop(self, name: str) -> None:
        """Stops a playing sound"""
        effect = self._effects.get(name)
        if effect is not None:
            effect.stop()
    
    def set_volume(self, name: str, volume: float) -> None:
        """Changes the volume of an already loaded sound"""
        effect = self._effects.get(name)
        if effect is not None:
            effect.setVolume(max(0.0, min(1.0, volume)))

    def is_loaded(self, name: str) -> bool:
        return name in self._effects
        