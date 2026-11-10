import os
import tempfile
import unittest

from ini_file import IniFile

SAMPLE = "[Settings]\r\nanimations=1\r\nfont-size=16\r\n; a comment\r\n\r\n[Versions]\r\nlast=1.2\r\n"


def make(raw: bytes):
    fd, path = tempfile.mkstemp(suffix=".ini")
    with os.fdopen(fd, "wb") as f:
        f.write(raw)
    return path


class IniFileTests(unittest.TestCase):
    def roundtrip(self, raw):
        path = make(raw)
        self.addCleanup(os.remove, path)
        return path

    def test_get_is_case_insensitive(self):
        path = self.roundtrip(SAMPLE.encode("utf-8"))
        ini = IniFile(path)
        self.assertEqual(ini.get("settings", "FONT-SIZE"), "16")
        self.assertIsNone(ini.get("settings", "missing"))
        self.assertEqual(ini.get("nope", "x", "d"), "d")

    def test_set_existing_keeps_everything_else(self):
        path = self.roundtrip(SAMPLE.encode("utf-8"))
        ini = IniFile(path)
        ini.set("Settings", "font-size", 18)
        ini.save()
        with open(path, "rb") as f:
            self.assertEqual(f.read().decode("utf-8"), SAMPLE.replace("font-size=16", "font-size=18"))

    def test_set_new_key_goes_inside_its_section(self):
        path = self.roundtrip(SAMPLE.encode("utf-8"))
        ini = IniFile(path)
        ini.set("Settings", "new key", 5)
        ini.save()
        again = IniFile(path)
        self.assertEqual(again.get("Settings", "new key"), "5")
        self.assertEqual(again.get("Versions", "last"), "1.2")
        self.assertLess(again.lines.index("new key=5"), again.lines.index("[Versions]"))

    def test_new_section_is_appended(self):
        path = self.roundtrip(SAMPLE.encode("utf-8"))
        ini = IniFile(path)
        ini.set("Brand New", "k", "v")
        ini.save()
        self.assertEqual(IniFile(path).get("Brand New", "k"), "v")

    def test_utf16_bom_is_preserved(self):
        raw = b"\xff\xfe" + SAMPLE.encode("utf-16-le")
        path = self.roundtrip(raw)
        ini = IniFile(path)
        ini.set("Settings", "animations", 0)
        ini.save()
        with open(path, "rb") as f:
            out = f.read()
        self.assertTrue(out.startswith(b"\xff\xfe"))
        self.assertEqual(IniFile(path).get("Settings", "animations"), "0")

    def test_utf8_bom_is_preserved(self):
        raw = b"\xef\xbb\xbf" + SAMPLE.encode("utf-8")
        path = self.roundtrip(raw)
        ini = IniFile(path)
        ini.set("Settings", "animations", 0)
        ini.save()
        with open(path, "rb") as f:
            self.assertTrue(f.read().startswith(b"\xef\xbb\xbf"))

    def test_missing_file_is_created(self):
        path = os.path.join(tempfile.mkdtemp(), "sub", "config.ini")
        ini = IniFile(path)
        ini.set("Settings", "animations", 1)
        ini.save()
        self.assertEqual(IniFile(path).get("Settings", "animations"), "1")


if __name__ == "__main__":
    unittest.main()
