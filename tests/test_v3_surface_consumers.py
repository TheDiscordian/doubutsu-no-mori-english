"""Secondary surface consumers and their retention through future bulk imports."""
import copy
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,apply_ups
from v3_asset_loader import BLOB
from v3_furniture_install import inputs
from v3_surface_runtime import SECONDARY,OWNERS,patch_owner,arrange_bounds,retain_catalogue,reader_layout
import v3_optional_composition as composer

OUT=ROOT/'build/v3-surface-consumers-runtime-01'


class SurfaceConsumersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUT/'build-lock.json')
        cls.base,cls.prior=inputs(OUT/'base-lock.json')
        cls.files=by_vrom(cls.image);cls.oldfiles=by_vrom(cls.base)
        cls.surface=cls.report['room_surfaces']

    def test_bounded_owners_and_original_constructor_fallback(self):
        for owner,record in zip(SECONDARY,self.surface['secondary_owners']):
            vrom,rel,ram,start,part,*_=owner;stride,_,_=reader_layout(owner)
            before=self.oldfiles[vrom].extract(self.base);reloc=self.oldfiles[rel].extract(self.base)
            code=(OUT/part/'code.bin').read_bytes()
            new,fixed,receipt=patch_owner(before,reloc,owner,code,record['compiled'])
            if part=='surface_arrange':
                new,receipt['bounds']=arrange_bounds(new,fixed);receipt['sha256']=sha256(new)
                self.assertEqual((receipt['bounds']['original_count'],receipt['bounds']['additive_first'],
                    receipt['bounds']['additive_count'],receipt['bounds']['missing_fallback']),(64,73,5,63))
                bad=bytearray(before);bad[0x154]^=1
                with self.assertRaisesRegex(ValueError,'complete arranged-room'):arrange_bounds(bad,reloc)
            self.assertEqual(receipt,record);self.assertEqual(new,self.files[vrom].extract(self.image))
            self.assertEqual(fixed,self.files[rel].extract(self.image))
            allowed=set(range(start,start+2*stride))|(set(range(0x1B0,0x1F8)) if part=='surface_arrange' else set())
            self.assertTrue(all(i in allowed or a==b for i,(a,b) in enumerate(zip(before,new))))
            bad=bytearray(before);bad[start+4]^=1
            with self.assertRaisesRegex(ValueError,'complete native surface'):patch_owner(bad,reloc,owner,code,record['compiled'])
            self.assertLessEqual(len(code),stride*2)
        self.assertEqual(self.report['catalogue']['output_sha256'],sha256(self.files[0x3970000].extract(self.image)))
        self.assertEqual(self.report['catalogue']['relocation_sha256'],sha256(self.files[0x3980000].extract(self.image)))

    def test_same_assets_and_passing_double_buffer_code_are_reused(self):
        self.assertEqual(self.report['blob_bytes'],self.prior['blob_bytes'])
        self.assertEqual(self.surface['banks'],self.prior['room_surfaces']['banks'])
        self.assertEqual(self.surface['rows'],self.prior['room_surfaces']['rows'])
        for owner in OWNERS:
            for vrom in owner[:2]:self.assertEqual(self.files[vrom].extract(self.image),self.oldfiles[vrom].extract(self.base))
        blob=self.files[BLOB].extract(self.image);old=self.oldfiles[BLOB].extract(self.base)
        for bank in self.surface['banks']:
            at=bank['blob_offset'];self.assertEqual(blob[at:at+bank['bytes']],old[at:at+bank['bytes']])
        self.assertFalse(self.report['shared_runtime_refresh']['artwork_changed'])
        self.assertEqual(self.surface['additional_resident_bytes'],0)
        self.assertEqual(self.surface['additional_scene_bytes'],0)

    def test_actual_consumer_c_under_memory_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-surface-consumers-') as temporary:
            binary=Path(temporary)/'test'
            result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_surface_consumers_test.c'),'-o',str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('price queries, missing IDs, and guards pass',result.stdout)

    def test_fresh_catalogue_rebuild_retains_checked_surface_reader(self):
        data=self.oldfiles[0x3970000].extract(self.base);rel=self.oldfiles[0x3980000].extract(self.base)
        fixed,relocated,receipt=retain_catalogue(self.report,self.image,data,rel)
        self.assertEqual(fixed,self.files[0x3970000].extract(self.image))
        self.assertEqual(relocated,self.files[0x3980000].extract(self.image))
        self.assertEqual(receipt['code_sha256'],self.report['catalogue']['surface_preview_code_sha256'])
        bad=bytearray(data);bad[0x754]^=1
        with self.assertRaisesRegex(ValueError,'complete native surface'):retain_catalogue(self.report,self.image,bad,rel)
        self.assertEqual(retain_catalogue(self.prior,self.base,data,rel),(data,rel,None))

    def test_profiles_saves_and_translation_only_remain_unchanged(self):
        for key in ('save_runtime','staged_furniture','equipment_resources'):
            self.assertEqual(self.report[key],self.prior[key])
        self.assertFalse(self.surface['selectable']);self.assertFalse(self.surface['application_and_persistence_installed'])
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(OUT/'build-lock.json');catalog=composer.catalogue(self.image,self.report)
            self.assertEqual(len(catalog),141)
            self.assertFalse({r['id'] for r in self.surface['rows']}&set(catalog))
            self.assertEqual(sha256(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,[]))[0]),self.report['translation_baseline']['sha256'])
            self.assertEqual(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,list(catalog)))[0],self.image)
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),(OUT/'asset-loader.ups').read_bytes()),self.image)


if __name__=='__main__':unittest.main()
