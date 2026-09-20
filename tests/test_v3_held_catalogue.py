"""Prepared parent previews, actual umbrella ordering, and unchanged room identities."""
import json
import copy
import os
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,apply_ups
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
from v3_asset_loader import BLOB,MODULE
from v3_furniture_install import inputs
from v3_import_storage import ROWS,ITEMS,slot
from v3_catalogue_capacity import shifted
import v3_catalogue as catalogue
import v3_furniture_runtime as room
import v3_held_catalogue as adapter
from tests import test_v3_equipment_runtime as shared

OUTPUT=ROOT/os.environ.get('V3_HELD_CATALOGUE_BUILD','build/v3-held-catalogue-02')

class HostTests(unittest.TestCase):
    sanitized=shared.HostTests.sanitized
    def test_selected_profiles_and_catalogue(self):
        self.sanitized('v3_held_catalogue_test.c')

    def test_shared_palette_bank_bounds(self):
        self.sanitized('v3_held_items_test.c',defines=('-DAF_V3_POCKET_ICON_PALETTES=1',))

@unittest.skipUnless((OUTPUT/'build.json').is_file(),'Current held catalogue cartridge required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((OUTPUT/'build.json').read_bytes())
        cls.base,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.rom);cls.old=cls.before[BLOB].extract(cls.base)
        cls.e=cls.report['equipment_resources'];cls.r=cls.e['catalogue'];cls.cat=cls.report['catalogue']
        cls.data=cls.files[catalogue.VROM].extract(cls.rom)
        cls.rel=cls.files[catalogue.RELOC].extract(cls.rom)

    def test_complete_prepared_art_profiles_and_parent_aliases(self):
        directory=ROOT/self.r['evidence']['prepared_directory']
        art=json.loads((directory/'art.json').read_bytes())
        self.assertEqual(sha256((directory/'art.json').read_bytes()),self.r['evidence']['prepared_sha256'])
        rows={r['item_id']:r for r in art['objects']}
        parents={r['display_item_id']:r for r in self.e['collection']['rows']}
        self.assertEqual(len(self.r['imports']),8)
        self.assertEqual(self.r['artwork_bytes'],11136)
        for r in self.r['imports']:
            item=int(r['item_id'],16);i=slot(item);at=int(r['object_vrom'],16)-BLOB
            prepared=(directory/rows[r['item_id']]['object_file']).read_bytes()
            self.assertEqual(self.blob[at:at+len(prepared)],prepared)
            self.assertEqual(sha256(prepared),r['object_sha256'])
            self.assertEqual(struct.unpack_from('>HHI',self.blob,ROWS+i*80),(r['runtime_index'],item,1))
            self.assertEqual(struct.unpack_from('>I',self.blob,ROWS+i*80+76)[0],1)
            self.assertEqual(self.blob[ITEMS+i*32:ITEMS+(i+1)*32],
                struct.pack('>HH',r['runtime_index'],item)+bytes(24)+struct.pack('>HH',int(r['parent_item_id'],16),0))
            self.assertEqual(parents[r['item_id']]['item_id'],r['parent_item_id'])
            self.assertEqual(parents[r['item_id']]['room_drop_item_id'],r['parent_item_id'])
            self.assertFalse(r['independently_selectable'])
        self.assertEqual(self.blob[0x20:0xE0],self.old[0x20:0xE0])
        self.assertEqual(self.report['display_aliases'],self.prior['display_aliases'])

    def test_native_order_relocation_pool_and_full_retention(self):
        r=self.cat['handheld'];at=r['table_address']-catalogue.RAM
        table=self.data[at:at+r['total_rows']*2]
        self.assertEqual((r['native_rows'],r['total_rows']),(32,40))
        self.assertEqual(struct.unpack('>40H',table),tuple(range(810,842))+tuple(range(2131,2139)))
        self.assertEqual(sha256(table),r['table_sha256'])
        self.assertEqual(self.cat['imports'],self.prior['catalogue']['imports'])
        self.assertEqual(self.cat['clothing']['table_sha256'],self.prior['catalogue']['clothing']['table_sha256'])
        self.assertLessEqual(self.cat['conservative_pool_required'],self.cat['pool_reserved'])
        self.assertEqual(self.cat['pool_reserved'],self.prior['catalogue']['pool_reserved'])
        pointer=shifted(catalogue.UMBRELLA_POINTER)-catalogue.RAM
        for address in (0x801A0010,0x802F8010,0x803D0010):
            moved=relocate_verified_data(Image(catalogue.RAM,len(self.data),struct.unpack_from('>5I',self.rel)),
                self.data,self.rel,address)
            self.assertEqual(struct.unpack_from('>2I',moved,pointer),(address+at,40))
            self.assertEqual(moved[at:at+len(table)],table)
        changed={BLOB,MODULE,0x19D40,catalogue.VROM,catalogue.RELOC,catalogue.PARENT,room.VROM}
        for v in self.files.keys()-changed:
            self.assertEqual(self.files[v].extract(self.rom),self.before[v].extract(self.base),hex(v))
        old=self.before[room.VROM].extract(self.base);new=bytearray(self.files[room.VROM].extract(self.rom))
        hook=self.report['furniture']['bank_pool']['hook'];at=hook['address']-room.RAM
        self.assertEqual(new[at:at+len(bytes.fromhex(hook['after']))].hex(),hook['after'])
        new[at:at+len(bytes.fromhex(hook['before']))]=bytes.fromhex(hook['before'])
        self.assertEqual(new,old)
        self.assertEqual(self.report['furniture']['imports'],self.prior['furniture']['imports'])
        for key in ('save_runtime','save_codec','collection','hra','feng_shui'):
            self.assertEqual(self.report[key],self.prior[key])
        at=self.e['blob_offset']
        self.assertEqual(self.blob[at:at+self.e['bytes']],self.old[at:at+self.e['bytes']])

    def test_complete_patch_receipts_and_no_memory_profile_growth(self):
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native,(OUTPUT/'asset-loader.ups').read_bytes()),self.rom)
        self.assertEqual(sha256(self.rom),self.report['output_sha256'])
        self.assertEqual(self.report['runtime_abi'],self.prior['runtime_abi']+1)
        self.assertEqual(self.r['additional_resident_bytes'],0)
        self.assertEqual(self.r['profile_bits_enabled'],0)
        self.assertFalse(self.r['saved_format_changed'])
        for path in adapter.SOURCES:
            self.assertEqual(sha256((ROOT/path).read_bytes()),self.report['sources'][path])

CATEGORY_OUTPUT=ROOT/os.environ.get('V3_HELD_CATEGORY_BUILD','build/v3-held-category-02')

@unittest.skipUnless((CATEGORY_OUTPUT/'build-lock.json').is_file(),'Current category refresh required')
class CategoryRefreshTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from v3_furniture_pipeline import Source
        cls.rom,cls.report=inputs(CATEGORY_OUTPUT/'build-lock.json')
        cls.base,cls.prior=inputs(CATEGORY_OUTPUT/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.rom);cls.oldblob=cls.before[BLOB].extract(cls.base)
        cls.e=cls.report['equipment_resources'];cls.old=cls.prior['equipment_resources']
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_complete_source_categories_and_unchanged_runtime_code(self):
        from v3_handheld_items import selection_records,parent_records,pocket_icons
        from v3_player_actions import POCKET_ICON_OFFSET,TABLE_OFFSET
        from v3_held_collection import source_records
        before=bytearray(self.oldblob)
        regenerated=adapter.refresh_parents(self.source,self.old,before)
        at=self.e['blob_offset'];n=self.e['bytes']
        self.assertEqual(before[at:at+n],self.blob[at:at+n])
        self.assertEqual(regenerated['category_refresh'],self.e['category_refresh'])
        self.assertEqual(self.e['bytes'],self.old['bytes'])
        restored=bytearray(self.blob[at:at+n]);old=self.oldblob[at:at+n]
        for data,receipt in ((selection_records(self.source,self.e)[0],self.e['player_actions']['equipment_selection']),
                (parent_records(self.source,self.e)[0],self.e['parent_readers']),
                (pocket_icons(self.source,self.e,self.e['pocket_icons']['ram'],TABLE_OFFSET-POCKET_ICON_OFFSET)[0],self.e['pocket_icons'])):
            start=receipt['table_offset'];self.assertEqual(restored[start:start+len(data)],data)
            restored[start:start+len(data)]=old[start:start+len(data)]
        self.assertEqual(restored,old)  # All action, sound, and preview code stays exact.
        self.assertEqual(len(self.e['parent_readers']['rows']),16)
        self.assertEqual(self.e['pocket_icons']['bytes'],1568)
        self.assertEqual(source_records(self.source,self.e)[1]['rows'],self.e['collection']['rows'])
        for key in ('inventory_preview','held_rig_actions','event_acquisition','ground_categories','item_categories','records'):
            self.assertEqual(self.e[key],self.old[key])
        stock=self.e['event_acquisition']['source']['rows']
        offered={r['item_id']:category['price'] for category in stock for r in category['items']}
        for item in self.e['category_refresh']['added_parent_ids']:self.assertEqual(offered[item],680)

    def test_retained_models_new_profiles_and_safe_catalogue_relocation(self):
        prepared,_=adapter.assets(self.source,self.e,ROOT/'build/v3-furniture-indexed-sequence-prepared-01')
        models={p['item_id']:data for p,_,data in prepared}
        old={r['parent_item_id']:r for r in self.old['catalogue']['imports']}
        for row in self.e['catalogue']['imports']:
            start=int(row['object_vrom'],16)-BLOB;data=models[row['parent_item_id']]
            self.assertEqual(self.blob[start:start+len(data)],data)
            if row['parent_item_id'] in old:self.assertEqual(row,old[row['parent_item_id']])
        cat=self.report['catalogue'];h=cat['handheld']
        self.assertEqual((h['native_rows'],h['total_rows']),(32,48))
        self.assertEqual(cat['imports'],self.prior['catalogue']['imports'])
        self.assertLessEqual(cat['conservative_pool_required'],cat['pool_reserved'])
        data=self.files[catalogue.VROM].extract(self.rom);rel=self.files[catalogue.RELOC].extract(self.rom)
        at=h['table_address']-catalogue.RAM
        self.assertEqual(struct.unpack_from('>48H',data,at),tuple(range(810,842))+tuple(range(2131,2147)))
        for address in (0x80200010,0x80380010):
            moved=relocate_verified_data(Image(catalogue.RAM,len(data),struct.unpack_from('>5I',rel)),data,rel,address)
            self.assertEqual(struct.unpack_from('>2I',moved,shifted(catalogue.UMBRELLA_POINTER)-catalogue.RAM),(address+at,48))
        changed={BLOB,MODULE,0x19D40,catalogue.VROM,catalogue.RELOC,catalogue.PARENT}
        for v in self.files.keys()-changed:
            self.assertEqual(self.files[v].extract(self.rom),self.before[v].extract(self.base),hex(v))

    def test_dependency_and_corruption_rejection(self):
        from v3_handheld_items import selection_records
        for mutation in ('sound','inventory','kind'):
            e=copy.deepcopy(self.old)
            if mutation=='sound':e['held_rig_actions']['loop_sound_installed']=False
            if mutation=='inventory':e['inventory_preview']['animated_rigs_installed']=False
            if mutation=='kind':e['kind_readers']['rows']=[r for r in e['kind_readers']['rows'] if r['item_id']!='224C']
            with self.assertRaises(ValueError):selection_records(self.source,e,categories=[22,23])
        damaged=bytearray(self.oldblob);damaged[self.old['blob_offset']]^=1
        with self.assertRaises(ValueError):adapter.refresh_parents(self.source,self.old,damaged)
        with self.assertRaises(ValueError):adapter.refresh_parents(self.source,self.e,bytearray(self.blob))

    def test_profile_retention_provenance_and_reconstructible_patch(self):
        before=bytes.fromhex(self.prior['save_runtime']['profile_hex']);after=bytes.fromhex(self.report['save_runtime']['profile_hex'])
        want=bytearray(before)
        for row in self.e['parent_readers']['rows']:want[row['profile_byte']]|=row['profile_mask']
        self.assertEqual(after,want);self.assertEqual(sum((a^b).bit_count() for a,b in zip(before,after)),8)
        self.assertEqual(self.e['optional_selection']['profile_bits_enabled'],16)
        self.assertTrue(self.report['shared_runtime_refresh']['saved_profile_changed'])
        self.assertFalse(self.report['shared_runtime_refresh']['saved_format_changed'])
        from v3_furniture_install import provenance_patch,reuse_resource_tail
        self.assertEqual(provenance_patch(self.e['parent_readers']['rows']),'')
        for path in adapter.SOURCES:self.assertEqual(sha256((ROOT/path).read_bytes()),self.report['sources'][path])
        reuse_resource_tail(self.rom,self.report,self.blob)
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native,(CATEGORY_OUTPUT/'asset-loader.ups').read_bytes()),self.rom)

ROOM_OUTPUT=ROOT/'build/v3-room-parent-category-06'


@unittest.skipUnless((ROOM_OUTPUT/'build-lock.json').is_file(),'Current room-parent cartridge required')
class RoomCategoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from v3_furniture_pipeline import Source
        cls.rom,cls.report=inputs(ROOM_OUTPUT/'build-lock.json')
        cls.base,cls.prior=inputs(ROOM_OUTPUT/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.rom);cls.oldblob=cls.before[BLOB].extract(cls.base)
        cls.e=cls.report['equipment_resources'];cls.old=cls.prior['equipment_resources']
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_complete_parent_contexts_source_order_and_retained_categories(self):
        from v3_handheld_items import selection_records,parent_records
        from v3_held_collection import source_records
        _,selected=selection_records(self.source,self.e)
        self.assertEqual(selected['categories'],[21,22,23])
        self.assertEqual(json.loads(json.dumps(selected['rows'])),self.e['player_actions']['equipment_selection']['rows'])
        _,parents=parent_records(self.source,self.e);self.assertEqual(parents['rows'],self.e['parent_readers']['rows'])
        _,collection=source_records(self.source,self.e);self.assertEqual(collection['rows'],self.e['collection']['rows'])
        self.assertEqual(len(parents['rows']),24)
        previous={r['item_id']:r for r in self.old['collection']['rows']}
        added=[r for r in collection['rows'] if r['item_id'] not in previous]
        self.assertEqual([r['catalogue']['position'] for r in added],list(range(48,56)))
        self.assertEqual([r['display_item_id'] for r in added],['3C00','3C04','3C08','3C0C','3000','3004','3008','300C'])
        for row in collection['rows']:
            if row['item_id'] in previous:self.assertEqual(row,previous[row['item_id']])
            else:self.assertEqual(row['room_drop_item_id'],row['display_item_id'])
        for key in ('inventory_preview','held_rig_actions','event_acquisition','ground_categories','item_categories','records'):
            self.assertEqual(self.e[key],self.old[key])

    def test_complete_reused_models_profiles_and_forward_inverse_aliases(self):
        from v3_furniture_install import profile
        import v3_display_aliases as aliases
        prepared,_=adapter.assets(self.source,self.e,ROOT/'build/v3-furniture-indexed-sequence-prepared-01',self.blob)
        installed={r['parent_item_id']:r for r in self.e['catalogue']['imports']}
        old={r['parent_item_id']:r for r in self.old['catalogue']['imports']}
        for parent,row,data in prepared:
            actual=installed[parent['item_id']];vrom=int(actual['object_vrom'],16);at=vrom-BLOB
            self.assertEqual(self.blob[at:at+len(data)],data)
            self.assertEqual(self.oldblob[at:at+len(data)],data)
            i=slot(int(row['item_id'],16));native=profile(row,vrom)
            self.assertEqual(self.blob[ROWS+i*80:ROWS+(i+1)*80],
                struct.pack('>HHI',parent['runtime_index'],int(row['item_id'],16),1)+native+struct.pack('>I',1))
            if parent['item_id'] in old:self.assertEqual(actual,old[parent['item_id']])
            else:
                self.assertEqual(native[16:48],bytes(32))
                self.assertEqual(native[-4:],struct.pack('>I',self.e['room_rigs']['vtable']))
        rows=aliases.records(self.report,self.blob);table,metadata=aliases.encode(rows)
        self.assertEqual(len(rows),11);self.assertEqual(rows,self.report['display_aliases']['rows'])
        self.assertEqual(self.blob[aliases.OFFSET:aliases.OFFSET+len(table)],table)
        for item,payload in metadata.items():self.assertEqual(self.blob[ITEMS+slot(item)*32+28:ITEMS+slot(item)*32+32],payload)
        h=self.report['catalogue']['handheld'];self.assertEqual(h['total_rows'],56)
        data=self.files[catalogue.VROM].extract(self.rom);at=h['table_address']-catalogue.RAM
        self.assertEqual(struct.unpack_from('>56H',data,at),tuple(range(810,842))+
            tuple(r['catalogue_index'] for r in h['imports']))
        self.assertLessEqual(self.report['catalogue']['conservative_pool_required'],self.report['catalogue']['pool_reserved'])

    def test_complete_bounded_icon_palettes_and_current_code(self):
        from v3_handheld_items import pocket_icons
        data,receipt=pocket_icons(self.source,self.e,0x804A6800,2048)
        for k,v in json.loads(json.dumps(receipt)).items():self.assertEqual(v,self.e['pocket_icons'][k])
        self.assertEqual(len(data),2016);bank=receipt['palette_bank'];self.assertEqual(bank['bytes'],96)
        start=self.e['blob_offset'];module=self.blob[start:start+self.e['bytes']]
        self.assertEqual(module[0x3800:0x3800+len(data)],data)
        self.assertEqual(module[0x37A0:0x3800],bytes.fromhex(bank['data_hex']))
        for resource in receipt['resources']:
            at=resource['ram']-0x804A3000
            self.assertEqual(sha256(module[at:at+resource['bytes']]),resource['sha256'])
        for part,at,end in (('held_items',0x3000,0x37A0),('room_rigs',0xE800,0xEE00)):
            code=(ROOM_OUTPUT/part/'code.bin').read_bytes();self.assertEqual(module[at:at+len(code)],code)
            self.assertFalse(any(module[at+len(code):end]))
        for v in self.files.keys()-{BLOB,MODULE,0x19D40,catalogue.VROM,catalogue.RELOC,catalogue.PARENT,room.VROM,0x7749C0}:
            self.assertEqual(self.files[v].extract(self.rom),self.before[v].extract(self.base),hex(v))
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native,(ROOM_OUTPUT/'asset-loader.ups').read_bytes()),self.rom)

    def test_profile_composition_and_incomplete_category_rejection(self):
        from v3_handheld_items import selection_records
        import v3_optional_composition as composer
        for key in ('room_rigs','inventory_preview'):
            changed=copy.deepcopy(self.e);changed.pop(key)
            with self.assertRaises(ValueError):selection_records(self.source,changed)
        changed=copy.deepcopy(self.e);changed['room_rigs']['rows'].pop()
        with self.assertRaises(ValueError):selection_records(self.source,changed)
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(ROOM_OUTPUT/'build-lock.json');catalog=composer.catalogue(self.rom,self.report)
            self.assertEqual(len(catalog),128)
            self.assertEqual(sha256(composer.compose(self.rom,self.report,catalog,composer.resolve(catalog,[]))[0]),
                self.report['translation_baseline']['sha256'])
            self.assertEqual(composer.compose(self.rom,self.report,catalog,composer.resolve(catalog,list(catalog)))[0],self.rom)
            chosen=[composer.item_key(0x2244),composer.item_key(0x224B)]
            selection=composer.resolve(catalog,chosen);profile=bytes.fromhex(selection['profile_hex'])
            self.assertEqual(sum(b.bit_count() for b in profile),2)
            self.assertEqual(profile[128],1);self.assertEqual(profile[32],8)
            for key in chosen:
                with self.assertRaises(ValueError):composer.resolve(catalog,[composer.item_key(int(catalog[key]['display_item_id'],16))])
            output,_,_=composer.compose(self.rom,self.report,catalog,selection)
            self.assertEqual(output,composer.compose(self.rom,self.report,catalog,composer.resolve(catalog,list(reversed(chosen))))[0])
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin


if __name__=='__main__':unittest.main()
