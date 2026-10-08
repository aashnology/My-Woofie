import os
import sys
import tempfile
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import autostart  # noqa: E402
import config  # noqa: E402
import daypart  # noqa: E402
from fullscreen import covers  # noqa: E402
from microbreak import MicroBreaks  # noqa: E402
from tips import TipBank, parse_tips  # noqa: E402
from toys import Ball, velocity_from_samples  # noqa: E402


class FakeClock:
    t = 0.0

    def __call__(self):
        return self.t


class MicroBreakTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.micro = MicroBreaks(100, 20, clock=self.clock)

    def test_starts_after_the_interval_of_focus(self):
        self.assertIsNone(self.micro.update(50, 1000, 0))
        self.assertEqual(self.micro.update(100, 1000, 0), "eyes")
        self.assertTrue(self.micro.active)

    def test_kinds_rotate(self):
        kinds = []
        for elapsed in (100, 300, 500, 700, 900):
            kinds.append(self.micro.update(elapsed, 5000, 0))
            self.micro.end()
        self.assertEqual(kinds, ["eyes", "stretch", "water", "posture", "eyes"])

    def test_not_close_to_a_big_break(self):
        self.assertIsNone(self.micro.update(100, 120, 0))

    def test_not_when_the_user_is_away_or_deferred(self):
        self.assertIsNone(self.micro.update(100, 1000, config.MICRO_PRESENCE_SECONDS + 1))
        self.assertIsNone(self.micro.update(101, 1000, 0, deferred=True))
        self.assertEqual(self.micro.update(102, 1000, 0), "eyes")

    def test_countdown_and_finish(self):
        self.micro.update(100, 1000, 0)
        self.clock.t = 10
        self.assertAlmostEqual(self.micro.remaining(), 10)
        self.assertFalse(self.micro.finished())
        self.clock.t = 21
        self.assertTrue(self.micro.finished())

    def test_disabled_never_starts(self):
        self.micro.enabled = False
        self.assertIsNone(self.micro.update(500, 5000, 0))

    def test_new_session_restarts_the_count(self):
        self.micro.update(100, 1000, 0)
        self.micro.end()
        self.micro.update(5, 1000, 0)               # focus timer restarted
        self.assertIsNone(self.micro.update(50, 1000, 0))
        self.assertEqual(self.micro.update(105, 1000, 0), "stretch")


class DayRhythmTests(unittest.TestCase):
    def setUp(self):
        self.rhythm = daypart.DayRhythm(22, 6, 23)

    def test_window_wraps_past_midnight(self):
        self.assertTrue(daypart.hour_in_window(23, 22, 6))
        self.assertTrue(daypart.hour_in_window(3, 22, 6))
        self.assertFalse(daypart.hour_in_window(12, 22, 6))
        self.assertFalse(daypart.hour_in_window(5, 5, 5))

    def test_sleeps_only_at_night_and_when_idle(self):
        night, noon = datetime(2026, 10, 8, 23, 30), datetime(2026, 10, 8, 12, 0)
        self.assertTrue(self.rhythm.should_sleep(night, config.SLEEP_AFTER_IDLE_SECONDS))
        self.assertFalse(self.rhythm.should_sleep(night, 10))
        self.assertFalse(self.rhythm.should_sleep(noon, 9999))

    def test_morning_greeting_once_a_day(self):
        morning = datetime(2026, 10, 8, 7, 0)
        self.assertTrue(self.rhythm.morning_due(morning, None))
        self.assertFalse(self.rhythm.morning_due(morning, "2026-10-08"))
        self.assertFalse(self.rhythm.morning_due(datetime(2026, 10, 8, 15, 0), None))

    def test_bedtime_nudge_repeats_hourly(self):
        late = datetime(2026, 10, 8, 23, 30)
        self.assertTrue(self.rhythm.bedtime_due(late, None))
        self.assertFalse(self.rhythm.bedtime_due(datetime(2026, 10, 8, 23, 50), late))
        self.assertTrue(self.rhythm.bedtime_due(datetime(2026, 10, 9, 0, 31), late))
        self.assertFalse(self.rhythm.bedtime_due(datetime(2026, 10, 8, 20, 0), None))

    def test_disabled_does_nothing(self):
        self.rhythm.enabled = False
        self.assertFalse(self.rhythm.bedtime_due(datetime(2026, 10, 8, 23, 30), None))
        self.assertFalse(self.rhythm.should_sleep(datetime(2026, 10, 8, 23, 30), 9999))


class TipTests(unittest.TestCase):
    def test_parse_ignores_comments_and_bad_lines(self):
        tips = parse_tips(["# hi", "", "eyes|Look away", "nonsense", "bogus|x", "water|Drink"])
        self.assertEqual(tips, {"eyes": ["Look away"], "water": ["Drink"]})

    def test_missing_file_uses_built_in_tips(self):
        bank = TipBank(os.path.join(tempfile.gettempdir(), "no-such-tips.txt"))
        title, text = bank.next("stretch")
        self.assertEqual(title, "STRETCH")
        self.assertTrue(text)

    def test_rotation_and_any_next(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "t.txt")
            with open(path, "w") as handle:
                handle.write("eyes|A\neyes|B\nwater|C\n")
            bank = TipBank(path)
            self.assertEqual([bank.next("eyes")[1] for _ in range(3)], ["A", "B", "A"])
            first, second = bank.any_next(("eyes", "water")), bank.any_next(("eyes", "water"))
            self.assertEqual({first[0], second[0]}, {"EYE REST", "WATER"})

    def test_shipped_tips_file_is_valid(self):
        with open(config.BREAK_TIPS_FILE, encoding="utf-8") as handle:
            tips = parse_tips(handle)
        self.assertGreaterEqual(len(tips), 6)


class BallTests(unittest.TestCase):
    RECT = (0, 0, 500, 300)

    def test_thrown_ball_slows_and_stops(self):
        ball = Ball(100, 100)
        ball.release(10, 0)
        for _ in range(600):
            ball.update(self.RECT)
        self.assertEqual(ball.speed, 0.0)
        self.assertTrue(ball.in_play)

    def test_ball_bounces_off_the_edge(self):
        ball = Ball(470, 100)
        ball.release(20, 0)
        for _ in range(5):
            ball.update(self.RECT)
        self.assertLessEqual(ball.x, 500 - ball.size)
        self.assertLess(ball.vx, 0)

    def test_held_or_carried_ball_does_not_move_by_itself(self):
        ball = Ball(50, 50)
        ball.grab()
        ball.vx = 9
        ball.update(self.RECT)
        self.assertEqual(ball.x, 50)

    def test_throw_velocity_from_drag(self):
        vx, vy = velocity_from_samples([(0.0, 0, 0), (0.1, 100, 0)])
        self.assertGreater(vx, 0)
        self.assertEqual(vy, 0)
        fast, _ = velocity_from_samples([(0.0, 0, 0), (0.001, 5000, 0)])
        self.assertLessEqual(fast, 28.0001)
        self.assertEqual(velocity_from_samples([(0.0, 0, 0)]), (0.0, 0.0))


class AutostartTests(unittest.TestCase):
    CMD = ["/usr/bin/python3", "/path with space/main.py"]

    def test_linux_round_trip(self):
        with tempfile.TemporaryDirectory() as home:
            self.assertFalse(autostart.is_enabled("linux", home))
            self.assertTrue(autostart.set_enabled(True, "linux", home, self.CMD))
            self.assertTrue(autostart.is_enabled("linux", home))
            with open(os.path.join(home, ".config", "autostart", "my-woofie.desktop")) as handle:
                text = handle.read()
            self.assertIn('"/path with space/main.py"', text)
            self.assertTrue(autostart.set_enabled(False, "linux", home, self.CMD))
            self.assertFalse(autostart.is_enabled("linux", home))

    def test_mac_round_trip(self):
        with tempfile.TemporaryDirectory() as home:
            self.assertTrue(autostart.set_enabled(True, "darwin", home, self.CMD))
            self.assertTrue(autostart.is_enabled("darwin", home))
            with open(os.path.join(home, "Library", "LaunchAgents", autostart.MAC_LABEL + ".plist")) as handle:
                plist = handle.read()
            self.assertIn("<key>RunAtLoad</key>", plist)
            self.assertIn("/path with space/main.py", plist)
            autostart.set_enabled(False, "darwin", home, self.CMD)
            self.assertFalse(autostart.is_enabled("darwin", home))

    def test_disabling_when_not_enabled_is_fine(self):
        with tempfile.TemporaryDirectory() as home:
            self.assertTrue(autostart.set_enabled(False, "linux", home, self.CMD))


class FullscreenTests(unittest.TestCase):
    def test_covers(self):
        monitor = (0, 0, 1920, 1080)
        self.assertTrue(covers((0, 0, 1920, 1080), monitor))
        self.assertTrue(covers((-8, -8, 1928, 1088), monitor))
        self.assertFalse(covers((0, 0, 1920, 1040), monitor))      # maximized with taskbar
        self.assertFalse(covers((100, 100, 900, 700), monitor))


if __name__ == "__main__":
    unittest.main()
