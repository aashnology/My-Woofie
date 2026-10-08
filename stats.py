"""Local-only break statistics (V2).

Stores one small record per day in stats.json next to settings.json: how many breaks were taken
or skipped, snoozes, micro-breaks, and minutes of mouse-active focus time. Nothing here ever
leaves the computer, and `delete_all()` removes every trace.
"""
import json
import logging
import os
from datetime import date, datetime, timedelta

import config

log = logging.getLogger("woofie.stats")

COUNTERS = ("taken", "skipped", "snoozed", "away", "micro_done", "micro_skipped",
            "pets", "treats", "fetches")


def _blank():
    record = {name: 0 for name in COUNTERS}
    record["focus_seconds"] = 0
    return record


class Stats:
    def __init__(self, path, enabled=True, today=date.today):
        self.path = path
        self.enabled = enabled
        self._today = today
        self.days = {}
        self._dirty = False
        self._load()

    # ----- storage -----------------------------------------------------------------------
    def _load(self):
        if not os.path.isfile(self.path):
            return
        try:
            with open(self.path, encoding="utf-8") as handle:
                loaded = json.load(handle)
            days = loaded.get("days", {}) if isinstance(loaded, dict) else {}
            for key, record in days.items():
                date.fromisoformat(key)
                merged = _blank()
                merged.update({k: int(v) for k, v in record.items() if k in merged})
                self.days[key] = merged
        except (OSError, ValueError, AttributeError, TypeError) as exc:
            log.warning("Could not read stats (%s); starting fresh", exc)
            self.days = {}

    def save(self):
        if not self._dirty:
            return
        self._prune()
        try:
            with open(self.path, "w", encoding="utf-8") as handle:
                json.dump({"days": self.days}, handle, indent=1, sort_keys=True)
            self._dirty = False
        except OSError as exc:
            log.warning("Could not save stats: %s", exc)

    def _prune(self):
        cutoff = (self._today() - timedelta(days=config.STATS_KEEP_DAYS)).isoformat()
        for key in [k for k in self.days if k < cutoff]:
            del self.days[key]

    def delete_all(self):
        """Forget everything and remove stats.json from disk."""
        self.days = {}
        self._dirty = False
        try:
            if os.path.isfile(self.path):
                os.remove(self.path)
        except OSError as exc:
            log.warning("Could not remove %s: %s", self.path, exc)
        log.info("All statistics deleted")

    # ----- recording ---------------------------------------------------------------------
    def _record(self, day=None):
        key = (day or self._today()).isoformat()
        if key not in self.days:
            self.days[key] = _blank()
        return self.days[key]

    def touch(self):
        """Mark today as a day the companion was running (so quiet days still count)."""
        if self.enabled:
            self._record()
            self._dirty = True

    def record(self, name, amount=1):
        if not self.enabled:
            return
        if name not in COUNTERS:
            raise ValueError(f"unknown statistic: {name}")
        self._record()[name] += amount
        self._dirty = True
        self.save()

    def add_focus_seconds(self, seconds):
        if self.enabled and seconds > 0:
            record = self._record()
            record["focus_seconds"] += int(round(seconds))
            self._dirty = True

    # ----- reading -----------------------------------------------------------------------
    def day(self, day=None):
        return dict(self.days.get((day or self._today()).isoformat(), _blank()))

    def last_days(self, count=7):
        """Oldest first, always `count` entries (days without data are blank)."""
        today = self._today()
        out = []
        for back in range(count - 1, -1, -1):
            d = today - timedelta(days=back)
            out.append((d, self.day(d)))
        return out

    def week_summary(self):
        days = self.last_days(7)
        totals = _blank()
        for _, record in days:
            for key, value in record.items():
                totals[key] += value
        total_breaks = totals["taken"] + totals["skipped"]
        totals["taken_share"] = (totals["taken"] / total_breaks) if total_breaks else None
        return dict(days=days, totals=totals, streak=self.streak(), best=self.best_streak())

    @staticmethod
    def _healthy(record):
        return record["skipped"] <= record["taken"]

    def _streak_runs(self):
        """Lengths of every run of healthy recorded days, with the date each run last touched."""
        runs, length, previous = [], 0, None
        for key in sorted(self.days):
            day = date.fromisoformat(key)
            healthy = self._healthy(self.days[key])
            if previous is not None and (day - previous).days > config.STREAK_GAP_DAYS:
                if length:
                    runs.append((length, previous))
                length = 0
            if healthy:
                length += 1
            else:
                if length:
                    runs.append((length, previous))
                length = 0
            previous = day
        if length:
            runs.append((length, previous))
        return runs

    def streak(self):
        """Consecutive healthy days up to today. A day is healthy when skipped <= taken."""
        if not self.days:
            return 0
        latest = max(self.days)
        last = date.fromisoformat(latest)
        if (self._today() - last).days > config.STREAK_GAP_DAYS:
            return 0
        if not self._healthy(self.days[latest]):
            return 0
        runs = self._streak_runs()
        return runs[-1][0] if runs and runs[-1][1] == last else 0

    def best_streak(self):
        runs = self._streak_runs()
        return max([length for length, _ in runs], default=0)

    def summary_text(self):
        """Plain-text version for `python main.py --stats`."""
        summary = self.week_summary()
        lines = ["My-Woofie, last 7 days (stored only on this computer)", ""]
        for day, record in summary["days"]:
            minutes = record["focus_seconds"] // 60
            lines.append(f"{day.isoformat()}  breaks taken {record['taken']}  skipped {record['skipped']}"
                         f"  snoozed {record['snoozed']}  focus {minutes} min")
        totals = summary["totals"]
        share = "n/a" if totals["taken_share"] is None else f"{round(totals['taken_share'] * 100)}%"
        lines += ["", f"Breaks taken: {totals['taken']} of {totals['taken'] + totals['skipped']} ({share})",
                  f"Current streak: {summary['streak']} day(s), best: {summary['best']}"]
        return "\n".join(lines)


def format_day(day):
    """Short weekday label such as MON."""
    if isinstance(day, datetime):
        day = day.date()
    return day.strftime("%a").upper()[:3]
