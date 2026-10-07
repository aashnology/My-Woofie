import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pet import Pet, State  # noqa: E402
from timer import Phase  # noqa: E402


def make_pet():
    return Pet((0, 0, 1000, 600), (40, 40))


class PetTests(unittest.TestCase):
    def test_phase_changes_drive_states(self):
        pet = make_pet()
        pet.set_phase(Phase.BREAK)
        self.assertEqual(pet.state, State.BARK_ALERT_STATE)
        pet.set_phase(Phase.HAUL)
        self.assertEqual(pet.state, State.HAUL_ALERT_STATE)
        pet.set_phase(Phase.FOCUS)
        self.assertEqual(pet.state, State.ROAM_STATE)

    def test_chases_the_cursor(self):
        pet = make_pet()
        start = math.hypot(500 - pet.x, 300 - pet.y)
        for i in range(200):
            pet.update((500, 300), True, i * 0.033)
        self.assertEqual(pet.state, State.CHASE_STATE)
        self.assertLess(math.hypot(480 - pet.x, 280 - pet.y), start)

    def test_stays_on_screen(self):
        pet = make_pet()
        for i in range(3000):
            pet.update((5000, -300) if i % 2 else (-100, 900), i % 3 == 0, i * 0.033)
            self.assertTrue(0 <= pet.x <= 960 and 0 <= pet.y <= 560)

    def test_alert_goes_to_mid_screen(self):
        pet = make_pet()
        pet.set_phase(Phase.BREAK)
        for i in range(600):
            pet.update((0, 0), False, i * 0.033)
        self.assertAlmostEqual(pet.x, 480, delta=2)

    def test_hop_height_scales_with_size(self):
        small, large = make_pet(), Pet((0, 0, 1000, 600), (160, 160))
        for pet in (small, large):
            pet.set_phase(Phase.BREAK)
        self.assertLess(abs(small.bob(0.3)), abs(large.bob(0.3)))

    def test_resize_keeps_pet_in_bounds(self):
        pet = make_pet()
        pet.x, pet.y = 960, 560
        pet.set_size((100, 100))
        self.assertLessEqual(pet.x, 900)
        self.assertLessEqual(pet.y, 500)


if __name__ == "__main__":
    unittest.main()
