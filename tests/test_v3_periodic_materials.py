"""Complete timed-texture models and shared periodic-steam integration."""
import copy
import json
import os
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,apply_ups,CODE_VROM
from v3_asset_loader import BLOB
from v3_furniture_pipeline import Source,prepare,scan,rig_import_plan
from v3_furniture_install import inputs
from v3_furniture_materials import steam_lifecycle,checked_steam
from v3_room_rig_runtime import bind_profiles
from v3_sound_programs import checked_furniture_loops
import tests.test_v3_equipment_runtime as shared


def source():
    return Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())


class SourceTests(unittest.TestCase):
    def test_complete_timed_texture_and_steam_contract(self):
        donor=source();p=prepare(donor,0x33C0);a=p[0]['callback_adapter']
        self.assertEqual(a['model_order'],['part0','part1','part2'])
        self.assertEqual([sum(len(r.get('triangles',[])) for r in m['rows']) for m in p[4].values()],
            [16,26,2])
        frames=a['material_frames'][0]
        self.assertEqual((frames['kind'],frames['segment_address'],len(frames['frames'])),('texture',0x08000000,2))
        self.assertEqual(frames['selector'],dict(input='room-or-preview-frame',division=6,modulo=2))
        lifecycle=steam_lifecycle(donor,p[0])
        self.assertEqual([lifecycle[k] for k in ('source_sound_id','source_period','native_period','height','spread')],
            [0x54,8,4,15.0,10])
        self.assertEqual(set(lifecycle['functions']),{'create','move','destroy'})
        damaged=copy.copy(donor);raw=bytearray(donor.rel)
        raw[donor.sections[4][0]+49768]^=1;damaged.rel=bytes(raw)
        with self.assertRaisesRegex(ValueError,'periodic material'):
            steam_lifecycle(damaged,p[0])
        damaged=copy.deepcopy(p[0]);damaged['callback_adapter']['material_frames'][0]['selector']['division']=3
        with self.assertRaises(ValueError):steam_lifecycle(donor,damaged)

    def test_shared_emitters_and_three_part_draw_under_sanitizers(self):
        shared.HostTests.sanitized(self,'v3_room_emitters_test.c')


class InstalledTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        batch=json.loads((ROOT/os.environ.get('V3_PERIODIC_MATERIAL_BATCH',
            'build/v3-periodic-material-imports-04')/'pipeline.json').read_bytes())
        lock=ROOT/batch['final_lock'];cls.out=lock.parent
        cls.image,cls.report=inputs(lock)
        cls.base,cls.prior=inputs(ROOT/'build/v3-particle-interaction-imports-03/cartridge/build-lock.json')
        cls.source=source()

    def test_complete_material_audio_artwork_and_no_pending_dependencies(self):
        bindings=bind_profiles(self.source,self.image,self.report)
        room=self.report['equipment_resources']['room_rigs']
        row=next(r for r in room['material_rows'] if r['source_item_id']=='33C0')
        self.assertEqual((row['lifecycle'],row['state_offset'],row['mode'],row['divisor']),(4,0x54,0,6))
        contracts,_=checked_furniture_loops(self.image,by_vrom(self.image)[CODE_VROM].extract(self.image),
            self.report['equipment_resources'],self.source)
        checked_steam(self.source,prepare(self.source,0x33C0)[0],row,contracts,room['effects'])
        blob=by_vrom(self.image)[BLOB].extract(self.image)
        directory=ROOT/'build/v3-periodic-material-imports-01/prepared'
        art=json.loads((directory/'art.json').read_bytes())['objects'][0]
        self.assertEqual(blob[row['blob_offset']:row['blob_offset']+row['bytes']],
            (directory/art['object_file']).read_bytes())
        old=self.prior['equipment_resources']['room_rigs']
        for prior in old['material_rows']:
            kept=next(r for r in room['material_rows'] if r['source_item_id']==prior['source_item_id'])
            self.assertEqual(kept,prior)
        self.assertEqual(room['effects']['bank'],old['effects']['bank'])
        inventory=scan(self.source,ROOT/'build/item-identity-megasheet.xlsx',[],selected=['33C0'])
        plan=rig_import_plan(inventory,self.report,bindings,source=self.source)
        self.assertTrue(all(not values for values in plan.values()),plan)
        self.assertEqual(self.report['save_codec'],self.prior['save_codec'])
        self.assertEqual({k:v for k,v in self.report['save_runtime'].items() if not k.startswith('profile_')},
            {k:v for k,v in self.prior['save_runtime'].items() if not k.startswith('profile_')})
        self.assertLessEqual(room['code']['bytes'],16384)
        self.assertLessEqual(room['bootstrap']['bytes'],1536)
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (self.out/'asset-loader.ups').read_bytes()),self.image)

    def test_actual_acquisition_and_browser_offline_composition(self):
        from tests.test_v3_room_rig_runtime import CurrentImportedRigTests
        self.rows=[r for r in self.report['furniture']['imports'] if r['item_id']=='33C0']
        self.assertEqual(len(self.rows),1)
        self.assertEqual(self.rows[0]['donor_list'],'ftr_listKamakura')
        self.assertTrue(self.rows[0]['enabled'])
        self.assertFalse(self.rows[0]['catalogue_orderable'])
        CurrentImportedRigTests.test_private_browser_selection_matches_offline_and_keeps_translation_only(self)


if __name__=='__main__':unittest.main()
