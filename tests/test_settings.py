import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from settings import Settings  # noqa: E402


class SettingsTests(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "s.json")
            Settings(path).set("avatar", "snow")
            self.assertEqual(Settings(path).get("avatar"), "snow")

    def test_corrupt_file_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "s.json")
            with open(path, "w") as handle:
                handle.write("{not json")
            self.assertEqual(Settings(path).get("avatar", "aspen"), "aspen")


if __name__ == "__main__":
    unittest.main()
