"""Retro-styled dialog for choosing how long to focus and how long to break."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QSpinBox, QVBoxLayout

import retro

PRESETS = (25, 45, 60, 90, 120, 240)


class TimerDialog(QDialog):
    def __init__(self, focus_minutes, break_minutes):
        super().__init__()
        self.setWindowTitle("My-Woofie: timer settings")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        font = retro.family()
        self.setStyleSheet(f"""
            QDialog {{ background: #1B1B2F; }}
            QLabel {{ color: #FFF4D6; font-family: "{font}"; font-size: 10px; }}
            QLabel#title {{ color: #FFC53D; font-size: 16px; }}
            QLabel#hint {{ color: #A9A4D0; font-size: 8px; }}
            QSpinBox {{ background: #FFF4D6; color: #2A1A0A; border: 4px solid #FFC53D;
                        padding: 6px; font-family: "{font}"; font-size: 14px; min-width: 120px; }}
            QPushButton {{ background: #FFC53D; color: #2A1A0A; border: 4px solid #2A1A0A;
                           padding: 8px 12px; font-family: "{font}"; font-size: 10px; }}
            QPushButton:hover {{ background: #FFE08A; }}
            QPushButton#preset {{ background: #FFF4D6; padding: 6px 8px; }}
            QPushButton#preset:hover {{ background: #FFE08A; }}
        """)
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 22)
        root.setSpacing(12)

        title = QLabel("TIMER SETTINGS")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        root.addWidget(QLabel("FOCUS TIME (MINUTES)"))
        self.focus = QSpinBox()
        self.focus.setRange(1, 720)
        self.focus.setValue(int(focus_minutes))
        root.addWidget(self.focus)
        presets = QHBoxLayout()
        for minutes in PRESETS:
            button = QPushButton(str(minutes))
            button.setObjectName("preset")
            button.clicked.connect(lambda _=False, m=minutes: self.focus.setValue(m))
            presets.addWidget(button)
        root.addLayout(presets)

        root.addWidget(QLabel("BREAK TIME (MINUTES)"))
        self.brk = QSpinBox()
        self.brk.setRange(1, 120)
        self.brk.setValue(int(break_minutes))
        root.addWidget(self.brk)

        hint = QLabel("My-Woofie speaks up after this much continuous\ncomputer use, then counts down your break.")
        hint.setObjectName("hint")
        root.addWidget(hint)

        buttons = QHBoxLayout()
        cancel = QPushButton("CANCEL")
        cancel.clicked.connect(self.reject)
        save = QPushButton("SAVE")
        save.setDefault(True)
        save.clicked.connect(self.accept)
        buttons.addWidget(cancel)
        buttons.addWidget(save)
        root.addLayout(buttons)

    @staticmethod
    def choose(focus_minutes, break_minutes):
        """Show the dialog. Returns (focus, break) in minutes, or None if cancelled."""
        dialog = TimerDialog(focus_minutes, break_minutes)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return dialog.focus.value(), dialog.brk.value()
        return None
