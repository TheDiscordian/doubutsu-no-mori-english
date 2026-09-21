"""Focused contact/floor preparation; no cartridge or hardware claim."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
from v3_furniture_install import inputs
from v3_furniture_pipeline import Source,prepare
from v3_furniture_contact import source_lifecycle,prepare_lifecycle,lifecycle_record,native_contract
from v3_furniture_scroll import encode_lifecycles,profile_lifecycle


class ContactFloorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(ROOT/'build/v3-start-disabled-imports-01/cartridge/build-lock.json')
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.profile=prepare(cls.source,0x33A0)[0]
        cls.prepared=prepare_lifecycle(cls.source,cls.profile,cls.image)

    def test_complete_source_and_native_dependencies(self):
        source=self.prepared['source']
        self.assertEqual(source['source_floors'],[26,48])
        self.assertEqual(source['states'],[1,2,3,4])
        self.assertEqual(source['source_steps_per_native_update'],2)
        self.assertEqual(source['constants']['fraction']['hex'],'3d23d70a')
        self.assertEqual(len(self.prepared['native']['blocks']),6)
        self.assertEqual(self.prepared['native']['floor_ram'],0x80137655)
        bad=copy.deepcopy(self.profile);bad['callback_adapter']['functions']['create']['bytes']=12
        with self.assertRaises(ValueError):source_lifecycle(self.source,bad)
        bad=copy.copy(self.source);bad.rel=bytearray(self.source.rel)
        bad.rel[self.source.sections[1][0]+0x103BC4+48]^=1
        with self.assertRaisesRegex(ValueError,'complete source room contact'):source_lifecycle(bad,self.profile)
        self.assertIsNone(source_lifecycle(self.source,prepare(self.source,0x3368)[0]))

    def test_missing_floor_is_not_a_numeric_alias_or_enabled_import(self):
        floors=self.prepared['floors']
        self.assertIsNone(floors[0]['native_index'])
        self.assertEqual(floors[0]['status'],'missing-additive-floor-import')
        self.assertEqual(floors[1]['native_index'],48)
        self.assertFalse(self.prepared['dependencies_complete'])
        row=dict(source_item_id='33A0',runtime_index=1256)
        with self.assertRaisesRegex(ValueError,'both complete native floor'):lifecycle_record(row,self.prepared)
        forged=copy.deepcopy(self.prepared);forged['dependencies_complete']=True
        forged['floors'][0]['native_index']=26;forged['floors'][0]['status']='complete-native-artwork-match'
        with self.assertRaisesRegex(ValueError,'both complete native floor'):lifecycle_record(row,forged)
        self.assertFalse(profile_lifecycle(self.profile,self.prepared['source']))
        self.assertNotIn('GAFE01-r0/item/33A0',{r['id'] for r in self.report['furniture']['imports']})

    def test_record_bounds_and_complete_prepared_code(self):
        row=dict(runtime_index=1256,mode=3,flags=0,sound=0,on=48,off=71,maximum=0,step=0)
        self.assertEqual(len(encode_lifecycles([row])),28)
        for key,value in [('on',128),('off',48),('flags',1),('sound',68),('step',1),('maximum',1)]:
            with self.assertRaises(ValueError):encode_lifecycles([dict(row,**{key:value})])
        out=ROOT/'build/v3-contact-floor-prepared-02'
        prepared=json.loads((out/'lifecycles.json').read_bytes())
        self.assertEqual(prepared['base_sha256'],sha256(self.image))
        self.assertEqual(prepared['complete_dependencies'],0)
        self.assertEqual(prepared['rows'][0]['floors'],self.prepared['floors'])
        self.assertFalse(prepared['runtime_installed'])
        code=prepared['code'];self.assertLessEqual(code['bytes'],4096)
        self.assertEqual(sha256((out/'room_scroll/code.bin').read_bytes()),code['sha256'])
        self.assertEqual(code['symbols']['add_calc'],0x8009A570)
        self.assertEqual(native_contract(self.image),self.prepared['native'])

    def test_callbacks_under_memory_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-contact-floor-') as temp:
            binary=Path(temp)/'test'
            result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_room_contact_test.c'),'-o',str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('untouched saves pass',result.stdout)


if __name__=='__main__':unittest.main()
