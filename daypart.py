"""Time-of-day behaviour (V2): night-time naps, a morning stretch and a gentle bedtime nudge.

Only the computer's clock is used.
"""
from datetime import datetime

import config


def hour_in_window(hour, start, end):
    """True if `hour` lies in [start, end), where the window may wrap past midnight (22 -> 6)."""
    if start == end:
        return False
    if start < end:
        return start <= hour < end
    return hour >= start or hour < end


class DayRhythm:
    def __init__(self, sleep_start=None, sleep_end=None, bedtime=None, enabled=True):
        self.sleep_start = config.DEFAULT_SLEEP_START_HOUR if sleep_start is None else sleep_start
        self.sleep_end = config.DEFAULT_SLEEP_END_HOUR if sleep_end is None else sleep_end
        self.bedtime = config.DEFAULT_BEDTIME_HOUR if bedtime is None else bedtime
        self.enabled = enabled

    def is_night(self, now):
        return hour_in_window(now.hour, self.sleep_start, self.sleep_end)

    def should_sleep(self, now, idle_seconds):
        """He naps at night once the mouse has been still for a couple of minutes."""
        return (self.enabled and self.is_night(now)
                and idle_seconds >= config.SLEEP_AFTER_IDLE_SECONDS)

    def is_morning(self, now):
        return config.MORNING_START_HOUR <= now.hour < config.MORNING_END_HOUR

    def morning_due(self, now, last_greeting_day):
        """One stretch and greeting per day, on the first activity in the morning."""
        return (self.enabled and self.is_morning(now)
                and last_greeting_day != now.date().isoformat())

    def late(self, now):
        """True between bedtime and the end of the sleep window."""
        return self.enabled and hour_in_window(now.hour, self.bedtime, self.sleep_end)

    def bedtime_due(self, now, last_nudge):
        """A nudge when it is late, then again every BEDTIME_REPEAT_MINUTES while still active."""
        if not self.late(now):
            return False
        if last_nudge is None:
            return True
        return (now - last_nudge).total_seconds() >= config.BEDTIME_REPEAT_MINUTES * 60


BEDTIME_MESSAGES = (
    "It's getting late. Time to wrap up and get some sleep.",
    "Still here? Rest helps you do better work tomorrow.",
    "My eyes are heavy, and yours must be too. Bedtime soon?",
)
MORNING_MESSAGES = (
    "Good morning! A little stretch before we start?",
    "Morning! Let's make it a good day.",
)


def pick(messages, count):
    return messages[count % len(messages)]


def parse_clock(value, fallback):
    """Accepts 'HH' or 'HH:MM' strings or ints; returns an hour 0..23."""
    try:
        return int(str(value).split(":")[0]) % 24
    except (TypeError, ValueError):
        return fallback


_hour_override = None


def set_hour_override(hour):
    """Pretend it is this hour (0-23). For testing night behaviour: python main.py --hour 1"""
    global _hour_override
    _hour_override = None if hour is None else int(hour) % 24


def now():
    """The current local time, or today at the overridden hour."""
    current = datetime.now()
    if _hour_override is not None:
        return current.replace(hour=_hour_override)
    return current
