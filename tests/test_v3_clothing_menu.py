"""Clothing type routing retains item IDs, furniture arithmetic, and code bounds."""
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
from v3_clothing_menu import ABI, CODE, LIMIT, inspect
from v3_furniture_menu import VROM, RELOC, RAM

OUTPUT, PARENT = (ROOT/'build'/p for p in ('v3-clothing-menu-02', 'v3-clothing-collection-01'))


class ClothingMenuLogic(unittest.TestCase):
    def test_sanitized_clothing_type_and_unchanged_furniture_modes(self):
        with tempfile.TemporaryDirectory(prefix='v3-clothing-menu-') as directory:
            binary = Path(directory)/'test'
            subprocess.run(['cc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-DAF_V3_CLOTHING_PROFILE', '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_furniture_room_test.c'), '-o', str(binary)],
                capture_output=True, text=True, check=True)
            result = subprocess.run([str(binary)], capture_output=True, text=True, check=True, timeout=20)
            self.assertIn('original room arithmetic pass', result.stdout)


@unittest.skipUnless((OUTPUT/'build.json').exists(), 'Current clothing menu build required')
class ClothingMenuCartridge(unittest.TestCase):
    def test_complete_guarded_edits_retained_resources_and_reconstruction(self):
        report, parent = (json.loads((p/'build.json').read_text()) for p in (OUTPUT, PARENT))
        rom, previous = ((p/'animal-forest-v3-asset-loader.z64').read_bytes() for p in (OUTPUT, PARENT))
        files, originals = by_vrom(rom), by_vrom(previous)
        blob, old = files[BLOB].extract(rom), originals[BLOB].extract(previous)
        menu = report['clothing']['menu']
        self.assertEqual(sha256(rom), report['output_sha256'])
        self.assertEqual(struct.unpack_from('>4I', files[MODULE].extract(rom), CONFIG),
                         (BLOB, 0xC000, zlib.crc32(blob[:0xC000]), ABI))
        restored = bytearray(blob)
        self.assertEqual(restored[0x8000:0x8008].hex(), menu['query_after'])
        restored[0x8000:0x8008] = bytes.fromhex(menu['query_before'])
        self.assertEqual(old[CODE:LIMIT], bytes(LIMIT-CODE))
        self.assertLessEqual(CODE+menu['code']['bytes'], LIMIT)
        self.assertEqual(sha256(blob[CODE:CODE+menu['code']['bytes']]), menu['code']['sha256'])
        restored[4:8], restored[CODE:LIMIT] = old[4:8], bytes(LIMIT-CODE)
        self.assertEqual(restored, old)
        original_tag = originals[VROM].extract(previous)
        reloc = files[RELOC].extract(rom)
        owner = next(row for row in parent['villager_readers']['owners'] if row['vrom'] == f'{VROM:08X}')
        self.assertEqual(menu['sites'], inspect(original_tag, reloc, owner))
        tag = bytearray(files[VROM].extract(rom))
        self.assertEqual(sha256(tag), menu['output_sha256'])
        for row in menu['sites']:
            target = menu['code']['symbols'][row['symbol']]
            at = row['start']-RAM
            self.assertEqual(struct.unpack_from('>2I', tag, at),
                             (0x08000000 | (target >> 2 & 0x3FFFFFF), 0))
            struct.pack_into('>2I', tag, at, row['first'], row['second'])
        self.assertEqual(tag, original_tag)
        with self.assertRaises(ValueError): inspect(bytes(len(tag)), reloc, owner)
        for key, value in parent['clothing'].items(): self.assertEqual(report['clothing'][key], value)
        for vrom, digest in parent['changed_resources'].items():
            if int(vrom, 16) in (MODULE, VROM): continue
            at = int(report['relocated_resources'].get(vrom, vrom), 16)
            self.assertEqual(sha256(files[at].extract(rom)), digest, vrom)
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native, (OUTPUT/'asset-loader.ups').read_bytes()), rom)


if __name__ == '__main__': unittest.main()
