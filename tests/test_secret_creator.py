"""Complete compact secret letters with guarded, metadata-preserving writes."""

import ctypes as C
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from audit_secret_letters import snapshots
from mail_record import unpack


@unittest.skipUnless((ROOT/'build/mail-glyph-catalog/catalog.bin').is_file(),'Local complete letter inputs required')
class SecretCreatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table,cls.report = snapshots((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                                         (ROOT/'build/mail-glyph-catalog/catalog.bin').read_bytes())
        cls.temporary = tempfile.TemporaryDirectory(prefix='af-secret-creator-')
        out = Path(cls.temporary.name);(out/'snapshots.bin').write_bytes(cls.table)
        flags = ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer','-g'] if os.environ.get('AF_SECRET_SANITIZE')=='1' else []
        subprocess.run(['gcc','-std=c99','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',*flags,
                        str(ROOT/'overlays/mail_generation/secret_creator.c'),str(ROOT/'tests/secret_creator_data.s'),
                        '-o',str(out/'creator.so')],cwd=out,check=True,capture_output=True)
        cls.lib = C.CDLL(str(out/'creator.so'));cls.create = cls.lib.af_secret_create
        cls.create.argtypes = [C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p]
        cls.readonly = (C.c_ubyte*600).in_dll(cls.lib,'af_secret_templates')

    @classmethod
    def tearDownClass(cls): cls.temporary.cleanup()

    def fixture(self,capital=0):
        return C.create_string_buffer(b'!'*164,164),C.c_uint(0x12345678),C.c_uint(capital)

    def test_all_thirty_records_preserve_unowned_metadata_and_guards(self):
        for case in self.report['cases']:
            mail,selected,capital = self.fixture(case['capital'])
            with self.subTest(template=case['template'],capital=case['capital']):
                self.assertEqual(self.create(C.byref(mail,16),C.byref(selected),case['template']-0x22,C.byref(capital)),1)
                expected = bytearray(b'!'*132);expected[0] = 0;expected[4] = 128
                expected[5:127] = bytes.fromhex(case['wire'])
                self.assertEqual(mail.raw,b'!'*16+bytes(expected)+b'!'*16)
                self.assertEqual(capital.value,bytes.fromhex(case['text'])[14]);self.assertEqual(selected.value,0x12345678)
                self.assertEqual(unpack(bytes(expected[5:127]),expected_catalog=4).templates,(case['template'],))
        self.assertEqual(bytes(self.readonly),self.table)

    def test_invalid_choices_capitals_addresses_and_alignments_retain_outputs(self):
        for argument,values in ((2,(15,16,0xFFFFFFFF)),(0,(None,1,4,15)),(1,(None,1,4,15)),(3,(None,1,4,15))):
            for value in values:
                mail,selected,capital = self.fixture(1);args = [C.byref(mail,16),C.byref(selected),0,C.byref(capital)]
                args[argument] = value;self.assertEqual(self.create(*args),0)
                self.assertEqual((mail.raw,selected.value,capital.value),(b'!'*164,0x12345678,1))
        for value in (2,255,0xFFFFFFFF):
            mail,selected,capital = self.fixture(value)
            self.assertEqual(self.create(C.byref(mail,16),C.byref(selected),0,C.byref(capital)),0)
            self.assertEqual((mail.raw,selected.value,capital.value),(b'!'*164,0x12345678,value))
        for argument in (0,1,3):
            mail,selected,capital = self.fixture(1);args = [C.byref(mail,16),C.byref(selected),0,C.byref(capital)]
            args[argument] = C.byref(mail,17)
            self.assertEqual(self.create(*args),0);self.assertEqual(mail.raw,b'!'*164)

    def test_overlaps_and_table_aliases_are_rejected_before_writes(self):
        for target in ('selected','capital','selected_capital','table_mail','table_selected','table_capital'):
            mail,selected,capital = self.fixture(1);args = [C.byref(mail,16),C.byref(selected),0,C.byref(capital)]
            if target=='selected': args[1] = C.byref(mail,20)
            elif target=='capital': args[3] = C.byref(mail,20)
            elif target=='selected_capital': args[1] = C.byref(capital)
            else: args[{'table_mail':0,'table_selected':1,'table_capital':3}[target]] = C.byref(self.readonly,4)
            self.assertEqual(self.create(*args),0)
            self.assertEqual((mail.raw,selected.value,capital.value,bytes(self.readonly)),(b'!'*164,0x12345678,1,self.table))

    def test_retry_needs_no_letter_allocation_or_text_read(self):
        mail,selected,capital = self.fixture(1)
        self.assertEqual(self.create(C.byref(mail,16),C.byref(selected),15,C.byref(capital)),0)
        self.assertEqual(self.create(C.byref(mail,16),C.byref(selected),0,C.byref(capital)),1)
        self.assertEqual(mail.raw[21:143],bytes.fromhex(self.report['cases'][1]['wire']))
        symbols = subprocess.run(['nm','-u',str(Path(self.temporary.name)/'creator.so')],capture_output=True,text=True,check=True).stdout
        self.assertFalse(any(name in symbols for name in ('af_mail','af_load','malloc','memcpy','memset','rand')))


if __name__=='__main__': unittest.main()
