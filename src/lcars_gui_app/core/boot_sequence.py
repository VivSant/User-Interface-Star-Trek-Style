""" Boot Sequence for the LCARS UI"""
from PySide6.QtCore import QObject, QTimer, Signal

class BootSequence(QObject):
    message_changed = Signal(str)
    finished  = Signal()

    def __init__(self, audio_engine=None, parent=None):
        super().__init__(parent)
        self.audio = audio_engine

        self.steps = [
            ("INITIALIZING LCARS INTERFACE", 900),
            ("LOADING CORE SYSTEMS", 700), 
            ("NETWORK SUBSYSTEM ONLINE", 800),
            ("AUDIO MATRIX READY", 600),
            ("ALL SYSTEMS NOMINAL", 1000),
        ]
        self._index = 0
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._next)

    def start(self):
        """Beging the boot sequence"""
        self._index = 0
        self._next()

    def _next(self):
        if self._index >= len(self.steps):
            self.finished.emit()
            return
    message, delay = self.steps[self._index]
    self.message_changed.emit(message)

    #Play boot sound
    if self.audio is not None:
        self.audio.play("boot_1")

    self._index += 1
    self._timer.start(delay)