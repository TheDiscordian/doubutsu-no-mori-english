"""Pinned donor HRA properties, safe relocation, and exact current composition."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom, sha256
from v3_asset_loader import compose
import v3_hra as hra

OUTPUT = ROOT / 'build/v3-hra-03'


@unittest.skipUnless((OUTPUT / 'build.json').exists(), 'Current HRA cartridge required')
class HRATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUTPUT / 'build.json').read_text())
        cls.hra = cls.report['hra']
        cls.rom = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.base = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        cls.native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.files = by_vrom(cls.rom)

    def test_actual_donor_subsets_preserve_native_properties(self):
        rel = (ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        furniture = self.report['furniture']['imports']
        native, _ = hra.sources(self.base)
        for subset in ([], furniture[:1], furniture[1:], furniture, furniture[::-1]):
            table, records = hra.table(self.base, rel, symbols, subset)
            self.assertEqual(table[:947 * 4], native[hra.TABLE - hra.RAM:hra.TABLE - hra.RAM + 947 * 4])
            chosen = {r['runtime_index'] for r in records}
            self.assertEqual(len(table), hra.COUNT * 4)
            for i in range(947, hra.COUNT):
                self.assertEqual(table[i * 4:i * 4 + 4], bytes.fromhex(
                    ('40050400' if i == 1161 else '40050000') if i in chosen else
                    ('D4002000' if i == 947 else 'FC000000')))
        with self.assertRaises(ValueError):
            hra.table(self.base, rel, symbols, furniture * 2)
        damaged = bytearray(rel); damaged[-1] ^= 1
        with self.assertRaises(ValueError):
            hra.table(self.base, damaged, symbols, furniture)

    def test_complete_owned_changes_and_translated_letter_retention(self):
        old, _ = hra.sources(self.base)
        expected = bytearray(old)
        for patch in self.hra['patches']:
            at = patch['address'] - hra.RAM
            self.assertEqual(struct.unpack_from('>I', expected, at)[0], patch['before'])
            struct.pack_into('>I', expected, at, patch['after'])
        actual = self.files[hra.NEW_VROM].extract(self.rom)
        self.assertEqual(actual[:hra.SIZE], expected)
        self.assertEqual(actual[hra.SIZE:hra.START], bytes(hra.START - hra.SIZE))
        self.assertEqual(actual[hra.START:], (OUTPUT / 'hra/code.bin').read_bytes())
        self.assertEqual(actual[0x468:0x6C4], old[0x468:0x6C4])
        self.assertEqual(self.hra['sites'], hra.inspect(self.base))
        self.assertEqual(len(self.hra['sites']), 40)
        self.assertEqual(len(self.hra['pointer_changes']), 48)
        before = by_vrom(self.base)[CODE_VROM].extract(self.base)
        code = self.files[CODE_VROM].extract(self.rom)
        for p in self.hra['scheduler']:
            self.assertEqual(struct.unpack_from('>I', before, p['address'] - CODE_RAM)[0], p['before'])
            self.assertEqual(struct.unpack_from('>I', code, p['address'] - CODE_RAM)[0], p['after'])
        at = 0x8009CF28 - CODE_RAM
        self.assertEqual(before[at:at + 68], code[at:at + 68])
        self.assertEqual(self.files[hra.NEW_RELOC].index, self.files[hra.NEW_VROM].index + 1)
        self.assertEqual(self.files[hra.NEW_VROM].index, by_vrom(self.base)[hra.VROM].index)

    def test_current_and_import_free_composition(self):
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])
        moved = {int(v, 16): int(t, 16) for v, t in self.report['relocated_resources'].items()}
        changes = {int(v, 16): self.files[moved.get(int(v, 16), int(v, 16))].extract(self.rom)
                   for v in self.report['changed_resources']}
        added = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['added_resources']}
        resized = tuple(int(v, 16) for v in self.report['resized_resources'])
        self.assertEqual(compose(self.native, self.base, changes, added, resized=resized, relocated=moved), self.rom)
        self.assertEqual(compose(self.native, self.base, {}, {}), self.base)
        with self.assertRaises(ValueError):
            compose(self.native, self.base, changes, added, resized=resized, relocated={hra.VROM: 0x1000})
        self.assertEqual(apply_ups(self.native, (OUTPUT / 'asset-loader.ups').read_bytes()), self.rom)


if __name__ == '__main__':
    unittest.main()
