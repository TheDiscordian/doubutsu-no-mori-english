"""Animated inventory category records, unchanged native allocations, and complete installation."""
import json
import copy
import os
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,apply_ups,by_vrom,sha256,u32
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


CAPACITY=ROOT/'build/v3-inventory-capacity-02'


@unittest.skipUnless((CAPACITY/'build-lock.json').is_file(),'Expanded inventory cartridge required')
class JointCapacityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(CAPACITY/'build-lock.json')
        cls.base,cls.prior=inputs(CAPACITY/'base-lock.json')
        cls.files,cls.old_files=by_vrom(cls.image),by_vrom(cls.base)
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.e=cls.report['equipment_resources'];cls.p=cls.e['inventory_preview']
        cls.work=cls.p['joint_work'];cls.blob=cls.files[BLOB].extract(cls.image)

    def test_exact_initializer_arrays_owner_bounds_and_relocations(self):
        w=self.work
        self.assertEqual((w['vectors'],w['joint_offset'],w['morph_offset'],w['array_bytes']),
                         (8,0x5E0,0x610,48))
        self.assertEqual((w['bss_bytes'],w['resident_bytes'],w['additional_bss_bytes'],w['additional_pool_bytes']),
                         (0x640,0x4800,96,64))
        owner=bytearray(self.files[inventory.VROM].extract(self.image))
        self.assertEqual(sha256(owner),self.p['owner_sha256'])
        for p in w['patches']:
            at=p['address']-inventory.OWNER_RAM
            self.assertEqual(u32(owner,at),p['after']);struct.pack_into('>I',owner,at,p['before'])
        self.assertEqual(owner,self.old_files[inventory.VROM].extract(self.base))
        rel=bytearray(self.files[inventory.RELOC].extract(self.image))
        self.assertEqual(u32(rel,12),0x640);struct.pack_into('>I',rel,12,w['previous_bss_bytes'])
        self.assertEqual(rel,self.old_files[inventory.RELOC].extract(self.base))
        parent=bytearray(self.files[inventory.MENU_VROM].extract(self.image))
        self.assertEqual(len(w['metadata']),2)
        for p in w['metadata']:
            at=p['offset'];self.assertEqual(parent[at:at+32].hex(),p['after'])
            self.assertEqual(u32(parent,at+12),inventory.OWNER_RAM+0x4800)
            parent[at:at+32]=bytes.fromhex(p['before'])
        self.assertEqual(parent,self.old_files[inventory.MENU_VROM].extract(self.base))
        core=bytearray(self.files[CODE_VROM].extract(self.image));p=w['pool_patch'];at=p['address']-CODE_RAM
        self.assertEqual(u32(core,at),p['after']);self.assertEqual(p['after']-p['before'],64)
        struct.pack_into('>I',core,at,p['before'])
        self.assertEqual(core,self.old_files[CODE_VROM].extract(self.base))
        from npc_mail_show import relocate_verified_data
        from types import SimpleNamespace
        current=self.files[inventory.VROM].extract(self.image);rel=self.files[inventory.RELOC].extract(self.image)
        for address in (0x80200010,0x80370010):
            moved=relocate_verified_data(SimpleNamespace(ram=inventory.OWNER_RAM,
                resident_bytes=w['resident_bytes'],sections=struct.unpack_from('>5I',rel)),current,rel,address)
            self.assertEqual(moved[len(current):],bytes(w['bss_bytes']))
            for p in w['patches']:self.assertEqual(u32(moved,p['address']-inventory.OWNER_RAM),p['after'])

    def test_shared_growth_reproduces_cartridge_and_rejects_changed_ownership(self):
        def run(prior=None,core=None):
            return inventory.grow_joint_work(self.base,prior or self.prior,
                bytearray(self.old_files[BLOB].extract(self.base)),
                bytearray(self.old_files[CODE_VROM].extract(self.base)) if core is None else core,
                self.native,CAPACITY)
        e,changed=run();self.assertEqual(e,self.e)
        for v,data in changed.items():self.assertEqual(data,self.files[v].extract(self.image))
        damaged=copy.deepcopy(self.prior)
        damaged['equipment_resources']['inventory_preview']['owner_sha256']='0'*64
        with self.assertRaises(ValueError):run(damaged)
        core=bytearray(self.old_files[CODE_VROM].extract(self.base))
        struct.pack_into('>I',core,0x800C4B10-CODE_RAM,0x25CE7FF0)
        with self.assertRaisesRegex(ValueError,'signed immediate'):run(core=core)
        core=bytearray(self.old_files[CODE_VROM].extract(self.base))
        struct.pack_into('>I',core,0x800C4B10-CODE_RAM,0x24CE8E20)
        with self.assertRaisesRegex(ValueError,'submenu immediate'):run(core=core)

    def test_every_other_resource_and_resident_module_are_retained(self):
        changed={inventory.VROM,inventory.RELOC,inventory.MENU_VROM,CODE_VROM,BLOB,MODULE,0x19D40}
        self.assertEqual(set(self.files),set(self.old_files))
        for v in set(self.files)-changed:
            self.assertEqual(self.files[v].extract(self.image),self.old_files[v].extract(self.base),hex(v))
        a=self.e['blob_offset'];n=self.e['bytes']
        self.assertEqual(self.blob[a:a+n],self.old_files[BLOB].extract(self.base)[a:a+n])
        self.assertEqual(self.p['rows'],self.prior['equipment_resources']['inventory_preview']['rows'])
        self.assertFalse(self.work['saved_format_changed'] or self.work['preview_records_changed'])
        for key in ('save_runtime','furniture','translation_baseline','translation_updates'):
            self.assertEqual(self.report[key],self.prior[key])
        self.assertEqual(apply_ups(self.native,(CAPACITY/'asset-loader.ups').read_bytes()),self.image)

    def test_optional_selection_and_exact_translation_only_stay_unchanged(self):
        pin=(composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI)
        try:
            composer.use_build_lock(CAPACITY/'build-lock.json');catalogue=composer.catalogue(self.image,self.report)
            self.assertEqual(len(catalogue),120)
            empty=composer.compose(self.image,self.report,catalogue,composer.resolve(catalogue,[]))[0]
            self.assertEqual(sha256(empty),self.report['translation_baseline']['sha256'])
            selection=composer.resolve(catalogue,list(catalogue))
            self.assertEqual(selection['profile_hex'],self.prior['save_runtime']['profile_hex'])
            self.assertEqual(composer.compose(self.image,self.report,catalogue,selection)[0],self.image)
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin


if __name__=='__main__':unittest.main()
