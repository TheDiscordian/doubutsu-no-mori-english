"""Complete tree-effect conversion and checked native runtime preparation."""
import copy
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zlib
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256,u32,by_vrom,apply_ups
from v3_furniture_pipeline import Source
import v3_tree_effects as effects
import v3_tree_effects_runtime as runtime

ART=ROOT/'build/v3-tree-effects-prepared-01'
BUILD=ROOT/os.environ.get('V3_TREE_EFFECTS','build/v3-tree-effects-work-01/installed-10')
PREPARED=BUILD/'tree-effects'


class PageTests(unittest.TestCase):
    def test_bounded_complete_page_loading(self):
        from tests.test_v3_equipment_runtime import HostTests
        HostTests.sanitized(self,'v3_paged_resource_test.c')

    def test_allocator_keeps_overlapping_and_pending_extents_occupied(self):
        import v3_physical_resources as physical
        rom=bytes(0x4000000)
        files={0:SimpleNamespace(pstart=0x100000,pend=0,size=0x3E00000),
               1:SimpleNamespace(pstart=0x200000,pend=0,size=0x1000)}
        with patch.object(physical,'by_vrom',return_value=files):
            r=physical.allocate(rom,[],bytes(4096),'page',best_fit=True,
                excluded_spans=((0x3F00000,0x3FFF000),))
            self.assertEqual(r['physical'],0x3FFF000)
            with self.assertRaisesRegex(ValueError,'space'):
                physical.allocate(rom,[],bytes(8192),'page',best_fit=True,
                    excluded_spans=((0x3F00000,0x3FFF000),))
            with self.assertRaisesRegex(ValueError,'space'):
                physical.allocate(rom,[],bytes(4096),'page',minimum_physical=0x3FFF010)


@unittest.skipUnless((ART/'art.json').is_file(),'Complete local tree-effect assets required')
class TreeEffects(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.art,cls.data,cls.sections=effects.checked(cls.source,ART)

    def test_all_tables_motions_models_and_native_materials(self):
        art=self.art
        self.assertEqual(art['counts'],dict(tables=14,table_entries=210,skeletons=63,
            animations=105,models=122,sprites=11,resources=152,max_joints=5))
        _,prepared=effects.prepare(self.source)
        row=art['object'];self.assertEqual(self.data[:len(prepared[1])],prepared[1])
        models={r['layer']:r for r in row['compiled_models']}
        for layer,model in prepared[4].items():
            native=models[layer];commands=list(struct.iter_unpack('>II',self.sections[layer]))
            self.assertEqual(native['bytes'],len(commands)*8)
            self.assertEqual(native['output_sha256'],sha256(self.sections[layer]))
            source_states=[r['words'] for r in model['rows'] if r['opcode'] in (0xFC,0xE2)]
            native_states=[(a,b) for a,b in commands if a>>24 in (0xFC,0xE2)]
            self.assertEqual(native_states,source_states)
            faces=[]
            for a,b in commands:
                self.assertNotIn(a>>24,(0x0A,0xD2))
                if a>>24 in (5,6):
                    faces.extend(tuple((w>>s&255)//2 for s in (16,8,0))
                        for w in ((a,) if a>>24==5 else (a,b)))
            self.assertEqual(faces,[t for r in model['rows'] for t in r.get('triangles',[])])
        self.assertEqual([r['symbol'] for r in art['retained_native']],['ef_s_yabu01_00_modelT'])
        self.assertFalse(art['runtime_installed']);self.assertFalse(art['selectable'])

    def test_prepared_reuse_needs_no_graphics_compiler(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'build') as temporary:
            out=Path(temporary)/'reuse'
            with patch.object(effects,'compile_commands_batch',side_effect=AssertionError('Unexpected reconversion')):
                effects.convert(self.source,out,reuse_assets=(ART,))
            art,data,_=effects.checked(self.source,out)
            self.assertEqual(art,self.art);self.assertEqual(data,self.data)

    def test_cpu_graphics_and_complete_palette_relocation(self):
        data,symbols,report=runtime.runtime_art(self.source,self.art,self.data)
        restored=bytearray(data[:len(self.data)])
        for p in report['relocations']:
            wanted=runtime.ART_RAM+p['target']
            if not p['cpu']:wanted&=0x1FFFFFFF
            self.assertEqual(u32(data,p['offset']),wanted)
            struct.pack_into('>I',restored,p['offset'],0x06000000+p['target'])
        self.assertEqual(restored,self.data)
        self.assertEqual(report['all_palette_frames'],42)
        self.assertEqual(symbols['af_tree_palette_data'],runtime.ART_RAM+len(self.data))
        self.assertEqual(data[symbols['af_tree_palette_terms']-runtime.ART_RAM:][:18],
            bytes(self.art['palettes']['gold']['term_indices']))
        for p in self.art['object']['rigs']:
            self.assertEqual(symbols[p['header']['symbol']],runtime.ART_RAM+p['header']['native_offset'])
        self.assertLessEqual(runtime.ART_RAM+len(data),runtime.END)
        changed=bytearray(self.data);changed[report['relocations'][0]['offset']]^=1
        with self.assertRaisesRegex(ValueError,'resource binding'):
            runtime.runtime_art(self.source,self.art,changed)

    def test_complete_source_and_safe_native_workspace(self):
        modules=runtime.generate(self.art)
        self.assertIn('#define EffectBg_JOINT_NUM 6',modules['actor.c'])
        self.assertIn('efbg->status=0;efbg->add_angle=0;efbg->leaf_angle=0;',modules['actor.c'])
        self.assertEqual(modules['actor.c'].count('EffectBG_object_move(efbg, game);'),2)
        self.assertIn('if(e->timer>1){--e->timer;eBushHappa_mv(e,g);}',modules['leaf.c'])
        self.assertIn('if(e->timer>1){--e->timer;eYoung_Tree_mv(e,g);}',modules['young.c'])
        self.assertNotIn('ef_s_yabu01_00_modelT',modules['leaf.c'])
        self.assertIn('if((b&0x0FFF)<4 || (b&0x0FFF)>7)return;',modules['leaf.c'])
        self.assertIn('af_tree_camera(game,&effect->offset);',modules['young.c'])
        bad=copy.deepcopy(self.art);bad['functions'].pop()
        with self.assertRaisesRegex(ValueError,'callbacks'):runtime.generate(bad)

    @unittest.skipUnless((PREPARED/'prepared.json').is_file(),'Compiled tree-effect runtime required')
    def test_mips_linkage_complete_tables_and_workspace(self):
        p=json.loads((PREPARED/'prepared.json').read_bytes());code=(PREPARED/'compiled/code.bin').read_bytes()
        self.assertEqual(sha256(code),p['code']['sha256'])
        self.assertLessEqual(len(code),runtime.ART_RAM-runtime.RAM)
        symbols=p['code']['symbols'];modules=runtime.generate(self.art)
        self.assertEqual(p['generated_sha256'],{name:sha256(text.encode()) for name,text in modules.items()})
        self.assertEqual(u32(code,symbols['af_tree_joint_vectors']-runtime.RAM),6)
        self.assertGreaterEqual(u32(code,symbols['af_tree_actor_bytes']-runtime.RAM),0xCF0+3*24)
        for table in self.art['tables']:
            at=symbols[table['symbol']]-runtime.RAM
            values=struct.unpack_from('>15I',code,at)
            expected=[]
            for target in table['targets']:
                name,_,_=self.source.containing(target,exact=True);expected.append(p['bindings'][name])
            self.assertEqual(values,tuple(expected))
        for prefix in ('af_tree_actor','af_tree_leaf','af_tree_young'):
            for role in ('ct','dt','mv','dw') if prefix.endswith('actor') else ('init','ct','mv','dw'):
                self.assertTrue(runtime.RAM<=symbols[prefix+'_'+role]<runtime.RAM+len(code))
        self.assertFalse(p['installed'])


@unittest.skipUnless((BUILD/'build-lock.json').is_file(),'Current tree-effect cartridge required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from v3_furniture_install import inputs
        from v3_asset_loader import BLOB
        cls.rom,cls.report=inputs(BUILD/'build-lock.json')
        cls.base,cls.prior=inputs(BUILD/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.e=cls.report['equipment_resources'];cls.r=cls.e['scenery']['tree_effects']
        cls.blob=cls.files[BLOB].extract(cls.rom)

    def test_complete_paged_art_code_startup_and_unchanged_saves(self):
        from v3_physical_resources import verify
        from v3_console_disk_install import reservations
        verify(self.rom,self.report['physical_resources'])
        p=self.r['packet'];raw=self.rom[p['physical']:p['physical']+p['bytes']]
        self.assertEqual((sha256(raw),zlib.crc32(raw)),(p['sha256'],p['crc32']))
        self.assertEqual(raw[:self.r['code']['bytes']],(PREPARED/'compiled/code.bin').read_bytes())
        self.assertEqual(raw[-16:],b'AFTE'*4)
        header=struct.unpack_from('>41I',raw,runtime.PAGE_TABLE-runtime.RAM)
        self.assertEqual(header[:4],(0x41465047,runtime.END-runtime.ART_RAM,4096,36))
        self.assertEqual(list(header[4:40]),self.r['art_packet']['page_addresses'])
        data=b''.join(self.rom[a:a+4096] for a in header[4:40])
        self.assertEqual((sha256(data),zlib.crc32(data)),
            (self.r['art_packet']['sha256'],header[-1]))
        expected=(PREPARED/'tree-art.bin').read_bytes()
        self.assertEqual(data,expected+bytes(len(data)-len(expected)-16)+b'AFTE'*4)
        self.assertFalse(any(a<runtime.END and runtime.RAM<b for a,b in reservations(self.prior)))
        boot=self.e['surface_bootstrap']['code'];start=self.e['blob_offset']+boot['symbols']['packets']-self.e['ram']
        self.assertEqual(boot['packet_count'],21);self.assertLessEqual(boot['bytes'],688)
        for i in range(boot['packet_count']):
            ram,source,n,crc=struct.unpack_from('>4I',self.blob,start+i*16)
            if source&0x80000000:data=self.rom[source&0x7FFFFFFF:(source&0x7FFFFFFF)+n]
            else:
                owner=next(e for e in self.files.values() if e.vstart<=source<source+n<=e.vend)
                data=owner.extract(self.rom)[source-owner.vstart:source-owner.vstart+n]
            self.assertEqual(zlib.crc32(data),u32(self.blob,self.e['blob_offset']+crc-self.e['ram']))
            if i==20:self.assertEqual((ram,source,n),(runtime.RAM,p['physical']|0x80000000,p['bytes']))
        for name,digest in self.r['sources'].items():self.assertEqual(sha256((ROOT/name).read_bytes()),digest,name)
        self.assertEqual(self.e['carried_items']['packet'],self.prior['equipment_resources']['carried_items']['packet'])
        self.assertFalse(self.r['saved_format_changed']);self.assertFalse(self.r['ordinary_gameplay_verified'])
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (BUILD/'asset-loader.ups').read_bytes()),self.rom)

    def test_actor_workspace_and_all_player_callers_relocate_safely(self):
        from npc_mail_show import relocate_verified_data
        from v3_import_storage import jump
        for role in ('actor','player'):
            row=self.r[role];data=self.files[row['vrom']].extract(self.rom);rel=self.files[row['reloc']].extract(self.rom)
            before=self.before[row['vrom']].extract(self.base);restored=bytearray(data)
            patches=row.get('callbacks',row.get('patches'))
            for p in patches:
                self.assertEqual(u32(before,p['offset']),p['before']);self.assertEqual(u32(data,p['offset']),p['after'])
                struct.pack_into('>I',restored,p['offset'],p['before'])
            if role=='actor':
                self.assertEqual(u32(data,0x1F28+12),row['actor_bytes'])
                self.assertGreaterEqual(row['additional_actor_bytes'],72)
                struct.pack_into('>I',restored,0x1F28+12,0xCF0)
            else:
                self.assertEqual(len(patches),4)
                for p in patches:self.assertEqual(p['after'],jump(self.r['code']['symbols']['af_tree_player_effect'],link=True))
            self.assertEqual(restored,before)
            self.assertEqual(sha256(data),row['sha256']);self.assertEqual(sha256(rel),row['reloc_sha256'])
            spec=SimpleNamespace(ram=row['ram'],resident_bytes=sum(struct.unpack_from('>4I',rel)),
                sections=struct.unpack_from('>5I',rel))
            for address in (0x80200010,0x80300010):
                loaded=relocate_verified_data(spec,data,rel,address)
                for p in patches:self.assertEqual(u32(loaded,p['offset']),p['after'])

    def test_existing_effect_profiles_and_native_controller_are_retained(self):
        from v3_room_effects import restore_controller
        current=self.e['room_rigs']['effects'];old=self.prior['equipment_resources']['room_rigs']['effects']
        c=current['controller'];o=old['controller']
        self.assertEqual(restore_controller(self.files[c['vrom']].extract(self.rom),self.files[c['reloc']].extract(self.rom),c),
            restore_controller(self.before[o['vrom']].extract(self.base),self.before[o['reloc']].extract(self.base),o))
        self.assertEqual((c['count'],c['active_pool_capacity'],c['code_pool_slots']),(122,80,12))
        for row,previous in zip(current['profiles'][:9],old['profiles'],strict=True):
            self.assertEqual(row['sha256'],previous['sha256'])
            self.assertEqual(row['callbacks'],previous['callbacks'])
        for row in current['profiles']:
            p=self.blob[row['blob_offset']:row['blob_offset']+64]
            self.assertEqual(sha256(p),row['sha256']);self.assertEqual(zlib.crc32(p[:24]),u32(p,24))
            if row['id']>=120:
                self.assertEqual(p[16:24],bytes.fromhex('fffe00ff44480000'))
                self.assertEqual(struct.unpack_from('>4I',p),tuple(row['callbacks']))
                self.assertTrue(all(runtime.RAM<=v<runtime.RAM+self.r['code']['bytes'] for v in row['callbacks']))
        self.assertEqual(current['bank'],old['bank'])

    def test_shared_room_refresh_retains_independent_tree_callbacks(self):
        from v3_room_effects import rebind_profiles
        room=self.e['room_rigs'];effects=copy.deepcopy(room['effects']);blob=bytearray(self.blob)
        rebind_profiles(effects,blob,room['code']['symbols'],code_bounds=(room['packet']['ram'],room['table_ram']))
        self.assertEqual(blob,self.blob);self.assertEqual(effects,room['effects'])
        bad=copy.deepcopy(effects);bad['profiles'][-1]['callbacks'][0]=runtime.RAM-4
        with self.assertRaisesRegex(ValueError,'profile'):
            rebind_profiles(bad,blob,room['code']['symbols'],code_bounds=(room['packet']['ram'],room['table_ram']))


if __name__=='__main__':unittest.main()
