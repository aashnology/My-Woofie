"""Accessories for My-Woofie (V2): tiny pixel-art hats and a bandana drawn onto the sprite frames.

Hats sit on the crown of the head, found by looking at the frame's own pixels. The bandana sits at
the neck, using a fixed spot per dog. Everything is drawn on the same 53 x 47 canvas as the dog,
so accessories never change the size of the window.
"""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QImage, QPainter, QPixmap

HAT_COLORS = {
    "P": "#F2545B", "W": "#FFFFFF", "Y": "#FFC53D", "B": "#4DA8FF", "N": "#2B2347",
    "K": "#2A2A3A", "R": "#D9444F", "G": "#5BD36B", "T": "#2BB3A3", "O": "#FF8FB1",
    "L": "#C8E64B", "C": "#FFF4D6", "H": "#F2D7A0", "Z": "#9AD0FF", "S": "#7CC4FF",
}

HAT_ART = {
    "party_hat": [
        "...Y...",
        "..PPP..",
        "..PWP..",
        ".PPPPP.",
        ".PWPPP.",
        "PPPPPWP",
    ],
    "flower": [
        ".O.O.",
        "OOYOO",
        ".OOO.",
    ],
    "beanie": [
        "....W....",
        "...WWW...",
        "..BBBBB..",
        ".BBBBBBB.",
        ".RRRRRRR.",
        ".BBBBBBB.",
    ],
    "top_hat": [
        "..KKKKK..",
        "..KKKKK..",
        "..KKKKK..",
        "..RRRRR..",
        "KKKKKKKKK",
    ],
    "crown": [
        "Y...Y...Y",
        "YY.YYY.YY",
        "YYYYYYYYY",
        "YRYYYYYRY",
        "YYYYYYYYY",
    ],
}

BANDANA_ART = [
    "TTTTTTT",
    ".TWTTWT.",
    "..TTTT..",
    "...TT...",
]

HATS = tuple(HAT_ART)
ALL = HATS + ("bandana",)
OVERLAP = 2                    # rows of the hat that sit on the head

# Where the crown search looks, as a share of the dog's width (left, right). Bailey's tail is the
# tallest part of his silhouette, so only his head side is searched.
CROWN_REGION = {"bailey": (0.0, 0.42)}

# Neck spot as (x share, y share) of the dog's visible area.
NECK_SPOT = {
    "aspen": (0.50, 0.61), "biscuit": (0.50, 0.61), "cocoa": (0.50, 0.61),
    "bailey": (0.36, 0.46), "benny": (0.56, 0.66), "snow": (0.45, 0.71),
}

TITLES = {
    "party_hat": "PARTY HAT", "flower": "FLOWER", "beanie": "BEANIE", "bandana": "BANDANA",
    "top_hat": "TOP HAT", "crown": "CROWN",
}


def _art_image(rows, outline=True):
    """Colored bitmap from text rows, with a 1-pixel dark outline around it."""
    w, h = max(len(r) for r in rows), len(rows)
    pad = 1 if outline else 0
    img = QImage(w + 2 * pad, h + 2 * pad, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    solid = set()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in HAT_COLORS:
                img.setPixelColor(x + pad, y + pad, QColor(HAT_COLORS[ch]))
                solid.add((x + pad, y + pad))
    if outline:
        edge = QColor("#1B1B1B")
        for (x, y) in solid:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if (nx, ny) not in solid and 0 <= nx < img.width() and 0 <= ny < img.height():
                    img.setPixelColor(nx, ny, edge)
    return img


def hat_height(name):
    return len(HAT_ART[name]) + 2 if name in HAT_ART else 0


def reserve_rows(name):
    """Rows the dog must give up at the top of the canvas to make room for the accessory."""
    return max(0, hat_height(name) - OVERLAP) if name in HAT_ART else 0


def crown_anchor(img, region=(0.0, 1.0)):
    """(x, y) of the top of the head: first row with pixels inside the region, mean x of two rows."""
    xs = [x for x in range(img.width()) if any(img.pixelColor(x, y).alpha() > 0 for y in range(img.height()))]
    if not xs:
        return None
    lo = xs[0] + region[0] * (xs[-1] - xs[0])
    hi = xs[0] + region[1] * (xs[-1] - xs[0])
    for y in range(img.height()):
        row = [x for x in range(img.width()) if lo <= x <= hi and img.pixelColor(x, y).alpha() > 0]
        if row:
            sample = row[:]
            if y + 1 < img.height():
                sample += [x for x in range(img.width()) if lo <= x <= hi and img.pixelColor(x, y + 1).alpha() > 0]
            return round(sum(sample) / len(sample)), y
    return None


def _visible_box(img):
    xs, ys = [], []
    for y in range(img.height()):
        for x in range(img.width()):
            if img.pixelColor(x, y).alpha() > 0:
                xs.append(x)
                ys.append(y)
    if not xs:
        return None
    return min(xs), min(ys), max(xs), max(ys)


def apply(pixmap, name, avatar):
    """Return a copy of the frame wearing the accessory (or the frame itself for None)."""
    if name is None or name not in ALL:
        return pixmap
    img = pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)
    painter = QPainter(img)
    if name in HAT_ART:
        anchor = crown_anchor(img, CROWN_REGION.get(avatar, (0.0, 1.0)))
        if anchor is not None:
            hat = _art_image(HAT_ART[name])
            painter.drawImage(anchor[0] - hat.width() // 2, anchor[1] + OVERLAP - hat.height() + 1, hat)
    else:
        box = _visible_box(img)
        if box is not None:
            fx, fy = NECK_SPOT.get(avatar, (0.5, 0.55))
            cx = box[0] + fx * (box[2] - box[0])
            cy = box[1] + fy * (box[3] - box[1])
            scarf = _art_image(BANDANA_ART)
            painter.drawImage(round(cx - scarf.width() / 2), round(cy - scarf.height() / 2), scarf)
    painter.end()
    return QPixmap.fromImage(img)


def icon(name, scale=4):
    """Pixmap of the accessory alone, for the wardrobe dialog."""
    rows = BANDANA_ART if name == "bandana" else HAT_ART[name]
    img = _art_image(rows)
    return QPixmap.fromImage(img).scaled(img.width() * scale, img.height() * scale,
                                         Qt.AspectRatioMode.IgnoreAspectRatio,
                                         Qt.TransformationMode.FastTransformation)
