import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from timer import Phase, SessionTimer  # noqa: E402


class FakeClock:
    t = 0.0

    def __call__(self):
        return self.t


def run(timer, clock, seconds, moving=True, step=0.5):
    seen, x, end = [], 0, clock.t + seconds
    while clock.t < end:
        clock.t += step
        if moving:
            x += 20
        phase = timer.update((x, 0))
        if phase:
            seen.append(phase)
    return seen


class SnoozeTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.timer = SessionTimer(100, 20, 50, 10, clock=self.clock, max_snoozes=2)

    def test_snooze_only_during_break(self):
        self.assertFalse(self.timer.snooze(30))
        run(self.timer, self.clock, 101)
        self.assertEqual(self.timer.phase, Phase.BREAK)
        self.assertTrue(self.timer.snooze(30))
        self.assertEqual(self.timer.phase, Phase.FOCUS)

    def test_snooze_brings_the_break_back_after_the_snooze_time(self):
        run(self.timer, self.clock, 101)
        self.timer.snooze(30)
        self.assertEqual(run(self.timer, self.clock, 28), [])
        self.assertEqual(run(self.timer, self.clock, 4), [Phase.BREAK])

    def test_snoozes_are_limited_per_cycle(self):
        run(self.timer, self.clock, 101)
        self.assertTrue(self.timer.snooze(10))
        run(self.timer, self.clock, 12)
        self.assertTrue(self.timer.snooze(10))
        run(self.timer, self.clock, 12)
        self.assertEqual(self.timer.phase, Phase.BREAK)
        self.assertFalse(self.timer.can_snooze())
        self.assertFalse(self.timer.snooze(10))

    def test_snoozes_reset_after_a_full_break_cycle(self):
        run(self.timer, self.clock, 101)
        self.timer.snooze(10)
        run(self.timer, self.clock, 12)
        run(self.timer, self.clock, 45)              # break, haul, back to focus
        self.assertEqual(self.timer.phase, Phase.FOCUS)
        self.assertEqual(self.timer.snoozes_left(), 2)

    def test_snooze_event_is_recorded(self):
        run(self.timer, self.clock, 101)
        self.timer.pop_events()
        self.timer.snooze(10)
        self.assertEqual(self.timer.pop_events(), ["snoozed"])


class BreakQualityTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.timer = SessionTimer(100, 20, 50, 10, clock=self.clock)

    def test_still_mouse_means_break_taken(self):
        run(self.timer, self.clock, 101)
        run(self.timer, self.clock, 21, moving=False)
        self.assertEqual(self.timer.pop_events(), ["taken"])

    def test_busy_mouse_means_break_skipped(self):
        run(self.timer, self.clock, 101)
        run(self.timer, self.clock, 21, moving=True)
        self.assertEqual(self.timer.pop_events(), ["skipped"])

    def test_a_little_movement_is_still_a_taken_break(self):
        run(self.timer, self.clock, 101)
        run(self.timer, self.clock, 3, moving=True)      # a few seconds, under 25% of a 20 s break
        run(self.timer, self.clock, 18, moving=False)
        self.assertEqual(self.timer.pop_events(), ["taken"])

    def test_going_away_is_recorded(self):
        run(self.timer, self.clock, 30)
        run(self.timer, self.clock, 55, moving=False)
        self.assertIn("away", self.timer.pop_events())


class DeferralTests(unittest.TestCase):
    def test_alerts_wait_while_deferred_then_fire(self):
        clock = FakeClock()
        timer = SessionTimer(100, 20, 50, 10, clock=clock)
        timer.defer_alerts = True
        self.assertEqual(run(timer, clock, 130), [])
        self.assertEqual(timer.phase, Phase.FOCUS)
        self.assertGreater(timer.overdue_seconds(), 25)
        timer.defer_alerts = False
        self.assertEqual(run(timer, clock, 1), [Phase.BREAK])


if __name__ == "__main__":
    unittest.main()
