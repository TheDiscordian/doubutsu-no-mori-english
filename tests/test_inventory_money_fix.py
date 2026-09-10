"""Money-only MIPS argument flow, five slot bounds, and retained font/cartridge."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, apply_ups
from inventory_money_fix import VROM, RAM, WORDS, patch_overlay, build
from font import FONT_VROM, ATLAS_OFFSET, ATLAS_SIZE, pixels, get_glyph


@unittest.skipUnless((ROOT/'build/v1-notice-tune-fix-01/animal-forest-title-preview.z64').is_file(),
                     'Checked notice/tune predecessor required')
class InventoryMoneyFixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT/'build/v1-notice-tune-fix-01/animal-forest-title-preview.z64').read_bytes()
        cls.files = by_vrom(cls.base)
        cls.old = cls.files[VROM].extract(cls.base)
        cls.reloc = cls.files[0x7898C0].extract(cls.base)
        cls.fixed = patch_overlay(cls.old, cls.reloc)

    def test_native_call_arguments_retain_colours_height_and_single_digit(self):
        # Evaluate the actual straight-line integer/FPU stores between glyph
        # selection and the resident draw call. No guessed source-only wrapper.
        def arguments(data):
            r = [0]*32; r[29] = 0x1000
            f = {20: 123.5, 22: 0.75, 24: 102.0}; stack = {}
            for at in range(0x8088038C, 0x808803CC, 4):
                w = struct.unpack_from('>I', data, at-RAM)[0]
                op, rs, rt, imm = w >> 26, w >> 21 & 31, w >> 16 & 31, w & 65535
                if op == 9: r[rt] = r[rs]+(imm if imm < 32768 else imm-65536)
                elif op == 15: r[rt] = imm << 16
                elif op == 43: stack[r[rs]+imm] = r[rt]
                elif op == 57: stack[r[rs]+imm] = struct.unpack('>I', struct.pack('>f', f[rt]))[0]
                elif op == 17 and rs == 0:
                    r[rt] = struct.unpack('>I', struct.pack('>f', f[w >> 11 & 31]))[0]
                elif op == 3:
                    self.assertEqual((w & 0x3FFFFFF) << 2 | 0x80000000, 0x80090E98)
                else: self.fail(f'Unreviewed money argument instruction {at:08X}: {w:08X}')
            return r, {a-0x1000: v for a, v in stack.items()}
        before_r, before = arguments(self.old); after_r, after = arguments(self.fixed)
        self.assertEqual(before_r[6], 1); self.assertEqual(after_r[6], 1)
        for at in (16, 20, 24, 28, 32, 36, 40, 48, 52): self.assertEqual(before[at], after[at])
        self.assertEqual([after[n] for n in (20, 24, 28, 32)], [255, 60, 0, 255])
        self.assertEqual(struct.unpack('>f', struct.pack('>I', after[44]))[0], 1.25)
        self.assertEqual(struct.unpack('>f', struct.pack('>I', after[48]))[0], 0.75)

    def test_all_digits_fill_but_do_not_overlap_adjacent_slots(self):
        atlas = self.files[FONT_VROM].extract(self.base)[ATLAS_OFFSET:ATLAS_OFFSET+ATLAS_SIZE]
        atlas = pixels(atlas)
        for digit in range(48, 58):
            glyph = get_glyph(atlas, digit)
            columns = [x for x in range(12) if any(row[x] for row in glyph)]
            self.assertEqual((min(columns), max(columns)), (0, 4))
            for slot in range(5):
                origin = 123.5+12*slot
                left, right = origin+min(columns)*1.25, origin+(max(columns)+1)*1.25
                self.assertEqual(right-left, 6.25)
                self.assertGreater(left, 122+12*slot)
                self.assertLess(right, 122+12*(slot+1))
        restored = bytearray(self.fixed)
        for at in WORDS: restored[at-RAM:at-RAM+4] = self.old[at-RAM:at-RAM+4]
        self.assertEqual(restored, self.old)

    def test_rom_retains_font_other_renderers_relocations_and_save_calculation(self):
        image, patch, report = build(self.native, self.base)
        self.assertEqual(apply_ups(self.native, patch), image)
        self.assertEqual(len(image), len(self.base))
        files = by_vrom(image); self.assertEqual(set(files), set(self.files))
        for v, e in files.items():
            self.assertEqual((e.index, e.size), (self.files[v].index, self.files[v].size))
            if v != 0x19D40:
                self.assertEqual(e.extract(image), self.fixed if v == VROM else self.files[v].extract(self.base))
        self.assertFalse(report['font_changed']); self.assertFalse(report['save_format_changed'])


if __name__ == '__main__':
    unittest.main()
