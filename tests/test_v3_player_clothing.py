"""Original/imported player sources, double buffering, and current cartridge."""
import ctypes as c
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
from v3_asset_loader import BLOB, CONFIG, MODULE
from v3_player_clothing import ABI, ENTRIES, install

OUTPUT = ROOT/'build/v3-player-clothing-01'


class PlayerClothingLogic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='v3-player-clothing-')
        library = Path(cls.temp.name)/'clothing.so'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
            str(ROOT/'overlays/v3/clothing.c'), str(ROOT/'overlays/v3/player_clothing.c'),
            str(ROOT/'tests/fixtures/v3_player_clothing.c'), '-o', str(library)],
            capture_output=True, text=True, check=True)
        cls.api = c.CDLL(str(library))
        for _, _, name, _ in ENTRIES[:2]:
            getattr(cls.api, name).argtypes = (c.c_void_p, c.c_int, c.c_int)
        cls.api.af_v3_player_change_cloth.argtypes = (c.c_void_p, c.c_ushort)

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def setUp(self):
        self.row = (c.c_ubyte*32).in_dll(self.api, 'af_v3_clothing')
        self.row[:] = struct.pack('=HHIHBB16sI', 0x34BF, 0x10BF, 0x3F0F000, 380, 1, 0, b'cherry shirt    ', 0)
        self.player = (c.c_ubyte*0xA80).in_dll(self.api, 'private_bytes')
        self.player[:] = bytes(len(self.player))
        self.buffers = (c.c_ubyte*1152).in_dll(self.api, 'buffers')
        self.buffers[:] = b'\xA5'*1152
        for name in ('active_bank', 'missing_bank', 'calls', 'toggles', 'dmas', 'invalid_calls'):
            c.c_int.in_dll(self.api, name).value = 0

    def test_startup_native_imported_and_checked_fallback(self):
        for i, index in enumerate((0xBF, 0x10BF)):
            self.player[0xA76:0xA78] = index.to_bytes(2, 'big')
            for _, _, name, _ in ENTRIES[:2]: getattr(self.api, name)(1, i, i*2)
        self.assertEqual(list((c.c_uint*4).in_dll(self.api, 'banks')), [14, 15, 14, 15])
        self.assertEqual(list((c.c_uint*4).in_dll(self.api, 'sources')), [0xB7FE00, 0xB897E0, 0x3F0F000, 0x3F0F200])
        self.assertEqual(list((c.c_uint*4).in_dll(self.api, 'sizes')), [512, 32, 512, 32])
        self.assertEqual(list((c.c_int*4).in_dll(self.api, 'af_v3_player_bank_ids')), [0, 2, 1, 3])
        c.c_int.in_dll(self.api, 'calls').value = 0
        self.row[10] = 0
        self.api.af_v3_player_cloth_texture(1, 0, 0)
        self.assertEqual((c.c_uint*4).in_dll(self.api, 'sources')[0], 0xB68000)
        self.assertEqual(bytes(self.player[0xA76:0xA78]), bytes.fromhex('10bf'))
        self.api.af_v3_player_cloth_texture(None, 0, 0)
        self.api.af_v3_player_cloth_texture(1, 2, 0)
        self.assertEqual(c.c_int.in_dll(self.api, 'calls').value, 1)

    def test_change_both_buffers_and_no_toggle_on_unknown_or_missing(self):
        self.api.af_v3_player_change_cloth(1, 0x10BF)
        self.assertEqual(c.c_int.in_dll(self.api, 'active_bank').value, 1)
        imported = b'\xA5'*16+b'\x80'*512+b'\x90'*32+b'\xA5'*16
        self.assertEqual(bytes(self.buffers), b'\xA5'*576+imported)
        self.api.af_v3_player_change_cloth(1, 0xBF)
        self.assertEqual(c.c_int.in_dll(self.api, 'active_bank').value, 0)
        native = b'\xA5'*16+b'\xF0'*512+b'\xBF'*32+b'\xA5'*16
        self.assertEqual(bytes(self.buffers), native+imported)
        before = bytes(self.buffers)
        self.api.af_v3_player_change_cloth(1, 0x10C0)
        self.api.af_v3_player_change_cloth(None, 0xBF)
        self.row[10] = 0
        self.api.af_v3_player_change_cloth(1, 0x10BF)
        self.assertEqual(c.c_int.in_dll(self.api, 'toggles').value, 2)
        c.c_int.in_dll(self.api, 'missing_bank').value = 1
        self.api.af_v3_player_change_cloth(1, 0xBF)
        self.assertEqual(c.c_int.in_dll(self.api, 'active_bank').value, 0)
        self.assertEqual(c.c_int.in_dll(self.api, 'toggles').value, 4)
        self.assertEqual(c.c_int.in_dll(self.api, 'dmas').value, 4)
        self.assertEqual(bytes(self.buffers), before)
        self.assertEqual(c.c_int.in_dll(self.api, 'invalid_calls').value, 0)


@unittest.skipUnless((OUTPUT/'build.json').exists(), 'Current player clothing build required')
class PlayerClothingCartridge(unittest.TestCase):
    def test_reader_edits_and_unchanged_npc_artwork_profile(self):
        report = json.loads((OUTPUT/'build.json').read_text())
        parent = json.loads((ROOT/'build/v3-npc-clothing-01/build.json').read_text())
        rom = (OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        files = by_vrom(rom)
        self.assertEqual(sha256(rom), report['output_sha256'])
        blob = files[BLOB].extract(rom)
        self.assertEqual(struct.unpack_from('>4I', files[MODULE].extract(rom), CONFIG),
                         (BLOB, 0xC000, zlib.crc32(blob[:0xC000]), ABI))
        code = bytearray(files[CODE_VROM].extract(rom))
        for hook in report['clothing']['player_readers']['hooks']:
            at, before, after = int(hook['entry'], 16)-CODE_RAM, bytes.fromhex(hook['before']), bytes.fromhex(hook['after'])
            self.assertEqual(code[at:at+8], after)
            code[at:at+8] = before
        self.assertEqual(sha256(code), parent['changed_resources'][f'{CODE_VROM:08X}'])
        install(code, report['asset']['symbols'])
        self.assertEqual(code, files[CODE_VROM].extract(rom))
        with self.assertRaises(ValueError): install(code, report['asset']['symbols'])
        for vrom, digest in parent['changed_resources'].items():
            if int(vrom, 16) in (MODULE, CODE_VROM): continue
            actual = int(report['relocated_resources'].get(vrom, vrom), 16)
            self.assertEqual(sha256(files[actual].extract(rom)), digest, vrom)
        self.assertEqual(report['save_runtime']['profile_hex'], parent['save_runtime']['profile_hex'])
        self.assertEqual(report['clothing']['imports'], parent['clothing']['imports'])
        self.assertFalse(report['clothing']['punchy_defaults_enabled'])
        self.assertEqual(apply_ups(native, (OUTPUT/'asset-loader.ups').read_bytes()), rom)


if __name__ == '__main__': unittest.main()
