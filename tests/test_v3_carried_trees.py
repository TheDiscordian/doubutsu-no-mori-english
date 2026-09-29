"""Complete palm/cedar preparation and shared seasonal loading, not gameplay."""
import copy
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from v3_furniture_pipeline import Source,prepare_material_pair
import v3_scenery as scenery
import v3_scenery_runtime as runtime
import tests.test_v3_equipment_runtime as host_helper
import tests.test_v3_furniture_pipeline as art_helper

ART=ROOT/'build/v3-carried-trees-prepared-02'
BANKS=ROOT/'build/v3-carried-runtime-work-01/tree-banks-01'
BUILD=ROOT/os.environ.get('V3_CARRIED_TREES','build/v3-carried-runtime-work-01/trees-connected-05')


class HostTests(unittest.TestCase):
    sanitized=host_helper.HostTests.sanitized
    def test_shared_palettes_light_callback_selection_and_rejection(self):
        self.sanitized('v3_tree_families_test.c')


class TreeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.inventory=scenery.discover(cls.source,'carried-trees')

    def test_complete_family_graphs_flags_palettes_and_aliases(self):
        inv=self.inventory
        self.assertEqual(inv['counts'],dict(seasons=4,foreground_ids=27,descriptors=85,
                                           model_pairs=67,object_bytes=124160))
        expected={f'{n:04X}' for n in (*range(0x70,0x7B),0x82,*range(0x854,0x863))}
        for season,(table,_) in zip(scenery.SEASONS,sorted(self.source.names['draw_part_table_a']),strict=True):
            rows=[r for r in inv['descriptors'] if r['season']==season]
            self.assertEqual(len(rows),22 if season=='xmas' else 21)
            self.assertEqual({b['foreground_id'] for b in inv['bindings'] if b['season']==season},expected)
            for row in rows:
                self.assertEqual(row['flags'],u32(self.source.data,table+row['table_index']*8+4))
        lights=[d for r in inv['descriptors'] for d in r['body'] if d['callback_kind']=='coloured-lights']
        self.assertEqual(len(lights),1)
        self.assertEqual([inv['palettes'][f]['palette_slot'] for f in ('cedar','palm')],[6,7])
        self.assertEqual(len(inv['model_aliases']),4)
        for row in inv['model_aliases']:
            alias=row['source'];target=scenery.resource(self.source,row['target'],pointers=True)
            self.assertEqual((alias['sha256'],alias['bytes']),(target['sha256'],target['bytes']))
            self.assertEqual({p-alias['donor_offset']:v for p,v in alias['pointers'].items()},
                             {p-target['donor_offset']:v for p,v in target['pointers'].items()})
        cedar_shadows=[r for r in inv['objects'] if r['models'][0][0]=='obj_cedar3_shadowT_mat_model']
        self.assertEqual(len(cedar_shadows),3)
        self.assertEqual(len({r['render_context']['external_vertices'][1] for r in cedar_shadows}),3)

    def test_changed_light_function_alias_and_palette_cannot_disappear(self):
        source=copy.copy(self.source);source.rel=bytearray(source.rel)
        fn=self.inventory['functions']['bXI_draw_loop_type1_xtree'][0]
        source.rel[source.sections[1][0]+fn['offset']]^=1
        with self.assertRaisesRegex(ValueError,'drawing callback'):scenery.discover(source,'carried-trees')
        source=copy.copy(self.source);source.data=bytearray(source.data)
        source.data[self.inventory['model_aliases'][0]['source']['donor_offset']]^=1
        with self.assertRaisesRegex(ValueError,'Unconsumed'):scenery.discover(source,'carried-trees')
        for family in ('palm','cedar'):
            source=copy.copy(self.source);source.data=bytearray(source.data)
            source.data[self.inventory['palettes'][family]['bank']['donor_offset']]^=1
            with self.assertRaisesRegex(ValueError,'palette bank'):scenery.discover(source,'carried-trees')

    @unittest.skipUnless((ART/'art.json').is_file(),'Prepared carried-tree resources required')
    def test_complete_art_and_packing_preserve_all_dependencies(self):
        bundle=runtime.prepared(self.source,ART)
        art,assets,palettes,_=bundle
        rows=[dict(r,models=r['compiled_models']) for r in art['objects']]
        art_helper.DonorTests.check_complete_artwork(self,ART,dict(objects=rows),prepare=lambda row:
            prepare_material_pair(self.source,[tuple(row['profile']['models'][k]) for k in ('material','geometry')],
                                  render_context=row['render_context']))
        for family,data in palettes.items():
            self.assertEqual(len(data),448);self.assertEqual(sha256(data),art['palettes'][family]['output_sha256'])
        mixed,models,pals=runtime.merge_categories([runtime.prepared(self.source,ROOT/'build/v3-scenery-gold-tree-01'),bundle])
        wrappers={n:(BANKS/'palette'/('palette.bin' if n==8 else f'palette{n}.bin')).read_bytes() for n in (6,7,8)}
        for season in scenery.SEASONS:
            data,report=runtime.pack_bank(mixed,models,pals,season,wrappers,
                light_loop=runtime.LIGHT_OFFSET if season=='xmas' else 0)
            self.assertEqual(data,(BANKS/(season+'.bin')).read_bytes())
            self.assertEqual(len(data),106640 if season=='xmas' else 105216)
            h=struct.unpack_from('>32I',data)
            self.assertEqual((h[1],h[11],h[13],h[19]),(2,32 if season=='xmas' else 31,41,3))
            self.assertEqual({p['slot'] for p in report['palettes']},{6,7,8})
            self.assertEqual(set(report['selected_items']),{0x223B,0x2807,0x290A})
            kinds=[u32(data,h[8]+i*8+4) for i in range(h[9])]
            self.assertEqual(kinds.count(2),int(season=='xmas'))
            used=set()
            for table,count,stride in ((h[4],h[5],4),(h[6],h[7],4),(h[8],h[9],8)):
                for i in range(count):
                    at=u32(data,table+i*stride);self.assertNotIn(at,used);used.add(at)
                    self.assertEqual(at%4,0);self.assertTrue(128<=at<=len(data)-4)
                    if stride==4:self.assertTrue(128<=u32(data,at)<len(data))
            # Every full descriptor's original flags survive packing, including palms.
            descriptors=[r for r in mixed['descriptors'] if r['season']==season]
            for i,row in enumerate(descriptors):self.assertEqual(u32(data,h[10]+i*8+4),row['flags'])
        with self.assertRaisesRegex(ValueError,'callback'):
            runtime.pack_bank(mixed,models,pals,'xmas',wrappers)


@unittest.skipUnless((BUILD/'build-lock.json').is_file(),'Current combined tree build required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from v3_furniture_install import inputs
        from v3_asset_loader import BLOB
        cls.rom,cls.report=inputs(BUILD/'build-lock.json')
        cls.base,cls.prior=inputs(BUILD/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.e=cls.report['equipment_resources'];cls.scene=cls.e['scenery']
        cls.blob=cls.files[BLOB].extract(cls.rom)

    def test_full_seasonal_bank_reconstruction_and_physical_ownership(self):
        p=self.scene['families']['packet']
        self.assertEqual(sha256(self.rom[p['physical']:p['physical']+p['bytes']]),p['sha256'])
        self.assertEqual(self.base[p['physical']:p['physical']+p['bytes']],bytes(p['bytes']))
        self.assertLess(p['bytes'],sum(b['bytes'] for b in self.scene['banks']))
        sources=set()
        for bank in self.scene['banks']:
            start=bank['vrom']&0x3FFFFFFF
            self.assertEqual(start,p['physical']+bank['packet_offset'])
            header=struct.unpack_from('>36I',self.rom,start)
            self.assertEqual(header[:4],(0x41465047,bank['bytes'],4096,(bank['bytes']+4095)//4096))
            rebuilt=bytearray()
            for i,address in enumerate(header[4:4+header[3]]):
                n=min(4096,bank['bytes']-i*4096)
                self.assertEqual(address,p['physical']+bank['page_offsets'][i])
                self.assertTrue(p['physical']+144*4<=address<address+n<=p['physical']+p['bytes'])
                self.assertEqual(address%16,0);sources.add(address)
                rebuilt.extend(self.rom[address:address+n])
            self.assertEqual(rebuilt,(BANKS/(bank['season']+'.bin')).read_bytes())
            self.assertEqual((sha256(rebuilt),zlib.crc32(rebuilt)),(bank['sha256'],bank['crc32']))
        self.assertLess(len(sources),sum(len(b['page_offsets']) for b in self.scene['banks']))
        from v3_physical_resources import verify
        verify(self.rom,self.report['physical_resources'])

    def test_all_seasonal_tables_arrays_stack_and_relocated_allocation(self):
        from npc_mail_show import relocate_verified_data
        from v3_player_actions import native_references
        core=self.files[CODE_VROM].extract(self.rom)
        for row,ground in zip(self.scene['owners'],self.e['ground_categories']['owners'],strict=True):
            data=self.files[row['vrom']].extract(self.rom);rel=self.files[row['reloc']].extract(self.rom)
            before=self.before[row['vrom']].extract(self.base);oldrel=self.before[row['reloc']].extract(self.base)
            cap=ground['capacity'];restored=bytearray(data)
            for h in row['patches']:
                self.assertEqual(u32(before,h['offset']),h['before']);self.assertEqual(u32(data,h['offset']),h['after'])
                struct.pack_into('>I',restored,h['offset'],h['before'])
            self.assertEqual(restored,before);self.assertEqual(rel[:12],oldrel[:12]);self.assertEqual(rel[16:],oldrel[16:])
            self.assertEqual(sha256(data),ground['output_sha256']);self.assertEqual(sha256(rel),ground['output_reloc_sha256'])
            self.assertEqual(u32(core,row['allocation_descriptor']-CODE_RAM+12),row['ram']+cap['resident_bytes'])
            self.assertEqual(cap['actor_bytes'],ground['actor']+cap['count']*8)
            self.assertEqual(cap['index_stride'],cap['count']*2)
            self.assertEqual(cap['stack_bytes'],176+2*(cap['count']-ground['count']))
            self.assertLessEqual(row['first_index']+row['descriptor_count'],cap['count'])
            self.assertGreaterEqual(cap['table_offset'],row['bank_offset']+row['bank_bytes'])
            self.assertEqual(cap['empty_offset'],cap['table_offset']+cap['count']*8)
            groups,*_=native_references(data,rel,expected_sections=struct.unpack_from('>4I',rel))
            for hi,lo in ground['refs']:
                self.assertIn((lo,row['ram']+cap['table_offset']),groups[hi])
            for address in (0x80200010,0x80300010):
                loaded=relocate_verified_data(SimpleNamespace(ram=row['ram'],resident_bytes=cap['resident_bytes'],
                    sections=struct.unpack_from('>5I',rel)),data,rel,address)
                self.assertEqual(loaded[len(data):],bytes(cap['bss_bytes']))
                for hi,lo in ground['refs']:
                    low=u32(loaded,lo)&65535;low=low-65536 if low&32768 else low
                    self.assertEqual(((u32(loaded,hi)&65535)<<16)+low,address+cap['table_offset'])
                self.assertEqual(u32(loaded,u32(rel,0)+16),self.scene['bootstrap']['symbols']['af_v3_scenery_'+row['role']])

    def test_rebound_consumers_preserve_all_other_code_and_startup_checksums(self):
        old=self.prior['equipment_resources']['scenery'];new=self.scene
        symbols=old['code']['symbols'];next_symbols=new['code']['symbols']
        targets={value:name for name,value in symbols.items() if name.startswith('af_v3_') and
                 old['ram']<=value<old['ram']+old['bytes']}
        targets.update({value:name for name,value in old['bootstrap']['symbols'].items() if name.startswith('af_v3_')})
        updates={**next_symbols,**new['bootstrap']['symbols']}
        for row in new['families']['bindings']:
            data=self.files[row['vrom']].extract(self.rom);before=self.before[row['vrom']].extract(self.base)
            restored=bytearray(data)
            for h in row['patches']:
                self.assertEqual(u32(data,h['offset']),h['after']);struct.pack_into('>I',restored,h['offset'],h['before'])
            self.assertEqual(restored,before);self.assertEqual(sha256(data),row['sha256'])
            # Every direct call into the moved shared code must still target the
            # same export, including calls inside the register-preserving gate.
            for at in range(0,len(before),4):
                word=u32(before,at)
                if word>>26 not in (2,3):continue
                target=0x80000000|((word&0x3FFFFFF)<<2)
                if target in targets:
                    from v3_import_storage import jump
                    self.assertEqual(u32(data,at),jump(updates[targets[target]],link=word>>26==3))
        insect=self.e['creature_insects'];p=insect['packet'];raw=self.rom[p['physical']:p['physical']+p['bytes']]
        at=insect['compiled']['symbols']['af_insect_tree_bee_query']-p['ram']
        self.assertEqual(u32(raw,at),next_symbols['af_v3_tree_bee_query'])
        self.assertEqual(sha256(raw[:insect['compiled']['bytes']]),insect['compiled']['sha256'])
        boot=self.e['surface_bootstrap']['code'];start=self.e['blob_offset']+boot['symbols']['packets']-self.e['ram']
        for i in range(boot['packet_count']):
            ram,vrom,n,crc=struct.unpack_from('>4I',self.blob,start+i*boot['packet_stride'])
            if vrom&0x80000000:raw=self.rom[vrom&0x7FFFFFFF:(vrom&0x7FFFFFFF)+n]
            else:
                file=next(f for f in self.files.values() if f.vstart<=vrom<vrom+n<=f.vend)
                raw=file.extract(self.rom)[vrom-file.vstart:vrom-file.vstart+n]
            self.assertEqual(zlib.crc32(raw),u32(self.blob,self.e['blob_offset']+crc-self.e['ram']),hex(ram))
        self.assertEqual(self.report['save_runtime']['profile_hex'],self.prior['save_runtime']['profile_hex'])
        self.assertEqual(self.e['carried_items'],self.prior['equipment_resources']['carried_items'])
        self.assertFalse(new['families']['field_behaviours_complete'])
        self.assertLessEqual(new['bytes'],12288)

    def test_subsequent_shared_refresh_reuses_complete_art_and_allocations(self):
        import v3_scenery_refresh as refresh
        def compiled(part,*args,**kwargs):
            row=self.scene['code' if part=='scenery' else 'bootstrap']
            return (BUILD/part/'code.bin').read_bytes(),copy.deepcopy(row)
        wrappers={name:(BUILD/'palette'/(name+'.bin')).read_bytes() for name in ('palette','palette6','palette7')}
        core=bytearray(self.files[CODE_VROM].extract(self.rom));blob=bytearray(self.blob)
        with tempfile.TemporaryDirectory(prefix='tree-refresh-',dir=ROOT/'build') as directory, \
                patch.object(refresh,'compile_part',side_effect=compiled), \
                patch('map_artwork.compile_commands',return_value=wrappers):
            equipment,changes,updates,writes=refresh.install(self.rom,self.report,blob,core,None,Path(directory),ART)
        self.assertEqual(blob,self.blob);self.assertEqual(core,self.files[CODE_VROM].extract(self.rom))
        self.assertEqual(updates['physical_resources'],self.report['physical_resources'])
        for vrom,data in changes.items():self.assertEqual(data,self.files[vrom].extract(self.rom))
        self.assertEqual(len(writes),1) # retained insect query, no new artwork write
        self.assertEqual(equipment['ground_categories'],self.e['ground_categories'])
        self.assertEqual(equipment['scenery']['families']['packet'],self.scene['families']['packet'])
        self.assertTrue(all(r['additional_scene_bytes']==0 for r in equipment['scenery']['families']['allocation']))


if __name__=='__main__':unittest.main()
