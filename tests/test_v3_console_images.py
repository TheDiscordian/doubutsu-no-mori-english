"""Focused cartridge allocation, preload, and private-composition checks."""
import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,apply_ups
from v3_asset_loader import BLOB,MODULE
from v3_furniture_install import inputs,owner_tail_storage
from v3_console_image_native import SOURCES
import v3_physical_resources as physical


class ConsoleImageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out=ROOT/'build/v3-console-images-native-01'
        cls.image,cls.report=inputs(cls.out/'build-lock.json')
        cls.base,cls.prior=inputs(cls.out/'base-lock.json')
        cls.images=cls.report['equipment_resources']['console_images']

    def test_installed_code_complete_pool_and_retained_resources(self):
        files=by_vrom(self.image);old=by_vrom(self.base);r=self.images;p=r['packet'];blob=files[BLOB].extract(self.image)
        data=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
        self.assertEqual(sha256(data),p['sha256']);self.assertEqual(zlib.crc32(data),p['crc32'])
        self.assertEqual(data[-16:],bytes.fromhex('AF4E4553')*4)
        self.assertEqual(sha256(data[:r['compiled']['bytes']]),r['compiled']['sha256'])
        m=r['metadata'];at=m['ram']-p['ram']
        self.assertEqual(sha256(data[at:at+m['bytes']]),m['sha256'])
        raw=r['pool'];pool=self.image[raw['physical']:raw['physical']+raw['bytes']]
        self.assertEqual(pool,(ROOT/'build/v3-console-games-prepared-06/games-pool.bin').read_bytes())
        self.assertEqual(sha256(pool),raw['sha256'])
        self.assertEqual(self.report['physical_resources'],[raw]);physical.verify(self.image,[raw])
        for path in SOURCES:self.assertEqual(r['sources'][path],sha256((ROOT/path).read_bytes()),path)
        self.assertEqual(set(files),set(old))
        for v in files:
            if v not in (BLOB,MODULE,0x19D40):self.assertEqual(files[v].extract(self.image),old[v].extract(self.base),hex(v))
        for key in ('console_storage','room_goods','room_carry'):
            self.assertEqual(self.report['equipment_resources'][key]['packet'],self.prior['equipment_resources'][key]['packet'])
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        self.assertEqual(self.report['automatic_furniture']['imports'],self.prior['automatic_furniture']['imports'])
        self.assertFalse(r['launch_installed']);self.assertEqual(r['choices_added'],0)
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (self.out/'asset-loader.ups').read_bytes()),self.image)

    def test_physical_reservations_reject_overlap_even_if_bytes_are_zero(self):
        files=by_vrom(self.image);p=self.images['pool'];bad=copy.deepcopy(p)
        bad['physical']=files[BLOB].pstart
        bad['sha256']=sha256(self.image[bad['physical']:bad['physical']+bad['bytes']])
        with self.assertRaises(ValueError):physical.verify(self.image,[bad])
        with self.assertRaises(ValueError):physical.verify(self.image,[p,p])
        # A zero-filled allocation still occupies space; appending an owner
        # must skip it rather than treating the bytes as free cartridge padding.
        highest=max(e.pend or e.pstart+e.size for e in files.values() if e.pstart!=0xFFFFFFFF)
        start=(highest+15)&~15;zero=dict(id='reserved-zero',physical=start,bytes=256,sha256=sha256(bytes(256)))
        physical.verify(self.image,[zero,p])
        row=owner_tail_storage(self.image,files,[(0x1060,b'x'*16)],reservations=[zero,p])[0]
        self.assertEqual(row['physical'],start+256)
        with self.assertRaises(ValueError):physical.allocate(self.image,[p],bytes(16),p['id'])
        bad=copy.deepcopy(p);bad['sha256']='0'*64
        with self.assertRaises(ValueError):physical.verify(self.image,[bad])

    def test_six_packet_preload_and_all_failure_paths(self):
        with tempfile.TemporaryDirectory(prefix='v3-console-images-startup-') as temp:
            binary=Path(temp)/'check'
            result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                '-DAF_TEST_CONSOLE=1','-DAF_TEST_CONSOLE_IMAGES=1',
                str(ROOT/'tests/v3_player_exercise_startup_test.c'),'-o',str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('six-packet startup',result.stdout)

    def test_private_composition_preserves_rom_only_resources(self):
        from tests.test_v3_room_rig_runtime import CurrentImportedRigTests
        self.rows=self.report['automatic_furniture']['imports']
        CurrentImportedRigTests.test_private_browser_selection_matches_offline_and_keeps_translation_only(self)


if __name__=='__main__':unittest.main()
