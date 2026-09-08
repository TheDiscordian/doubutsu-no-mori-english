"""Full leaflet creation, source identities, date semantics, and retained failure."""

import ctypes as C
from datetime import date,timedelta
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
from leaflet_letters import RENEWAL,REDD,SALE,TEMPLATES,fields,verify_templates
from leaflet_date_scenario import reference_fields
from mail_catalog import templates
from mail_format import format_letter
from mail_record import Field,Record,pack,unpack
from test_mail_format import CField,CText,inplace_reference

ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'
CATALOG = ROOT/'build/mail-catalog/catalog.bin'


class Choice(C.Structure):
    _fields_ = [('template_id',C.c_ushort),('year',C.c_ushort),
                ('month',C.c_ubyte),('day',C.c_ubyte),('hour',C.c_ubyte),('item_count',C.c_ubyte),
                ('items',C.c_ushort*3)]


class Item(C.Structure):
    _fields_ = [('item',C.c_ushort),('name',CField)]


@unittest.skipUnless(ROM.is_file() and CATALOG.is_file(),'Local native ROM and supplied catalogue required')
class LeafletSourceTests(unittest.TestCase):
    def test_all_66_complete_parts_and_native_field_identities(self):
        report = verify_templates(ROM.read_bytes(),CATALOG.read_bytes())
        self.assertEqual(len(report['parts']),66)
        self.assertEqual(report['classic_templates'],list(TEMPLATES))
        self.assertFalse(report['native_delivery_installed'])
        self.assertEqual(fields(2),{7,17,18,19})
        self.assertEqual(fields(6),{17,18,19})
        self.assertEqual(fields(6,native=True),{0,17,18,19})
        with self.assertRaises(ValueError): fields(18)
        data = bytearray(CATALOG.read_bytes());data[-64] ^= 1
        with self.assertRaises(ValueError): verify_templates(ROM.read_bytes(),bytes(data))

    @unittest.skipUnless((ROOT/'build/leaflet-letters-probe/generate.json').is_file(),'Compiled leaflet code required')
    def test_probe_variant_complete_imports_relocations_and_owned_bounds(self):
        from mail_generate_probe import validate,relocate
        path = ROOT/'build/leaflet-letters-probe'
        code = (path/'generate.bin').read_bytes();report = json.loads((path/'generate.json').read_text())
        module = json.loads((ROOT/'build/runtime-module/module.json').read_text())
        validate(code,report,module,leaflets=True)
        with self.assertRaises(ValueError): validate(code,report,module)
        with self.assertRaises(ValueError): validate(code,report,module,leaflets=True,fortune_slip=True)
        for base in (0x801A0010,0x802F8010,0x803F0000):
            self.assertEqual(len(relocate(code,report,module,base,leaflets=True)),len(code))
        for key,value in (('variant',None),('sources',{}),('jump_relocations',[]),('imports',{})):
            changed = deepcopy(report);changed[key] = value
            with self.assertRaises(ValueError): validate(code,changed,module,leaflets=True)
        for base in (0,0x801948E0,0x80200001,0x80400000):
            with self.assertRaises(ValueError): relocate(code,report,module,base,leaflets=True)


@unittest.skipUnless(shutil.which('gcc') and ROM.is_file() and CATALOG.is_file(),
                     'Host GCC and local catalogue required')
class LeafletRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = CATALOG.read_bytes();verify_templates(ROM.read_bytes(),cls.catalog)
        cls.words = reference_fields()
        cls.temporary = tempfile.TemporaryDirectory(prefix='af-leaflet-')
        library = Path(cls.temporary.name)/'leaflet.so'
        sources = ('overlays/mail_generation/generate.c','overlays/mail_generation/leaflet.c',
                   'overlays/leaflet_dates/hour.c','runtime/dateformat.c','runtime/mail/catalog.c',
                   'runtime/mail/format.c','runtime/mail/record.c','tests/mail_catalog_mock.c','tests/leaflet_mock.c')
        subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-O2','-shared','-fPIC',
                        *(str(ROOT/source) for source in sources),'-o',str(library)],
                       check=True,capture_output=True)
        cls.lib = C.CDLL(str(library))
        cls.lib.af_leaflet_create.argtypes = [C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p]
        cls.work_size = cls.lib.af_leaflet_test_work_size()
        cls.text_offset = cls.lib.af_leaflet_test_text_offset()

    @classmethod
    def tearDownClass(cls): cls.temporary.cleanup()

    def setUp(self):
        self.rom = (C.c_ubyte*0x100000).in_dll(self.lib,'af_mail_catalog_rom')
        C.memset(self.rom,0,len(self.rom));C.memmove(self.rom,self.catalog,len(self.catalog))
        for key,value in (('enabled',1),('reads',0),('dma_error',0),('fail_read',0)):
            C.c_uint.in_dll(self.lib,'af_mail_catalog_'+key).value = value

    def fixture(self,id=49,when=date(2000,9,21),hour=12,count=None,capital=0):
        count = min(3,1+(id-2)//4) if count is None and id in SALE else count or 0
        choice = Choice(id,when.year,when.month,when.day,hour,count)
        items = (Item*count)() if count else None
        for i in range(count):
            choice.items[i] = 0x1000+i*4;items[i].item = choice.items[i]
            value = (b'synthetic name '+bytes((65+i,))).ljust(16,b' ')
            items[i].name = CField(16,i,(C.c_ubyte*16)(*value))
        mail = C.create_string_buffer(b'!'*16+bytes(range(164))+b'!'*16,196)
        state = C.c_uint(capital)
        memory = C.create_string_buffer(b'!'*(self.work_size+64),self.work_size+64)
        work = (C.addressof(memory)+31)&~15
        return mail,choice,items,state,memory,work

    def invoke(self,fixture,success=True,changed=None):
        mail,choice,items,capital,memory,work = fixture
        before = mail.raw,bytes(choice),bytes(items) if items is not None else None,capital.value,memory.raw
        args = [C.addressof(mail)+16,164,C.addressof(choice),C.addressof(items) if items is not None else 0,
                C.addressof(capital),work]
        if changed: args[changed[0]] = changed[1]
        self.assertEqual(self.lib.af_leaflet_create(*args),int(success))
        self.assertEqual((bytes(choice),bytes(items) if items is not None else None),before[1:3])
        lead = work-C.addressof(memory)
        self.assertEqual(memory.raw[:lead]+memory.raw[lead+self.work_size:],b'!'*64)
        self.assertEqual(mail.raw[:16]+mail.raw[180:],b'!'*32)
        if not success:
            self.assertEqual((mail.raw,capital.value),(before[0],before[3]));return
        id = choice.template_id;when = date(choice.year,choice.month,choice.day)
        if id in RENEWAL: when -= timedelta(days=1)
        start = 17 if id in SALE else 0
        values = {start:Field(self.words['months'][when.month-1].encode().ljust(9,b' ')),
                  start+1:Field(self.words['days'][when.day-1].encode().ljust(4,b' ')),
                  start+2:Field(str(when.year).encode() if id in RENEWAL else
                      f'{choice.hour%12 or 12} {self.words["ampm"][int(choice.hour>=12)]}'.encode())}
        if id in SALE:
            values[0] = Field(str(choice.item_count).encode())
            for i,item in enumerate(items): values[7+i] = Field(bytes(item.name.text),item.name.article)
        record = Record(2,0,(id,),tuple((slot,values[slot]) for slot in sorted(fields(id))),bool(before[3]))
        expected = bytearray(before[0][16:180])
        expected[38:42] = bytes((0,128,3 if id in REDD else 2,54 if id in REDD else 55))
        expected[42:] = pack(record)
        self.assertEqual(mail.raw[16:180],bytes(expected))
        self.assertEqual(unpack(mail.raw[58:180],expected_catalog=2),record)
        letter = format_letter(record,templates(self.catalog,record))
        self.assertEqual(letter,inplace_reference(record,templates(self.catalog,record)))
        actual = CText.from_address(work+self.text_offset)
        self.assertEqual(tuple(bytes(actual.text[o:o+n]) for o,n in zip(actual.offsets,actual.lengths)),
                         (letter.header,letter.body,letter.footer))
        self.assertEqual(capital.value,int(letter.final_capital))
        self.assertEqual(C.c_uint.in_dll(self.lib,'af_mail_catalog_dma_error').value,0)
        return record

    def test_all_22_templates_months_both_capitals_and_full_wording(self):
        for id in TEMPLATES:
            for month in range(1,13):
                for capital in range(2):
                    self.invoke(self.fixture(id,date(2000,month,21),month+11,capital=capital))

    def test_closed_day_at_every_month_boundary_in_supported_years(self):
        for year in range(1901,2100):
            for month in range(1,13):
                self.invoke(self.fixture(24+(month%3),date(year,month,1)),not(year==1901 and month==1))

    def test_all_sale_counts_and_full_item_fields_without_stale_padding(self):
        for id in SALE:
            for count in range(1,min(3,1+(id-2)//4)+1): self.invoke(self.fixture(id,count=count))
        fixture = self.fixture(2);first = self.invoke(fixture)
        fixture[2][0].name.text[:] = b'A'.ljust(16,b' ')
        self.assertNotEqual(self.invoke(fixture),first)

    def test_every_read_failure_and_disabled_catalog_retain_letter_and_capital(self):
        for id in (2,24,49):
            reads = C.c_uint.in_dll(self.lib,'af_mail_catalog_reads');reads.value = 0
            self.invoke(self.fixture(id));total = reads.value
            fail = C.c_uint.in_dll(self.lib,'af_mail_catalog_fail_read')
            for index in range(1,total+1):
                reads.value,fail.value = 0,index;self.invoke(self.fixture(id,capital=1),False)
            fail.value = 0
        C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled').value = 0
        self.invoke(self.fixture(),False)

    def test_invalid_choices_item_identity_capacity_commands_and_input_ownership(self):
        for field,value in (('template_id',0),('template_id',18),('template_id',27),('template_id',52),
                            ('year',1900),('year',2100),('month',0),('month',13),('day',0),('day',32),
                            ('hour',24),('item_count',4)):
            fixture = self.fixture();setattr(fixture[1],field,value);self.invoke(fixture,False)
        fixture = self.fixture(49,date(2001,2,28));fixture[1].day = 29;self.invoke(fixture,False)
        fixture = self.fixture(49,date(2000,4,30));fixture[1].day = 31;self.invoke(fixture,False)
        self.invoke(self.fixture(capital=2),False)
        self.invoke(self.fixture(2,count=2),False)
        fixture = self.fixture(2);fixture[1].item_count = 0;self.invoke(fixture,False)
        fixture = self.fixture(2);fixture[2][0].item += 1;self.invoke(fixture,False)
        fixture = self.fixture(2);fixture[2][0].name.article = 5;self.invoke(fixture,False)
        fixture = self.fixture(2);fixture[1].items[2] = 0x1008;self.invoke(fixture,False)
        for width in (0,10,15,17):
            fixture = self.fixture(2);fixture[2][0].name.length = width;self.invoke(fixture,False)
        for byte in (0x7F,0x80):
            fixture = self.fixture(2);fixture[2][0].name.text[0] = byte;self.invoke(fixture,False)
        fixture = self.fixture(2)
        for index in (0,2,3,4,5): self.invoke(fixture,False,(index,0))
        for index,value in ((1,163),(1,165),(2,C.addressof(fixture[1])+1),
                            (3,C.addressof(fixture[2])+1),(4,C.addressof(fixture[3])+1),(5,fixture[5]+1)):
            self.invoke(fixture,False,(index,value))
        addresses = {0:C.addressof(fixture[0])+16,2:C.addressof(fixture[1]),3:C.addressof(fixture[2]),
                     4:C.addressof(fixture[3]),5:fixture[5]}
        for index in (0,4,5):
            for other,address in addresses.items():
                if index != other: self.invoke(fixture,False,(index,address))


if __name__ == '__main__': unittest.main()
