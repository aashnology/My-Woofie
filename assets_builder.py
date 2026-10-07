"""Generates Aspen's pixel-art avatars and sound effects on first run.

Existing files in assets/ are never overwritten, so you can drop in your own
art or audio with the same file names and Aspen will use them.
"""
import logging
import math
import os
import random
import struct
import wave

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QImage, QPainter

import config

log = logging.getLogger("aspen.assets")

CANVAS = 32
RATE = 22050

BASE_COLORS = {
    "outline": "#1B1B1B", "gold": "#E9B04B", "ear": "#C98A2E", "cream": "#FFE9B5",
    "eye": "#2E1808", "white": "#FFFFFF", "pink": "#F59AB4", "tongue": "#F2788F",
    "collar": "#D9444F", "tag": "#FFD83A",
}

# Avatar registry. "drawn" avatars are painted in code; "design" avatars are built from the
# base sprites in assets/designs/ (see tools/import_designs.py) and animated by pose edits.
AVATARS = {
    "aspen": dict(kind="drawn", name="ASPEN", breed="GOLDEN RETRIEVER", palette={}),
    "biscuit": dict(kind="drawn", name="BISCUIT", breed="CREAM PUPPY", palette={
        "gold": "#FFF0C8", "ear": "#D18B3C", "cream": "#FFFBEA", "collar": "#3F8FD9"}),
    "cocoa": dict(kind="drawn", name="COCOA", breed="CHOCOLATE LAB", palette={
        "gold": "#8B5A2B", "ear": "#5E3A1A", "cream": "#D9B38C", "collar": "#4CAF6A",
        "tag": "#FFE27A"}),
    "bailey": dict(kind="design", name="BAILEY", breed="BEAGLE", facing=-1, spec=dict(
        head_box=(0, 5, 25, 24), feet=(38, 26), eyes=[(13, 12)], mouth=(8, 22))),
    "benny": dict(kind="design", name="BENNY", breed="BERNESE PUP", facing=1, spec=dict(
        head_box=(0, 0, 48, 28), feet=(40, 24), eyes=[(19, 17), (26, 17)], mouth=None)),
    "snow": dict(kind="design", name="SNOW", breed="FLUFFY PUP", facing=1, spec=dict(
        head_box=(0, 0, 48, 38), feet=(44, 26), eyes=[(18, 31), (26, 31)], mouth=(21, 35))),
}

DESIGN_DIR = os.path.join(config.BASE_DIR, "assets", "designs")

_DEFAULTS = dict(tail=0, eyes="open", mouth="closed", ears=0, head=0, body=0, lift_l=0, lift_r=0)

POSES = {
    "idle_0": dict(),
    "idle_1": dict(tail=1),
    "walk_0": dict(mouth="open", lift_l=2),
    "walk_1": dict(mouth="open", lift_r=2, tail=1, body=-1),
    "bark_0": dict(mouth="open"),
    "bark_1": dict(mouth="wide", head=-1, ears=-2, tail=1),
    "haul_0": dict(mouth="open", ears=-2, lift_l=2),
    "haul_1": dict(mouth="open", eyes="happy", ears=-2, tail=1, lift_r=2),
    "happy_0": dict(mouth="open", eyes="happy"),
    "happy_1": dict(mouth="open", eyes="happy", ears=-2, tail=1),
}

ANIMATIONS = {
    "idle": ["idle_0", "idle_1"],
    "walk": ["walk_0", "walk_1"],
    "bark": ["bark_0", "bark_1"],
    "haul": ["haul_0", "haul_1"],
    "happy": ["happy_0", "happy_1"],
}

SOUND_FILES = ("puppy_bark", "soft_howl", "soft_chime")


# ----- sprites -------------------------------------------------------------
def render_pose(name, avatar="aspen"):
    colors = {**BASE_COLORS, **AVATARS[avatar]["palette"]}
    o = {**_DEFAULTS, **POSES[name]}
    b, hd, ed = o["body"], o["head"], o["ears"]
    img = QImage(CANVAS, CANVAS, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setPen(Qt.PenStyle.NoPen)

    def blob(rect, fill):
        x, y, w, h = rect
        p.setBrush(QColor(colors["outline"]))
        p.drawEllipse(x - 1, y - 1, w + 2, h + 2)
        p.setBrush(QColor(colors[fill]))
        p.drawEllipse(x, y, w, h)

    def px(x, y, w, h, color):
        p.fillRect(x, y, w, h, QColor(colors[color]))

    blob((22, 17, 5, 9) if o["tail"] == 0 else (23, 19, 5, 8), "gold")
    blob((9, 18 + b, 14, 12), "gold")
    p.setBrush(QColor(colors["cream"]))
    p.drawEllipse(12, 19 + b, 8, 10)
    blob((11, 24 + b - o["lift_l"], 4, 6), "cream")
    blob((17, 24 + b - o["lift_r"], 4, 6), "cream")

    blob((3, 5 + ed, 7, 13), "ear")
    blob((22, 5 + ed, 7, 13), "ear")

    blob((7, 3 + hd, 18, 16), "gold")
    px(14, 4 + hd, 4, 7, "cream")
    p.setBrush(QColor(colors["cream"]))
    p.drawEllipse(10, 10 + hd, 12, 9)
    px(8, 13 + hd, 3, 2, "pink")
    px(21, 13 + hd, 3, 2, "pink")

    for ex in (10, 19):
        if o["eyes"] == "open":
            px(ex, 9 + hd, 3, 4, "eye")
            px(ex, 9 + hd, 1, 1, "white")
        elif o["eyes"] == "happy":
            px(ex, 11 + hd, 1, 1, "eye")
            px(ex + 1, 10 + hd, 1, 1, "eye")
            px(ex + 2, 11 + hd, 1, 1, "eye")
        else:
            px(ex, 11 + hd, 3, 1, "eye")

    px(14, 12 + hd, 4, 2, "eye")
    if o["mouth"] == "closed":
        px(13, 15 + hd, 1, 1, "eye")
        px(14, 16 + hd, 4, 1, "eye")
        px(18, 15 + hd, 1, 1, "eye")
    elif o["mouth"] == "open":
        px(14, 15 + hd, 4, 3, "eye")
        px(15, 16 + hd, 2, 3, "tongue")
    else:
        px(13, 15 + hd, 6, 4, "eye")
        px(14, 17 + hd, 4, 2, "tongue")

    px(10, 19, 12, 2, "collar")
    px(15, 21, 3, 3, "outline")
    px(16, 22, 1, 1, "tag")
    px(15, 21, 3, 1, "tag")
    p.end()
    return _shade(img, colors)


def _shade(img, colors):
    """Cell shading in the style of the supplied designs: shadow on lower/right edges, highlight on upper/left."""
    outline = QColor(colors["outline"]).rgb() & 0xFFFFFF
    protected = {QColor(colors[k]).rgb() & 0xFFFFFF for k in ("eye", "white", "pink", "tongue", "tag")}
    w, h = img.width(), img.height()
    src = [[img.pixel(x, y) for x in range(w)] for y in range(h)]

    def solid(x, y):
        return 0 <= x < w and 0 <= y < h and (src[y][x] >> 24) & 255 and (src[y][x] & 0xFFFFFF) != outline

    out = QImage(img)
    for y in range(h):
        for x in range(w):
            c = src[y][x]
            rgb = c & 0xFFFFFF
            if not (c >> 24) & 255 or rgb == outline or rgb in protected:
                continue
            r, g, b = (rgb >> 16) & 255, (rgb >> 8) & 255, rgb & 255
            if not solid(x, y + 1) or not solid(x + 1, y):
                r, g, b = int(r * 0.80), int(g * 0.80), int(b * 0.80)
            elif not solid(x, y - 1) or not solid(x - 1, y):
                r, g, b = (int(v + (255 - v) * 0.22) for v in (r, g, b))
            else:
                continue
            out.setPixel(x, y, 0xFF000000 | (r << 16) | (g << 8) | b)
    return out


# ----- designs ---------------------------------------------------------------
_DARK = 0xFF1B1B1B
_PINK = 0xFFF59AB4


def base_path(avatar):
    return os.path.join(DESIGN_DIR, avatar + ".png")


def available_avatars():
    return [a for a, meta in AVATARS.items() if meta["kind"] == "drawn" or os.path.isfile(base_path(a))]


def _load_grid(path):
    img = QImage(path).convertToFormat(QImage.Format.Format_ARGB32)
    return [[img.pixel(x, y) if (img.pixel(x, y) >> 24) & 255 else 0 for x in range(img.width())]
            for y in range(img.height())]


def _copy(grid):
    return [row[:] for row in grid]


def _lift_region(grid, box, d):
    """Move a rectangular region (the head) up by d cells, stretching its bottom row to stay joined."""
    x0, y0, x1, y1 = box
    out = _copy(grid)
    for y in range(y0, y1):
        if y - d >= 0:
            out[y - d][x0:x1] = grid[y][x0:x1]
    for y in range(y1 - d, y1):
        out[y][x0:x1] = grid[y1 - 1][x0:x1]
    return out


def _lift_feet(grid, y0, x0, x1, d=1):
    """Raise the paws in columns x0..x1 by d cells."""
    out = _copy(grid)
    height = len(grid)
    for y in range(y0, height):
        out[y - d][x0:x1] = grid[y][x0:x1]
    for y in range(height - d, height):
        out[y][x0:x1] = [0] * (x1 - x0)
    return out


def _face_color(grid, x, y):
    for dx, dy in ((0, -2), (0, -3), (3, 0), (-3, 0), (0, 3), (2, -2)):
        if 0 <= y + dy < len(grid) and 0 <= x + dx < len(grid[0]):
            c = grid[y + dy][x + dx]
            if c and 0.299 * ((c >> 16) & 255) + 0.587 * ((c >> 8) & 255) + 0.114 * (c & 255) > 110:
                return c
    return 0xFFFFFFFF


def _happy_eyes(grid, eyes):
    for x, y in eyes:
        fill = _face_color(grid, x, y)
        for yy in (y, y + 1):
            for xx in (x, x + 1):
                grid[yy][xx] = fill
        for xx in range(x - 1, x + 3):
            grid[y + 1][xx] = _DARK


def _open_mouth(grid, mx, my):
    for yy in (my, my + 1):
        for xx in (mx, mx + 1, mx + 2):
            grid[yy][xx] = _DARK
    grid[my + 1][mx + 1] = _PINK


def render_design_pose(name, avatar):
    spec = AVATARS[avatar]["spec"]
    grid = _load_grid(base_path(avatar))
    happy = name in ("haul_0", "haul_1", "happy_0", "happy_1")
    if happy:
        _happy_eyes(grid, spec["eyes"])
    if spec["mouth"] and (happy or name in ("bark_0", "bark_1")):
        _open_mouth(grid, *spec["mouth"])
    lift = {"idle_1": 1, "bark_1": 2, "haul_0": 1, "haul_1": 1, "happy_1": 1}.get(name, 0)
    if lift:
        grid = _lift_region(grid, spec["head_box"], lift)
    feet_y, mid = spec["feet"]
    if name in ("walk_0", "haul_1"):
        grid = _lift_feet(grid, feet_y, 0, mid)
    elif name == "walk_1":
        grid = _lift_feet(grid, feet_y, mid, len(grid[0]))
    img = QImage(len(grid[0]), len(grid), QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    for y, row in enumerate(grid):
        for x, value in enumerate(row):
            if value:
                img.setPixel(x, y, value)
    return img


def render_frame(name, avatar):
    if AVATARS[avatar]["kind"] == "design":
        return render_design_pose(name, avatar)
    return render_pose(name, avatar)


# ----- sounds --------------------------------------------------------------
def _normalize(samples, peak=0.85):
    top = max((abs(s) for s in samples), default=0.0) or 1.0
    return [s / top * peak for s in samples]


def _fade_out(samples, ms=8):
    n = min(len(samples), int(RATE * ms / 1000))
    for i in range(n):
        samples[len(samples) - 1 - i] *= i / n
    return samples


def _formant_gain(freq):
    return (1.0 + 2.2 * math.exp(-((freq - 900) / 350) ** 2)
            + 1.2 * math.exp(-((freq - 2300) / 700) ** 2))


def _yip(f0, dur, seed):
    """One puppy yap: falling pitch, vocal-tract formants and a breathy onset."""
    rng = random.Random(seed)
    n = int(dur * RATE)
    phase, lowpass, jitter = 0.0, 0.0, 0.0
    out = []
    for i in range(n):
        ts, t = i / RATE, i / n
        jitter += (rng.uniform(-1, 1) - jitter) * 0.02
        freq = f0 * (1.35 - 0.7 * t ** 0.7) * (1 + 0.02 * jitter)
        phase += 2 * math.pi * freq / RATE
        voiced = 0.0
        for k in range(1, 11):
            fk = freq * k
            if fk > 7500:
                break
            voiced += math.sin(k * phase) / (k ** 1.05) * _formant_gain(fk)
        lowpass += (rng.uniform(-1, 1) - lowpass) * 0.35
        env = min(ts / 0.008, 1.0) * math.exp(-ts * 9.0)
        burst = math.exp(-ts * 45)
        out.append((voiced * 0.4 + lowpass * (0.8 * burst + 0.15)) * env)
    return _fade_out(out)


def _bark_samples():
    out = _yip(640, 0.20, 1) + [0.0] * int(0.11 * RATE)
    out += _yip(720, 0.17, 2) + [0.0] * int(0.10 * RATE)
    return _normalize(out)


def _howl_samples():
    dur = 1.9
    n = int(dur * RATE)
    phase = 0.0
    out = []
    for i in range(n):
        ts = i / RATE
        t = ts / dur
        if t < 0.3:
            base = 330 + 170 * (t / 0.3) ** 0.8
        elif t < 0.7:
            base = 500
        else:
            base = 500 - 110 * ((t - 0.7) / 0.3)
        vibrato = 7 * min(1.0, max(0.0, (ts - 0.35) / 0.5)) * math.sin(2 * math.pi * 5.3 * ts)
        phase += 2 * math.pi * (base + vibrato) / RATE
        tone = (math.sin(phase) + 0.5 * math.sin(2 * phase) + 0.25 * math.sin(3 * phase)
                + 0.12 * math.sin(4 * phase) + 0.06 * math.sin(5 * phase))
        env = math.sin(min(ts / 0.3, 1.0) * math.pi / 2) ** 2 * min(1.0, (dur - ts) / 0.5)
        out.append(tone * env)
    return _normalize(out, 0.7)


def _chime_samples():
    total = int(1.5 * RATE)
    buf = [0.0] * total
    partials = ((1.0, 1.0, 3.0), (2.0, 0.35, 5.0), (3.01, 0.15, 8.0))
    for start, f0 in ((0.0, 988.0), (0.2, 1318.5)):
        offset = int(start * RATE)
        for i in range(min(int(1.2 * RATE), total - offset)):
            ts = i / RATE
            value = sum(a * math.sin(2 * math.pi * f0 * r * ts) * math.exp(-ts * d)
                        for r, a, d in partials)
            buf[offset + i] += value * min(ts / 0.004, 1.0)
    return _normalize(buf, 0.7)


_SOUND_BUILDERS = {"puppy_bark": _bark_samples, "soft_howl": _howl_samples,
                   "soft_chime": _chime_samples}


def _write_wav(path, samples):
    frames = b"".join(struct.pack("<h", int(max(-1.0, min(1.0, s)) * 32767)) for s in samples)
    with wave.open(path, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(RATE)
        wav.writeframes(frames)


def ensure_assets():
    os.makedirs(config.AUDIO_DIR, exist_ok=True)
    for avatar in available_avatars():
        folder = os.path.join(config.IMAGE_DIR, avatar)
        os.makedirs(folder, exist_ok=True)
        for name in POSES:
            path = os.path.join(folder, name + ".png")
            if not os.path.isfile(path):
                if render_frame(name, avatar).save(path):
                    log.info("Generated sprite %s/%s", avatar, name)
                else:
                    log.warning("Could not save sprite %s", path)
    for stem in SOUND_FILES:
        path = os.path.join(config.AUDIO_DIR, stem + ".wav")
        if not os.path.isfile(path):
            try:
                _write_wav(path, _SOUND_BUILDERS[stem]())
                log.info("Generated audio %s.wav", stem)
            except OSError as exc:
                log.warning("Could not write %s: %s", path, exc)
