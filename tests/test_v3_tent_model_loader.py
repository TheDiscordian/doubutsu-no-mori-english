"""Current repaired loader, retained content, and complete-object callback gate."""
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
from aflib import by_vrom, sha256, n64_checksum
import v3_tent_model_loader as repair
import v3_optional_composition as composer


class TentLoader(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image, cls.report = composer.inputs()
        cls.base = (repair.BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.prior = json.loads((repair.BASE / 'build.json').read_bytes())
        cls.files, cls.old = by_vrom(cls.image), by_vrom(cls.base)

    def test_only_checked_loader_and_bridges_change(self):
        self.assertEqual(sha256(self.base), repair.BASE_SHA)
        self.assertEqual(self.files, self.old)
        blob = self.files[repair.BLOB].extract(self.image)
        before = self.old[repair.BLOB].extract(self.base)
        expanded = self.report['furniture']['expanded_tables']
        code = expanded['expanded_code']
        self.assertEqual(code['bytes'], 1760)
        self.assertIn('-DAF_V3_TENT_MODEL=1', code['flags'])
        self.assertEqual(sha256(blob[0x5800:0x5800 + code['bytes']]), code['sha256'])
        self.assertEqual(blob[0x5800 + code['bytes']:0x6000], bytes(0x800 - code['bytes']))
        restored = bytearray(blob)
        restored[0x5800:0x6000] = before[0x5800:0x6000]
        for row in expanded['public_entries']:
            at = row['entry'] - 0x80460000
            self.assertEqual(blob[at:at + 8].hex(), row['after'])
            self.assertEqual(struct.unpack('>II', blob[at:at + 8]), (repair.jump(code['symbols'][row['name']]), 0))
            restored[at:at + 8] = bytes.fromhex(row['before'])
        self.assertEqual(restored, before)
        self.assertEqual(self.report['save_runtime'], self.prior['save_runtime'])
        self.assertEqual(self.report['catalogue'], self.prior['catalogue'])
        self.assertEqual(self.report['import_storage'], self.prior['import_storage'])
        self.assertEqual(self.report['furniture']['imports'], self.prior['furniture']['imports'])

    def test_whole_current_rom_checksums_and_unchanged_resources(self):
        blob = self.files[repair.BLOB].extract(self.image)
        module = self.files[repair.MODULE].extract(self.image)
        self.assertEqual(struct.unpack_from('>4I', module, repair.CONFIG),
                         (repair.BLOB, 0xC000, zlib.crc32(blob[:0xC000]), 69))
        self.assertEqual(sha256(blob), self.report['blob_sha256'])
        self.assertEqual(struct.unpack_from('>2I', self.image, 16), n64_checksum(self.image))
        self.assertEqual(sha256(self.image), self.report['output_sha256'])
        restored = bytearray(self.image)
        restored[16:24] = self.base[16:24]
        for v in (repair.BLOB, repair.MODULE, repair.ROOM):
            e = self.files[v]
            restored[e.pstart:e.pstart + e.size] = self.base[e.pstart:e.pstart + e.size]
        self.assertEqual(restored, self.base)
        current_room = self.files[repair.ROOM].extract(self.image)
        old_room = self.old[repair.ROOM].extract(self.base)
        # The bank initializer precedes the changed DMA body and keeps its address.
        self.assertEqual(current_room, old_room)
        self.assertEqual(sha256(current_room), self.report['furniture']['expanded_tables']['output_sha256'])
        corrected = bytearray(module)
        corrected[repair.CONFIG + 8:repair.CONFIG + 12] = self.old[repair.MODULE].extract(self.base)[repair.CONFIG + 8:repair.CONFIG + 12]
        self.assertEqual(corrected, self.old[repair.MODULE].extract(self.base))

    def test_sanitized_actual_callback_dma_source(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-tent-dma-') as folder:
            binary = Path(folder) / 'test'
            subprocess.run(['cc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT / 'tests/v3_callback_furniture_dma_test.c'), '-o', str(binary)],
                check=True, capture_output=True)
            result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=20)
            self.assertIn('static/speed-bag retention, rejection, and failure handling pass', result.stdout)


if __name__ == '__main__':
    unittest.main()
