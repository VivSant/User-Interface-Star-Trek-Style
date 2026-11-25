"""Network Connectivity model"""

from dataclasses import dataclassesfrom enum import Enum, auto
import socket
from typing import Optional

class ConnectionState(Enum):
    CONNECTED = auto()
    DISCONNECTED = auto()
    CHECKING = auto()

@dataclass
class etworkStatus:
    state: ConnectionState = ConnectionState.CHECKING
    local_ip: Optional[str] = None
    message: str = "Checking..."

    def refresh(self) -> None:
        """Checks real connectivity and updates the status"""
        try:
            # Quick connectivity test
            socket.create_connection(("8.8.8.8", 53), timeout=1.5)
            self.state = ConnectionState.CONNECTED
            self.message = "Connected"
            self.local_ip = self._get_local_ip()
        except OSError:
            self.state = ConnectionState.DISCONNECTED
            self.message = "Disconnected"
            self.local_ip = None
    def _get_local_ip(self) -> Optional[str]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return None