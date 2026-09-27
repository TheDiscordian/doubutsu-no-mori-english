"""Complete skeleton/material category, ordinary installation, and composition."""
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
from aflib import by_vrom,sha256,apply_ups,CODE_VROM
from v3_asset_loader import BLOB
from v3_furniture_pipeline import Source,prepare,scan,rig_import_plan,PreparedAssets
from v3_furniture_install import inputs
from v3_furniture_rigs import MATERIAL_RIG_CATEGORY,suffix
from v3_room_rig_runtime import bind_profiles,encode_packet,prepared_categories
from v3_sound_programs import checked_furniture_loops

ART=ROOT/os.environ.get('V3_MATERIAL_RIG_BATCH','build/v3-material-rig-imports-01')/'prepared'


def donor_source():
    return Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())


class ResourceTests(unittest.TestCase):
    def test_complete_source_rig_materials_motion_helpers_and_plan(self):
        source=donor_source();p=prepare(source,0x3274);profile=p[0];a=profile['callback_adapter']
        self.assertEqual(a['category'],MATERIAL_RIG_CATEGORY)
        self.assertEqual((profile['skeleton']['joints'],profile['skeleton']['shown_joints']),(7,5))
        self.assertEqual([sum(len(r.get('triangles',[])) for r in m['rows']) for m in p[4].values()],[40,1,2,2,16])
        self.assertEqual(a['constructor'],dict(mode='repeat',initial_speed=.5))
        self.assertEqual((a['move_speed'],a['source_steps_per_native_update']),(1.0,2))
        self.assertEqual(a['material_frames'][0]['selector'],dict(input='graphics-frame',division=5,modulo=2))
        self.assertEqual(a['level_sound']['source_sound_id'],0x56)
        self.assertEqual(a['level_sound']['excluded_states'],[])
        inventory=scan(source,ROOT/'build/item-identity-megasheet.xlsx',[],selected=['3274'])
        self.assertEqual(rig_import_plan(inventory,{'equipment_resources':{'room_rigs':{'rows':[]}}},{},source=source),
            dict(resources=['3274'],audio=[],loops=['3274'],profiles=['3274']))
        for f in [*a['functions'].values(),a['helpers']['sAdo_OngenPos'],a['helpers']['cKF_SkeletonInfo_R_init_standard_repeat']]:
            changed=copy.copy(source);data=bytearray(source.rel);data[source.sections[1][0]+f['offset']]^=1
            changed.rel=bytes(data)
            with self.subTest(function=f['symbol']),self.assertRaises(ValueError):prepare(changed,0x3274)

    def test_full_prepared_resources_and_combined_dispatch_under_sanitizers(self):
        source=donor_source();art=json.loads((ART/'art.json').read_bytes());r=art['objects'][0]
        p=prepare(source,0x3274);blob=(ART/r['object_file']).read_bytes()
        start=(len(p[1])+sum(n for _,n in p[6])+15)&~15
        tail,receipt=suffix(source,p[0],r['model_offsets'],start=start,resources=p[2])
        self.assertEqual(blob[start:],tail);self.assertEqual(r['rig'],json.loads(json.dumps(receipt)))
        self.assertEqual(PreparedAssets(source,[ART]).reuse(source,'3274',p)[1]['object_sha256'],sha256(blob))
        for resource in receipt['animations']['arrays']:
            n=resource['bytes'];at=resource['native_offset'];origin=resource['donor_offset']
            self.assertEqual(blob[at:at+n],source.data[origin:origin+n])
        for relocation in receipt['skeleton']['relocations']+receipt['animations']['relocations']:
            self.assertEqual(struct.unpack_from('>I',blob,relocation['offset'])[0],0x06000000+relocation['target_offset'])
        from tests.test_v3_furniture_pipeline import DonorTests
        self.source=source;DonorTests.check_complete_artwork(self,ART,art)
        rows,_,_=prepared_categories(source,[ART])
        with tempfile.TemporaryDirectory(prefix='v3-material-rig-') as d:
            directory=Path(d);table=directory/'table';binary=directory/'check'
            table.write_bytes(encode_packet(rows))
            run=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',str(ROOT/'tests/v3_material_rigs_test.c'),
                '-o',str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stderr)
            run=subprocess.run([str(binary),str(table),str(ART/r['object_file'])],capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertIn('600 combined motion/draw frames',run.stdout)


class InstalledTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batch=ROOT/os.environ.get('V3_MATERIAL_RIG_BATCH','build/v3-material-rig-imports-01')
        result=json.loads((cls.batch/'pipeline.json').read_bytes())
        cls.out=(ROOT/result['final_lock']).parent;cls.image,cls.report=inputs(cls.out/'build-lock.json')
        cls.base,cls.prior=inputs(ROOT/'build/v3-switched-material-imports-02/profile-runtime/build-lock.json')
        cls.source=donor_source();cls.blob=by_vrom(cls.image)[BLOB].extract(cls.image)

    def test_complete_asset_audio_profile_acquisition_and_retained_resources(self):
        bindings=bind_profiles(self.source,self.image,self.report)
        e=self.report['equipment_resources'];room=e['room_rigs'];old=self.prior['equipment_resources']
        row=next(r for r in room['rows'] if r['source_item_id']=='3274')
        self.assertEqual((row['mode'],row['joints'],row['shown']),(8,7,5))
        self.assertTrue(row['profile_installed']);self.assertTrue(row['parent_selectable'])
        self.assertFalse(bindings['3274']['staged'])
        self.assertEqual(self.blob[row['blob_offset']:row['blob_offset']+row['bytes']],(ART/'3274.n64obj.bin').read_bytes())
        contracts,_=checked_furniture_loops(self.image,by_vrom(self.image)[CODE_VROM].extract(self.image),e,self.source)
        self.assertEqual(contracts['3274'],self.source.profile(0x3274)['callback_adapter']['level_sound'])
        imported=next(r for r in self.report['furniture']['imports'] if r['item_id']=='3274')
        self.assertTrue(imported['enabled']);self.assertFalse(imported['ordinary_stock']);self.assertTrue(imported['catalogue_orderable'])
        self.assertEqual((imported['donor_list'],imported['stock_group'],imported['birth_category']),('ftr_listLottery',5,7))
        blob=by_vrom(self.base)[BLOB].extract(self.base)
        for key in ('rows','material_rows','sound_rows'):
            for r in old['room_rigs'][key]:
                kept=next(x for x in room[key] if x['source_item_id']==r['source_item_id'])
                self.assertEqual(kept,r)
                if 'blob_offset' in r:
                    at=r['blob_offset'];self.assertEqual(self.blob[at:at+r['bytes']],blob[at:at+r['bytes']])
        for key in ('room_goods','room_carry'):self.assertEqual(e[key],old[key])
        self.assertEqual(self.report['save_codec'],self.prior['save_codec'])
        flags=bytearray.fromhex(self.prior['save_runtime']['profile_hex'])
        from v3_import_storage import slot
        i=slot(0x3274);flags[0x20+i//8]|=1<<(i&7)
        self.assertEqual(self.report['save_runtime']['profile_hex'],flags.hex())
        inventory=scan(self.source,ROOT/'build/item-identity-megasheet.xlsx',[],selected=['3274'])
        self.assertTrue(all(not v for v in rig_import_plan(inventory,self.report,bindings,source=self.source).values()))
        self.assertLessEqual(room['code']['bytes'],32768);self.assertLessEqual(room['bootstrap']['bytes'],1536)
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (self.out/'asset-loader.ups').read_bytes()),self.image)

    def test_private_browser_and_offline_compositions_include_optional_rig(self):
        from tests.test_v3_room_rig_runtime import CurrentImportedRigTests
        self.rows=[r for r in self.report['furniture']['imports'] if r['item_id']=='3274']
        CurrentImportedRigTests.test_private_browser_selection_matches_offline_and_keeps_translation_only(self)


if __name__=='__main__':unittest.main()
