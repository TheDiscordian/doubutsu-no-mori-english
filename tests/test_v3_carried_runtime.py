"""Shared carried readers and installed resources, not ordinary gameplay proof."""
import copy
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from v3_asset_loader import BLOB,MODULE,MODULE_RAM
from v3_carried_runtime import RAM,TABLE,ICON,ART,PAPER,END,GUARD,native_identities
from v3_furniture_install import inputs
from v3_registry import CARRIED_ITEMS,CARRIED_ITEM_CATEGORIES
import v3_physical_resources as physical

OUT=ROOT/os.environ.get('V3_CARRIED_RUNTIME','build/v3-carried-runtime-work-01/readers-connected-12')

class CarriedRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUT/'build-lock.json')
        cls.base,cls.prior=inputs(OUT/'base-lock.json')

    def test_complete_packet_readers_preserved_native_identities_and_startup(self):
        image,r=self.image,self.report;base,prior=self.base,self.prior
        e=r['equipment_resources'];d=e['carried_items'];p=d['packet'];old=d['previous_packet']
        raw=image[p['physical']:p['physical']+p['bytes']]
        physical.verify(image,r['physical_resources'])
        self.assertEqual((sha256(raw),zlib.crc32(raw)),(p['sha256'],p['crc32']))
        self.assertEqual(raw[:old['bytes']],base[old['physical']:old['physical']+old['bytes']])
        self.assertEqual(p['ram']+len(raw),END);self.assertEqual(raw[-16:],GUARD)
        self.assertEqual(sha256(raw[RAM-p['ram']:]),d['sha256'])
        self.assertEqual(sha256(raw[RAM-p['ram']:RAM-p['ram']+d['code']['bytes']]),d['code']['sha256'])
        self.assertEqual(raw,(OUT/'carried-packet.bin').read_bytes())
        table=raw[TABLE-p['ram']:TABLE-p['ram']+d['table_bytes']]
        self.assertEqual(struct.unpack_from('>8I',table),(0x41464350,1,26,32,0,0,0,0))
        for i,row in enumerate(d['rows']):
            fields=struct.unpack_from('>3H4BHI16s',table,32+i*32)
            self.assertEqual(fields,(CARRIED_ITEMS[int(row['donor_item_id'],16)],int(row['donor_item_id'],16),
                CARRIED_ITEMS[int(row['parent_item_id'],16)],row['family'],row['state_index'],
                CARRIED_ITEM_CATEGORIES[row['source_category']],0,row['price'],row['icon'],row['name'].encode().ljust(16,b' ')))
        for a in d['artwork']:
            at=a['ram']-p['ram'];self.assertEqual(sha256(raw[at:at+a['object_bytes']]),a['installed_sha256'])
        paper=d['paper'];at=PAPER-p['ram']
        self.assertEqual(sha256(raw[at:at+paper['bytes']]),paper['installed_sha256'])
        prepared=bytearray((ROOT/d['prepared']/paper['file']).read_bytes())
        self.assertEqual(sha256(prepared),paper['sha256'])
        for fix in paper['pointer_relocations']:
            self.assertEqual(u32(prepared,fix['offset']),fix['before'])
            struct.pack_into('>I',prepared,fix['offset'],fix['after'])
        self.assertEqual(raw[at:at+paper['bytes']],bytes(prepared))
        files=by_vrom(image);blob=files[BLOB].extract(image);core=files[CODE_VROM].extract(image);module=files[MODULE].extract(image)
        self.assertEqual(native_identities(core),d['native_tables'])
        for h in d['hooks']:
            data,origin=(blob,0x80460000) if h['address']>=0x80460000 else ((module,MODULE_RAM) if h['address']>=MODULE_RAM else (core,CODE_RAM))
            self.assertEqual(data[h['address']-origin:h['address']-origin+8].hex(),h['after'])
        h=d['icon_hook'];menu=files[h['vrom']].extract(image)
        self.assertEqual(menu[h['address']-0x8085BAC0:h['address']-0x8085BAC0+8].hex(),h['after'])
        boot=e['surface_bootstrap']['code'];at=e['blob_offset']+boot['symbols']['packets']-e['ram']
        self.assertEqual(boot['packet_count'],20);self.assertLessEqual(boot['bytes'],688)
        for dest,src,n,crc in struct.iter_unpack('>4I',blob[at:at+20*16]):
            if src&0x80000000:data=image[src&0x7FFFFFFF:(src&0x7FFFFFFF)+n]
            else:
                owner=next(x for x in files.values() if x.vstart<=src<src+n<=x.vend)
                data=owner.extract(image)[src-owner.vstart:src-owner.vstart+n]
            self.assertEqual(u32(blob,e['blob_offset']+crc-e['ram']),zlib.crc32(data))
            self.assertTrue(0x80400000<=dest<dest+n<=0x807DA800)
        self.assertEqual((dest,src,n),(p['ram'],p['physical']|0x80000000,p['bytes']))
        self.assertEqual(r['save_runtime']['profile_hex'],prior['save_runtime']['profile_hex'])
        self.assertFalse(d['saved_format_changed']);self.assertFalse(d['native_execution_verified'])

    def test_retained_reader_chain_and_full_submenu_capacity(self):
        from v3_creature_items import checked
        from v3_furniture_pipeline import Source
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        self.assertIsNotNone(checked(self.image,self.report,source))
        from v3_furniture_capacity import checked as capacity
        broken=copy.deepcopy(self.report)
        broken['equipment_resources']['carried_items']['menu_allocations'][0]['pool_patch']['after']+=64
        with self.assertRaisesRegex(ValueError,'allocation chain'):capacity(self.image,broken)
        broken=copy.deepcopy(self.report)
        broken['equipment_resources']['holiday_items']['controls']['metadata'][0]['additional_pool_bytes']+=64
        with self.assertRaisesRegex(ValueError,'allocation chain'):capacity(self.image,broken)

    def test_complete_letter_tables_and_original_editor_preserved(self):
        d=self.report['equipment_resources']['carried_items'];paper=d['paper'];r=paper['letter_window']
        files=by_vrom(self.image);old=by_vrom(self.base)
        data=files[r['vrom']].extract(self.image);before=old[r['vrom']].extract(self.base)
        self.assertEqual(sha256(data),r['owner_sha256'])
        self.assertEqual(sha256(files[r['reloc']].extract(self.image)),r['relocation_sha256'])
        self.assertEqual(len(r['tables']),3)
        for table in r['tables']:
            at=table['address']-r['ram'];start=table['original']-r['ram']
            self.assertEqual((table['count'],table['original_count'],table['stride']),(65,64,4))
            self.assertEqual(data[at:at+256],before[start:start+256])
        binding=paper['bindings'][0]
        for table,kind in zip(r['tables'][:2],('background','lines')):
            self.assertEqual(u32(data,table['address']-r['ram']+256),
                (PAPER&0x1FFFFFFF)+paper['offsets'][binding[kind]])
        at=r['tables'][2]['address']-r['ram']+256
        self.assertEqual(list(data[at:at+4]),binding['text_rgba'])
        allowed={p['address']-r['ram']+i for p in r['patches'] for i in range(4)}
        self.assertTrue(all(a==b or i in allowed for i,(a,b) in enumerate(zip(data,before))))

    def test_shared_rebasing_retains_interior_vertices_and_rejects_overruns(self):
        from v3_category_runtime import rebase_art
        d=self.report['equipment_resources']['carried_items'];p=d['paper']
        raw=(ROOT/d['prepared']/p['file']).read_bytes()
        row=dict(resources=p['resources'],compiled_models=p['models'])
        result,fixes=rebase_art(raw,row,PAPER)
        self.assertEqual(sha256(result),p['installed_sha256'])
        starts={r['native_offset'] for r in p['resources']}
        interior=[f for f in fixes if f['resource_kind']=='vertices' and f['before']&0xFFFFFF not in starts]
        self.assertEqual(len(interior),2)
        broken=bytearray(raw);f=interior[0];offset=f['before']&0xFFFFFF
        owner=next(r for r in p['resources'] if r['kind']=='vertices' and r['native_offset']<=offset<r['native_offset']+r['bytes'])
        struct.pack_into('>I',broken,f['offset'],0x6000000+owner['native_offset']+owner['bytes']-16)
        with self.assertRaisesRegex(ValueError,'vertex slice'):rebase_art(bytes(broken),row,PAPER)

    def test_ground_categories_keep_diary_and_cedar_distinct(self):
        image,r=self.image,self.report;base,prior=self.base,self.prior
        e=r['equipment_resources'];c=e['item_categories'];g=e['ground_categories']
        files=by_vrom(image);old=by_vrom(base);blob=files[BLOB].extract(image);data=blob[e['blob_offset']:e['blob_offset']+e['bytes']]
        self.assertEqual(data[c['map_offset']+16+17],44)
        mask=c['ground_bitmap'];self.assertEqual(sha256(data[mask['offset']:mask['offset']+16]),mask['sha256'])
        self.assertTrue({44,48,49,50}<=set(mask['categories']));self.assertNotIn(51,mask['categories'])
        for row in c['objects']:
            for t in c['tables']:
                self.assertEqual(u32(data,t['offset']+row['native_category']*4),(row['ram']&0x1FFFFFFF)+row['model_offsets'][t['role']])
        h=g['carried_prepare'];at=h['address']-e['ram'];self.assertEqual(data[at:at+8].hex(),h['after'])
        for row in g['owners']:
            self.assertEqual(files[row['vrom']].extract(image),old[row['vrom']].extract(base))
            cap=row['capacity'];self.assertLessEqual(cap['parts_offset']+52*len(mask['categories']),cap['resident_bytes'])
            expected=bytearray(old[row['reloc']].extract(base));struct.pack_into('>I',expected,12,cap['bss_bytes'])
            self.assertEqual(files[row['reloc']].extract(image),bytes(expected))
        self.assertEqual(e['scenery'],prior['equipment_resources']['scenery'])

    def test_sanitized_changed_shared_readers_and_ground_bitmap(self):
        d=self.report['equipment_resources']['carried_items']
        with tempfile.TemporaryDirectory(prefix='v3-carried-readers-') as temp:
            for name,flags,args in (
                ('v3_carried_items_test',[],[str(OUT/'carried-packet.bin'),str(TABLE-d['packet']['ram'])]),
                ('v3_ground_categories_test',['-DAF_V3_GROUND_CATEGORY_FLAGS=1'],[])):
                target=Path(temp)/name
                result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                    '-fsanitize=address,undefined','-fno-omit-frame-pointer',*flags,'tests/'+name+'.c','-o',str(target)],
                    cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                result=subprocess.run([str(target),*args],capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr);print(result.stdout.strip())

if __name__=='__main__':unittest.main()
