"""Complete renewal publication, native eligibility, retained failure, and heap ownership."""

import ctypes as C
from datetime import date,timedelta
from itertools import permutations
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from leaflet_date_scenario import reference_fields
from mail_record import Field,Record,pack


@unittest.skipUnless(shutil.which('gcc') and (ROOT/'build/mail-catalog/catalog.bin').is_file(),
                     'Host GCC and complete local catalogue required')
class RenewalActorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='af-renewal-actor-')
        output = Path(cls.temp.name)/'actor.so'
        sources = ('overlays/mail_generation/generate.c','overlays/mail_generation/leaflet.c',
                   'overlays/mail_generation/renewal_actor.c','overlays/leaflet_dates/hour.c',
                   'runtime/dateformat.c','runtime/mail/catalog.c','runtime/mail/format.c','runtime/mail/record.c',
                   'tests/mail_catalog_mock.c','tests/renewal_actor_mock.c')
        result = subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-O2','-shared','-fPIC',
                                 *(str(ROOT/p) for p in sources),'-o',str(output)],capture_output=True,text=True)
        if result.returncode: raise ValueError(result.stderr)
        cls.lib = C.CDLL(str(output));cls.lib.af_renewal_deliver.argtypes = [C.c_uint,C.c_void_p]
        cls.words = reference_fields();cls.catalog = (ROOT/'build/mail-catalog/catalog.bin').read_bytes()

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def counter(self,name): return C.c_uint.in_dll(self.lib,'af_renewal_test_'+name)

    def setUp(self):
        for name in ('allocations','frees','live','fail_malloc','bad_heap','bad_free','alignment',
                     'copies','working','event_count','bad_slot'): self.counter(name).value = 0
        for name,value in (('enabled',1),('reads',0),('dma_error',0),('fail_read',0)):
            C.c_uint.in_dll(self.lib,'af_mail_catalog_'+name).value = value
        rom = (C.c_ubyte*0x100000).in_dll(self.lib,'af_mail_catalog_rom')
        C.memset(rom,0,len(rom));C.memmove(rom,self.catalog,len(self.catalog))
        self.save = (C.c_ubyte*0xF980).in_dll(self.lib,'af_renewal_save')
        self.capital = C.c_uint.in_dll(self.lib,'af_mail_generation_capital');self.capital.value = 0
        self.fixture()

    def fixture(self,mapping=(0,1,2,3),slot=0,owners=15,working=0,when=date(2000,9,21)):
        self.mapping = tuple(mapping);self.slot = slot;self.owners = owners
        self.when = when
        self.save[:] = bytes(i%251 for i in range(len(self.save)))
        self.save[0xEF5A] = sum(h<<(p*2) for p,h in enumerate(mapping))
        self.counter('working').value = working
        for home in range(4):
            at = 0x3596+home*0xB48
            self.save[at:at+2] = b'AB' if owners>>home&1 else b'\xff\xff'
            for i in range(10): self.save[0x3A00+home*0xB48+i*164+38] = 255 if i >= slot else 0
        self.rtc = C.create_string_buffer(bytes((0,0,12,when.day,0,when.month,when.year>>8,when.year&255)),8)

    def invoke(self,level=0,success=True,null=False):
        before,capital,rtc,copies = bytes(self.save),self.capital.value,self.rtc.raw,self.counter('copies').value
        self.assertEqual(self.lib.af_renewal_deliver(level,None if null else self.rtc),int(success))
        self.assertEqual(self.rtc.raw,rtc)
        self.assertEqual((self.counter('live').value,self.counter('bad_free').value),(0,0))
        self.assertEqual(C.c_uint.in_dll(self.lib,'af_mail_catalog_dma_error').value,0)
        if not success:
            self.assertEqual((bytes(self.save),self.capital.value,self.counter('copies').value),(before,capital,copies));return
        expected = bytearray(before);count = 0
        when = self.when-timedelta(days=1)
        values = (Field(self.words['months'][when.month-1].encode().ljust(9,b' ')),
                  Field(self.words['days'][when.day-1].encode().ljust(4,b' ')),Field(str(when.year).encode()))
        record = Record(2,0,(24+min(level&3,2),),tuple(enumerate(values)),bool(capital))
        for home in range(4):
            player = self.mapping.index(home) if home in self.mapping else 0  # Original helper's four AND three.
            if self.slot >= 10 or not self.owners>>home&1 or self.counter('working').value>>player&1: continue
            mail = bytearray(164);mail[:16] = before[0x20+player*0xBD0:0x30+player*0xBD0]
            mail[18:30] = b' '*12;mail[30:34] = b'\xff'*4;mail[34] = 255
            mail[38:42] = bytes((0,128,2,55));mail[42:] = pack(record)
            at = 0x3A00+home*0xB48+self.slot*164;expected[at:at+164] = mail;count += 1
        self.assertEqual(bytes(self.save),bytes(expected))
        self.assertEqual(self.capital.value,capital)
        self.assertEqual(self.counter('copies').value,copies+count)

    def test_every_shop_level_home_mapping_and_mailbox_position(self):
        for mapping in permutations(range(4)):
            for level in range(4):
                self.fixture(mapping=mapping,slot=level+6);self.capital.value = level&1;self.invoke(level)
        for slot in range(10): self.fixture(slot=slot);self.invoke(0xFFFFFFFF)
        self.fixture(mapping=(0,0,0,0));self.invoke()  # Preserve original missing-map fallback.

    def test_all_owner_and_working_player_masks_preserve_native_skip_semantics(self):
        for owners in range(16):
            for working in range(16):
                self.fixture(owners=owners,working=working,mapping=(2,0,3,1));self.invoke(2)
        for kind in ('full','owner','working'):
            self.setUp();self.fixture(slot=10 if kind=='full' else 0,owners=0 if kind=='owner' else 15,
                                      working=15 if kind=='working' else 0)
            C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled').value = 0
            self.invoke();self.assertEqual(self.counter('allocations').value,0)

    def test_every_selected_read_failure_retains_all_homes_and_can_retry(self):
        self.invoke();total = C.c_uint.in_dll(self.lib,'af_mail_catalog_reads').value
        for fail in range(1,total+1):
            self.setUp();self.capital.value = 1
            C.c_uint.in_dll(self.lib,'af_mail_catalog_fail_read').value = fail
            self.invoke(success=False)
            C.c_uint.in_dll(self.lib,'af_mail_catalog_fail_read').value = 0
            self.invoke()
            self.assertEqual((self.counter('allocations').value,self.counter('frees').value),(2,2))

    def test_alignment_allocation_invalid_inputs_and_disabled_catalogue_keep_ownership(self):
        for alignment in range(16):
            self.setUp();self.counter('alignment').value = alignment;self.invoke()
        for kind in ('fail_malloc','bad_heap','bad_slot','capital','null','date','disabled'):
            self.setUp()
            if kind in ('fail_malloc','bad_heap'): self.counter(kind).value = 1
            elif kind == 'bad_slot': self.counter(kind).value = 10
            elif kind == 'capital': self.capital.value = 2
            elif kind == 'date': self.fixture(when=date(1901,1,1))
            elif kind == 'disabled': C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled').value = 0
            self.invoke(success=False,null=kind=='null')
        self.setUp();self.invoke()
        events = (C.c_uint*64).in_dll(self.lib,'af_renewal_test_events')
        self.assertEqual(list(events)[:self.counter('event_count').value],[1,2,3,3,3,3,4])


if __name__ == '__main__': unittest.main()
