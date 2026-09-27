"""Shared disk preload, reservation safety, and retained current cartridge."""
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
from v3_furniture_install import inputs
from v3_console_disk_install import RAM,END,LAYOUT,SOURCES,install,packet


class ConsoleDiskInstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out=ROOT/'build/v3-console-disk-resident-01'
        cls.image,cls.report=inputs(cls.out/'build-lock.json')
        cls.base,cls.prior=inputs(cls.out/'base-lock.json')
        cls.prepared=ROOT/'build/v3-console-games-prepared-14'

    def test_complete_packet_and_unchanged_game_resources(self):
        files=by_vrom(self.image);old=by_vrom(self.base);e=self.report['equipment_resources']
        disk=e['console_disk'];p=disk['packet'];blob=files[BLOB].extract(self.image)
        raw=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
        expected,prepared=packet(self.prepared)
        self.assertEqual(raw,expected);self.assertEqual(disk['prepared'],prepared)
        self.assertEqual(sha256(raw),p['sha256']);self.assertEqual(zlib.crc32(raw),p['crc32'])
        self.assertEqual((p['ram'],p['bytes']),(RAM,END-RAM))
        self.assertEqual(disk['layout'],LAYOUT)
        for name in ('context','program','characters'):
            region=LAYOUT[name];at=region['ram']-RAM
            self.assertEqual(raw[at:at+region['bytes']],bytes(region['bytes']))
        self.assertEqual(raw[-16:],bytes.fromhex('51444721')*4)
        for path in SOURCES:self.assertEqual(disk['sources'][path],sha256((ROOT/path).read_bytes()),path)
        flags=e['surface_bootstrap']['code']['flags']
        for key,value in [('VROM',p['vrom']),('CRC',p['crc32']),('BYTES',p['bytes'])]:
            self.assertIn(f'-DAF_CONSOLE_DISK_{key}=0x{value:X}u',flags)
        self.assertLessEqual(disk['startup']['bytes'],disk['startup']['capacity'])
        self.assertFalse(disk['session_hooks_installed']);self.assertFalse(disk['choice_eligible'])
        self.assertFalse(disk['save_format_changed'])
        self.assertEqual(set(files),set(old))
        for v in files:
            if v not in (BLOB,MODULE,0x19D40):
                self.assertEqual(files[v].extract(self.image),old[v].extract(self.base),hex(v))
        for key in ('console_storage','console_images','room_goods','room_carry'):
            self.assertEqual(e[key]['packet'],self.prior['equipment_resources'][key]['packet'])
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        self.assertEqual(self.report['automatic_furniture']['imports'],self.prior['automatic_furniture']['imports'])
        self.assertEqual(self.report['physical_resources'],self.prior['physical_resources'])
        for row in self.report['physical_resources']:
            self.assertEqual(self.image[row['physical']:row['physical']+row['bytes']],
                             self.base[row['physical']:row['physical']+row['bytes']])
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (self.out/'asset-loader.ups').read_bytes()),self.image)

    def test_overlap_rejects_before_blob_mutation(self):
        raw=by_vrom(self.base)[BLOB].extract(self.base)
        for region in (dict(ram=RAM-16,bytes=32),dict(start=END-16,end=END+16)):
            prior=copy.deepcopy(self.prior);prior['equipment_resources']['future_resource']=region
            blob=bytearray(raw)
            with self.assertRaisesRegex(ValueError,'overlaps retained resident memory'):
                install(self.base,prior,blob,self.out,self.prepared)
            self.assertEqual(blob,raw)

    def test_seven_packet_preload_and_all_failure_paths(self):
        with tempfile.TemporaryDirectory(prefix='v3-console-disk-startup-') as temp:
            binary=Path(temp)/'check'
            run=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                '-DAF_TEST_CONSOLE=1','-DAF_TEST_CONSOLE_IMAGES=1','-DAF_TEST_CONSOLE_DISK=1',
                str(ROOT/'tests/v3_player_exercise_startup_test.c'),'-o',str(binary)],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertIn('seven-packet startup',run.stdout)

    def test_private_composition_preserves_disk_packet(self):
        from tests.test_v3_room_rig_runtime import CurrentImportedRigTests
        self.rows=self.report['automatic_furniture']['imports']
        CurrentImportedRigTests.test_private_browser_selection_matches_offline_and_keeps_translation_only(self)


if __name__=='__main__':unittest.main()
