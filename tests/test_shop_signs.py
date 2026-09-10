"""Exact donor sign and native control-label encoding, with prior resources retained."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, sha256, apply_ups
from shop_signs import OBJECT, GRID, sign_asset, build
from keyboard_grid_labels import LABELS, install, compiled_form, CORRECTED_SHA, encode_label
from keyboard_grid_overlay import validate
from textcodec import GLYPHS
from title_assets import DATA_BASE, untile, pack4


@unittest.skipUnless((ROOT/'build/nookington-sign-02/build.json').is_file(), 'Local source assets required')
class ShopSignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT/'build/nookington-sign-02/animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((ROOT/'build/nookington-sign-02/build.json').read_text())
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.files = by_vrom(cls.base)

    def test_native_labels_change_three_data_bytes_and_reject_other_mutations(self):
        original = self.files[GRID].extract(self.base)
        corrected = install(original)
        self.assertEqual(sha256(corrected), CORRECTED_SHA)
        self.assertEqual(sum(a != b for a, b in zip(original, corrected)), 3)
        self.assertEqual(compiled_form(corrected), original)
        self.assertEqual(compiled_form(original), original)
        for _, label in LABELS:
            self.assertEqual(''.join(GLYPHS[b] for b in encode_label(label)), label.decode().replace('/', ' '))
        reloc = self.files[0x3948000].extract(self.base)
        validate(self.native, corrected, reloc, self.report['keyboard_grid']['overlay'])
        wrong = bytearray(corrected); wrong[0x6000] ^= 1
        with self.assertRaises(ValueError): validate(self.native, bytes(wrong), reloc, self.report['keyboard_grid']['overlay'])
        with self.assertRaises(ValueError): install(corrected)

    def test_complete_source_sign_and_unchanged_native_model_palette_and_neighbouring_items(self):
        changed, report = sign_asset(self.native, self.rel, self.symbols)
        original = self.files[OBJECT].extract(self.base)
        expected = pack4(untile(self.rel[DATA_BASE+0x399280:DATA_BASE+0x399480], 32, 32, 4))
        self.assertEqual(changed[0x36D0:0x38D0], expected)
        self.assertEqual(changed[:0x36D0], original[:0x36D0])
        self.assertEqual(changed[0x38D0:], original[0x38D0:])
        self.assertEqual(report['changed_texture_bytes'], 197)
        self.assertEqual(report['matched_vertex_uses'], 12)
        with self.assertRaises(ValueError): sign_asset(self.native, self.rel[:-1], self.symbols)
        with self.assertRaises(ValueError): sign_asset(self.native, self.rel, self.symbols+b'\n')

    def test_complete_rom_ups_and_current_shared_editor_verification(self):
        before = copy.deepcopy(self.report)
        image, patch, report = build(self.native, self.base, self.report, self.rel, self.symbols)
        self.assertEqual(self.report, before)
        self.assertEqual(apply_ups(self.native, patch), image)
        self.assertEqual(sha256(image), report['output_sha256'])
        self.assertEqual(len(image), 32*1024*1024)
        files = by_vrom(image)
        self.assertEqual(set(files), set(self.files))
        for vrom, entry in self.files.items():
            if vrom not in (OBJECT, GRID, 0x19D40):
                self.assertEqual(files[vrom].extract(image), entry.extract(self.base), f'{vrom:08X}')
            self.assertEqual(files[vrom].index, entry.index)
            self.assertEqual(files[vrom].size, entry.size)
        for key, value in self.report.items():
            if key not in ('output_sha256', 'patch_sha256', 'replacement_files', 'release_status'):
                self.assertEqual(report[key], value, key)


if __name__ == '__main__':
    unittest.main()
