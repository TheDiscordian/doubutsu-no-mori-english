"""Current explicit town policy, retained native schedules, and bounded installation."""
import ctypes as c
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
from aflib import CODE_RAM,CODE_VROM,apply_ups,by_vrom,n64_checksum,sha256
from v3_town_residents import BASE,BASE_SHA,BLOB,CONFIG,MODE_OFFSET,MODULE,STARTUP

OUTPUT=ROOT/'build/v3-town-residents-03'


class TownPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='v3-town-policy-')
        library=Path(cls.temp.name)/'town.so'
        fixture='''
unsigned char af_v3_town_flags[20],af_v3_town_modes[20],af_v3_town_metadata[640],af_v3_town_profile[192];
int af_v3_town_ready=1, outfit_enabled=1, outfit_calls;
unsigned int last_outfit;
int af_v3_town_outfit(unsigned int cloth) {
    ++outfit_calls;last_outfit=cloth;return outfit_enabled;
}
'''
        subprocess.run(['cc','-shared','-fPIC','-Wall','-Wextra','-Werror',
            str(ROOT/'overlays/v3/town_eligible.c'),'-x','c','-','-o',str(library)],
            input=fixture,text=True,check=True,capture_output=True)
        cls.api=c.CDLL(str(library));cls.api.af_v3_town_eligible.argtypes=[c.c_int]

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def setUp(self):
        for name,size in (('flags',20),('modes',20),('metadata',640),('profile',192)):
            array=(c.c_ubyte*size).in_dll(self.api,'af_v3_town_'+name)
            c.memset(c.addressof(array),0,size);setattr(self,name,array)
        for name,value in (('af_v3_town_ready',1),('outfit_enabled',1),('outfit_calls',0)):
            c.c_int.in_dll(self.api,name).value=value
        for slot in range(20):
            idx=218+slot;at=slot*32
            self.flags[slot]=self.modes[slot]=1
            self.profile[idx//8]|=1<<(idx&7)
            self.metadata[at:at+8]=bytes((0xE0,idx,0x24,0x1A,slot%6,0,0 if slot in (16,19) else 2,1))
            self.metadata[at+30:at+32]=bytes.fromhex('341A')

    def test_native_ids_and_invalid_bounds_do_not_read_import_dependencies(self):
        c.c_int.in_dll(self.api,'af_v3_town_ready').value=0
        for idx in range(216):self.assertEqual(self.api.af_v3_town_eligible(idx),1)
        for idx in (-2147483648,-1,216,217,218,237,238,255,2147483647):
            self.assertEqual(self.api.af_v3_town_eligible(idx),0)
        self.assertEqual(c.c_int.in_dll(self.api,'outfit_calls').value,0)

    def test_all_fixed_identities_keep_original_roles_and_require_exact_outfits(self):
        before=bytes(self.metadata)
        for idx in range(218,238):self.assertEqual(self.api.af_v3_town_eligible(idx),1)
        self.assertEqual(c.c_int.in_dll(self.api,'outfit_calls').value,20)
        self.assertEqual(c.c_uint.in_dll(self.api,'last_outfit').value,0x341A)
        c.c_int.in_dll(self.api,'outfit_enabled').value=0
        self.assertEqual(self.api.af_v3_town_eligible(218),0)
        self.assertEqual(bytes(self.metadata),before)

    def test_mode_flag_profile_and_metadata_reject_independently(self):
        for array,at,value in ((self.flags,0,0),(self.flags,0,2),(self.modes,0,0),
                (self.modes,0,2),(self.profile,27,0),(self.metadata,0,0),
                (self.metadata,1,219),(self.metadata,4,6),(self.metadata,6,1),
                (self.metadata,6,255),(self.metadata,7,0),(self.metadata,7,2)):
            old=array[at];array[at]=value
            self.assertEqual(self.api.af_v3_town_eligible(218),0)
            self.assertEqual(self.api.af_v3_town_eligible(237),1)
            array[at]=old


@unittest.skipUnless((OUTPUT/'build.json').exists(),'Current town cartridge required')
class TownCartridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((OUTPUT/'build.json').read_text())
        cls.base=(BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.prior=json.loads((BASE/'build.json').read_text())
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.files,cls.old=by_vrom(cls.rom),by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.rom)

    def test_exact_policy_code_hooks_and_complete_retained_resources(self):
        helper=(OUTPUT/'town_eligible/code.bin').read_bytes()
        expected=bytearray(self.old[BLOB].extract(self.base))
        self.assertLessEqual(len(helper),448)
        self.assertEqual(len(helper),self.report['town_residents']['code']['bytes'])
        hook=self.report['town_residents']['hook'];at=int(hook['entry'],16)-0x80460000
        self.assertEqual(expected[at:at+8].hex(),hook['before'])
        self.assertEqual(struct.unpack('>2I',bytes.fromhex(hook['after'])),
                         (0x08000000|(int(hook['target'],16)>>2&0x3FFFFFF),0))
        expected[at:at+8]=bytes.fromhex(hook['after'])
        expected[0x70E40:0x70E40+len(helper)]=helper
        expected[0x1E60:0x1E74]=expected[MODE_OFFSET:MODE_OFFSET+20]=b'\1'*20
        struct.pack_into('>I',expected,4,57)
        struct.pack_into('>I',expected,0xF8,zlib.crc32(expected[0x70000:0x7F000]))
        self.assertEqual(expected,self.blob)
        self.assertEqual(self.files,self.old)
        self.assertEqual(self.report['save_runtime']['profile_hex'],self.prior['save_runtime']['profile_hex'])
        self.assertEqual(self.report['villager_selection']['move_in_enabled'],[f'{n:04X}' for n in range(0xE0DA,0xE0EE)])
        # The original private callee's callers retain live caller-saved values.
        at=int(hook['target'],16)-0x80473E40
        words=struct.unpack('>37I',helper[at:at+148])
        self.assertEqual(words[0],0x27BDFF70)
        registers=(3,4,5,6,7,8,9,10,11,12,13,14,15,24,25,31)
        for pos,reg in enumerate(registers):
            offset=16+pos*8
            self.assertEqual(words[1+pos],0xFFA00000|(reg<<16)|offset)
            self.assertEqual(words[19+pos],0xDFA00000|(reg<<16)|offset)
        self.assertEqual(words[-2:],(0x03E00008,0x27BD0090))

    def test_all_six_complete_native_schedules_and_personality_mapping(self):
        code=self.files[CODE_VROM].extract(self.rom)
        self.assertEqual(code,self.old[CODE_VROM].extract(self.base))
        original=by_vrom(self.native)[CODE_VROM].extract(self.native)
        for row in self.report['town_residents']['retained_native_schedule_ranges']:
            start,end=int(row['start'],16)-CODE_RAM,int(row['end'],16)-CODE_RAM
            self.assertEqual(code[start:end],original[start:end])
            self.assertEqual(sha256(code[start:end]),row['sha256'])
        for personality in range(6):
            table=struct.unpack_from('>I',code,0x8010BB10-CODE_RAM+personality*4)[0]
            count,data=struct.unpack_from('>2I',code,table-CODE_RAM)
            self.assertGreaterEqual(data,0x8010B970)
            self.assertLessEqual(data+count*8,0x8010BB10)
            self.assertEqual(count,7 if personality<4 else 9)
            times=[struct.unpack_from('>2I',code,data-CODE_RAM+i*8) for i in range(count)]
            self.assertEqual(times[-1][1],86400)
            self.assertEqual({entry[0] for entry in times},{0,1,2})
        for row,previous in zip(self.report['villager_text']['imports'],self.prior['villager_text']['imports']):
            self.assertEqual(row['record_sha256'],previous['record_sha256'])
            self.assertEqual(row['personality'],previous['personality'])

    def test_only_reviewed_writes_startup_checksums_and_patch(self):
        expected=bytearray(self.base)
        for vrom in (BLOB,MODULE):
            entry=self.files[vrom]
            expected[entry.pstart:entry.pstart+entry.size]=entry.extract(self.rom)
        expected[0x10:0x18]=self.rom[0x10:0x18]
        self.assertEqual(expected,self.rom)
        module=self.files[MODULE].extract(self.rom)
        old=bytearray(self.old[MODULE].extract(self.base))
        old[STARTUP:CONFIG+16]=module[STARTUP:CONFIG+16]
        self.assertEqual(old,module)
        self.assertEqual(struct.unpack_from('>4I',module,CONFIG),(BLOB,0xC000,zlib.crc32(self.blob[:0xC000]),57))
        self.assertEqual(sha256(self.base),BASE_SHA)
        self.assertEqual(sha256(self.rom),self.report['output_sha256'])
        self.assertEqual(n64_checksum(self.rom),struct.unpack_from('>2I',self.rom,0x10))
        self.assertEqual(apply_ups(self.native,(OUTPUT/'asset-loader.ups').read_bytes()),self.rom)


if __name__=='__main__':unittest.main()
