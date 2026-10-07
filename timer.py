"""Focus/break timing and mouse-based presence detection.

Only elapsed time and cursor displacement are used. No keystrokes, screen
contents, files or window titles are ever read.
"""
import logging
import math
import time
from enum import Enum

import config

log = logging.getLogger("aspen.timer")


class Phase(Enum):
    FOCUS = "FOCUS"
    BREAK = "BREAK"
    HAUL = "HAUL"


class SessionTimer:
    def __init__(self, clock=time.monotonic):
        self._clock = clock
        now = clock()
        self.phase = Phase.FOCUS
        self.moved_now = False
        self._anchor = None
        self._last_activity = now
        self._session_start = now
        self._break_start = None
        self._haul_start = None
        log.info("Focus session started")

    def update(self, position):
        """Feed the current cursor position. Returns the new Phase on a change, else None."""
        now = self._clock()
        idle = now - self._last_activity
        if (self.phase is Phase.FOCUS and self._session_start is not None
                and idle >= config.AWAY_RESET_SECONDS):
            log.info("No mouse movement for %.0fs, focus timer reset", idle)
            self._session_start = None

        self.moved_now = self._moved(position)
        if self.moved_now:
            self._last_activity = now
            if self._session_start is None and self.phase is Phase.FOCUS:
                self._session_start = now
                log.info("Presence detected, focus timer started")
        return self._advance(now)

    def seconds_since_move(self):
        return self._clock() - self._last_activity

    def focus_elapsed(self):
        if self._session_start is None:
            return 0.0
        return self._clock() - self._session_start

    def break_remaining(self):
        if self._break_start is None:
            return 0.0
        return max(0.0, config.BREAK_TIME_LIMIT_SECONDS - (self._clock() - self._break_start))

    def _moved(self, position):
        if self._anchor is None:
            self._anchor = position
            return False
        distance = math.hypot(position[0] - self._anchor[0], position[1] - self._anchor[1])
        if distance >= config.MOUSE_MOVE_THRESHOLD_PX:
            self._anchor = position
            return True
        return False

    def _advance(self, now):
        if self.phase is Phase.FOCUS:
            if (self._session_start is not None
                    and now - self._session_start >= config.FOCUS_TIME_LIMIT_SECONDS):
                return self._enter(Phase.BREAK, now)
        elif self.phase is Phase.BREAK:
            if now - self._break_start >= config.BREAK_TIME_LIMIT_SECONDS:
                return self._enter(Phase.HAUL, now)
        elif self.phase is Phase.HAUL:
            if now - self._haul_start >= config.HAUL_DISPLAY_SECONDS:
                return self._enter(Phase.FOCUS, now)
        return None

    def _enter(self, phase, now):
        log.info("Phase %s -> %s", self.phase.value, phase.value)
        self.phase = phase
        if phase is Phase.BREAK:
            self._break_start = now
        elif phase is Phase.HAUL:
            self._haul_start = now
        else:
            self._session_start = None
            self._last_activity = now
        return phase
