"""Complete mannequin owner installation and unchanged surrounding game resources."""
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
from v3_shop_mannequin import ABI, CODE, LIMIT, RAM, VROM, inspect, install

OUTPUT, PARENT = (ROOT/'build'/p for p in ('v3-clothing-mannequin-02', 'v3-clothing-stock-01'))


@unittest.skipUnless((OUTPUT/'build.json').exists(), 'Current mannequin build required')
class ShopMannequinCartridge(unittest.TestCase):
    def test_complete_owner_and_retained_stock_artwork_save_resources(self):
        report, parent = (json.loads((p/'build.json').read_text()) for p in (OUTPUT, PARENT))
        rom, before = ((p/'animal-forest-v3-asset-loader.z64').read_bytes() for p in (OUTPUT, PARENT))
        files, originals = by_vrom(rom), by_vrom(before)
        blob, old = files[BLOB].extract(rom), originals[BLOB].extract(before)
        mannequin = report['clothing']['mannequin']
        compiled = mannequin['code']
        helper = blob[CODE:CODE+compiled['bytes']]
        self.assertEqual(sha256(helper), compiled['sha256'])
        self.assertLessEqual(CODE+len(helper), LIMIT)
        self.assertEqual(old[CODE:LIMIT], bytes(LIMIT-CODE))
        restored = bytearray(blob); restored[4:8], restored[CODE:LIMIT] = old[4:8], old[CODE:LIMIT]
        self.assertEqual(restored, old)
        self.assertEqual(struct.unpack_from('>4I', files[MODULE].extract(rom), CONFIG),
                         (BLOB, 0xC000, zlib.crc32(blob[:0xC000]), ABI))
        base = (ROOT/'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        source, _, rows = inspect(base)
        self.assertEqual(len(rows), 6)
        owner = bytearray(files[VROM].extract(rom))
        for row in rows:
            at = row['start']-RAM
            target = compiled['symbols'][row['symbol']]
            self.assertEqual(owner[at:at+16], struct.pack('>4I', 0x08000000 | (target >> 2 & 0x3FFFFFF), 0, 0, 0))
            self.assertEqual(owner[at+16:at+20], source[at+16:at+20])
            owner[at:at+16] = source[at:at+16]
        self.assertEqual(owner, source)
        self.assertEqual(set(files), set(originals))
        for vrom in files:
            self.assertEqual(files[vrom].index, originals[vrom].index)
            self.assertEqual(files[vrom].size, originals[vrom].size)
            if vrom not in (BLOB, MODULE, VROM, 0x19D40):
                self.assertEqual(files[vrom].extract(rom), originals[vrom].extract(before), f'{vrom:08X}')
        for key, value in parent['clothing'].items(): self.assertEqual(report['clothing'][key], value, key)
        rebuilt_blob = bytearray(blob[:0xC000]); rebuilt_blob[CODE:LIMIT] = bytes(LIMIT-CODE)
        changes, rebuilt = install(base, rebuilt_blob, helper, compiled, report['furniture_room']['code'], report['villager_selection'])
        self.assertEqual(rebuilt, mannequin)
        self.assertEqual(rebuilt_blob, blob[:0xC000])
        self.assertEqual(changes[VROM], files[VROM].extract(rom))
        with self.assertRaises(ValueError):
            install(base, rebuilt_blob, helper, compiled, report['furniture_room']['code'], report['villager_selection'])
        self.assertEqual(sha256(rom), report['output_sha256'])
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native, (OUTPUT/'asset-loader.ups').read_bytes()), rom)


if __name__ == '__main__': unittest.main()
