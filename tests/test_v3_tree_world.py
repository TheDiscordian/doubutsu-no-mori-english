"""Installed core world queries, original routine retention, and optionality."""
import json
import os
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,apply_ups,u32
from v3_asset_loader import BLOB,MODULE
from v3_furniture_install import inputs
from npc_mail_show import relocate_verified_data
import v3_scenery_runtime as scenery
import tests.test_v3_equipment_runtime as shared
OUTPUT=ROOT/os.environ.get('V3_TREE_WORLD_BUILD','build/v3-shared-tree-world-02')

class HostTests(unittest.TestCase):
    sanitized=shared.HostTests.sanitized
    def test_geometry_mapping_exclusions_removal_and_walkability(self):self.sanitized('v3_tree_world_test.c')

@unittest.skipUnless((OUTPUT/'build.json').is_file(),'Current tree-world cartridge required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((OUTPUT/'build.json').read_bytes());cls.base,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.e=cls.report['equipment_resources'];cls.r=cls.e['scenery'];cls.d=cls.r['world_queries']
        cls.blob=cls.files[BLOB].extract(cls.rom);cls.oldblob=cls.before[BLOB].extract(cls.base)

    def test_complete_source_core_and_displaced_prologues(self):
        original=self.before[CODE_VROM].extract(self.base);core=bytearray(self.files[CODE_VROM].extract(self.rom))
        source=scenery.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        evidence=scenery.world_contract(source,original)
        for k,value in evidence.items():self.assertEqual(json.loads(json.dumps(value)),self.d[k])
        bad=bytearray(original);bad[0x8006C980-CODE_RAM+12]^=1
        with self.assertRaises(ValueError):scenery.world_contract(source,bad)
        for h in self.d['core_hooks']:
            at=h['offset'];self.assertEqual(core[at:at+8].hex(),h['after']);self.assertEqual(original[at:at+8].hex(),h['before'])
            core[at:at+8]=bytes.fromhex(h['before'])
        self.assertEqual(core,original)
        from v3_import_storage import jump
        code=(OUTPUT/'scenery/code.bin').read_bytes()
        for name,start,_,_,prologue in scenery.WORLD_NATIVE:
            at=self.r['code']['symbols']['af_v3_tree_'+name+'_native']-self.r['ram']
            self.assertEqual(code[at:at+16],bytes.fromhex(prologue)+struct.pack('>2I',jump(start+8),0))

    def test_installed_loading_and_retained_owners_allocations(self):
        old=self.prior['equipment_resources'];a=scenery.BOOT_RAM-old['ram'];b=scenery.BOOT_END-old['ram'];start=old['blob_offset']
        before=self.oldblob[start:start+old['bytes']];after=self.blob[start:start+self.e['bytes']]
        self.assertEqual(before[:a],after[:a]);self.assertEqual(before[b:],after[b:]);self.assertEqual(len(before),len(after))
        boot=(OUTPUT/'scenery_bootstrap/code.bin').read_bytes();self.assertEqual(after[a:b],boot+bytes(b-a-len(boot)))
        self.assertEqual(after[b-4:b],bytes(4))
        code=(OUTPUT/'scenery/code.bin').read_bytes();start=self.r['blob_offset']
        self.assertEqual(self.blob[start:start+len(code)],code);self.assertLessEqual(len(code),8192)
        self.assertEqual(self.r['additional_fixed_resident_bytes'],8192)
        self.assertEqual(self.d['additional_resident_bytes'],0);self.assertEqual(self.d['additional_scene_resident_bytes'],0)
        self.assertEqual(self.r['banks'],old['scenery']['banks'])
        for row in self.r['banks']:
            a,n=row['blob_offset'],row['bytes'];self.assertEqual(self.blob[a:a+n],self.oldblob[a:a+n])
        for row in (*self.r['owners'],self.d):
            data=self.files[row['vrom']].extract(self.rom);before=self.before[row['vrom']].extract(self.base);restored=bytearray(data)
            for p in row['patches']:
                self.assertEqual(u32(data,p['offset']),p['after']);self.assertEqual(u32(before,p['offset']),p['before'])
                struct.pack_into('>I',restored,p['offset'],p['before'])
            self.assertEqual(restored,before)
            rel=self.files[row['reloc']].extract(self.rom);self.assertEqual(rel,self.before[row['reloc']].extract(self.base))
            if row is self.d:
                for ram in (0x80200010,0x80300010):
                    moved=relocate_verified_data(SimpleNamespace(ram=row['ram'],resident_bytes=row['resident_bytes'],
                        sections=struct.unpack_from('>5I',rel)),data,rel,ram)
                    for p in row['patches']:self.assertEqual(u32(moved,p['offset']),p['after'])

    def test_complete_patch_optional_profiles_and_saved_formats(self):
        self.assertEqual(sha256(self.rom),self.report['output_sha256'])
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native,(OUTPUT/'asset-loader.ups').read_bytes()),self.rom)
        changed={BLOB,MODULE,CODE_VROM,0x19D40,self.d['vrom'],self.d['reloc']}|{r['vrom'] for r in self.r['owners']}
        for v,e in self.before.items():
            if v not in changed:self.assertEqual(e.extract(self.base),self.files[v].extract(self.rom),hex(v))
        for key in ('save_runtime','save_codec','catalogue','furniture'):self.assertEqual(self.prior[key],self.report[key])
        self.assertFalse(self.report['shared_runtime_refresh']['saved_format_changed'])
        self.assertFalse(self.r['selectable']);self.assertFalse(self.r['acquisition_installed'])
        for path in scenery.SOURCES:self.assertEqual(sha256((ROOT/path).read_bytes()),self.report['sources'][path])
        import v3_optional_composition as composer
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(OUTPUT/'build-lock.json');choices=composer.catalogue(self.rom,self.report)
            self.assertEqual(len(choices),128)
            self.assertEqual(composer.compose(self.rom,self.report,choices,composer.resolve(choices,list(choices)))[0],self.rom)
            self.assertEqual(sha256(composer.compose(self.rom,self.report,choices,composer.resolve(choices,[]))[0]),
                'a09373b051cbcd93991e5dd6cb17a238a2afb1e2e2d7694d75408d24a55d4eee')
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin

if __name__=='__main__':unittest.main()
