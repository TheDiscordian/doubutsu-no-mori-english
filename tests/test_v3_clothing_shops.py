"""Current clothing shop category, original fallbacks, and cartridge retention."""
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
from v3_asset_loader import BLOB, MODULE, CONFIG
from v3_shops import CLOTHING_ABI, CODE, LIMIT

OUTPUT, PARENT = (ROOT/'build'/p for p in ('v3-clothing-shop-category-01', 'v3-clothing-wear-01'))


class ClothingShopLogic(unittest.TestCase):
    def test_sanitized_clothing_and_original_variants(self):
        with tempfile.TemporaryDirectory(prefix='v3-clothing-shop-') as directory:
            for clothing in (False, True):
                with self.subTest(clothing=clothing):
                    binary = Path(directory)/('clothing' if clothing else 'original')
                    subprocess.run(['cc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                        '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                        *(['-DAF_V3_CLOTHING_PROFILE=1'] if clothing else []),
                        str(ROOT/'tests/v3_shops_test.c'), '-o', str(binary)],
                        capture_output=True, text=True, check=True)
                    result = subprocess.run([str(binary)], capture_output=True, text=True,
                                            check=True, timeout=20)
                    self.assertIn('original fallbacks pass', result.stdout)


@unittest.skipUnless((OUTPUT/'build.json').exists(), 'Current clothing shop category build required')
class ClothingShopCartridge(unittest.TestCase):
    def test_installed_category_and_complete_retained_resources(self):
        report, parent = (json.loads((p/'build.json').read_text()) for p in (OUTPUT, PARENT))
        rom, previous = ((p/'animal-forest-v3-asset-loader.z64').read_bytes() for p in (OUTPUT, PARENT))
        files, originals = by_vrom(rom), by_vrom(previous)
        blob, old = files[BLOB].extract(rom), originals[BLOB].extract(previous)
        helper = report['shops']['code']
        self.assertEqual(sha256(rom), report['output_sha256'])
        self.assertTrue(report['shops']['clothing_category_enabled'])
        self.assertEqual(helper['symbols']['af_v3_item_type'], 0x8046744C)
        self.assertLessEqual(CODE+helper['bytes'], LIMIT)
        self.assertEqual(sha256(blob[CODE:CODE+helper['bytes']]), helper['sha256'])
        self.assertEqual(struct.unpack_from('>4I', files[MODULE].extract(rom), CONFIG),
                         (BLOB, 0xC000, zlib.crc32(blob[:0xC000]), CLOTHING_ABI))
        restored = bytearray(blob)
        restored[4:8], restored[CODE:LIMIT] = old[4:8], old[CODE:LIMIT]
        self.assertEqual(restored, old)
        self.assertEqual(set(files), set(originals))
        for vrom in files:
            if vrom not in (BLOB, MODULE):
                self.assertEqual(files[vrom].extract(rom), originals[vrom].extract(previous), f'{vrom:08X}')
        for key in ('clothing', 'collection', 'save_codec', 'save_runtime'):
            if key in parent: self.assertEqual(report[key], parent[key], key)
        self.assertEqual(report['shops']['imports'], parent['shops']['imports'])
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native, (OUTPUT/'asset-loader.ups').read_bytes()), rom)


if __name__ == '__main__': unittest.main()
