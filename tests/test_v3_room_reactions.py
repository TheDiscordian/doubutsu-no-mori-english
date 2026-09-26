"""Focused source, envelope, and motor-transport checks for material reactions."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from v3_furniture_pipeline import Source
from v3_furniture_install import inputs
from aflib import sha256
import v3_furniture_reactions as reactions


class MaterialReactionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_complete_source_lifecycle_and_bank(self):
        profile = self.source.profile(0x1FD8)
        result = reactions.source_lifecycle(self.source, profile)
        self.assertEqual((result['source_face'], result['native_face'], result['native_countdown']),
                         (0x82C, 0x1A4, 0x1A6))
        self.assertEqual(result['vibration'], dict(percent=100, waves=[1, 1, 13], frames=[0, 7, 7], distance=0))
        for role in ('create', 'move', 'destroy'):
            changed = copy.copy(self.source);changed.rel = bytearray(changed.rel)
            at = profile['callback_adapter']['functions'][role]['offset']+changed.sections[1][0]
            changed.rel[at] ^= 1
            with self.assertRaises(ValueError): reactions.source_lifecycle(changed, profile)
        self.assertIsNone(reactions.source_lifecycle(self.source, self.source.profile(0x3298)))
        for offset in (0x1070B8, 0x6AA3C):
            changed = copy.copy(self.source);changed.rel = bytearray(changed.rel)
            changed.rel[changed.sections[1][0]+offset] ^= 1
            with self.assertRaises(ValueError): reactions.source_lifecycle(changed, profile)
        bank, receipt = reactions.vibration_bank(self.source)
        self.assertEqual((len(bank), len(receipt['rows'])), (272, 16))
        for section, offset in ((1, reactions.ENGINE_START), (4, reactions.WAVES_START)):
            changed = copy.copy(self.source);changed.rel = bytearray(changed.rel)
            changed.rel[changed.sections[section][0]+offset] ^= 1
            with self.assertRaises(ValueError): reactions.vibration_bank(changed)
        changed = copy.copy(self.source);changed.section_relocations = dict(changed.section_relocations)
        changed.section_relocations[(4, reactions.WAVE_TABLE)] = (1, 1, 4, reactions.WAVES_START+1)
        with self.assertRaises(ValueError): reactions.vibration_bank(changed)

    def test_native_transport_and_player_bindings(self):
        image, report = inputs(ROOT/'build/v3-material-lifecycle-imports-02/build-lock.json')
        result = reactions.native_contract(image)
        self.assertEqual(len(result['blocks']), 12)
        self.assertEqual(result['serial_hook'], 0x800D7150)
        self.assertFalse(result['callback_installed'])
        bridge = reactions.bridge_reservation(image, report)
        self.assertTrue(bridge['native_part_copy_fallback_preserved'])
        self.assertEqual([r['bytes'] for r in bridge['windows']], [64, 64])
        bad = copy.deepcopy(report)
        bad['equipment_resources']['code']['symbols']['af_v3_equipment_size'] += 4
        with self.assertRaises(ValueError): reactions.bridge_reservation(image, bad)

    def test_donor_comparison_and_motor_transport_under_sanitizers(self):
        source = (ROOT/'local/ac-decomp/src/game/m_vibctl.c').read_text()
        functions = []
        for name in ('mVibElem_move', 'mVibInfo_elem_entry', 'mVibInfo_elem_delete', 'mVibInfo_set_target_elem'):
            start = source.index('static void '+name+'(')
            end = source.index('\n}', start)+2
            functions.append(source[start:end])
        with tempfile.TemporaryDirectory(prefix='v3-room-reactions-') as directory:
            directory = Path(directory)
            (directory/'donor_vibration.inc').write_text('\n\n'.join(functions))
            (directory/'waves.bin').write_bytes(reactions.vibration_bank(self.source)[0])
            binary = directory/'test'
            result = subprocess.run(['cc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-ffp-contract=off', '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                '-I'+str(directory), str(ROOT/'tests/v3_room_rumble_test.c'), '-o', str(binary)],
                capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([str(binary), str(directory/'waves.bin')],
                                    capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('2850 donor frame comparisons', result.stdout)

    def test_prepared_mips_bank_bridge_and_current_sources(self):
        directory = ROOT/os.environ.get('V3_REACTIONS_PREPARED', 'build/v3-room-reactions-prepared-06')
        report = json.loads((directory/'lifecycles.json').read_bytes())
        self.assertFalse(report['runtime_installed'])
        self.assertFalse(report['native_execution_tested'])
        self.assertEqual([r['source_item_id'] for r in report['rows']], ['1FD8'])
        for name, digest in report['sources'].items():
            self.assertEqual(sha256((ROOT/name).read_bytes()), digest, name)
        bank, receipt = reactions.vibration_bank(self.source)
        self.assertEqual(report['bank'], json.loads(json.dumps(receipt)))
        code = (directory/'code/code.bin').read_bytes()
        self.assertEqual((len(code), sha256(code)), (report['code']['bytes'], report['code']['sha256']))
        at = report['code']['symbols']['af_v3_rumble_waves']-0x804C8000
        self.assertEqual(code[at:at+len(bank)], bank)
        self.assertEqual(report['code']['symbols']['af_rumble_motor_init'], 0x80031574)
        self.assertEqual(report['code']['symbols']['af_rumble_motor_access'], 0x80031300)
        bridge = (directory/'bridge/code.bin').read_bytes()
        self.assertEqual(sha256(bridge), report['bridge']['code']['sha256'])
        for row in report['bridge']['windows']:
            at = row['address']-reactions.BRIDGE_WINDOWS[0][0]
            self.assertEqual(bridge[at:at+64].ljust(64, b'\0').hex(), row['compiled_hex'])
        self.assertLessEqual(report['bootstrap_capacity_check']['bytes'], 1536)
        self.assertEqual(report['state'], dict(ram=0x804CD000, bytes=1024, mutable=True, saved=False, installed=False))
