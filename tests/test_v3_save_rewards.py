"""Format-3 migration, independent event flags, stable native entries, and bounds."""
import ctypes as c
import json
import os
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
from v3_furniture_install import inputs,reuse_resource_tail
from tests import test_v3_save_clothing as clothing
from tests import test_v3_save_codec as legacy
from tests import test_v3_equipment_runtime as shared
from v3_save_rewards import WORKING_BYTES,STATE_BYTES,source_bindings

OUTPUT=ROOT/os.environ.get('V3_REWARD_STATE_BUILD','build/v3-shared-reward-state-02')


def fixture(profile=None):
    bank,prior=clothing.fixture()
    if profile is not None:
        prior[:192]=profile
        # The existing fixture's selected furniture/clothing belongs to this
        # proposal; reject a narrower profile instead of inventing ownership.
        if any(prior[192+i]&~profile[32+(i%128)] for i in range(512)):
            raise ValueError('Current proposal omits fixture furniture')
    flags=b''.join(struct.pack('>IIB3x',1<<(player*7),1<<player,1<<player) for player in range(4))
    return bank,prior+flags


def reference_pack(bank,state):
    result=clothing.reference_pack(bank,state[:832]);ext=legacy.PAYLOAD
    struct.pack_into('>H',result,ext+4,3)
    result[ext+0x360:ext+0x390]=state[832:880]
    legacy.seal_extension(result)
    return result


class RewardStateHostTests(unittest.TestCase):
    sanitized=shared.HostTests.sanitized
    def test_sanitized_reward_lifecycle_and_failure_order(self):self.sanitized('v3_reward_state_test.c')


@unittest.skipUnless((OUTPUT/'build.json').is_file(),'Current reward-state proposal required')
class RewardCompatibilityNoteTests(unittest.TestCase):
    def test_exports_use_the_current_format_warning(self):
        from v3_optional_composition import save_compatibility
        report=json.loads((OUTPUT/'build.json').read_bytes())
        self.assertEqual(save_compatibility(report),report['save_warning'])
        self.assertIn('older format-1/2 V3 builds',save_compatibility(report))
        for version in (1,2):
            self.assertTrue(save_compatibility({'save_codec':{'format_version':version}})
                .startswith(f'Format {version}:'))
        del report['save_warning']
        with self.assertRaises(KeyError):save_compatibility(report)


class RewardCodecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='v3-reward-codec-')
        cls.apis={}
        for version,flags in ((1,()),(2,('-DAF_V3_CLOTHING_PROFILE=1',)),
                (3,('-DAF_V3_CLOTHING_PROFILE=1','-DAF_V3_REWARD_PROFILE=1'))):
            path=Path(cls.temp.name)/f'codec{version}.so'
            subprocess.run(['cc','-shared','-fPIC','-O2','-Wall','-Wextra','-Werror',*flags,
                str(ROOT/'overlays/v3/save_codec.c'),'-o',str(path)],check=True,capture_output=True)
            api=c.CDLL(str(path));api.af_v3_save_check.argtypes=(c.c_void_p,c.c_uint,c.c_void_p,c.c_void_p)
            api.af_v3_save_pack.argtypes=(c.c_void_p,c.c_uint,c.c_void_p);cls.apis[version]=api
        cls.api=cls.apis[3]

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    @staticmethod
    def buffer(raw):return (c.c_ubyte*len(raw)).from_buffer_copy(raw)
    def check(self,bank,profile,want,state=None):
        raw,p,out=self.buffer(bank),self.buffer(profile),self.buffer(b'\xA5'*912)
        self.assertEqual(self.api.af_v3_save_check(raw,len(bank),p,c.byref(out,16)),want)
        self.assertEqual(bytes(raw),bank);self.assertEqual(bytes(p),profile)
        self.assertEqual(bytes(out),b'\xA5'*16+(bytes(state) if state is not None else b'\xA5'*880)+b'\xA5'*16)

    def test_independent_complete_bank_and_all_older_migrations(self):
        bank,state=fixture();packed=reference_pack(bank,state);raw=self.buffer(bank)
        self.assertEqual(self.api.af_v3_save_pack(raw,len(bank),self.buffer(state)),1)
        self.assertEqual(bytes(raw),packed);self.check(packed,state[:192],1,state)
        self.assertEqual(self.api.af_v3_save_pack(raw,len(bank),self.buffer(state)),1)
        self.assertEqual(bytes(raw),packed)
        self.check(bank,state[:192],0,state[:192]+bytes(688))
        old,old_state=legacy.fixture()
        self.check(legacy.reference_pack(old,old_state),state[:192],1,state[:192]+old_state[160:]+bytes(176))
        self.check(clothing.reference_pack(bank,state[:832]),state[:192],1,state[:832]+bytes(48))
        for version,length in ((1,672),(2,832)):
            out=self.buffer(b'\xA5'*length)
            self.assertEqual(self.apis[version].af_v3_save_check(raw,len(bank),self.buffer(state[:192]),out),-4)
            self.assertEqual(bytes(out),b'\xA5'*length)

    def test_corruption_rejection_is_atomic_and_profiles_stay_required(self):
        bank,state=fixture();packed=reference_pack(bank,state)
        missing=bytearray(state[:192]);missing[183]=0;self.check(packed,missing,-7)
        larger=bytearray(state[:192]);larger[182]|=1;self.check(packed,larger,1,larger+state[192:])
        for offset,value,error,seal in ((0x360,0x80,-6,False),(0x360,0x80,-9,True),
                (0x364,1,-9,True),(0x367,0x80,-9,True),(0x368,0x80,-9,True),
                (0x369,1,-9,True),(0x36A,1,-9,True),(0x36B,1,-9,True),(0x390,1,-4,True)):
            bad=bytearray(packed);bad[legacy.PAYLOAD+offset]^=value
            if seal:legacy.seal_extension(bad)
            self.check(bad,state[:192],error)
        bad=bytearray(packed);bad[0x400]^=1;legacy.checksum(bad);self.check(bad,state[:192],-5)
        invalid=bytearray(state);invalid[832+9]=1;raw=self.buffer(bank)
        self.assertEqual(self.api.af_v3_save_pack(raw,len(bank),self.buffer(invalid)),-9)
        self.assertEqual(bytes(raw),bank)
        self.assertEqual(self.api.af_v3_save_pack(raw,len(bank),c.byref(raw,128)),-1)
        self.assertEqual(self.api.af_v3_save_check(raw,len(bank),self.buffer(state[:192]),c.byref(raw,256)),-1)
        self.assertEqual(bytes(raw),bank)


@unittest.skipUnless((OUTPUT/'build-lock.json').is_file(),'Current reward-state proposal required')
class RewardStateCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom,cls.report=inputs(OUTPUT/'build-lock.json');cls.base,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.rom);cls.old=cls.before[BLOB].extract(cls.base)
        cls.r=cls.report['equipment_resources']['player_actions']['reward_state']

    def test_complete_loaded_resources_stable_entries_and_state_bounds(self):
        r=self.r;self.assertEqual(json.loads(json.dumps(source_bindings())),r['source'])
        self.assertEqual(r['runtime_bytes'],STATE_BYTES);self.assertEqual(r['working_state_bytes'],WORKING_BYTES)
        self.assertEqual(self.report['save_runtime']['code']['symbols'],self.prior['save_runtime']['code']['symbols'])
        self.assertEqual(self.report['save_runtime']['profile_hex'],self.prior['save_runtime']['profile_hex'])
        self.assertEqual(self.report['save_codec']['format_version'],3)
        self.assertEqual(self.report['save_codec']['registry_version'],2)
        self.assertEqual(self.report['expansion_state_range'],['8046C000','8046C390'])
        at=r['resource_vrom']-BLOB;extra=self.blob[at:at+r['resource_bytes']]
        self.assertEqual(sha256(extra),r['resource_sha256'])
        self.assertEqual(struct.unpack_from('>4I',self.blob,0xE0),
            (r['resource_vrom'],len(extra),zlib.crc32(extra),0x8046D000))
        self.assertEqual(extra[0x8DC:],self.old[at+0x8DC:at+len(extra)])
        for key,start,directory in (('codec_code',at,'save_rewards'),('code',0xB408,'reward_state'),
                                  ('runtime_code',0x9200,'save_runtime')):
            code=(OUTPUT/directory/'code.bin').read_bytes()
            self.assertEqual(self.blob[start:start+len(code)],code);self.assertEqual(sha256(code),r[key]['sha256'])
        for row in r['public_entries']:
            self.assertEqual(self.blob[int(row['entry'],16)-0x80460000:][:8],bytes.fromhex(row['after']))
        retained=bytearray(self.blob)
        for first,last in ((4,8),(0xE8,0xEC),(0x9200,0x9200+r['runtime_code']['bytes']),
                (0xB400,0xB7A8),(0xB9C4,0xB9CC),(at,at+0x8DC)):
            retained[first:last]=self.old[first:last]
        self.assertEqual(retained,self.old)
        self.assertLessEqual(0xC000+STATE_BYTES,0xD000)

    def test_native_hooks_preserved_resources_composition_and_patch(self):
        hook=self.r['private_clear_hook'];at=hook['entry']-CODE_RAM
        core=bytearray(self.files[CODE_VROM].extract(self.rom));before=self.before[CODE_VROM].extract(self.base)
        self.assertEqual(core[at:at+8].hex(),hook['after']);self.assertEqual(before[at:at+8].hex(),hook['before'])
        core[at:at+8]=before[at:at+8];self.assertEqual(core,before)
        for v in self.files.keys()-{BLOB,MODULE,CODE_VROM,0x19D40}:
            self.assertEqual(self.files[v].extract(self.rom),self.before[v].extract(self.base),hex(v))
        import v3_optional_composition as composer
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(OUTPUT/'build-lock.json');choices=composer.catalogue(self.rom,self.report)
            self.assertEqual(len(choices),128)
            self.assertEqual(composer.compose(self.rom,self.report,choices,composer.resolve(choices,list(choices)))[0],self.rom)
            self.assertEqual(sha256(composer.compose(self.rom,self.report,choices,composer.resolve(choices,[]))[0]),
                self.report['translation_baseline']['sha256'])
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(original,(OUTPUT/'asset-loader.ups').read_bytes()),self.rom)
        reuse_resource_tail(self.rom,self.report,self.blob)


if __name__=='__main__':unittest.main()
