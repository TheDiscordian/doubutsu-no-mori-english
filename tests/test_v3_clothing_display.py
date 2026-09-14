"""Native mannequin retention, selected display identity, and save dependencies."""
import ctypes as c
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import apply_ups, by_vrom, sha256
from npc_mail_show import relocate_verified_data
from v3_asset_loader import BLOB, MODULE, CONFIG
import v3_clothing_display as display
from tests.test_v3_save_clothing import fixture, reference_pack

OUTPUT = ROOT/'build/v3-clothing-display-01'
PARENT = ROOT/'build/v3-furniture-tables-02'


class ClothingDisplayHost(unittest.TestCase):
    def test_sanitized_profile_bank_and_initializer(self):
        with tempfile.TemporaryDirectory(prefix='v3-clothing-display-') as directory:
            for source, defines in (('v3_clothing_display_test.c', []),
                    ('v3_furniture_tables_test.c', ['-DAF_V3_CLOTHING_DISPLAY=1'])):
                binary = Path(directory)/source
                subprocess.run(['cc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-omit-frame-pointer', *defines,
                    str(ROOT/'tests'/source), '-o', str(binary)], check=True, capture_output=True)
                result = subprocess.run([str(binary)], check=True, capture_output=True, timeout=20)
                self.assertIn(b'pass', result.stdout)


@unittest.skipUnless((OUTPUT/'build.json').is_file(), 'Current display cartridge required')
class ClothingDisplayCartridge(unittest.TestCase):
    def test_complete_native_program_and_cartridge_retention(self):
        report = json.loads((OUTPUT/'build.json').read_text())
        previous = json.loads((PARENT/'build.json').read_text())
        rom = (OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        old = (PARENT/'animal-forest-v3-asset-loader.z64').read_bytes()
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        files, before, original = by_vrom(rom), by_vrom(old), by_vrom(native)
        self.assertEqual(sha256(rom), report['output_sha256'])
        self.assertEqual(set(files), set(before))
        blob, prior = files[BLOB].extract(rom), before[BLOB].extract(old)
        installed = report['clothing']['display']
        program = blob[display.PROGRAM:display.PROGRAM+display.SIZE]
        self.assertEqual(sha256(program), installed['program_sha256'])
        data, reloc = (original[v].extract(native) for v in (display.VROM, display.RELOC))
        loaded = relocate_verified_data(SimpleNamespace(ram=display.RAM,
            resident_bytes=display.SIZE, sections=display.SECTIONS), data, reloc,
            0x80460000+display.PROGRAM, memory_end=0x80800000)
        restored = bytearray(program)
        restored[0xDC:0x100] = display.WINDOW
        self.assertEqual(restored, loaded)
        self.assertEqual(blob[display.ROW+8:display.ROW+76], loaded[0x164:0x1A8])
        self.assertEqual(report['furniture']['display_imports'], [display.profile_dependency()])
        staging = bytearray(blob)
        for start, end in ((4, 8), (0x20, 0xE0), (0x5800, 0x6650), (0xA000, 0xA200)):
            staging[start:end] = prior[start:end]
        for entry in report['furniture']['expanded_tables']['public_entries']:
            at = entry['entry']-0x80460000
            self.assertEqual(blob[at:at+8].hex(), entry['after'])
            staging[at:at+8] = prior[at:at+8]
        self.assertEqual(staging, prior)
        for folder, at in (('furniture-expanded', 0x5800), ('furniture_tables', 0xA000),
                           ('clothing_display', display.CODE)):
            helper = (OUTPUT/folder/'code.bin').read_bytes()
            self.assertEqual(blob[at:at+len(helper)], helper)
            limit = {'furniture-expanded': display.PROGRAM, 'furniture_tables': 0xA200,
                     'clothing_display': display.ROW}[folder]
            self.assertEqual(blob[at+len(helper):limit], bytes(limit-at-len(helper)))
        self.assertEqual(blob[display.PROGRAM+display.SIZE:display.CODE],
                         bytes(display.CODE-display.PROGRAM-display.SIZE))
        profile = bytearray.fromhex(report['save_runtime']['profile_hex'])
        self.assertEqual(profile[119], 0x80)
        profile[119] = 0
        self.assertEqual(profile.hex(), previous['save_runtime']['profile_hex'])
        self.assertEqual(report['save_runtime']['code'], previous['save_runtime']['code'])
        self.assertEqual(report['clothing']['save_extension'], previous['clothing']['save_extension'])
        self.assertEqual(struct.unpack_from('>4I', files[MODULE].extract(rom), CONFIG),
                         (BLOB, 0xC000, zlib.crc32(blob[:0xC000]), display.ABI))
        for vrom in files:
            if vrom not in (0x19D40, MODULE, BLOB):
                self.assertEqual(files[vrom].extract(rom), before[vrom].extract(old), f'{vrom:08X}')
        self.assertEqual(apply_ups(native, (OUTPUT/'asset-loader.ups').read_bytes()), rom)

    def test_added_display_dependency_accepts_old_but_rejects_reverse(self):
        report = json.loads((OUTPUT/'build.json').read_text())
        previous = json.loads((PARENT/'build.json').read_text())
        current = bytes.fromhex(report['save_runtime']['profile_hex'])
        old = bytes.fromhex(previous['save_runtime']['profile_hex'])
        source, _ = fixture()
        buffer = lambda data: (c.c_ubyte*len(data)).from_buffer_copy(data)
        with tempfile.TemporaryDirectory(prefix='v3-display-save-') as directory:
            library = Path(directory)/'codec.so'
            subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
                '-DAF_V3_CLOTHING_PROFILE=1', str(ROOT/'overlays/v3/save_codec.c'),
                '-o', str(library)], check=True, capture_output=True)
            api = c.CDLL(str(library))
            api.af_v3_save_check.argtypes = (c.c_void_p, c.c_uint, c.c_void_p, c.c_void_p)
            for saved, active, expected in ((old, current, 1), (current, current, 1),
                                           (current, old, -7)):
                bank = reference_pack(source, saved+bytes(640))
                destination = buffer(b'\xA5'*832)
                self.assertEqual(api.af_v3_save_check(buffer(bank), len(bank), buffer(active), destination), expected)
                self.assertEqual(bytes(destination), active+bytes(640) if expected == 1 else b'\xA5'*832)


if __name__ == '__main__': unittest.main()
