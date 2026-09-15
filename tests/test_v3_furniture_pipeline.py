"""Shared format discovery, conversion integrity, and current batch installation."""
import copy
import json
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

    def test_review_does_not_drop_callbacks_or_action_sounds(self):
        with self.assertRaisesRegex(ValueError,'custom callbacks'): self.source.profile(0x3350)
        identities=pipeline.identity_rows(ROOT/'build/item-identity-megasheet.xlsx')
        p=self.source.profile(0x324C)
        with self.assertRaisesRegex(ValueError,'action-sound category'):
            pipeline.metadata(self.source,0x324C,p,identities[0x324C])
        with self.assertRaises(ValueError): self.source.pointers(self.source.size-2,4)

    def test_complete_texels_vertices_and_compiled_triangles_for_entire_batch(self):
        for row in self.report['objects']:
            asset=(self.art/row['object_file']).read_bytes()
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
        at=shops.DESCRIPTOR-CODE_RAM;code[at:at+12]=native[at:at+12];self.assertEqual(code,native)

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
