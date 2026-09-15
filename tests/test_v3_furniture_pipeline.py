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
    def test_constant_palette_binding_preserves_commands_and_rejects_ambiguous_dependencies(self):
        raw,pointers=fixture();raw=bytearray(raw)
        struct.pack_into('>I',raw,0x1C,0x08000000)
        pointers.pop(0x11C)
        def parse(binding, fixups=pointers):
            return parse_model(raw,0x100,fixups,(0x500,),{0x600:(32,32)},0x1000,48,
                               static_ci4=True,palette_bindings=binding)
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
                rows=parse_model(changed,0x100,pointers,(0x500,),{0x600:(32,32)},0x1000,48,static_ci4=True)
                self.assertIn((0xFA000080,0x123456FF),[r['words'] for r in rows])
                source,_=command_source({'opaque':{'rows':rows}},{0x500:0,0x600:32,0x1000:544})
                self.assertIn('gsSPVertex',source)
        for value in (0xD2F0FC00,0xD2F0F300,0xD2F0F001):
            changed=bytearray(raw);struct.pack_into('>I',changed,0x28,value)
            with self.assertRaises(ValueError):
                parse_model(changed,0x100,pointers,(0x500,),{0x600:(32,32)},0x1000,48,static_ci4=True)

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
        with self.assertRaisesRegex(ValueError,'acquisition needs an adapter'):
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
        identities=pipeline.identity_rows(worksheet)
        for row in report['objects']:
            item=int(row['item_id'],16)
            self.assertEqual(row['profile'],json.loads(json.dumps(self.source.profile(item))))
            names=pipeline.name_metadata(self.source,item,identities[item])
            self.assertEqual({k:row[k] for k in names},names)
            if not row['import_ready']:
                with self.assertRaises(pipeline.ReviewRequired) as error:
                    pipeline.metadata(self.source,item,self.source.profile(item),identities[item])
                self.assertEqual(str(error.exception),row['pending_reason'])
        self.check_complete_artwork(art,report)

    def test_complete_texels_vertices_and_compiled_triangles_for_entire_batch(self):
        self.check_complete_artwork(self.art,self.report)

    def check_complete_artwork(self,art,report):
        for row in report['objects']:
            asset=(art/row['object_file']).read_bytes()
            descriptor,body,resources,offsets,models,_,sections=pipeline.prepare(self.source,int(row['item_id'],16))
            self.assertEqual(asset[:len(body)],body)
            self.assertEqual(sha256(asset),row['object_sha256'])
            vertex=next(r for r in resources if r['kind']=='vertices')
            for r in resources:
                at,n,dst=r['donor_offset'],r['bytes'],r['native_offset']
                donor,native=self.source.data[at:at+n],asset[dst:dst+n]
                if r['kind']=='texture':
                    for y in range(r['height']):
                        for x in range(r['width']):
                            gx=((y//8)*(r['width']//8)+x//8)*64+y%8*8+x%8
                            flat=y*r['width']+x
                            self.assertEqual(donor[gx//2]>>(4 if gx%2==0 else 0)&15,
                                native[flat//2]>>(4 if flat%2==0 else 0)&15)
                elif r['kind']=='vertices':
                    for start in range(0,n,16):
                        self.assertEqual(native[start:start+6],donor[start:start+6])
                        self.assertEqual(native[start+6:start+8],bytes(2))
                        self.assertEqual(native[start+8:start+16],donor[start+8:start+16])
            for model in row['models']:
                start,n=model['native_offset'],model['bytes']; faces=[]; state=[]; loads=[]
                self.assertEqual(n,dict(sections)[model['layer']])
                first,count=0,0
                for a,b in struct.iter_unpack('>II',asset[start:start+n]):
                    op=a>>24
                    self.assertNotIn(op,(0x0A,0xD2,0xDE))
                    if op in (0xFC,0xE2,0xFA,0xFB,0xD9):state.append((a,b))
                    if op==0xFD:
                        self.assertEqual(b>>24,6);loads.append(b-0x06000000)
                    if op==1:
                        self.assertEqual(b>>24,6);count=a>>12&255
                        first=(b-0x06000000-vertex['native_offset'])//16
                        self.assertLessEqual(first+count,vertex['bytes']//16)
                    if op in (5,6):
                        for word in ((a,b) if op==6 else (a,)):
                            indices=tuple(word>>shift&255 for shift in (16,8,0))
                            self.assertTrue(all(i%2==0 and i//2<count for i in indices))
                            faces.append(tuple(first+i//2 for i in indices))
                donor=models[model['layer']]['rows']
                self.assertEqual(faces,[t for r in donor for t in r.get('global_triangles',[])])
                self.assertEqual(state,[r['words'] for r in donor if r['opcode'] in (0xFC,0xE2,0xFA,0xFB,0xD9)])
                self.assertEqual(loads,[offsets[r['target']] for r in donor if r['opcode'] in (0xF0,0xFD)])
                self.assertEqual(asset[start+n-8:start+n],struct.pack('>II',0xDF000000,0))

    def test_automatic_text_credits_are_in_the_single_catalogue(self):
        self.assertEqual(install.provenance_patch(self.report['objects']),'')
        entries={r['id']:r for r in json.loads((ROOT/'translations/provenance.json').read_bytes())['entries']}
        for row in self.report['objects']:
            entry=entries[row['id']+'/name']['locales']['en']
            self.assertEqual(entry['text'],row['name']);self.assertEqual(entry['credit'],'official')
            self.assertEqual(entry['source']['index'],row['name_source_index'])


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
        self.assertEqual(self.report['furniture']['bank_pool'],self.prior['furniture']['bank_pool'])
        self.assertEqual(self.report['furniture']['expanded_tables'],self.prior['furniture']['expanded_tables'])
        self.assertEqual(self.report['save_runtime']['code'],self.prior['save_runtime']['code'])

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
        for row in self.rows:self.assertIn(int(row['item_id'],16),new[row['stock_group']])
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

    def test_current_rom_checksums_directory_and_prior_runtime_preserved(self):
        self.assertEqual(set(self.files),set(self.old));self.assertEqual(self.image[DMA_END-16:DMA_END],bytes(16))
        self.assertEqual(struct.unpack_from('>II',self.image,16),n64_checksum(self.image))
        self.assertEqual(struct.unpack_from('>4I',self.blob,0xF0),
            (install.BLOB+install.PACKAGE,install.PACKAGE_SIZE,
             zlib.crc32(self.blob[install.PACKAGE:install.PACKAGE+install.PACKAGE_SIZE]),install.PACKAGE_RAM))
        before=self.old[install.BLOB].extract(self.base)
        self.assertEqual(self.blob[0x100:0xC000],before[0x100:0xC000])
        self.assertEqual(self.blob[0xE0:0xF0],before[0xE0:0xF0])
        code=bytearray(self.files[CODE_VROM].extract(self.image));native=self.old[CODE_VROM].extract(self.base)
        at=shops.DESCRIPTOR-CODE_RAM;code[at:at+12]=native[at:at+12]
        hook=self.report['furniture_behaviours']['hook'];at=hook['address']-CODE_RAM
        self.assertEqual(code[at:at+8].hex(),hook['after']);code[at:at+8]=native[at:at+8]
        self.assertEqual(code,native)

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
