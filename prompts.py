"""Message banks for My-Woofie's speech bubbles, loaded from plain text files."""
import logging
import os
import random

log = logging.getLogger("woofie.prompts")

DEFAULT_BREAK = ["Time for a break!"]
DEFAULT_FOCUS = ["Time to get back to focus!"]


class PromptBank:
    """One message per line. Blank lines and lines starting with # are ignored.

    The file is re-read whenever it changes on disk, so edits apply without a restart.
    """

    def __init__(self, path, fallback, order="sequential"):
        self.path = path
        self.fallback = list(fallback)
        self.order = order
        self._lines = list(fallback)
        self._mtime = None
        self._index = 0
        self._last = None
        self._warned = False

    def _refresh(self):
        try:
            mtime = os.path.getmtime(self.path)
        except OSError:
            if not self._warned:
                log.warning("Prompt file missing: %s (using built-in message)", self.path)
                self._warned = True
            return
        if mtime == self._mtime:
            return
        self._mtime = mtime
        try:
            with open(self.path, encoding="utf-8") as handle:
                lines = [ln.strip() for ln in handle if ln.strip() and not ln.lstrip().startswith("#")]
        except OSError as exc:
            log.warning("Could not read %s: %s", self.path, exc)
            return
        self._lines = lines or list(self.fallback)
        log.info("Loaded %d prompts from %s", len(self._lines), os.path.basename(self.path))

    def next(self):
        self._refresh()
        lines = self._lines
        if self.order == "random" and len(lines) > 1:
            choice = random.choice([ln for ln in lines if ln != self._last])
        else:
            choice = lines[self._index % len(lines)]
            self._index += 1
        self._last = choice
        return choice
