"""Actual aloha conversion, shared reader/default hooks, and profile isolation."""
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
from aflib import CODE_VROM, DMA_START, apply_ups, by_vrom, n64_checksum, sha256
from v3_aloha_runtime import BASE, BASE_SHA, BLOB, CONFIG, MODULE, PACKAGE_OFFSET, PACKAGE_BYTES, STARTUP
from v3_clothing import convert
from v3_import_catalog import read_donor
from v3_villager_text import read_text_donor
from tests.test_v3_save_clothing import fixture, reference_pack, STATE

OUTPUT=ROOT/'build/v3-aloha-outfits-03'


@unittest.skipUnless((OUTPUT/'build.json').exists(),'Current aloha cartridge required')
class Aloha(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.base=(BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.report=json.loads((OUTPUT/'build.json').read_text())
        cls.previous=json.loads((BASE/'build.json').read_text())
        cls.files,cls.old=by_vrom(cls.rom),by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.rom)
        cls.donor=read_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
        cls.first=read_text_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
        cls.symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()

    def test_complete_donor_artwork_names_prices_and_fixed_identities(self):
        self.assertEqual(len(self.report['clothing']['imports']),3)
        for i,item in enumerate((0x24BF,0x241A,0x241B)):
            resource,record,row=convert(self.native,self.first,self.donor['rel'],self.symbols,donor_item=item)
            offset=int(row['vrom'],16)-BLOB
            self.assertEqual(self.blob[offset:offset+544],resource)
            self.assertEqual(self.blob[0x2820+i*32:0x2840+i*32],record)
            self.assertEqual(row['resource_index'],item-0x1400)
            if i:self.assertEqual(row['price'],0)
        a=self.report['clothing']['imports']
        self.assertEqual([x['item_id'] for x in a],['34BF','341A','341B'])
        self.assertEqual(a[1]['texture_sha256'],a[2]['texture_sha256'])
        self.assertNotEqual(a[1]['palette_sha256'],a[2]['palette_sha256'])
        for v in (0xB68000,0xB88000):
            self.assertEqual(self.files[v].extract(self.rom),by_vrom(self.native)[v].extract(self.native))

    def test_actual_roster_and_all_defaults_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-aloha-') as directory:
            binary=Path(directory)/'test'
            subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_clothing_roster_test.c'),'-o',str(binary)],check=True,capture_output=True)
            result=subprocess.run([str(binary)],input=self.blob[0x2820:0x2880]+self.blob[0x2C00:0x2E80]
                +self.blob[0x20:0xE0],check=True,capture_output=True,timeout=20)
            self.assertIn(b'Three garments, complete twenty-villager defaults',result.stdout)

    def test_islander_fields_change_only_the_verified_applied_outfit(self):
        before=self.old[BLOB].extract(self.base)
        self.assertEqual(len(self.report['aloha_outfits']['defaults']),18)
        for i,row in enumerate(self.report['villager_text']['imports']):
            old=bytearray(before[0x2C00+i*32:0x2C20+i*32])
            after=self.blob[0x2C00+i*32:0x2C20+i*32]
            if i not in (16,19):
                self.assertEqual(old[6],2)
                self.assertEqual(old[30:],bytes(2))
                self.assertEqual(after[30:],struct.pack('>H',int(row['donor_clothing_id'],16)+0x1000))
                old[30:]=after[30:]
            self.assertEqual(old,after)
            self.assertTrue(row['initial_defaults_applied'])
        self.assertEqual(self.blob[0x1E60:0x1E74],bytes(20))

    def test_owned_profiles_and_codec_keep_three_clothing_identities_separate(self):
        current=bytes.fromhex(self.report['save_runtime']['profile_hex'])
        previous=bytes.fromhex(self.previous['save_runtime']['profile_hex'])
        expected=bytearray(previous);expected[163]|=12
        self.assertEqual(current,expected)
        with tempfile.TemporaryDirectory(prefix='af-v3-aloha-codec-') as directory:
            library=Path(directory)/'codec.so'
            subprocess.run(['cc','-shared','-fPIC','-Wall','-Wextra','-Werror',
                '-DAF_V3_CLOTHING_PROFILE=1',str(ROOT/'overlays/v3/save_codec.c'),'-o',str(library)],
                check=True,capture_output=True)
            api=c.CDLL(str(library))
            api.af_v3_save_collect.argtypes=(c.c_void_p,c.c_uint,c.c_uint,c.c_uint)
            api.af_v3_save_pack.argtypes=(c.c_void_p,c.c_uint,c.c_void_p)
            api.af_v3_save_check.argtypes=(c.c_void_p,c.c_uint,c.c_void_p,c.c_void_p)
            state=c.create_string_buffer(current+bytes(640),STATE)
            expected=bytearray(state.raw)
            for player,item in enumerate((0x341A,0x341B,0x34BF)):
                self.assertEqual(api.af_v3_save_collect(state,player,item,1),1)
                expected[192+512+player*32+((item&255)>>3)]|=1<<(item&7)
            self.assertEqual(state.raw,expected)
            self.assertEqual(api.af_v3_save_collect(state,0,0x341B,0),0)
            self.assertEqual(api.af_v3_save_collect(state,1,0x341A,0),0)
            self.assertEqual(api.af_v3_save_collect(state,0,0x3418,1),-7)
            bank,_=fixture();packed=c.create_string_buffer(bytes(bank),len(bank))
            self.assertEqual(api.af_v3_save_pack(packed,len(bank),state),1)
            self.assertEqual(packed.raw,reference_pack(bank,expected))
            out=c.create_string_buffer(b'!'*STATE,STATE)
            self.assertEqual(api.af_v3_save_check(packed,len(bank),c.create_string_buffer(previous),out),-7)
            self.assertEqual(out.raw,b'!'*STATE)
            old=bytes(reference_pack(bank,previous+bytes(640)))
            self.assertEqual(api.af_v3_save_check(c.create_string_buffer(old),len(old),
                c.create_string_buffer(current),out),1)
            self.assertEqual(out.raw,current+bytes(640))

    def test_hooks_descriptors_and_all_unrelated_instructions_are_retained(self):
        before=self.old[BLOB].extract(self.base)
        expected=bytearray(before)
        for begin,end in ((4,8),(0x20,0xE0),(0xE8,0xEC),(0xF8,0xFC),(0x2840,0x2880),
                          (0x2C00,0x2E80),(PACKAGE_OFFSET+0xA00,PACKAGE_OFFSET+0x1000)):
            expected[begin:end]=self.blob[begin:end]
        for hook in self.report['aloha_outfits']['hooks']:
            at=hook['blob_offset'];self.assertEqual(before[at:at+8].hex(),hook['before'])
            after=bytes.fromhex(hook['after']);self.assertEqual(self.blob[at:at+8],after)
            self.assertEqual(struct.unpack('>II',after),
                (0x08000000 | (int(hook['target'],16)>>2 & 0x3FFFFFF),0))
            expected[at:at+8]=after
        for fix in self.report['aloha_outfits']['reader_fixes']:
            at=fix['blob_offset']
            self.assertEqual(before[at:at+4].hex(),fix['before'])
            self.assertEqual(self.blob[at:at+4].hex(),fix['after'])
            expected[at:at+4]=bytes.fromhex(fix['after'])
        expected.extend(bytes(len(self.blob)-len(expected)))
        for row in self.report['clothing']['imports'][1:]:
            at=int(row['vrom'],16)-BLOB;expected[at:at+544]=self.blob[at:at+544]
        self.assertEqual(expected,self.blob)
        for at,offset,size,ram in ((0xE0,0xF400,self.previous['clothing']['save_extension']['resource_bytes'],0x8046D000),
                                  (0xF0,PACKAGE_OFFSET,PACKAGE_BYTES,0x80473000)):
            self.assertEqual(struct.unpack_from('>4I',self.blob,at),
                             (BLOB+offset,size,zlib.crc32(self.blob[offset:offset+size]),ram))
        self.assertEqual(self.files[CODE_VROM].extract(self.rom),self.old[CODE_VROM].extract(self.base))

    def test_complete_bridges_preserve_compiler_retained_registers(self):
        symbols=self.report['aloha_outfits']['code']['symbols']
        saved=list(range(3,16))+[24,25,31]
        for hook in self.report['aloha_outfits']['hooks']:
            target=symbols[hook['helper']]
            address=symbols[hook['helper']+'_bridge']
            self.assertEqual(int(hook['target'],16),address)
            words=[0x27BDFF70]
            words += [0xFFA00000|(reg<<16)|(16+i*8) for i,reg in enumerate(saved)]
            words += [0x0C000000|(target>>2&0x3FFFFFF),0]
            words += [0xDFA00000|(reg<<16)|(16+i*8) for i,reg in enumerate(saved)]
            words += [0x03E00008,0x27BD0090]
            expected=struct.pack('>'+str(len(words))+'I',*words)
            at=PACKAGE_OFFSET+address-0x80473000
            self.assertEqual(self.blob[at:at+len(expected)],expected)
        # No C helper instruction modifies HI/LO or coprocessor state.
        first_bridge=min(symbols[h['helper']+'_bridge'] for h in self.report['aloha_outfits']['hooks'])
        start=PACKAGE_OFFSET+0xA00
        end=PACKAGE_OFFSET+first_bridge-0x80473000
        for (word,) in struct.iter_unpack('>I',self.blob[start:end]):
            self.assertNotIn(word>>26,(16,17,18,19))
            if word>>26==0:self.assertNotIn(word&63,(17,19,24,25,26,27,28,29,30,31))

    def test_physical_directory_retention_startup_and_full_patch(self):
        self.assertEqual(set(self.files),set(self.old))
        expected=bytearray(self.base)
        for vrom,row in self.files.items():
            self.assertEqual(row.pstart,self.old[vrom].pstart)
            if vrom not in (BLOB,MODULE):self.assertEqual(row,self.old[vrom])
        for vrom in (BLOB,MODULE):
            row=self.files[vrom];expected[row.pstart:row.pstart+row.size]=row.extract(self.rom)
        at=DMA_START+self.files[BLOB].index*16;expected[at:at+16]=self.rom[at:at+16]
        expected[0x10:0x18]=self.rom[0x10:0x18];self.assertEqual(expected,self.rom)
        module=self.files[MODULE].extract(self.rom)
        old=bytearray(self.old[MODULE].extract(self.base));old[STARTUP:CONFIG+16]=module[STARTUP:CONFIG+16]
        self.assertEqual(module,old)
        self.assertEqual(struct.unpack_from('>4I',module,CONFIG),(BLOB,0xC000,zlib.crc32(self.blob[:0xC000]),55))
        self.assertEqual(sha256(self.base),BASE_SHA)
        self.assertEqual(sha256(self.rom),self.report['output_sha256'])
        self.assertEqual(n64_checksum(self.rom),struct.unpack_from('>II',self.rom,0x10))
        self.assertEqual(apply_ups(self.native,(OUTPUT/'asset-loader.ups').read_bytes()),self.rom)


if __name__=='__main__':unittest.main()
