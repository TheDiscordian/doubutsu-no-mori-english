"""Complete switched-joint behaviour, installed batch, and optional composition."""
import copy
import json
import os
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,apply_ups
from v3_asset_loader import BLOB
from v3_furniture_install import inputs,profile
from v3_furniture_pipeline import Source,prepare,PreparedAssets
from v3_import_storage import ROWS,slot
import v3_furniture_joint_rigs as joints
import v3_room_rig_runtime as runtime


class JointLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out=ROOT/os.environ.get('V3_JOINT_BUILD','build/v3-switched-joint-imports-03/profile-runtime')
        cls.image,cls.report=inputs(cls.out/'build-lock.json')
        cls.base,cls.prior=inputs(ROOT/'build/v3-large-model-imports-01/cartridge/build-lock.json')
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.blob=by_vrom(cls.image)[BLOB].extract(cls.image)

    def test_complete_source_motion_audio_and_immutable_prepared_art(self):
        art=ROOT/'build/v3-joint-callback-rigs-prepared-01'
        cache=PreparedAssets(self.source,[art])
        for item,kind in ((0x3070,1),(0x309C,2),(0x31AC,3)):
            parts=prepare(self.source,item);descriptor=parts[0];before=copy.deepcopy(descriptor)
            lifecycle=joints.lifecycle(self.source,descriptor)
            self.assertEqual(descriptor,before)
            self.assertEqual(lifecycle['mode'],kind)
            self.assertEqual(lifecycle['source_steps_per_native_update'],2)
            self.assertEqual(lifecycle['initial_speed'],.5)
            self.assertEqual(lifecycle['state_offset'],0x450)
            self.assertEqual(lifecycle['switch_clicks'],[0x16,0x17] if kind==3 else [])
            self.assertEqual(lifecycle['source_sound_id'],0x51 if kind==3 else None)
            self.assertIsNotNone(cache.reuse(self.source,f'{item:04X}',parts))
            for receipt in [lifecycle['functions']['move'],*lifecycle['helpers'].values(),lifecycle['initializer']]:
                bad=copy.copy(self.source);bad.rel=bytearray(self.source.rel)
                bad.rel[self.source.sections[1][0]+receipt['offset']]^=1
                with self.assertRaises(ValueError):joints.lifecycle(bad,descriptor)
            bad=copy.copy(self.source);bad.rel=bytearray(self.source.rel)
            offset=int(next(iter(lifecycle['constants'])),16)
            bad.rel[self.source.sections[4][0]+offset]^=1
            with self.assertRaises(ValueError):joints.lifecycle(bad,descriptor)
        self.assertIsNone(joints.lifecycle(self.source,prepare(self.source,0x3064)[0]))

    def test_complete_profiles_relocated_packet_and_preserved_save_resources(self):
        bindings=runtime.bind_profiles(self.source,self.image,self.report)
        equipment=self.report['equipment_resources'];room=equipment['room_rigs']
        self.assertEqual(runtime.packet_layout(room),(0x804D0000,0x804D8000,36864))
        self.assertLessEqual(room['code']['bytes'],32768)
        self.assertEqual(room['joint_contract'],joints.native_contract(self.image))
        self.assertEqual(room['joint_contract']['state_matrix_slot'],9)
        self.assertEqual(room['joint_contract']['maximum_shown_joints'],8)
        for path in ('overlays/v3/room_joints.c','overlays/v3/room_rigs.c','overlays/v3/room_rigs.h'):
            self.assertEqual(self.report['sources'][path],sha256((ROOT/path).read_bytes()))
        from v3_furniture_reactions import state_reservation,colour_state_reservation
        self.assertEqual(state_reservation(self.report),room['reactions']['state'])
        self.assertEqual(colour_state_reservation(self.report),room['colours']['state'])
        from v3_room_effects import profile_overlay
        for row in room['effects']['profiles']:
            self.assertEqual(self.blob[row['blob_offset']:row['blob_offset']+64],
                profile_overlay(room['code']['symbols'],kind=row['kind'],code_bounds=(0x804D0000,0x804D8000)))
        for item in ('3070','309C','31AC'):
            row=next(r for r in self.report['staged_furniture']['rows'] if r['item_id']==item)
            rig=next(r for r in room['rows'] if r['source_item_id']==item)
            self.assertTrue(row['reused_asset'] and row['profile_installed'] and row['item_record_installed'])
            self.assertFalse(row['selected'] or row['acquisition_installed'] or rig['parent_selectable'])
            self.assertTrue(bindings[item]['staged'])
            self.assertEqual(sha256(self.blob[rig['blob_offset']:rig['blob_offset']+rig['bytes']]),rig['sha256'])
            self.assertEqual(rig['sha256'],row['object_sha256'])
            index=slot(int(item,16));self.assertEqual(self.blob[ROWS+index*80+4:ROWS+index*80+8],bytes(4))
            self.assertFalse(self.blob[0x40+index//8]&(1<<(index&7)))
            bad=copy.deepcopy(rig);bad['first']=0x7FFF
            with self.assertRaises(ValueError):runtime.encode_packet([bad])
            bad=copy.deepcopy(rig['source'])
            with self.assertRaisesRegex(ValueError,'native lifecycle'):
                profile(bad,rig['vrom'],limit=self.report['import_storage']['virtual_limit'],model_capacity=12288)
        old=self.prior['equipment_resources']['room_rigs']
        previous=by_vrom(self.base)[BLOB].extract(self.base)
        for row in old['rows']:
            kept=next(r for r in room['rows'] if r['source_item_id']==row['source_item_id'])
            self.assertEqual(kept,row)
            start=row['blob_offset'];self.assertEqual(self.blob[start:start+row['bytes']],previous[start:start+row['bytes']])
        for key in ('furniture','save_runtime','save_codec','translation_baseline'):
            self.assertEqual(self.report[key],self.prior[key])
        self.assertEqual(room['effects']['bank'],old['effects']['bank'])
        self.assertEqual(self.report['save_codec']['format_version'],4)
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (self.out/'asset-loader.ups').read_bytes()),self.image)

    def test_optional_composition_retains_existing_choices_and_disables_unfinished_acquisition(self):
        from tests.test_v3_room_rig_runtime import CurrentImportedRigTests
        import v3_optional_composition as composer
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(self.out/'build-lock.json')
            catalog=composer.catalogue(self.image,self.report)
            self.assertEqual(len(catalog),158)
            for item in ('3070','309C','31AC'):
                self.assertNotIn('GAFE01-r0/item/'+item,catalog)
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin
        self.rows=self.report['automatic_furniture']['imports']
        CurrentImportedRigTests.test_private_browser_selection_matches_offline_and_keeps_translation_only(self)


if __name__=='__main__':unittest.main()
