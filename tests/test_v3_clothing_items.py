"""Selected garment metadata, independent identities, and installed readers."""
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
from v3_clothing_items import ABI, install
from v3_save_clothing import VROM

OUTPUT = ROOT/'build/v3-clothing-items-03'


class ClothingItemsLogic(unittest.TestCase):
    def test_sanitized_actual_resource_profile_and_shared_consumers(self):
        with tempfile.TemporaryDirectory(prefix='v3-clothing-items-') as directory:
            binary = Path(directory)/'test'
            subprocess.run(['cc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT/'tests/fixtures/v3_clothing_items.c'), '-o', str(binary)],
                capture_output=True, text=True, check=True)
            result = subprocess.run([str(binary)], capture_output=True, text=True, check=True, timeout=20)
            self.assertIn('original fallback, and guards pass', result.stdout)


@unittest.skipUnless((OUTPUT/'build.json').exists(), 'Current clothing-item build required')
class ClothingItemsCartridge(unittest.TestCase):
    def test_guarded_dispatch_and_retained_code_artwork_profile(self):
        report = json.loads((OUTPUT/'build.json').read_text())
        parent = json.loads((ROOT/'build/v3-clothing-save-02/build.json').read_text())
        rom = (OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        previous = (ROOT/'build/v3-clothing-save-02/animal-forest-v3-asset-loader.z64').read_bytes()
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        files = by_vrom(rom)
        blob, old = files[BLOB].extract(rom), by_vrom(previous)[BLOB].extract(previous)
        self.assertEqual(sha256(rom), report['output_sha256'])
        self.assertEqual(struct.unpack_from('>4I', files[MODULE].extract(rom), CONFIG),
                         (BLOB, 0xC000, zlib.crc32(blob[:0xC000]), ABI))
        restored = bytearray(blob[:0xC000])
        for hook in report['clothing']['item_readers']['hooks']:
            at = int(hook['entry'], 16)-0x80460000
            self.assertEqual(restored[at:at+8].hex(), hook['after'])
            restored[at:at+8] = bytes.fromhex(hook['before'])
        compiled = report['clothing']['save_extension']['code']
        install(restored, compiled, report['furniture_items']['code'], report['asset'])
        self.assertEqual(restored, blob[:0xC000])
        with self.assertRaises(ValueError): install(restored, compiled, report['furniture_items']['code'], report['asset'])
        for hook in report['clothing']['item_readers']['hooks']:
            at = int(hook['entry'], 16)-0x80460000
            restored[at:at+8] = bytes.fromhex(hook['before'])
        restored[4:8], restored[0xE0:0xF0] = old[4:8], old[0xE0:0xF0]
        self.assertEqual(restored, old[:0xC000])
        # Shared save-code instructions remain intact at the start of the
        # extended resource; the added item readers follow that exact code.
        count = parent['clothing']['save_extension']['code']['bytes']
        self.assertEqual(blob[VROM-BLOB:VROM-BLOB+count], old[VROM-BLOB:VROM-BLOB+count])
        self.assertEqual(blob[0xC000:VROM-BLOB], old[0xC000:VROM-BLOB])
        self.assertEqual(report['save_runtime'], parent['save_runtime'])
        for vrom, digest in parent['changed_resources'].items():
            if int(vrom, 16) == MODULE: continue
            actual = int(report['relocated_resources'].get(vrom, vrom), 16)
            self.assertEqual(sha256(files[actual].extract(rom)), digest, vrom)
        self.assertLessEqual(len(blob), 0x10000)
        self.assertEqual(apply_ups(native, (OUTPUT/'asset-loader.ups').read_bytes()), rom)


if __name__ == '__main__': unittest.main()
