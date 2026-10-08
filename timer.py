"""Focus/break timing and mouse-based presence detection.

Only elapsed time and cursor displacement are used. No keystrokes, screen
contents, files or window titles are ever read.
"""
import logging
import math
import time
from enum import Enum

import config

log = logging.getLogger("woofie.timer")


class Phase(Enum):
    FOCUS = "FOCUS"
    BREAK = "BREAK"
    HAUL = "HAUL"


class SessionTimer:
    def __init__(self, focus_limit=None, break_limit=None, away_reset=None, haul_display=None,
                 clock=time.monotonic, max_snoozes=None):
        self.focus_limit = config.FOCUS_TIME_LIMIT_SECONDS if focus_limit is None else focus_limit
        self.break_limit = config.BREAK_TIME_LIMIT_SECONDS if break_limit is None else break_limit
        self.away_reset = config.AWAY_RESET_SECONDS if away_reset is None else away_reset
        self.haul_display = config.HAUL_DISPLAY_SECONDS if haul_display is None else haul_display
        self.max_snoozes = config.DEFAULT_MAX_SNOOZES if max_snoozes is None else max_snoozes
        self.snoozes_used = 0
        self.defer_alerts = False      # True while fullscreen / presentation mode holds alerts back
        self._events = []              # ("taken" | "skipped" | "snoozed" | "away"), drained by the app
        self._break_active = 0.0
        self._last_update = None
        self._clock = clock
        now = clock()
        self.phase = Phase.FOCUS
        self.moved_now = False
        self._anchor = None
        self._last_activity = now
        self._session_start = now
        self._break_start = None
        self._haul_start = None
        log.info("Focus session started (focus %ds, break %ds)", self.focus_limit, self.break_limit)

    def set_limits(self, focus_limit, break_limit):
        self.focus_limit, self.break_limit = focus_limit, break_limit
        log.info("Limits changed: focus %ds, break %ds", focus_limit, break_limit)

    def restart_focus(self):
        """Begin a fresh focus session now (used after the limits are changed)."""
        now = self._clock()
        self.phase = Phase.FOCUS
        self._session_start = now
        self._last_activity = now
        self._break_start = self._haul_start = None
        self.snoozes_used = 0

    # ----- V2: snooze, break quality, deferral ---------------------------------------------
    def pop_events(self):
        """Return and clear the events recorded since the last call."""
        events, self._events = self._events, []
        return events

    def snoozes_left(self):
        return max(0, self.max_snoozes - self.snoozes_used)

    def can_snooze(self):
        """Snoozing is possible while the break alert is showing and snoozes remain."""
        return self.phase is Phase.BREAK and self.snoozes_left() > 0

    def snooze(self, seconds):
        """Send the break away for `seconds`. Returns True if it was allowed."""
        if not self.can_snooze():
            return False
        now = self._clock()
        self.snoozes_used += 1
        self.phase = Phase.FOCUS
        self._session_start = now - max(0.0, self.focus_limit - seconds)
        self._last_activity = now
        self._break_start = self._haul_start = None
        self._break_active = 0.0
        self._events.append("snoozed")
        log.info("Break snoozed for %ds (%d of %d snoozes used)", seconds, self.snoozes_used, self.max_snoozes)
        return True

    def overdue_seconds(self):
        """How long the focus limit has been exceeded while alerts are deferred."""
        if self.phase is not Phase.FOCUS or self._session_start is None:
            return 0.0
        return max(0.0, self.focus_elapsed() - self.focus_limit)

    def break_taken(self):
        """True if the mouse stayed mostly still during the break (you really stepped away)."""
        return self._break_active <= config.BREAK_ACTIVE_TOLERANCE * self.break_limit

    def update(self, position):
        """Feed the current cursor position. Returns the new Phase on a change, else None."""
        now = self._clock()
        step = 0.0 if self._last_update is None else min(max(now - self._last_update, 0.0), 2.0)
        self._last_update = now
        idle = now - self._last_activity
        if (self.phase is Phase.FOCUS and self._session_start is not None
                and idle >= self.away_reset):
            log.info("No mouse movement for %.0fs, focus timer reset", idle)
            self._session_start = None
            self.snoozes_used = 0
            self._events.append("away")

        self.moved_now = self._moved(position)
        if self.moved_now:
            self._last_activity = now
            if self.phase is Phase.BREAK:
                self._break_active += max(step, 0.5)
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
        return max(0.0, self.break_limit - (self._clock() - self._break_start))

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
            if (self._session_start is not None and now - self._session_start >= self.focus_limit
                    and not self.defer_alerts):
                return self._enter(Phase.BREAK, now)
        elif self.phase is Phase.BREAK:
            if now - self._break_start >= self.break_limit:
                self._events.append("taken" if self.break_taken() else "skipped")
                return self._enter(Phase.HAUL, now)
        elif self.phase is Phase.HAUL:
            if now - self._haul_start >= self.haul_display:
                return self._enter(Phase.FOCUS, now)
        return None

    def _enter(self, phase, now):
        log.info("Phase %s -> %s", self.phase.value, phase.value)
        self.phase = phase
        if phase is Phase.BREAK:
            self._break_start = now
            self._break_active = 0.0
        elif phase is Phase.HAUL:
            self._haul_start = now
        else:
            self._session_start = None
            self._last_activity = now
            self.snoozes_used = 0
        return phase
