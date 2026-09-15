"""Copied-town fixture boundaries and actual format-2 reader acceptance."""
import copy
import ctypes
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from v3_punchy_gameplay_fixture import ANIMAL, create
from v3_save_codec import BANK, PAYLOAD
from v3_save_clothing import PROFILE, STATE

OUTPUT = ROOT/'build/v3-house-markers-01'
SOURCE = ROOT/'local/rc2-save-report-g3O4lU/test.flash'


@unittest.skipUnless((OUTPUT/'build.json').exists() and SOURCE.exists(),
                     'Current Punchy build and preserved source town required')
class PunchyFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_bytes()
        cls.rom = (OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report = json.loads((OUTPUT/'build.json').read_text())

    def test_both_banks_only_change_declared_fields_and_decode_natively(self):
        result, receipt = create(self.source, self.rom, self.report)
        self.assertEqual(len(result), 2*BANK)
        self.assertEqual(SOURCE.read_bytes(), self.source)
        self.assertTrue(receipt['fixture_only_resident_substitution'])
        self.assertFalse(receipt['natural_move_in_or_schedule_tested'])
        allowed = set(range(4, 8)) | {0x12, 0x13, 0xF86C+237//8}
        for edit in receipt['field_changes']:
            allowed.update(range(edit['offset'], edit['offset']+len(bytes.fromhex(edit['after']))))
        with tempfile.TemporaryDirectory(prefix='v3-punchy-fixture-') as directory:
            library = Path(directory)/'codec.so'
            subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
                '-DAF_V3_CLOTHING_PROFILE=1', str(ROOT/'overlays/v3/save_codec.c'),
                '-o', str(library)], check=True, capture_output=True)
            api = ctypes.CDLL(str(library))
            api.af_v3_save_check.argtypes = (ctypes.c_void_p, ctypes.c_uint,
                                             ctypes.c_void_p, ctypes.c_void_p)
            profile = bytes.fromhex(self.report['save_runtime']['profile_hex'])
            for index in range(2):
                original = self.source[index*BANK:(index+1)*BANK]
                bank = result[index*BANK:(index+1)*BANK]
                changed = {i for i in range(PAYLOAD) if bank[i] != original[i]}
                self.assertLessEqual(changed, allowed)
                self.assertEqual(sum(struct.unpack('>'+str(PAYLOAD//2)+'H', bank[:PAYLOAD])) & 65535, 0)
                self.assertEqual(bank[ANIMAL:ANIMAL+2], bytes.fromhex('E0ED'))
                self.assertEqual(bank[ANIMAL+10:ANIMAL+12], bytes((237, 2)))
                self.assertEqual(bank[ANIMAL+0x520:ANIMAL+0x522], bytes.fromhex('34BF'))
                self.assertEqual(bank[ANIMAL+0x524], 1)
                self.assertEqual(receipt['house_cell_offset'],0x7D7E)
                self.assertEqual(bank[0x7D7E:0x7D80],bytes.fromhex('50ED'))
                # No other foreground tile changes in this disposable fixture.
                foreground=bytearray(original[0x62A8:0x9EA8])
                foreground[0x7D7E-0x62A8:0x7D80-0x62A8]=bytes.fromhex('50ED')
                self.assertEqual(bank[0x62A8:0x9EA8],foreground)
                source = ctypes.create_string_buffer(bank)
                selected = ctypes.create_string_buffer(profile)
                state = ctypes.create_string_buffer(b'\xA5'*STATE)
                self.assertEqual(api.af_v3_save_check(source, BANK, selected, state), 1)
                self.assertEqual(state.raw[:STATE], profile+bytes(STATE-PROFILE))
                self.assertEqual(source.raw[:BANK], bank)

    def test_unknown_input_and_incomplete_dependencies_are_rejected(self):
        altered = bytearray(self.source)
        altered[ANIMAL] ^= 1
        with self.assertRaises(ValueError):
            create(altered, self.rom, self.report)
        for key in ('clothing', 'villager_houses'):
            report = copy.deepcopy(self.report)
            if key == 'clothing':
                report[key]['punchy_defaults_enabled'] = False
            else:
                report[key]['installed_villagers'].remove('E0ED')
            with self.assertRaises(ValueError):
                create(self.source, self.rom, report)

    def test_selected_maelle_fixture_keeps_every_unrelated_payload_byte(self):
        result, receipt = create(self.source, self.rom, self.report, actor=0xE0DA)
        self.assertEqual(receipt['actor_id'], 'E0DA')
        self.assertEqual(receipt['matching_outdoor_house_identity'], '50DA')
        self.assertFalse(receipt['natural_move_in_or_schedule_tested'])
        for number in range(2):
            original = self.source[number*BANK:(number+1)*BANK]
            actual = result[number*BANK:(number+1)*BANK]
            expected = bytearray(original[:PAYLOAD])
            expected[4:8] = b'NAF3'
            expected[0x12:0x14] = actual[0x12:0x14]
            expected[0xF86C+218//8] |= 1<<(218&7)
            for edit in receipt['field_changes']:
                if edit['bank'] != number:
                    continue
                at, before, after = edit['offset'], bytes.fromhex(edit['before']), bytes.fromhex(edit['after'])
                self.assertEqual(expected[at:at+len(before)], before)
                expected[at:at+len(after)] = after
            self.assertEqual(actual[:PAYLOAD], expected)
            self.assertEqual(actual[ANIMAL:ANIMAL+2].hex(), 'e0da')
            self.assertEqual(actual[ANIMAL+10:ANIMAL+12].hex(), 'da05')
            self.assertEqual(actual[ANIMAL+0x4E5:ANIMAL+0x4E9].hex(), 'fef3da20')
            self.assertEqual(actual[ANIMAL+0x520:ANIMAL+0x522].hex(), '341a')
            self.assertEqual(actual[0x7D7E:0x7D80].hex(), '50da')
            self.assertEqual(sum(struct.unpack('>'+str(PAYLOAD//2)+'H', actual[:PAYLOAD])) & 65535, 0)
        self.assertEqual(SOURCE.read_bytes(), self.source)
        for actor in (0xE0D9, 0xE0EE, 'E0DA'):
            with self.assertRaises(ValueError):
                create(self.source, self.rom, self.report, actor=actor)


if __name__ == '__main__':
    unittest.main()
