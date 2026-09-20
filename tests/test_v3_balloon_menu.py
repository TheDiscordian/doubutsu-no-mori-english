"""Additive ordinary balloon menu: preserved tables, helpers, memory, and saves."""
import json
import os
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,apply_ups,u32
from v3_asset_loader import BLOB,MODULE
from v3_furniture_install import inputs,reuse_resource_tail
from npc_mail_show import relocate_verified_data
from catalogue_names import Image
import v3_balloon_release as implementation
from tests import test_v3_equipment_runtime as shared
OUTPUT=ROOT/os.environ.get('V3_BALLOON_MENU_BUILD','build/v3-shared-balloon-menu-04')


class HostTests(unittest.TestCase):
    sanitized=shared.HostTests.sanitized
    def test_all_shapes_fields_conditions_and_safe_consumption(self):self.sanitized('v3_balloon_menu_test.c')


@unittest.skipUnless((OUTPUT/'build-lock.json').is_file(),'Current balloon menu proposal required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom,cls.report=inputs(OUTPUT/'build-lock.json');cls.base,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.e=cls.report['equipment_resources'];cls.old=cls.prior['equipment_resources']
        cls.r=cls.e['player_actions']['balloon_menu'];cls.blob=cls.files[BLOB].extract(cls.rom)
        cls.oldblob=cls.before[BLOB].extract(cls.base)

    def test_complete_sources_native_helpers_and_official_credit(self):
        source=implementation.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        self.assertEqual(sha256(source.raw('mTG_tag_word_fly')),self.r['source_label_sha256'])
        for row in self.r['source_functions']:
            self.assertEqual(json.loads(json.dumps(source.function(row['offset'])[1])),row)
        entries=json.loads((ROOT/'translations/provenance.json').read_bytes())['entries']
        self.assertEqual([r for r in entries if r['id']==self.r['provenance_entry']['id']],[self.r['provenance_entry']])
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        core=self.before[CODE_VROM].extract(self.base);tag=self.before[0x3950000].extract(self.base)
        self.assertEqual(implementation.menu_field_address(tag),0x80136EA1)
        self.assertEqual(self.r['field_address'],0x80136EA1)
        self.assertEqual(implementation.menu_native_bindings(self.prior,core,tag,original),self.r['native_functions'])
        for at,is_tag in ((0x80875610,True),(0x80875688,True),(0x800B8B08,False),(0x800B8B18,False)):
            bad=bytearray(tag if is_tag else core);bad[at-(0x8086F310 if is_tag else CODE_RAM)]^=1
            with self.assertRaises(ValueError):
                implementation.menu_native_bindings(self.prior,core if is_tag else bad,bad if is_tag else tag,original)

    def test_complete_table_relocation_hooks_allocation_and_retention(self):
        r=self.r;ram=0x8086F310
        tag=self.files[0x3950000].extract(self.rom);old=self.before[0x3950000].extract(self.base)
        rel=self.files[0x3960000].extract(self.rom);oldrel=self.before[0x3960000].extract(self.base)
        prefix=bytearray(tag[:len(old)])
        for row in r['patches']:
            at=row['address']-ram;self.assertEqual(u32(prefix,at),row['after']);struct.pack_into('>I',prefix,at,row['before'])
        self.assertEqual(prefix,old);self.assertEqual(r['native_count'],44);self.assertEqual(r['menu_type'],44)
        self.assertEqual(tag[r['label_offset']:r['label_offset']+16],b'Let Go          ')
        self.assertEqual(u32(tag,r['label_offset']+16),r['code']['symbols']['af_v3_balloon_menu_fly'])
        for row in r['relocated_images']:
            base=row['base']
            a=relocate_verified_data(Image(ram,len(tag),struct.unpack_from('>5I',rel)),tag,rel,base)
            b=relocate_verified_data(Image(ram,len(old),struct.unpack_from('>5I',oldrel)),old,oldrel,base)
            self.assertEqual(sha256(a),row['sha256'])
            self.assertEqual(a[r['table_offset']:r['table_offset']+44*8],b[r['old_table']-ram:r['old_table']-ram+44*8])
            self.assertEqual(struct.unpack_from('>2I',a,r['table_offset']+44*8),(base+r['words_offset'],3))
            words=struct.unpack_from('>3I',a,r['words_offset'])
            self.assertEqual(words[1],base+r['label_offset'])
            self.assertEqual([a[p-base:p-base+16].rstrip() for p in words],[b'Grab',b'Let Go',b'Quit'])
            self.assertEqual(u32(a,r['label_offset']+16),r['code']['symbols']['af_v3_balloon_menu_fly'])
        at=self.e['blob_offset'];n=self.e['bytes'];module=bytearray(self.blob[at:at+n]);prior=self.oldblob[at:at+n]
        start,end=r['offset'],r['end'];size=r['code']['bytes']
        self.assertFalse(any(prior[start:end]));self.assertLessEqual(start+size,end)
        self.assertEqual(module[start:start+size],(OUTPUT/'balloon_menu/code.bin').read_bytes())
        module[start:end]=prior[start:end];self.assertEqual(module,prior)
        parent=bytearray(self.files[0x7749C0].extract(self.rom))
        for row in r['metadata']:
            at=row['offset'];before,after=bytes.fromhex(row['before']),bytes.fromhex(row['after'])
            self.assertEqual(parent[at:at+len(after)],after);parent[at:at+len(before)]=before
        self.assertEqual(parent,self.before[0x7749C0].extract(self.base))
        core=bytearray(self.files[CODE_VROM].extract(self.rom));p=r['pool_patch'];at=p['address']-CODE_RAM
        self.assertEqual(u32(core,at),p['after']);struct.pack_into('>I',core,at,p['before'])
        self.assertEqual(core,self.before[CODE_VROM].extract(self.base))
        self.assertEqual(p['after']-p['before'],r['additional_pool_bytes'])
        self.assertEqual(r['additional_pool_bytes'],((len(tag)+63)&~63)-((len(old)+63)&~63))
        for v in self.files.keys()-{BLOB,MODULE,CODE_VROM,0x19D40,0x3950000,0x3960000,0x7749C0}:
            self.assertEqual(self.files[v].extract(self.rom),self.before[v].extract(self.base),hex(v))
        for key in ('save_runtime','save_codec','save_warning','translation_baseline'):
            self.assertEqual(self.report[key],self.prior[key])
        self.assertEqual(self.e['optional_selection'],self.old['optional_selection'])

    def test_optional_composition_patch_and_resource_tail(self):
        import v3_optional_composition as composer
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(OUTPUT/'build-lock.json');choices=composer.catalogue(self.rom,self.report)
            self.assertEqual(len(choices),128)
            self.assertEqual(composer.compose(self.rom,self.report,choices,composer.resolve(choices,list(choices)))[0],self.rom)
            self.assertEqual(sha256(composer.compose(self.rom,self.report,choices,composer.resolve(choices,[]))[0]),
                             self.report['translation_baseline']['sha256'])
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(original,(OUTPUT/'asset-loader.ups').read_bytes()),self.rom)
        reuse_resource_tail(self.rom,self.report,self.blob)


if __name__=='__main__':unittest.main()
