"""Current shared tree drops, retained native machinery, and all seasonal bindings."""
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
OUTPUT=ROOT/os.environ.get('V3_TREE_INTERACTIONS_BUILD','build/v3-shared-tree-interactions-04')

class HostTests(unittest.TestCase):
    sanitized=shared.HostTests.sanitized
    def test_selected_drop_luck_bees_and_complete_cut_attributes(self):self.sanitized('v3_tree_interactions_test.c')

@unittest.skipUnless((OUTPUT/'build.json').is_file(),'Current tree-interaction cartridge required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((OUTPUT/'build.json').read_bytes());cls.base,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.e=cls.report['equipment_resources'];cls.r=cls.e['scenery'];cls.d=cls.r['interactions']
        cls.blob=cls.files[BLOB].extract(cls.rom);cls.oldblob=cls.before[BLOB].extract(cls.base)
        cls.original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()

    def test_source_records_complete_native_functions_and_relocated_consumers(self):
        source=scenery.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        old=self.prior['equipment_resources']
        evidence=scenery.interaction_contract(source,self.base,self.original,old['scenery'],old['ground_categories'])
        for key,value in evidence.items():self.assertEqual(json.loads(json.dumps(value)),self.d[key])
        code=(OUTPUT/'scenery/code.bin').read_bytes()
        for name,rows in (('drops',self.d['drops']),('cuts',self.d['cuts'])):
            at=self.r['code']['symbols']['af_v3_tree_'+name]-self.r['ram']
            want=b''.join(struct.pack('>'+str(len(row))+'H',*row) for row in rows)
            self.assertEqual(code[at:at+len(want)],want)
        self.assertEqual([len(row['calls']) for row in self.d['owners']],[2,3,2,2])
        for row in (*self.r['owners'],self.d['daily_owner']):
            data=self.files[row['vrom']].extract(self.rom);before=self.before[row['vrom']].extract(self.base)
            restored=bytearray(data)
            for p in row['patches']:
                self.assertEqual(u32(data,p['offset']),p['after']);self.assertEqual(u32(before,p['offset']),p['before'])
                struct.pack_into('>I',restored,p['offset'],p['before'])
            self.assertEqual(restored,before)
            rel=self.files[row['reloc']].extract(self.rom);oldrel=self.before[row['reloc']].extract(self.base)
            previous=struct.unpack_from('>'+str(u32(oldrel,16))+'I',oldrel,20)
            kept=tuple(v for v in previous if v not in row['removed_relocations'])
            self.assertEqual(u32(rel,16),len(kept));self.assertEqual(rel[:16],oldrel[:16])
            self.assertEqual(struct.unpack_from('>'+str(len(kept))+'I',rel,20),kept)
            for ram in (0x80200010,0x80300010):
                moved=relocate_verified_data(SimpleNamespace(ram=row['ram'],resident_bytes=row['resident_bytes'],
                    sections=struct.unpack_from('>5I',rel)),data,rel,ram)
                for p in row['patches']:self.assertEqual(u32(moved,p['offset']),p['after'])
        core=bytearray(self.files[CODE_VROM].extract(self.rom));before=self.before[CODE_VROM].extract(self.base)
        for h in self.d['daily_owner']['core_hooks']:
            a=h['offset'];self.assertEqual(core[a:a+8].hex(),h['after']);self.assertEqual(before[a:a+8].hex(),h['before'])
            core[a:a+8]=bytes.fromhex(h['before'])
        self.assertEqual(core,before)

    def test_packet_bootstrap_memory_and_complete_resource_retention(self):
        old=self.prior['equipment_resources'];a=scenery.BOOT_RAM-old['ram'];b=scenery.BOOT_END-old['ram'];start=old['blob_offset']
        before=self.oldblob[start:start+old['bytes']];after=self.blob[start:start+self.e['bytes']]
        self.assertEqual(before[:a],after[:a]);self.assertEqual(before[b:],after[b:]);self.assertEqual(len(before),len(after))
        boot=(OUTPUT/'scenery_bootstrap/code.bin').read_bytes();self.assertEqual(after[a:b],boot+bytes(b-a-len(boot)))
        self.assertEqual(after[b-4:b],bytes(4))
        code=(OUTPUT/'scenery/code.bin').read_bytes();start=self.r['blob_offset']
        self.assertEqual(self.blob[start:start+len(code)],code);self.assertLessEqual(len(code),12288)
        self.assertEqual(self.r['additional_fixed_resident_bytes'],12288)
        self.assertLessEqual(self.r['ram']+12288,self.report['furniture']['bank_pool']['start'])
        self.assertEqual(self.d['additional_resident_bytes'],4096);self.assertEqual(self.d['additional_scene_resident_bytes'],0)
        self.assertEqual(self.r['banks'],old['scenery']['banks'])
        self.assertEqual(len(self.blob),len(self.oldblob))
        for row in self.r['banks']:
            a,n=row['blob_offset'],row['bytes'];self.assertEqual(self.blob[a:a+n],self.oldblob[a:a+n])
        for path in scenery.SOURCES:self.assertEqual(sha256((ROOT/path).read_bytes()),self.report['sources'][path])

    def test_complete_patch_optional_profiles_and_saved_formats(self):
        self.assertEqual(sha256(self.rom),self.report['output_sha256'])
        self.assertEqual(apply_ups(self.original,(OUTPUT/'asset-loader.ups').read_bytes()),self.rom)
        changed={BLOB,MODULE,CODE_VROM,0x19D40,0x970920,0x9754A0}|{r[k] for r in self.r['owners'] for k in ('vrom','reloc')}
        for v,e in self.before.items():
            if v not in changed:self.assertEqual(e.extract(self.base),self.files[v].extract(self.rom),hex(v))
        for key in ('save_runtime','save_codec','catalogue','furniture'):self.assertEqual(self.prior[key],self.report[key])
        self.assertFalse(self.report['shared_runtime_refresh']['saved_format_changed'])
        self.assertFalse(self.r['selectable']);self.assertFalse(self.r['acquisition_installed'])
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
