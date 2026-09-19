"""Prepared parent previews, actual umbrella ordering, and unchanged room identities."""
import json
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

if __name__=='__main__':unittest.main()
