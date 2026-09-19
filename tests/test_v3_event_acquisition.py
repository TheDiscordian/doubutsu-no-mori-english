"""Shared donor acquisition records and additive native stock integration."""
import copy
import json
import os
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,apply_ups,n64_checksum,u32
from v3_asset_loader import BLOB,MODULE,STARTUP,CONFIG
from v3_furniture_install import inputs
from v3_furniture_pipeline import Source
from npc_mail_show import relocate_verified_data
from v3_handheld_items import discover as equipment
import v3_event_acquisition as event
import tests.test_v3_equipment_runtime as shared

OUTPUT=ROOT/os.environ.get('V3_EVENT_BUILD','build/v3-event-stock-01')

class SourceTests(unittest.TestCase):
    sanitized=shared.HostTests.sanitized
    @classmethod
    def setUpClass(cls):
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_stock_operations_and_preserved_native_prefix(self):
        self.sanitized('v3_event_acquisition_test.c')

    def test_source_categories_attach_to_existing_identities(self):
        inventory=equipment(self.source); before=copy.deepcopy(inventory)
        result=event.annotate(inventory,self.source)
        self.assertEqual([(r['first'],r['count'],r['price']) for r in result['rows']],
                         [(0x2254,8,780),(0x224C,8,680),(0x2244,8,480)])
        self.assertEqual(len(inventory['rows']),79)
        self.assertEqual(sum('acquisition' in r for r in inventory['rows']),24)
        for old,new in zip(before['rows'],inventory['rows']):
            self.assertEqual(old,{k:v for k,v in new.items() if k!='acquisition'})
        self.assertFalse(result['acquisition_installed']);self.assertFalse(result['sold_out_refills'])

    def test_complete_function_table_and_dependency_mutations_reject(self):
        original=self.source
        for at,n,_,_ in event.FUNCTIONS:
            s=copy.copy(original);s.rel=bytearray(original.rel)
            s.rel[s.sections[1][0]+at+n-1]^=1
            with self.assertRaisesRegex(ValueError,'complete donor event stock function'):
                event.discover(s)
        for name,_ in event.TABLES:
            s=copy.copy(original);s.data=bytearray(original.data);at,n=s.symbol(name);s.data[at+n-1]^=1
            with self.assertRaisesRegex(ValueError,'complete donor event stock table'):
                event.discover(s)
        s=copy.copy(original);s.code_relocations=dict(original.code_relocations)
        s.code_relocations[0x1B61F0+0x46]=(6,1,5,0x53A6A)
        with self.assertRaisesRegex(ValueError,'function/dependencies'):event.discover(s)

@unittest.skipUnless((OUTPUT/'build.json').is_file(),'Current event stock cartridge required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((OUTPUT/'build.json').read_bytes())
        cls.base,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.rom);cls.e=cls.report['equipment_resources']
        cls.r=cls.e['event_acquisition'];at=cls.e['blob_offset'];cls.module=cls.blob[at:at+cls.e['bytes']]

    def test_constructor_relocation_and_all_retained_owner_code(self):
        old=self.before[event.OWNER].extract(self.base);new=self.files[event.OWNER].extract(self.rom)
        rel=self.files[event.RELOC].extract(self.rom);oldrel=self.before[event.RELOC].extract(self.base)
        patch=self.r['constructor_hook'];at=patch['offset'];restored=bytearray(new)
        self.assertEqual(u32(old,at),patch['before']);self.assertEqual(u32(new,at),patch['after'])
        restored[at:at+4]=old[at:at+4];self.assertEqual(restored,old)
        self.assertEqual(sha256(new),self.r['owner_sha256']);self.assertEqual(sha256(rel),self.r['reloc_sha256'])
        oldrows=list(struct.unpack_from('>'+str(u32(oldrel,16))+'I',oldrel,20));oldrows.remove(self.r['removed_relocation'])
        self.assertEqual(list(struct.unpack_from('>'+str(u32(rel,16))+'I',rel,20)),oldrows)
        sections=struct.unpack_from('>5I',rel)
        for base in (0x80200010,0x80350010):
            moved=relocate_verified_data(SimpleNamespace(ram=event.OWNER_RAM,resident_bytes=len(new),sections=sections),new,rel,base)
            self.assertEqual(u32(moved,at),patch['after'])
            # Both initializer/getter calls remain owner-relative, not stale linked addresses.
            self.assertEqual(u32(moved,0x4C0),event.jump(base+0x228,link=True))
        self.assertEqual(self.before[CODE_VROM].extract(self.base),self.files[CODE_VROM].extract(self.rom))

    def test_complete_module_records_and_startup(self):
        old=self.prior['equipment_resources'];blob=self.before[BLOB].extract(self.base)
        previous=blob[old['blob_offset']:old['blob_offset']+old['bytes']]
        self.assertEqual(self.module[:len(previous)],previous)
        self.assertEqual(len(self.module),event.SIZE)
        self.assertEqual(sha256(self.module),self.e['sha256']);self.assertEqual(zlib.crc32(self.module),self.e['crc32'])
        self.assertEqual(self.module[-16:],bytes.fromhex('AF48C0DE')*4)
        self.assertLessEqual(self.r['code']['bytes'],event.TABLE-event.CODE)
        self.assertEqual(sha256(self.module[event.CODE:event.CODE+self.r['code']['bytes']]),self.r['code']['sha256'])
        for k,r in enumerate(self.r['source']['rows']):
            self.assertEqual(struct.unpack_from('>3H2B',self.module,event.TABLE+8*k),
                             (r['first'],r['price'],r['message'],r['count'],r['kind']))
        self.assertEqual(self.blob[0x20:0xE0],blob[0x20:0xE0])
        self.assertIn('-DAF_V3_EQUIPMENT_BYTES=0xC000u',self.report['startup']['flags'])
        self.assertLessEqual(self.report['startup']['bytes'],CONFIG-STARTUP)
        self.assertTrue(self.r['stock_initialization_installed']);self.assertFalse(self.r['acquisition_installed'])
        self.assertFalse(self.r['purchase_menu_installed']);self.assertEqual(self.r['profile_bits_enabled'],0)

    def test_patch_resources_and_source_contracts(self):
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(original,(OUTPUT/'asset-loader.ups').read_bytes()),self.rom)
        self.assertEqual(struct.unpack_from('>2I',self.rom,16),n64_checksum(self.rom))
        changed={BLOB,MODULE,0x19D40,event.OWNER,event.RELOC}
        self.assertEqual(self.before.keys(),self.files.keys())
        for v,file in self.before.items():
            self.assertEqual(file.index,self.files[v].index)
            if v not in changed:self.assertEqual(file.extract(self.base),self.files[v].extract(self.rom),hex(v))
        for p in event.SOURCES:self.assertEqual(sha256((ROOT/p).read_bytes()),self.report['sources'][p])
        self.assertFalse(self.report['shared_runtime_refresh']['saved_format_changed'])
        self.assertFalse(self.report['shared_runtime_refresh']['saved_profile_changed'])
        core=self.before[CODE_VROM].extract(self.base)
        for address in (0x80080080,0x8008033C):
            bad=bytearray(core);bad[address-CODE_RAM]^=1
            with self.assertRaisesRegex(ValueError,'native event allocation/lookup'):
                event.native_contract(self.base,bad)

if __name__=='__main__':unittest.main()
