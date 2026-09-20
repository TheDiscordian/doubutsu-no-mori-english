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


if __name__=='__main__':unittest.main()
