"""Animated inventory category records, unchanged native allocations, and complete installation."""
import json
import os
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_VROM,apply_ups,by_vrom,sha256
from v3_asset_loader import BLOB,MODULE
from v3_furniture_install import inputs,reuse_resource_tail
from v3_equipment_runtime import RAM,GUARD
from v3_furniture_pipeline import Source
import v3_inventory_equipment as inventory
import v3_optional_composition as composer

OUTPUT=ROOT/os.environ.get('V3_INVENTORY_RIG_BUILD','build/v3-inventory-rigs-02')


@unittest.skipUnless((OUTPUT/'build-lock.json').is_file(),'Current animated inventory cartridge required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUTPUT/'build-lock.json');cls.base,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.image),by_vrom(cls.base)
        cls.e=cls.report['equipment_resources'];cls.old=cls.prior['equipment_resources']
        cls.p=cls.e['inventory_preview'];cls.previous=cls.old['inventory_preview']
        cls.blob=cls.files[BLOB].extract(cls.image);cls.oldblob=cls.before[BLOB].extract(cls.base)
        p=cls.e['blob_offset'];cls.module=cls.blob[p:p+cls.e['bytes']]
        cls.oldmodule=cls.oldblob[p:p+cls.old['bytes']]

    def test_complete_source_records_and_eight_rigs_without_parent_enablement(self):
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        selector,receipt=inventory.records(source,self.old,animated=True)
        self.assertEqual(json.loads(json.dumps(receipt))['rows'],self.p['rows'])
        self.assertEqual(self.p['rows'][:8],self.previous['rows'])
        self.assertEqual(len(self.p['rows']),16)
        self.assertEqual(self.module[inventory.SELECTOR:inventory.SELECTOR+len(selector)],selector)
        self.assertEqual(self.p['animated_rig_indices'],list(range(18,26)))
        resources={r['index']:r for r in self.e['records']}
        for row in self.p['rows'][8:]:
            fields=row['fields'];model=resources[fields['shape']];motion=resources[fields['item_animation']]
            self.assertEqual((fields['skeleton'],fields['item_pointer']),(model['pointer'],motion['pointer']))
            self.assertLessEqual(model['bytes']+motion['bytes'],self.p['item_bank_bytes'])
            self.assertEqual((row['draw_callback'],row['joint_vectors'],row['native_frame_speed']),(0x8087E098,4,15))
        for name in ('parent_readers','kind_readers','player_actions','held_rig_actions','sound_programs','animated_rigs','records'):
            self.assertEqual(self.e[name],self.old[name])

    def test_only_preview_tables_code_and_initializer_call_change(self):
        self.assertEqual(self.e['bytes'],self.old['bytes']);self.assertEqual(sha256(self.module),self.e['sha256'])
        self.assertEqual(zlib.crc32(self.module),self.e['crc32'])
        self.assertEqual(self.module[-16:],struct.pack('>4I',*(GUARD,)*4))
        restored=bytearray(self.module);start,end=inventory.CODE,inventory.TABLE
        self.assertEqual(sha256(restored[start:start+self.p['code']['bytes']]),self.p['code']['sha256'])
        restored[start:end]=self.oldmodule[start:end]
        for table in self.p['tables']:
            at,n=table['offset'],table['bytes'];self.assertEqual(sha256(restored[at:at+n]),table['sha256'])
            for row in self.p['rows'][8:]:
                pos=at+row['preview_kind']*4
                want=row['draw_callback'] if table['role']=='draw' else row['fields'][table['role']]
                self.assertEqual(struct.unpack_from('>I',restored,pos)[0],want)
                restored[pos:pos+4]=bytes(4)
        p=inventory.SELECTOR;restored[p:p+self.p['selector_bytes']]=self.oldmodule[p:p+self.p['selector_bytes']]
        self.assertEqual(restored,self.oldmodule)
        owner=bytearray(self.files[inventory.VROM].extract(self.image));h=self.p['animation_speed_hook']
        at=h['address']-inventory.OWNER_RAM
        self.assertEqual(struct.unpack_from('>I',owner,at)[0],h['after']);struct.pack_into('>I',owner,at,h['before'])
        self.assertEqual(owner,self.before[inventory.VROM].extract(self.base))
        symbols=self.p['code']['symbols'];at=symbols['af_v3_inventory_rig_init']-RAM
        self.assertEqual(self.module[at:at+36],struct.pack('>9I',0x86180016,0x2718FFEE,
            0x2F180008,0x13000003,0,0x3C184170,0xAFB80018,0x08014961,0))
        for v in set(self.files)-{inventory.VROM,BLOB,MODULE,0x19D40}:
            self.assertEqual(self.files[v].extract(self.image),self.before[v].extract(self.base),hex(v))
        self.assertEqual(self.files[CODE_VROM].extract(self.image),self.before[CODE_VROM].extract(self.base))
        reuse_resource_tail(self.image,self.report,self.blob)
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native,(OUTPUT/'asset-loader.ups').read_bytes()),self.image)

    def test_unchanged_optional_profiles_saves_and_translation_only(self):
        for key in ('save_runtime','furniture','translation_baseline','translation_updates'):
            self.assertEqual(self.report[key],self.prior[key])
        pin=(composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI)
        try:
            composer.use_build_lock(OUTPUT/'build-lock.json');catalog=composer.catalogue(self.image,self.report)
            self.assertEqual(len(catalog),112)
            self.assertFalse(any(f'GAFE01-r0/item/{i:04X}' in catalog for i in range(0x224C,0x2254)))
            empty=composer.compose(self.image,self.report,catalog,composer.resolve(catalog,[]))[0]
            self.assertEqual(sha256(empty),self.report['translation_baseline']['sha256'])
            self.assertEqual(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,list(catalog)))[0],self.image)
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin


if __name__=='__main__':unittest.main()
