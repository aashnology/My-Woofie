"""Small JSON store for user choices (selected avatar, mute state)."""
import json
import logging
import os

log = logging.getLogger("woofie.settings")


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

    def set(self, key, value):
        self.data[key] = value
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
