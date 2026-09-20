"""Shared planting/state integration; keep unchanged scenery evidence separate."""
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
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,apply_ups,u32
from v3_asset_loader import BLOB,MODULE
from v3_furniture_install import inputs
from npc_mail_show import relocate_verified_data
import v3_scenery_runtime as scenery
import tests.test_v3_equipment_runtime as shared

OUTPUT=ROOT/os.environ.get('V3_TREE_BUILD','build/v3-shared-tree-states-02')

class HostTests(unittest.TestCase):
    sanitized=shared.HostTests.sanitized
    def test_growth_stumps_selection_and_planting_bounds(self): self.sanitized('v3_tree_states_test.c')

@unittest.skipUnless((OUTPUT/'build.json').is_file(),'Current tree-state cartridge required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((OUTPUT/'build.json').read_bytes())
        cls.base,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.rom);cls.oldblob=cls.before[BLOB].extract(cls.base)
        cls.e=cls.report['equipment_resources'];cls.r=cls.e['scenery'];cls.t=cls.r['tree_states']

    def test_actual_donor_rules_and_complete_cartridge_bindings(self):
        source=scenery.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        self.assertEqual(json.loads(json.dumps(scenery.tree_rules(source))),self.t['source'])
        core=self.files[CODE_VROM].extract(self.rom);oldcore=self.before[CODE_VROM].extract(self.base)
        restored=bytearray(core)
        for r in self.t['core_consumers']:
            at=r['start']-CODE_RAM
            self.assertEqual(sha256(oldcore[at:r['end']-CODE_RAM]),r['sha256'])
            self.assertEqual(core[at:at+8].hex(),r['after'])
            self.assertEqual(oldcore[at:at+8].hex(),r['before']);restored[at:at+8]=oldcore[at:at+8]
        self.assertEqual(restored,oldcore)
        for r,p in zip(self.r['owners'],self.t['planting'],strict=True):
            old=self.before[r['vrom']].extract(self.base);data=self.files[r['vrom']].extract(self.rom)
            rel=self.files[r['reloc']].extract(self.rom);oldrel=self.before[r['reloc']].extract(self.base)
            restored=bytearray(data)
            for patch in r['patches']:
                at=patch['offset'];self.assertEqual(u32(data,at),patch['after']);self.assertEqual(u32(old,at),patch['before'])
                struct.pack_into('>I',restored,at,patch['before'])
            self.assertEqual(restored,old)
            self.assertEqual(sha256(data[p['entry']:p['end']]),p['native_sha256'])
            count=u32(oldrel,16);records=struct.unpack_from('>'+str(count)+'I',oldrel,20)
            want=[v for v in records if v not in p['removed_relocations']]
            self.assertEqual(rel[:16],oldrel[:16]);self.assertEqual(u32(rel,16),len(want))
            self.assertEqual(struct.unpack_from('>'+str(len(want))+'I',rel,20),tuple(want))
            for location in (0x80200010,0x80300010):
                moved=relocate_verified_data(SimpleNamespace(ram=r['ram'],resident_bytes=r['resident_bytes'],
                    sections=struct.unpack_from('>5I',rel)),data,rel,location)
                for at in p['calls']+[0x47A8,u32(rel,0)+16]: self.assertEqual(u32(moved,at),u32(data,at))
        self.assertEqual(len(self.t['planting']),4)

    def test_packet_bootstrap_cache_guards_and_existing_resources(self):
        old=self.prior['equipment_resources'];start=old['blob_offset']
        original=self.oldblob[start:start+old['bytes']];current=self.blob[start:start+self.e['bytes']]
        a=scenery.BOOT_RAM-self.e['ram'];b=scenery.BOOT_END-self.e['ram']
        self.assertEqual(current[:a],original[:a]);self.assertEqual(current[b:],original[b:])
        boot=(OUTPUT/'scenery_bootstrap/code.bin').read_bytes()
        self.assertEqual(current[a:b],boot+bytes(b-a-len(boot)))
        self.assertEqual(current[b-4:b],bytes(4))
        for address,words in ((0x804ADFC0,(0xAFA40000,0x3084FFFF,0x0802965E,0)),
                              (0x804ADFD0,(0xAFA50004,0x00052C00,0x080295BE,0))):
            self.assertEqual(current[address-self.e['ram']:address-self.e['ram']+16],struct.pack('>4I',*words))
        self.assertEqual(sha256(current),self.e['sha256']);self.assertEqual(zlib.crc32(current),self.e['crc32'])
        self.assertEqual(self.e['bytes'],old['bytes']);self.assertEqual(self.r['additional_fixed_resident_bytes'],4096)
        self.assertEqual(self.t['additional_resident_bytes'],0);self.assertLessEqual(self.r['bytes'],4096)
        self.assertEqual(self.blob[self.r['blob_offset']:self.r['blob_offset']+self.r['bytes']],
            (OUTPUT/'scenery/code.bin').read_bytes())
        self.assertEqual(self.r['banks'],old['scenery']['banks'])
        for r in self.r['banks']:
            at,n=r['blob_offset'],r['bytes'];self.assertEqual(self.blob[at:at+n],self.oldblob[at:at+n])

    def test_patch_choices_native_retention_and_no_new_save_format(self):
        self.assertEqual(sha256(self.rom),self.report['output_sha256'])
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(original,(OUTPUT/'asset-loader.ups').read_bytes()),self.rom)
        changed={BLOB,MODULE,CODE_VROM,0x19D40}|{r[k] for r in self.r['owners'] for k in ('vrom','reloc')}
        self.assertEqual(self.before.keys(),self.files.keys())
        for v,f in self.before.items():
            if v not in changed:self.assertEqual(f.extract(self.base),self.files[v].extract(self.rom),hex(v))
        for key in ('save_runtime','save_codec','furniture','catalogue'):
            self.assertEqual(self.report[key],self.prior[key])
        self.assertFalse(self.report['shared_runtime_refresh']['saved_format_changed'])
        self.assertEqual(self.report['shared_runtime_refresh']['additional_resident_bytes'],0)
        self.assertFalse(self.r['selectable']);self.assertFalse(self.r['acquisition_installed'])
        self.assertFalse(self.t['daily_growth_owner_installed']);self.assertFalse(self.t['shake_drop_installed'])
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

if __name__=='__main__': unittest.main()
