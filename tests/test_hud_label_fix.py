"""English HUD source/consumer bindings, clock geometry, and complete ROM retention."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, apply_ups, sha256
from hud_label_fix import VROM, CLOCK, CASH_LOAD, BASE_SHA, patch_bank, build
from title_assets import DATA_BASE
from texture_preview import decode


@unittest.skipUnless((ROOT/'build/v1-editor-pixel-fix-03/animal-forest-title-preview.z64').is_file(),
                     'Supplied sources and checked pixel-editor predecessor required')
class HudLabelFixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT/'build/v1-editor-pixel-fix-03/animal-forest-title-preview.z64').read_bytes()
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.bank = by_vrom(cls.base)[VROM].extract(cls.base)
        cls.fixed, cls.changes = patch_bank(cls.bank, cls.rel, cls.symbols, {'cash': CASH_LOAD})

    def test_english_pixels_match_decoded_gc_and_fit_native_commands(self):
        for src, dest, length, fmt in ((0x87EE40, 0x8F8, 1024, 'ia8'),
                                       (0x8966A0, 0xB4D0, 512, 'i4')):
            donor = self.rel[DATA_BASE+src:DATA_BASE+src+length]
            self.assertEqual(decode(self.fixed[dest:dest+length], 64, 16, fmt),
                             decode(donor, 64, 16, fmt, gamecube=True))
        self.assertEqual(self.fixed[0xB6D0:0xB7D0], bytes(256))
        self.assertEqual(self.fixed[0xB480:0xB4B8], CASH_LOAD)
        self.assertEqual(struct.unpack_from('>2I', self.fixed, 0xB4B8), (0x01004008, 0x0400B320))
        self.assertEqual(struct.unpack_from('>2I', self.fixed, 0xB4B0), (0xF2000000, 0x000FC03C))
        # English cash wording is 48 screen units wide; not a stretched native 60.
        verts = list(struct.iter_unpack('>3hH2h4B', self.fixed[0xB320:0xB360]))
        self.assertEqual(sorted({v[0] for v in verts}), [51, 99])
        self.assertEqual(sorted({v[1] for v in verts}), [74, 86])
        self.assertEqual(sorted({v[4] for v in verts}), [0, 2048])
        for before, after in zip(struct.iter_unpack('>3hH2h4B', self.bank[0xB320:0xB360]), verts):
            self.assertEqual(before[3], after[3])
            self.assertEqual(before[6:], after[6:])

    def test_clock_order_preserves_footprint_and_every_non_x_vertex_field(self):
        bounds = []
        for at, delta, (left, right) in CLOCK:
            old = list(struct.iter_unpack('>3hH2h4B', self.bank[at:at+64]))
            new = list(struct.iter_unpack('>3hH2h4B', self.fixed[at:at+64]))
            for a, b in zip(old, new):
                self.assertEqual(b[0], a[0]+delta)
                self.assertEqual(a[1:], b[1:])
            bounds.append((left+delta, right+delta))
        self.assertEqual(bounds, [(120, 133), (84, 90), (90, 96), (98, 104), (105, 111), (112, 118)])
        self.assertEqual((min(a for a, _ in bounds), max(b for _, b in bounds)), (84, 133))
        restored = bytearray(self.fixed)
        for row in self.changes:
            at, size = row['offset'], row['bytes']
            restored[at:at+size] = self.bank[at:at+size]
        self.assertEqual(restored, self.bank)

    def test_complete_cartridge_retains_title_editors_code_allocations_and_all_other_resources(self):
        image, patch, report = build(self.native, self.base, self.rel, self.symbols, {'cash': CASH_LOAD})
        self.assertEqual(sha256(self.base), BASE_SHA)
        self.assertEqual(apply_ups(self.native, patch), image)
        self.assertEqual(len(image), len(self.base))
        before, after = by_vrom(self.base), by_vrom(image)
        self.assertEqual(set(before), set(after))
        for address, entry in after.items():
            self.assertEqual((entry.index, entry.size), (before[address].index, before[address].size))
            if address == 0x19D40: continue
            self.assertEqual(entry.extract(image), self.fixed if address == VROM else before[address].extract(self.base))
        for key in ('code_changed', 'allocation_changed', 'save_format_changed'):
            self.assertFalse(report[key])

    def test_unexpected_inputs_reject(self):
        for bank, rel, symbols, commands in (
                (self.bank[:-1], self.rel, self.symbols, {'cash': CASH_LOAD}),
                (self.bank, self.rel[:-1], self.symbols, {'cash': CASH_LOAD}),
                (self.bank, self.rel, self.symbols+b'\n', {'cash': CASH_LOAD}),
                (self.bank, self.rel, self.symbols, {'cash': CASH_LOAD[:-8]})):
            with self.assertRaises(ValueError): patch_bank(bank, rel, symbols, commands)
        with self.assertRaises(ValueError):
            build(self.native, self.native, self.rel, self.symbols, {'cash': CASH_LOAD})


if __name__ == '__main__':
    unittest.main()
