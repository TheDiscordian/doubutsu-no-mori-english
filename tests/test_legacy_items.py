"""Actual legacy loader metadata replaces unverified archived item offsets."""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from aflib import CODE_VROM, by_vrom
from legacy_items import ITEM_VROM, layout
from textbanks import banks
from test_retail import ROM_PATH

LEGACY = ROOT/"build/inspect/legacy.z64"


@unittest.skipUnless(ROM_PATH.is_file() and LEGACY.is_file(), "Original and legacy ROMs are local-only test inputs")
class LegacyItemTests(unittest.TestCase):
    def setUp(self):
        self.rom = LEGACY.read_bytes()
        files = by_vrom(self.rom)
        self.code = files[CODE_VROM].extract(self.rom)
        self.data = files[ITEM_VROM].extract(self.rom)

    def test_actual_pointers_counts_and_roundtrip(self):
        descriptors = layout(self.code, self.data)
        self.assertEqual(len(descriptors), 17)
        self.assertEqual(descriptors[1], (0x21, 0x118, 0x14, 0x2020, 0x2048, 4))
        self.assertEqual(descriptors[-1], (0x10, 0xC50, 0xED0, 0x44A4, len(self.data), 947))
        selected = [b for b in banks(self.rom, legacy=True) if b.name.startswith("item_")]
        self.assertEqual(len(selected), 17)
        for bank, descriptor in zip(selected, descriptors):
            self.assertEqual(len(bank.entries()), descriptor[-1])
            self.assertEqual(bank.rebuild(bank.entries()), (bank.data, bank.table))

    def test_changed_code_offsets_and_truncation_fail(self):
        with self.assertRaisesRegex(ValueError, "Unknown legacy"):
            layout(bytes(len(self.code)), self.data)
        with self.assertRaises(ValueError):
            layout(self.code, self.data[:0x2000])
        bad = bytearray(self.data)
        bad[0x10:0x14] = b"\xff"*4
        with self.assertRaisesRegex(ValueError, "cumulative"):
            layout(self.code, bad)
        bad = bytearray(self.data)
        bad[0x110:0x114] = b"\0\0\0\1"
        with self.assertRaisesRegex(ValueError, "cumulative"):
            layout(self.code, bad)

    def test_native_furniture_has_four_rotations_per_legacy_entry(self):
        native = next(b for b in banks(ROM_PATH.read_bytes()) if b.name == "item_10").entries()
        self.assertEqual(len(native), 947*4+1)
        for index in range(947):
            self.assertEqual(len(set(native[index*4:index*4+4])), 1)
