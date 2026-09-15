import json
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.test_v3_furniture_art import ROOT
from aflib import sha256
from v3_fire import BASE, ENGINE, ENTRIES, RAM, VTABLE, asset_contract, native_contract, profiles

OUTPUT = ROOT / 'build/v3-fire-callbacks-05'


class FireTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUTPUT / 'callbacks.json').read_bytes())
        cls.code = (OUTPUT / 'code/code.bin').read_bytes()

    def test_complete_native_dependencies_and_caller_context(self):
        result = native_contract((ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes())
        self.assertEqual(result, self.report['native_contract'])
        self.assertEqual(result['ordinary_heap_bytes'], 0)
        self.assertEqual(result['frame_allocation_bytes'], 176)
        self.assertEqual(result['scroll_drift_texels'], 0)

    def test_complete_assets_callbacks_profiles_and_dependencies(self):
        assets, details = asset_contract((ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        self.assertEqual([sha256(a) for a in assets], self.report['object_sha256'])
        self.assertEqual(details, self.report['source_metadata'])
        self.assertEqual(sha256(self.code), self.report['code']['sha256'])
        result = profiles(self.report['proposed_objects_vrom'], self.code, self.report['code'])
        for i, (native, table) in enumerate(result):
            self.assertEqual(native.hex(), self.report['profiles_hex'][i])
            self.assertEqual(table.hex(), self.report['vtables_hex'][i])
            self.assertEqual(len(native), 68)
            self.assertEqual(native[16:48], bytes(32))
            self.assertEqual(struct.unpack_from('>I', native, 64)[0], VTABLE + 24 * i)
            self.assertEqual(struct.unpack('>5I', table),
                tuple(self.report['code']['symbols'][n] for n in ENTRIES[i * 3:i * 3 + 3]) + (0, 0))
        self.assertLessEqual(len(self.code), VTABLE - RAM)
        self.assertTrue({r[0] for r in ENGINE}.issubset({r['symbol'] for r in self.report['calls']}))
        for name, digest in self.report['source_sha256'].items():
            self.assertEqual(sha256((ROOT / name).read_bytes()), digest)
        for vroms in ((0x2468001, 0x246A000), (0x2468000, 0x2468000), (0x2468000, 0x25F0000)):
            with self.assertRaises(ValueError): profiles(vroms, self.code, self.report['code'])

    def test_sanitized_actual_callbacks(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-fire-') as directory:
            binary = Path(directory) / 'test'
            result = subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-ffp-contract=off', '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT / 'tests/v3_fire_test.c'), '-o', str(binary)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('Fire rig callbacks, sound identities, billboard order, scroll phases, frame lifetime, and arena bounds pass', result.stdout)


if __name__ == '__main__': unittest.main()
