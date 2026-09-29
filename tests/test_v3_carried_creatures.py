"""Shared carried-creature preparation and complete source lifecycle checks."""
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from unittest.mock import patch
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,u32
from v3_furniture_pipeline import Source,prepare_models
from v3_creature_field import discover
from v3_creature_insects import PROGRAMS,CARRIED_PROGRAMS,program_source

PREPARED=ROOT/os.environ.get('V3_CARRIED_CREATURES','build/v3-carried-field-prepared-04')
BUILD=ROOT/os.environ.get('V3_CARRIED_FIELD_BUILD','build/v3-carried-field-work-01/installed-04')


class CarriedCreatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.rows=json.loads((ROOT/'build/v3-carried-batch-prepared-05/items.json').read_bytes())['rows']

    def test_complete_field_and_program_preparation(self):
        inventory=discover(self.source,carried_rows=self.rows)
        self.assertEqual(inventory['counts'],dict(creatures=1,frames=4,unique_models=2,object_bytes=1440))
        row,=inventory['rows']
        self.assertEqual((row['item_id'],row['source_index'],row['program_type']),('2D28',40,8))
        self.assertIsNone(row['display_item_id'],'A quest spirit is not museum cage furniture')
        self.assertEqual(row['frame_labels'],['frame0','frame0','frame1','frame1'])
        report=json.loads((PREPARED/'compiled.json').read_bytes())
        self.assertEqual(report['field']['inventory'],json.loads(json.dumps(inventory)))
        obj,=report['field']['objects'];data=(PREPARED/'field'/obj['object_file']).read_bytes()
        self.assertEqual(sha256(data),obj['object_sha256'])
        part=prepare_models(self.source,row['descriptor'])
        self.assertEqual(data[:len(part[1])],part[1])
        self.assertEqual(sum(m['triangles'] for m in obj['models']),4)
        self.assertFalse(report['installed']);self.assertFalse(report['selectable'])
        source,receipt=program_source(self.source,CARRIED_PROGRAMS[0],carried=True)
        self.assertEqual(len(receipt['functions']),15)
        self.assertEqual(source,(PREPARED/'hitodama.c').read_bytes())
        for path,digest in report['compiled']['runtime_sources'].items():
            self.assertEqual(sha256((ROOT/path).read_bytes()),digest)
        self.assertEqual(sha256((PREPARED/report['compiled']['file']).read_bytes()),report['compiled']['sha256'])

    def test_complete_source_lifecycle(self):
        with tempfile.TemporaryDirectory(prefix='af-carried-creatures-') as temporary:
            directory=Path(temporary);inputs=[]
            for program in (*PROGRAMS,*CARRIED_PROGRAMS):
                data,_=program_source(self.source,program,carried=program in CARRIED_PROGRAMS)
                file=directory/(program[0]+'.c');file.write_bytes(data);inputs.append(str(file))
            exe=directory/'programs'
            result=subprocess.run(['cc','-std=c11','-O1','-g','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-sanitize-recover=all','-DAF_INSECT_CARRIED',
                '-Wall','-Wextra','-Werror','-Wno-unused-parameter','-Wno-unused-variable',
                '-I'+str(ROOT/'overlays/v3'),*inputs,
                *(str(ROOT/'overlays/v3'/f'{n}.c') for n in
                  ('creature_carried','creature_insects','creature_insect_state')),
                str(ROOT/'tests/v3_creature_insects_test.c'),'-lm','-o',str(exe)],
                capture_output=True,text=True,timeout=60)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('Carried spirit:',result.stdout)
            self.assertIn('Eight species:',result.stdout)

    def test_native_drawing_adapter(self):
        with tempfile.TemporaryDirectory(prefix='af-carried-draw-') as temporary:
            exe=Path(temporary)/'draw'
            result=subprocess.run(['cc','-std=c11','-O1','-g','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-sanitize-recover=all','-Wall','-Wextra','-Werror',
                '-I'+str(ROOT/'overlays/v3'),str(ROOT/'overlays/v3/creature_carried_draw.c'),
                str(ROOT/'tests/v3_carried_creature_draw_test.c'),'-o',str(exe)],
                capture_output=True,text=True,timeout=60)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('Carried field:',result.stdout)

    def test_capture_release_inventory_and_message_selection(self):
        with tempfile.TemporaryDirectory(prefix='af-carried-interactions-') as temporary:
            exe=Path(temporary)/'interactions'
            result=subprocess.run(['cc','-std=c11','-O1','-g','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-sanitize-recover=all','-Wall','-Wextra','-Werror',
                '-DAF_CARRIED_SPIRIT_MESSAGE_FIRST=13082','-I'+str(ROOT/'overlays/v3'),
                str(ROOT/'overlays/v3/carried_interactions.c'),
                str(ROOT/'tests/v3_carried_interactions_test.c'),'-o',str(exe)],
                capture_output=True,text=True,timeout=60)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('Carried interactions:',result.stdout)


class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from v3_furniture_install import inputs
        cls.rom,cls.report=inputs(BUILD/'build-lock.json')
        cls.base,cls.prior=inputs(BUILD/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.e=cls.report['equipment_resources'];cls.d=cls.e['carried_items']
        cls.r=cls.d['field_creatures']

    def test_shared_packet_complete_resources_startup_and_save_retention(self):
        from v3_asset_loader import BLOB
        from v3_physical_resources import verify
        from aflib import apply_ups
        verify(self.rom,self.report['physical_resources'])
        r=self.r;p=r['packet'];before=r['previous_packet']
        raw=self.rom[p['physical']:p['physical']+p['bytes']]
        old=self.base[before['physical']:before['physical']+before['bytes']]
        self.assertEqual((sha256(raw),zlib.crc32(raw)),(p['sha256'],p['crc32']))
        start=r['ram']-p['ram'];end=start+r['bytes']
        self.assertEqual(raw[:start],old[:start]);self.assertEqual(raw[end:],old[end:])
        self.assertFalse(any(old[start:end]))
        self.assertEqual(sha256(raw[start:end]),r['sha256'])
        self.assertEqual(raw[end-16:end],b'AFCARRIEDFIELD!!')
        code=r['code'];self.assertEqual(raw[start:start+code['bytes']],
            (PREPARED/code['file']).read_bytes())
        self.assertEqual(r['additional_resident_bytes'],0)
        self.assertEqual(r['packet'],self.e['scenery']['tree_effects']['packet'])
        self.assertEqual(self.e['scenery']['tree_effects']['art_packet'],
            self.prior['equipment_resources']['scenery']['tree_effects']['art_packet'])
        for row in (*r['tables'],r['art']):
            at=row['ram']-p['ram']
            self.assertEqual(sha256(raw[at:at+row['bytes']]),row['sha256'])
        for name in ('packet','storage','ready_mask','selected_mask'):
            self.assertEqual(self.d[name],self.prior['equipment_resources']['carried_items'][name])
        blob=self.files[BLOB].extract(self.rom)
        boot=self.e['surface_bootstrap']['code']
        start=self.e['blob_offset']+boot['symbols']['packets']-self.e['ram']
        self.assertEqual(boot['packet_count'],21);self.assertLessEqual(boot['bytes'],688)
        for i in range(boot['packet_count']):
            ram,source,n,crc=struct.unpack_from('>4I',blob,start+i*16)
            if source&0x80000000:data=self.rom[source&0x7FFFFFFF:(source&0x7FFFFFFF)+n]
            else:
                owner=next(f for f in self.files.values() if f.vstart<=source<source+n<=f.vend)
                data=owner.extract(self.rom)[source-owner.vstart:source-owner.vstart+n]
            self.assertEqual(zlib.crc32(data),u32(blob,self.e['blob_offset']+crc-self.e['ram']))
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (BUILD/'asset-loader.ups').read_bytes()),self.rom)

    def test_exact_native_callers_and_retained_insect_programs(self):
        from npc_mail_show import relocate_verified_data
        from types import SimpleNamespace
        r=self.r;owner=r['owner'];data=self.files[owner['vrom']].extract(self.rom)
        before=self.before[owner['vrom']].extract(self.base);restored=bytearray(data)
        for patch in owner['patches']:
            at=patch['address']-owner['ram']
            self.assertEqual(u32(before,at),patch['before']);self.assertEqual(u32(data,at),patch['after'])
            struct.pack_into('>I',restored,at,patch['before'])
        self.assertEqual(restored,before)
        rel=self.files[owner['reloc']].extract(self.rom)
        oldrel=self.before[owner['reloc']].extract(self.base)
        oldwords=list(struct.unpack_from('>'+str(u32(oldrel,16))+'I',oldrel,20))
        for word in owner['removed_relocations']:oldwords.remove(word)
        self.assertEqual(list(struct.unpack_from('>'+str(u32(rel,16))+'I',rel,20)),oldwords)
        self.assertEqual(len(owner['removed_relocations']),3)
        spec=SimpleNamespace(ram=owner['ram'],resident_bytes=sum(struct.unpack_from('>4I',rel)),
            sections=struct.unpack_from('>5I',rel))
        for address in (0x80200010,0x80300010):
            loaded=relocate_verified_data(spec,data,rel,address)
            for patch in owner['patches']:
                self.assertEqual(u32(loaded,patch['address']-owner['ram']),patch['after'])
        p=self.e['creature_insects']['packet'];oldp=self.prior['equipment_resources']['creature_insects']['packet']
        raw=self.rom[p['physical']:p['physical']+p['bytes']];restored=bytearray(raw)
        before=self.base[oldp['physical']:oldp['physical']+oldp['bytes']]
        self.assertEqual(sha256(raw),p['sha256']);self.assertEqual(len(r['redirects']),21)
        for redirect in r['redirects']:
            at=redirect['previous']-p['ram']
            self.assertEqual(raw[at:at+8].hex(),redirect['after'])
            self.assertEqual(before[at:at+8].hex(),redirect['before'])
            restored[at:at+8]=bytes.fromhex(redirect['before'])
        self.assertEqual(restored,before)


class InteractionCartridgeTests(unittest.TestCase):
    def test_changed_consumers_complete_dialogue_and_unchanged_native_state(self):
        from aflib import apply_ups
        from v3_asset_loader import BLOB
        from v3_furniture_install import inputs
        from v3_carried_runtime import capture_text
        from v3_event_text import MESSAGE,TABLE
        from v3_physical_resources import verify
        from textbanks import Bank
        out=ROOT/os.environ.get('V3_CARRIED_INTERACTIONS','build/v3-carried-field-work-01/inventory-01')
        rom,report=inputs(out/'build-lock.json');base,prior=inputs(out/'base-lock.json')
        files,before=by_vrom(rom),by_vrom(base);e=report['equipment_resources'];d=e['carried_items']
        r=d['interactions'];p=d['packet'];old=prior['equipment_resources']['carried_items']
        raw=rom[p['physical']:p['physical']+p['bytes']]
        self.assertEqual((sha256(raw),zlib.crc32(raw)),(p['sha256'],p['crc32']))
        start=r['ram']-p['ram'];end=start+r['bytes'];restored=bytearray(raw)
        self.assertEqual(raw[start:end],(out/'carried-interactions/code.bin').read_bytes())
        original=base[old['packet']['physical']:old['packet']['physical']+old['packet']['bytes']]
        restored[start:end]=original[start:end]
        self.assertEqual(restored,original)
        for key in ('storage','ready_mask','selected_mask'):
            self.assertEqual(d[key],old[key])
        for v,row in ((0x3950000,r['tag']),(r['player']['vrom'],r['player'])):
            data=files[v].extract(rom);restored=bytearray(data);previous=before[v].extract(base)
            ram=0x8086F310 if v==0x3950000 else row['ram']
            for change in row['patches']:
                at=change['address']-ram
                self.assertEqual(u32(data,at),change['after']);self.assertEqual(u32(previous,at),change['before'])
                struct.pack_into('>I',restored,at,change['before'])
            self.assertEqual(restored,previous)
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        extra,text=capture_text(base,source)
        prior_bank=Bank('prior',0,0,before[MESSAGE].extract(base),before[TABLE].extract(base)).entries()
        bank=Bank('current',0,0,files[MESSAGE].extract(rom),files[TABLE].extract(rom)).entries()
        self.assertEqual(bank,prior_bank if r.get('refresh') else prior_bank+extra)
        self.assertEqual(bank[text['first_id']:text['first_id']+len(extra)],extra)
        self.assertEqual(r['text']['rows'],text['rows'])
        self.assertEqual(len(extra),6)
        from aflib import CODE_RAM,CODE_VROM
        from v3_carried_runtime import CARRIED_FILTERS,CARRIED_FILTER_SOURCES
        core=files[CODE_VROM].extract(rom);old_core=before[CODE_VROM].extract(base)
        self.assertEqual(len(r['inventory_filters']),len(CARRIED_FILTERS))
        self.assertTrue({name for _,name,_ in CARRIED_FILTER_SOURCES}<={row['symbol'] for row in r['donors']})
        for row in r['inventory_filters']:
            self.assertEqual(u32(core,row['address']-CODE_RAM),r['code']['symbols'][row['symbol']])
            self.assertEqual(u32(old_core,row['address']-CODE_RAM),row['before'])
        changed={index for index,_,_ in CARRIED_FILTERS}
        for index in range(17):
            if index not in changed:
                self.assertEqual(u32(core,0x8010DD38-CODE_RAM+index*4),
                    u32(old_core,0x8010DD38-CODE_RAM+index*4))
        mail=r['retained_mail'];tag=files[0x3950000].extract(rom);at=mail['address']-0x8086F310
        self.assertEqual(sha256(tag[at:at+mail['bytes']]),mail['sha256'])
        for row in r['text']['resources']:
            self.assertEqual(sha256(files[row['vrom']].extract(rom)),row['sha256'])
        verify(rom,report['physical_resources'])
        blob=files[BLOB].extract(rom);boot=e['surface_bootstrap']['code']
        start=e['blob_offset']+boot['symbols']['packets']-e['ram']
        self.assertEqual(boot['packet_count'],21);self.assertLessEqual(boot['bytes'],688)
        for i in range(boot['packet_count']):
            _,src,n,crc=struct.unpack_from('>4I',blob,start+i*16)
            if src&0x80000000:data=rom[src&0x7FFFFFFF:(src&0x7FFFFFFF)+n]
            else:
                owner=next(f for f in files.values() if f.vstart<=src<src+n<=f.vend)
                data=owner.extract(rom)[src-owner.vstart:src-owner.vstart+n]
            self.assertEqual(zlib.crc32(data),u32(blob,e['blob_offset']+crc-e['ram']))
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (out/'asset-loader.ups').read_bytes()),rom)

    def test_text_index_slides_within_owned_banks_before_allocating(self):
        from v3_event_text import split_placements
        files={1:SimpleNamespace(pstart=0x300000,size=0x1000),
            2:SimpleNamespace(pstart=0x301000,size=0x100),
            3:SimpleNamespace(pstart=0x301100,size=0x100)}
        calls=[]
        def allocate(image,records,data,name,**options):
            calls.append((len(data),options));return dict(physical=0x400000,bytes=len(data))
        image=bytes(0x500000)
        with patch('v3_physical_resources.allocate',side_effect=allocate):
            rows=split_placements(image,files,{1:bytes(0x1020),2:bytes(0x110),3:bytes(0x100)},[],0x200000)
        self.assertEqual([r['physical'] for r in rows],[0x300000,0x301020,0x400000])
        self.assertEqual(calls,[(0x100,dict(best_fit=True,minimum_physical=0x200000))])


class CarriedEventPreparationTests(unittest.TestCase):
    def test_complete_quest_source_and_translucent_art(self):
        from v3_npc_stream_art import prepare
        from v3_npc_stream_runtime import native_records
        from v3_villager_mesh import faces
        from tests.test_v3_islander_bodies import gx_pixel
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        directory=ROOT/'build/v3-carried-event-prepared-03'
        report=json.loads((directory/'prepared.json').read_bytes())
        owner,=report['family'];functions=owner['functions']+report['event_manager_functions']
        self.assertEqual((len(owner['functions']),len(report['event_manager_functions'])),(48,4))
        for row in functions:
            self.assertEqual(json.loads(json.dumps(source.function(row['offset'])[1])),row)
        for path,row in report['references'].items():
            raw=(ROOT/'local/ac-decomp'/path).read_bytes()
            self.assertEqual((len(raw),sha256(raw)),(row['bytes'],row['sha256']))
        for name,digest in report['generated_sha256'].items():
            self.assertEqual(sha256((directory/name).read_bytes()),digest)
        obj=(directory/'carried-event.o').read_bytes()
        self.assertEqual(obj[:6],b'\x7fELF\x01\x02')
        self.assertEqual(struct.unpack_from('>H',obj,18)[0],8)
        self.assertEqual(sha256(obj),report['object']['sha256'])
        self.assertFalse(report['object']['linked']);self.assertFalse(report['installed'])
        self.assertTrue(report['unbound_services'])
        directory=ROOT/'build/v3-carried-wisp-art-01';r=json.loads((directory/'art.json').read_bytes())
        p=prepare(source,349);model=(directory/'model.bin').read_bytes();texture=(directory/'texture.bin').read_bytes()
        self.assertEqual((len(model),len(texture),r['triangles']),(6688,4128,186))
        self.assertEqual((sha256(model),sha256(texture)),(r['model_sha256'],r['texture_sha256']))
        self.assertEqual(texture,p['texture']);self.assertEqual(len(r['eye_offsets']),8)
        self.assertEqual(len(r['mouth_offsets']),6);self.assertFalse(r['runtime_installed'])
        self.assertEqual(native_records(source,r,0xDFFE,510,511)[2],249)
        for row in r['resources']:
            raw=source.data[row['source_offset']:row['source_offset']+row['bytes']]
            for y in range(row['height']):
                for x in range(row['width']):
                    native=texture[row['offset']+(y*row['width']+x)//2]>>(0 if x&1 else 4)&15
                    self.assertEqual(native,gx_pixel(raw,row['width'],x,y))
        triangles=0
        for row in r['models']:
            raw=model[row['offset']:row['offset']+row['bytes']]
            self.assertEqual(raw,(directory/'gbi'/(row['symbol']+'.bin')).read_bytes())
            self.assertIn(bytes.fromhex('fc123a0efffffe38'),raw)
            self.assertIn(bytes.fromhex('e200001cc81049d8'),raw)
            primitive=source.raw(row['symbol'])[16:24]
            self.assertEqual(primitive[0],0xFA)
            self.assertIn(primitive,raw)
            triangles+=len(faces(raw,donor=False,streamed=True,vertex_bytes=len(p['vertices'])))
        self.assertEqual(triangles,186)


if __name__=='__main__':unittest.main()
