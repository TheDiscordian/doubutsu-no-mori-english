"""Current shared material renderer, complete frame tables, and inactive routing."""
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
from aflib import by_vrom,sha256,apply_ups
from v3_asset_loader import BLOB
from v3_equipment_runtime import RAM as EQUIPMENT_RAM
from v3_furniture_install import inputs
from v3_furniture_pipeline import Source,prepare,metadata,identity_rows
from v3_import_storage import ROWS,TABLE_END
import v3_furniture_materials as materials
import v3_room_rig_runtime as runtime
import v3_optional_composition as composer

OUT=ROOT/'build/v3-material-frames-runtime-02'
ART=ROOT/'build/v3-material-frames-prepared-01'


class MaterialRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUT/'build-lock.json')
        cls.base,cls.prior=inputs(ROOT/'build/v3-shared-fixed-clock-profiles-01/build-lock.json')
        cls.blob=by_vrom(cls.image)[BLOB].extract(cls.image)
        cls.old=by_vrom(cls.base)[BLOB].extract(cls.base)
        cls.runtime=cls.report['equipment_resources']['room_rigs']
        cls.art=json.loads((ART/'art.json').read_bytes())
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_complete_source_records_assets_packet_and_stable_identity(self):
        rows=self.runtime['material_rows'];self.assertEqual(len(rows),6)
        self.assertEqual(sum(r['bytes'] for r in rows),17104)
        for row in rows:
            art=next(r for r in self.art['objects'] if r['item_id']==row['source_item_id'])
            expected=materials.runtime_record(art)
            self.assertEqual({k:v for k,v in row.items() if k not in ('blob_offset','vrom')},expected)
            self.assertEqual(self.blob[row['blob_offset']:row['blob_offset']+row['bytes']],(ART/art['object_file']).read_bytes())
            self.assertTrue(row['renderer_installed'])
            self.assertFalse(any(row[k] for k in ('lifecycle_installed','profile_installed','parent_selectable')))
        mouth=next(r for r in rows if r['source_item_id']=='1FD8')
        self.assertEqual((mouth['item_id'],mouth['runtime_index'],mouth['mode'],mouth['state_offset']),('3C30',1804,2,0x1A4))
        sheet=identity_rows(ROOT/'build/item-identity-megasheet.xlsx',extra_items=[0x1FD8])[0x1FD8]
        self.assertEqual(sheet[0],2392)
        self.assertTrue(all(sheet[1][k]=='-' for k in ('C','H','CG','CJ')))
        for path in ('translations/item_reference_matches.json','translations/item_resolved_matches.json'):
            matches=json.loads((ROOT/path).read_bytes())
            self.assertFalse(any(r.get('reference_id','').lower()=='furniture:03f6' for r in matches))
        packet=self.runtime['packet'];raw=self.blob[packet['blob_offset']:packet['blob_offset']+packet['bytes']]
        self.assertEqual(raw,(OUT/'room_rigs_packet/code.bin').read_bytes().ljust(4096,b'\0')+
            runtime.encode_packet(self.runtime['rows'],self.runtime['sound_rows'],rows))
        self.assertEqual(sha256(raw),packet['sha256'])
        self.assertLess(self.runtime['code']['bytes'],4096)
        e=self.report['equipment_resources'];module=self.blob[e['blob_offset']:e['blob_offset']+e['bytes']]
        self.assertEqual(module[runtime.MATERIAL_VTABLE-EQUIPMENT_RAM:runtime.MATERIAL_VTABLE-EQUIPMENT_RAM+20],
            struct.pack('>5I',0,0,self.runtime['bootstrap']['symbols']['af_v3_room_boot_material_dw'],0,0))
        self.assertEqual(module[runtime.TABLE-EQUIPMENT_RAM:runtime.TABLE-EQUIPMENT_RAM+4],bytes(4))

    def test_renderer_timing_and_bounds_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-room-materials-') as temporary:
            binary=Path(temporary)/'test';table=Path(temporary)/'table'
            table.write_bytes(runtime.encode_materials(self.runtime['material_rows']))
            result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',str(ROOT/'tests/v3_room_materials_test.c'),
                '-o',str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(binary),str(table)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('immutable assets, and bounds',result.stdout)

    def test_invalid_tables_and_unfinished_lifecycles_are_rejected(self):
        rows=self.runtime['material_rows']
        for key,value in (('bytes',9217),('segment',7),('mode',3),('frame_bytes',0),
                          ('model_offsets',[65528]),('frame_offsets',[65528]),('state_offset',0x82C)):
            bad=copy.deepcopy(rows);bad[0][key]=value
            with self.assertRaises(ValueError):runtime.encode_materials(bad)
        with self.assertRaises(ValueError):runtime.encode_materials(rows+rows)
        with self.assertRaises(ValueError):runtime.encode_materials(list(reversed(rows)))
        bad=copy.deepcopy(self.art['objects'][0]);bad['profile']['callback_adapter']['material_frames'][0]['selector']['offset']=0x1A4
        with self.assertRaises(ValueError):materials.runtime_record(bad)
        identities=identity_rows(ROOT/'build/item-identity-megasheet.xlsx',include_unmapped_legacy=True)
        for row in rows:
            item=int(row['source_item_id'],16);profile=prepare(self.source,item)[0]
            profile['callback_adapter']['runtime_installed']=True
            with self.assertRaisesRegex(ValueError,'lifecycle behaviour'):
                metadata(self.source,item,profile,identities[item])
        self.assertEqual(len(runtime.bind_profiles(self.source,self.image,self.report)),23)

    def test_retained_resources_profiles_saves_and_optional_composition(self):
        prior=self.prior['equipment_resources'];current=self.report['equipment_resources']
        for key in ('rows','sound_rows'):
            self.assertEqual(self.runtime[key],prior['room_rigs'][key])
            for row in self.runtime[key]:
                if 'blob_offset' in row:
                    a=row['blob_offset'];self.assertEqual(self.blob[a:a+row['bytes']],self.old[a:a+row['bytes']])
        self.assertEqual(self.blob[ROWS:TABLE_END],self.old[ROWS:TABLE_END])
        self.assertEqual(self.report['staged_furniture'],self.prior['staged_furniture'])
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        self.assertEqual(current['furniture_audio'],prior['furniture_audio'])
        self.assertEqual(current['scenery'],prior['scenery'])
        self.assertEqual(current['bytes'],prior['bytes'])
        self.assertEqual(self.report['shared_runtime_refresh']['additional_resident_bytes'],0)
        self.assertIn('material_frames',self.report['shared_runtime_refresh']['adapters'])
        self.assertTrue(self.report['shared_runtime_refresh']['artwork_changed'])
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(OUT/'build-lock.json');catalog=composer.catalogue(self.image,self.report)
            self.assertEqual(len(catalog),136)
            self.assertFalse({r['source']['id'] for r in self.runtime['material_rows']}&set(catalog))
            self.assertEqual(sha256(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,[]))[0]),
                self.report['translation_baseline']['sha256'])
            self.assertEqual(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,list(catalog)))[0],self.image)
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (OUT/'asset-loader.ups').read_bytes()),self.image)


class MaterialProfileIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out=ROOT/'build/v3-material-trigger-profiles-02'
        cls.image,cls.report=inputs(cls.out/'build-lock.json')
        cls.base,cls.prior=inputs(cls.out/'base-lock.json')
        cls.blob=by_vrom(cls.image)[BLOB].extract(cls.image)
        cls.old=by_vrom(cls.base)[BLOB].extract(cls.base)
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.rows=[r for r in cls.report['staged_furniture']['rows'] if r['category']==materials.CATEGORY]

    def test_complete_profiles_reuse_existing_artwork_runtime_and_names(self):
        from v3_import_storage import ITEMS,slot
        self.assertEqual({r['item_id'] for r in self.rows},{'3314','3318','332C'})
        self.assertEqual(len(self.report['staged_furniture']['rows']),26)
        self.assertEqual({r['source_item_id'] for r in self.report['staged_furniture']['deferred_resources']},
            {'1FD8','3298','331C'})
        self.assertEqual(self.report['blob_bytes'],self.prior['blob_bytes'])
        e=self.report['equipment_resources'];old_e=self.prior['equipment_resources']
        a=e['blob_offset'];self.assertEqual(self.blob[a:a+e['bytes']],self.old[a:a+e['bytes']])
        p=e['room_rigs']['packet'];a=p['blob_offset'];self.assertEqual(p,old_e['room_rigs']['packet'])
        self.assertEqual(self.blob[a:a+p['bytes']],self.old[a:a+p['bytes']])
        expected=bytearray(self.old[ROWS:TABLE_END])
        for row in self.rows:
            i=slot(int(row['item_id'],16));a=row['object_vrom']-BLOB;n=row['object_bytes']
            self.assertEqual(self.blob[a:a+n],self.old[a:a+n]);self.assertTrue(row['reused_asset'])
            self.assertFalse(self.blob[0x40+i//8]&(1<<(i&7)))
            profile=self.blob[ROWS+i*80:ROWS+(i+1)*80];item=self.blob[ITEMS+i*32:ITEMS+(i+1)*32]
            self.assertEqual(profile[:8],struct.pack('>HHI',row['runtime_index'],int(row['item_id'],16),0))
            self.assertEqual(profile[24:56],bytes(32))  # No engine rig or generic model duplicates.
            self.assertEqual(struct.unpack_from('>I',profile,72)[0],runtime.MATERIAL_VTABLE)
            self.assertEqual(item[8:24],row['name'].encode().ljust(16,b' '));self.assertEqual(item[7],0)
            expected[i*80:(i+1)*80]=profile;expected[ITEMS-ROWS+i*32:ITEMS-ROWS+(i+1)*32]=item
        self.assertEqual(self.blob[ROWS:TABLE_END],expected)
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        self.assertEqual(e['furniture_audio'],old_e['furniture_audio'])

    def test_verified_bindings_advance_to_acquisition_and_reject_missing_lifecycle(self):
        ids=identity_rows(ROOT/'build/item-identity-megasheet.xlsx')
        bindings=runtime.bind_profiles(self.source,self.image,self.report)
        self.assertEqual(len(bindings),26)
        for row in self.rows:
            item=int(row['item_id'],16)
            with self.assertRaisesRegex(ValueError,'^acquisition needs an adapter:'):
                metadata(self.source,item,prepare(self.source,item)[0],ids[item])
        for key,value in (('lifecycle_installed',False),('move_category','unknown')):
            bad=copy.deepcopy(self.report)
            next(r for r in bad['equipment_resources']['room_rigs']['material_rows'] if r['source_item_id']=='3314')[key]=value
            with self.assertRaisesRegex(ValueError,'Incomplete installed material/trigger lifecycle'):
                runtime.bind_profiles(self.source,self.image,bad)
        bad=copy.deepcopy(self.report)
        next(r for r in bad['equipment_resources']['room_rigs']['sound_rows'] if r['source_item_id']=='3314')['profile_installed']=False
        with self.assertRaisesRegex(ValueError,'Incomplete installed material/trigger lifecycle'):
            runtime.bind_profiles(self.source,self.image,bad)
        runtime.bind_profiles(self.source,self.image,self.report)

    def test_no_new_choices_and_exact_translation_only_and_patch_outputs(self):
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(self.out/'build-lock.json');catalog=composer.catalogue(self.image,self.report)
            self.assertEqual(len(catalog),136);self.assertFalse({r['id'] for r in self.rows}&set(catalog))
            self.assertEqual(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,list(catalog)))[0],self.image)
            self.assertEqual(sha256(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,[]))[0]),
                self.report['translation_baseline']['sha256'])
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (self.out/'asset-loader.ups').read_bytes()),self.image)


if __name__=='__main__':unittest.main()
