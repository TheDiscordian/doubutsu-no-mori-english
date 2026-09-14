"""Installed display aliases, full donor scoring tables, and preserved cartridge."""
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
from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom, sha256
from v3_asset_loader import BLOB, MODULE, CONFIG, STARTUP
import v3_hra as hra
import v3_feng_shui as feng
import v3_display_items as display

OUTPUT = ROOT/'build/v3-display-readers-02'
PARENT = ROOT/'build/v3-clothing-display-01'


class DisplayItemsHost(unittest.TestCase):
    def test_sanitized_canonical_metadata_and_collection_routing(self):
        with tempfile.TemporaryDirectory(prefix='v3-display-items-') as directory:
            binary = Path(directory)/'test'
            subprocess.run(['cc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_display_items_test.c'), '-o', str(binary)],
                check=True, capture_output=True)
            result = subprocess.run([str(binary)], check=True, capture_output=True, timeout=20)
            self.assertIn(b'pass', result.stdout)


@unittest.skipUnless((OUTPUT/'build.json').is_file(), 'Current display-readers cartridge required')
class DisplayItemsCartridge(unittest.TestCase):
    def test_complete_resident_readers_scoring_and_other_resources(self):
        report = json.loads((OUTPUT/'build.json').read_text())
        previous = json.loads((PARENT/'build.json').read_text())
        rom = (OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        old = (PARENT/'animal-forest-v3-asset-loader.z64').read_bytes()
        files, before = by_vrom(rom), by_vrom(old)
        self.assertEqual(sha256(rom), report['output_sha256'])
        self.assertEqual(set(files), set(before))
        blob, prior = files[BLOB].extract(rom), before[BLOB].extract(old)
        readers = report['clothing']['display']['readers']
        helper = (OUTPUT/'display_items/code.bin').read_bytes()
        self.assertEqual(blob[display.CODE:display.CODE+len(helper)], helper)
        self.assertEqual(blob[display.CODE+len(helper):display.BRIDGES],
                         bytes(display.BRIDGES-display.CODE-len(helper)))
        restored = bytearray(blob)
        for row in readers['item_hooks']+readers['collection_hooks']:
            at = row['entry']-0x80460000
            self.assertEqual(blob[at:at+8].hex(), row['after'])
            restored[at:at+8] = bytes.fromhex(row['before'])
            if 'bridge' in row:
                at = row['bridge']-0x80460000
                self.assertEqual(blob[at:at+16].hex(), row['bridge_bytes'])
        restored[display.CODE:display.BRIDGES+32] = prior[display.CODE:display.BRIDGES+32]
        restored[4:8] = prior[4:8]
        self.assertEqual(restored, prior)
        self.assertEqual(report['save_runtime'], previous['save_runtime'])
        self.assertEqual(report['clothing']['save_extension'], previous['clothing']['save_extension'])
        self.assertEqual(struct.unpack_from('>4I', files[MODULE].extract(rom), CONFIG),
                         (BLOB, 0xC000, zlib.crc32(blob[:0xC000]), display.ABI))
        code = bytearray(files[CODE_VROM].extract(rom))
        for name in ('hra', 'feng_shui'):
            previous_words = {row['address']: row['after'] for row in previous[name]['scheduler']}
            for row in report[name]['scheduler']:
                at = row['address']-CODE_RAM
                self.assertEqual(struct.unpack_from('>I', code, at)[0], row['after'])
                struct.pack_into('>I', code, at, previous_words[row['address']])
        self.assertEqual(code, before[CODE_VROM].extract(old))
        module = bytearray(files[MODULE].extract(rom))
        old_module = before[MODULE].extract(old)
        startup = (OUTPUT/'startup/code.bin').read_bytes()
        self.assertEqual(module[STARTUP:STARTUP+len(startup)], startup)
        module[STARTUP:STARTUP+len(startup)] = old_module[STARTUP:STARTUP+len(startup)]
        module[CONFIG:CONFIG+16] = old_module[CONFIG:CONFIG+16]
        self.assertEqual(module, old_module)
        changed = {0x19D40, CODE_VROM, MODULE, BLOB, hra.NEW_VROM, hra.NEW_RELOC, feng.NEW_VROM, feng.NEW_RELOC}
        for vrom in files:
            if vrom not in changed:
                self.assertEqual(files[vrom].extract(rom), before[vrom].extract(old), f'{vrom:08X}')
        for name, module, width, metadata in (('hra', hra, 4, bytes.fromhex('d4051000')),
                                              ('feng_shui', feng, 2, bytes(2))):
            current, prior_report = report[name], previous[name]
            data = files[module.NEW_VROM].extract(rom)
            previous_data = before[module.NEW_VROM].extract(old)
            self.assertEqual(sha256(data), current['output_sha256'])
            self.assertEqual(sha256(files[module.NEW_RELOC].extract(rom)), current['relocation_sha256'])
            self.assertEqual(current['metadata_rows'], 2051)
            at = current['metadata_address']-module.RAM
            old_at = prior_report['metadata_address']-module.RAM
            table = data[at:at+2051*width]
            old_table = previous_data[old_at:old_at+1267*width]
            self.assertEqual(table[:1267*width], old_table)
            self.assertEqual(table[1727*width:1728*width], metadata)
            gap = bytes.fromhex('fc000000') if width == 4 else bytes(2)
            for index in range(1267, 2051):
                if index != 1727: self.assertEqual(table[index*width:index*width+width], gap)
            record = next(row for row in current['imports'] if row['item_id'] == '3AFC')
            self.assertEqual(record['donor_runtime_index'], 682)
            self.assertEqual(record['metadata'], metadata.hex())
            self.assertLessEqual(len(data), 0x8000 if width == 4 else 0x2000)
            # Every changed native-prefix word has an exact declared patch.
            restored_owner = bytearray(data[:module.SIZE])
            for patch in current['patches']:
                struct.pack_into('>I', restored_owner, patch['address']-module.RAM, patch['before'])
            restored_old = bytearray(previous_data[:module.SIZE])
            for patch in prior_report['patches']:
                struct.pack_into('>I', restored_old, patch['address']-module.RAM, patch['before'])
            self.assertEqual(restored_owner, restored_old)
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native, (OUTPUT/'asset-loader.ups').read_bytes()), rom)


if __name__ == '__main__': unittest.main()
