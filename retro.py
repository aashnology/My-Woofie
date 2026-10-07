"""Retro pixel-art styling helpers: palette, bitmap font and notched pixel boxes."""
import logging
import os

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QFontDatabase

import config

log = logging.getLogger("aspen.retro")

INK = QColor("#2A1A0A")
PAPER = QColor("#FFF4D6")
NAVY = QColor("#1B1B2F")
PLUM = QColor("#2B2347")
GOLD = QColor("#FFC53D")
GREEN = QColor("#5BD36B")
AMBER = QColor("#FFB02E")
RED = QColor("#F2545B")
BLUE = QColor("#4DA8FF")
TRACK = QColor("#3A3560")
SHADOW = QColor(0, 0, 0, 90)

CENTER_WRAP = Qt.AlignmentFlag.AlignCenter.value | Qt.TextFlag.TextWordWrap.value
LEFT_WRAP = (Qt.AlignmentFlag.AlignLeft.value | Qt.AlignmentFlag.AlignTop.value
             | Qt.TextFlag.TextWordWrap.value)
LEFT_VCENTER = Qt.AlignmentFlag.AlignLeft.value | Qt.AlignmentFlag.AlignVCenter.value

_family = None


def load_font():
    """Register the bundled pixel font. Falls back to a monospace system font."""
    global _family
    if os.path.isfile(config.FONT_FILE):
        font_id = QFontDatabase.addApplicationFont(config.FONT_FILE)
        families = QFontDatabase.applicationFontFamilies(font_id) if font_id >= 0 else []
        if families:
            _family = families[0]
            return
    log.warning("Pixel font not found at %s; using Courier New", config.FONT_FILE)
    _family = "Courier New"


def pixel_font(pixel_size):
    font = QFont(_family or "Courier New")
    font.setPixelSize(pixel_size)
    font.setStyleStrategy(QFont.StyleStrategy.NoAntialias)
    return font


def _notched(painter, rect, color, notch):
    x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
    painter.fillRect(x + notch, y, w - 2 * notch, h, color)
    painter.fillRect(x, y + notch, w, h - 2 * notch, color)


def draw_box(painter, rect, fill, border=INK, shadow=True, px=4):
    """Pixel container with chunky border, notched corners and a drop shadow."""
    if shadow:
        _notched(painter, rect.translated(px, px), SHADOW, px)
    _notched(painter, rect, border, px)
    _notched(painter, rect.adjusted(px, px, -px, -px), fill, max(1, px // 2))


def draw_text(painter, rect, text, pixel_size, color, flags=CENTER_WRAP):
    painter.setFont(pixel_font(pixel_size))
    painter.setPen(color)
    painter.drawText(rect, flags, text)
