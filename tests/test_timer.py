import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from timer import Phase, SessionTimer  # noqa: E402


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def run(timer, clock, seconds, step=0.5):
    """Move the mouse steadily for the given time. Returns the phase changes seen."""
    seen, x, end = [], 0, clock.t + seconds
    while clock.t < end:
        clock.t += step
        x += 20
        phase = timer.update((x, 0))
        if phase:
            seen.append(phase)
    return seen


class SessionTimerTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.timer = SessionTimer(100, 20, 50, 10, clock=self.clock)

    def test_full_cycle(self):
        seen = run(self.timer, self.clock, 140)
        self.assertEqual(seen[:3], [Phase.BREAK, Phase.HAUL, Phase.FOCUS])

    def test_break_starts_at_focus_limit(self):
        self.assertEqual(run(self.timer, self.clock, 99), [])
        self.assertEqual(run(self.timer, self.clock, 2), [Phase.BREAK])

    def test_long_idle_resets_focus_session(self):
        run(self.timer, self.clock, 60)
        self.clock.t += 60                      # away longer than away_reset
        self.timer.update((0, 0))
        self.timer.update((500, 0))             # back at the desk
        self.assertLess(self.timer.focus_elapsed(), 5)

    def test_tiny_jitter_is_not_activity(self):
        self.timer.update((100, 100))
        self.clock.t += 1
        self.timer.update((102, 101))
        self.assertFalse(self.timer.moved_now)

    def test_changing_limits(self):
        self.timer.set_limits(30, 10)
        self.timer.restart_focus()
        self.assertEqual(run(self.timer, self.clock, 31), [Phase.BREAK])

    def test_break_remaining_counts_down(self):
        run(self.timer, self.clock, 101)
        self.assertEqual(self.timer.phase, Phase.BREAK)
        self.assertLessEqual(self.timer.break_remaining(), 20)


if __name__ == "__main__":
    unittest.main()
