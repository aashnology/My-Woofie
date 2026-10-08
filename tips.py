"""Break guidance (V2): short, specific things to do during a break, loaded from break_tips.txt.

File format, one tip per line:  category|text      (categories: eyes, stretch, water, posture,
walk, breathe). Blank lines and lines starting with # are ignored. The file is re-read whenever it
changes, so edits apply without a restart.
"""
import logging
import os
import random

log = logging.getLogger("woofie.tips")

CATEGORY_TITLES = {
    "eyes": "EYE REST", "stretch": "STRETCH", "water": "WATER", "posture": "POSTURE",
    "walk": "WALK", "breathe": "BREATHE",
}

BUILT_IN = {
    "eyes": ["Look at something 20 feet away for 20 seconds."],
    "stretch": ["Stand up and reach both arms overhead for 10 seconds."],
    "water": ["Fill your water bottle and have a few sips."],
    "posture": ["Drop your shoulders and sit tall, feet flat on the floor."],
    "walk": ["Take a short walk around the room."],
    "breathe": ["Breathe in for 4 counts, out for 6. Repeat five times."],
}


def parse_tips(lines):
    tips = {}
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "|" not in line:
            continue
        category, text = line.split("|", 1)
        category, text = category.strip().lower(), text.strip()
        if category in CATEGORY_TITLES and text:
            tips.setdefault(category, []).append(text)
    return tips


class TipBank:
    def __init__(self, path, order="sequential"):
        self.path = path
        self.order = order
        self._tips = {k: list(v) for k, v in BUILT_IN.items()}
        self._mtime = None
        self._index = {}
        self._warned = False

    def _refresh(self):
        try:
            mtime = os.path.getmtime(self.path)
        except OSError:
            if not self._warned:
                log.warning("Tip file missing: %s (using built-in tips)", self.path)
                self._warned = True
            return
        if mtime == self._mtime:
            return
        self._mtime = mtime
        try:
            with open(self.path, encoding="utf-8") as handle:
                loaded = parse_tips(handle)
        except OSError as exc:
            log.warning("Could not read %s: %s", self.path, exc)
            return
        merged = {k: list(v) for k, v in BUILT_IN.items()}
        merged.update(loaded)
        self._tips = merged
        log.info("Loaded %d break tips from %s", sum(len(v) for v in loaded.values()),
                 os.path.basename(self.path))

    def next(self, category):
        """Return (title, text) for a category, rotating through that category's tips."""
        self._refresh()
        lines = self._tips.get(category) or BUILT_IN.get(category) or ["Take a moment away from the screen."]
        if self.order == "random" and len(lines) > 1:
            text = random.choice(lines)
        else:
            index = self._index.get(category, 0)
            text = lines[index % len(lines)]
            self._index[category] = index + 1
        return CATEGORY_TITLES.get(category, category.upper()), text

    def any_next(self, categories):
        """Rotate across several categories, one tip from each in turn."""
        self._refresh()
        count = self._index.get("_any", 0)
        self._index["_any"] = count + 1
        return self.next(categories[count % len(categories)])
