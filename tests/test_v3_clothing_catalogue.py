"""Current clothing catalogue data, code, relocation, and retained cartridge."""
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
from aflib import by_vrom, sha256, apply_ups
from v3_asset_loader import BLOB, MODULE, CONFIG, STARTUP
import v3_catalogue as cat
import v3_clothing_catalogue as cloth

OUTPUT = ROOT/'build/v3-clothing-catalogue-01'
PARENT = ROOT/'build/v3-display-conversion-01'


class ClothingCatalogueHost(unittest.TestCase):
    def test_sanitized_ownership_preview_and_native_availability(self):
        with tempfile.TemporaryDirectory(prefix='v3-clothing-catalogue-') as directory:
            binary = Path(directory)/'test'
            subprocess.run(['cc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_clothing_catalogue_test.c'), '-o', str(binary)],
                check=True, capture_output=True)
            result = subprocess.run([str(binary)], check=True, capture_output=True, timeout=20)
            self.assertIn(b'pass', result.stdout)


@unittest.skipUnless((OUTPUT/'build.json').exists(), 'Current clothing catalogue cartridge required')
class ClothingCatalogueCartridge(unittest.TestCase):
    def test_complete_table_previews_bounds_and_retained_resources(self):
        report, old_report = (json.loads((p/'build.json').read_text()) for p in (OUTPUT, PARENT))
        rom, old = ((p/'animal-forest-v3-asset-loader.z64').read_bytes() for p in (OUTPUT, PARENT))
        files, before = by_vrom(rom), by_vrom(old)
        result, previous = report['catalogue'], old_report['catalogue']
        self.assertEqual(sha256(rom), report['output_sha256'])
        self.assertEqual(set(files), set(before))
        data, previous_data = files[cat.VROM].extract(rom), before[cat.VROM].extract(old)
        self.assertEqual(sha256(data), result['output_sha256'])
        row = result['clothing']; at = row['table_address']-cat.RAM
        ordering = data[at:at+492]
        self.assertEqual(ordering[:-2], previous_data[cloth.TABLE-cat.RAM:cloth.TABLE-cat.RAM+490])
        self.assertEqual(sha256(ordering[:-2]), cloth.NATIVE_SHA)
        self.assertEqual(ordering[-2:], bytes.fromhex('0ABF'))
        self.assertEqual(struct.unpack_from('>2I', data, cloth.POINTER-cat.RAM), (row['table_address'], 246))
        self.assertEqual((row['donor_rows'], row['donor_position'], row['donor_runtime_index']), (247, 183, 682))
        self.assertEqual(data[cat.SIZE:], (OUTPUT/'catalogue/code.bin').read_bytes())
        restored, restored_before = bytearray(data[:cat.SIZE]), bytearray(previous_data[:cat.SIZE])
        for target, receipt in ((restored, result), (restored_before, previous)):
            for patch in receipt['patches']:
                self.assertEqual(struct.unpack_from('>I', target, patch['address']-cat.RAM)[0], patch['after'])
                struct.pack_into('>I', target, patch['address']-cat.RAM, patch['before'])
        self.assertEqual(restored, restored_before)
        self.assertLessEqual(result['conservative_pool_required'], result['pool_reserved'])
        self.assertEqual(result['additional_pool_allocation'], 0)
        self.assertEqual(result['total_rows'], 438)
        parent, prior_parent = bytearray(files[cat.PARENT].extract(rom)), before[cat.PARENT].extract(old)
        self.assertEqual(struct.unpack_from('>4I', parent, cat.OWNER),
                         (cat.VROM, cat.VROM+len(data), cat.RAM, cat.RAM+len(data)))
        parent[cat.OWNER+4:cat.OWNER+8] = prior_parent[cat.OWNER+4:cat.OWNER+8]
        parent[cat.OWNER+12:cat.OWNER+16] = prior_parent[cat.OWNER+12:cat.OWNER+16]
        self.assertEqual(parent, prior_parent)
        blob, prior = files[BLOB].extract(rom), before[BLOB].extract(old)
        restored_blob = bytearray(blob); restored_blob[4:8] = prior[4:8]
        self.assertEqual(restored_blob, prior)
        self.assertEqual(report['save_runtime'], old_report['save_runtime'])
        self.assertEqual(report['clothing'], old_report['clothing'])
        module, old_module = bytearray(files[MODULE].extract(rom)), before[MODULE].extract(old)
        self.assertEqual(struct.unpack_from('>4I', module, CONFIG),
                         (BLOB, 0xC000, zlib.crc32(blob[:0xC000]), cloth.ABI))
        startup = (OUTPUT/'startup/code.bin').read_bytes()
        self.assertEqual(module[STARTUP:STARTUP+len(startup)], startup)
        module[STARTUP:STARTUP+len(startup)] = old_module[STARTUP:STARTUP+len(startup)]
        module[CONFIG:CONFIG+16] = old_module[CONFIG:CONFIG+16]
        self.assertEqual(module, old_module)
        self.assertEqual(sha256(files[cat.RELOC].extract(rom)), result['relocation_sha256'])
        for vrom in set(files)-{0x19D40, BLOB, MODULE, cat.VROM, cat.RELOC, cat.PARENT}:
            self.assertEqual(files[vrom].extract(rom), before[vrom].extract(old), f'{vrom:08X}')
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native, (OUTPUT/'asset-loader.ups').read_bytes()), rom)


if __name__ == '__main__': unittest.main()
