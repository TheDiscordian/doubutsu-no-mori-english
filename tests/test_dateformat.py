"""Execute the original C formatter with every retail-width input and guards."""

import calendar
import ctypes
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("gcc"), "Host GCC is needed to execute the portable formatter tests")
class DateFormatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        library = Path(cls.temporary.name)/"dateformat.so"
        subprocess.run(["gcc", "-std=c99", "-Wall", "-Wextra", "-Werror", "-O2",
                        "-shared", "-fPIC", str(ROOT/"runtime/dateformat.c"), "-o", str(library)],
                       check=True, capture_output=True, text=True)
        cls.lib = ctypes.CDLL(str(library))
        cls.format = cls.lib.af_date_format
        cls.format.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint]
        cls.format.restype = ctypes.c_int

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def check(self, part, value, expected, capacity=9):
        guard = ctypes.create_string_buffer(b"!"*32, 32)
        result = self.format(ctypes.byref(guard, 8), capacity, part, value)
        self.assertEqual(result, len(expected))
        self.assertEqual(guard.raw, b"!"*8+expected.encode().ljust(capacity, b" ")+b"!"*(24-capacity))

    def test_every_year(self):
        for year in range(65536):
            self.check(0, year, str(year if 1901 <= year <= 2099 else 2000), 6)

    def test_all_byte_inputs_and_ordinal_exceptions(self):
        days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        for value in range(256):
            self.check(1, value, calendar.month_name[value if 1 <= value <= 12 else 1])
            self.check(2, value, days[value if value <= 6 else 0])
            day = value if 1 <= value <= 31 else 1
            suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
            self.check(3, value, f"{day}{suffix}", 4)
            hour = value if value < 24 else 0
            self.check(4, value, str(hour % 12 or 12), 2)
            for part in (5, 6):
                self.check(part, value, f"{value if value < 60 else 0:02d}", 2)
            self.check(7, value, "AM" if hour < 12 else "PM", 2)

    def test_insufficient_capacity_and_unknown_parts_do_not_write(self):
        for part, value, needed in ((0, 2000, 4), (1, 9, 9), (2, 3, 9), (3, 31, 4),
                                    (4, 0, 2), (5, 59, 2), (6, 59, 2), (7, 23, 2)):
            for capacity in range(needed):
                guard = ctypes.create_string_buffer(b"!"*32, 32)
                self.assertEqual(self.format(ctypes.byref(guard, 8), capacity, part, value), -1)
                self.assertEqual(guard.raw, b"!"*32)
        guard = ctypes.create_string_buffer(b"!"*32, 32)
        self.assertEqual(self.format(guard, 9, 8, 0), -1)
        self.assertEqual(guard.raw, b"!"*32)
        self.assertEqual(self.format(None, 9, 0, 2000), -1)

    @unittest.skipUnless((ROOT/"build/gamecube/text/string.jsonl").is_file(),
                         "GameCube text references remain local-only optional inputs")
    def test_calendar_words_match_supplied_english_disc(self):
        rows = {row["id"]: row["text"] for row in map(json.loads,
                (ROOT/"build/gamecube/text/string.jsonl").read_text().splitlines())}
        for part, start, count, first in ((1, 0x66D, 12, 1), (2, 9, 7, 0), (3, 0x64E, 31, 1)):
            for index in range(count):
                text = rows[f"string:{start+index:04X}"].rstrip()
                self.check(part, first+index, text)


if __name__ == "__main__":
    unittest.main()
