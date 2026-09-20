"""Shared format discovery, conversion integrity, and current batch installation."""
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
from aflib import CODE_RAM,CODE_VROM,DMA_START,DMA_END,by_vrom,sha256,n64_checksum
from tests.test_v3_furniture_art import fixture
from v3_furniture_art import parse_model,command_source,SCHOOL_DESKS,scalar_profile
from v3_villager_art import data_pointers
import v3_furniture_pipeline as pipeline
import v3_furniture_install as install
import v3_optional_composition as composer
import v3_catalogue as catalogue
import v3_shops as shops
import v3_hra as hra
import v3_feng_shui as feng


class FormatTests(unittest.TestCase):
    def test_ia8_retains_every_intensity_alpha_pair_and_tiled_sample(self):
        for w,h in ((8,4),(16,16),(32,32)):
            raw=bytearray(w*h);expected=bytearray(w*h)
            for y in range(h):
                for x in range(w):
                    i=y*w+x;value=(i*73)&255
                    gx=((y//4)*(w//8)+x//8)*32+y%4*8+x%8
                    raw[gx]=value;expected[i]=(value&15)<<4|value>>4
            self.assertEqual(pipeline.native_ia8(raw,w,h),expected)
        for raw,w,h in ((bytes(32),4,8),(bytes(31),8,4),(bytes(32),8,0)):
            with self.assertRaises(ValueError):pipeline.native_ia8(raw,w,h)

    def test_ia8_material_keeps_alpha_format_stride_and_direct_lut(self):
        original,_=fixture();raw=bytearray(original[:0x18]+original[0x20:])
        pointers={0x11C:0x600,0x13C:0x1000}
        struct.pack_into('>I',raw,0x18,0xFD6C1C1F)
        struct.pack_into('>I',raw,0x20,0xD2F00511)
        rows=parse_model(raw,0x100,pointers,(),{0x600:(32,32)},0x1000,48,static_materials=True)
        texture=next(r for r in rows if r['opcode']==0xFD)
        self.assertTrue(texture['ia8']);self.assertNotIn('rgba16',texture)
        code,_=command_source({'opaque':{'rows':rows}},{0x600:0,0x1000:1024})
        self.assertIn('G_IM_FMT_IA, G_IM_SIZ_8b, 32, 32, 0, G_TX_WRAP, G_TX_WRAP, 5, 5, 1, 1',code)
        self.assertIn('gsDPSetTextureLUT(G_TT_NONE)',code)
        self.assertNotIn('gsDPLoadTLUT',code)
        for field,value in (('shape',(64,64)),('shape',(12,8)),('rgba16',True),('intensity',True)):
            bad=copy.deepcopy(rows);next(r for r in bad if r['opcode']==0xFD)[field]=value
            with self.assertRaises(ValueError):command_source({'opaque':{'rows':bad}},{0x600:0,0x1000:1024})

    def test_joint_matrices_preserve_partial_vertex_cache_and_reject_future_reads(self):
        raw,pointers=fixture();pointers.pop(0x144)
        words=[(0xDA380003,0x0D000000),(0x01002004,0),
               (0xDA380003,0x0D000040),(0x01001006,0),
               (0x0A000000,(1<<5|2<<10)<<4),(0xDF000000,0)]
        raw=bytearray(raw[:0x40]+b''.join(struct.pack('>II',*w) for w in words))
        pointers.update({0x14C:0x1010,0x15C:0x1000})
        def parse(data=raw,fixups=pointers,limit=2):
            return parse_model(data,0x100,fixups,(0x500,),{0x600:(32,32)},0x1000,48,
                               static_materials=True,joint_matrices=limit)
        rows=parse()
        self.assertEqual(next(r['global_triangles'] for r in rows if 'triangles' in r),[(1,2,0)])
        self.assertEqual([r['joint_matrix'] for r in rows if r['opcode']==0xDA],[0,1])
        self.assertEqual([r.get('vertex_slot',0) for r in rows if r['opcode']==1],[0,2])
        code,_=command_source({'joint1':{'rows':rows}},{0x500:0,0x600:32,0x1000:544})
        self.assertIn('gsSPVertex(0x06000220, 1, 2)',code)
        self.assertIn('gsSPMatrix(0x0D000040, G_MTX_NOPUSH | G_MTX_LOAD | G_MTX_MODELVIEW)',code)
        for off,value in ((0x44,0x0D000080),(0x44,0x0D000001),(0x44,0x0C000000),
                          (0x40,0xDA380001),(0x58,0x01001008),(0x58,0x01001042)):
            bad=bytearray(raw);struct.pack_into('>I',bad,off,value)
            with self.subTest(offset=off,value=value),self.assertRaises(ValueError):parse(bad)
        for limit in (0,1,-1,256,True):
            with self.assertRaises(ValueError):parse(limit=limit)
        with self.assertRaisesRegex(ValueError,'Unaccounted'):parse(fixups={**pointers,0x144:0x1000})

    def test_static_model_linker_keeps_order_and_rejects_bad_layouts(self):
        profile={'callback_adapter':{'category':'constant-model-sequence','draw_arena':'opaque',
                                     'model_order':['part0','part1','part2']}}
        sections=[('part0',16),('part1',24),('part2',8)]
        record,raw=pipeline.draw_sequence(profile,64,sections)
        self.assertEqual(record['native_offset'],112)
        self.assertEqual(record['model_offsets'],{'part0':64,'part1':80,'part2':104})
        self.assertEqual(list(struct.iter_unpack('>II',raw)),
            [(0xDE000000,0x06000040),(0xDE000000,0x06000050),(0xDE000000,0x06000068),(0xDF000000,0)])
        self.assertEqual(record['output_sha256'],sha256(raw))
        for body,sections in ((65,sections),(64,sections[::-1]),(64,[('part0',7),*sections[1:]])):
            with self.assertRaises(pipeline.ReviewRequired):pipeline.draw_sequence(profile,body,sections)
        self.assertEqual(pipeline.draw_sequence({},64,[]),(None,b''))

    def test_dynamic_palette_keeps_segment_and_refuses_constant_or_relocated_binding(self):
        raw,pointers=fixture();raw=bytearray(raw)
        struct.pack_into('>I',raw,0x1C,0x08000000);pointers.pop(0x11C)
        def parse(**kwargs):
            return parse_model(raw,0x100,pointers,(0x500,),{0x600:(32,32)},0x1000,48,
                               static_materials=True,palette_fade=True,**kwargs)
        rows=parse();palette=next(r for r in rows if r['opcode']==0xF0)
        self.assertEqual(palette['dynamic_palette'],0x08000000)
        source,_=command_source({'part0':{'rows':rows}},{0x500:32,0x600:64,0x1000:576})
        self.assertIn('gsDPLoadTLUT_pal16(15, 0x08000000)',source)
        with self.assertRaisesRegex(ValueError,'no constant binding'):parse(palette_bindings={0x08000000:0x500})
        pointers[0x11C]=0x500
        with self.assertRaisesRegex(ValueError,'also has a relocation'):parse()

    def test_shared_camping_trade_categories_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-shared-camping-') as temporary:
            binary=Path(temporary)/'test'
            subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_camper_trade_test.c'),str(ROOT/'overlays/v3/camper_trade.c'),
                '-o',str(binary)],check=True,capture_output=True)
            result=subprocess.run([str(binary)],check=True,capture_output=True,text=True,timeout=20)
            self.assertIn('actual camping rewards, optional profiles, exclusions, donor rolls',result.stdout)

    def test_shared_reward_categories_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-furniture-rewards-') as temporary:
            binary=Path(temporary)/'test'
            subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_furniture_rewards_test.c'),'-o',str(binary)],check=True,capture_output=True)
            result=subprocess.run([str(binary)],check=True,capture_output=True,text=True,timeout=20)
            self.assertIn('Reward categories, sparse profiles, exclusions, bounds, and seven-argument fallbacks pass',result.stdout)

    def test_four_cell_item_readers_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-four-cell-items-') as temporary:
            binary=Path(temporary)/'test'
            subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_four_cell_items_test.c'),'-o',str(binary)],check=True,capture_output=True)
            result=subprocess.run([str(binary)],check=True,capture_output=True,text=True,timeout=20)
            self.assertIn('Four-cell size, all rotations, sparse selection, signed boundaries, and original fallbacks pass',
                          result.stdout)

    def test_unlit_material_uses_native_texture_primitive_expression_without_item_switches(self):
        raw,pointers=fixture();raw=bytearray(raw)
        struct.pack_into('>II',raw,8,0xFCFFFE60,0xFFFCF3F8)
        rows=parse_model(raw,0x100,pointers,(0x500,),{0x600:(32,32)},0x1000,48,static_materials=True)
        self.assertTrue(rows[1]['unlit_texture_primitive'])
        source,_=command_source({'opaque':{'rows':rows}},{0x500:0,0x600:32,0x1000:544})
        self.assertIn('gsDPSetCombineLERP(0, 0, 0, TEXEL0, 0, 0, 0, TEXEL0, '
                      'PRIMITIVE, 0, COMBINED, 0, 0, 0, 0, COMBINED)',source)
        struct.pack_into('>I',raw,12,0xFFFCF3F9)
        with self.assertRaisesRegex(ValueError,'colour combiner'):
            parse_model(raw,0x100,pointers,(0x500,),{0x600:(32,32)},0x1000,48,static_materials=True)

    def test_constant_palette_binding_preserves_commands_and_rejects_ambiguous_dependencies(self):
        raw,pointers=fixture();raw=bytearray(raw)
        struct.pack_into('>I',raw,0x1C,0x08000000)
        pointers.pop(0x11C)
        def parse(binding, fixups=pointers):
            return parse_model(raw,0x100,fixups,(0x500,),{0x600:(32,32)},0x1000,48,
                               static_materials=True,palette_bindings=binding)
        rows=parse({0x08000000:0x500})
        palette=next(r for r in rows if r['opcode']==0xF0)
        self.assertEqual(palette['target'],0x500)
        self.assertEqual(palette['bound_segment'],0x08000000)
        source,_=command_source({'opaque':{'rows':rows}},{0x500:0,0x600:32,0x1000:544})
        self.assertIn('gsDPLoadTLUT_pal16(15, 0x06000000)',source)
        self.assertNotIn('0x08000000',source)
        for bindings in ({},{0x09000000:0x500},{0x08000000:0x501}):
            with self.assertRaises(ValueError): parse(bindings)
        with self.assertRaises(ValueError): parse({0x08000000:0x500},{**pointers,0x11C:0x500})

    def test_shared_seating_categories_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-seating-sounds-') as temporary:
            binary=Path(temporary)/'test'
            subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_furniture_behaviours_test.c'),'-o',str(binary)],check=True,capture_output=True)
            result=subprocess.run([str(binary)],check=True,capture_output=True,text=True,timeout=20)
            self.assertIn('original fallbacks, and bounds pass',result.stdout)

    def test_category_rules_preserve_colour_and_all_valid_wrap_combinations(self):
        raw,pointers=fixture()
        for s in range(3):
            for t in range(3):
                changed=bytearray(raw)
                struct.pack_into('>I',changed,0x28,0xD2F0F000|s<<10|t<<8)
                struct.pack_into('>I',changed,0x34,0x123456FF)
                rows=parse_model(changed,0x100,pointers,(0x500,),{0x600:(32,32)},0x1000,48,static_materials=True)
                self.assertIn((0xFA000080,0x123456FF),[r['words'] for r in rows])
                source,_=command_source({'opaque':{'rows':rows}},{0x500:0,0x600:32,0x1000:544})
                self.assertIn('gsSPVertex',source)
        for value in (0xD2F0FC00,0xD2F0F300,0xD2F1F000):
            changed=bytearray(raw);struct.pack_into('>I',changed,0x28,value)
            with self.assertRaises(ValueError):
                parse_model(changed,0x100,pointers,(0x500,),{0x600:(32,32)},0x1000,48,static_materials=True)

    def test_palette_free_intensity_and_asymmetric_texture_scales_shifts(self):
        original,_=fixture()
        raw=bytearray(original[:0x18]+original[0x20:])
        pointers={0x11C:0x600,0x13C:0x1000}
        struct.pack_into('>I',raw,0x18,0xFD841C1F)
        struct.pack_into('>I',raw,4,0x11940FA0)
        for s,t in ((0,1),(2,1),(15,15)):
            struct.pack_into('>I',raw,0x20,0xD2F0F500|s<<4|t)
            rows=parse_model(raw,0x100,pointers,(),{0x600:(32,32)},0x1000,48,static_materials=True)
            texture=next(r for r in rows if r['opcode']==0xFD)
            self.assertTrue(texture['intensity']);self.assertEqual(texture['tile_shifts'],(s,t))
            source,_=command_source({'translucent':{'rows':rows}},{0x600:0,0x1000:512})
            self.assertIn('gsSPTexture(4500, 4000,',source)
            self.assertIn('gsDPSetTextureLUT(G_TT_NONE)',source)
            self.assertNotIn('gsDPLoadTLUT',source)
            self.assertIn(f'G_IM_FMT_I, 32, 32, 0, G_TX_WRAP, G_TX_WRAP, 5, 5, {s}, {t}',source)
        struct.pack_into('>I',raw,0x18,0xFD441C1F)
        with self.assertRaisesRegex(ValueError,'texture or palette'):
            parse_model(raw,0x100,pointers,(),{0x600:(32,32)},0x1000,48,static_materials=True)

    def test_mixed_materials_switch_native_palette_mode_at_each_format_change(self):
        raw,pointers=fixture();words=list(struct.iter_unpack('>II',raw));triangle=words[-2]
        words=words[:-1]+[(0xFD841C1F,0),(0xD2F0F521,0),triangle,
                          (0xFD441C1F,0),(0xD2F0F000,0),triangle,words[-1]]
        pointers.update({0x154:0x700,0x16C:0x800})
        rows=parse_model(b''.join(struct.pack('>II',*w) for w in words),0x100,pointers,(0x500,),
            {a:(32,32) for a in (0x600,0x700,0x800)},0x1000,48,static_materials=True)
        source,_=command_source({'opaque':{'rows':rows}},
            {0x500:0,0x600:32,0x700:544,0x800:1056,0x1000:1568})
        self.assertEqual(source.count('gsDPSetTextureLUT(G_TT_RGBA16)'),2)
        self.assertEqual(source.count('gsDPSetTextureLUT(G_TT_NONE)'),1)

    def test_direct_colour_untile_preserves_all_opaque_and_transparent_samples(self):
        for w,h in ((4,4),(8,12),(12,8)):
            raw=bytearray(w*h*2);expected=bytearray(w*h*2)
            for y in range(h):
                for x in range(w):
                    i=y*w+x
                    pixel=(0x8000|(i*971)&0x7FFF) if i%3 else (i*337)&0xFFF
                    gx=((y//4)*(w//4)+x//4)*16+y%4*4+x%4
                    struct.pack_into('>H',raw,gx*2,pixel)
                    if pixel&0x8000:
                        native=((pixel&0x7FFF)<<1)|1
                    else:
                        r,g,b=((pixel>>s&15)*17>>3 for s in (8,4,0))
                        native=r<<11|g<<6|b<<1
                    struct.pack_into('>H',expected,i*2,native)
            self.assertEqual(pipeline.native_rgba16(raw,w,h),expected)
        for bad in (0x1000,0x6000):
            with self.assertRaisesRegex(pipeline.ReviewRequired,'Partial-alpha'):
                pipeline.native_rgba16(struct.pack('>16H',bad,*([0xFFFF]*15)),4,4)
        for data,w,h in ((bytes(32),3,4),(bytes(30),4,4),(bytes(32),4,0)):
            with self.assertRaises(pipeline.ReviewRequired):pipeline.native_rgba16(data,w,h)

    def test_direct_colour_material_has_native_16bit_load_and_no_palette(self):
        original,_=fixture();raw=bytearray(original[:0x18]+original[0x20:])
        pointers={0x11C:0x600,0x13C:0x1000}
        struct.pack_into('>I',raw,0x18,0xFD141C0F)
        struct.pack_into('>I',raw,0x20,0xD2F00800)
        rows=parse_model(raw,0x100,pointers,(),{0x600:(16,32)},0x1000,48,static_materials=True)
        texture=next(r for r in rows if r['opcode']==0xFD)
        self.assertTrue(texture['rgba16']);self.assertNotIn('intensity',texture)
        source,_=command_source({'opaque':{'rows':rows}},{0x600:0,0x1000:1024})
        self.assertIn('gsDPLoadTextureBlock(0x06000000, G_IM_FMT_RGBA, G_IM_SIZ_16b, 16, 32, 0,',source)
        self.assertIn('gsDPSetTextureLUT(G_TT_NONE)',source)
        self.assertNotIn('gsDPLoadTLUT',source)
        for shape in ((32,64),(6,8)):
            texture['shape']=shape
            with self.assertRaises(ValueError):command_source({'opaque':{'rows':rows}},{0x600:0,0x1000:1024})

    def test_record_driven_catalogue_under_address_and_undefined_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-catalogue-records-') as temporary:
            binary=Path(temporary)/'test'
            subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_catalogue_records_test.c'),'-o',str(binary)],check=True,capture_output=True)
            result=subprocess.run([str(binary)],check=True,capture_output=True,text=True,timeout=20)
            self.assertIn('categories and bounds pass',result.stdout)


class DonorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=pipeline.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        _,current=composer.inputs()
        cls.art=ROOT/current['automatic_furniture']['art_directory']
        cls.report=json.loads((cls.art/'art.json').read_bytes())

    def test_indexed_model_sequences_discover_complete_categories_and_conditional_layers(self):
        inventory=pipeline.scan(self.source,ROOT/'build/item-identity-megasheet.xlsx',[])
        rows=[r for r in inventory['rows'] if 'indexed-model-sequence' in r.get('categories',[])]
        self.assertEqual(len(rows),24)
        self.assertTrue(all(r['asset_ready'] and r['status']=='review' and 'room_alias' in r for r in rows))
        self.assertEqual(sum('translucent' in r['profile']['models'] for r in rows),2)
        for row in rows:
            item=int(row['item_id'],16);profile,_,_,_,models,_,_=pipeline.prepare(self.source,item)
            adapter=profile['callback_adapter'];draw=adapter['functions']['draw']
            self.assertEqual(draw['normalized_sha256'],pipeline.INDEXED_SEQUENCE_CODE[draw['bytes']][0])
            self.assertEqual(adapter['selected_index'],1024+(item-0x3000)//4-adapter['first_runtime_index'])
            self.assertEqual(set(models),set(adapter['model_sequences']))
            for label,parts in adapter['model_sequences'].items():
                raw,pointers,receipts=self.source.model_sequence(parts)
                originals=[self.source.data[a:a+n] for _,a,n in parts]
                self.assertEqual(raw,b''.join(r[:-8] for r in originals[:-1])+originals[-1])
                self.assertEqual(receipts,models[label]['source_parts'])
                self.assertEqual(sha256(raw),models[label]['source_sha256'])
                for part in receipts:
                    a,n=part['donor_offset'],part['bytes']
                    self.assertEqual(part['sha256'],sha256(self.source.data[a:a+n]))
                    for p,target in data_pointers(self.source.rel,a,n).items():
                        self.assertEqual(pointers[part['joined_offset']+p-a],target)
            if adapter['conditional_translucent']:
                self.assertEqual('translucent' in models,adapter['selected_index']==adapter['entries']-1)
                if 'translucent' in models:
                    self.assertEqual(adapter['model_sequences']['translucent'],adapter['conditional_translucent'])

    def test_indexed_sequences_reject_extra_effects_incomplete_tables_and_bad_returns(self):
        # One representative per actual compiled draw shape, not one scenario per item.
        inventory=pipeline.scan(self.source,ROOT/'build/item-identity-megasheet.xlsx',[])
        shapes={r['profile']['callback_adapter']['functions']['draw']['bytes']:r
            for r in inventory['rows'] if 'indexed-model-sequence' in r.get('categories',[])}
        self.assertEqual(set(shapes),{136,168,284})
        for row in shapes.values():
            item=int(row['item_id'],16);adapter=row['profile']['callback_adapter'];draw=adapter['functions']['draw']
            changed=copy.copy(self.source);changed.rel=bytearray(self.source.rel)
            changed.rel[self.source.sections[1][0]+draw['offset']+0x20]^=1
            with self.assertRaisesRegex(ValueError,'indexed sequence'):changed.profile(item)
            changed=copy.copy(self.source);changed.relocations=dict(self.source.relocations)
            changed.relocations.pop(adapter['tables'][0]['offset'])
            changed.relocation_addresses=sorted(changed.relocations)
            with self.assertRaisesRegex(ValueError,'selector table'):changed.profile(item)
            parts=adapter['model_sequences']['opaque'];_,at,n=parts[-1]
            changed=copy.copy(self.source);changed.data=bytearray(self.source.data)
            changed.data[at+n-1]^=1
            with self.assertRaisesRegex(ValueError,'final return'):changed.model_sequence(parts)
            changed=copy.copy(self.source);changed.relocations=dict(self.source.relocations)
            changed.relocations[at+n-4]=(1,True,5,at)
            changed.relocation_addresses=sorted(changed.relocations)
            with self.assertRaisesRegex(ValueError,'relocated model sequence return'):changed.model_sequence(parts)
            with self.assertRaisesRegex(ValueError,'selector escapes'):
                self.source.callback_models(row['profile']['profile_offset'],adapter['first_runtime_index']-1)
            if adapter['conditional_translucent']:
                changed=copy.copy(self.source);changed.rel=bytearray(self.source.rel)
                changed.rel[self.source.sections[1][0]+draw['offset']+0x9F]^=1
                with self.assertRaisesRegex(ValueError,'conditional layer selector'):changed.profile(item)

    def test_actual_donor_executable_maps_direct_colour_to_rgb5a3(self):
        from v3_villager_audio import read_audio_donor
        dol,_=read_audio_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
        table=dol.read(0x800AAFC0,64)
        self.assertEqual(sha256(table),'7ae4019ff69d72ee09dd42b8b1c5a4c7a3a236d07aa238e2acdb93c97302fe30')
        self.assertEqual(struct.unpack_from('>H',table,2*2)[0],5)  # RGBA/16 -> GX_RGB5A3
        self.assertEqual(struct.unpack_from('>H',table,2*4*2)[0],8)  # CI/4 -> GX_C4
        self.assertEqual(struct.unpack_from('>H',table,4*4*2)[0],0)  # I/4 -> GX_I4
        self.assertEqual(struct.unpack_from('>H',table,(3*4+1)*2)[0],2)  # IA/8 -> GX_IA4

    def test_palette_fade_category_discovers_all_shared_code_and_complete_layouts(self):
        inventory=pipeline.scan(self.source,ROOT/'build/item-identity-megasheet.xlsx')
        rows=[r for r in inventory['rows'] if 'switch-palette-fade' in r.get('categories',[])]
        self.assertEqual(len(rows),8)
        self.assertEqual(sum(r['status']=='supported' for r in rows),1)
        self.assertEqual({r['reason'].split(':')[0] for r in rows if r['status']=='review'},
                         {'acquisition needs an adapter'})
        for row in rows:
            p,body,resources,offsets,models,_,sections=pipeline.prepare(self.source,int(row['item_id'],16))
            adapter=p['callback_adapter'];self.assertEqual(p['interaction_flags'],0x8000)
            self.assertEqual(list(models),adapter['model_order']);self.assertEqual(len(models),3)
            self.assertEqual(struct.unpack_from('>IHH',body),(0x41465031,row['object_bytes'],3))
            self.assertEqual(struct.unpack_from('>2I',body,8),tuple(
                offsets[adapter['endpoints'][role]['donor_offset']] for role in ('on','off')))
            cursor=len(body)
            for i,(label,n) in enumerate(sections):
                self.assertEqual(struct.unpack_from('>I',body,16+i*4)[0],0x06000000+cursor)
                cursor+=n
            self.assertEqual(body[28:32],bytes(4))
            for role,f in adapter['functions'].items():
                self.assertEqual(f['normalized_sha256'],pipeline.PALETTE_FADE_CODE[role][1])
                self.assertEqual(set(f['local_calls']),set(pipeline.PALETTE_FADE_CODE[role][2]))
        # The roof-colour selector is a different effect, not a static alias.
        with self.assertRaises(pipeline.ReviewRequired):self.source.profile(0x3024)

    def test_constant_draw_sequences_keep_all_models_and_reject_additional_effects(self):
        inventory=pipeline.scan(self.source,ROOT/'build/item-identity-megasheet.xlsx')
        rows=[r for r in inventory['rows'] if 'constant-model-sequence' in r.get('categories',[])]
        self.assertEqual(sorted(len(r['profile']['models']) for r in rows),[1,3])
        self.assertTrue(all(r['status']=='supported' for r in rows))
        for row in rows:
            item=int(row['item_id'],16);profile,body,_,_,models,_,sections=pipeline.prepare(self.source,item)
            adapter=profile['callback_adapter'];draw=adapter['functions']['draw']
            self.assertEqual(adapter['null_callbacks'],['create','move','destroy'])
            self.assertEqual(list(models),adapter['model_order']);self.assertEqual(adapter['draw_arena'],'opaque')
            record,linked=pipeline.draw_sequence(profile,len(body),sections)
            self.assertEqual(record['bytes'],(len(models)+1)*8)
            self.assertEqual(row['object_bytes'],(record['native_offset']+len(linked)+15)&~15)
            raw=self.source.function(draw['offset'])[0]
            for location in (0,0x34):
                changed=copy.copy(self.source);changed.rel=bytearray(self.source.rel)
                changed.rel[self.source.sections[1][0]+draw['offset']+location+3]^=4
                with self.assertRaisesRegex(ValueError,'fixed draw'):changed.profile(item)
            # Even a valid function pointer must not replace a null move with effects.
            changed=copy.copy(self.source);changed.relocations=dict(self.source.relocations)
            changed.relocations[adapter['vtable_offset']+4]=(1,True,1,draw['offset'])
            with self.assertRaisesRegex(ValueError,'lifecycle effects'):changed.profile(item)
            changed=copy.copy(self.source);changed.code_relocations=dict(self.source.code_relocations)
            location=next(iter(draw['relocations']))
            kind,module,section,target=draw['relocations'][location]
            changed.code_relocations[draw['offset']+location]=(kind,module,section,target+8)
            with self.assertRaises(ValueError):changed.profile(item)

    def test_palette_category_rejects_changed_code_calls_palettes_and_effects(self):
        p=self.source.profile(0x31A4);adapter=p['callback_adapter']
        f=adapter['functions']['move'];text=self.source.sections[1][0]
        for loc in (0,0x24):
            changed=copy.copy(self.source);changed.rel=bytearray(self.source.rel)
            changed.rel[text+f['offset']+loc+3]^=4
            with self.assertRaisesRegex(ValueError,'palette fade'):changed.profile(0x31A4)
        changed=copy.copy(self.source);changed.code_relocations=dict(self.source.code_relocations)
        changed.code_relocations[f['offset']+0x0A]=(6,1,5,0)
        with self.assertRaisesRegex(ValueError,'dependencies'):changed.profile(0x31A4)
        off=adapter['endpoints']['off']['donor_offset'];on=adapter['endpoints']['on']['donor_offset']
        changed=copy.copy(self.source);changed.data=bytearray(self.source.data)
        struct.pack_into('>H',changed.data,on+6,0x09AD)
        with self.assertRaisesRegex(ValueError,'changing colours'):changed.profile(0x31A4)
        struct.pack_into('>H',changed.data,on+6,0x19AC)
        with self.assertRaisesRegex(ValueError,'Partial-alpha'):changed.profile(0x31A4)
        changed=copy.copy(self.source);changed.data=bytearray(self.source.data)
        changed.data[p['profile_offset']+44]=1
        with self.assertRaisesRegex(ValueError,'contact/interaction'):changed.profile(0x31A4)

    def test_indexed_dependencies_match_independent_relocation_reader(self):
        for row in self.report['objects'][:3]:
            for model in row['models']:
                at,n=self.source.symbol(model['symbol'])
                self.assertEqual(self.source.pointers(at,n),data_pointers(self.source.rel,at,n))

    def test_profile_discovery_preserves_existing_desk_scalars_and_shape_footprint(self):
        for desk in SCHOOL_DESKS:
            p=self.source.profile(desk.item)
            self.assertEqual(bytes.fromhex(p['scalar_hex']),scalar_profile(desk))
            self.assertEqual(p['size_code'],int(desk.shape==3))
        # Collision is independent of the shape-derived footprint.
        source=copy.copy(self.source);source.data=bytearray(source.data)
        p=source.profile(0x3220);source.data[p['profile_offset']+41]=0
        self.assertEqual(source.profile(0x3220)['size_code'],1)

    def test_review_does_not_drop_callbacks_or_unknown_action_sounds(self):
        with self.assertRaisesRegex(ValueError,'custom callbacks'): self.source.profile(0x3350)
        identities=pipeline.identity_rows(ROOT/'build/item-identity-megasheet.xlsx')
        p=self.source.profile(0x324C)
        row=pipeline.metadata(self.source,0x324C,p,identities[0x324C])
        self.assertEqual(row['action_sound'],1)
        changed=copy.copy(self.source);changed.data=bytearray(changed.data)
        at,_=changed.symbol('mRmTp_ftr_se_type');changed.data[at+row['runtime_index']]=3
        with self.assertRaisesRegex(ValueError,'action-sound category'):
            pipeline.metadata(changed,0x324C,p,identities[0x324C])
        with self.assertRaises(ValueError): self.source.pointers(self.source.size-2,4)

    def test_single_bed_category_discovers_models_without_waiving_acquisition(self):
        inventory=pipeline.scan(self.source,ROOT/'build/item-identity-megasheet.xlsx')
        for row in inventory['rows']:
            if row.get('reason')=='name/identity is ambiguous or unused':
                self.assertFalse(row['asset_ready'])
            if row.get('reason','').startswith('shared dummy profile:'):
                self.assertFalse(row['asset_ready'])
                index=1024+(int(row['item_id'],16)-0x3000)//4
                for (at,_),table in zip(self.source.names['furniture_quality'],self.source.quality):
                    self.assertEqual(table[at+index*4],self.source.symbol('iam_dummy')[0])
        beds=[r for r in inventory['rows'] if r.get('profile',{}).get('contact_action')==8]
        self.assertEqual(len(beds),4)
        self.assertEqual(sum(r['status']=='supported' for r in beds),2)
        for row in beds:
            self.assertTrue(row['asset_ready'])
            self.assertIn('single-bed',row['categories'])
            self.assertEqual(row['profile']['size_code'],1)
            if row['status']=='review': self.assertIn('acquisition needs an adapter',row['reason'])
        p=beds[0]['profile'];changed=copy.copy(self.source);changed.data=bytearray(changed.data)
        for contact in (3,32,255):
            changed.data[p['profile_offset']+44]=contact
            with self.assertRaisesRegex(ValueError,'contact/interaction'):
                changed.profile(int(beds[0]['item_id'],16))

    def test_square_collision_and_double_bed_categories_keep_complete_scalars(self):
        inventory=pipeline.scan(self.source,ROOT/'build/item-identity-megasheet.xlsx')
        double=[r for r in inventory['rows'] if r.get('profile',{}).get('contact_action')==16]
        self.assertEqual(len(double),3)
        for row in double:
            p=row['profile'];at=p['profile_offset']
            self.assertEqual(p['scalar_hex'],self.source.data[at+32:at+48].hex())
            self.assertEqual(p['size_code'],2)
            self.assertEqual(self.source.data[at+41],5)
            self.assertIn('double-bed',row['categories'])
            self.assertEqual(row['status'],'supported')
        p=double[0]['profile'];changed=copy.copy(self.source);changed.data=bytearray(changed.data)
        for collision in (3,4,6,255):
            changed.data[p['profile_offset']+41]=collision
            with self.assertRaisesRegex(ValueError,'scalar profile category'):
                changed.profile(int(double[0]['item_id'],16))

    def test_shared_collision_flag_and_placement_categories_preserve_unknowns_for_review(self):
        identities=pipeline.identity_rows(ROOT/'build/item-identity-megasheet.xlsx')
        profile=self.source.profile(0x30E8)
        self.assertEqual(profile['interaction_flags'],0x10)
        self.assertEqual(bytes.fromhex(profile['scalar_hex'])[-2:],bytes.fromhex('0010'))
        changed=copy.copy(self.source);changed.data=bytearray(changed.data)
        struct.pack_into('>H',changed.data,profile['profile_offset']+46,0x20)
        with self.assertRaisesRegex(ValueError,'contact/interaction'):
            changed.profile(0x30E8)
        changed=copy.copy(self.source);changed.data=bytearray(changed.data)
        at,_=changed.symbol('aMR_layer_set_info');changed.data[at+1082]=3
        with self.assertRaisesRegex(ValueError,'placement-layer category'):
            pipeline.metadata(changed,0x30E8,profile,identities[0x30E8])
        # Diary display models are not ordinary furniture: recognising their
        # collision flag must not bypass the missing gameplay/acquisition route.
        with self.assertRaisesRegex(ValueError,'parent-item support'):
            pipeline.metadata(self.source,0x30FC,self.source.profile(0x30FC),identities[0x30FC])

    def test_indexed_static_callback_category_uses_every_actual_selector_row(self):
        source=self.source
        table,n=source.symbol('fNFL_model_data')
        pointers=data_pointers(source.rel,table,n)
        for selected in range(n//12):
            item=0x3378+selected*4
            descriptor,_,resources,_,models,_,_=pipeline.prepare(source,item)
            adapter=descriptor['callback_adapter']
            self.assertEqual(adapter['selected_index'],selected)
            self.assertEqual(adapter['first_runtime_index'],1246)
            self.assertEqual(adapter['table_pointers'],pointers)
            self.assertEqual(adapter['entries'],9)
            self.assertEqual(list(models),['opaque','opaque1'])
            for slot,layer in enumerate(models):
                self.assertEqual(models[layer]['donor_offset'],pointers[table+selected*12+slot*4])
            palette=next(r for r in resources if r['kind']=='palette')
            self.assertEqual(palette['donor_offset'],pointers[table+selected*12+8])
            self.assertEqual(descriptor['palette_bindings'],{0x08000000:palette['donor_offset']})
            self.assertEqual(descriptor['interaction_flags'],0x10)
        vtable,n=source.symbol('fNFL_func')
        self.assertEqual(data_pointers(source.rel,vtable,n,expected_section=1),
            {vtable+i*4:adapter['functions'][role]['offset']
             for i,role in enumerate(('create','move','draw','destroy'))})

    def test_callback_specialisation_rejects_changed_effects_dependencies_and_indices(self):
        source=self.source;profile=source.profile(0x3378);adapter=profile['callback_adapter']
        for role in ('create','move','draw','destroy'):
            changed=copy.copy(source);changed.rel=bytearray(source.rel)
            changed.rel[source.sections[1][0]+adapter['functions'][role]['offset']]^=1
            with self.subTest(role=role),self.assertRaisesRegex(ValueError,'custom callbacks'):
                changed.profile(0x3378)
        changed=copy.copy(source);changed.code_relocations=dict(source.code_relocations)
        changed.code_relocations[adapter['functions']['draw']['offset']+0x10]=(10,2,4,0x8009AECC)
        with self.assertRaisesRegex(ValueError,'changed draw dependencies'): changed.profile(0x3378)
        changed=copy.copy(source);changed.relocations=dict(source.relocations)
        at=adapter['vtable_offset']
        changed.relocations[at+16]=changed.relocations[at]
        with self.assertRaisesRegex(ValueError,'DMA callback'): changed.profile(0x3378)
        changed=copy.copy(source);changed.data=bytearray(source.data)
        changed.data[adapter['table_offset']]=1
        with self.assertRaises(ValueError): changed.profile(0x3378)
        for index in (1245,1255):
            with self.assertRaisesRegex(ValueError,'selector index escapes'):
                source.callback_models(profile['profile_offset'],index)

    def test_prepared_artwork_cannot_bypass_missing_gameplay_or_acquisition(self):
        path=os.environ.get('V3_FURNITURE_PREPARED_ART')
        if not path: self.skipTest('No optional prepared-asset batch supplied')
        art=Path(path).resolve();report=json.loads((art/'art.json').read_bytes())
        self.assertEqual(report['format'],'AFV3-AUTO-FURNITURE-PREPARED-ASSETS-1')
        self.assertFalse(report['runtime_installed'])
        worksheet=ROOT/'build/item-identity-megasheet.xlsx'
        with self.assertRaisesRegex(ValueError,'Unknown converter/source revision'):
            install.checked_assets(art,self.source,worksheet)
        identities=pipeline.identity_rows(worksheet,extra_items={int(r['item_id'],16) for r in report['objects']})
        for row in report['objects']:
            item=int(row['item_id'],16)
            self.assertEqual(row['profile'],json.loads(json.dumps(self.source.profile(item))))
            names=pipeline.name_metadata(self.source,item,identities[item])
            self.assertEqual({k:row[k] for k in names},names)
            if not row['import_ready']:
                with self.assertRaises(pipeline.ReviewRequired) as error:
                    pipeline.metadata(self.source,item,self.source.profile(item),identities[item])
                self.assertEqual(str(error.exception),row['pending_reason'])
            if 'room_alias' in row:
                alias=next(r for r in pipeline.room_aliases(self.source)['rows'] if r['display_item_id']==row['item_id'])
                self.assertEqual(row['room_alias'],alias)
            if row['profile'].get('callback_adapter',{}).get('category')=='indexed-model-sequence':
                native=install.profile(row,0x02500000)
                self.assertEqual(struct.unpack_from('>4I',native,16),tuple(
                    0x06000000+row['model_offsets'][label] if label in row['model_offsets'] else 0
                    for label in pipeline.LAYERS))
                self.assertEqual(native[32:48],bytes(16))
                self.assertEqual(native[-4:],bytes(4))
        self.check_complete_artwork(art,report)

    def test_shared_palette_runtime_with_prepared_source_objects_under_sanitizers(self):
        path=os.environ.get('V3_FURNITURE_PREPARED_ART')
        if not path:self.skipTest('No optional prepared-asset batch supplied')
        art=Path(path);report=json.loads((art/'art.json').read_bytes())
        rows=[r for r in report['objects'] if r['profile'].get('callback_adapter',{}).get('category')=='switch-palette-fade']
        if not rows:self.skipTest('No palette-fade category in prepared batch')
        with tempfile.TemporaryDirectory(prefix='v3-shared-palette-') as temporary:
            binary=Path(temporary)/'test'
            subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_furniture_palette_test.c'),'-o',str(binary)],check=True,capture_output=True)
            result=subprocess.run([str(binary),str(ROOT/'build/v3-camping-actor-art-01/tent-model.n64obj.bin'),
                *(str(art/r['object_file']) for r in rows)],check=True,capture_output=True,text=True,timeout=20)
            self.assertIn('retained frames, bounds, and actor guards pass',result.stdout)

    def test_complete_texels_vertices_and_compiled_triangles_for_entire_batch(self):
        self.check_complete_artwork(self.art,self.report)

    def test_generated_sequence_targets_every_complete_compiled_model_in_order(self):
        for row in self.report['objects']:
            linked=row.get('draw_sequence')
            if not linked:continue
            asset=(self.art/row['object_file']).read_bytes()
            order=row['profile']['callback_adapter']['model_order']
            words=list(struct.iter_unpack('>II',asset[linked['native_offset']:linked['native_offset']+linked['bytes']]))
            self.assertEqual(words,[(0xDE000000,0x06000000+row['model_offsets'][label]) for label in order]+[(0xDF000000,0)])
            self.assertEqual(linked['model_offsets'],row['model_offsets'])
            for label in order:
                model=next(m for m in row['models'] if m['layer']==label)
                self.assertEqual(model['native_offset'],row['model_offsets'][label])
                self.assertLessEqual(model['native_offset']+model['bytes'],linked['native_offset'])
            native=install.profile(row,0x02500000)
            self.assertEqual(struct.unpack_from('>4I',native,16),(0x06000000+linked['native_offset'],0,0,0))
            self.assertEqual(native[32:48],bytes(16));self.assertEqual(native[-4:],bytes(4))

    def check_complete_artwork(self,art,report,prepare=None):
        prepare = prepare or (lambda row:pipeline.prepare(self.source,int(row['item_id'],16)))
        for row in report['objects']:
            asset=(art/row['object_file']).read_bytes()
            descriptor,body,resources,offsets,models,_,sections=prepare(row)
            self.assertEqual(asset[:len(body)],body)
            self.assertEqual(sha256(asset),row['object_sha256'])
            vertex=next(r for r in resources if r['kind']=='vertices')
            for r in resources:
                at,n,dst=r['donor_offset'],r['bytes'],r['native_offset']
                donor,native=self.source.data[at:at+n],asset[dst:dst+n]
                if r['kind']=='texture':
                    for y in range(r['height']):
                        for x in range(r['width']):
                            flat=y*r['width']+x
                            if r['format']=='RGBA16':
                                gx=((y//4)*(r['width']//4)+x//4)*16+y%4*4+x%4
                                value=struct.unpack_from('>H',donor,gx*2)[0]
                                if value&0x8000:expected=((value&0x7FFF)<<1)|1
                                else:
                                    alpha=value>>12;self.assertIn(alpha,(0,7))
                                    red,green,blue=((value>>s&15)*17>>3 for s in (8,4,0))
                                    expected=red<<11|green<<6|blue<<1|bool(alpha)
                                self.assertEqual(struct.unpack_from('>H',native,flat*2)[0],expected)
                            elif r['format']=='IA8':
                                gx=((y//4)*(r['width']//8)+x//8)*32+y%4*8+x%8
                                self.assertEqual(native[flat],(donor[gx]&15)<<4|donor[gx]>>4)
                            else:
                                gx=((y//8)*(r['width']//8)+x//8)*64+y%8*8+x%8
                                self.assertEqual(donor[gx//2]>>(4 if gx%2==0 else 0)&15,
                                    native[flat//2]>>(4 if flat%2==0 else 0)&15)
                elif r['kind']=='vertices':
                    for start in range(0,n,16):
                        self.assertEqual(native[start:start+6],donor[start:start+6])
                        self.assertEqual(native[start+6:start+8],bytes(2))
                        self.assertEqual(native[start+8:start+16],donor[start+8:start+16])
            for model in row['models']:
                self.assertEqual(model.get('source_parts'),models[model['layer']].get('source_parts'))
                start,n=model['native_offset'],model['bytes']; faces=[]; state=[]; loads=[]
                self.assertEqual(n,dict(sections)[model['layer']])
                cache=[None]*32;matrices=[];matrix=-1;posed_cache=[None]*32;posed_faces=[]
                inherited_vertices = descriptor.get('render_context', {}).get('external_vertices')
                if inherited_vertices:
                    count = inherited_vertices[2]//16
                    cache[:count] = range(count)
                    posed_cache[:count] = [(i, -1) for i in range(count)]
                for a,b in struct.iter_unpack('>II',asset[start:start+n]):
                    op=a>>24
                    self.assertNotIn(op,(0x0A,0xD2,0xDE))
                    if op in (0xFC,0xE2,0xFA,0xFB,0xD9):state.append((a,b))
                    if op==0xDA:
                        self.assertEqual(a,0xDA380003);matrices.append((a,b));matrix=(b&0xFFFFFF)//64
                    if op==0xFD:
                        self.assertIn(b>>24,(6,8));loads.append(b)
                    if op==1:
                        self.assertEqual(b>>24,6);count=a>>12&255
                        first=(b-0x06000000-vertex['native_offset'])//16
                        slot=(a&255)//2-count
                        self.assertTrue(0<=slot<=32-count)
                        self.assertGreaterEqual(first,0)
                        self.assertLessEqual(first+count,vertex['bytes']//16)
                        cache[slot:slot+count]=range(first,first+count)
                        posed_cache[slot:slot+count]=[(i,matrix) for i in range(first,first+count)]
                    if op in (5,6):
                        for word in ((a,b) if op==6 else (a,)):
                            indices=tuple(word>>shift&255 for shift in (16,8,0))
                            self.assertTrue(all(i%2==0 and i//2<32 and cache[i//2] is not None for i in indices))
                            faces.append(tuple(cache[i//2] for i in indices))
                            posed_faces.append(tuple(posed_cache[i//2] for i in indices))
                donor=models[model['layer']]['rows']
                expected_faces=[];expected_cache=[None]*32;matrix=-1
                if inherited_vertices:
                    expected_cache[:inherited_vertices[2]//16] = [(i, -1) for i in range(inherited_vertices[2]//16)]
                for command in donor:
                    if command['opcode']==0xDA:matrix=command['joint_matrix']
                    if command['opcode']==1:
                        slot=command.get('vertex_slot',0);count=command['count'];first=command['first_vertex']
                        expected_cache[slot:slot+count]=[(i,matrix) for i in range(first,first+count)]
                    expected_faces.extend(tuple(expected_cache[v] for v in face) for face in command.get('triangles',[]))
                self.assertEqual(posed_faces,expected_faces)
                self.assertEqual(faces,[t for r in donor for t in r.get('global_triangles',[])])
                self.assertEqual(matrices,[r['words'] for r in donor if r['opcode']==0xDA])
                self.assertEqual(state,[r['words'] for r in donor if r['opcode'] in (0xFC,0xE2,0xFA,0xFB,0xD9)])
                self.assertEqual(loads,[r['dynamic_palette'] if 'dynamic_palette' in r else 0x06000000+offsets[r['target']]
                                       for r in donor if r['opcode'] in (0xF0,0xFD)])
                self.assertEqual(asset[start+n-8:start+n],struct.pack('>II',0xDF000000,0))
                # Independently decode the native tile descriptors, not just
                # the generated C, including the new 8-bit line stride/LUT.
                words=list(struct.iter_unpack('>II',asset[start:start+n]))
                expected=[];luts=[];last=None
                for command in donor:
                    if command['opcode'] not in (0xFD,0xD2):continue
                    ia8=bool(command.get('ia8'));rgba16=bool(command.get('rgba16'))
                    intensity=bool(command.get('intensity'));w,h=command['shape']
                    direct=ia8 or rgba16 or intensity
                    wraps=tuple({0:2,1:0,2:1}[v] for v in command.get('wrap_modes',(0,0)))
                    shifts=command.get('tile_shifts',(0,0))
                    expected.append((0 if rgba16 else 3 if ia8 else 4 if intensity else 2,
                                     2 if rgba16 else 1 if ia8 else 0,
                                     w//4 if rgba16 else w//8 if ia8 else (w+15)//16,0,
                                     0 if direct else command.get('palette_slot',15),*wraps,*shifts))
                    if command['opcode']==0xFD and direct!=last:
                        luts.append((0xE3001001,0 if direct else 0x8000));last=direct
                actual=[(a>>21&7,a>>19&3,a>>9&511,a&511,b>>20&15,
                         b>>8&3,b>>18&3,b&15,b>>10&15)
                        for a,b in words if a>>24==0xF5 and b>>24&7==0]
                self.assertEqual(actual,expected)
                self.assertEqual([w for w in words if w[0]==0xE3001001],luts)

    def test_automatic_text_credits_are_in_the_single_catalogue(self):
        self.assertEqual(install.provenance_patch(self.report['objects']),'')
        entries={r['id']:r for r in json.loads((ROOT/'translations/provenance.json').read_bytes())['entries']}
        for row in self.report['objects']:
            entry=entries[row['id']+'/name']['locales']['en']
            self.assertEqual(entry['text'],row['name']);self.assertEqual(entry['credit'],'official')
            self.assertEqual(entry['source']['index'],row['name_source_index'])

    def test_compiled_material_formats_scales_and_tile_shifts_match_the_source(self):
        batches=[(self.art,self.report)]
        if path:=os.environ.get('V3_FURNITURE_PREPARED_ART'):
            art=Path(path).resolve();batches.append((art,json.loads((art/'art.json').read_bytes())))
        for art,report in batches:
            for row in report['objects']:
                asset=(art/row['object_file']).read_bytes()
                _,_,_,_,models,_,_=pipeline.prepare(self.source,int(row['item_id'],16))
                for model in row['models']:
                    at,n=model['native_offset'],model['bytes']
                    words=list(struct.iter_unpack('>II',asset[at:at+n]))
                    source=models[model['layer']]['rows']
                    scales=[(0xD7000002,r['words'][1] or 0xFFFFFFFF) for r in source if r['opcode']==0xD7]
                    self.assertEqual([w for w in words if w[0]>>24==0xD7],scales)
                    expected=[];luts=[];last=None
                    for r in source:
                        if r['opcode'] not in (0xFD,0xD2):continue
                        intensity=bool(r.get('intensity'));rgba16=bool(r.get('rgba16'));w,h=r['shape']
                        direct=intensity or rgba16
                        wraps=tuple({0:2,1:0,2:1}[x] for x in r['wrap_modes'])
                        shifts=r.get('tile_shifts',(0,0))
                        expected.append((0 if rgba16 else 4 if intensity else 2,2 if rgba16 else 0,
                                         w//4 if rgba16 else (w+15)//16,0,
                                         0 if direct else 15,*wraps,*shifts))
                        if r['opcode']==0xFD and direct!=last:
                            luts.append((0xE3001001,0 if direct else 0x8000));last=direct
                    actual=[(a>>21&7,a>>19&3,a>>9&511,a&511,b>>20&15,
                             b>>8&3,b>>18&3,b&15,b>>10&15)
                            for a,b in words if a>>24==0xF5 and b>>24&7==0]
                    self.assertEqual(actual,expected)
                    self.assertEqual([w for w in words if w[0]==0xE3001001],luts)


class CurrentCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=composer.inputs();cls.files=by_vrom(cls.image)
        cls.blob=cls.files[install.BLOB].extract(cls.image)
        cls.rows=cls.report['automatic_furniture']['imports']
        pin=cls.report['automatic_furniture']['base'];directory=ROOT/pin['directory']
        cls.base=(directory/'animal-forest-v3-asset-loader.z64').read_bytes()
        raw=(directory/'build.json').read_bytes()
        if sha256(cls.base)!=pin['rom_sha256'] or sha256(raw)!=pin['report_sha256']:
            raise ValueError('Changed current batch prerequisite')
        cls.old=by_vrom(cls.base);cls.prior=json.loads(raw)

    def test_all_batch_assets_and_canonical_profiles_installed_without_heap_growth(self):
        for row in self.rows:
            item=int(row['item_id'],16);i=install.slot(item);at=int(row['object_vrom'],16)-install.BLOB
            self.assertEqual(sha256(self.blob[at:at+row['object_bytes']]),row['object_sha256'])
            native=install.profile(row,int(row['object_vrom'],16))
            self.assertEqual(self.blob[install.ROWS+i*80:install.ROWS+(i+1)*80],
                struct.pack('>HHI',1024+i,item,1)+native+bytes(4))
            record=self.blob[install.ITEMS+i*32:install.ITEMS+(i+1)*32]
            self.assertEqual(record[8:24],row['name'].encode().ljust(16,b' '))
            self.assertEqual(record[24],install.order_mask(install.catalogue_record(row)))
            self.assertEqual(record[25],row['action_sound'])
            self.assertEqual(record[27],row.get('reward_route',0))
        self.assertEqual(self.report['furniture']['bank_pool'],self.prior['furniture']['bank_pool'])
        expanded=self.report['furniture']['expanded_tables'];prior=self.prior['furniture']['expanded_tables']
        if 'furniture_palette_fade' not in self.report:
            self.assertEqual(expanded,prior)
        else:
            self.assertEqual({k:v for k,v in expanded.items() if k not in ('expanded_code','public_entries')},
                             {k:v for k,v in prior.items() if k not in ('expanded_code','public_entries')})
            code=expanded['expanded_code']
            self.assertEqual(sha256(self.blob[0x5800:0x5800+code['bytes']]),code['sha256'])
            for row in expanded['public_entries']:
                at=row['entry']-0x80460000
                self.assertEqual(self.blob[at:at+8],bytes.fromhex(row['after']))
        self.assertEqual(self.report['save_runtime']['code'],self.prior['save_runtime']['code'])

    def test_reused_terminal_resources_and_retained_objects(self):
        old_blob=self.old[install.BLOB].extract(self.base)
        retained,receipt=install.reuse_resource_tail(self.base,self.prior,old_blob)
        self.assertEqual(receipt,self.report['automatic_furniture']['resource_tail_reuse'])
        self.assertGreater(receipt['reused_bytes'],0)
        self.assertEqual(old_blob[:receipt['blob_offset']],retained)
        self.assertEqual(int(self.rows[0]['object_vrom'],16)-install.BLOB,receipt['blob_offset'])
        for row in self.prior['furniture']['imports']+[self.prior['speed_bag']]:
            at=int(row['object_vrom'],16)-install.BLOB;n=row['object_bytes']
            self.assertLessEqual(at+n,len(retained))
            self.assertEqual(self.blob[at:at+n],old_blob[at:at+n])
        # Reuse is repeatable from the newly built receipt; no growing stack
        # of catalogue/shop copies is needed on the next import.
        next_blob,next_receipt=install.reuse_resource_tail(self.image,self.report,self.blob)
        self.assertEqual(next_receipt['blob_offset'],len(next_blob))
        self.assertEqual(len(self.blob)-len(next_blob),next_receipt['reused_bytes'])

    def test_resource_tail_rejects_bad_receipts_contents_and_retained_profile_overlap(self):
        old_blob=self.old[install.BLOB].extract(self.base)
        changed=copy.deepcopy(self.prior)
        changed['automatic_furniture']['resource_moves'][0]['physical']+=16
        with self.assertRaisesRegex(ValueError,'extent, mapping, padding, or contents'):
            install.reuse_resource_tail(self.base,changed,old_blob)
        changed=copy.deepcopy(self.prior)
        changed['automatic_furniture']['resource_moves'].pop()
        with self.assertRaisesRegex(ValueError,'tail inventory'):
            install.reuse_resource_tail(self.base,changed,old_blob)
        blob=bytearray(old_blob);blob[-1]^=1;changed=copy.deepcopy(self.prior)
        changed['blob_sha256']=sha256(blob)
        with self.assertRaisesRegex(ValueError,'extent, mapping, padding, or contents'):
            install.reuse_resource_tail(self.base,changed,blob)
        first=min(r['blob_offset'] for r in self.prior['automatic_furniture']['resource_moves'])
        blob=bytearray(old_blob);struct.pack_into('>II',blob,install.ROWS+8,install.BLOB+first,install.BLOB+first+16)
        changed=copy.deepcopy(self.prior);changed['blob_sha256']=sha256(blob)
        with self.assertRaisesRegex(ValueError,'overlaps retained furniture'):
            install.reuse_resource_tail(self.base,changed,blob)

    def test_bed_category_uses_checked_existing_engine_and_rejects_changed_bindings(self):
        from v3_furniture_behaviours import contact_contract
        rows=self.report['furniture']['imports']+[self.report['speed_bag']]
        current=contact_contract(self.image,self.report,self.blob,rows)
        self.assertEqual(current,self.report['furniture_behaviours'].get('contacts'))
        if current:
            self.assertEqual(current['added_runtime_bytes'],0)
            changed=copy.deepcopy(self.report)
            changed['furniture']['expanded_tables']['profile_table_ram']='80465800'
            with self.assertRaisesRegex(ValueError,'complete expanded profile table'):
                contact_contract(self.image,changed,self.blob,rows)
            image=bytearray(self.image)
            image[self.files[0x82D7F0].pstart+0x80940518-0x80936710]^=1
            with self.assertRaisesRegex(ValueError,'native bed/contact engine'):
                contact_contract(bytes(image),self.report,self.blob,rows)

    def test_four_cell_category_requires_actual_extended_native_reader(self):
        from v3_furniture_behaviours import four_cell_contract
        source=pipeline.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        rows=self.report['furniture']['imports']+[self.report['speed_bag']]
        current=four_cell_contract(original,self.report,self.blob,rows,source)
        self.assertEqual(current,self.report['furniture_behaviours']['four_cells'])
        self.assertEqual(current['added_runtime_bytes'],0)
        changed=bytearray(self.blob);changed[install.PACKAGE+0x80483000-install.PACKAGE_RAM]^=1
        with self.assertRaisesRegex(ValueError,'complete native item readers'):
            four_cell_contract(original,self.report,changed,rows,source)

    def test_catalogue_and_stock_keep_prior_members_and_all_new_category_records(self):
        def lists(image,files,report):
            data=files[shops.VROM].extract(image);result=[]
            for ptr in struct.unpack_from('>11I',data,report['shops']['table_offset']):
                at=ptr&0xFFFFFF;items=[]
                while (item:=struct.unpack_from('>H',data,at)[0]):items.append(item);at+=2
                result.append(items)
            return result
        new=lists(self.image,self.files,self.report);old=lists(self.base,self.old,self.prior)
        ids={int(r['item_id'],16) for r in self.rows}
        self.assertEqual([[i for i in group if i not in ids] for group in new],old)
        for row in self.rows:
            item=int(row['item_id'],16)
            if row.get('reward_route'):
                self.assertFalse(any(item in group for group in new))
            else:self.assertIn(item,new[row['stock_group']])
        cat=self.report['catalogue']
        self.assertEqual(cat['total_rows'],self.prior['catalogue']['total_rows']+len(self.rows))
        self.assertLessEqual(cat['conservative_pool_required'],cat['pool_reserved'])
        self.assertEqual([r['donor_position'] for r in cat['imports']],sorted(r['donor_position'] for r in cat['imports']))
        for row in cat['imports']:
            self.assertEqual(self.blob[install.ITEMS+install.slot(int(row['item_id'],16))*32+24],install.order_mask(row))

    def test_only_new_scoring_records_change(self):
        for key,tool,width in (('hra',hra,4),('feng_shui',feng,2)):
            expected=bytearray(self.old[tool.NEW_VROM].extract(self.base))
            table=self.report[key]['metadata_address']-tool.RAM
            for row in self.rows:
                at=table+row['runtime_index']*width
                expected[at:at+width]=bytes.fromhex(row['native_hra_hex'] if width==4 else row['feng_hex'])
            self.assertEqual(self.files[tool.NEW_VROM].extract(self.image),expected)

    def test_reward_scoring_aliases_keep_actual_weights_and_reject_changed_category(self):
        aliases=[r for r in self.rows if r.get('donor_birth_category',r['birth_category'])!=r['birth_category']]
        if not aliases:self.skipTest('Current batch needs no scoring aliases')
        source=pipeline.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        data=self.files[hra.NEW_VROM].extract(self.image);ext=self.report['hra']['birth_extension']
        for row in aliases:
            donor=struct.unpack_from('>I',source.raw('mMkRm_birth_point_table'),row['donor_birth_category']*4)[0]
            native=struct.unpack_from('>I',data,ext['points_address']-hra.RAM+row['birth_category']*4)[0]
            self.assertEqual(native,donor);self.assertEqual(native,412)
            receipt=next(r for r in self.report['hra']['automatic_scoring_aliases'] if r['item_id']==row['item_id'])
            self.assertEqual(receipt['donor_category'],row['donor_birth_category'])
            self.assertFalse(receipt['acquisition_category_changed'])
        changed=copy.deepcopy(aliases[0]);changed['donor_birth_category']=34
        with self.assertRaisesRegex(ValueError,'scoring equivalence'):
            install.scoring(self.base,self.prior,[changed],source)

    def test_shared_camping_suffix_retains_native_prefix_and_fixed_allocations(self):
        from v3_camper_trade import VROM,RELOC,RAM,SIZE,QUEST,QUEST_RELOC
        current=self.report['camper_trade'];previous=self.prior['camper_trade']
        if not current.get('shared_reward_categories'):self.skipTest('No shared camping suffix')
        self.assertEqual(current['shared_reward_categories'],[19,23])
        before=self.old[VROM].extract(self.base);after=bytearray(self.files[VROM].extract(self.image))
        self.assertEqual(len(after),len(before));self.assertEqual(self.files[RELOC].size,self.old[RELOC].size)
        for new,old in zip(current['hooks'],previous['hooks']):
            at=new['address']-RAM;self.assertEqual(after[at:at+8].hex(),new['after'])
            after[at:at+8]=bytes.fromhex(old['after'])
        self.assertEqual(after[:SIZE],before[:SIZE])
        self.assertEqual(self.files[QUEST].extract(self.image),self.old[QUEST].extract(self.base))
        self.assertEqual(self.files[QUEST_RELOC].extract(self.image),self.old[QUEST_RELOC].extract(self.base))
        self.assertEqual(after[SIZE+current['code']['bytes']:],bytes(current['unused_suffix_bytes']))
        self.assertEqual(current['reward_count_entry'],self.report['furniture_rewards']['code']['symbols']['af_v3_furniture_reward_count'])

    def test_reward_binding_preserves_complete_owner_and_reuses_reservation(self):
        import v3_furniture_rewards as rewards
        current=self.report.get('furniture_rewards')
        if not current:self.skipTest('Current batch has no optional NPC rewards')
        begin=install.PACKAGE+rewards.FIRST-install.PACKAGE_RAM
        end=install.PACKAGE+rewards.END-install.PACKAGE_RAM
        self.assertEqual(self.blob[begin:begin+16],rewards.GUARD)
        self.assertEqual(self.blob[end-16:end],rewards.GUARD)
        self.assertEqual(sha256(self.blob[begin:end]),current['reservation_sha256'])
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes();native=by_vrom(original)
        for route in current['routes']:
            expected=bytearray(native[route['vrom']].extract(original))
            for patch in route['patches']:
                pos=patch['address']-route['ram']
                self.assertEqual(struct.unpack_from('>I',expected,pos)[0],patch['before'])
                struct.pack_into('>I',expected,pos,patch['after'])
            self.assertEqual(self.files[route['vrom']].extract(self.image),expected)
            self.assertFalse(self.files[route['vrom']].pend)
            self.assertEqual(self.files[route['reloc']].extract(self.image),native[route['reloc']].extract(original))
        for row in current['imports']:
            at=install.ITEMS+install.slot(int(row['item_id'],16))*32
            self.assertEqual(self.blob[at+24],0)
            self.assertEqual(self.blob[at+27],row['route'])
        source=pipeline.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        blob=bytearray(self.blob)
        with tempfile.TemporaryDirectory(prefix='reward-reuse-',dir=ROOT/'build') as temporary:
            changes,again=rewards.install(original,self.image,self.report,blob,
                self.report['furniture']['imports']+[self.report['speed_bag']],source,Path(temporary))
        self.assertEqual(blob,self.blob)
        self.assertEqual(again['reservation_sha256'],current['reservation_sha256'])
        for vrom,data in changes.items():self.assertEqual(data,self.files[vrom].extract(self.image))

    def test_current_rom_checksums_directory_and_prior_runtime_preserved(self):
        self.assertEqual(set(self.files),set(self.old));self.assertEqual(self.image[DMA_END-16:DMA_END],bytes(16))
        self.assertEqual(struct.unpack_from('>II',self.image,16),n64_checksum(self.image))
        self.assertEqual(struct.unpack_from('>4I',self.blob,0xF0),
            (install.BLOB+install.PACKAGE,install.PACKAGE_SIZE,
             zlib.crc32(self.blob[install.PACKAGE:install.PACKAGE+install.PACKAGE_SIZE]),install.PACKAGE_RAM))
        before=self.old[install.BLOB].extract(self.base)
        expected=bytearray(before)
        if 'furniture_palette_fade' in self.report:
            helper=self.report['furniture']['expanded_tables']['expanded_code']
            self.assertEqual(sha256(self.blob[0x5800:0x5800+helper['bytes']]),helper['sha256'])
            self.assertEqual(self.blob[0x5800+helper['bytes']:0x6000],bytes(0x800-helper['bytes']))
            expected[0x5800:0x6000]=self.blob[0x5800:0x6000]
            for row in self.report['furniture']['expanded_tables']['public_entries']:
                at=row['entry']-0x80460000
                self.assertEqual(expected[at:at+8],bytes.fromhex(row['before']))
                expected[at:at+8]=bytes.fromhex(row['after'])
        self.assertEqual(self.blob[0x100:0xC000],expected[0x100:0xC000])
        self.assertEqual(self.blob[0xE0:0xF0],before[0xE0:0xF0])
        code=bytearray(self.files[CODE_VROM].extract(self.image));native=self.old[CODE_VROM].extract(self.base)
        at=shops.DESCRIPTOR-CODE_RAM;code[at:at+12]=native[at:at+12]
        hook=self.report['furniture_behaviours']['hook'];at=hook['address']-CODE_RAM
        self.assertEqual(code[at:at+8].hex(),hook['after']);code[at:at+8]=native[at:at+8]
        self.assertEqual(code,native)

    def test_shared_palette_code_layout_and_both_complete_callback_tables(self):
        current=self.report.get('furniture_palette_fade')
        if not current:self.skipTest('Current build has no shared palette category')
        from v3_furniture_palette import RAM,LIMIT,VTABLE,LEGACY_VTABLE,LEGACY_LAYOUT
        at=install.PACKAGE+RAM-install.PACKAGE_RAM;resident=self.blob[at:at+LIMIT-RAM]
        self.assertEqual(sha256(resident),current['resident_sha256'])
        linked=bytearray(resident);symbols=current['code']['symbols']
        for address in (VTABLE,LEGACY_VTABLE):
            table=resident[address-RAM:address-RAM+20]
            self.assertEqual(table.hex(),current['vtables'][f'{address:08X}'])
            entries=[symbols['af_v3_tent_model_'+r] for r in ('ct','mv','dw','dt')]+[0]
            if address==VTABLE:entries[2]=symbols['af_v3_palette_fade_dw']
            self.assertEqual(struct.unpack('>5I',table),tuple(entries))
            linked[address-RAM:address-RAM+20]=bytes(20)
        self.assertEqual(resident[LEGACY_LAYOUT-RAM:LEGACY_LAYOUT-RAM+32].hex(),current['legacy_layout_hex'])
        linked[LEGACY_LAYOUT-RAM:LEGACY_LAYOUT-RAM+32]=bytes(32)
        self.assertEqual(sha256(linked[:current['code']['bytes']]),current['code']['sha256'])
        self.assertEqual(linked[current['code']['bytes']:],bytes(LIMIT-RAM-current['code']['bytes']))
        self.assertEqual(self.report['tent_model']['code']['sha256'],sha256(resident[:current['code']['bytes']]))
        self.assertEqual(current['additional_resident_bytes'],0)
        self.assertEqual(current['heap_bytes'],0)

    def test_shared_sound_code_metadata_original_body_and_fire_remain_intact(self):
        from v3_furniture_behaviours import RAM,LIMIT,ENTRY,END,audio_contract
        current=self.report['furniture_behaviours'];at=install.PACKAGE+RAM-install.PACKAGE_RAM
        self.assertEqual(sha256(self.blob[at:at+current['code']['bytes']]),current['code']['sha256'])
        self.assertEqual(self.blob[at+current['code']['bytes']:install.PACKAGE+LIMIT-install.PACKAGE_RAM],
            bytes(LIMIT-RAM-current['code']['bytes']))
        code=self.files[CODE_VROM].extract(self.image);before=self.old[CODE_VROM].extract(self.base)
        self.assertEqual(code[ENTRY-CODE_RAM+8:END-CODE_RAM],before[ENTRY-CODE_RAM+8:END-CODE_RAM])
        source=pipeline.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        for row in current['imports']:
            self.assertEqual(self.blob[install.ITEMS+install.slot(int(row['item_id'],16))*32+25],
                source.raw('mRmTp_ftr_se_type')[row['runtime_index']])
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(audio_contract(original,self.image,self.report,source),current['donor'])
        fire=self.report['fire']['code'];at=install.PACKAGE+0x80483800-install.PACKAGE_RAM
        self.assertEqual(sha256(self.blob[at:at+fire['bytes']]),fire['sha256'])

    def test_complete_placement_table_bindings_and_unrelated_owner_bytes(self):
        import v3_furniture_placement as placement
        from npc_mail_show import relocate_verified_data
        from types import SimpleNamespace
        source=pipeline.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        row=self.report['furniture_placement'];at=install.PACKAGE+placement.TABLE-install.PACKAGE_RAM
        table=self.blob[at:at+placement.CAPACITY]
        self.assertEqual(sha256(table),row['table_sha256'])
        self.assertEqual(sha256(table[:947]),placement.NATIVE_SHA)
        for item in row['imports']:
            self.assertEqual(table[item['runtime_index']],source.raw('aMR_layer_set_info')[item['source_index']])
        start=install.PACKAGE+placement.FIRST-install.PACKAGE_RAM
        end=install.PACKAGE+placement.END-install.PACKAGE_RAM
        self.assertEqual(self.blob[start:start+16],placement.GUARD)
        self.assertEqual(self.blob[end-16:end],placement.GUARD)
        self.assertEqual(self.blob[at+placement.CAPACITY:end-16],bytes(end-16-at-placement.CAPACITY))
        before=self.old[placement.VROM].extract(self.base)
        changed=self.files[placement.VROM].extract(self.image);expected=bytearray(before)
        for patch in row['patches']:struct.pack_into('>I',expected,patch['address']-placement.RAM,patch['after'])
        self.assertEqual(changed,expected)
        relocation=self.files[placement.RELOC].extract(self.image)
        pairs,_,locations=placement.references(changed,relocation,placement.NATIVE_TABLE)
        self.assertEqual(pairs,());self.assertFalse(locations&{p['address']-placement.RAM for p in row['patches']})
        old_reloc=self.old[placement.RELOC].extract(self.base)
        new_spec=SimpleNamespace(ram=placement.RAM,resident_bytes=placement.RESIDENT,sections=struct.unpack_from('>5I',relocation))
        old_spec=SimpleNamespace(ram=placement.RAM,resident_bytes=placement.RESIDENT,sections=struct.unpack_from('>5I',old_reloc))
        # The sole effect after real owner relocation is the five table pointers.
        for destination in (0x801A0010,0x803D0010):
            old=bytearray(relocate_verified_data(old_spec,before,old_reloc,destination))
            new=relocate_verified_data(new_spec,changed,relocation,destination)
            for patch in row['patches']:
                pos=patch['address']-placement.RAM;old[pos:pos+4]=new[pos:pos+4]
            self.assertEqual(old,new)
        # A later import batch reuses the same reservation without new patches.
        blob=bytearray(self.blob)
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        changes,again=placement.install(original,self.image,self.report,blob,
            self.report['furniture']['imports']+[self.report['speed_bag']],source)
        self.assertEqual(blob,self.blob);self.assertEqual(again,row)
        self.assertEqual(changes[placement.VROM],changed);self.assertEqual(changes[placement.RELOC],relocation)

    def test_shared_preview_table_selectors_guards_and_repeat_batch(self):
        source=pipeline.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        row=self.report['catalogue_preview_records']
        start=install.PACKAGE+catalogue.PREVIEW_FIRST-install.PACKAGE_RAM
        at=install.PACKAGE+catalogue.PREVIEW_TABLE-install.PACKAGE_RAM
        end=install.PACKAGE+catalogue.PREVIEW_END-install.PACKAGE_RAM
        draw=source.raw('furniture_draw_data$436')
        self.assertEqual(self.blob[at:at+len(draw)],draw)
        self.assertEqual(self.blob[start:start+16],catalogue.PREVIEW_GUARD)
        self.assertEqual(self.blob[end-16:end],catalogue.PREVIEW_GUARD)
        self.assertEqual(sha256(self.blob[start:end]),row['reservation_sha256'])
        for r in row['imports']:
            pos=install.ITEMS+install.slot(int(r['item_id'],16))*32
            self.assertEqual(self.blob[pos+26],r['mode']+1)
            self.assertEqual(self.blob[pos+28:pos+32],bytes(4))
            self.assertEqual(r['scalar_hex'],draw[r['mode']*8:r['mode']*8+8].hex())
        blob=bytearray(self.blob)
        again=catalogue.install_preview_records(blob,self.report,source,copy.deepcopy(self.report['catalogue']['imports']))
        self.assertEqual(blob,self.blob);self.assertEqual(again,row)
        blob[start]^=1
        with self.assertRaisesRegex(ValueError,'Changed installed'):
            catalogue.install_preview_records(blob,self.report,source,copy.deepcopy(self.report['catalogue']['imports']))

    def test_batch_selection_is_identity_based_and_removes_disabled_scores(self):
        cat=composer.catalogue(self.image,self.report);keys=[r['id'] for r in self.rows]
        choice=composer.resolve(cat,keys[::3])
        self.assertEqual(choice,composer.resolve(cat,list(reversed(keys[::3]))))
        image,_,blob=composer.compose(self.image,self.report,cat,choice)
        score=by_vrom(image)[hra.NEW_VROM].extract(image);table=self.report['hra']['metadata_address']-hra.RAM
        for row in self.rows:
            enabled=row['id'] in choice['enabled'];i=install.slot(int(row['item_id'],16))
            self.assertEqual(struct.unpack_from('>I',blob,install.ROWS+i*80+4)[0],enabled)
            at=table+row['runtime_index']*4
            self.assertEqual(score[at:at+4],bytes.fromhex(row['native_hra_hex'] if enabled else 'fc000000'))


if __name__=='__main__':unittest.main()
