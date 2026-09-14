"""Installed player-animation index window and retained clothing menu resources."""
import json
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import apply_ups, by_vrom, sha256
from v3_asset_loader import BLOB, CONFIG, MODULE
from v3_clothing_menu import CODE, LIMIT
from v3_clothing_wear import ABI, SPEC, START, END, WINDOW, install
from v3_furniture_menu import VROM as TAG, RAM as TAG_RAM
from tests import test_v3_clothing_menu as menu_tests

OUTPUT, PARENT = (ROOT/'build'/p for p in ('v3-clothing-wear-01', 'v3-clothing-menu-02'))


class ClothingWearLogic(menu_tests.ClothingMenuLogic):
    pass


@unittest.skipUnless((OUTPUT/'build.json').exists(), 'Current clothing wearing build required')
class ClothingWearCartridge(unittest.TestCase):
    def test_complete_player_window_and_retained_menu_identity_save_artwork(self):
        report, parent = (json.loads((p/'build.json').read_text()) for p in (OUTPUT, PARENT))
        rom, previous = ((p/'animal-forest-v3-asset-loader.z64').read_bytes() for p in (OUTPUT, PARENT))
        files, originals = by_vrom(rom), by_vrom(previous)
        blob, old = files[BLOB].extract(rom), originals[BLOB].extract(previous)
        menu, wear = report['clothing']['menu'], report['clothing']['wearing']
        self.assertEqual(sha256(rom), report['output_sha256'])
        self.assertEqual(struct.unpack_from('>4I', files[MODULE].extract(rom), CONFIG),
                         (BLOB, 0xC000, zlib.crc32(blob[:0xC000]), ABI))
        self.assertLessEqual(CODE+menu['code']['bytes'], LIMIT)
        self.assertEqual(sha256(blob[CODE:CODE+menu['code']['bytes']]), menu['code']['sha256'])
        restored = bytearray(blob)
        restored[4:8], restored[CODE:LIMIT] = old[4:8], old[CODE:LIMIT]
        self.assertEqual(restored, old)
        player = bytearray(files[SPEC.vrom].extract(rom))
        self.assertEqual(sha256(player), wear['output_sha256'])
        self.assertEqual(player[START-SPEC.ram:END-SPEC.ram].hex(), wear['after'])
        player[START-SPEC.ram:END-SPEC.ram] = WINDOW
        self.assertEqual(player, originals[SPEC.vrom].extract(previous))
        tag = bytearray(files[TAG].extract(rom))
        for row in menu['sites']:
            target = parent['clothing']['menu']['code']['symbols'][row['symbol']]
            struct.pack_into('>2I', tag, row['start']-TAG_RAM, 0x08000000 | (target >> 2 & 0x3FFFFFF), 0)
        self.assertEqual(tag, originals[TAG].extract(previous))
        for key, value in parent['clothing'].items():
            if key != 'menu': self.assertEqual(report['clothing'][key], value)
        for vrom, digest in parent['changed_resources'].items():
            if int(vrom, 16) in (MODULE, TAG): continue
            at = int(report['relocated_resources'].get(vrom, vrom), 16)
            self.assertEqual(sha256(files[at].extract(rom)), digest, vrom)
        base = (ROOT/'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        changes, rebuilt = install(base, menu['code'])
        self.assertEqual(changes[SPEC.vrom], files[SPEC.vrom].extract(rom))
        self.assertEqual(rebuilt, wear)
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native, (OUTPUT/'asset-loader.ups').read_bytes()), rom)


if __name__ == '__main__': unittest.main()
