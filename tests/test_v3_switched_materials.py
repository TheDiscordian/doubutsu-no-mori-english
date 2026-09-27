"""Switched screens reuse complete material, audio, and profile import paths."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,apply_ups,CODE_VROM
from v3_asset_loader import BLOB
from v3_furniture_pipeline import Source,prepare,scan,rig_import_plan,ReviewRequired
from v3_furniture_install import inputs,profile
from v3_furniture_materials import switched_lifecycle,checked_switched,runtime_record
from v3_room_rig_runtime import bind_profiles,encode_materials
from v3_sound_programs import checked_furniture_loops


def donor_source():
    return Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())


class SourceTests(unittest.TestCase):
    def test_complete_frames_callbacks_helpers_and_shared_plan(self):
        source=donor_source();prepared=prepare(source,0x32E4);p=prepared[0]
        a=p['callback_adapter'];material=a['material_frames'][0]
        self.assertEqual(a['model_order'],['part0','part1'])
        self.assertEqual([sum(len(r.get('triangles',[])) for r in m['rows']) for m in prepared[4].values()],[2,35])
        self.assertEqual([r['symbol'] for r in material['frames']],
            [f'int_iku_turkey_TV_{c}_tex_txt' for c in 'ghihf'])
        self.assertEqual([r['bytes'] for r in material['frames']],[128]*5)
        self.assertEqual(material['frames'][1],material['frames'][3])
        lifecycle=switched_lifecycle(source,p)
        self.assertEqual((lifecycle['source_sound_id'],lifecycle['switch_clicks']),(0x5E,[0x16,0x17]))
        self.assertTrue(lifecycle['start_disabled']);self.assertEqual(lifecycle['click_excluded_states'],[])
        inventory=scan(source,ROOT/'build/item-identity-megasheet.xlsx',[],selected=['32E4'])
        self.assertEqual(rig_import_plan(inventory,{'equipment_resources':{'room_rigs':{'rows':[]}}},{},source=source),
            dict(resources=[],audio=[],loops=['32E4'],profiles=['32E4'],materials=['32E4']))
        for fn in [*a['functions'].values(),*lifecycle['helpers'].values()]:
            changed=copy.copy(source);data=bytearray(source.rel)
            data[source.sections[1][0]+fn['offset']]^=1;changed.rel=bytes(data)
            with self.assertRaises((ValueError,ReviewRequired)):
                switched_lifecycle(changed,p) if fn['symbol']!='fITT_dw' else prepare(changed,0x32E4)
        off=material['frames'][-1];changed=copy.copy(source);data=bytearray(source.rel)
        data[source.sections[5][0]+off['donor_offset']]^=1;changed.rel=bytes(data)
        changed.data=bytes(data[source.sections[5][0]:source.sections[5][0]+source.sections[5][1]])
        self.assertNotEqual(prepare(changed,0x32E4)[0]['callback_adapter']['material_frames'][0]['frames'][-1],off)


class InstalledTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batch=ROOT/os.environ.get('V3_SWITCHED_MATERIAL_BATCH','build/v3-switched-material-imports-02')
        pipeline=json.loads((cls.batch/'pipeline.json').read_bytes())
        cls.out=(ROOT/pipeline['final_lock']).parent
        cls.image,cls.report=inputs(cls.out/'build-lock.json')
        cls.base,cls.prior=inputs(ROOT/'build/v3-selected-palette-runtime-04/build-lock.json')
        cls.source=donor_source();cls.blob=by_vrom(cls.image)[BLOB].extract(cls.image)
        cls.room=cls.report['equipment_resources']['room_rigs']
        cls.row=next(r for r in cls.room['material_rows'] if r['source_item_id']=='32E4')

    def test_actual_dispatch_frames_clicks_and_bounds_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-switched-material-') as d:
            directory=Path(d);binary=directory/'check';table=directory/'table.bin'
            table.write_bytes(encode_materials([self.row]))
            run=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-ffunction-sections','-fdata-sections',
                '-Wl,--gc-sections','-DAF_V3_ROOM_RIG_PACKET','-DAF_V3_ROOM_TRIGGER_SOUND',
                '-DAF_V3_ROOM_MATERIALS','-DAF_V3_ROOM_SWITCHED_MATERIAL',
                str(ROOT/'tests/v3_room_materials_test.c'),'-o',str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stderr)
            run=subprocess.run([str(binary),str(table)],capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertIn('immutable assets, and bounds',run.stdout)

    def test_complete_installed_art_audio_placement_profiles_and_retention(self):
        bindings=bind_profiles(self.source,self.image,self.report);binding=bindings['32E4']
        self.assertTrue(binding['staged']);self.assertTrue(self.row['profile_installed'])
        self.assertFalse(self.row['parent_selectable'])
        self.assertEqual((self.row['mode'],self.row['lifecycle'],self.row['state_offset'],self.row['divisor']),
            (3,5,0x5E,6))
        self.assertEqual(self.row['frame_offsets'][1],self.row['frame_offsets'][3])
        contracts,_=checked_furniture_loops(self.image,by_vrom(self.image)[CODE_VROM].extract(self.image),
            self.report['equipment_resources'],self.source)
        descriptor=self.source.profile(0x32E4)
        checked_switched(self.source,descriptor,self.row,contracts,binding['room_placement'])
        art=json.loads((self.batch/'prepared/art.json').read_bytes())['objects'][0]
        self.assertEqual(self.blob[self.row['blob_offset']:self.row['blob_offset']+self.row['bytes']],
            (self.batch/'prepared'/art['object_file']).read_bytes())
        for key in ('mode','divisor','frame_offsets','model_offsets','frame_bytes','kind','segment'):
            self.assertEqual(self.row[key],runtime_record(art)[key])
        # Assets alone and unbound fresh-placement state never enable the profile.
        with self.assertRaises(ValueError):profile(art,self.row['vrom'],limit=self.report['import_storage']['virtual_limit'])
        for key,value in (('lifecycle',0),('mode',0),('state_offset',0x54),('lifecycle_installed',False)):
            bad=copy.deepcopy(self.row);bad[key]=value
            with self.assertRaises(ValueError):checked_switched(self.source,descriptor,bad,contracts,binding['room_placement'])
        with self.assertRaises(ValueError):checked_switched(self.source,descriptor,self.row,contracts,None)
        old=self.prior['equipment_resources'];blob=by_vrom(self.base)[BLOB].extract(self.base)
        for key in ('rows','sound_rows','material_rows'):
            for row in old['room_rigs'][key]:
                kept=next(r for r in self.room[key] if r['source_item_id']==row['source_item_id'])
                self.assertEqual(kept,row)
                if 'blob_offset' in row:
                    at=row['blob_offset'];self.assertEqual(self.blob[at:at+row['bytes']],blob[at:at+row['bytes']])
        for key in ('room_goods','room_carry'):self.assertEqual(self.report['equipment_resources'][key],old[key])
        self.assertEqual(self.report['save_codec'],self.prior['save_codec'])
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        provenance=json.loads((ROOT/'translations/provenance.json').read_bytes())['entries']
        entry=next(r for r in provenance if r['id']=='GAFE01-r0/item/32E4/name')
        self.assertEqual(entry['locales']['en']['credit'],'official')
        self.assertEqual(entry['locales']['en']['text'],'harvest TV')
        self.assertLessEqual(self.room['code']['bytes'],32768);self.assertLessEqual(self.room['bootstrap']['bytes'],1536)
        inventory=scan(self.source,ROOT/'build/item-identity-megasheet.xlsx',[],selected=['32E4'])
        plan=rig_import_plan(inventory,self.report,bindings,source=self.source)
        self.assertTrue(all(not v for v in plan.values()),plan)
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (self.out/'asset-loader.ups').read_bytes()),self.image)

    def test_private_browser_and_offline_compositions_keep_staged_item_disabled(self):
        from tests.test_v3_room_rig_runtime import CurrentImportedRigTests
        self.rows=self.report['automatic_furniture']['imports']
        CurrentImportedRigTests.test_private_browser_selection_matches_offline_and_keeps_translation_only(self)


if __name__=='__main__':unittest.main()
