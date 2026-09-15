"""Changed storage/lookup checks; do not replay historical candidate builds."""
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
from aflib import CODE_RAM, CODE_VROM, DMA_START, DMA_END, by_vrom, sha256, n64_checksum
from v3_asset_loader import BLOB, MODULE, CONFIG
import v3_import_storage as s

OUTPUT = ROOT / 'build/v3-import-storage-02'


class SparseHost(unittest.TestCase):
    def test_sanitized_sparse_readers_and_complete_initialization(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-sparse-') as directory:
            for name in ('v3_sparse_items_test.c', 'v3_sparse_tables_test.c'):
                binary = Path(directory) / name
                subprocess.run(['cc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                    str(ROOT / 'tests' / name), '-o', str(binary)], check=True, capture_output=True)
                result = subprocess.run([str(binary)], check=True, capture_output=True, timeout=20)
                self.assertIn(b'pass', result.stdout)


class SparseCartridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report = json.loads((OUTPUT / 'build.json').read_bytes())
        cls.base = (s.BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.prior = json.loads((s.BASE / 'build.json').read_bytes())
        cls.files, cls.old = by_vrom(cls.image), by_vrom(cls.base)
        cls.blob, cls.before = cls.files[BLOB].extract(cls.image), cls.old[BLOB].extract(cls.base)

    def test_complete_rows_and_uninstalled_zero_slots(self):
        rows, items = bytearray(80 * 1024), bytearray(32 * 1024)
        for n, row in enumerate(self.report['furniture']['imports']):
            i = s.slot(int(row['item_id'], 16))
            rows[i * 80:(i + 1) * 80] = self.before[0x1D9000 + n * 80:0x1D9000 + (n + 1) * 80]
            self.assertEqual(int(row['profile_ram'], 16), s.ROWS_RAM + i * 80 + 8)
            self.assertEqual(self.blob[0x5800 + row['runtime_index'] * 4:0x5804 + row['runtime_index'] * 4], bytes(4))
        for n in range(26):
            row = self.before[0x1D9800 + n * 32:0x1D9820 + n * 32]
            i = s.slot(int.from_bytes(row[2:4], 'big'))
            items[i * 32:(i + 1) * 32] = row
        self.assertEqual(self.blob[s.ROWS:s.ITEMS], rows)
        self.assertEqual(self.blob[s.ITEMS:s.TABLE_END], items)
        self.assertEqual(self.report['save_runtime'], self.prior['save_runtime'])
        self.assertEqual(self.blob[0x20:0xE0], self.before[0x20:0xE0])

    def test_checked_package_and_fixed_public_dispatch(self):
        package = self.blob[s.PACKAGE:s.PACKAGE + s.PACKAGE_SIZE]
        self.assertEqual(struct.unpack_from('>4I', package), (0x41464133, 1, s.PACKAGE_SIZE, 20))
        self.assertEqual(package[-16:], bytes.fromhex('AFACC0DE') * 4)
        self.assertEqual(struct.unpack_from('>4I', self.blob, 0xF0),
            (BLOB + s.PACKAGE, s.PACKAGE_SIZE, zlib.crc32(package), s.PACKAGE_RAM))
        retained = bytearray(package[:0x10000]); struct.pack_into('>I', retained, 8, 0x11000)
        self.assertEqual(retained, self.before[0x1CA000:0x1DA000])
        for r in self.report['furniture']['expanded_tables']['public_entries']:
            self.assertEqual(self.blob[r['entry'] - 0x80460000:r['entry'] - 0x80460000 + 8].hex(), r['after'])
            self.assertEqual(struct.unpack('>2I', bytes.fromhex(r['after'])), (s.jump(r['target']), 0))
        extra = bytearray(self.blob[0xF400:0xFFA0])
        for r in self.report['clothing']['save_extension']['item_dispatch']:
            at = r['entry'] - 0x8046D000
            self.assertEqual(extra[at:at + 8].hex(), r['after'])
            extra[at:at + 8] = bytes.fromhex(r['before'])
        self.assertEqual(extra, self.before[0xF400:0xFFA0])
        self.assertEqual(struct.unpack_from('>4I', self.files[MODULE].extract(self.image), CONFIG),
            (BLOB, 0xC000, zlib.crc32(self.blob[:0xC000]), s.ABI))
        self.assertLess(s.PACKAGE_RAM + s.PACKAGE_SIZE, self.report['furniture']['bank_pool']['start'])

    def test_directory_choice_relocation_and_all_other_resources(self):
        self.assertEqual(len(self.files), 3389)
        self.assertEqual(self.image[DMA_END - 16:DMA_END], bytes(16))
        self.assertEqual(set(self.files), set(self.old) - {s.CHOICE_OLD} | {s.CHOICE_NEW})
        self.assertEqual(self.files[s.CHOICE_NEW].pstart, self.old[s.CHOICE_OLD].pstart)
        self.assertEqual(self.files[s.CHOICE_NEW].index, self.old[s.CHOICE_OLD].index)
        self.assertEqual(self.files[s.CHOICE_NEW].extract(self.image), self.old[s.CHOICE_OLD].extract(self.base))
        game = bytearray(self.files[CODE_VROM].extract(self.image))
        s.replace_checked(game, s.CHOICE_READER - CODE_RAM, bytes.fromhex('3c18025f27180000'), bytes.fromhex('3c18024027180000'))
        self.assertEqual(game, self.old[CODE_VROM].extract(self.base))
        room = bytearray(self.files[s.ROOM].extract(self.image))
        hook = self.report['furniture']['bank_pool']['hook']
        s.replace_checked(room, hook['address'] - s.ROOM_RAM, bytes.fromhex(hook['after']), bytes.fromhex(hook['before']))
        self.assertEqual(room, self.old[s.ROOM].extract(self.base))
        for vrom, entry in self.files.items():
            if vrom not in (BLOB, MODULE, CODE_VROM, s.ROOM, s.CHOICE_NEW, 0x19D40):
                self.assertEqual(entry, self.old[vrom])
                self.assertEqual(entry.extract(self.image), self.old[vrom].extract(self.base), f'{vrom:08X}')
        spans = sorted((e.vstart, e.vend) for e in self.files.values())
        self.assertTrue(all(a[1] <= b[0] for a, b in zip(spans, spans[1:])))
        self.assertEqual(self.report['import_storage']['remaining_bytes'], s.END - BLOB - len(self.blob))
        self.assertEqual(sha256(self.image), self.report['output_sha256'])
        self.assertEqual(struct.unpack_from('>2I', self.image, 16), n64_checksum(self.image))


if __name__ == '__main__':
    unittest.main()
