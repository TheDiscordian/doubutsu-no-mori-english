"""Integration checks run when the user supplies the supported retail ROM."""

import os
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from aflib import CODE_RAM, CODE_VROM, by_vrom, n64_checksum, replace_dma, verified_rom
from build import apply_translations
from font import FONT_VROM, WIDTH_TABLE, make_halfwidth
from textbanks import Bank, banks
from textcodec import command_info, decode, encode
from keyboard import (CURSOR_CODE, EDITOR_VROM, LABELS, LABELS_VROM, LEDIT_RAM,
                      LEDIT_RELOC_VROM, LEDIT_VROM, TITLES, make_english_keyboard,
                      validate_label_layout)

ROM_PATH = Path(os.environ.get("AF_TEST_ROM", ROOT/"local/rom/Doubutsu no Mori (Japan).z64"))


@unittest.skipUnless(ROM_PATH.is_file(), "Retail ROM is a local-only optional test input")
class RetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes())
        cls.files = by_vrom(cls.rom)
        cls.info = command_info(cls.files[CODE_VROM].extract(cls.rom))

    def test_all_original_banks_roundtrip(self):
        for bank in banks(self.rom):
            entries = bank.entries()
            self.assertEqual(bank.rebuild(entries), (bank.data, bank.table), bank.name)
            for entry in entries:
                self.assertEqual(encode(decode(entry, self.info), self.info), entry)

    def test_font_metrics_and_relocation(self):
        replacements, report = make_halfwidth(self.rom)
        for char in "iIl'":
            self.assertEqual(replacements[CODE_VROM][WIDTH_TABLE+ord(char)], 8)
        count, relocations = apply_translations(self.rom, replacements, ROOT/"translations/opening.json")
        output = replace_dma(self.rom, replacements, relocations)
        files = by_vrom(output)
        self.assertEqual(n64_checksum(output), struct.unpack_from(">2I", output, 16))
        for vrom, data in replacements.items():
            self.assertEqual(files[relocations.get(vrom, vrom)].extract(output), data)
        # Full-ROM IPL/header identity outside checksums and source file data
        # remain intact; only DMA metadata and the two CRC words may differ in
        # the original physical ROM region.
        allowed = set(range(16, 24))
        for vrom in replacements:
            at = 0x19D50+self.files[vrom].index*16
            allowed.update(range(at, at+16))
        self.assertFalse(any(a != b and i not in allowed
                             for i, (a, b) in enumerate(zip(self.rom, output))))

    def test_keyboard_prompts_labels_and_overlay_sizes(self):
        _, metrics = make_halfwidth(self.rom)
        replacements, report = make_english_keyboard(self.rom, self.info, metrics["advance_by_glyph"])
        for vrom, data in replacements.items():
            self.assertEqual(len(data), len(self.files[vrom].extract(self.rom)))
        data = replacements[LEDIT_VROM]
        original = self.files[LEDIT_VROM].extract(self.rom)
        for i, title in enumerate(TITLES):
            record = 0xA18+40*i
            pointer, length, maximum = struct.unpack_from(">3I", data, record+0x10)
            offset = pointer-LEDIT_RAM
            self.assertGreaterEqual(offset, 0x9E0)
            self.assertLessEqual(offset+length, 0xA18)
            self.assertEqual(decode(data[offset:offset+length], self.info), title)
            self.assertEqual(maximum, [6, 6, 4, 10, 10][i])
            self.assertEqual(data[record+0x18:record+0x28], original[record+0x18:record+0x28])
        self.assertEqual(data[0xAF4:0xAF8], b"town")
        allowed = set()
        graphics = replacements[LABELS_VROM]
        for offset, width, height, fmt, _ in LABELS:
            size = width*height//2 if fmt == "I4" else width*height
            region = set(range(offset, offset+size))
            self.assertFalse(allowed & region)
            allowed.update(region)
        original_graphics = self.files[LABELS_VROM].extract(self.rom)
        self.assertFalse(any(a != b and i not in allowed for i, (a, b) in
                             enumerate(zip(original_graphics, graphics))))
        output = replace_dma(self.rom, replacements)
        files = by_vrom(output)
        for vrom, content in replacements.items():
            self.assertEqual(files[vrom].extract(output), content)
        self.assertEqual(files[0x790530].extract(output), self.files[0x790530].extract(self.rom))
        before = self.files[LEDIT_RELOC_VROM].extract(self.rom)
        after = files[LEDIT_RELOC_VROM].extract(output)
        self.assertEqual(before[:16], after[:16])
        self.assertEqual(before[-4:], after[-4:])
        records = list(struct.unpack_from(">37I", before, 20))
        self.assertEqual(struct.unpack_from(">I", after, 16)[0], 35)
        self.assertEqual(list(struct.unpack_from(">35I", after, 20)),
                         [r for r in records if r not in (0x450006E4, 0x460006E8)])
        self.assertEqual(data[0x6E0:0x740], CURSOR_CODE)

    def test_keyboard_texture_descriptors_are_verified(self):
        data = bytearray(self.files[LABELS_VROM].extract(self.rom))
        validate_label_layout(data)
        # Corrupt the render-tile width for the first tab, not its pixel data.
        data[0x1448+53] ^= 1
        with self.assertRaisesRegex(ValueError, "descriptor"):
            validate_label_layout(data)
