import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompts import PromptBank  # noqa: E402


def write(path, text, mtime=None):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    if mtime:
        os.utime(path, (mtime, mtime))


class PromptBankTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "prompts.txt")

    def tearDown(self):
        self.dir.cleanup()

    def test_sequential_skips_comments_and_blanks(self):
        write(self.path, "# comment\n\none\n  two  \n")
        bank = PromptBank(self.path, ["fallback"], "sequential")
        self.assertEqual([bank.next() for _ in range(3)], ["one", "two", "one"])

    def test_missing_file_uses_fallback(self):
        bank = PromptBank(os.path.join(self.dir.name, "nope.txt"), ["fallback"])
        self.assertEqual(bank.next(), "fallback")

    def test_empty_file_uses_fallback(self):
        write(self.path, "# only a comment\n")
        self.assertEqual(PromptBank(self.path, ["fallback"]).next(), "fallback")

    def test_random_never_repeats_immediately(self):
        write(self.path, "a\nb\nc\n")
        bank = PromptBank(self.path, ["x"], "random")
        picks = [bank.next() for _ in range(40)]
        self.assertTrue(all(a != b for a, b in zip(picks, picks[1:])))

    def test_edits_apply_without_restart(self):
        write(self.path, "old\n", mtime=1000)
        bank = PromptBank(self.path, ["x"])
        self.assertEqual(bank.next(), "old")
        write(self.path, "new\n", mtime=2000)
        self.assertEqual(bank.next(), "new")


if __name__ == "__main__":
    unittest.main()
