"""Small JSON store for user choices (selected avatar, mute state)."""
import json
import logging
import os

import config

log = logging.getLogger("woofie.settings")

# Every user-changeable option with its default. The Settings window edits exactly these keys.
DEFAULTS = dict(
    focus_minutes=config.DEFAULT_FOCUS_MINUTES, break_minutes=config.DEFAULT_BREAK_MINUTES,
    snooze_minutes=config.DEFAULT_SNOOZE_MINUTES, max_snoozes=config.DEFAULT_MAX_SNOOZES,
    micro_enabled=config.MICRO_ENABLED, micro_interval_minutes=config.DEFAULT_MICRO_INTERVAL_MINUTES,
    micro_seconds=config.DEFAULT_MICRO_SECONDS,
    pet_speed=3, roam_all_monitors=True,
    night_sleep=True, sleep_start=config.DEFAULT_SLEEP_START_HOUR, sleep_end=config.DEFAULT_SLEEP_END_HOUR,
    bedtime_hour=config.DEFAULT_BEDTIME_HOUR,
    volume=80, muted=False, fullscreen_aware=True, hud_always=config.HUD_ALWAYS_VISIBLE,
    stats_enabled=True,
)

# Settings "speed" slider (1..5) -> multiplier on config.PET_SPEED
SPEED_FACTORS = {1: 0.5, 2: 0.75, 3: 1.0, 4: 1.35, 5: 1.75}


class Settings:
    def __init__(self, path):
        self.path = path
        self.data = {}
        self.existed = os.path.isfile(path)
        if self.existed:
            try:
                with open(path, encoding="utf-8") as handle:
                    loaded = json.load(handle)
                if isinstance(loaded, dict):
                    self.data = loaded
            except (OSError, ValueError) as exc:
                log.warning("Could not read settings (%s); starting fresh", exc)

    def get(self, key, default=None):
        return self.data.get(key, default)

    def pref(self, key):
        """A saved choice, or its default from DEFAULTS."""
        return self.data.get(key, DEFAULTS[key])

    def speed_factor(self):
        return SPEED_FACTORS.get(int(self.pref("pet_speed")), 1.0)

    def set(self, key, value):
        self.data[key] = value
        self.save()

    def update_many(self, values):
        """Set several keys and save once."""
        self.data.update(values)
        self.save()

    def clear(self):
        """Forget every saved choice."""
        self.data = {}
        self.save()

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as handle:
                json.dump(self.data, handle, indent=2)
        except OSError as exc:
            log.warning("Could not save settings: %s", exc)
