"""Current contact/floor installation and shared category retention checks."""
import copy
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_VROM,by_vrom,sha256
from v3_asset_loader import BLOB
from v3_furniture_install import inputs
from v3_furniture_pipeline import Source,prepare
from v3_furniture_contact import checked_contracts,lifecycle_record,prepare_lifecycle
from v3_furniture_scroll import SOURCES,checked_runtime,profile_lifecycle,tables
from v3_room_rig_runtime import bind_profiles
from v3_sound_programs import checked_furniture_loops
import v3_optional_composition as composer

OUT=ROOT/'build/v3-contact-floor-runtime-04'


class ContactRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        composer.use_build_lock(OUT/'build-lock.json')
        cls.image,cls.report=inputs(OUT/'build-lock.json')
        cls.base,cls.prior=inputs(OUT/'base-lock.json')
        cls.blob=by_vrom(cls.image)[BLOB].extract(cls.image)
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.contracts=checked_contracts(cls.source,cls.image,cls.report)

    @classmethod
    def tearDownClass(cls):
        composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=cls.pin

    def test_complete_floor_identity_binding_and_mutations(self):
        self.assertEqual(set(self.contracts),{'33A0'})
        contract=self.contracts['33A0'];floors=contract['floors']
        self.assertEqual([(r['source_index'],r['native_index']) for r in floors],[(26,74),(48,48)])
        self.assertTrue(contract['dependencies_complete'])
        self.assertEqual(floors[0]['status'],'complete-additive-floor-import')
        self.assertEqual(len(contract['native']['blocks']),6)
        profile=prepare(self.source,0x33A0)[0]
        # Absent import bindings are still missing; native slot 26 is never a fallback.
        absent=prepare_lifecycle(self.source,profile,self.image)
        self.assertFalse(absent['dependencies_complete']);self.assertIsNone(absent['floors'][0]['native_index'])
        row=dict(source_item_id='33A0',runtime_index=1256)
        self.assertEqual(lifecycle_record(row,contract)['on'],74)
        bad=copy.deepcopy(contract);bad['floors'][0]['native_index']=26
        with self.assertRaisesRegex(ValueError,'complete native floor'):lifecycle_record(row,bad)
        bad=copy.deepcopy(self.report)
        next(r for r in bad['room_surfaces']['rows'] if r['source_item_id']=='261A')['destination_index']=26
        with self.assertRaisesRegex(ValueError,'additive contact floor'):checked_contracts(self.source,self.image,bad)
        bad=bytearray(self.image);entry=by_vrom(self.image)[BLOB]
        floor=next(r for r in self.report['room_surfaces']['rows'] if r['source_item_id']=='261A')
        bad[entry.pstart+floor['blob_offset']+64]^=1
        with self.assertRaisesRegex(ValueError,'additive contact floor'):checked_contracts(self.source,bad,self.report)

    def test_installed_category_preserves_profiles_assets_and_optional_output(self):
        equipment=self.report['equipment_resources'];runtime=equipment['room_rigs']['scrolling']
        rows=checked_runtime(equipment,self.blob);row=rows['33A0']
        self.assertTrue(row['lifecycle_installed']);self.assertFalse(row['profile_installed'])
        self.assertFalse(row['parent_selectable'])
        self.assertEqual(row['lifecycle'],json.loads(json.dumps(self.contracts['33A0'])))
        record=next(r for r in runtime['lifecycle_rows'] if r['source_item_id']=='33A0')
        self.assertEqual(record,json.loads(json.dumps(lifecycle_record(row,self.contracts['33A0']))))
        self.assertEqual((record['mode'],record['on'],record['off']),(3,74,48))
        packet=runtime['packet'];data=self.blob[packet['blob_offset']:packet['blob_offset']+packet['bytes']]
        self.assertEqual(data[4096:],tables(runtime));self.assertLessEqual(runtime['code']['bytes'],4096)
        self.assertIn('-DAF_V3_ROOM_CONTACT=1',runtime['code']['flags'])
        self.assertEqual(runtime['code']['symbols']['add_calc'],0x8009A570)
        previous=self.prior['equipment_resources']['room_rigs']['scrolling']
        for old in previous['rows']:
            now=rows[old['source_item_id']]
            for key in ('blob_offset','vrom','bytes','sha256','source','profile_installed','parent_selectable'):
                self.assertEqual(now[key],old[key])
        for key in ('room_surfaces','save_codec','save_runtime','staged_furniture'):
            self.assertEqual(self.report[key],self.prior[key])
        self.assertEqual(equipment['sound_programs'],self.prior['equipment_resources']['sound_programs'])
        self.assertEqual(by_vrom(self.image)[CODE_VROM].extract(self.image),by_vrom(self.base)[CODE_VROM].extract(self.base))
        self.assertFalse(self.report['saved_format_changed']);self.assertEqual(len(self.blob),len(by_vrom(self.base)[BLOB].extract(self.base)))
        # A complete alpha update must not enable unfinished movement sounds.
        self.assertFalse(profile_lifecycle(prepare(self.source,0x33A0)[0],self.contracts['33A0']))
        bindings=bind_profiles(self.source,self.image,self.report)
        self.assertNotIn('33A0',bindings)
        self.assertEqual(len(bindings),len(bind_profiles(self.source,self.base,self.prior)))
        catalogue=composer.catalogue(self.image,self.report)
        self.assertEqual(len(catalogue),147);self.assertNotIn('GAFE01-r0/item/33A0',catalogue)
        self.assertEqual(composer.compose(self.image,self.report,catalogue,
            composer.resolve(catalogue,list(catalogue)))[0],self.image)
        self.assertEqual(sha256(composer.compose(self.image,self.report,catalogue,
            composer.resolve(catalogue,[]))[0]),self.report['translation_baseline']['sha256'])
        for path in SOURCES:self.assertEqual(sha256((ROOT/path).read_bytes()),self.report['sources'][path])

    def test_extended_movement_table_preserves_complete_switch_clicks(self):
        equipment=self.report['equipment_resources'];core=by_vrom(self.image)[CODE_VROM].extract(self.image)
        contracts,proof=checked_furniture_loops(self.image,core,equipment,self.source)
        self.assertEqual(len(contracts),4);self.assertTrue(proof['complete_programs_and_instruments'])
        self.assertTrue(proof['clicks'])
        bad=copy.deepcopy(equipment)
        bad['sound_programs']['surface_batch']['movement_table']['offset']-=2
        with self.assertRaisesRegex(ValueError,'click dispatch'):checked_furniture_loops(self.image,core,bad,self.source)

    def test_contact_callbacks_under_memory_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-contact-installed-') as temporary:
            binary=Path(temporary)/'contact'
            result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_room_contact_test.c'),'-o',str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('untouched saves pass',result.stdout)


if __name__=='__main__':unittest.main()
