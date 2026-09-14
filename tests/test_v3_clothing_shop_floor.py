"""Current clothing floor branches and complete retained furniture/garment resources."""
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
from v3_shop_floor import CODE, LIMIT, RAM, VROM
from v3_clothing_shop_floor import ABI, install

OUTPUT, PARENT = (ROOT/'build'/p for p in ('v3-clothing-shop-floor-01', 'v3-clothing-mannequin-02'))


@unittest.skipUnless((OUTPUT/'build.json').exists(), 'Current clothing floor build required')
class ClothingShopFloorCartridge(unittest.TestCase):
    def test_complete_owner_helper_delays_and_other_resources(self):
        report, parent = (json.loads((p/'build.json').read_text()) for p in (OUTPUT, PARENT))
        rom, before = ((p/'animal-forest-v3-asset-loader.z64').read_bytes() for p in (OUTPUT, PARENT))
        files, originals = by_vrom(rom), by_vrom(before)
        blob, old = files[BLOB].extract(rom), originals[BLOB].extract(before)
        floor, previous = report['shop_floor'], parent['shop_floor']
        self.assertEqual(blob[CODE:CODE+previous['code']['bytes']], old[CODE:CODE+previous['code']['bytes']])
        restored = bytearray(blob); restored[4:8], restored[CODE:LIMIT] = old[4:8], old[CODE:LIMIT]
        self.assertEqual(restored, old)
        self.assertEqual(sha256(blob[CODE:CODE+floor['code']['bytes']]), floor['code']['sha256'])
        self.assertLessEqual(CODE+floor['code']['bytes'], LIMIT)
        self.assertEqual(struct.unpack_from('>4I', files[MODULE].extract(rom), CONFIG),
                         (BLOB, 0xC000, zlib.crc32(blob[:0xC000]), ABI))
        owner, native = bytearray(files[VROM].extract(rom)), originals[VROM].extract(before)
        self.assertEqual(len(floor['clothing']['sites']), 3)
        for row in floor['clothing']['sites']:
            at, target = row['start']-RAM, floor['code']['symbols'][row['symbol']]
            self.assertEqual(struct.unpack_from('>I', owner, at)[0], 0x08000000 | (target >> 2 & 0x3FFFFFF))
            self.assertEqual(owner[at+4:at+8], native[at+4:at+8])
            owner[at:at+4] = native[at:at+4]
        self.assertEqual(owner, native)
        rebuilt, contract = install(native, blob[:0xC000], floor['clothing']['sites'], floor['code'], previous)
        self.assertEqual(rebuilt, files[VROM].extract(rom)); self.assertEqual(contract, floor['clothing'])
        self.assertEqual(report['clothing'], parent['clothing'])
        self.assertEqual(set(files), set(originals))
        for vrom in files:
            self.assertEqual(files[vrom].index, originals[vrom].index)
            self.assertEqual(files[vrom].size, originals[vrom].size)
            if vrom not in (BLOB, MODULE, VROM, 0x19D40):
                self.assertEqual(files[vrom].extract(rom), originals[vrom].extract(before), f'{vrom:08X}')
        self.assertEqual(sha256(rom), report['output_sha256'])
        native_rom = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native_rom, (OUTPUT/'asset-loader.ups').read_bytes()), rom)


if __name__ == '__main__': unittest.main()
