import os
import sys
import tempfile
import unittest
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402
from mood import Mood, PetState  # noqa: E402
from stats import Stats  # noqa: E402


class StatsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "stats.json")
        self.day = date(2026, 10, 8)
        self.stats = Stats(self.path, today=lambda: self.day)

    def tearDown(self):
        self.tmp.cleanup()

    def record_day(self, offset, taken, skipped):
        self.day = date(2026, 10, 8) - timedelta(days=offset)
        self.stats.record("taken", taken) if taken else self.stats.touch()
        if skipped:
            self.stats.record("skipped", skipped)
        self.day = date(2026, 10, 8)

    def test_round_trip_on_disk(self):
        self.stats.record("taken", 2)
        self.stats.add_focus_seconds(600)
        self.stats.save()
        again = Stats(self.path, today=lambda: self.day)
        self.assertEqual(again.day()["taken"], 2)
        self.assertEqual(again.day()["focus_seconds"], 600)

    def test_disabled_stats_record_nothing(self):
        self.stats.enabled = False
        self.stats.record("taken")
        self.stats.add_focus_seconds(60)
        self.assertEqual(self.stats.day()["taken"], 0)
        self.assertFalse(os.path.exists(self.path))

    def test_delete_all_removes_the_file(self):
        self.stats.record("taken")
        self.assertTrue(os.path.exists(self.path))
        self.stats.delete_all()
        self.assertFalse(os.path.exists(self.path))
        self.assertEqual(self.stats.day()["taken"], 0)

    def test_unknown_counter_is_rejected(self):
        with self.assertRaises(ValueError):
            self.stats.record("keystrokes")

    def test_streak_counts_consecutive_healthy_days(self):
        for offset in (2, 1, 0):
            self.record_day(offset, 1, 0)
        self.assertEqual(self.stats.streak(), 3)

    def test_unhealthy_day_breaks_the_streak(self):
        self.record_day(2, 1, 0)
        self.record_day(1, 0, 2)
        self.record_day(0, 1, 0)
        self.assertEqual(self.stats.streak(), 1)
        self.assertEqual(self.stats.best_streak(), 1)

    def test_one_missing_day_keeps_the_streak(self):
        self.record_day(3, 1, 0)
        self.record_day(1, 1, 0)
        self.record_day(0, 1, 0)
        self.assertEqual(self.stats.streak(), 3)

    def test_two_missing_days_reset_it(self):
        self.record_day(4, 1, 0)
        self.record_day(0, 1, 0)
        self.assertEqual(self.stats.streak(), 1)

    def test_old_streak_expires(self):
        self.record_day(6, 1, 0)
        self.assertEqual(self.stats.streak(), 0)
        self.assertEqual(self.stats.best_streak(), 1)

    def test_week_summary_has_seven_days(self):
        self.record_day(0, 2, 1)
        summary = self.stats.week_summary()
        self.assertEqual(len(summary["days"]), 7)
        self.assertEqual(summary["totals"]["taken"], 2)
        self.assertAlmostEqual(summary["totals"]["taken_share"], 2 / 3)

    def test_corrupt_file_is_ignored(self):
        with open(self.path, "w") as handle:
            handle.write("{nope")
        self.assertEqual(Stats(self.path).week_summary()["totals"]["taken"], 0)

    def test_stats_file_holds_only_counters(self):
        self.stats.record("taken")
        with open(self.path) as handle:
            text = handle.read()
        self.assertNotIn("title", text.lower())
        self.assertNotIn("key", text.lower())


class MoodTests(unittest.TestCase):
    def test_events_move_mood_and_clamp(self):
        mood = Mood(95)
        mood.apply("break_taken")
        self.assertEqual(mood.value, 100)
        mood = Mood(5)
        mood.apply("break_skipped")
        self.assertEqual(mood.value, 0)

    def test_levels_and_speed(self):
        self.assertEqual(Mood(90).level, "ecstatic")
        self.assertEqual(Mood(70).level, "happy")
        self.assertEqual(Mood(40).level, "okay")
        self.assertEqual(Mood(20).level, "droopy")
        self.assertEqual(Mood(5).level, "sad")
        self.assertEqual(Mood(70).speed_factor, 1.0)
        self.assertLess(Mood(5).speed_factor, 1.0)

    def test_mood_drifts_toward_neutral_while_away(self):
        low, high = Mood(10), Mood(100)
        low.drift(10)
        high.drift(10)
        self.assertGreater(low.value, 10)
        self.assertLess(high.value, 100)
        low.drift(1000)
        self.assertEqual(low.value, config.MOOD_DRIFT_TARGET)


class PetStateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "pet.json")
        self.day = date(2026, 10, 8)
        self.clock = 1_000_000.0
        self.state = PetState(self.path, today=lambda: self.day, wall_clock=lambda: self.clock)

    def tearDown(self):
        self.tmp.cleanup()

    def test_treat_limit_per_day(self):
        results = [self.state.give_treat() for _ in range(config.MAX_TREATS_PER_DAY + 2)]
        self.assertEqual(results.count(True), config.MAX_TREATS_PER_DAY)
        self.assertEqual(self.state.treats_left(), 0)
        self.day += timedelta(days=1)
        self.assertEqual(self.state.treats_left(), config.MAX_TREATS_PER_DAY)

    def test_pat_boost_is_capped(self):
        start = self.state.mood.value
        for _ in range(config.MAX_PET_BOOSTS_PER_DAY + 10):
            self.state.pat()
        self.assertAlmostEqual(self.state.mood.value - start, config.MAX_PET_BOOSTS_PER_DAY * 1.0)

    def test_accessories_unlock_by_streak(self):
        self.assertEqual(self.state.unlocked(0), [])
        self.assertEqual(self.state.unlocked(3), ["party_hat", "flower"])
        self.assertFalse(self.state.wear("crown", 3))
        self.assertTrue(self.state.wear("flower", 3))
        self.assertTrue(self.state.wear(None, 0))

    def test_unlock_announcements_happen_once(self):
        fresh = self.state.new_unlocks(3)
        self.assertEqual(fresh, ["party_hat", "flower"])
        self.state.mark_seen(fresh)
        self.assertEqual(self.state.new_unlocks(3), [])
        self.assertEqual(self.state.new_unlocks(5), ["beanie"])

    def test_saves_and_restores(self):
        self.state.mood.value = 33
        self.state.accessory = "flower"
        self.state.save()
        again = PetState(self.path, today=lambda: self.day, wall_clock=lambda: self.clock)
        self.assertEqual(again.mood.value, 33)
        self.assertEqual(again.accessory, "flower")

    def test_delete_resets_everything(self):
        self.state.mood.value = 10
        self.state.save()
        self.state.delete()
        self.assertEqual(self.state.mood.value, config.MOOD_START)
        self.assertFalse(os.path.exists(self.path))


if __name__ == "__main__":
    unittest.main()
