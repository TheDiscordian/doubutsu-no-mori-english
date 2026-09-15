import json
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.test_v3_furniture_art import ROOT
from aflib import sha256
from v3_tent_model import ART, BASE, ENTRIES, RAM, VTABLE, asset_contract, native_contract, profile

OUTPUT = ROOT / 'build/v3-tent-model-callbacks-02'


class TentModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUTPUT / 'callbacks.json').read_bytes())
        cls.code = (OUTPUT / 'code/code.bin').read_bytes()

    def test_native_instance_lifetime_contract_is_preserved_in_current_cartridge(self):
        result = native_contract((ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes())
        self.assertEqual(result, self.report['native_contract'])
        self.assertEqual(result['private_fade_offset'], 0x1A4)
        self.assertEqual(result['heap_allocation_bytes'], 0)

    def test_complete_tent_source_profile_and_compiled_dependencies(self):
        asset, details = asset_contract((ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        self.assertEqual(sha256(asset), self.report['object_sha256'])
        self.assertEqual(details, self.report['source_metadata'])
        self.assertEqual(sha256(self.code), self.report['code']['sha256'])
        native, table = profile(0x0244E000, self.code, self.report['code'])
        self.assertEqual(native.hex(), self.report['profile_hex'])
        self.assertEqual(table.hex(), self.report['vtable_hex'])
        self.assertEqual(native[16:48], bytes(32))
        self.assertEqual(native[48:64].hex(), '417b33333c23d70a0400000000008000')
        self.assertEqual(struct.unpack_from('>I', native, 64)[0], VTABLE)
        self.assertEqual(struct.unpack('>5I', table), tuple(self.report['code']['symbols'][n] for n in ENTRIES) + (0,))
        self.assertLessEqual(len(self.code), VTABLE - RAM)
        self.assertEqual({r['symbol'] for r in self.report['external_calls']}, {'_Matrix_to_Mtx', 'osWritebackDCache'})
        for name, digest in self.report['source_sha256'].items():
            self.assertEqual(sha256((ROOT / name).read_bytes()), digest)
        with self.assertRaises(ValueError): profile(0x0244E008, self.code, self.report['code'])
        bad = dict(self.report['code']); bad['symbols'] = dict(bad['symbols']); bad['symbols'][ENTRIES[2]] = VTABLE
        with self.assertRaises(ValueError): profile(0x0244E000, self.code, bad)

    def test_sanitized_actual_callbacks_with_complete_converted_palettes(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-tent-light-') as directory:
            binary = Path(directory) / 'test'
            result = subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-ffp-contract=off', '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT / 'tests/v3_tent_model_test.c'), '-o', str(binary)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([str(binary), str(ART / 'tent-model.n64obj.bin')],
                capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('Tent source palettes, independent fades, frame lifetime, six commands, bounds, and actor guards pass',
                          result.stdout)


if __name__ == '__main__': unittest.main()
