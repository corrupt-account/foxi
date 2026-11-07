"""Offline tests for the menu screen layout (no emulator needed)."""
import unittest
from unittest import mock

from rcfo import panel, ui


class Layout(unittest.TestCase):
    def check(self, cols, rows, n_status):
        out = panel.render(cols, rows, [panel.ok("x" * 300)] * n_status)
        self.assertLessEqual(len(out) + 1, rows, f"{cols}x{rows}: prompt pushed off-screen")
        self.assertLessEqual(max(panel.visible_len(l) for l in out), cols - 1, f"{cols}x{rows}: wraps")
        return out

    def test_mac_terminal_120x30(self):
        for colour in (False, True):
            with mock.patch.object(ui, "COLOUR", colour):
                out = self.check(120, 30, 3)
                plain = [panel._ANSI.sub("", l) for l in out]
                url_row = next(i for i, l in enumerate(plain) if "tiktok.com/@rcfo" in l)
                self.assertEqual(plain[url_row].index("tiktok"), 1)            # left column
                self.assertIn("TikProfileBanner", plain[url_row + 1])
                self.assertIn("vanquzie", plain[url_row + 2])
                self.assertIn("GPL-3.0", plain[url_row + 2])
                self.assertTrue(any("1  Add images" in l for l in plain))
                self.assertTrue(any("3  Close program and erase all program data" in l for l in plain))

    def test_many_sizes_never_overflow(self):
        for colour in (False, True):
            with mock.patch.object(ui, "COLOUR", colour):
                for cols in range(50, 201, 10):
                    for rows in range(16, 61, 4):
                        for n in (0, 3):
                            self.check(cols, rows, n)

    def test_link_has_plain_fallback(self):
        with mock.patch.object(ui, "COLOUR", False):
            self.assertEqual(panel.link("tiktok.com/@rcfo", panel.PROFILE_URL), "tiktok.com/@rcfo")
        with mock.patch.object(ui, "COLOUR", True):
            l = panel.link("x", panel.PROFILE_URL)
            self.assertTrue(l.startswith("\x1b]8;;https://www.tiktok.com/@rcfo\x1b\\"))
            self.assertEqual(panel.visible_len(l), 1)

    def test_fit(self):
        self.assertEqual(panel.fit("abc", 5), "abc")
        self.assertEqual(len(panel.fit("a" * 50, 10)), 10)


if __name__ == "__main__":
    unittest.main()
