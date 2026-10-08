import os
import sys
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication  # noqa: E402

import config  # noqa: E402
import paths  # noqa: E402
import retro  # noqa: E402
import settings as prefs  # noqa: E402
import wardrobe  # noqa: E402
from assets_builder import available_avatars  # noqa: E402
from gui import load_frames  # noqa: E402

APP = QApplication.instance() or QApplication([])
retro.load_font()


class FrameTests(unittest.TestCase):
    def test_every_dog_keeps_the_fixed_size_with_every_accessory(self):
        for avatar in available_avatars():
            for accessory in [None] + list(wardrobe.ALL):
                frames = load_frames(avatar, accessory=accessory)
                for anim in ("idle", "walk", "bark", "haul", "happy", "sleep", "stretch"):
                    for pix in frames[anim]:
                        self.assertEqual((pix.width(), pix.height()), config.SPRITE_SIZE,
                                         f"{avatar}/{accessory}/{anim}")

    def test_accessories_change_the_picture(self):
        plain = load_frames("aspen")["idle"][0].toImage()
        for accessory in wardrobe.ALL:
            dressed = load_frames("aspen", accessory=accessory)["idle"][0].toImage()
            self.assertNotEqual(plain, dressed, accessory)

    def test_every_configured_accessory_has_art(self):
        for name in config.ACCESSORIES:
            self.assertIn(name, wardrobe.ALL)
            self.assertIn(name, wardrobe.TITLES)

    def test_sleep_frames_differ_from_idle(self):
        frames = load_frames("aspen")
        self.assertNotEqual(frames["sleep"][0].toImage(), frames["idle"][0].toImage())


class PathsAndSettingsTests(unittest.TestCase):
    def test_source_run_keeps_files_in_the_project_folder(self):
        self.assertEqual(paths.data_dir(), paths.resource_dir())

    def test_pref_falls_back_to_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = prefs.Settings(os.path.join(tmp, "s.json"))
            self.assertEqual(store.pref("snooze_minutes"), config.DEFAULT_SNOOZE_MINUTES)
            store.update_many({"snooze_minutes": 10, "pet_speed": 5})
            again = prefs.Settings(os.path.join(tmp, "s.json"))
            self.assertEqual(again.pref("snooze_minutes"), 10)
            self.assertEqual(again.speed_factor(), prefs.SPEED_FACTORS[5])

    def test_every_default_has_a_matching_dialog_field(self):
        import dialogs
        window = dialogs.SettingsWindow(dict(prefs.DEFAULTS), False)
        self.assertTrue(set(prefs.DEFAULTS) - {"muted"} <= set(window.values()) | {"muted"})
        self.assertEqual(set(prefs.DEFAULTS) | {"autostart"}, set(window.values()))

    def test_settings_window_values_round_trip(self):
        import dialogs
        current = dict(prefs.DEFAULTS, snooze_minutes=9, micro_enabled=False, volume=30)
        values = dialogs.SettingsWindow(current, True).values()
        self.assertEqual(values["snooze_minutes"], 9)
        self.assertFalse(values["micro_enabled"])
        self.assertEqual(values["volume"], 30)
        self.assertTrue(values["autostart"])


if __name__ == "__main__":
    unittest.main()
