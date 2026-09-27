"""Complete combined reversible/material/effect category, including donor parity."""
import copy
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256,by_vrom,apply_ups
from v3_furniture_pipeline import Source,prepare,PreparedAssets,scan,rig_import_plan
from v3_furniture_effect_rigs import CATEGORY
from v3_furniture_install import inputs
from v3_asset_loader import BLOB
ART=ROOT/'build/v3-effect-rigs-prepared-01'

class EffectRigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_complete_source_resources_and_planner(self):
        from tests.test_v3_furniture_pipeline import DonorTests
        from v3_furniture_rigs import suffix
        source=self.source;prepared=prepare(source,0x319C);adapter=prepared[0]['callback_adapter']
        self.assertEqual((adapter['category'],adapter['vtable_symbol']),(CATEGORY,'fNNB_func'))
        self.assertEqual((adapter['skeleton']['joints'],adapter['skeleton']['shown_joints'],adapter['animation']['duration']),(4,3,8))
        art=json.loads((ART/'art.json').read_bytes());row=art['objects'][0]
        DonorTests.check_complete_artwork(self,ART,art)
        self.assertEqual(PreparedAssets(source,[ART]).reuse(source,'319C',prepared)[1]['object_sha256'],row['object_sha256'])
        blob=(ART/row['object_file']).read_bytes();start=(len(prepared[1])+sum(n for _,n in prepared[6])+15)&~15
        packed,receipt=suffix(source,prepared[0],row['model_offsets'],start=start,resources=row['resources'])
        self.assertEqual(blob[start:],packed)
        values=struct.unpack('>fI4B2H5H6x',bytes.fromhex(receipt['material_hex']))
        self.assertEqual(values[:8],(8,0x06000000+row['model_offsets']['joint2'],8,5,0x50,2,19,128))
        self.assertEqual(values[8],values[9]);self.assertEqual(values[10],values[11])
        inventory=scan(source,ROOT/'build/item-identity-megasheet.xlsx',[],selected=['319C'])
        plan=rig_import_plan(inventory,{'equipment_resources':{'room_rigs':{'rows':[]}}},{},source=source)
        self.assertEqual((plan['resources'],plan['loops'],plan['profiles'],plan['particles']),(['319C'],['319C'],['319C'],['steam']))
        self.assertFalse(plan['audio'])
        for receipt in list(adapter['functions'].values())+adapter['joint_callbacks']:
            changed=copy.copy(source);data=bytearray(source.rel);data[source.sections[1][0]+receipt['offset']]^=1;changed.rel=bytes(data)
            with self.subTest(function=receipt['symbol']),self.assertRaises(ValueError):prepare(changed,0x319C)

    def test_complete_dispatch_against_donor_under_sanitizers(self):
        from v3_room_rig_runtime import prepared_categories,encode_packet
        rows,_,_=prepared_categories(self.source,[ART])
        text=(ROOT/'local/ac-decomp/src/furniture/ac_nog_nabe.c').read_text();functions=[]
        for name in ('fNNB_ct','fNNB_mv','fNNB_dt'):
            start=text.index('\nvoid '+name+'(')+1;functions.append(text[start:text.index('\n}',start)+2])
        with tempfile.TemporaryDirectory(prefix='v3-effect-rig-') as d:
            directory=Path(d);table=directory/'table';binary=directory/'check'
            table.write_bytes(encode_packet(rows));(directory/'donor_effect_rig.inc').write_text('\n\n'.join(functions))
            run=subprocess.run(['cc','-std=gnu11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                '-I'+str(directory),str(ROOT/'tests/v3_effect_rigs_test.c'),'-o',str(binary)],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stderr)
            run=subprocess.run([str(binary),str(table),str(ART/'319C.n64obj.bin')],capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertIn('8008 donor effect-rig comparisons; 4000 draw frames',run.stdout)

class InstalledTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batch=ROOT/os.environ.get('V3_EFFECT_RIG_BATCH','build/v3-effect-rig-imports-01')
        result=json.loads((cls.batch/'pipeline.json').read_bytes());cls.out=(ROOT/result['final_lock']).parent
        cls.image,cls.report=inputs(cls.out/'build-lock.json')
        cls.base,cls.prior=inputs(ROOT/'build/v3-reversible-rig-imports-03/cartridge/build-lock.json')
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_complete_installed_category_and_retained_resources(self):
        from v3_room_rig_runtime import bind_profiles
        bindings=bind_profiles(self.source,self.image,self.report)
        e=self.report['equipment_resources'];room=e['room_rigs'];old=self.prior['equipment_resources']
        row=next(r for r in room['rows'] if r['source_item_id']=='319C')
        self.assertEqual((row['mode'],row['joints'],row['shown']),(10,4,3))
        self.assertTrue(row['profile_installed']);self.assertFalse(bindings['319C']['staged'])
        blob=by_vrom(self.image)[BLOB].extract(self.image);previous=by_vrom(self.base)[BLOB].extract(self.base)
        self.assertEqual(blob[row['blob_offset']:row['blob_offset']+row['bytes']],(ART/'319C.n64obj.bin').read_bytes())
        for key in ('rows','sound_rows','material_rows'):
            for prior in old['room_rigs'][key]:
                kept=next(r for r in room[key] if r['source_item_id']==prior['source_item_id'])
                self.assertEqual(kept,prior)
                if 'blob_offset' in prior:
                    at=prior['blob_offset'];self.assertEqual(blob[at:at+prior['bytes']],previous[at:at+prior['bytes']])
        for key in ('room_goods','room_carry'):self.assertEqual(e[key],old[key])
        effects=copy.deepcopy(room['effects']);prior_effects=copy.deepcopy(old['room_rigs']['effects'])
        from v3_room_effects import profile_overlay
        profiles=effects.pop('profiles');old_profiles=prior_effects.pop('profiles')
        self.assertEqual(effects,prior_effects)
        for current,prior in zip(profiles,old_profiles,strict=True):
            self.assertEqual({k:v for k,v in current.items() if k not in ('callbacks','sha256')},
                {k:v for k,v in prior.items() if k not in ('callbacks','sha256')})
            at=current['blob_offset'];data=blob[at:at+current['bytes']]
            self.assertEqual(data,profile_overlay(room['code']['symbols'],kind=current['kind'],code_bounds=(0x804D0000,0x804D8000)))
            self.assertEqual(sha256(data),current['sha256'])
        self.assertEqual(self.report['save_codec'],self.prior['save_codec'])
        imported=next(r for r in self.report['furniture']['imports'] if r['id'].endswith('/319C'))
        self.assertEqual(imported['name'],'crab stew');self.assertTrue(imported['enabled'])
        self.assertEqual((imported['price'],imported['donor_list'],imported['stock_group'],imported['birth_category']),
            (1380,'ftr_listKamakura',19,3))
        self.assertFalse(imported['ordinary_stock']);self.assertFalse(imported['catalogue_orderable'])
        from v3_import_storage import slot
        flags=bytearray.fromhex(self.prior['save_runtime']['profile_hex']);i=slot(0x319C);flags[0x20+i//8]|=1<<(i&7)
        self.assertEqual(self.report['save_runtime']['profile_hex'],flags.hex())
        self.assertIn(imported['id']+'/name',{r['id'] for r in json.loads((ROOT/'translations/provenance.json').read_bytes())['entries']})
        inventory=scan(self.source,ROOT/'build/item-identity-megasheet.xlsx',[],selected=['319C'])
        self.assertTrue(all(not values for values in rig_import_plan(inventory,self.report,bindings,source=self.source).values()))
        self.assertLessEqual(room['code']['bytes'],32768);self.assertLessEqual(room['bootstrap']['bytes'],1536)
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),(self.out/'asset-loader.ups').read_bytes()),self.image)

    def test_private_browser_and_offline_composition(self):
        from tests.test_v3_room_rig_runtime import CurrentImportedRigTests
        self.rows=[r for r in self.report['furniture']['imports'] if r['id'].endswith('/319C')];self.assertEqual(len(self.rows),1)
        CurrentImportedRigTests.test_private_browser_selection_matches_offline_and_keeps_translation_only(self)

if __name__=='__main__':unittest.main()
