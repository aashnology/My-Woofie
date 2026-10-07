"""One-off helper: turns the artwork in My-Woofie_designs.pdf into clean pixel-art base sprites.

Usage: python tools/import_designs.py path/to/My-Woofie_designs.pdf
Requires: pillow, numpy and poppler's pdfimages. The generated PNGs in assets/designs/ are
committed to the repo, so you only need to run this again if the source artwork changes.
"""
import os
import subprocess
import sys
import tempfile
from collections import deque

import numpy as np
from PIL import Image

CANVAS = 48
OUTLINE = (27, 27, 27)
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "designs")
# PDF page order -> (avatar id, approximate source cell size in pixels, palette size)
DESIGNS = [("bailey", 8.5, 26), ("benny", 16.0, 22), ("snow", 17.5, 12)]


def grid_phase(profile, cell):
    best, best_phase = -1.0, 0.0
    for phase in np.arange(0, cell, 0.25):
        idx = (phase + cell * np.arange(int((len(profile) - phase) / cell))).round().astype(int)
        score = profile[idx[idx < len(profile)]].mean()
        if score > best:
            best, best_phase = score, phase
    return best_phase


def flood_background(is_bg):
    h, w = is_bg.shape
    edge = {(y, x) for y in range(h) for x in (0, w - 1)} | {(y, x) for x in range(w) for y in (0, h - 1)}
    queue, seen = deque(edge), np.zeros((h, w), bool)
    while queue:
        y, x = queue.popleft()
        if 0 <= y < h and 0 <= x < w and not seen[y, x] and is_bg[y, x]:
            seen[y, x] = True
            queue.extend(((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)))
    return seen


def convert(path, name, cell, colors):
    src = Image.open(path).convert("RGB")
    full = np.asarray(src, dtype=int)
    ys, xs = np.where(full.min(axis=2) < 200)
    crop = src.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    palette = np.asarray(crop, dtype=int)
    h, w, _ = palette.shape
    gray = np.asarray(crop.convert("L"), dtype=float)
    ph_x = grid_phase(np.abs(np.diff(gray, axis=1)).sum(axis=0), cell)
    ph_y = grid_phase(np.abs(np.diff(gray, axis=0)).sum(axis=1), cell)

    cols = range(-1, int(np.ceil((w - ph_x) / cell)) + 1)
    rows = range(-1, int(np.ceil((h - ph_y) / cell)) + 1)
    grid = {}
    for r in rows:
        for c in cols:
            x0, x1 = ph_x + c * cell, ph_x + (c + 1) * cell
            y0, y1 = ph_y + r * cell, ph_y + (r + 1) * cell
            cx0, cx1, cy0, cy1 = max(0, x0), min(w, x1), max(0, y0), min(h, y1)
            if (cx1 - cx0) * (cy1 - cy0) < 0.4 * cell * cell:
                continue
            m = 0.2 * cell if (cx1 - cx0 >= cell - 1e-6 and cy1 - cy0 >= cell - 1e-6) else 0
            block = palette[int(cy0 + m):max(int(cy0 + m) + 1, int(cy1 - m)),
                            int(cx0 + m):max(int(cx0 + m) + 1, int(cx1 - m))].reshape(-1, 3)
            if block.size == 0:
                continue
            grid[(r, c)] = tuple(int(v) for v in np.median(block, axis=0))
    r_min, r_max = min(k[0] for k in grid), max(k[0] for k in grid)
    c_min, c_max = min(k[1] for k in grid), max(k[1] for k in grid)
    gh, gw = r_max - r_min + 1, c_max - c_min + 1
    cells = np.full((gh, gw, 3), 255, int)
    for (r, c), color in grid.items():
        cells[r - r_min, c - c_min] = color
    tidy = Image.fromarray(cells.astype(np.uint8), "RGB").quantize(
        colors=colors, method=Image.Quantize.MEDIANCUT, kmeans=3, dither=Image.Dither.NONE).convert("RGB")
    cells = np.asarray(tidy, dtype=int)
    is_bg = (cells.min(axis=2) >= 215) & ((cells.max(axis=2) - cells.min(axis=2)) < 30)
    background = flood_background(is_bg)

    out = np.zeros((CANVAS, CANVAS, 4), np.uint8)
    ox, oy = (CANVAS - gw) // 2, CANVAS - gh - 1
    for y in range(gh):
        for x in range(gw):
            if background[y, x] or (r_min + y, c_min + x) not in grid:
                continue
            color = cells[y, x]
            if 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2] < 62:
                color = OUTLINE
            out[oy + y, ox + x] = (*color, 255)
    os.makedirs(OUT_DIR, exist_ok=True)
    Image.fromarray(out, "RGBA").save(os.path.join(OUT_DIR, name + ".png"))
    print(name, (gw, gh))


def main(pdf):
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(["pdfimages", "-png", pdf, os.path.join(tmp, "img")], check=True)
        for index, (name, cell, colors) in enumerate(DESIGNS):
            convert(os.path.join(tmp, f"img-{index:03d}.png"), name, cell, colors)


if __name__ == "__main__":
    main(sys.argv[1])
