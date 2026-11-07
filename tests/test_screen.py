"""Offline tests for the single-column screen (no emulator needed)."""
import unittest
from unittest import mock

from rcfo import app, screen, ui


def bodies():
    """The tallest real screens: menu with 3 status lines, Magisk instructions, an error."""
    status = [screen.ok("x" * 300)] * 3
    magisk = screen.step_body(6, 7, "Installing the Vector (LSPosed) framework") + [
        screen.warn("One-time step in the phone window (Magisk is open there):"),
        "1. a", "2. b", "3. c", "4. d"]
    return {"menu": app.menu_body(status), "magisk": magisk,
            "error": [screen.warn("e")] * 6 + ["", screen.note("retry"), screen.note("erase")]}


class Layout(unittest.TestCase):
    def check(self, cols, rows, body, prompt=True):
        out = screen.render(body, cols, rows)
        self.assertLessEqual(len(out) + (1 if prompt else 0), rows, f"{cols}x{rows}: prompt pushed off")
        self.assertLessEqual(max(screen.visible_len(l) for l in out), cols - 1, f"{cols}x{rows}: wraps")
        return out

    def test_mac_terminal_120x30(self):
        for colour in (False, True):
            with mock.patch.object(ui, "COLOUR", colour):
                for name, body in bodies().items():
                    out = self.check(120, 30, body)
                    plain = [screen._ANSI.sub("", l) for l in out]
                    u = next(i for i, l in enumerate(plain) if "tiktok.com/@rcfo" in l)
                    self.assertGreaterEqual(u, 10, "fox should be above the URL")
                    centre = 119 / 2                                              # centred in the window
                    self.assertLessEqual(abs(plain[u].index("tiktok") + 8 - centre), 1.5)
                    self.assertEqual(plain[u + 1].strip(), "Banner unlock by: github.com/vanquzie")
                    self.assertLessEqual(abs(plain[u + 1].index("Banner") + 18.5 - centre), 1.5)
                    self.assertTrue(all("Tik: RCFO" not in l and "banner helper" not in l for l in plain))
                    if name == "menu":
                        menu = [l.strip() for l in plain[u + 2:]]
                        for item in ("1  Add images", "2  Close program", "3  Close program and erase all program data"):
                            self.assertIn(item, menu)
                        self.assertEqual(len(body), len(out) - u - 3, "whole menu body visible")

    def test_header_same_on_every_screen(self):
        with mock.patch.object(ui, "COLOUR", False):
            heads = {n: screen.render(b, 120, 30)[:18] for n, b in bodies().items()}
            self.assertEqual(len({tuple(h) for h in heads.values()}), 1)

    def test_many_sizes_never_overflow(self):
        for colour in (False, True):
            with mock.patch.object(ui, "COLOUR", colour):
                for cols in range(40, 201, 10):
                    for rows in range(14, 61, 4):
                        for body in bodies().values():
                            self.check(cols, rows, body)

    def test_link_has_plain_fallback(self):
        with mock.patch.object(ui, "COLOUR", False):
            self.assertEqual(screen.link("tiktok.com/@rcfo", screen.PROFILE_URL), "tiktok.com/@rcfo")
        with mock.patch.object(ui, "COLOUR", True):
            l = screen.link("x", screen.PROFILE_URL)
            self.assertTrue(l.startswith("\x1b]8;;https://www.tiktok.com/@rcfo\x1b\\"))
            self.assertEqual(screen.visible_len(l), 1)

    def test_heading_between_fox_and_url_and_url_plain(self):
        for colour in (False, True):
            with mock.patch.object(ui, "COLOUR", colour):
                for body in bodies().values():
                    out = screen.render(body, 120, 30)
                    plain = [screen._ANSI.sub("", l) for l in out]
                    u = next(i for i, l in enumerate(plain) if "tiktok.com/@rcfo" in l)
                    self.assertEqual([l.strip() for l in plain[u - 3:u]], [h.strip() for h in screen.HEADING])
                    start = plain[u - 3].index("▀█▀")                                   # heading centred
                    self.assertLessEqual(abs(start + screen.HEADING_WIDTH / 2 - 119 / 2), 1.5)
                    self.assertNotIn("\x1b[", out[u].replace("\x1b]8;;", ""))          # URL uncoloured
                    fox_rows = [l for l in plain[:u - 3] if l.strip()]                  # fox centred over heading
                    mid = 119 / 2
                    left = min(len(l) - len(l.lstrip()) for l in plain[:u - 3])
                    fox_w = max(len(l.rstrip()) for l in plain[:u - 3]) - left
                    self.assertTrue(fox_rows)
                    self.assertLessEqual(abs(left + fox_w / 2 - mid), 2)
                    body = plain[u + 3]                                                  # body stays left
                    self.assertTrue(body.startswith(" ") and not body.startswith("  "))
        self.assertLessEqual(screen.HEADING_WIDTH, 60)
        g = screen._GLYPHS                                    # spells exactly "TIKTOK : RCFO"
        self.assertEqual(screen.HEADING, [" ".join(g[c][r] for c in "TIKTOK : RCFO") for r in range(3)])
        self.assertNotIn("@", screen._GLYPHS)

    def test_credit_points_at_module_author(self):
        self.assertEqual(screen.CREDIT_URL, "https://github.com/vanquzie/TikProfileBanner")

    def test_fit(self):
        self.assertEqual(screen.fit("abc", 5), "abc")
        self.assertEqual(len(screen.fit("a" * 50, 10)), 10)


if __name__ == "__main__":
    unittest.main()
