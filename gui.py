"""Transparent, always-on-top overlay windows: the pet, the retro HUD and the speech bubble."""
import logging
import os

from PyQt6.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QFontMetrics, QImage, QPainter, QPixmap, QTransform
from PyQt6.QtWidgets import QWidget

import config
import retro
from assets_builder import ANIMATIONS, render_frame

log = logging.getLogger("aspen.gui")

SHADOW = 4  # transparent margin kept free for drop shadows


def format_clock(seconds):
    seconds = max(0, int(round(seconds)))
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def _content_box(images):
    """Smallest rectangle containing every visible pixel across all frames of an avatar."""
    x0 = y0 = 10 ** 6
    x1 = y1 = -1
    for img in images:
        for y in range(img.height()):
            for x in range(img.width()):
                if img.pixel(x, y) >> 24:
                    x0, y0, x1, y1 = min(x0, x), min(y0, y), max(x1, x), max(y1, y)
    return QRect(x0, y0, x1 - x0 + 1, y1 - y0 + 1)


def _scale(img, factor):
    """Large sizes use whole-number nearest scaling (crisp); small sizes are supersampled."""
    pixmap = QPixmap.fromImage(img)
    ignore = Qt.AspectRatioMode.IgnoreAspectRatio
    if factor >= 1.8:
        n = round(factor)
        return pixmap.scaled(pixmap.width() * n, pixmap.height() * n, ignore,
                             Qt.TransformationMode.FastTransformation)
    big = pixmap.scaled(pixmap.width() * 4, pixmap.height() * 4, ignore,
                        Qt.TransformationMode.FastTransformation)
    return big.scaled(max(1, round(pixmap.width() * factor)), max(1, round(pixmap.height() * factor)),
                      ignore, Qt.TransformationMode.SmoothTransformation)


def load_frames(avatar, target_px=None):
    """Load an avatar's frames, crop them to the dog and scale so its longest side is target_px."""
    target = target_px or config.SPRITE_TARGET_PX
    images = {}
    for anim, names in ANIMATIONS.items():
        images[anim] = []
        for name in names:
            img = QImage(os.path.join(config.IMAGE_DIR, avatar, name + ".png"))
            if img.isNull():
                log.warning("Sprite %s/%s missing on disk, drawing it in memory", avatar, name)
                img = render_frame(name, avatar)
            images[anim].append(img.convertToFormat(QImage.Format.Format_ARGB32))
    box = _content_box([img for group in images.values() for img in group])
    factor = target / max(box.width(), box.height())
    return {anim: [_scale(img.copy(box), factor) for img in group] for anim, group in images.items()}


def _overlay(widget, click_through):
    flags = (Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
             | Qt.WindowType.Tool)
    if click_through:
        flags |= Qt.WindowType.WindowTransparentForInput
    widget.setWindowFlags(flags)
    widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    widget.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)


class PetWindow(QWidget):
    """Sprite window. Its mask follows the opaque pixels, so clicks anywhere else pass through."""
    clicked = pyqtSignal()
    menu_requested = pyqtSignal(QPoint)

    def __init__(self, frames, native_facing=1):
        super().__init__()
        _overlay(self, click_through=False)
        self._variants = {}
        self._key = None
        self.set_frames(frames, native_facing)

    def set_frames(self, frames, native_facing=1):
        self._frames = frames
        self._native = native_facing
        self._variants.clear()
        self._key = None
        self._pixmap = frames["idle"][0]
        self.setFixedSize(self._pixmap.size())

    def _variant(self, anim, index, flip):
        key = (anim, index, flip)
        if key not in self._variants:
            pixmap = self._frames[anim][index]
            if flip:
                pixmap = pixmap.transformed(QTransform().scale(-1, 1))
            self._variants[key] = (pixmap, pixmap.mask())
        return self._variants[key]

    def sync(self, x, y, anim, facing, now):
        frames = self._frames[anim]
        index = int(now * 1000 / config.ANIMATION_FRAME_MS) % len(frames)
        key = (anim, index, facing != self._native)
        if key != self._key:
            self._key = key
            self._pixmap, mask = self._variant(*key)
            self.setMask(mask)
            self.update()
        self.move(round(x), round(y))

    def paintEvent(self, event):
        QPainter(self).drawPixmap(0, 0, self._pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        elif event.button() == Qt.MouseButton.RightButton:
            self.menu_requested.emit(event.globalPosition().toPoint())


class HudWindow(QWidget):
    """Retro game-style status bar: focus meter, break countdown, or the back-to-work flash."""
    WIDTH, HEIGHT = 428, 60
    SEGMENTS = 16

    def __init__(self, screen_rect):
        super().__init__()
        _overlay(self, click_through=True)
        self.setGeometry(screen_rect.center().x() - self.WIDTH // 2, screen_rect.top() + 8,
                         self.WIDTH, self.HEIGHT)
        self._state = ("FOCUS", 0, "", retro.GREEN)

    def set_state(self, label, fraction, time_text, color):
        """fraction in 0..1 fills the bar; None shows the label alone, centered."""
        filled = None if fraction is None else round(max(0.0, min(1.0, fraction)) * self.SEGMENTS)
        state = (label, filled, time_text, color)
        if state != self._state:
            self._state = state
            self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        box = QRect(0, 0, self.WIDTH - SHADOW, self.HEIGHT - SHADOW)
        retro.draw_box(p, box, retro.NAVY, retro.GOLD)
        label, filled, time_text, color = self._state
        if filled is None:
            retro.draw_text(p, box, label, 14, color)
            return
        retro.draw_text(p, QRect(18, 0, 110, box.height()), label, 10, retro.GOLD, retro.LEFT_VCENTER)
        x0, seg_w, gap, seg_h = 130, 10, 2, 18
        y = (box.height() - seg_h) // 2
        for i in range(self.SEGMENTS):
            p.fillRect(x0 + i * (seg_w + gap), y, seg_w, seg_h, color if i < filled else retro.TRACK)
        retro.draw_text(p, QRect(x0 + self.SEGMENTS * (seg_w + gap) + 8, 0, 90, box.height()),
                        time_text, 10, retro.PAPER, retro.LEFT_VCENTER)


class BubbleWindow(QWidget):
    """Pixel speech bubble that floats above the avatar."""
    MAX_TEXT_W, PAD, TAIL = 240, 14, 8

    def __init__(self):
        super().__init__()
        _overlay(self, click_through=True)
        self._lines = []

    LINE_H = 14

    def _wrap(self, text):
        metrics = QFontMetrics(retro.pixel_font(8))
        lines, current = [], ""
        for word in text.split():
            trial = f"{current} {word}".strip()
            if current and metrics.horizontalAdvance(trial) > self.MAX_TEXT_W:
                lines.append(current)
                current = word
            else:
                current = trial
        lines.append(current)
        width = max(metrics.horizontalAdvance(line) for line in lines)
        return lines, width

    def say(self, text):
        self._lines, text_w = self._wrap(text)
        text_h = len(self._lines) * self.LINE_H - (self.LINE_H - 8)
        self.resize(text_w + 2 * self.PAD + SHADOW, text_h + 2 * self.PAD + self.TAIL + SHADOW)
        self.update()
        self.show()

    def follow(self, pet_x, pet_y, sprite_w, screen_rect):
        x = pet_x + sprite_w / 2 - self.width() / 2
        x = min(max(x, screen_rect.left()), screen_rect.right() - self.width())
        y = max(pet_y - self.height() + 6, screen_rect.top())
        self.move(round(x), round(y))

    def paintEvent(self, event):
        p = QPainter(self)
        box_h = self.height() - self.TAIL - SHADOW
        box = QRect(0, 0, self.width() - SHADOW, box_h)
        retro.draw_box(p, box, retro.PAPER, retro.INK)
        cx = box.width() // 2
        p.fillRect(cx - 8, box_h - 4, 16, 4, retro.INK)
        p.fillRect(cx - 4, box_h - 4, 8, 4, retro.PAPER)
        p.fillRect(cx - 4, box_h, 8, 4, retro.INK)
        p.fillRect(cx - 4, box_h + 4, 4, 4, retro.INK)
        for i, line in enumerate(self._lines):
            retro.draw_text(p, QRect(self.PAD, self.PAD + i * self.LINE_H, self.MAX_TEXT_W + 40, 10),
                            line, 8, retro.INK, retro.LEFT_VCENTER)
