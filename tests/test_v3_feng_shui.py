"""Actual donor feng shui rules and checked native evaluator composition."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, apply_ups
from v3_asset_loader import compose
import v3_feng_shui as feng

OUTPUT = ROOT / 'build/v3-feng-shui-02'


@unittest.skipUnless((OUTPUT / 'build.json').exists(), 'Current feng shui cartridge required')
class FengShuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUTPUT / 'build.json').read_text())
        cls.feng = cls.report['feng_shui']
        cls.rom = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.base = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        cls.files = by_vrom(cls.rom)

    def test_selected_metadata_and_actual_native_donor_rules(self):
        donor = (ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        furniture = self.report['furniture']['imports']
        old, _ = feng.sources(self.base)
        for subset in ([], furniture[:1], furniture[1:], furniture, furniture[::-1]):
            data, records = feng.table(self.base, donor, symbols, subset)
            self.assertEqual(data[:947 * 2], old[0x640:0x640 + 947 * 2])
            chosen = {r['runtime_index'] for r in records}
            for i in range(947, feng.COUNT):
                self.assertEqual(data[i * 2:i * 2 + 2], bytes((2 if i == 1161 else 3, 0)) if i in chosen else bytes(2))
        with self.assertRaises(ValueError):
            feng.table(self.base, donor, symbols, furniture * 2)

    def test_only_declared_native_patches_and_allocation(self):
        old, _ = feng.sources(self.base)
        expected = bytearray(old)
        for p in self.feng['patches']:
            at = p['address'] - feng.RAM
            self.assertEqual(struct.unpack_from('>I', expected, at)[0], p['before'])
            struct.pack_into('>I', expected, at, p['after'])
        actual = self.files[feng.NEW_VROM].extract(self.rom)
        self.assertEqual(actual[:feng.SIZE], expected)
        self.assertEqual(actual[feng.SIZE:], (OUTPUT / 'feng_shui/code.bin').read_bytes())
        self.assertEqual(sha256(actual), self.feng['output_sha256'])
        self.assertLessEqual(len(actual), 0x2000)
        code = self.files[CODE_VROM].extract(self.rom)
        for p in self.feng['scheduler']:
            self.assertEqual(struct.unpack_from('>I', code, p['address'] - CODE_RAM)[0], p['after'])
        self.assertEqual(self.files[feng.NEW_VROM].index, by_vrom(self.base)[feng.VROM].index)
        self.assertEqual(self.files[feng.NEW_RELOC].index, self.files[feng.NEW_VROM].index + 1)
        damaged = bytearray(code)
        with self.assertRaises(ValueError):
            feng.install(self.base, damaged, actual[feng.SIZE:], self.feng['code'],
                         (OUTPUT / 'feng-metadata.bin').read_bytes(), self.feng['imports'])

    def test_current_composition_preserves_hra_and_import_free_v2(self):
        native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        moved = {int(v, 16): int(t, 16) for v, t in self.report['relocated_resources'].items()}
        changes = {int(v, 16): self.files[moved.get(int(v, 16), int(v, 16))].extract(self.rom)
                   for v in self.report['changed_resources']}
        added = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['added_resources']}
        resized = tuple(int(v, 16) for v in self.report['resized_resources'])
        self.assertEqual(compose(native, self.base, changes, added, resized=resized, relocated=moved), self.rom)
        self.assertEqual(compose(native, self.base, {}, {}), self.base)
        self.assertEqual(apply_ups(native, (OUTPUT / 'asset-loader.ups').read_bytes()), self.rom)
        previous = json.loads((ROOT / 'build/v3-hra-03/build.json').read_text())['hra']
        # Generated assembly embeds its fresh build-directory input path. The
        # resulting code, metadata, relocation, and all other facts stay fixed.
        self.assertEqual({k: v for k, v in self.report['hra'].items() if k != 'generated_hooks_sha256'},
                         {k: v for k, v in previous.items() if k != 'generated_hooks_sha256'})


if __name__ == '__main__':
    unittest.main()
