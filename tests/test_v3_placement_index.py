"""Complete current placement patch and retained assembled V3 dependencies."""
import json
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from aflib import CODE_VROM, apply_ups, by_vrom, sha256
from v3_asset_loader import BLOB, CONFIG, MODULE, compose
import v3_furniture_menu as menu

OUTPUT = ROOT / 'build/v3-placement-index-01'


@unittest.skipUnless((OUTPUT / 'build.json').exists(), 'Current placement cartridge required')
class PlacementIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUTPUT / 'build.json').read_text())
        cls.rom = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.base = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        cls.files, cls.original = by_vrom(cls.rom), by_vrom(cls.base)

    def test_complete_tag_changes_and_relocation_safety(self):
        before = self.original[menu.VROM].extract(self.base)
        root = self.original[menu.ROOT_VROM].extract(self.base)
        reloc = self.original[menu.RELOC].extract(self.base)
        code = self.files[CODE_VROM].extract(self.rom)
        report = self.report['furniture_menu']
        self.assertEqual(menu.inspect(code, root, before, reloc), report['sites'])
        expected = bytearray(before)
        for row in report['sites'] + [report['placement_index']]:
            target = report['code']['symbols'][row['symbol']]
            expected[row['start'] - menu.RAM:row['end'] - menu.RAM] = (
                struct.pack('>I', 0x08000000 | (target >> 2 & 0x3FFFFFF)) +
                bytes(row['end'] - row['start'] - 4))
        self.assertEqual(self.files[menu.VROM].extract(self.rom), expected)
        self.assertEqual(self.files[menu.RELOC].extract(self.rom), reloc)
        damaged = bytearray(before)
        damaged[menu.INDEX_START - menu.RAM] ^= 1
        with self.assertRaises(ValueError):
            menu.inspect(code, root, damaged, reloc)

    def test_query_guards_layout_and_unchanged_dependencies(self):
        blob = self.files[BLOB].extract(self.rom)[:0xC000]
        helper = (OUTPUT / 'menu/code.bin').read_bytes()
        self.assertEqual(blob[menu.CODE:menu.CODE + len(helper)], helper)
        self.assertLessEqual(menu.CODE + len(helper), 0xAB00)
        self.assertEqual(self.report['furniture_menu']['code']['symbols']['af_v3_room_query'], 0x804680B8)
        self.assertEqual(struct.unpack_from('>4I', self.files[MODULE].extract(self.rom), CONFIG),
                         (BLOB, 0xC000, zlib.crc32(blob), 21))
        self.assertEqual(blob[-16:], bytes.fromhex('AF33C0DE') * 4)
        parent = json.loads((ROOT / 'build/v3-feng-shui-02/build.json').read_text())
        for vrom, digest in parent['changed_resources'].items():
            if int(vrom, 16) in (BLOB, MODULE, menu.VROM):
                continue
            actual = int(self.report['relocated_resources'].get(vrom, vrom), 16)
            self.assertEqual(sha256(self.files[actual].extract(self.rom)), digest)
        for part in ('room', 'hra', 'feng_shui'):
            self.assertEqual((OUTPUT / part / 'code.bin').read_bytes(),
                             (ROOT / 'build/v3-feng-shui-02' / part / 'code.bin').read_bytes())

    def test_complete_composition_patch_and_import_free_v2(self):
        native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        moved = {int(v, 16): int(t, 16) for v, t in self.report['relocated_resources'].items()}
        changes = {int(v, 16): self.files[moved.get(int(v, 16), int(v, 16))].extract(self.rom)
                   for v in self.report['changed_resources']}
        added = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['added_resources']}
        resized = tuple(int(v, 16) for v in self.report['resized_resources'])
        self.assertEqual(compose(native, self.base, changes, added, resized=resized, relocated=moved), self.rom)
        self.assertEqual(compose(native, self.base, {}, {}), self.base)
        self.assertEqual(apply_ups(native, (OUTPUT / 'asset-loader.ups').read_bytes()), self.rom)
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])


if __name__ == '__main__':
    unittest.main()
