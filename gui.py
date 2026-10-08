"""Transparent, always-on-top overlay windows: the pet, the retro HUD and the speech bubble."""
import logging
import os
import time

from PyQt6.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QFontMetrics, QImage, QPainter, QPixmap, QTransform
from PyQt6.QtWidgets import QWidget

import config
import retro
import wardrobe
from assets_builder import ANIMATIONS, render_frame

log = logging.getLogger("woofie.gui")

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
    """Large previews scale in whole-number steps; small sizes are supersampled for clean edges."""
    pixmap = QPixmap.fromImage(img)
    ignore = Qt.AspectRatioMode.IgnoreAspectRatio
    if factor >= 3:
        n = int(factor)
        return pixmap.scaled(pixmap.width() * n, pixmap.height() * n, ignore,
                             Qt.TransformationMode.FastTransformation)
    big = pixmap.scaled(pixmap.width() * 4, pixmap.height() * 4, ignore,
                        Qt.TransformationMode.FastTransformation)
    return big.scaled(max(1, round(pixmap.width() * factor)), max(1, round(pixmap.height() * factor)),
                      ignore, Qt.TransformationMode.SmoothTransformation)


def _fit(img, factor, width, height):
    """Place the scaled dog bottom-centre on a transparent canvas of exactly width x height."""
    dog = _scale(img, factor)
    canvas = QPixmap(width, height)
    canvas.fill(Qt.GlobalColor.transparent)
    painter = QPainter(canvas)
    painter.drawPixmap((width - dog.width()) // 2, height - dog.height(), dog)
    painter.end()
    return canvas


def _squash(pixmap, sx, sy):
    """Squash a frame toward its bottom edge, keeping the canvas size (used for sleep and stretch)."""
    w, h = pixmap.width(), pixmap.height()
    sw, sh = max(1, round(w * sx)), max(1, round(h * sy))
    scaled = pixmap.scaled(sw, sh, Qt.AspectRatioMode.IgnoreAspectRatio,
                           Qt.TransformationMode.FastTransformation)
    canvas = QPixmap(w, h)
    canvas.fill(Qt.GlobalColor.transparent)
    painter = QPainter(canvas)
    painter.drawPixmap((w - sw) // 2, h - sh, scaled)
    painter.end()
    return canvas


def derive_frames(frames):
    """Add the V2 poses that are built from the drawn ones: curled-up sleep and a play-bow stretch."""
    frames["sleep"] = [_squash(frames["happy"][0], 1.0, 0.90), _squash(frames["happy"][0], 1.0, 0.86)]
    frames["stretch"] = [_squash(frames["idle"][0], 1.0, 0.82), _squash(frames["idle"][1], 1.0, 0.90)]
    return frames


def load_frames(avatar, size=None, accessory=None):
    """Load an avatar's frames, crop them to the dog and fit them onto a fixed-size canvas.

    Every frame of every avatar comes out exactly `size` pixels (default config.SPRITE_SIZE).
    With an accessory the dog is drawn a little smaller to leave room for it on the same canvas.
    """
    width, height = size or config.SPRITE_SIZE
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
    fit_height = height - wardrobe.reserve_rows(accessory) if accessory else height
    factor = min(width / box.width(), fit_height / box.height())
    frames = {anim: [_fit(img.copy(box), factor, width, height) for img in group]
              for anim, group in images.items()}
    if accessory:
        frames = {anim: [wardrobe.apply(pix, accessory, avatar) for pix in group]
                  for anim, group in frames.items()}
    return derive_frames(frames)


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
    pressed = pyqtSignal()
    released = pyqtSignal()
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
            self.pressed.emit()
        elif event.button() == Qt.MouseButton.RightButton:
            self.menu_requested.emit(event.globalPosition().toPoint())

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.released.emit()


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

    def move_to_screen(self, screen_rect):
        """Place the bar at the top centre of the given monitor."""
        self.move(screen_rect.center().x() - self.WIDTH // 2, screen_rect.top() + 8)

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


def wrap_text(text, pixel_size, max_width):
    """Split text into lines that fit max_width in the pixel font. Returns (lines, widest line)."""
    metrics = QFontMetrics(retro.pixel_font(pixel_size))
    lines, current = [], ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if current and metrics.horizontalAdvance(trial) > max_width:
            lines.append(current)
            current = word
        else:
            current = trial
    lines.append(current)
    return lines, max(metrics.horizontalAdvance(line) for line in lines)


ICONS = {
    "heart": (["..RR.RR..", ".RRRRRRR.", ".RRWRRRR.", ".RRRRRRR.", "..RRRRR..", "...RRR...", "....R...."], 3),
    "z1": (["ZZZZZ", "...ZZ", "..ZZ.", ".ZZ..", "ZZZZZ"], 3),
    "z2": (["ZZZZ", "..ZZ", ".ZZ.", "ZZZZ"], 2),
    "sweat": ([".S.", "SSS", "SSS", ".S."], 3),
    "star": (["..Y..", ".YYY.", "YYYYY", ".YYY.", "Y...Y"], 3),
    "sparkle": (["..Y..", "..Y..", "YYYYY", "..Y..", "..Y.."], 3),
}


def icon_pixmap(name):
    rows, scale = ICONS[name]
    img = wardrobe._art_image(rows, outline=False)
    return QPixmap.fromImage(img).scaled(img.width() * scale, img.height() * scale,
                                         Qt.AspectRatioMode.IgnoreAspectRatio,
                                         Qt.TransformationMode.FastTransformation)


class EmoteWindow(QWidget):
    """A small icon (heart, Zzz, sweat drop, star) that floats beside the dog's head."""

    def __init__(self):
        super().__init__()
        _overlay(self, click_through=True)
        self._pixmaps = {}
        self._name = None
        self._until = 0.0
        self.resize(40, 40)

    def show_emote(self, name, now, seconds=2.0):
        self._name = name
        self._until = now + seconds
        if name not in self._pixmaps:
            self._pixmaps[name] = icon_pixmap(name)
        self.resize(self._pixmaps[name].size())
        self.update()
        self.show()

    @property
    def active(self):
        return self._name is not None

    def clear(self):
        self._name = None
        self.hide()

    def tick(self, now, pet_x, pet_y, sprite_w, sleeping=False):
        """Follow the dog; Zzz alternates its two shapes; hide when the time is up."""
        if self._name is None:
            return
        if not sleeping and now >= self._until:
            self.clear()
            return
        if sleeping and self._name in ("z1", "z2"):
            wanted = "z1" if int(now * 1.5) % 2 == 0 else "z2"
            if wanted != self._name:
                self._name = wanted
                if wanted not in self._pixmaps:
                    self._pixmaps[wanted] = icon_pixmap(wanted)
                self.resize(self._pixmaps[wanted].size())
                self.update()
        self.move(round(pet_x + sprite_w - 6), round(pet_y - self.height() + 8))

    def paintEvent(self, event):
        if self._name is not None:
            QPainter(self).drawPixmap(0, 0, self._pixmaps[self._name])


class ToyWindow(QWidget):
    """The fetch ball (grab it and throw it) or the treat bone (click-through)."""
    grabbed = pyqtSignal()
    dragged = pyqtSignal(float, float)       # top-left x, y while dragging
    released = pyqtSignal(float, float)      # throw velocity in pixels per frame

    ART = {
        "ball": (["..LLL..", ".LWLLLL", "LWLLLLL", "LLLLLLL", "LLLLLWL", ".LLLLWL", "..LLL.."], 2),
        "bone": (["CC....CC", "CCCCCCCC", "CCCCCCCC", "CC....CC"], 2),
    }

    def __init__(self, kind):
        super().__init__()
        self.kind = kind
        _overlay(self, click_through=(kind != "ball"))
        rows, scale = self.ART[kind]
        img = wardrobe._art_image(rows)
        self._pixmap = QPixmap.fromImage(img).scaled(img.width() * scale, img.height() * scale,
                                                     Qt.AspectRatioMode.IgnoreAspectRatio,
                                                     Qt.TransformationMode.FastTransformation)
        self.setFixedSize(self._pixmap.size())
        self.setMask(self._pixmap.mask())
        self._grab = None
        self._samples = []

    def paintEvent(self, event):
        QPainter(self).drawPixmap(0, 0, self._pixmap)

    def place(self, x, y):
        self.move(round(x), round(y))

    def mousePressEvent(self, event):
        if self.kind == "ball" and event.button() == Qt.MouseButton.LeftButton:
            point = event.globalPosition()
            self._grab = (point.x() - self.x(), point.y() - self.y())
            self._samples = [(time.monotonic(), point.x(), point.y())]
            self.grabbed.emit()

    def mouseMoveEvent(self, event):
        if self._grab is None:
            return
        point = event.globalPosition()
        now = time.monotonic()
        self._samples = [s for s in self._samples if now - s[0] < 0.12] + [(now, point.x(), point.y())]
        x, y = point.x() - self._grab[0], point.y() - self._grab[1]
        self.move(round(x), round(y))
        self.dragged.emit(x, y)

    def mouseReleaseEvent(self, event):
        if self._grab is None:
            return
        self._grab = None
        from toys import velocity_from_samples
        vx, vy = velocity_from_samples(self._samples)
        self._samples = []
        self.released.emit(vx, vy)


class AlertPanel(QWidget):
    """Retro card under the HUD: break guidance with Snooze, or a micro-break with Done / Skip."""
    WIDTH, HEIGHT = 428, 150
    snooze_clicked = pyqtSignal()
    dismiss_clicked = pyqtSignal()
    done_clicked = pyqtSignal()
    skip_clicked = pyqtSignal()

    def __init__(self):
        super().__init__()
        _overlay(self, click_through=False)
        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.mode = "break"
        self._title = ""
        self._lines = []
        self._time = ""
        self._snooze_left = 0
        self._snooze_text = "SNOOZE"
        self._left = QRect(14, 98, 192, 32)
        self._right = QRect(214, 98, 192, 32)
        self._hover = None

    def move_to_screen(self, screen_rect):
        self.move(screen_rect.center().x() - self.WIDTH // 2, screen_rect.top() + 76)

    def show_break(self, tip_title, tip_text, snooze_left, snooze_minutes):
        self.mode = "break"
        self._title = "BREAK TIME: " + tip_title
        self._lines, _ = wrap_text(tip_text, 8, 380)
        self._snooze_left = snooze_left
        self._snooze_text = f"SNOOZE {snooze_minutes:g} MIN ({snooze_left} LEFT)"
        self._set_visible()

    def show_micro(self, tip_title, tip_text):
        self.mode = "micro"
        self._title = "QUICK BREAK: " + tip_title
        self._lines, _ = wrap_text(tip_text, 8, 380)
        self._set_visible()

    def _set_visible(self):
        self.update()
        self.show()

    def set_tip(self, tip_title, tip_text):
        prefix = "BREAK TIME: " if self.mode == "break" else "QUICK BREAK: "
        self._title = prefix + tip_title
        self._lines, _ = wrap_text(tip_text, 8, 380)
        self.update()

    def set_snooze_left(self, left, minutes):
        if left != self._snooze_left:
            self._snooze_left = left
            self._snooze_text = f"SNOOZE {minutes:g} MIN ({left} LEFT)"
            self.update()

    def set_time(self, text):
        if text != self._time:
            self._time = text
            self.update()

    def _button(self, painter, rect, text, fill, enabled=True):
        color = fill if enabled else retro.TRACK
        retro.draw_box(painter, rect.adjusted(0, 0, -4, -4), color, retro.INK, shadow=False, px=2)
        retro.draw_text(painter, rect.adjusted(0, 0, -4, -4), text, 8,
                        retro.INK if enabled else retro.PAPER)

    def paintEvent(self, event):
        p = QPainter(self)
        box = QRect(0, 0, self.WIDTH - SHADOW, self.HEIGHT - SHADOW)
        retro.draw_box(p, box, retro.NAVY, retro.GOLD)
        retro.draw_text(p, QRect(16, 12, 300, 18), self._title, 10, retro.GOLD, retro.LEFT_VCENTER)
        retro.draw_text(p, QRect(box.width() - 108, 12, 92, 18), self._time, 10, retro.PAPER,
                        Qt.AlignmentFlag.AlignRight.value | Qt.AlignmentFlag.AlignVCenter.value)
        for i, line in enumerate(self._lines[:3]):
            retro.draw_text(p, QRect(16, 40 + i * 16, 392, 12), line, 8, retro.PAPER, retro.LEFT_VCENTER)
        if self.mode == "break":
            self._button(p, self._left, self._snooze_text, retro.AMBER, self._snooze_left > 0)
            self._button(p, self._right, "OK, ON IT!", retro.GREEN)
        else:
            self._button(p, self._left, "DONE", retro.GREEN)
            self._button(p, self._right, "SKIP", retro.PAPER)

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        point = event.position().toPoint()
        if self._left.contains(point):
            if self.mode == "break":
                if self._snooze_left > 0:
                    self.snooze_clicked.emit()
            else:
                self.done_clicked.emit()
        elif self._right.contains(point):
            (self.dismiss_clicked if self.mode == "break" else self.skip_clicked).emit()
