"""Complete reversible resources and source-compared motion, not installed gameplay."""
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
from v3_furniture_pipeline import Source,prepare,PreparedAssets,scan,rig_import_plan
from v3_furniture_reversible import CATEGORY
from v3_furniture_rigs import suffix
from aflib import sha256

ART=ROOT/os.environ.get('V3_REVERSIBLE_ART','build/v3-reversible-rigs-prepared-01')

class ReversibleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_complete_source_and_prepared_models_motion_and_unavailable_gameplay(self):
        source=self.source;prepared=prepare(source,0x1FB8);a=prepared[0]['callback_adapter']
        self.assertEqual(a['category'],CATEGORY)
        self.assertEqual((a['skeleton']['joints'],a['skeleton']['shown_joints']),(11,5))
        self.assertEqual((a['animation']['duration'],a['trigger']['sound_word']),(46,0x7A))
        self.assertEqual(a['work']['joint_bytes']+a['work']['morph_bytes'],204)
        art=json.loads((ART/'art.json').read_bytes());row=art['objects'][0]
        self.assertEqual(row['item_id'],'1FB8');self.assertFalse(row['import_ready'])
        self.assertEqual(PreparedAssets(source,[ART]).reuse(source,'1FB8',prepared)[1]['object_sha256'],row['object_sha256'])
        blob=(ART/row['object_file']).read_bytes();start=(len(prepared[1])+sum(n for _,n in prepared[6])+15)&~15
        packed,receipt=suffix(source,prepared[0],row['model_offsets'],start=start)
        self.assertEqual(blob[start:],packed);self.assertEqual(sha256(blob),row['object_sha256'])
        from tests.test_v3_furniture_pipeline import DonorTests
        DonorTests.check_complete_artwork(self,ART,art)
        for r in receipt['animations']['arrays']:
            self.assertEqual(blob[r['native_offset']:r['native_offset']+r['bytes']],
                source.data[r['donor_offset']:r['donor_offset']+r['bytes']])
        inventory=scan(source,ROOT/'build/item-identity-megasheet.xlsx',[],selected=['1FB8'])
        self.assertTrue(inventory['rows'][0]['asset_ready']);self.assertNotEqual(inventory['rows'][0]['status'],'supported')
        self.assertTrue(all(not v for v in rig_import_plan(inventory,{'equipment_resources':{'room_rigs':{'rows':[]}}},{},source=source).values()))
        for receipt in list(a['functions'].values())+[a['helpers']['sAdo_OngenTrgStart'],a['initializer']]:
            changed=copy.copy(source);data=bytearray(source.rel);data[source.sections[1][0]+receipt['offset']]^=1
            changed.rel=bytes(data)
            with self.subTest(function=receipt['symbol']),self.assertRaises(ValueError):prepare(changed,0x1FB8)

    def test_actual_donor_reversible_motion_and_extended_joint_work_under_sanitizers(self):
        text=(ROOT/'local/ac-decomp/src/furniture/ac_ike_jny_rosia01.c').read_text();functions=[]
        for name in ('aIkeJnyRosia01_ct','aIkeJnyRosia01_mv','aIkeJnyRosia01_dt'):
            start=text.index('static void '+name+'(')
            while text.index(';',start)<text.index('{',start):start=text.index('static void '+name+'(',start+1)
            functions.append(text[start:text.index('\n}',start)+2])
        with tempfile.TemporaryDirectory(prefix='v3-reversible-') as directory:
            directory=Path(directory);(directory/'donor_reversible.inc').write_text('\n\n'.join(functions))
            binary=directory/'test'
            run=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                '-I'+str(directory),str(ROOT/'tests/v3_reversible_rigs_test.c'),'-o',str(binary)],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stderr)
            run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertIn('4324 donor reversible comparisons',run.stdout)

if __name__=='__main__':unittest.main()
