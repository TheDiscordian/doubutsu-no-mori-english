"""Persistent font source, native relocation, startup, and ownership contracts."""

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
from extended_font_cartridge import RAM,configuration,relocate,validate
from aflib import sha256

FONT=ROOT/'build/extended-font-cartridge'


class FontLoaderHostTests(unittest.TestCase):
    def test_owned_system_allocation_success_failures_reentry_and_no_premature_execution(self):
        self.assertEqual(zlib.crc32(bytes(range(96))),0x51C87372)
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'font-loader-test'
            subprocess.run(['gcc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                            '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                            str(ROOT/'runtime/extended_font_loader.c'),str(ROOT/'tests/extended_font_loader_test.c'),
                            '-o',str(target)],check=True,capture_output=True)
            result=subprocess.run([str(target)],check=True,capture_output=True,text=True,timeout=20)
            self.assertIn('ownership and failures passed',result.stdout)


@unittest.skipUnless((FONT/'font.json').is_file(),'Cartridge font is a local generated resource')
class FontCartridgeTests(unittest.TestCase):
    def setUp(self):
        self.data=(FONT/'font.bin').read_bytes();self.reloc=(FONT/'relocation.bin').read_bytes()
        self.report=json.loads((FONT/'font.json').read_text())

    def test_complete_resource_code_and_configuration_are_bound(self):
        validate(self.data,self.reloc,self.report)
        config=configuration(self.data,self.reloc,self.report)
        self.assertEqual(config[:4],[0x03400000,len(self.data)+len(self.reloc),len(self.data),len(self.reloc)])
        self.assertEqual(config[5:], [0,zlib.crc32(self.data+self.reloc),0x41464701])
        for field in ('sha256','relocation_sha256','resource_sha256'):
            report=copy.deepcopy(self.report);report[field]='0'*64
            with self.assertRaises(ValueError): validate(self.data,self.reloc,report)
        report=copy.deepcopy(self.report);report['symbols']['af_font_entry']=4
        with self.assertRaises(ValueError): validate(self.data,self.reloc,report)

    def test_native_pointer_and_jump_relocations_cross_signed_low_boundaries(self):
        text,writable,rodata,bss,count=struct.unpack_from('>5I',self.reloc)
        for base in (0x801A0010,0x802F8010,0x803F0000):
            output=relocate(self.data,self.reloc,base);high={}
            self.assertEqual(output[-bss:],bytes(bss))
            for entry in struct.unpack_from('>'+str(count)+'I',self.reloc,20):
                section,kind,at=entry>>30,(entry>>24)&63,entry&0xFFFFFF
                at += {1:0,2:text,3:text+writable}[section]
                before,after=(struct.unpack_from('>I',data,at)[0] for data in (self.data,output))
                if kind==2: self.assertEqual(after-before,base-RAM)
                elif kind==4: self.assertEqual((after&0x3FFFFFF)*4-(before&0x3FFFFFF)*4,base-RAM)
                elif kind==5: high[(before>>16)&31]=at
                else:
                    hi=high.pop((before>>21)&31)
                    def target(data):
                        return struct.unpack_from('>H',data,hi+2)[0]*65536+struct.unpack_from('>h',data,at+2)[0]
                    self.assertEqual(target(output)-target(self.data),base-RAM)
            self.assertEqual(high,{})
        for base in (RAM,0,True,0x801A0011,0x80400000):
            with self.assertRaises(ValueError): relocate(self.data,self.reloc,base)
        for offset in (0,4,8,12,16,len(self.reloc)-1):
            changed=bytearray(self.reloc);changed[offset]^=1
            with self.assertRaises(ValueError): relocate(self.data,bytes(changed),0x802F8010)


if __name__=='__main__': unittest.main()
