"""Native callback contract, explicit dependencies, and relocatable text bounds."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
from v3_speed_bag import ENGINE, ENTRIES, ORIGIN, native_contract, validate_calls

OUTPUT = ROOT/'build/v3-speed-bag-callbacks-01'


class CallbackRelocationTests(unittest.TestCase):
    def fixture(self):
        targets = {**ENGINE, 'af_v3_speed_bag_sound': 0x8019ADE0}
        code, rows = bytearray(), []
        for i, (name, address) in enumerate(targets.items()):
            code.extend(struct.pack('>II', 0x0C000000 | ((address & 0x0FFFFFFF) >> 2), 0))
            rows.append(f'{ORIGIN+i*8:08x} 00000104 R_MIPS_26 {address:08x} {name}')
        code.extend(bytes.fromhex('03e0000800000000'))
        return bytes(code), '\n'.join(rows), targets

    def test_only_bound_external_calls_relocate(self):
        code, rows, targets = self.fixture()
        calls = validate_calls(code, rows, targets)
        self.assertEqual(len(calls), len(targets))
        for new_origin in (0x80200000, 0x80473000, 0x807F0000):
            for call in calls:
                word = struct.unpack_from('>I', code, call['offset'])[0]
                self.assertEqual((new_origin & 0xF0000000) | ((word & 0x3FFFFFF) << 2), call['target'])

    def test_reject_missing_local_data_changed_target_and_duplicate_calls(self):
        code, rows, targets = self.fixture()
        variants = (rows.replace('R_MIPS_26', 'R_MIPS_HI16', 1),
                    rows.replace('cKF_SkeletonInfo_R_ct', '.rodata', 1),
                    rows.replace('80052228', '8005222c', 1),
                    '\n'.join(rows.splitlines()[1:]), rows+'\n'+rows.splitlines()[0],
                    rows.replace('80000000', '80001000', 1))
        for changed in variants:
            with self.subTest(rows=changed), self.assertRaises(ValueError):
                validate_calls(code, changed, targets)
        bad = bytearray(code); struct.pack_into('>I', bad, len(code)-8, 0x08000000)
        with self.assertRaises(ValueError): validate_calls(bytes(bad), rows, targets)
        bad = bytearray(code); bad[3] ^= 1
        with self.assertRaises(ValueError): validate_calls(bytes(bad), rows, targets)

    def test_unknown_rom_contract_is_rejected(self):
        with self.assertRaises(ValueError): native_contract(b'not an N64 ROM')


@unittest.skipUnless((OUTPUT/'callbacks.json').is_file(), 'Local compiled callbacks required')
class CompiledCallbackTests(unittest.TestCase):
    def test_actual_native_contract_and_compiled_dependencies(self):
        report = json.loads((OUTPUT/'callbacks.json').read_text())
        code = (OUTPUT/'code.bin').read_bytes()
        original = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(native_contract(original), report['native_contract'])
        self.assertEqual(report['native_contract']['silent_native_states'], [5, 6, 13, 15])
        self.assertEqual(report['entry_offsets'], dict(zip(ENTRIES, (0, 148, 328))))
        self.assertEqual(len(code), 472)
        self.assertEqual(sha256(code), '69204f52e3c2ce1599408e621e5e2e8460dc1b1730749e345a66b32c69f04730')
        self.assertEqual(sha256(code), report['sha256'])
        self.assertEqual(validate_calls(code, (OUTPUT/'relocations.txt').read_text(),
            {**ENGINE, 'af_v3_speed_bag_sound': report['sound_entry']}), report['external_calls'])
        self.assertFalse(report['runtime_installed'])
        self.assertFalse(report['sound_dependency_verified'])
        self.assertFalse(report['selectable'])

    def test_compiled_rig_offsets_match_actual_converted_object(self):
        art = json.loads((ROOT/'build/v3-speed-bag-art-01/art.json').read_text())
        self.assertEqual(art['headers']['animation']['native_offset'], 0xE58)
        self.assertEqual(art['headers']['skeleton']['native_offset'], 0xE84)
        code = (OUTPUT/'code.bin').read_bytes()
        self.assertIn(struct.pack('>I', 0x26240E58), code)
        self.assertIn(struct.pack('>I', 0x26240E84), code)


if __name__ == '__main__':
    unittest.main()
