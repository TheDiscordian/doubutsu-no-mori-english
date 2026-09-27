"""Changed format-five integration checks; no hardware claim."""
import copy
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,DMA_START,DMA_END,by_vrom,sha256,apply_ups
from v3_asset_loader import BLOB,MODULE,CONFIG,STARTUP
from v3_furniture_install import inputs
from v3_console_storage import SOURCES


class ConsoleStorageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out=ROOT/'build/v3-console-storage-native-04'
        cls.image,cls.report=inputs(cls.out/'build-lock.json')
        cls.base,cls.prior=inputs(cls.out/'base-lock.json')
        cls.storage=cls.report['equipment_resources']['console_storage']

    def test_host_native_adapter_state_and_io_order(self):
        with tempfile.TemporaryDirectory(prefix='v3-console-native-save-') as temp:
            out=Path(temp);flags=['-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fno-pie','-no-pie','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-DAF_V3_CLOTHING_PROFILE=1','-DAF_V3_REWARD_PROFILE=1','-DAF_V3_SURFACE_PROFILE=1']
            run=subprocess.run(['cc',*flags,'-Daf_v3_save_check=af_console_canonical_check',
                '-Daf_v3_save_pack=af_console_canonical_pack','-Daf_v3_save_collect=af_console_canonical_collect',
                '-c',str(ROOT/'overlays/v3/save_codec.c'),'-o',str(out/'codec.o')],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            run=subprocess.run(['cc',*flags,'-DAF_V3_CONSOLE_STORAGE=1',
                *[str(ROOT/p) for p in ('tests/v3_console_storage_test.c','overlays/v3/save_runtime.c',
                   'overlays/v3/console_storage.c','overlays/v3/save_compressed.c')],
                str(out/'codec.o'),'-o',str(out/'check')],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            run=subprocess.run([str(out/'check')],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr);print(run.stdout.strip())

    def test_installed_packets_dispatch_and_unchanged_resources(self):
        r=self.storage;files=by_vrom(self.image);before=by_vrom(self.base);blob=files[BLOB].extract(self.image)
        p=r['packet'];raw=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
        self.assertEqual(sha256(raw),p['sha256']);self.assertEqual(zlib.crc32(raw),p['crc32'])
        self.assertEqual(raw[-16:],bytes.fromhex('AF4355DE')*4)
        self.assertLessEqual(p['ram']+p['bytes'],r['scratch']['ram'])
        self.assertLessEqual(r['scratch']['guard']+16,r['hash']['ram'])
        self.assertLessEqual(r['hash']['guard']+16,self.report['furniture']['bank_pool']['start'])
        for path in SOURCES:self.assertEqual(sha256((ROOT/path).read_bytes()),r['sources'][path],path)
        for row in r['stable_runtime_dispatch']+r['codec_entries'][:2]:
            address=row.get('address') or int(row['entry'],16);at=address-0x80460000
            self.assertEqual(blob[at:at+8].hex(),row['after'])
        core=files[CODE_VROM].extract(self.image);at=r['player_clear']['address']-CODE_RAM
        self.assertEqual(core[at:at+8].hex(),r['player_clear']['after'])
        old_core=before[CODE_VROM].extract(self.base)
        self.assertEqual(core[:at],old_core[:at]);self.assertEqual(core[at+8:],old_core[at+8:])
        # Growth moves three retained resources and updates the blob extent.
        # Check the directory fields individually, not as unrelated game data.
        self.assertEqual(set(files),set(before))
        for v in files:
            self.assertEqual(files[v].vstart,before[v].vstart)
            if v!=BLOB:self.assertEqual(files[v].vend,before[v].vend)
            if v not in (BLOB,CODE_VROM,MODULE,0x19D40):
                self.assertEqual(files[v].extract(self.image),before[v].extract(self.base),hex(v))
        directory=files[0x19D40].extract(self.image);old_directory=before[0x19D40].extract(self.base)
        self.assertEqual(directory[:DMA_START-0x19D40],old_directory[:DMA_START-0x19D40])
        self.assertEqual(directory[DMA_END-0x19D40:],old_directory[DMA_END-0x19D40:])
        module=files[MODULE].extract(self.image);old_module=before[MODULE].extract(self.base)
        self.assertEqual(module[:STARTUP],old_module[:STARTUP]);self.assertEqual(module[CONFIG+16:],old_module[CONFIG+16:])
        self.assertEqual(sha256(module[STARTUP:STARTUP+self.report['startup']['bytes']]),self.report['startup']['sha256'])
        self.assertEqual(struct.unpack_from('>4I',module,CONFIG),(BLOB,0xC000,zlib.crc32(blob[:0xC000]),self.report['runtime_abi']))
        e=self.report['equipment_resources'];old_e=self.prior['equipment_resources']
        for key in ('room_goods','room_carry'):
            self.assertEqual(e[key]['packet'],old_e[key]['packet'])
        self.assertEqual(e['player_motion']['exercise']['native']['packet'],old_e['player_motion']['exercise']['native']['packet'])
        self.assertEqual(self.report['save_codec']['format_version'],5)
        self.assertEqual(self.report['save_runtime']['state_bytes'],1232)
        self.assertEqual(self.report['automatic_furniture']['imports'],self.prior['automatic_furniture']['imports'])
        self.assertIn('format-1/2/3/4',self.report['save_warning'])
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                                  (self.out/'asset-loader.ups').read_bytes()),self.image)

    def test_five_packet_preload_success_and_rejection(self):
        with tempfile.TemporaryDirectory(prefix='v3-console-preload-') as temp:
            binary=Path(temp)/'check'
            result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                '-DAF_TEST_CONSOLE=1',str(ROOT/'tests/v3_player_exercise_startup_test.c'),'-o',str(binary)],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('five-packet startup',result.stdout)

    def test_current_private_compositions(self):
        from tests.test_v3_room_rig_runtime import CurrentImportedRigTests
        self.rows=self.report['automatic_furniture']['imports']
        CurrentImportedRigTests.test_private_browser_selection_matches_offline_and_keeps_translation_only(self)


if __name__=='__main__':unittest.main()
