"""Format-4 surface selection/ownership, existing ABI, and focused safety."""
import copy
import ctypes as c
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,apply_ups
from v3_asset_loader import BLOB,MODULE
from v3_furniture_install import inputs
from v3_surface_save import SIZE,STATE_BYTES,WORKING_BYTES,SOURCES,DEFINES
from v3_surface_items import RAM,BOOT,BOOT_END
from tests import test_v3_save_rewards as rewards
from tests import test_v3_save_codec as legacy
import v3_optional_composition as composer

OUT=ROOT/'build/v3-surface-save-runtime-01'


def fixture(profile=None):
    bank,prior=rewards.fixture(profile)
    selected=bytearray(64);selected[9]=selected[41]=62
    owned=bytearray(256)
    for player in range(4):owned[player*64+9]=owned[player*64+41]=1<<(player+1)
    return bank,prior+selected+owned


def reference_pack(bank,state):
    result=rewards.reference_pack(bank,state[:880]);ext=legacy.PAYLOAD
    struct.pack_into('>HHI',result,ext+4,4,0x680,3)
    result[ext+0x390:ext+0x4D0]=state[880:1200]
    legacy.seal_extension(result)
    return result


class SurfaceSaveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUT/'build-lock.json');cls.base,cls.prior=inputs(OUT/'base-lock.json')
        cls.files=by_vrom(cls.image);cls.before=by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.image);cls.old=cls.before[BLOB].extract(cls.base)
        cls.surface=cls.report['room_surfaces'];cls.saved=cls.surface['save'];cls.items=cls.surface['items']
        cls.temp=tempfile.TemporaryDirectory(prefix='v3-surface-save-')
        binary=Path(cls.temp.name)/'codec.so'
        cls.flags=['-D'+v for v in DEFINES]
        subprocess.run(['cc','-std=c11','-shared','-fPIC','-O2','-Wall','-Wextra','-Werror',*cls.flags,
            str(ROOT/'tests/v3_surface_save_runtime_test.c'),'-o',str(binary)],check=True,capture_output=True)
        cls.api=c.CDLL(str(binary));cls.api.af_v3_save_check.argtypes=(c.c_void_p,c.c_uint,c.c_void_p,c.c_void_p)
        cls.api.af_v3_save_pack.argtypes=(c.c_void_p,c.c_uint,c.c_void_p)
        cls.api.af_v3_save_collect.argtypes=(c.c_void_p,c.c_uint,c.c_uint,c.c_uint)

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    @staticmethod
    def buffer(value):return (c.c_ubyte*len(value)).from_buffer_copy(value)
    def check(self,bank,profile,want,state=None):
        b,p,o=self.buffer(bank),self.buffer(profile),self.buffer(b'\xA5'*(WORKING_BYTES+32))
        self.assertEqual(self.api.af_v3_save_check(b,len(bank),p,c.byref(o,16)),want)
        self.assertEqual(bytes(b),bank);self.assertEqual(bytes(p),profile)
        self.assertEqual(bytes(o),b'\xA5'*16+(bytes(state) if state is not None else b'\xA5'*WORKING_BYTES)+b'\xA5'*16)

    def test_independent_complete_bank_migration_and_atomic_rejection(self):
        self.api.surface_fixture_select(1023);bank,state=fixture();packed=reference_pack(bank,state)
        raw=self.buffer(bank)
        self.assertEqual(self.api.af_v3_save_pack(raw,len(bank),self.buffer(state)),1)
        self.assertEqual(bytes(raw),packed);self.check(packed,state[:192],1,state)
        self.assertEqual(self.api.af_v3_save_pack(raw,len(bank),self.buffer(state)),1);self.assertEqual(bytes(raw),packed)
        selected=state[880:944]
        self.check(bank,state[:192],0,state[:192]+bytes(688)+selected+bytes(256))
        old,old_state=legacy.fixture()
        self.check(legacy.reference_pack(old,old_state),state[:192],1,state[:192]+old_state[160:]+bytes(176)+selected+bytes(256))
        self.check(rewards.clothing.reference_pack(bank,state[:832]),state[:192],1,state[:832]+bytes(48)+selected+bytes(256))
        self.check(rewards.reference_pack(bank,state[:880]),state[:192],1,state[:944]+bytes(256))
        self.api.surface_fixture_select(1022);self.check(packed,state[:192],-7)
        self.api.surface_fixture_select(1023)
        for offset,bit,error,seal in ((0x390+9,2,-6,False),(0x3D0,1,-8,True),(0x4D0,1,-4,True)):
            bad=bytearray(packed);bad[legacy.PAYLOAD+offset]^=bit
            if seal:legacy.seal_extension(bad)
            self.check(bad,state[:192],error)
        bad=bytearray(state);bad[944]=1;raw=self.buffer(bank)
        self.assertEqual(self.api.af_v3_save_pack(raw,len(bank),self.buffer(bad)),-8);self.assertEqual(bytes(raw),bank)
        smaller=bytearray(state);smaller[889]&=~2
        for p in range(4):smaller[944+p*64+9]&=~2
        # A larger current selection retains owned bits and adds only required profile bits.
        small=reference_pack(bank,smaller);expanded=smaller[:];expanded[880:944]=selected
        self.check(small,state[:192],1,expanded)
        oldbin=Path(self.temp.name)/'format3.so'
        subprocess.run(['cc','-shared','-fPIC','-O2','-Wall','-Wextra','-Werror',*self.flags[:2],
            str(ROOT/'overlays/v3/save_codec.c'),'-o',str(oldbin)],check=True,capture_output=True)
        oldapi=c.CDLL(str(oldbin));oldapi.af_v3_save_check.argtypes=(c.c_void_p,c.c_uint,c.c_void_p,c.c_void_p)
        destination=self.buffer(b'\xA5'*880)
        self.assertEqual(oldapi.af_v3_save_check(self.buffer(packed),len(packed),self.buffer(state[:192]),destination),-4)
        self.assertEqual(bytes(destination),b'\xA5'*880)

    def test_actual_runtime_collection_and_device_failure_order_under_sanitizers(self):
        binary=Path(self.temp.name)/'sanitized'
        result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
            '-fsanitize=address,undefined','-fno-omit-frame-pointer',*self.flags,
            str(ROOT/'tests/v3_surface_save_runtime_test.c'),'-o',str(binary)],capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr)
        result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_complete_resources_stable_dispatch_and_bootstrap(self):
        packet=self.blob[self.items['blob_offset']:self.items['blob_offset']+SIZE]
        self.assertEqual(sha256(packet),self.items['sha256']);self.assertEqual(zlib.crc32(packet),self.items['crc32'])
        for key,part,at in (('helpers','surface_save',0x900),('codec','surface_codec',0x1000),('runtime','surface_save_runtime',0x2000)):
            code=(OUT/part/'code.bin').read_bytes();self.assertEqual(packet[at:at+len(code)],code)
            self.assertEqual(sha256(code),self.saved[key]['sha256'])
        self.assertEqual(packet[0xFF0:0x1000],bytes.fromhex('AF5351DE')*4)
        self.assertEqual(packet[-16:],bytes.fromhex('AF5351DE')*4)
        for p in self.saved['stable_runtime_dispatch']+self.saved['collection_hooks']:
            address=p['address'];new,old,ram=(self.blob,self.old,0x80460000) if address>=0x80460000 else (
                self.files[CODE_VROM].extract(self.image),self.before[CODE_VROM].extract(self.base),CODE_RAM)
            at=address-ram;self.assertEqual(new[at:at+8].hex(),p['after']);self.assertEqual(old[at:at+8].hex(),p['before'])
        for p in self.saved['codec_entries']:
            at=int(p['entry'],16)-0x80460000;self.assertEqual(self.blob[at:at+8].hex(),p['after'])
        self.assertEqual(self.report['save_runtime']['code']['symbols'],self.prior['save_runtime']['code']['symbols'])
        self.assertEqual(self.report['save_runtime']['state_bytes'],STATE_BYTES)
        self.assertEqual(self.report['save_runtime']['guard_ram'],0x8046C4C0)
        self.assertEqual(self.report['expansion_state_range'],['8046C000','8046C4D0'])
        self.assertLessEqual(0x8046C000+STATE_BYTES,0x8046D000);self.assertLessEqual(RAM+SIZE,0x80500000)
        ep=self.report['equipment_resources'];e=self.blob[ep['blob_offset']:ep['blob_offset']+ep['bytes']]
        self.assertEqual(zlib.crc32(e),ep['crc32']);self.assertEqual(sha256(e),ep['sha256'])
        self.assertIn('-DAF_SURFACE_ITEMS_BYTES=0x4000u',self.items['bootstrap']['code']['flags'])
        self.assertIn(f'-DAF_V3_EQUIPMENT_CRC=0x{ep["crc32"]:08X}u',self.report['startup']['flags'])
        self.assertLessEqual(self.report['startup']['bytes'],992)
        for p in SOURCES:self.assertEqual(self.surface['sources'][p],sha256((ROOT/p).read_bytes()),p)

    def test_retained_assets_profiles_composition_and_compatibility_warning(self):
        self.assertEqual(self.report['save_runtime']['profile_hex'],self.prior['save_runtime']['profile_hex'])
        for key in ('owners','secondary_owners','banks','rows'):self.assertEqual(self.surface[key],self.prior['room_surfaces'][key])
        for row in self.surface['rows']:
            at=row['blob_offset'];n=row['bytes'];self.assertEqual(self.blob[at:at+n],self.old[at:at+n])
        v,n,_,_=struct.unpack_from('>4I',self.blob,0xE0);at=v-BLOB
        self.assertEqual(self.blob[at:at+n],self.old[at:at+n])
        self.assertIn('Older format-1/2/3',composer.save_compatibility(self.report))
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(OUT/'build-lock.json');choices=composer.catalogue(self.image,self.report)
            self.assertEqual(len(choices),141)
            self.assertEqual(composer.compose(self.image,self.report,choices,composer.resolve(choices,list(choices)))[0],self.image)
            self.assertEqual(sha256(composer.compose(self.image,self.report,choices,composer.resolve(choices,[]))[0]),self.report['translation_baseline']['sha256'])
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),(OUT/'asset-loader.ups').read_bytes()),self.image)

    def test_future_shared_display_refresh_retains_surface_collection(self):
        from v3_display_aliases import install
        prior=copy.deepcopy(self.report)
        prior['sources']['tools/v3_display_aliases.py']='force changed shared-reader source'
        blob=bytearray(self.blob);core=bytearray(self.files[CODE_VROM].extract(self.image))
        output=Path(self.temp.name)/'future-display-refresh'
        display,_=install(prior,blob,core,output)
        self.assertEqual(display['readers']['collection_hooks'],self.report['clothing']['display']['readers']['collection_hooks'])
        for hook in display['readers']['collection_hooks']:
            at=hook['entry']-0x80460000
            self.assertEqual(blob[at:at+8].hex(),hook['after'])
            self.assertEqual(hook['target'],hook['surface_outer_target'])


if __name__=='__main__':unittest.main()
