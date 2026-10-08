import math
import os
import sys
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402
import daypart  # noqa: E402
from pet import Pet, State  # noqa: E402


def distance_to(pet, cursor):
    return math.hypot(pet.x + pet.w / 2 - cursor[0], pet.y + pet.h / 2 - cursor[1])


class ChaseTests(unittest.TestCase):
    CURSOR = (1800, 900)

    def make(self):
        pet = Pet((0, 0, 1920, 1080), (53, 47))
        pet.x, pet.y = 0.0, 1033.0
        return pet

    def test_reaches_a_far_cursor_after_the_mouse_stops(self):
        """The old behaviour gave up 3 seconds after the last mouse movement and stopped midway."""
        pet = self.make()
        for i in range(60):                                   # about 2 s of mouse movement
            pet.update(self.CURSOR, True, i * 0.033)
        self.assertGreater(distance_to(pet, self.CURSOR), 500)
        for i in range(60, 2400):                             # mouse is now still
            pet.update(self.CURSOR, False, i * 0.033)
            if distance_to(pet, self.CURSOR) <= config.CHASE_STOP_DISTANCE_PX:
                break
        self.assertLessEqual(distance_to(pet, self.CURSOR), config.CHASE_STOP_DISTANCE_PX)
        self.assertLess(i, 1500)                              # within about 50 seconds, and normally far less

    def test_crosses_the_screen_in_a_reasonable_time(self):
        pet = self.make()
        frames = 0
        while distance_to(pet, self.CURSOR) > config.CHASE_STOP_DISTANCE_PX and frames < 3000:
            pet.update(self.CURSOR, True, frames * 0.033)
            frames += 1
        self.assertLess(frames * 0.033, 20)

    def test_roams_again_once_he_has_caught_up(self):
        pet = self.make()
        for i in range(3000):
            pet.update(self.CURSOR, i < 30, i * 0.033)
        self.assertEqual(pet.state, State.ROAM_STATE)

    def test_a_slow_timer_does_not_make_him_slower(self):
        fast, slow = self.make(), self.make()
        for i in range(300):
            fast.update(self.CURSOR, True, i * 0.033)
        for i in range(100):                                  # timer fires three times less often
            slow.update(self.CURSOR, True, i * 0.099)
        self.assertAlmostEqual(distance_to(fast, self.CURSOR), distance_to(slow, self.CURSOR), delta=60)

    def test_every_avatar_uses_the_same_following_logic(self):
        # The pet logic has no per-dog code; only the sprite size is passed in.
        for size in ((53, 47), (40, 40)):
            pet = Pet((0, 0, 1000, 600), size)
            closest = float("inf")
            for i in range(900):
                pet.update((900, 300), i < 20, i * 0.033)
                closest = min(closest, distance_to(pet, (900, 300)))
            self.assertLessEqual(closest, config.CHASE_STOP_DISTANCE_PX, size)


class NightTests(unittest.TestCase):
    def tearDown(self):
        daypart.set_hour_override(None)

    def test_hour_override(self):
        daypart.set_hour_override(1)
        self.assertEqual(daypart.now().hour, 1)
        daypart.set_hour_override(None)
        self.assertEqual(daypart.now().hour, datetime.now().hour)

    def test_one_in_the_morning_is_night_and_late(self):
        rhythm = daypart.DayRhythm()
        at_one = datetime(2026, 10, 9, 1, 22)
        self.assertTrue(rhythm.is_night(at_one))
        self.assertTrue(rhythm.late(at_one))
        self.assertTrue(rhythm.bedtime_due(at_one, None))
        self.assertTrue(rhythm.should_sleep(at_one, config.SLEEP_AFTER_IDLE_SECONDS))


if __name__ == "__main__":
    unittest.main()
