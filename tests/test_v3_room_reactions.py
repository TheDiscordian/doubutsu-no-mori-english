"""Focused source, envelope, and motor-transport checks for material reactions."""
import copy
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from v3_furniture_pipeline import Source
from v3_furniture_install import inputs
from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom, sha256
from v3_asset_loader import BLOB
from v3_import_storage import ROWS, slot
import v3_room_rig_runtime as runtime
import v3_furniture_reactions as reactions


class InstalledMaterialReactionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = ROOT/os.environ.get('V3_REACTIONS_BUILD', 'build/v3-material-reaction-imports-03/cartridge')
        cls.image, cls.report = inputs(cls.out/'build-lock.json')
        cls.base, cls.prior = inputs(ROOT/'build/v3-material-lifecycle-imports-02/build-lock.json')
        cls.blob = by_vrom(cls.image)[BLOB].extract(cls.image)
        cls.source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.rows = cls.report['automatic_furniture']['imports']

    def test_installed_category_preserves_assets_and_uses_complete_lifecycle(self):
        from v3_furniture_install import profile
        bindings = runtime.bind_profiles(self.source, self.image, self.report)
        engine = reactions.checked_binding(self.source, self.image, self.report)
        self.assertTrue(engine['installed'])
        self.assertEqual(engine['state'], dict(ram=0x804CD000, bytes=1024, mutable=True, saved=False, installed=True))
        room = self.report['equipment_resources']['room_rigs']
        art = ROOT/'build/v3-material-frames-prepared-01'
        prepared = json.loads((art/'art.json').read_bytes())
        for row in self.rows:
            donor = row['donor_item_id']
            material = next(r for r in room['material_rows'] if r['source_item_id'] == donor)
            self.assertEqual((material['lifecycle'], material['mode'], material['state_offset']), (2, 2, 0x1A4))
            expected = reactions.checked_lifecycle(self.source, self.source.profile(int(donor, 16)), material)
            self.assertEqual(row['room_lifecycle'], expected)
            self.assertTrue(material['parent_selectable'])
            self.assertFalse(bindings[donor]['staged'])
            obj = next(r for r in prepared['objects'] if r['item_id'] == donor)
            self.assertEqual(self.blob[material['blob_offset']:material['blob_offset']+material['bytes']],
                             (art/obj['object_file']).read_bytes())
            i = slot(int(row['item_id'], 16))
            self.assertEqual(self.blob[ROWS+i*80:ROWS+(i+1)*80],
                struct.pack('>HHI', row['runtime_index'], int(row['item_id'], 16), 1)+
                profile(row, material['vrom'], limit=self.report['import_storage']['virtual_limit'])+bytes(4))
            entries = json.loads((ROOT/'translations/provenance.json').read_bytes())['entries']
            self.assertIn(row['id']+'/name', {entry['id'] for entry in entries})
        self.assertEqual((self.rows[0]['donor_list'], self.rows[0]['reward_route']), ('ftr_listJonason', 12))
        self.assertFalse(self.rows[0]['catalogue_orderable'])
        self.assertLessEqual(room['code']['bytes'], 16384)
        self.assertLessEqual(room['bootstrap']['bytes'], 1536)
        for key in ('save_codec', 'translation_baseline'):
            self.assertEqual(self.report[key], self.prior[key])
        self.assertEqual(self.report['save_codec']['format_version'], 4)
        saved = copy.deepcopy(self.prior['save_runtime'])
        flags = bytearray.fromhex(saved['profile_hex'])
        for row in self.rows:
            i = slot(int(row['item_id'], 16)); flags[0x20+i//8] |= 1 << (i & 7)
        saved.update(profile_hex=flags.hex(), profile_sha256=sha256(flags))
        self.assertEqual(self.report['save_runtime'], saved)

    def test_bridge_modifies_only_owned_windows_and_rejects_changed_bindings(self):
        engine = self.report['equipment_resources']['room_rigs']['reactions']
        core = by_vrom(self.image)[CODE_VROM].extract(self.image)
        before = by_vrom(self.base)[CODE_VROM].extract(self.base)
        self.assertEqual(reactions.restored_core(core, engine['bridge']), before)
        self.assertEqual([len(bytes.fromhex(h['after'])) for h in engine['bridge']['hooks']], [64, 64, 4])
        for hook in engine['bridge']['hooks']:
            at = hook['address']-CODE_RAM
            self.assertEqual(core[at:at+len(bytes.fromhex(hook['after']))].hex(), hook['after'])
        for key in ('packet_crc32', 'callback'):
            changed = copy.deepcopy(self.report)
            changed['equipment_resources']['room_rigs']['reactions']['bridge'][key] ^= 4
            with self.assertRaises(ValueError): reactions.checked_binding(self.source, self.image, changed)
        self.assertEqual(core[0x800B1DF0-CODE_RAM:0x800B1E50-CODE_RAM],
                         before[0x800B1DF0-CODE_RAM:0x800B1E50-CODE_RAM])

    def test_browser_selection_and_patch_reconstruction(self):
        from tests.test_v3_room_rig_runtime import CurrentImportedRigTests
        CurrentImportedRigTests.test_private_browser_selection_matches_offline_and_keeps_translation_only(self)
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                                 (self.out/'asset-loader.ups').read_bytes()), self.image)


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
