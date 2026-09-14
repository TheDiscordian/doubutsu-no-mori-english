"""Actual conditional collection, stable callers, and current cartridge retention."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import apply_ups, by_vrom, sha256
from v3_asset_loader import BLOB, CONFIG, MODULE
from v3_collection import CLOTHING_ABI, CODE, LIMIT

OUTPUT = ROOT/'build/v3-clothing-collection-01'
PARENT = ROOT/'build/v3-clothing-items-03'


class ClothingCollectionLogic(unittest.TestCase):
    def test_sanitized_four_player_clothing_and_furniture_ownership(self):
        with tempfile.TemporaryDirectory(prefix='v3-clothing-collection-') as directory:
            binary = Path(directory)/'test'
            subprocess.run(['cc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-DAF_V3_CLOTHING_PROFILE', '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_collection_test.c'), '-o', str(binary)],
                capture_output=True, text=True, check=True)
            result = subprocess.run([str(binary)], capture_output=True, text=True, check=True, timeout=20)
            self.assertIn('clearing, fallbacks, and rejection pass', result.stdout)


@unittest.skipUnless((OUTPUT/'build.json').exists(), 'Current clothing collection build required')
class ClothingCollectionCartridge(unittest.TestCase):
    def test_stable_entries_complete_retained_resources_and_reconstruction(self):
        report, old_report = (json.loads((p/'build.json').read_text()) for p in (OUTPUT, PARENT))
        rom, previous = ((p/'animal-forest-v3-asset-loader.z64').read_bytes() for p in (OUTPUT, PARENT))
        files = by_vrom(rom)
        blob, old = files[BLOB].extract(rom), by_vrom(previous)[BLOB].extract(previous)
        self.assertEqual(sha256(rom), report['output_sha256'])
        self.assertEqual(struct.unpack_from('>4I', files[MODULE].extract(rom), CONFIG),
                         (BLOB, 0xC000, zlib.crc32(blob[:0xC000]), CLOTHING_ABI))
        compiled = report['collection']['code']
        self.assertTrue(report['collection']['clothing_collection_enabled'])
        for name in ('af_v3_catalogue_record', 'af_v3_catalogue_owned', 'af_v3_catalogue_clear'):
            self.assertEqual(compiled['symbols'][name], old_report['collection']['code']['symbols'][name])
        self.assertEqual(compiled['symbols']['af_v3_item_type'],
                         report['furniture_items']['code']['symbols']['af_v3_item_type'])
        self.assertLessEqual(CODE+compiled['bytes'], LIMIT)
        self.assertEqual(sha256(blob[CODE:CODE+compiled['bytes']]), compiled['sha256'])
        restored = bytearray(blob)
        restored[4:8], restored[CODE:LIMIT] = old[4:8], old[CODE:LIMIT]
        self.assertEqual(restored, old)
        for key in ('save_runtime', 'clothing', 'save_codec'):
            self.assertEqual(report[key], old_report[key])
        for vrom, digest in old_report['changed_resources'].items():
            if int(vrom, 16) == MODULE: continue
            at = int(report['relocated_resources'].get(vrom, vrom), 16)
            self.assertEqual(sha256(files[at].extract(rom)), digest, vrom)
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native, (OUTPUT/'asset-loader.ups').read_bytes()), rom)


if __name__ == '__main__': unittest.main()
