"""Retro 'choose your pup' dialog."""
import random

from PyQt6.QtCore import QRect, Qt, QTimer
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QDialog

import retro
from assets_builder import AVATARS, available_avatars
from gui import load_frames

CARD_W, CARD_H, GAP = 176, 252, 14
CARDS_Y = 80
START_RECT = QRect(0, 350, 200, 48)


class AvatarSelector(QDialog):
    def __init__(self, current=None):
        super().__init__()
        self.setWindowTitle("Aspen: choose your pup")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.ids = available_avatars()
        self.index = self.ids.index(current) if current in self.ids else 0
        self._previews = {a: load_frames(a)["idle"][0] for a in self.ids}
        self._blink = True
        total_w = len(self.ids) * CARD_W + (len(self.ids) + 1) * GAP
        self.setFixedSize(total_w, 438)
        self._start = QRect((total_w - START_RECT.width()) // 2, START_RECT.y(),
                            START_RECT.width(), START_RECT.height())
        rng = random.Random(7)
        self._stars = [(rng.randrange(8, total_w - 12), rng.randrange(8, 426), rng.choice((2, 4)))
                       for _ in range(46)]
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._toggle_blink)
        self._timer.start(450)

    @property
    def selected(self):
        return self.ids[self.index]

    @staticmethod
    def choose(current=None):
        """Show the dialog. Returns the chosen avatar id, or None if it was dismissed."""
        dialog = AvatarSelector(current)
        return dialog.selected if dialog.exec() == QDialog.DialogCode.Accepted else None

    def _toggle_blink(self):
        self._blink = not self._blink
        self.update()

    def _card_rect(self, i):
        return QRect(GAP + i * (CARD_W + GAP), CARDS_Y, CARD_W, CARD_H)

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), retro.NAVY)
        for x, y, size in self._stars:
            p.fillRect(x, y, size, size, retro.TRACK)
        retro.draw_text(p, QRect(0, 22, self.width(), 40), "CHOOSE YOUR PUP", 20, retro.GOLD)

        for i, avatar in enumerate(self.ids):
            rect = self._card_rect(i)
            box = rect.adjusted(0, 0, -4, -4)
            chosen = i == self.index
            border = (retro.GOLD if self._blink else retro.RED) if chosen else retro.INK
            retro.draw_box(p, box, retro.PAPER, border)
            pixmap = self._previews[avatar]
            p.drawPixmap(rect.x() + (box.width() - pixmap.width()) // 2, rect.y() + 10, pixmap)
            info = AVATARS[avatar]
            retro.draw_text(p, QRect(rect.x(), rect.y() + 176, box.width(), 24), info["name"], 14, retro.INK)
            retro.draw_text(p, QRect(rect.x(), rect.y() + 206, box.width(), 20), info["breed"], 8, retro.INK)

        retro.draw_box(p, self._start.adjusted(0, 0, -4, -4), retro.GOLD, retro.INK)
        retro.draw_text(p, self._start.adjusted(0, 0, -4, -4), "START", 14, retro.INK)
        retro.draw_text(p, QRect(0, 414, self.width(), 20), "ARROWS: CHOOSE   ENTER: START", 8, retro.PAPER)

    def mousePressEvent(self, event):
        point = event.position().toPoint()
        for i in range(len(self.ids)):
            if self._card_rect(i).contains(point):
                self.index = i
                self.update()
                return
        if self._start.contains(point):
            self.accept()

    def mouseDoubleClickEvent(self, event):
        point = event.position().toPoint()
        if any(self._card_rect(i).contains(point) for i in range(len(self.ids))):
            self.accept()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Left:
            self.index = (self.index - 1) % len(self.ids)
            self.update()
        elif key == Qt.Key.Key_Right:
            self.index = (self.index + 1) % len(self.ids)
            self.update()
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.accept()
        else:
            super().keyPressEvent(event)
