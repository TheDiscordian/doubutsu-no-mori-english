"""Shared owner integration; host/native distinction remains explicit."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,apply_ups,DMA_START
from v3_asset_loader import BLOB,MODULE
from v3_furniture_install import inputs
import v3_room_carry_native as native


class NativeCarrySourceTests(unittest.TestCase):
    def test_native_adapters_and_startup_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-carry-owner-') as directory:
            binary=Path(directory)/'test'
            args=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-ffp-contract=off',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                '-DAF_GOODS_ROTATE_LOW=0xEF000FD9u','-DAF_GOODS_ROTATE_HIGH=3u',
                'tests/v3_room_carry_native_test.c','overlays/v3/room_carry_native.c',
                'overlays/v3/room_carry.c','overlays/v3/room_goods.c','-lm','-o',str(binary)]
            result=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('cleanup, retry, and startup pass',result.stdout)


class NativeCarryInstalledTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out=ROOT/os.environ.get('V3_CARRY_BUILD','build/v3-room-carry-native-runtime-01')
        cls.image,cls.report=inputs(cls.out/'build-lock.json')
        cls.base,cls.prior=inputs(cls.out/'base-lock.json')
        cls.files=by_vrom(cls.image);cls.oldfiles=by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.image)

    def test_complete_installed_hooks_reservations_and_retained_resources(self):
        e=self.report['equipment_resources'];c=e['room_carry'];p=c['packet'];symbols=c['compiled']['symbols']
        packet=self.blob[p['blob_offset']:p['blob_offset']+p['bytes']]
        self.assertEqual(sha256(packet),p['sha256']);self.assertEqual(zlib.crc32(packet),p['crc32'])
        self.assertLessEqual(p['bytes'],8192);self.assertEqual(p['ram'],0x804DA000)
        self.assertEqual(c['state'],dict(ram=0x804DC400,bytes=1024,used=172,mutable=True,saved=False))
        self.assertTrue(c['installed'] and c['occupied_table_movement_enabled'])
        self.assertFalse(c['native_execution_tested'] or c['saved_format_changed'])
        owner=self.oldfiles[native.VROM].extract(self.base);reloc=self.oldfiles[native.RELOC].extract(self.base)
        patched,new_reloc,binding=native.patch_native(owner,reloc,symbols)
        self.assertEqual(self.files[native.VROM].extract(self.image),patched)
        self.assertEqual(self.files[native.RELOC].extract(self.image),new_reloc)
        self.assertEqual(len(binding['hooks']),12);self.assertEqual(len(binding['removed_relocations']),12)
        for row in binding['hooks']:
            bad=bytearray(owner);bad[row['address']-native.RAM]^=1
            with self.assertRaises(ValueError):native.patch_native(bad,reloc,symbols)
        self.assertEqual(self.report['shared_runtime_refresh']['additional_resident_bytes'],9216)
        for key in ('save_codec','save_runtime','furniture','translation_baseline','staged_furniture'):
            self.assertEqual(self.report[key],self.prior[key])
        self.assertEqual(e['room_rigs'],self.prior['equipment_resources']['room_rigs'])
        self.assertEqual(e['room_goods']['packet'],self.prior['equipment_resources']['room_goods']['packet'])
        boot=self.report['room_surfaces']['items']['bootstrap']['code'];at=e['blob_offset']+0x804A8D40-e['ram']
        self.assertEqual(sha256(self.blob[at:at+boot['bytes']]),boot['sha256'])
        self.assertLessEqual(boot['bytes'],688);self.assertLessEqual(self.report['startup']['bytes'],992)
        for key,value in [('VROM',p['vrom']),('CRC',p['crc32']),('BYTES',p['bytes'])]:
            self.assertIn(f'-DAF_ROOM_CARRY_{key}=0x{value:X}u',boot['flags'])
        for vrom,entry in self.oldfiles.items():
            if vrom<=DMA_START<entry.vend or vrom in (BLOB,MODULE,native.VROM,native.RELOC):continue
            self.assertEqual(self.files[vrom].extract(self.image),entry.extract(self.base),hex(vrom))
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (self.out/'asset-loader.ups').read_bytes()),self.image)

    def test_private_browser_optional_composition(self):
        from tests.test_v3_room_rig_runtime import CurrentImportedRigTests
        self.rows=self.report['automatic_furniture']['imports']
        CurrentImportedRigTests.test_private_browser_selection_matches_offline_and_keeps_translation_only(self)


if __name__=='__main__':unittest.main()
