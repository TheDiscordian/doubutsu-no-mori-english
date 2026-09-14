"""V3 collection ownership, installed native paths, and retained composition."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom, sha256
from v3_asset_loader import BLOB, CONFIG, MODULE, compose
from v3_collection import ABI, BLOB_SIZE, BRIDGE, CODE, ENTRIES, LIMIT, POSSESSION_SHA

OUTPUT = ROOT / 'build/v3-collection-01'


class CollectionHostTests(unittest.TestCase):
    def test_sanitized_ownership_clear_fallback_and_rejection(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-collection-tests-') as directory:
            binary = Path(directory) / 'test'
            subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT / 'tests/v3_collection_test.c'), '-o', str(binary)], check=True, capture_output=True)
            result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=20)
            self.assertIn('clearing, fallbacks, and rejection pass', result.stdout)


@unittest.skipUnless((OUTPUT / 'build.json').exists(), 'Current collection cartridge required')
class CollectionCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUTPUT / 'build.json').read_text())
        cls.collection = cls.report['collection']
        cls.rom = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        cls.files, cls.original = by_vrom(cls.rom), by_vrom(cls.base)
        cls.blob = cls.files[BLOB].extract(cls.rom)[:BLOB_SIZE]

    def test_complete_native_owners_bridges_and_acquisition(self):
        code, old = self.files[CODE_VROM].extract(self.rom), self.original[CODE_VROM].extract(self.base)
        jump = lambda target: 0x08000000 | (target >> 2 & 0x3FFFFFF)
        for i, (address, size, name, prologue, digest) in enumerate(ENTRIES):
            at = address - CODE_RAM
            self.assertEqual(sha256(old[at:at + size]), digest)
            self.assertEqual(struct.unpack_from('>II', code, at),
                             (jump(self.collection['code']['symbols'][name]), 0))
            self.assertEqual(code[at + 8:at + size], old[at + 8:at + size])
            self.assertEqual(struct.unpack_from('>4I', self.blob, BRIDGE + i * 16),
                             (*prologue, jump(address + 8), 0))
        self.assertEqual(sha256(code[0x800B8B08 - CODE_RAM:0x800B8BE4 - CODE_RAM]), POSSESSION_SHA)

    def test_code_layout_and_retained_save_format(self):
        helper = (OUTPUT / 'collection/code.bin').read_bytes()
        self.assertLessEqual(CODE + len(helper), LIMIT)
        self.assertEqual(self.blob[CODE:CODE + len(helper)], helper)
        self.assertEqual(sha256(helper), self.collection['code']['sha256'])
        for part, offset in (('save_codec', 0xB400), ('save_runtime', 0x9200)):
            data = self.report[part]['code']
            self.assertEqual(sha256(self.blob[offset:offset + data['bytes']]), data['sha256'])
        self.assertEqual(self.report['save_runtime']['code']['sha256'],
                         '21bb3b82007790f77e9b9e6d4445974474726658bea3e3158778f56f477368ab')
        self.assertFalse(self.collection['save_format_changed'])
        self.assertEqual(struct.unpack_from('>4I', self.files[MODULE].extract(self.rom), CONFIG),
                         (BLOB, BLOB_SIZE, zlib.crc32(self.blob), ABI))
        for offset in (0x7FF0, 0xBFF0):
            self.assertEqual(self.blob[offset:offset + 16], bytes.fromhex('AF33C0DE') * 4)
        for row in self.report['furniture']['imports']:
            at = int(row['object_vrom'], 16) - BLOB
            self.assertEqual(sha256(self.files[BLOB].extract(self.rom)[at:at + row['object_bytes']]), row['object_sha256'])

    def test_current_composition_and_import_free_retention(self):
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])
        changes = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['changed_resources']}
        added = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['added_resources']}
        self.assertEqual(compose(self.native, self.base, changes, added), self.rom)
        self.assertEqual(compose(self.native, self.base, {}, {}), self.base)
        self.assertEqual(apply_ups(self.native, (OUTPUT / 'asset-loader.ups').read_bytes()), self.rom)


if __name__ == '__main__':
    unittest.main()
