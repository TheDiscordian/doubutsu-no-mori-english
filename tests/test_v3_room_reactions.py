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


class InstalledColourAudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = ROOT/os.environ.get('V3_COLOUR_AUDIO_BUILD', 'build/v3-material-colour-audio-runtime-01')
        cls.image, cls.report = inputs(cls.out/'build-lock.json')
        cls.base, cls.prior = inputs(cls.out/'base-lock.json')
        cls.source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_complete_installed_loop_sample_and_retained_behaviours(self):
        import v3_sound_programs as sounds
        core = by_vrom(self.image)[CODE_VROM].extract(self.image)
        equipment = self.report['equipment_resources']
        contracts, _ = sounds.checked_furniture_loops(self.image, core, equipment, self.source)
        self.assertEqual(contracts['331C']['category'], reactions.COLOUR_CATEGORY)
        row = equipment['furniture_level_audio']['programs'][-1]
        self.assertEqual((row['source_sound_id'], row['native_sound_id'], row['native_instrument']), (95,95,90))
        self.assertEqual(row['instrument_identity']['samples'][1]['sample_bytes'], 46900)
        seq, _, _ = sounds.installed_resource(self.image, core, 'seq', 199)
        bound = seq[row['offset']:row['offset']+row['bytes']]
        actual = sounds.looping_layer(bound, row['offset'], prefix=True)
        self.assertIsNone(actual['envelope'])
        self.assertEqual((actual['duration'], actual['note'], actual['velocity']), (32000,39,90))
        budget = sounds.permanent_budget(core)
        self.assertEqual(budget, equipment['furniture_level_audio']['after_budget'])
        self.assertGreaterEqual(budget['conservative_spare'], 0)
        for key in ('room_rigs', 'scenery'):
            self.assertEqual(equipment[key], self.prior['equipment_resources'][key])
        self.assertTrue(reactions.checked_binding(self.source, self.image, self.report)['installed'])

    def test_pending_parent_preserves_selections_saves_artwork_and_patch(self):
        import v3_optional_composition as composer
        for key in ('furniture', 'save_codec', 'save_runtime', 'translation_baseline'):
            self.assertEqual(self.report[key], self.prior[key])
        before = by_vrom(self.base)[BLOB].extract(self.base)
        after = by_vrom(self.image)[BLOB].extract(self.image)
        for row in self.report['equipment_resources']['room_rigs']['material_rows']:
            at = row['blob_offset']; end = at+row['bytes']
            self.assertEqual(after[at:end], before[at:end])
        pin = composer.BASE, composer.BASE_SHA, composer.REPORT_SHA, composer.ABI
        try:
            composer.use_build_lock(self.out/'build-lock.json')
            catalogue = composer.catalogue(self.image, self.report)
            self.assertEqual(len(catalogue), 155)
            self.assertNotIn('GAFE01-r0/item/331C', catalogue)
            none = composer.compose(self.image, self.report, catalogue, composer.resolve(catalogue, []))[0]
            self.assertEqual(sha256(none), self.report['translation_baseline']['sha256'])
        finally:
            composer.BASE, composer.BASE_SHA, composer.REPORT_SHA, composer.ABI = pin
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                                 (self.out/'asset-loader.ups').read_bytes()), self.image)


class InstalledColourLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = ROOT/os.environ.get('V3_COLOURS_BUILD', 'build/v3-material-colour-lifecycle-imports-05/profile-runtime')
        cls.image, cls.report = inputs(cls.out/'build-lock.json')
        cls.base, cls.prior = inputs(cls.out/'base-lock.json')
        cls.source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_installed_complete_lifecycle_and_exact_native_hooks(self):
        from v3_equipment_runtime import PLAYER_VROM, PLAYER_RAM, PLAYER_RELOC
        from v3_npc_draw import relocation_offsets
        from v3_furniture_install import profile
        from v3_sound_programs import checked_furniture_loops
        equipment = self.report['equipment_resources']; room = equipment['room_rigs']
        engine = reactions.checked_colours(self.image, self.report)
        self.assertEqual(engine['native']['live_move_pointer'], 0x80143908)
        self.assertEqual(engine['state'], dict(ram=0x804CD400, bytes=256, mutable=True, saved=False, installed=True))
        bindings = runtime.bind_profiles(self.source, self.image, self.report)
        self.assertTrue(bindings['331C']['staged'])
        row = next(r for r in room['material_rows'] if r['source_item_id']=='331C')
        contracts, _ = checked_furniture_loops(self.image, by_vrom(self.image)[CODE_VROM].extract(self.image),
                                             equipment, self.source)
        lifecycle = reactions.checked_colour_lifecycle(self.source, self.source.profile(0x331C), row, contracts)
        self.assertEqual((row['mode'], row['lifecycle'], row['state_offset']), (1,3,95))
        self.assertTrue(row['profile_installed']);self.assertFalse(row['parent_selectable'])
        staged = next(r for r in self.report['staged_furniture']['rows'] if r['id']=='GAFE01-r0/item/331C')
        self.assertEqual(staged['room_lifecycle'], lifecycle)
        original = copy.deepcopy(row['source'])
        original.update(room_lifecycle=lifecycle, room_runtime=staged['room_runtime'])
        self.assertEqual(profile(original, row['vrom'], limit=self.report['import_storage']['virtual_limit']).hex(),
                         staged['profile_hex'])
        files = by_vrom(self.image); before = by_vrom(self.base)
        player = bytearray(files[PLAYER_VROM].extract(self.image))
        for hook in engine['hooks']:
            at = hook['address']-PLAYER_RAM
            self.assertEqual(player[at:at+4].hex(), hook['after'])
            player[at:at+4] = bytes.fromhex(hook['before'])
        self.assertEqual(player, before[PLAYER_VROM].extract(self.base))
        rel = files[PLAYER_RELOC].extract(self.image); old_rel = before[PLAYER_RELOC].extract(self.base)
        self.assertEqual(set(relocation_offsets(old_rel, len(player)))-set(relocation_offsets(rel, len(player))),
                         {0x808DDB70-PLAYER_RAM})
        self.assertFalse(set(relocation_offsets(rel, len(player)))-set(relocation_offsets(old_rel, len(player))))
        for key in ('packet_crc32',):
            bad = copy.deepcopy(self.report);bad['equipment_resources']['room_rigs']['colours'][key] ^= 4
            with self.assertRaises(ValueError):reactions.checked_colours(self.image, bad)
        self.assertLessEqual(room['code']['bytes'], 16384)
        self.assertLessEqual(room['bootstrap']['bytes'], 1536)
        self.assertLessEqual(engine['bridge']['bytes'], 224)

    def test_retained_resources_saves_and_rebound_controller_bridge(self):
        for key in ('save_codec', 'save_runtime', 'translation_baseline'):
            self.assertEqual(self.report[key], self.prior[key])
        equipment = self.report['equipment_resources']
        self.assertEqual(equipment['furniture_level_audio'], self.prior['equipment_resources']['furniture_level_audio'])
        self.assertTrue(reactions.checked_binding(self.source, self.image, self.report)['installed'])
        before = by_vrom(self.base)[BLOB].extract(self.base)
        after = by_vrom(self.image)[BLOB].extract(self.image)
        for row in equipment['room_rigs']['material_rows']:
            at = row['blob_offset'];end = at+row['bytes']
            self.assertEqual(after[at:end], before[at:end])
        for key, value in self.report['sources'].items():
            if key in reactions.SOURCES:
                self.assertEqual(sha256((ROOT/key).read_bytes()), value, key)
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                                 (self.out/'asset-loader.ups').read_bytes()), self.image)

    def test_browser_composition_keeps_pending_reward_unavailable(self):
        import v3_optional_composition as composer
        from tests.test_v3_room_rig_runtime import CurrentImportedRigTests
        pin = composer.BASE, composer.BASE_SHA, composer.REPORT_SHA, composer.ABI
        try:
            composer.use_build_lock(self.out/'build-lock.json')
            catalogue = composer.catalogue(self.image, self.report)
            self.assertEqual(len(catalogue), 155)
            self.assertNotIn('GAFE01-r0/item/331C', catalogue)
        finally:
            composer.BASE, composer.BASE_SHA, composer.REPORT_SHA, composer.ABI = pin
        # The complete retained reaction category also shares the changed packet.
        self.rows = self.prior['automatic_furniture']['imports']
        if not self.rows:
            self.rows = [r for r in self.report['automatic_furniture']['retained']
                         if r.get('donor_item_id')=='1FD8']
        CurrentImportedRigTests.test_private_browser_selection_matches_offline_and_keeps_translation_only(self)


class MaterialReactionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_colour_update_dispatch_and_rendering_under_sanitizers(self):
        source = (ROOT/'local/ac-decomp/src/game/m_player_common.c_inc').read_text()
        start = source.index('static void Player_actor_Check_player_change_color_for_main(')
        end = source.index('\n}', start)+2
        with tempfile.TemporaryDirectory(prefix='v3-room-colours-') as temporary:
            directory = Path(temporary)
            (directory/'donor_colour_update.inc').write_text(source[start:end])
            binary = directory/'test'
            result = subprocess.run(['cc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-ffp-contract=off', '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                '-I'+str(directory), str(ROOT/'tests/v3_room_colours_test.c'), '-lm', '-o', str(binary)],
                capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('480 donor ticks', result.stdout)

    def test_colour_profile_guard_accepts_serialized_relocations(self):
        profile = self.source.profile(0x331C)
        lifecycle = reactions.colour_lifecycle(self.source, profile)
        self.assertTrue(reactions.colour_profile_lifecycle(profile, lifecycle))
        self.assertTrue(reactions.colour_profile_lifecycle(json.loads(json.dumps(profile)), lifecycle))
        changed = copy.deepcopy(lifecycle)
        changed['functions']['draw']['relocations'][16] = (10,0,4,0)
        self.assertFalse(reactions.colour_profile_lifecycle(profile, changed))

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

    def test_complete_colour_lifecycle_and_player_consumers(self):
        from v3_sound_programs import furniture_level
        profile = self.source.profile(0x331C)
        expected = copy.deepcopy(profile)
        result = reactions.colour_lifecycle(self.source, profile)
        self.assertEqual(profile, expected)
        self.assertEqual(result['category'], reactions.COLOUR_CATEGORY)
        self.assertEqual((result['source_sound_id'], result['exclusive_source_index']), (95, 1223))
        self.assertTrue(result['start_disabled'])
        self.assertFalse(result['callback_installed'])
        self.assertEqual(result['colours']['rgb'], [[255,100,255], [255,255,255], [100,100,100], [100,255,255]])
        self.assertEqual(furniture_level(self.source, profile), result)
        for key in ('create', 'move'):
            changed = copy.copy(self.source); changed.rel = bytearray(changed.rel)
            changed.rel[changed.sections[1][0]+profile['callback_adapter']['functions'][key]['offset']] ^= 1
            with self.assertRaises(ValueError): reactions.colour_lifecycle(changed, profile)
        for key, row in result['consumers'].items():
            changed = copy.copy(self.source); changed.rel = bytearray(changed.rel)
            changed.rel[changed.sections[1][0]+row['offset']] ^= 1
            with self.assertRaises(ValueError, msg=key): reactions.colour_lifecycle(changed, profile)
        for row in list(result['constants'].values())+[result['colours']]:
            changed = copy.copy(self.source); changed.rel = bytearray(changed.rel)
            changed.rel[changed.sections[4][0]+row['offset']] ^= 1
            with self.assertRaises(ValueError): reactions.colour_lifecycle(changed, profile)
        self.assertIsNone(reactions.colour_lifecycle(self.source, self.source.profile(0x1FD8)))

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
