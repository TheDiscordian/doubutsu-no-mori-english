"""Current imported catalogue construction and isolated helper checks."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from aflib import apply_ups, by_vrom, sha256
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
from v3_asset_loader import compose
from v3_catalogue import OWNER, PARENT, RAM, RELOC, SIZE, TABLE, VROM, sources

OUTPUT = ROOT / 'build/v3-catalogue-04'


class CatalogueHostTests(unittest.TestCase):
    def test_sanitized_helpers(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-catalogue-test-') as directory:
            binary = Path(directory) / 'test'
            subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT / 'tests/v3_catalogue_test.c'), '-o', str(binary)], check=True, capture_output=True)
            result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=20)
            self.assertIn('eligibility, fallbacks, and rejection pass', result.stdout)


@unittest.skipUnless((OUTPUT / 'build.json').exists(), 'Current catalogue cartridge required')
class CatalogueCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUTPUT / 'build.json').read_text())
        cls.cat = cls.report['catalogue']
        cls.rom = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        cls.files = by_vrom(cls.rom)
        cls.old, cls.old_rel, cls.parent = sources(cls.base)
        cls.data, cls.rel = (cls.files[v].extract(cls.rom) for v in (VROM, RELOC))

    def test_additive_table_and_real_pool(self):
        at = self.cat['code']['symbols']['af_v3_catalogue_order'] - RAM
        table = self.data[at:at + 438 * 4]
        self.assertEqual(table[:436 * 4], self.old[TABLE - RAM:TABLE - RAM + 436 * 4])
        self.assertEqual(struct.unpack('>4H', table[-8:]), (2185, 0, 2222, 0))
        self.assertEqual([r['donor_position'] for r in self.cat['imports']], [195, 202])
        self.assertEqual([r['ordinary_shop_list'] for r in self.cat['imports']], ['ftr_listC', 'ftr_listA'])
        self.assertLessEqual(self.cat['total_rows'], self.cat['row_capacity'])
        self.assertLessEqual(self.cat['conservative_pool_required'], self.cat['pool_reserved'])
        self.assertEqual(self.cat['additional_pool_allocation'], 0)
        self.assertEqual(len(self.data) % 16, 0)
        self.assertEqual(len(self.rel) % 16, 0)
        self.assertEqual(self.data[SIZE:], (OUTPUT / 'catalogue/code.bin').read_bytes())

    def test_native_relocation_and_only_declared_edits(self):
        allowed = {i for p in self.cat['patches'] for i in range(p['address'] - RAM, p['address'] - RAM + 4)}
        for base in (0x801A0010, 0x802F8010, 0x803D0010):
            before = relocate_verified_data(Image(RAM, SIZE, struct.unpack_from('>5I', self.old_rel)),
                                            self.old, self.old_rel, base)
            after = relocate_verified_data(Image(RAM, len(self.data), struct.unpack_from('>5I', self.rel)),
                                           self.data, self.rel, base)
            self.assertTrue(all(a == b or i in allowed for i, (a, b) in enumerate(zip(before, after))))
            target = self.cat['code']['symbols']['af_v3_catalogue_type'] - RAM + base
            self.assertEqual(struct.unpack_from('>II', after, 0xA14),
                             (0x08000000 | (target >> 2 & 0x3FFFFFF), 0))
        parent = self.files[PARENT].extract(self.rom)
        self.assertEqual(struct.unpack_from('>4I', parent, OWNER),
                         (VROM, VROM + len(self.data), RAM, RAM + len(self.data)))
        self.assertFalse(self.cat['save_format_changed'])
        self.assertEqual(self.report['save_runtime']['code']['sha256'],
                         '21bb3b82007790f77e9b9e6d4445974474726658bea3e3158778f56f477368ab')

    def test_resized_composition_and_exact_import_free_v2(self):
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])
        changes = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['changed_resources']}
        added = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['added_resources']}
        self.assertEqual(compose(self.native, self.base, changes, added, resized=(VROM, RELOC)), self.rom)
        with self.assertRaises(ValueError):
            compose(self.native, self.base, changes, added)
        self.assertEqual(compose(self.native, self.base, {}, {}), self.base)
        self.assertEqual(apply_ups(self.native, (OUTPUT / 'asset-loader.ups').read_bytes()), self.rom)


if __name__ == '__main__':
    unittest.main()
