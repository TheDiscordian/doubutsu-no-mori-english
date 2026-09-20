"""Current seasonal bank installation, complete source graphs, and lifetime bounds."""
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

OUTPUT=ROOT/os.environ.get('V3_SCENERY_BUILD','build/v3-shared-scenery-04')

class HostTests(unittest.TestCase):
    sanitized=shared.HostTests.sanitized
    def test_owner_lifetimes_selection_palettes_and_failure_bounds(self): self.sanitized('v3_scenery_test.c')

@unittest.skipUnless((OUTPUT/'build.json').is_file(),'Current scenery cartridge required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((OUTPUT/'build.json').read_bytes())
        cls.base,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.rom);cls.oldblob=cls.before[BLOB].extract(cls.base)
        cls.e=cls.report['equipment_resources'];cls.r=cls.e['scenery']

    def test_complete_prepared_banks_every_declared_pointer_and_storage(self):
        source=scenery.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        art,assets,palette,evidence=scenery.prepared(source,ROOT/self.r['art_directory'])
        self.assertEqual(evidence['art_report_sha256'],self.r['art_report_sha256'])
        wrapper=(OUTPUT/'palette/palette.bin').read_bytes()
        self.assertEqual(len(self.r['reservations']),3)
        for r in self.r['banks']:
            data,want=scenery.pack_bank(art,assets,palette,r['season'],wrapper)
            self.assertEqual(self.blob[r['blob_offset']:r['blob_offset']+r['bytes']],data)
            self.assertEqual(r['sha256'],sha256(data));self.assertEqual(r['crc32'],zlib.crc32(data))
            self.assertEqual(len(data),32864)
            h=struct.unpack_from('>32I',data); locations=set()
            for kind in (4,6,8):
                step=8 if kind==8 else 4
                for i in range(h[kind+1]):
                    at=u32(data,h[kind]+i*step)
                    self.assertNotIn(at,locations);locations.add(at)
                    self.assertEqual(at%4,0);self.assertTrue(128<=at<len(data)-3)
                    target=u32(data,at)
                    if kind==8: self.assertEqual(target,0);self.assertIn(u32(data,h[kind]+i*8+4),(0,1))
                    else: self.assertTrue(128<=target<len(data));self.assertEqual(target%4,0)
            for i in range(h[13]):
                fg,word,p,q=struct.unpack_from('>4I',data,h[12]+16*i)
                self.assertIn(f'{fg:04X}',r['foreground_ids']);self.assertLess(word,10)
                self.assertTrue(p+64<=len(data) and q+64<=len(data))
            self.assertEqual(data[h[14]:h[14]+448],palette)
        for space in self.r['reservations']:
            at,n=space['blob_offset'],space['bytes']
            self.assertEqual(sha256(self.oldblob[at:at+n]),space['retired_module_sha256'])
            self.assertEqual(sha256((ROOT/space['predecessor_report']).read_bytes()),space['predecessor_report_sha256'])
        self.assertEqual(len({r['vrom'] for r in self.r['banks']}),3)
        from v3_equipment_runtime import retired_module_space
        next_space=retired_module_space(self.rom,self.report,self.blob,32768)
        if next_space:
            a=next_space['blob_offset'];b=a+next_space['bytes']
            for used in self.r['reservations']:
                self.assertFalse(a<used['blob_offset']+used['bytes'] and used['blob_offset']<b)

    def test_overlay_allocation_relocation_and_exact_retained_code(self):
        core=self.files[CODE_VROM].extract(self.rom);oldcore=self.before[CODE_VROM].extract(self.base)
        restored=bytearray(core)
        for r in self.r['owners']:
            old=self.before[r['vrom']].extract(self.base);data=self.files[r['vrom']].extract(self.rom)
            rel=self.files[r['reloc']].extract(self.rom);oldrel=self.before[r['reloc']].extract(self.base)
            copy=bytearray(data)
            for p in r['patches']:
                self.assertEqual(u32(old,p['offset']),p['before']);self.assertEqual(u32(data,p['offset']),p['after'])
                struct.pack_into('>I',copy,p['offset'],p['before'])
            self.assertEqual(copy,old);self.assertEqual(len(data),len(old))
            self.assertEqual(rel[:12],oldrel[:12]);self.assertEqual(rel[16:],oldrel[16:])
            self.assertEqual(sum(struct.unpack_from('>4I',rel)),r['resident_bytes'])
            at=r['allocation_descriptor']-CODE_RAM+12
            self.assertEqual(u32(core,at),r['ram']+r['resident_bytes']);restored[at:at+4]=oldcore[at:at+4]
            for ram in (0x80200010,0x80300010):
                moved=relocate_verified_data(SimpleNamespace(ram=r['ram'],resident_bytes=r['resident_bytes'],
                    sections=struct.unpack_from('>5I',rel)),data,rel,ram)
                self.assertEqual(moved[len(data):],bytes(r['resident_bytes']-len(data)))
                self.assertEqual(u32(moved,0x47A8),u32(data,0x47A8))
                self.assertEqual(u32(moved,u32(rel,0)+16),self.r['bootstrap']['symbols']['af_v3_scenery_'+r['role']])
        self.assertEqual(restored,oldcore)
        old=self.prior['equipment_resources'];start=old['blob_offset']
        original=self.oldblob[start:start+old['bytes']];current=self.blob[start:start+self.e['bytes']]
        boot=scenery.BOOT_RAM-self.e['ram'];n=self.r['bootstrap']['bytes']
        self.assertEqual(current[:boot],original[:boot]);self.assertEqual(current[boot+n:],original[boot+n:])
        self.assertEqual(current[boot:boot+n],(OUTPUT/'scenery_bootstrap/code.bin').read_bytes())
        self.assertEqual(sha256(current),self.e['sha256']);self.assertEqual(zlib.crc32(current),self.e['crc32'])
        self.assertEqual(self.e['bytes'],old['bytes'])

    def test_patch_retention_profiles_and_no_public_changes(self):
        self.assertEqual(sha256(self.rom),self.report['output_sha256'])
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(original,(OUTPUT/'asset-loader.ups').read_bytes()),self.rom)
        changed={BLOB,MODULE,CODE_VROM,0x19D40}|{r[k] for r in self.r['owners'] for k in ('vrom','reloc')}
        self.assertEqual(self.before.keys(),self.files.keys())
        for v,f in self.before.items():
            if v not in changed:self.assertEqual(f.extract(self.base),self.files[v].extract(self.rom),hex(v))
        self.assertEqual(self.prior['save_runtime']['profile_hex'],self.report['save_runtime']['profile_hex'])
        self.assertFalse(self.report['shared_runtime_refresh']['saved_format_changed'])
        self.assertFalse(self.r['selectable']);self.assertFalse(self.r['acquisition_installed'])
        for path in scenery.SOURCES:self.assertEqual(sha256((ROOT/path).read_bytes()),self.report['sources'][path])
        from text_provenance import validate
        catalogue=json.loads((ROOT/'translations/provenance.json').read_bytes());validate(catalogue)
        diagnostics=[e['locales']['en'] for e in catalogue['entries'] if e['id'].startswith('v3/scenery/diagnostic/')]
        self.assertEqual(len(diagnostics),5)
        for row in diagnostics:
            self.assertEqual(row['credit'],'assistant')
            self.assertEqual(row['encoded_sha256'],sha256(row['text'].encode()))
        self.assertLessEqual(self.r['code']['bytes'],4096)
        self.assertLessEqual(self.r['bootstrap']['bytes'],scenery.BOOT_END-scenery.BOOT_RAM)
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
