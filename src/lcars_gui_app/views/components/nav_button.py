"""LCARS navigation button"""
from PySide6.QtWidgets import QPushButton

class NavButton(QPushButton):
    def __init__(self, text: str, color: str, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(70)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color:#111111;
                font-weight: bold;
                font-size: 14px;
                border: none;
                border-radious: 4px;
                text-align: center;
            }}
            QPushButton:hover {{
                border: 2px solid white;
            }}
            QPushButton:pressed {{
                background-color: #ffffff;
            }}
            """)