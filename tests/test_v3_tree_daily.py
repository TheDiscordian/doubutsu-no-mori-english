"""Current daily-growth integration, selected source rules, and retained owners."""
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
OUTPUT=ROOT/os.environ.get('V3_DAILY_TREE_BUILD','build/v3-shared-tree-daily-01')

class HostTests(unittest.TestCase):
    sanitized=shared.HostTests.sanitized
    def test_daily_growth_neighbours_death_and_acre_limits(self):self.sanitized('v3_tree_daily_test.c')

@unittest.skipUnless((OUTPUT/'build.json').is_file(),'Current daily tree cartridge required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((OUTPUT/'build.json').read_bytes());cls.base,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.e=cls.report['equipment_resources'];cls.r=cls.e['scenery'];cls.d=cls.r['daily_growth']
        cls.blob=cls.files[BLOB].extract(cls.rom);cls.oldblob=cls.before[BLOB].extract(cls.base)

    def test_complete_source_and_native_consumer_retention(self):
        d=self.d;v=d['vrom'];old=self.before[v].extract(self.base);data=self.files[v].extract(self.rom)
        rel=self.files[d['reloc']].extract(self.rom);oldrel=self.before[d['reloc']].extract(self.base)
        source=scenery.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        evidence,_,records,_=scenery.daily_contract(source,old,oldrel,self.before[CODE_VROM].extract(self.base))
        for k,value in evidence.items():self.assertEqual(json.loads(json.dumps(value)),d[k])
        for broken in (bytes([old[0]^1])+old[1:0x398]+bytes([old[0x398]^1])+old[0x399:],):
            with self.assertRaises(ValueError):scenery.daily_contract(source,broken,oldrel,self.before[CODE_VROM].extract(self.base))
        restored=bytearray(data)
        for p in d['patches']:
            self.assertEqual(u32(old,p['offset']),p['before']);self.assertEqual(u32(data,p['offset']),p['after'])
            struct.pack_into('>I',restored,p['offset'],p['before'])
        self.assertEqual(restored,old) # Includes every previous imported-house protection.
        expected=[v for v in records if v not in d['removed_relocations']]
        self.assertEqual(len(expected),u32(rel,16));self.assertEqual(rel[:16],oldrel[:16])
        self.assertEqual(struct.unpack_from('>'+str(len(expected))+'I',rel,20),tuple(expected))
        for ram in (0x80200010,0x80300010):
            moved=relocate_verified_data(SimpleNamespace(ram=d['ram'],resident_bytes=d['resident_bytes'],
                sections=struct.unpack_from('>5I',rel)),data,rel,ram)
            for p in d['patches']:self.assertEqual(u32(moved,p['offset']),p['after'])
        core=self.files[CODE_VROM].extract(self.rom);oldcore=self.before[CODE_VROM].extract(self.base)
        restored=bytearray(core)
        for h in d['core_hooks']:
            at=h['offset'];self.assertEqual(core[at:at+8].hex(),h['after']);self.assertEqual(oldcore[at:at+8].hex(),h['before'])
            restored[at:at+8]=oldcore[at:at+8]
        self.assertEqual(restored,oldcore)

    def test_owned_packet_bootstrap_and_unchanged_banks(self):
        old=self.prior['equipment_resources'];a=scenery.BOOT_RAM-old['ram'];b=scenery.BOOT_END-old['ram']
        start=old['blob_offset'];oldmod=self.oldblob[start:start+old['bytes']];newmod=self.blob[start:start+self.e['bytes']]
        self.assertEqual(newmod[:a],oldmod[:a]);self.assertEqual(newmod[b:],oldmod[b:])
        boot=(OUTPUT/'scenery_bootstrap/code.bin').read_bytes()
        self.assertEqual(newmod[a:b],boot+bytes(b-a-len(boot)));self.assertEqual(newmod[b-4:b],bytes(4))
        self.assertEqual(sha256(newmod),self.e['sha256']);self.assertEqual(old['bytes'],self.e['bytes'])
        code=(OUTPUT/'scenery/code.bin').read_bytes();start=self.r['blob_offset']
        self.assertEqual(self.blob[start:start+len(code)],code);self.assertLessEqual(len(code),8192)
        self.assertEqual(self.r['banks'],old['scenery']['banks'])
        for r in self.r['banks']:
            a,n=r['blob_offset'],r['bytes'];self.assertEqual(self.blob[a:a+n],self.oldblob[a:a+n])
        self.assertEqual(self.r['additional_fixed_resident_bytes'],8192)
        self.assertEqual(self.d['additional_resident_bytes'],4096)
        self.assertEqual(self.d['additional_scene_resident_bytes'],0)
        for row in self.r['owners']:
            olddata=self.before[row['vrom']].extract(self.base);data=self.files[row['vrom']].extract(self.rom);restored=bytearray(data)
            for p in row['patches']:
                self.assertEqual(u32(data,p['offset']),p['after']);self.assertEqual(u32(olddata,p['offset']),p['before'])
                struct.pack_into('>I',restored,p['offset'],p['before'])
            self.assertEqual(restored,olddata)
            self.assertEqual(self.files[row['reloc']].extract(self.rom),self.before[row['reloc']].extract(self.base))

    def test_patch_composition_and_unchanged_saves(self):
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
