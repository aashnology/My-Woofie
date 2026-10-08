import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pet import Pet, State  # noqa: E402
from timer import Phase  # noqa: E402
from toys import Ball  # noqa: E402


def make_pet():
    return Pet((0, 0, 1000, 600), (40, 40))


def center(pet):
    return pet.x + pet.w / 2, pet.y + pet.h / 2


class SleepAndStretchTests(unittest.TestCase):
    def test_sleep_and_wake(self):
        pet = make_pet()
        pet.sleep()
        self.assertEqual(pet.state, State.SLEEP_STATE)
        x, y = pet.x, pet.y
        for i in range(50):
            pet.update((900, 500), True, i * 0.033)
        self.assertEqual((pet.x, pet.y), (x, y))
        self.assertEqual(pet.animation(1.0), "sleep")
        pet.wake()
        self.assertEqual(pet.state, State.ROAM_STATE)

    def test_break_wakes_a_sleeping_pet(self):
        pet = make_pet()
        pet.sleep()
        pet.set_phase(Phase.BREAK)
        self.assertEqual(pet.state, State.BARK_ALERT_STATE)

    def test_cannot_sleep_during_an_alert(self):
        pet = make_pet()
        pet.set_phase(Phase.BREAK)
        pet.sleep()
        self.assertEqual(pet.state, State.BARK_ALERT_STATE)

    def test_stretch_animation(self):
        pet = make_pet()
        pet._pause_until = 0
        pet.stretch(0.0, 3.0)
        pet.moving = False
        self.assertEqual(pet.animation(1.0), "stretch")
        self.assertEqual(pet.animation(4.0), "idle")


class TreatTests(unittest.TestCase):
    def test_pet_runs_to_the_bone_and_eats_it(self):
        pet = make_pet()
        bone = pet.give_treat((600, 300))
        self.assertIsNotNone(bone)
        self.assertEqual(pet.state, State.TREAT_STATE)
        for i in range(2000):
            pet.update((0, 0), False, i * 0.033)
            if pet.events:
                break
        self.assertEqual(pet.events, ["treat_eaten"])
        self.assertIsNone(pet.bone)
        self.assertEqual(pet.state, State.ROAM_STATE)

    def test_no_treat_during_an_alert(self):
        pet = make_pet()
        pet.set_phase(Phase.BREAK)
        self.assertIsNone(pet.give_treat((100, 100)))

    def test_alert_removes_the_bone(self):
        pet = make_pet()
        pet.give_treat((600, 300))
        pet.set_phase(Phase.BREAK)
        self.assertIsNone(pet.bone)


class FetchTests(unittest.TestCase):
    def play(self, pet, ball, cursor, steps=3000):
        for i in range(steps):
            pet.update(cursor, False, i * 0.033)
            if ball.carried:
                ball.place_center(*pet.mouth_point())
            ball.update((0, 0, 1000, 600))
            if "ball_delivered" in pet.events:
                return True
        return False

    def test_full_fetch_cycle(self):
        pet, ball = make_pet(), Ball(300, 300)
        self.assertTrue(pet.start_fetch(ball))
        ball.release(9, 0)
        cursor = (150, 450)
        self.assertTrue(self.play(pet, ball, cursor))
        self.assertIn("ball_picked", pet.events)
        self.assertFalse(ball.in_play)
        self.assertLess(math.hypot(center(pet)[0] - cursor[0], center(pet)[1] - cursor[1]), 90)

    def test_pet_waits_while_the_ball_is_held_or_not_thrown(self):
        pet, ball = make_pet(), Ball(600, 300)
        pet.start_fetch(ball)
        x, y = pet.x, pet.y
        for i in range(100):
            pet.update((0, 0), False, i * 0.033)
        self.assertEqual((pet.x, pet.y), (x, y))
        ball.grab()
        for i in range(100):
            pet.update((0, 0), False, i * 0.033)
        self.assertEqual((pet.x, pet.y), (x, y))

    def test_break_ends_fetch(self):
        pet, ball = make_pet(), Ball(600, 300)
        pet.start_fetch(ball)
        pet.set_phase(Phase.BREAK)
        self.assertFalse(pet.carrying)
        self.assertEqual(pet.state, State.BARK_ALERT_STATE)

    def test_stop_fetch_returns_to_roaming(self):
        pet, ball = make_pet(), Ball(600, 300)
        pet.start_fetch(ball)
        pet.stop_fetch()
        self.assertIsNone(pet.ball)
        self.assertEqual(pet.state, State.ROAM_STATE)


class MultiMonitorTests(unittest.TestCase):
    SCREENS = [(0, 0, 1000, 600), (1000, 0, 2000, 600)]

    def make(self):
        pet = make_pet()
        pet.set_screens(self.SCREENS)
        return pet

    def test_chases_the_cursor_onto_the_other_monitor(self):
        pet = self.make()
        for i in range(4000):
            pet.update((1700, 300), True, i * 0.033)
        self.assertGreater(center(pet)[0], 1000)
        self.assertEqual(pet.current, 1)

    def test_stays_on_the_virtual_desktop(self):
        pet = self.make()
        for i in range(3000):
            pet.update((5000, -300) if i % 2 else (-100, 900), i % 3 == 0, i * 0.033)
            self.assertTrue(0 <= pet.x <= 2000 - pet.w and 0 <= pet.y <= 600 - pet.h)

    def test_alert_goes_to_the_monitor_with_the_cursor(self):
        pet = self.make()
        pet.set_phase(Phase.BREAK)
        for i in range(1500):
            pet.update((1500, 300), False, i * 0.033)
        self.assertAlmostEqual(center(pet)[0], 1500, delta=3)

    def test_roams_to_the_other_monitor_eventually(self):
        import config
        pet = self.make()
        old = config.SCREEN_HOP_SECONDS
        config.SCREEN_HOP_SECONDS = 1
        try:
            seen = set()
            for i in range(20000):
                pet.update((500, 300), False, i * 0.033)
                seen.add(pet.current)
        finally:
            config.SCREEN_HOP_SECONDS = old
        self.assertEqual(seen, {0, 1})

    def test_single_monitor_never_hops(self):
        pet = make_pet()
        for i in range(3000):
            pet.update((500, 300), False, i * 0.033)
        self.assertEqual(pet.current, 0)

    def test_hop_can_be_turned_off(self):
        import config
        pet = self.make()
        pet.roam_all_screens = False
        old = config.SCREEN_HOP_SECONDS
        config.SCREEN_HOP_SECONDS = 1
        try:
            for i in range(5000):
                pet.update((500, 300), False, i * 0.033)
        finally:
            config.SCREEN_HOP_SECONDS = old
        self.assertEqual(pet.current, 0)

    def test_monitor_removed(self):
        pet = self.make()
        pet.x = 1500
        pet.set_screens([(0, 0, 1000, 600)])
        self.assertLessEqual(pet.x, 960)


class SpeedTests(unittest.TestCase):
    def test_speed_scales(self):
        pet = make_pet()
        base = pet.speed
        pet.speed_scale = 2.0
        self.assertAlmostEqual(pet.speed, base * 2)
        pet.mood_scale = 0.5
        self.assertAlmostEqual(pet.speed, base)


if __name__ == "__main__":
    unittest.main()
