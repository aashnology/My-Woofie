import os
import sys
import tempfile
import unittest
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402
import main  # noqa: E402
from assets_builder import available_avatars  # noqa: E402
from settings import Settings  # noqa: E402


class Args:
    settings = False


class AskTimersTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.settings = Settings(os.path.join(self.tmp.name, "s.json"))

    def tearDown(self):
        self.tmp.cleanup()

    def ask(self, answer, test_mode=False, args=None):
        with mock.patch("timer_dialog.TimerDialog.choose", return_value=answer) as choose:
            main.ask_timers_if_needed(self.settings, args or Args(), test_mode)
        return choose

    def test_first_launch_asks_and_saves(self):
        choose = self.ask((50, 10, True))
        choose.assert_called_once()
        self.assertEqual((self.settings.get("focus_minutes"), self.settings.get("break_minutes")), (50, 10))

    def test_second_launch_asks_again_by_default(self):
        self.ask((50, 10, True))
        choose = self.ask((90, 20, True))
        choose.assert_called_once_with(50, 10, True)
        self.assertEqual(self.settings.get("focus_minutes"), 90)

    def test_turning_the_box_off_stops_the_question(self):
        self.ask((50, 10, False))
        choose = self.ask(None)
        choose.assert_not_called()
        self.assertEqual(self.settings.pref("focus_minutes"), 50)

    def test_cancelling_keeps_the_saved_times(self):
        self.ask((50, 10, True))
        self.ask(None)
        self.assertEqual(self.settings.get("focus_minutes"), 50)
        self.assertEqual(self.settings.get("break_minutes"), 10)

    def test_cancelling_on_the_very_first_launch_saves_the_defaults(self):
        self.ask(None)
        self.assertEqual(self.settings.get("focus_minutes"), config.DEFAULT_FOCUS_MINUTES)

    def test_settings_flag_asks_even_when_switched_off(self):
        self.ask((50, 10, False))
        args = Args()
        args.settings = True
        self.assertTrue(self.ask((60, 10, False), args=args).called)

    def test_test_mode_never_asks(self):
        self.assertFalse(self.ask((50, 10, True), test_mode=True).called)


class SpriteSizeLockTests(unittest.TestCase):
    def test_the_approved_size_is_locked(self):
        self.assertEqual(config.SPRITE_SIZE, (53, 47))

    def test_every_available_avatar_is_registered_for_the_size_check(self):
        # tests/test_gui_v2.py renders every avatar returned here and requires 53 x 47 for every frame,
        # so a newly added avatar is checked automatically.
        self.assertGreaterEqual(len(available_avatars()), 6)


if __name__ == "__main__":
    unittest.main()
