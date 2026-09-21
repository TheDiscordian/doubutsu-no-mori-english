"""Changed surface readers/resources; preserve earlier unrelated native evidence."""
import json
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
from v3_import_storage import ROWS,TABLE_END
from v3_room_surfaces import KINDS
from v3_surface_runtime import OWNERS,patch_owner
from v3_npc_draw import relocation_offsets
import v3_optional_composition as composer

OUT=ROOT/'build/v3-room-surfaces-runtime-02'


class SurfaceRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUT/'build-lock.json')
        cls.base,cls.prior=inputs(OUT/'base-lock.json')
        cls.files=by_vrom(cls.image);cls.oldfiles=by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.image);cls.old=cls.oldfiles[BLOB].extract(cls.base)
        cls.surface=cls.report['room_surfaces']

    def test_complete_assets_existing_banks_and_unchanged_memory(self):
        rows=self.surface['rows'];self.assertEqual(len(rows),10)
        self.assertEqual(self.report['blob_bytes']-self.prior['blob_bytes'],61760)
        self.assertEqual(self.surface['additional_resident_bytes'],0)
        self.assertEqual(self.surface['additional_scene_bytes'],0)
        art=ROOT/self.surface['preparation']
        for row in rows:
            a=row['blob_offset'];raw=self.blob[a:a+row['bytes']]
            self.assertEqual(raw,(art/(row['source_item_id']+'.surface.bin')).read_bytes())
            self.assertEqual(sha256(raw),row['converted_sha256'])
            self.assertTrue(row['room_texture_installed']);self.assertFalse(row['selectable'])
            self.assertEqual(row['vrom'],BLOB+a)
        for kind,bank in zip(KINDS,self.surface['banks']):
            self.assertEqual(self.files[kind['vrom']].extract(self.image),self.oldfiles[kind['vrom']].extract(self.base))
            self.assertEqual((bank['first'],bank['count'],bank['stride']),(73,5,kind['stride']))
            a=bank['blob_offset'];self.assertEqual(sha256(self.blob[a:a+bank['bytes']]),bank['sha256'])
        self.assertFalse(self.surface['application_and_persistence_installed'])
        self.assertFalse(self.surface['catalogue_texture_reader_installed'])

    def test_complete_owner_patches_relocation_removal_and_mutation_rejection(self):
        for owner,record in zip(OWNERS,self.surface['owners']):
            vrom,rel,ram,start,part,*_=owner
            before=self.oldfiles[vrom].extract(self.base);reloc=self.oldfiles[rel].extract(self.base)
            code=(OUT/part/'code.bin').read_bytes()
            new,fixed,receipt=patch_owner(before,reloc,owner,code,record['compiled'])
            self.assertEqual(receipt,record)
            self.assertEqual(self.files[vrom].extract(self.image),new)
            self.assertEqual(self.files[rel].extract(self.image),fixed)
            self.assertEqual(new[:start],before[:start]);self.assertEqual(new[start+0x230:],before[start+0x230:])
            self.assertFalse(relocation_offsets(fixed,len(new))&set(range(start,start+0x230,4)))
            self.assertEqual(len(relocation_offsets(reloc,len(new)))-len(relocation_offsets(fixed,len(new))),8)
            bad=bytearray(before);bad[start+40]^=1
            with self.assertRaisesRegex(ValueError,'complete native surface'):patch_owner(bad,reloc,owner,code,record['compiled'])
            bad=bytearray(reloc);bad[24]^=1
            with self.assertRaisesRegex(ValueError,'complete native surface'):patch_owner(before,bad,owner,code,record['compiled'])
            self.assertLessEqual(record['compiled']['bytes'],0x230)
            self.assertEqual(record['compiled']['symbols']['af_v3_surface_wall'],ram+start+0x118)

    def test_actual_c_under_memory_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-room-surfaces-') as temporary:
            binary=Path(temporary)/'test'
            result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_room_surfaces_test.c'),'-o',str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('unchanged actor state pass',result.stdout)

    def test_existing_profiles_and_empty_all_composition_are_retained(self):
        self.assertEqual(self.blob[ROWS:TABLE_END],self.old[ROWS:TABLE_END])
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        self.assertEqual(self.report['staged_furniture'],self.prior['staged_furniture'])
        self.assertEqual(self.report['equipment_resources'],self.prior['equipment_resources'])
        self.assertFalse(self.report['shared_runtime_refresh']['saved_profile_changed'])
        self.assertFalse(self.report['shared_runtime_refresh']['web_patcher_enabled'])
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(OUT/'build-lock.json');catalog=composer.catalogue(self.image,self.report)
            self.assertEqual(len(catalog),141)
            self.assertFalse({r['id'] for r in self.surface['rows']}&set(catalog))
            self.assertEqual(sha256(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,[]))[0]),
                self.report['translation_baseline']['sha256'])
            self.assertEqual(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,list(catalog)))[0],self.image)
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (OUT/'asset-loader.ups').read_bytes()),self.image)


if __name__=='__main__':unittest.main()
