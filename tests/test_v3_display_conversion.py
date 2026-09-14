"""Selected room representation and precise retention of the current cartridge."""
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
import v3_display_conversion as conversion

OUTPUT = ROOT/'build/v3-display-conversion-01'
PARENT = ROOT/'build/v3-display-readers-02'


class ConversionHost(unittest.TestCase):
    def test_selected_mapping_and_native_argument_retention(self):
        with tempfile.TemporaryDirectory(prefix='v3-display-conversion-') as directory:
            binary = Path(directory)/'test'
            subprocess.run(['cc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_display_conversion_test.c'), '-o', str(binary)],
                check=True, capture_output=True)
            result = subprocess.run([str(binary)], check=True, capture_output=True, timeout=20)
            self.assertIn(b'pass', result.stdout)


@unittest.skipUnless((OUTPUT/'build.json').is_file(), 'Current conversion cartridge required')
class ConversionCartridge(unittest.TestCase):
    def test_complete_conversion_installation_and_retained_resources(self):
        report, old_report = (json.loads((p/'build.json').read_text()) for p in (OUTPUT, PARENT))
        rom, old = ((p/'animal-forest-v3-asset-loader.z64').read_bytes() for p in (OUTPUT, PARENT))
        files, before = by_vrom(rom), by_vrom(old)
        self.assertEqual(sha256(rom), report['output_sha256'])
        self.assertEqual(set(files), set(before))
        result = report['clothing']['display']['conversion']
        helper = (OUTPUT/'display_conversion/code.bin').read_bytes()
        blob, prior = files[BLOB].extract(rom), before[BLOB].extract(old)
        self.assertEqual(blob[conversion.CODE:conversion.CODE+len(helper)], helper)
        self.assertEqual(sha256(helper), result['code']['sha256'])
        self.assertEqual(blob[conversion.CODE+len(helper):conversion.BRIDGES],
                         bytes(conversion.BRIDGES-conversion.CODE-len(helper)))
        code, old_code = bytearray(files[CODE_VROM].extract(rom)), before[CODE_VROM].extract(old)
        for row in result['hooks']:
            at, bridge = row['entry']-CODE_RAM, row['bridge']-0x80460000
            self.assertEqual(code[at:at+8].hex(), row['after'])
            self.assertEqual(blob[bridge:bridge+16].hex(), row['bridge_bytes'])
            struct.pack_into('>2I', code, at, *struct.unpack('>2I', bytes.fromhex(row['before'])))
            self.assertEqual(sha256(code[at:row['end']-CODE_RAM]), row['native_function_sha256'])
        self.assertEqual(code, old_code)
        restored = bytearray(blob)
        restored[conversion.CODE:conversion.END] = prior[conversion.CODE:conversion.END]
        restored[4:8] = prior[4:8]
        self.assertEqual(restored, prior)
        for key in ('save_runtime', 'hra', 'feng_shui', 'collection', 'furniture'):
            # Generated assembly embeds the output directory in .incbin; its
            # source hash differs even when the complete linked image is equal.
            current, previous = dict(report[key]), dict(old_report[key])
            if key in ('hra', 'feng_shui'):
                current.pop('generated_hooks_sha256', None)
                previous.pop('generated_hooks_sha256', None)
            self.assertEqual(current, previous)
        self.assertEqual(report['clothing']['save_extension'], old_report['clothing']['save_extension'])
        self.assertEqual(report['clothing']['display']['readers'], old_report['clothing']['display']['readers'])
        module, old_module = bytearray(files[MODULE].extract(rom)), before[MODULE].extract(old)
        self.assertEqual(struct.unpack_from('>4I', module, CONFIG),
                         (BLOB, 0xC000, zlib.crc32(blob[:0xC000]), conversion.ABI))
        startup = (OUTPUT/'startup/code.bin').read_bytes()
        self.assertEqual(module[STARTUP:STARTUP+len(startup)], startup)
        module[STARTUP:STARTUP+len(startup)] = old_module[STARTUP:STARTUP+len(startup)]
        module[CONFIG:CONFIG+16] = old_module[CONFIG:CONFIG+16]
        self.assertEqual(module, old_module)
        for vrom in set(files)-{0x19D40, CODE_VROM, BLOB, MODULE}:
            self.assertEqual(files[vrom].extract(rom), before[vrom].extract(old), f'{vrom:08X}')
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native, (OUTPUT/'asset-loader.ups').read_bytes()), rom)


if __name__ == '__main__': unittest.main()
