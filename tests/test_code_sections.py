"""CPU-reference audits distinguish instructions from embedded overlay data."""

from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from aflib import by_vrom, replace_dma
from code_sections import code_segments, parse_segments
from runtime_module import audit_watchdog_references
from test_retail import ROM_PATH


class CodeSectionTests(unittest.TestCase):
    def test_pinned_text_and_embedded_data_boundaries(self):
        segments, definitions = code_segments()
        self.assertEqual(len(definitions), 4)
        for vrom, boundary, texture in ((0x7908A0, 0x1910, 0x1C04),
                                        (0x7A28F0, 0x36E0, 0x8A74)):
            self.assertTrue(segments[vrom].is_text(boundary-4))
            self.assertFalse(segments[vrom].is_text(boundary))
            self.assertFalse(segments[vrom].is_text(texture))
        self.assertTrue(segments[0x1060].is_text(0x8F20-0x1060))
        self.assertFalse(segments[0x1060].is_text(0x179A0-0x1060))
        self.assertFalse(segments[0x741A40].is_text(0))

    def test_unknown_types_and_unordered_boundaries_fail(self):
        prefix = "  - name: synthetic\n    type: code\n    start: 0x100\n    vram: 0x80000100\n    subsegments:\n"
        for suffix in ("      - [0x100, unexpected]\n",
                       "      - [0x100, c, first]\n      - [0xF0, data, second]\n",
                       "      - [0x100, lib, library, object, .unknown]\n",
                       "      - {type: data, vram: 0x80000100, name: data}\n"):
            with self.assertRaises(ValueError):
                parse_segments(prefix+suffix)

    @unittest.skipUnless(ROM_PATH.is_file(), "Retail ROM is local-only")
    def test_real_calls_and_data_pointers_are_still_rejected(self):
        rom = ROM_PATH.read_bytes()
        vrom = 0x7908A0
        original = by_vrom(rom)[vrom].extract(rom)
        self.assertEqual(struct.unpack_from(">I", original, 0x1C04)[0], 0x0C027630)
        self.assertEqual(audit_watchdog_references(rom)["external_interior_references"], [])
        for offset, word in ((0, 0x0C027630), (0x1C04, 0x8009D8C0)):
            data = bytearray(original)
            struct.pack_into(">I", data, offset, word)
            altered = replace_dma(rom, {vrom: bytes(data)})
            with self.assertRaisesRegex(ValueError, "External replaced-function-interior"):
                audit_watchdog_references(altered)


if __name__ == "__main__":
    unittest.main()
