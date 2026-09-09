"""All fixed Snowman letters, full names, and transactional input rejection."""

import ctypes as C
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from mail_record import unpack
from snowman_snapshots import snapshots,TABLE_BYTES


@unittest.skipUnless((ROOT/'build/mail-glyph-catalog/catalog.bin').is_file(),'Local complete letter resources required')
class SnowmanCreatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.catalog = (ROOT/'build/mail-glyph-catalog/catalog.bin').read_bytes()
        cls.items = (ROOT/'build/interior-items-resource/names.bin').read_bytes()
        cls.table,cls.report = snapshots(cls.native,cls.catalog,cls.items)
        cls.temporary = tempfile.TemporaryDirectory(prefix='af-snowman-creator-')
        out = Path(cls.temporary.name);(out/'snapshots.bin').write_bytes(cls.table)
        flags = ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer','-g'] if os.environ.get('AF_SNOWMAN_SANITIZE')=='1' else []
        subprocess.run(['gcc','-std=c99','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',*flags,
                        str(ROOT/'overlays/mail_generation/snowman_creator.c'),str(ROOT/'tests/snowman_creator_data.s'),
                        '-o',str(out/'creator.so')],cwd=out,check=True,capture_output=True)
        cls.lib = C.CDLL(str(out/'creator.so'))
        cls.create = cls.lib.af_snowman_create;cls.create.argtypes = [C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p]
        cls.readonly = (C.c_ubyte*TABLE_BYTES).in_dll(cls.lib,'af_snowman_templates')

    @classmethod
    def tearDownClass(cls): cls.temporary.cleanup()

    def fixture(self,capital=0):
        mail = C.create_string_buffer(b'!'*196,196)
        pid = C.create_string_buffer(b'PLAYER' + b'TOWN  ' + bytes.fromhex('12345678'),16)
        return mail,pid,C.c_uint(capital)

    def test_all_twenty_four_exact_records_names_and_metadata(self):
        for case in self.report['cases']:
            mail,pid,capital = self.fixture(case['capital'])
            with self.subTest(choice=case['choice'],capital=case['capital']):
                self.assertEqual(self.create(C.byref(mail,16),pid,case['choice'],C.byref(capital)),1)
                expected = bytearray(164);expected[:16] = pid.raw
                expected[18:30] = b' '*12;expected[30:35] = b'\xff'*5
                expected[36:38] = case['gift'].to_bytes(2,'big');expected[39:42] = bytes((128,8,12))
                expected[42:] = bytes.fromhex(case['wire'])
                self.assertEqual(mail.raw,b'!'*16+bytes(expected)+b'!'*16)
                self.assertEqual(capital.value,bytes.fromhex(case['text'])[14])
                record = unpack(mail.raw[58:180],expected_catalog=4)
                self.assertEqual(record.templates,(case['template'],));self.assertEqual(len(record.fields[0][1].text),16)
        self.assertEqual(bytes(self.readonly),self.table)

    def test_invalid_choices_capitals_alignment_and_small_addresses_reject(self):
        for choice in (12,13,0x10000,0xFFFFFFFF):
            mail,pid,capital = self.fixture(1);before = mail.raw,pid.raw,capital.value
            self.assertEqual(self.create(C.byref(mail,16),pid,choice,C.byref(capital)),0)
            self.assertEqual((mail.raw,pid.raw,capital.value),before)
        for value in (2,255,0xFFFFFFFF):
            mail,pid,capital = self.fixture(value)
            self.assertEqual(self.create(C.byref(mail,16),pid,0,C.byref(capital)),0)
            self.assertEqual(mail.raw,b'!'*196);self.assertEqual(capital.value,value)
        for argument in (0,1,3):
            for invalid in (None,1,4,15):
                mail,pid,capital = self.fixture(1);args = [C.byref(mail,16),pid,0,C.byref(capital)]
                args[argument] = invalid
                self.assertEqual(self.create(*args),0);self.assertEqual(mail.raw,b'!'*196);self.assertEqual(capital.value,1)

    def test_every_overlap_and_readonly_alias_retains_all_objects(self):
        for target in ('player','capital','player_capital','table_mail','table_player','table_capital'):
            mail,pid,capital = self.fixture(1);args = [C.byref(mail,16),pid,0,C.byref(capital)]
            if target=='player': args[1] = C.byref(mail,18)
            elif target=='capital': args[3] = C.byref(mail,20)
            elif target=='player_capital': args[3] = C.byref(pid,4)
            else: args[{'table_mail':0,'table_player':1,'table_capital':3}[target]] = C.byref(self.readonly,4)
            before = mail.raw,pid.raw,capital.value,bytes(self.readonly)
            self.assertEqual(self.create(*args),0)
            self.assertEqual((mail.raw,pid.raw,capital.value,bytes(self.readonly)),before)

    def test_rejected_request_can_retry_without_any_runtime_resources(self):
        mail,pid,capital = self.fixture(1)
        self.assertEqual(self.create(C.byref(mail,16),pid,12,C.byref(capital)),0)
        self.assertEqual(self.create(C.byref(mail,16),pid,0,C.byref(capital)),1)
        self.assertEqual(mail.raw[58:180],bytes.fromhex(self.report['cases'][1]['wire']))
        # The library has no native DMA, allocation, date, random, item-name,
        # formatter, or reader imports. Every complete case was proved at build.
        symbols = subprocess.run(['nm','-u',str(Path(self.temporary.name)/'creator.so')],capture_output=True,text=True,check=True).stdout
        self.assertFalse(any(name in symbols for name in ('af_mail','af_load','malloc','memcpy','memset','rand')))


if __name__=='__main__': unittest.main()
