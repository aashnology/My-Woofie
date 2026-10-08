"""Mood, daily counters and wardrobe: the part of My-Woofie that remembers how he feels (V2).

Everything here is plain numbers saved to pet_state.json on this computer.
"""
import json
import logging
import os
import time
from datetime import date

import config

log = logging.getLogger("woofie.mood")

LEVELS = (("ecstatic", 85), ("happy", 60), ("okay", 35), ("droopy", 15), ("sad", -1))


class Mood:
    def __init__(self, value=None):
        self.value = config.MOOD_START if value is None else self._clamp(value)

    @staticmethod
    def _clamp(value):
        return max(config.MOOD_FLOOR, min(config.MOOD_CEILING, float(value)))

    def apply(self, event):
        """Apply a named event from config.MOOD_EVENTS. Returns the change actually made."""
        delta = config.MOOD_EVENTS.get(event, 0.0)
        before = self.value
        self.value = self._clamp(self.value + delta)
        return self.value - before

    def nudge(self, delta):
        before = self.value
        self.value = self._clamp(self.value + delta)
        return self.value - before

    def drift(self, hours_away):
        """While the app was closed, mood eases toward a neutral value (no punishment)."""
        step = config.MOOD_DRIFT_PER_HOUR * max(0.0, hours_away)
        target = config.MOOD_DRIFT_TARGET
        if self.value < target:
            self.value = min(target, self.value + step)
        else:
            self.value = max(target, self.value - step)

    @property
    def level(self):
        for name, floor in LEVELS:
            if self.value >= floor:
                return name
        return "sad"

    @property
    def speed_factor(self):
        return config.DROOPY_SPEED_FACTOR if self.level in ("droopy", "sad") else 1.0


class PetState:
    """Mood plus per-day counters (pats, treats, fetch boosts) and the worn accessory."""

    def __init__(self, path, today=date.today, wall_clock=time.time):
        self.path = path
        self._today = today
        self._wall = wall_clock
        self.mood = Mood()
        self.accessory = None
        self.counters = {"day": self._today().isoformat(), "pats": 0, "treats": 0, "fetch": 0}
        self.unlocked_seen = []
        self._load()

    def _load(self):
        if not os.path.isfile(self.path):
            return
        try:
            with open(self.path, encoding="utf-8") as handle:
                data = json.load(handle)
            self.mood = Mood(data.get("mood", config.MOOD_START))
            accessory = data.get("accessory")
            self.accessory = accessory if accessory in config.ACCESSORIES else None
            self.unlocked_seen = [a for a in data.get("unlocked_seen", []) if a in config.ACCESSORIES]
            saved = data.get("counters", {})
            if saved.get("day") == self.counters["day"]:
                for key in ("pats", "treats", "fetch"):
                    self.counters[key] = int(saved.get(key, 0))
            last_seen = float(data.get("last_seen", 0))
            if last_seen:
                self.mood.drift((self._wall() - last_seen) / 3600.0)
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            log.warning("Could not read pet state (%s); starting fresh", exc)
            self.mood = Mood()

    def save(self):
        data = dict(mood=round(self.mood.value, 2), accessory=self.accessory, counters=self.counters,
                    unlocked_seen=self.unlocked_seen, last_seen=self._wall())
        try:
            with open(self.path, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=1)
        except OSError as exc:
            log.warning("Could not save pet state: %s", exc)

    def delete(self):
        self.mood = Mood()
        self.accessory = None
        self.unlocked_seen = []
        self.counters = {"day": self._today().isoformat(), "pats": 0, "treats": 0, "fetch": 0}
        try:
            if os.path.isfile(self.path):
                os.remove(self.path)
        except OSError as exc:
            log.warning("Could not remove %s: %s", self.path, exc)

    # ----- daily counters --------------------------------------------------------------------
    def _roll(self):
        today = self._today().isoformat()
        if self.counters["day"] != today:
            self.counters = {"day": today, "pats": 0, "treats": 0, "fetch": 0}

    def _try(self, key, limit):
        self._roll()
        if self.counters[key] >= limit:
            return False
        self.counters[key] += 1
        return True

    def pat(self):
        """Returns True if this pat still lifts mood today."""
        if self._try("pats", config.MAX_PET_BOOSTS_PER_DAY):
            self.mood.apply("pet")
            return True
        return False

    def treats_left(self):
        self._roll()
        return max(0, config.MAX_TREATS_PER_DAY - self.counters["treats"])

    def give_treat(self):
        if self._try("treats", config.MAX_TREATS_PER_DAY):
            self.mood.apply("treat")
            return True
        return False

    def fetch_done(self):
        if self._try("fetch", config.MAX_FETCH_BOOSTS_PER_DAY):
            self.mood.apply("fetch")
            return True
        return False

    # ----- wardrobe ----------------------------------------------------------------------------
    @staticmethod
    def unlocked(best_streak):
        return [name for name, days in config.ACCESSORIES.items() if best_streak >= days]

    def new_unlocks(self, best_streak):
        """Accessories unlocked since the last time we announced one."""
        fresh = [a for a in self.unlocked(best_streak) if a not in self.unlocked_seen]
        return fresh

    def mark_seen(self, names):
        for name in names:
            if name not in self.unlocked_seen:
                self.unlocked_seen.append(name)

    def wear(self, name, best_streak):
        if name is None or name in self.unlocked(best_streak):
            self.accessory = name
            return True
        return False
