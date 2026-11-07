"""Offline tests: drag-and-drop path parsing, image checks, erase safety (no emulator needed)."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from foxi_core import app, config as C, ui

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 16


class PathParsing(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        self.spaced = d / "My Banner (1).jpg"
        self.uni = d / "صورة الغلاف.png"
        self.plain = d / "fox.png"
        self.quote = d / "it's mine.jpg"
        for p, b in ((self.spaced, JPG), (self.uni, PNG), (self.plain, PNG), (self.quote, JPG)):
            p.write_bytes(b)

    def tearDown(self):
        self.tmp.cleanup()

    def one(self, raw):
        got = ui.parse_paths(raw)
        self.assertEqual(len(got), 1, got)
        return Path(ui._existing(got[0]))

    def test_plain_and_spaces_unquoted(self):
        self.assertEqual(self.one(str(self.plain)), self.plain)
        self.assertEqual(self.one(str(self.spaced) + " "), self.spaced)   # Terminal adds a trailing space

    def test_macos_backslash_escapes(self):
        esc = str(self.spaced).replace(" ", "\\ ").replace("(", "\\(").replace(")", "\\)")
        self.assertEqual(self.one(esc), self.spaced)

    def test_quoted(self):
        self.assertEqual(self.one(f"'{self.spaced}'"), self.spaced)
        self.assertEqual(self.one(f'"{self.spaced}"'), self.spaced)
        self.assertEqual(self.one(f'"{self.quote}"'), self.quote)

    def test_unicode_and_nfd(self):
        import unicodedata
        self.assertEqual(self.one(str(self.uni)), self.uni)
        nfd = unicodedata.normalize("NFD", str(self.uni))
        self.assertIsNotNone(ui._existing(nfd))

    def test_file_uri(self):
        self.assertEqual(self.one(self.spaced.as_uri()), self.spaced)

    def test_several_dropped_files(self):
        esc = str(self.spaced).replace(" ", "\\ ").replace("(", "\\(").replace(")", "\\)")
        got = ui.parse_paths(f"{self.plain} {esc} '{self.uni}'")
        self.assertEqual([Path(ui._existing(g)) for g in got], [self.plain, self.spaced, self.uni])

    def test_windows_styles(self):
        with mock.patch.object(C, "IS_WINDOWS", True):
            self.assertEqual(ui.parse_paths(r'"C:\Users\Ana Maria\Pictures\a b.jpg"'),
                             [r"C:\Users\Ana Maria\Pictures\a b.jpg"])
            self.assertEqual(ui.parse_paths(r"& 'C:\Users\x\b.png'"), [r"C:\Users\x\b.png"])
            self.assertEqual(ui.parse_paths(r'"C:\a.jpg" "D:\x y\b.png"'), [r"C:\a.jpg", r"D:\x y\b.png"])
            self.assertEqual(ui.parse_paths(r"\\server\share\c.jpg"), [r"\\server\share\c.jpg"])

    def test_empty(self):
        self.assertEqual(ui.parse_paths("   "), [])


class ImageChecks(unittest.TestCase):
    def test_kinds_and_rejections(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "a.jpg").write_bytes(JPG)
            (d / "b.webp").write_bytes(b"RIFF\x00\x00\x00\x00WEBPVP8 ")
            (d / "c.heic").write_bytes(b"\x00\x00\x00\x18ftypheic\x00\x00")
            (d / "fake.jpg").write_bytes(b"not an image")
            (d / "doc.pdf").write_bytes(b"%PDF-1.7")
            self.assertEqual(ui.check_image(str(d / "a.jpg"))[1], "JPEG")
            self.assertEqual(ui.check_image(str(d / "b.webp"))[1], "WebP")
            self.assertEqual(ui.check_image(str(d / "c.heic"))[1], "HEIC")
            self.assertIsNone(ui.check_image(str(d / "fake.jpg"))[0])
            self.assertIsNone(ui.check_image(str(d / "doc.pdf"))[0])
            self.assertIsNone(ui.check_image(str(d / "missing.png"))[0])
            self.assertIsNone(ui.check_image(str(d))[0])

    def test_device_names_are_safe_and_unique(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "it's \"my\" $(rm -rf) فوكس.PNG"
            p.write_bytes(PNG)
            n1 = ui.device_name(p, set())
            self.assertTrue(n1.endswith(".png"))
            self.assertNotRegex(n1, r"['\"$`;&|/\\]")   # () are kept; every device command quotes names
            self.assertIn("فوكس", n1)
            self.assertNotEqual(ui.device_name(p, {n1}), n1)


class EraseSafety(unittest.TestCase):
    def test_refuses_unmarked_or_home(self):
        with tempfile.TemporaryDirectory() as d:
            with mock.patch.object(C, "APP_DIR", Path(d)):
                with self.assertRaises(Exception):
                    app.remove_app_dir()                    # no state.json marker
            with mock.patch.object(C, "APP_DIR", Path.home()):
                with self.assertRaises(Exception):
                    app.remove_app_dir()

    def test_removes_marked_folder(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "app"
            (target / "sdk").mkdir(parents=True)
            (target / "state.json").write_text("{}")
            with mock.patch.object(C, "APP_DIR", target):
                app.remove_app_dir()
            self.assertFalse(target.exists())
            self.assertTrue(Path(d).exists())


if __name__ == "__main__":
    unittest.main()
