"""Micro-breaks (V2): short reminders between the big breaks.

Every `interval` seconds of focus the pup suggests a 20-second eye rest, stretch, water sip or
posture check. Time-based only, nothing about what is on screen.
"""
import logging
import time

import config

log = logging.getLogger("woofie.micro")


class MicroBreaks:
    def __init__(self, interval, duration, enabled=True, kinds=None, clock=time.monotonic):
        self.interval = interval
        self.duration = duration
        self.enabled = enabled
        self.kinds = tuple(kinds or config.MICRO_KINDS)
        self._clock = clock
        self._next_at = interval
        self._last_elapsed = 0.0
        self._count = 0
        self.kind = None
        self._started = None

    # ----- configuration -------------------------------------------------------------------------
    def configure(self, interval, duration, enabled):
        self.interval, self.duration, self.enabled = interval, duration, enabled
        self.reset()

    def reset(self):
        """Start counting from zero again (after a real break, snooze or away period)."""
        self._next_at = self.interval
        self._last_elapsed = 0.0
        if self.kind is not None:
            self.kind = None
            self._started = None

    # ----- state -------------------------------------------------------------------------------
    @property
    def active(self):
        return self.kind is not None

    def remaining(self):
        if not self.active:
            return 0.0
        return max(0.0, self.duration - (self._clock() - self._started))

    def due(self, focus_elapsed, focus_limit, idle_seconds, deferred=False, in_focus=True):
        """Should a micro-break start now? Does not change any state."""
        if not self.enabled or self.active or deferred or not in_focus:
            return False
        if idle_seconds >= config.MICRO_PRESENCE_SECONDS:
            return False
        quiet = min(config.MICRO_QUIET_BEFORE_BREAK_SECONDS, focus_limit * 0.25)
        if focus_limit - focus_elapsed <= quiet:
            return False
        return focus_elapsed >= self._next_at

    def update(self, focus_elapsed, focus_limit, idle_seconds, deferred=False, in_focus=True):
        """Call every tick. Returns the new micro-break kind when one starts, else None."""
        if focus_elapsed < self._last_elapsed - 1:      # the focus session restarted
            self._next_at = self.interval
            if self.active:
                self.kind, self._started = None, None
        self._last_elapsed = focus_elapsed
        if not self.due(focus_elapsed, focus_limit, idle_seconds, deferred, in_focus):
            return None
        self.kind = self.kinds[self._count % len(self.kinds)]
        self._count += 1
        self._started = self._clock()
        self._next_at = focus_elapsed + self.interval
        log.info("Micro-break started: %s (%ds)", self.kind, self.duration)
        return self.kind

    def finished(self):
        """True once the countdown has run out."""
        return self.active and self.remaining() <= 0.0

    def end(self):
        """Close the current micro-break. Returns (kind, seconds it was open)."""
        if not self.active:
            return None, 0.0
        kind, spent = self.kind, self._clock() - self._started
        self.kind, self._started = None, None
        return kind, spent
