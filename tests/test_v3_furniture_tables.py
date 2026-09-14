"""Expanded table memory, complete retargeting, and retained cartridge content."""
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
from v3_furniture_runtime import VROM, RELOC, RAM
from v3_furniture_tables import ABI, CODE, CAPACITY, PROFILES, INDICES, START, END

OUTPUT = ROOT/'build/v3-furniture-tables-02'
PARENT = ROOT/'build/v3-clothing-shop-floor-01'


class FurnitureTablesHost(unittest.TestCase):
    def test_sanitized_initialization_and_existing_bank_helpers(self):
        with tempfile.TemporaryDirectory(prefix='v3-furniture-tables-') as directory:
            for source, defines in (('v3_furniture_tables_test.c', []),
                                    ('v3_furniture_test.c', ['-DAF_V3_FURNITURE_TABLES=1'])):
                binary = Path(directory)/source
                subprocess.run(['cc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-omit-frame-pointer', *defines,
                    str(ROOT/'tests'/source), '-o', str(binary)], check=True, capture_output=True)
                result = subprocess.run([str(binary)], check=True, capture_output=True, timeout=20)
                self.assertIn(b'pass', result.stdout)


@unittest.skipUnless((OUTPUT/'build.json').is_file(), 'Current expanded-table cartridge required')
class FurnitureTablesCartridge(unittest.TestCase):
    def test_exact_owner_and_all_other_resources(self):
        report = json.loads((OUTPUT/'build.json').read_text())
        previous = json.loads((PARENT/'build.json').read_text())
        rom = (OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        old = (PARENT/'animal-forest-v3-asset-loader.z64').read_bytes()
        files, before = by_vrom(rom), by_vrom(old)
        tables = report['furniture']['expanded_tables']
        self.assertEqual(sha256(rom), report['output_sha256'])
        self.assertEqual(set(files), set(before))
        self.assertEqual(files[RELOC].extract(rom), before[RELOC].extract(old))
        owner = bytearray(files[VROM].extract(rom))
        self.assertEqual(sha256(owner), tables['output_sha256'])
        for patch in tables['patches']:
            at = patch['address']-RAM
            self.assertEqual(struct.unpack_from('>I', owner, at)[0], patch['after'])
            struct.pack_into('>I', owner, at, patch['before'])
        self.assertEqual(owner, before[VROM].extract(old))
        self.assertEqual(tables['retargeted_references'], 72)
        self.assertEqual(tables['capacity'], CAPACITY)
        self.assertEqual(tables['profile_table_ram'], f'{PROFILES:08X}')
        self.assertEqual(tables['bank_index_ram'], f'{INDICES:08X}')
        self.assertEqual(tables['reservation_bytes'], END-START)
        blob = files[BLOB].extract(rom)
        staging = bytearray(blob)
        code = (OUTPUT/'furniture_tables/code.bin').read_bytes()
        self.assertEqual(blob[CODE:CODE+len(code)], code)
        staging[CODE:CODE+len(code)] = bytes(len(code))
        self.assertEqual(blob[0xA200:0xA210], before[BLOB].extract(old)[0xA200:0xA210])
        helper = (OUTPUT/'furniture-expanded/code.bin').read_bytes()
        self.assertEqual(blob[0x5800:0x5800+len(helper)], helper)
        staging[0x5800:0x5800+len(helper)] = bytes(len(helper))
        for entry in tables['public_entries']:
            at = entry['entry']-0x80460000
            self.assertEqual(blob[at:at+8].hex(), entry['after'])
            staging[at:at+8] = bytes.fromhex(entry['before'])
        staging[4:8] = before[BLOB].extract(old)[4:8]
        self.assertEqual(staging, before[BLOB].extract(old))
        self.assertEqual(struct.unpack_from('>4I', files[MODULE].extract(rom), CONFIG),
                         (BLOB, 0xC000, zlib.crc32(blob[:0xC000]), ABI))
        catalogue = bytearray(files[0x03970000].extract(rom))
        for address, current, original in ((0x808B3370, 0x3C028047, 0x3C028046),
                                            (0x808B3378, 0x8C42F010, 0x8C424800)):
            at = address-0x808A6100
            self.assertEqual(struct.unpack_from('>I', catalogue, at)[0], current)
            struct.pack_into('>I', catalogue, at, original)
        self.assertEqual(catalogue, before[0x03970000].extract(old))
        for vrom in files:
            if vrom not in (0x19D40, MODULE, BLOB, VROM, 0x03970000):
                self.assertEqual(files[vrom].extract(rom), before[vrom].extract(old), f'{vrom:08X}')
        self.assertEqual(report['save_runtime'], previous['save_runtime'])
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native, (OUTPUT/'asset-loader.ups').read_bytes()), rom)


if __name__ == '__main__': unittest.main()
