"""Current scrolling renderer integration; no replay of unchanged cartridges."""
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
from v3_import_storage import ROWS,TABLE_END,ITEMS,slot
import v3_furniture_scroll as scroll
import v3_room_rig_runtime as room
import v3_optional_composition as composer

OUT=ROOT/'build/v3-scrolling-materials-runtime-02'
ART=ROOT/'build/v3-scrolling-materials-prepared-02'


class ScrollingRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUT/'build-lock.json')
        cls.base,cls.prior=inputs(OUT/'base-lock.json')
        cls.blob=by_vrom(cls.image)[BLOB].extract(cls.image);cls.old=by_vrom(cls.base)[BLOB].extract(cls.base)
        cls.runtime=cls.report['equipment_resources']['room_rigs'];cls.scroll=cls.runtime['scrolling']
        cls.art=json.loads((ART/'art.json').read_bytes())
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_complete_assets_records_packet_and_additive_destinations(self):
        self.assertEqual(len(self.scroll['rows']),5)
        self.assertEqual(sum(r['bytes'] for r in self.scroll['rows']),28112)
        for row in self.scroll['rows']:
            art=next(r for r in self.art['objects'] if r['item_id']==row['source_item_id'])
            self.assertEqual({k:v for k,v in row.items() if k not in ('blob_offset','vrom')},
                             json.loads(json.dumps(scroll.runtime_record(art))))
            self.assertEqual(self.blob[row['blob_offset']:row['blob_offset']+row['bytes']],(ART/art['object_file']).read_bytes())
            self.assertTrue(row['renderer_installed'])
            self.assertFalse(any(row[k] for k in ('lifecycle_installed','profile_installed','parent_selectable')))
        mapped={r['source_item_id']:(r['item_id'],r['runtime_index']) for r in self.scroll['rows']}
        self.assertEqual(mapped['1FE4'],('3C34',1805));self.assertEqual(mapped['1FE8'],('3C38',1806))
        sheet=identity_rows(ROOT/'build/item-identity-megasheet.xlsx',include_unmapped_legacy=True)
        for item in (0x1FE4,0x1FE8):
            self.assertTrue(all(sheet[item][1][k]=='-' for k in ('C','H','CG','CJ')))
            key=f'furniture:{(item-0x1000)//4:04x}'
            for path in ('translations/item_reference_matches.json','translations/item_resolved_matches.json'):
                self.assertFalse(any(r.get('reference_id','').lower()==key for r in json.loads((ROOT/path).read_bytes())))
        packet=self.scroll['packet'];raw=self.blob[packet['blob_offset']:packet['blob_offset']+packet['bytes']]
        code=(OUT/'room_scroll/code.bin').read_bytes();table=scroll.encode(self.scroll['rows'])
        self.assertEqual(raw,code.ljust(4096,b'\0')+table.ljust(4096,b'\0'))
        self.assertEqual(sha256(raw),packet['sha256']);self.assertLessEqual(len(code),4096)
        self.assertEqual(packet['ram'],room.PACKET_RAM+room.PACKET_BYTES)
        self.assertLessEqual(packet['ram']+packet['bytes'],self.report['furniture']['bank_pool']['start'])
        self.assertEqual(self.report['shared_runtime_refresh']['additional_resident_bytes'],8192)
        e=self.report['equipment_resources'];module=self.blob[e['blob_offset']:e['blob_offset']+e['bytes']]
        self.assertEqual(module[scroll.VTABLE-EQUIPMENT_RAM:scroll.VTABLE-EQUIPMENT_RAM+20],
            struct.pack('>5I',0,0,self.runtime['bootstrap']['symbols']['af_v3_room_boot_scroll_dw'],0,0))
        self.assertEqual(module[room.TABLE-EQUIPMENT_RAM:room.TABLE-EQUIPMENT_RAM+8],bytes(8))

    def test_actual_renderer_under_address_and_undefined_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-room-scroll-') as temporary:
            binary=Path(temporary)/'test';table=Path(temporary)/'table'
            table.write_bytes(scroll.encode(self.scroll['rows']))
            result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',str(ROOT/'tests/v3_room_scroll_test.c'),
                '-o',str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(binary),str(table)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('bounded rejection pass',result.stdout)

    def test_bad_records_and_incomplete_lifecycles_remain_rejected(self):
        rows=self.scroll['rows']
        for key,value in (('bytes',9217),('segment',7),('colour_mode',3),('model_offsets',[65528]),
                          ('dimensions',[[0,0]]),('rates',[[17,0]]),('state_offset',0x834)):
            bad=copy.deepcopy(rows);bad[0][key]=value
            with self.assertRaises(ValueError):scroll.encode(bad)
        with self.assertRaises(ValueError):scroll.encode(rows+rows)
        with self.assertRaises(ValueError):scroll.encode(list(reversed(rows)))
        for row in rows:
            p=prepare(self.source,int(row['source_item_id'],16))[0];p['callback_adapter']['runtime_installed']=True
            with self.assertRaisesRegex(ValueError,'Scrolling artwork'):metadata(self.source,int(row['source_item_id'],16),p,None)
            i=slot(int(row['item_id'],16))
            self.assertEqual(self.blob[ROWS+i*80:ROWS+(i+1)*80],bytes(80))
            self.assertEqual(self.blob[ITEMS+i*32:ITEMS+(i+1)*32],bytes(32))
        self.assertEqual(len(room.bind_profiles(self.source,self.image,self.report)),26)

    def test_existing_runtime_saves_and_optional_composition_are_retained(self):
        prior=self.prior['equipment_resources'];current=self.report['equipment_resources']
        for key in ('rows','sound_rows','material_rows','code','packet'):
            self.assertEqual(self.runtime[key],prior['room_rigs'][key])
        packet=self.runtime['packet'];at=packet['blob_offset'];n=packet['bytes']
        self.assertEqual(self.blob[at:at+n],self.old[at:at+n])
        self.assertEqual(self.blob[ROWS:TABLE_END],self.old[ROWS:TABLE_END])
        for key in ('furniture_audio','scenery','bytes'):self.assertEqual(current[key],prior[key])
        for key in ('staged_furniture','save_runtime'):self.assertEqual(self.report[key],self.prior[key])
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(OUT/'build-lock.json');catalog=composer.catalogue(self.image,self.report)
            self.assertEqual(len(catalog),136)
            self.assertFalse({r['source']['id'] for r in self.scroll['rows']}&set(catalog))
            self.assertEqual(sha256(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,[]))[0]),
                             self.report['translation_baseline']['sha256'])
            self.assertEqual(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,list(catalog)))[0],self.image)
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                                  (OUT/'asset-loader.ups').read_bytes()),self.image)
