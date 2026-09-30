"""Bounded scene-workspace control and exact current-cartridge installation."""
import json
from pathlib import Path
import subprocess
import struct
import sys
import tempfile
import unittest
import zlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,apply_ups,yaz0_decode
from v3_scene_arena import PLAY,PLAY_RAM,CODE,RELOC,PLAY_SHA,RELOC_SHA

class SceneArenaHostTests(unittest.TestCase):
    def test_exclusive_ownership_sentinel_and_guards(self):
        with tempfile.TemporaryDirectory(prefix='v3-scene-host-') as directory:
            exe=Path(directory)/'scene'
            subprocess.run(['cc','-std=c11','-O1','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                str(ROOT/'overlays/v3/scene_arena.c'),str(ROOT/'tests/fixtures/v3_scene_arena_host.c'),
                '-o',str(exe)],check=True,capture_output=True,timeout=30)
            result=subprocess.run([str(exe)],check=True,capture_output=True,text=True,timeout=10)
            self.assertIn('Exclusive scene ownership',result.stdout)

class SceneArenaCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out=ROOT/'build/v3-scene-arena-installed-03'
        pin=cls.out/'build-lock.json'
        if not pin.exists(): raise unittest.SkipTest('Current scene repair build is not available')
        cls.rom=(cls.out/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((cls.out/'build.json').read_bytes())
        cls.owner=cls.report['equipment_resources']['scene_arena']
        cls.base=(ROOT/'build/v3-private-save-bank-installed-06/animal-forest-v3-asset-loader.z64').read_bytes()
    def test_only_two_lifecycle_calls_change_and_relocations_remain(self):
        before=by_vrom(self.base)[PLAY].extract(self.base)
        after=bytearray(by_vrom(self.rom)[PLAY].extract(self.rom))
        self.assertEqual(sha256(before),PLAY_SHA)
        for row in self.owner['patches']:
            offset=row['address']-PLAY_RAM
            self.assertEqual(struct.unpack_from('>I',after,offset+4)[0],row['delay_slot'])
            struct.pack_into('>I',after,offset,row['before'])
        self.assertEqual(bytes(after),before)
        self.assertEqual(sha256(by_vrom(self.rom)[RELOC].extract(self.rom)),RELOC_SHA)
    def test_complete_packet_preserves_save_bank_and_fits_retained_code_extent(self):
        old=self.report['equipment_resources']['private_save_bank']
        packet=self.owner['packet']; at=packet['physical']
        raw=self.rom[at:at+packet['bytes']]
        self.assertEqual(sha256(raw),packet['sha256'])
        old_packet=json.loads((ROOT/'build/v3-private-save-bank-installed-06/build.json').read_bytes())['equipment_resources']['console_storage']['packet']
        previous=self.base[old_packet['physical']:old_packet['physical']+old_packet['bytes']]
        fixed=bytearray(raw);offset=CODE-packet['ram'];size=self.owner['code']['bytes']
        fixed[offset:offset+size]=bytes(size)
        self.assertEqual(fixed,previous)
        self.assertLessEqual(CODE+size,old['reservation']['ram']+old['reservation']['bytes'])
        self.assertEqual(self.owner['native_main_heap_end'],0x80400000)
        self.assertEqual(self.owner['workspace']['free_payload_bytes'],0x4FFB0)
    def test_patch_reconstructs_current_rom(self):
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        patch=(self.out/'asset-loader.ups').read_bytes()
        self.assertEqual(apply_ups(native,patch),self.rom)

@unittest.skipUnless((ROOT/'build/v3-import-pipeline-ordinary-save-03/results.json').is_file(),
                     'Current ordinary gameplay save output is required')
class OrdinarySaveChipTests(unittest.TestCase):
    def test_complete_actual_banks_profiles_and_imported_item(self):
        directory=ROOT/'build/v3-import-pipeline-ordinary-save-03'
        profile=json.loads((ROOT/'build/v3-import-pipeline-profile-06/profile.json').read_bytes())
        results=json.loads((directory/'results.json').read_bytes())
        self.assertEqual(results[0]['rom_sha256'],profile['output_sha256'])
        self.assertTrue(results[-1]['graceful_shutdown'])
        self.assertTrue(any(r.get('choice_count')==2 and r.get('choice_cursor')==0 for r in results))
        self.assertTrue(any(r.get('message_id')=='2B0D' and r.get('loaded')==1 for r in results))
        chip=(directory/'test.flash').read_bytes()
        self.assertEqual(len(chip),131072)
        self.assertEqual(chip[:65536],chip[65536:])
        for start in (0,65536):
            bank=chip[start:start+65536]; ext=bank[0xF980:]
            magic,version,registry,total,length,flags,crc,town_crc,console_crc,extra_crc=struct.unpack_from('>10I',ext)
            self.assertEqual((magic,version,registry,flags),(0x41465333,0x00150680,5,1))
            self.assertFalse(any(ext[40:]))
            seal=bytearray(bank);seal[18:20]=bytes(2);seal[0xF998:0xF99C]=bytes(4)
            self.assertEqual(zlib.crc32(seal),crc)
            self.assertEqual(sum(struct.unpack('>31936H',bank[:0xF980]))&65535,0)
            stream=bank[20:0x2F68]+bank[0x2F6A:0xF980]
            self.assertGreater(length,0);self.assertLessEqual(length,len(stream))
            self.assertFalse(any(stream[length:]))
            raw=yaz0_decode(b'Yaz0'+struct.pack('>I',total)+bytes(8)+stream[:length])
            self.assertEqual(len(raw),total)
            self.assertEqual(zlib.crc32(raw[:65536]),town_crc)
            self.assertEqual(zlib.crc32(raw[65536:72064]),console_crc)
            self.assertEqual(zlib.crc32(raw[72064:]),extra_crc)
            canonical=raw[0xF980:65536]
            self.assertEqual(struct.unpack_from('>3I',canonical),(0x41465333,0x00080680,5))
            expected=bytes.fromhex(profile['profile_hex'])
            self.assertEqual(canonical[0x18:0xB8],expected[:160])
            self.assertEqual(canonical[0x2C0:0x2E0],expected[160:192])
            self.assertEqual(canonical[0x4D0:0x4D4],bytes.fromhex(profile['creature_profile_hex']))
            self.assertEqual(raw[0x40C:0x40E],bytes.fromhex('2255'))

if __name__=='__main__':unittest.main()
