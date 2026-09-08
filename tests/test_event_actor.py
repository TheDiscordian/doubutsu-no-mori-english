"""Whole English event notices with cached and save-marker retry ownership."""

import ctypes as C
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))


@unittest.skipUnless(shutil.which('gcc') and (ROOT/'build/mail-catalog/catalog.bin').is_file(),
                     'Host GCC and local complete catalogue required')
class EventActorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='af-event-actor-')
        sources = ('overlays/mail_generation/generate.c','overlays/mail_generation/leaflet.c',
                   'overlays/mail_generation/event_leaflet.c','overlays/mail_generation/event_actor.c',
                   'overlays/leaflet_dates/hour.c','runtime/dateformat.c','runtime/mail/catalog.c',
                   'runtime/mail/format.c','runtime/mail/record.c','tests/mail_catalog_mock.c',
                   'tests/event_leaflet_mock.c','tests/event_actor_mock.c')
        output = Path(cls.temp.name)/'event.so'
        result = subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-O2','-shared','-fPIC',
                                 *(str(ROOT/p) for p in sources),'-o',str(output)],capture_output=True,text=True)
        if result.returncode: raise ValueError(result.stderr)
        cls.lib = C.CDLL(str(output))
        cls.lib.af_event_sale_fields.argtypes = [C.c_void_p,C.c_uint]
        cls.lib.af_event_leaflet_publish.argtypes = [C.c_void_p,C.c_uint,C.c_uint,C.c_uint,C.c_void_p,C.c_void_p]
        cls.catalog = (ROOT/'build/mail-catalog/catalog.bin').read_bytes()

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def word(self,name): return C.c_uint.in_dll(self.lib,name)
    def counter(self,name): return self.word('af_event_test_'+name)

    def setUp(self):
        for name in ('loads','receipts','fail_load','fail_receipt','bad_mode','native_inits',
                     'native_fields','native_saves','native_destroys','nonletter'): self.counter(name).value = 0
        for name,value in (('enabled',1),('reads',0),('fail_read',0),('dma_error',0)):
            self.word('af_mail_catalog_'+name).value = value
        rom = (C.c_ubyte*0x100000).in_dll(self.lib,'af_mail_catalog_rom');C.memmove(rom,self.catalog,len(self.catalog))
        self.saved = (C.c_ubyte*156).in_dll(self.lib,'af_event_saved')
        self.flag = C.c_ubyte.in_dll(self.lib,'af_event_init_flag')
        self.pending = (C.c_ubyte*172).in_dll(self.lib,'af_event_pending')
        self.destination = (C.c_ubyte*168).in_dll(self.lib,'af_event_test_destination')
        self.capital = self.word('af_mail_generation_capital');self.capital.value = 0
        self.reload();self.fixture()

    def reload(self):
        self.pending[:] = bytes(172)
        self.word('af_event_count').value = self.word('af_event_busy').value = 0

    def fixture(self,template=2,count=1,capital=0):
        self.counter('template').value = template;self.counter('count').value = count
        self.capital.value = capital;self.flag.value = 1
        self.saved[:] = bytes(range(156))
        for at in (0,12): self.saved[at:at+8] = bytes((0,0,23,21,0,9,7,208))
        self.saved[28:34] = bytes.fromhex('100025002600')
        self.destination[:] = bytes(range(168))

    def reference(self,template,count,capital):
        storage = C.create_string_buffer(self.lib.af_event_test_work_size()+32)
        work = (C.addressof(storage)+15)&~15;state = C.c_uint(capital)
        self.assertEqual(self.lib.af_event_leaflet_publish(self.saved,156,template,count,C.byref(state),work),1)
        output = bytes(self.destination)
        self.destination[:] = bytes(range(168));self.counter('receipts').value = self.counter('loads').value = 0
        return output

    def test_all_valid_choices_preserve_complete_output_and_do_not_duplicate(self):
        for template in (*range(2,18),49,50,51):
            counts = range(1,min(3,1+(template-2)//4)+1) if template < 49 else (0,)
            for count in counts:
                for capital in (0,1):
                    self.setUp();self.fixture(template,count,capital)
                    expected = self.reference(template,count,capital);source = bytes(self.saved)
                    self.assertEqual(self.lib.af_event_special_init(),1)
                    self.assertEqual(bytes(self.destination),expected)
                    self.assertEqual((bytes(self.saved),self.flag.value),(source,0))
                    self.assertEqual(self.lib.af_event_special_init(),1)
                    self.assertEqual((self.counter('native_inits').value,self.counter('receipts').value),(1,1))

    def test_every_choice_can_retry_after_cache_loss_without_reselecting(self):
        for template in (*range(2,18),49,50,51):
            counts = range(1,min(3,1+(template-2)//4)+1) if template < 49 else (0,)
            for count in counts:
                for capital in (0,1):
                    self.setUp();self.fixture(template,count,capital)
                    expected = self.reference(template,count,capital);source = bytes(self.saved)
                    self.word('af_mail_catalog_enabled').value = 0
                    self.assertEqual(self.lib.af_event_special_init(),0)
                    choice = (template-2)*3+count-1 if template < 49 else 48+template-49
                    self.assertEqual(self.flag.value,2+choice*2+capital)
                    self.assertEqual((bytes(self.saved),bytes(self.destination)),(source,bytes(range(168))))
                    self.assertEqual(self.lib.af_event_special_init(),0)
                    self.reload()  # Loaded overlay work disappears; only saved event and flag survive.
                    self.capital.value = 1  # Another letter cannot lose its later sticky capitalization.
                    self.word('af_mail_catalog_enabled').value = 1
                    self.assertEqual(self.lib.af_event_special_init(),1)
                    self.assertEqual((bytes(self.destination),self.capital.value,self.flag.value),(expected,1,0))
                    self.assertEqual(self.counter('native_inits').value,1)

    def test_failed_load_save_destroy_and_changed_source_do_not_publish_stale_notice(self):
        for callback in ('af_event_save','af_event_destroy'):
            self.setUp();self.fixture(10,3)
            self.counter('fail_load').value = 2
            self.assertEqual(self.lib.af_event_special_init(),0)
            marker = self.flag.value;self.saved[31] ^= 1
            self.counter('fail_load').value = 0
            getattr(self.lib,callback)(None,None)
            self.assertEqual((self.flag.value,self.counter('receipts').value),(marker,0))
            self.saved[31] ^= 1
            getattr(self.lib,callback)(None,None)
            self.assertEqual((self.flag.value,self.counter('receipts').value),(0,1))
            self.assertEqual(self.counter('native_saves' if callback.endswith('save') else 'native_destroys').value,2)
        self.setUp();self.word('af_mail_catalog_enabled').value = 0
        self.assertEqual(self.lib.af_event_special_init(),0)
        self.fixture(51,0);self.word('af_mail_catalog_enabled').value = 1
        self.assertEqual(self.lib.af_event_special_init(),1)
        self.assertEqual(self.counter('native_inits').value,2)

    def test_invalid_flags_arguments_reentrance_and_nonletter_results(self):
        valid = {2+((t-2)*3+c-1)*2+k for t in range(2,18)
                 for c in range(1,min(3,1+(t-2)//4)+1) for k in (0,1)}|set(range(98,104))
        for marker in set(range(2,256))-valid:
            self.setUp();self.flag.value = marker
            self.assertEqual(self.lib.af_event_special_init(),0)
            self.assertEqual((self.flag.value,self.counter('receipts').value),(marker,0))
        for template,count,paper,type_ in ((2,2,55,2),(2,0,55,2),(10,4,55,2),(2,1,54,2),
                                           (49,0,55,3),(49,0,54,2),(24,0,55,2)):
            self.setUp();self.word('af_event_count').value = count
            self.assertEqual(self.lib.af_event_register(template,paper,type_),0)
            self.assertEqual((self.flag.value,self.counter('receipts').value),(1,0))
        self.setUp();self.word('af_event_busy').value = 1
        self.assertEqual(self.lib.af_event_special_init(),0)
        self.assertEqual(self.counter('native_inits').value,0)
        for state,result in ((1,1),(2,0)):
            self.setUp();self.counter('nonletter').value = state
            self.assertEqual(self.lib.af_event_special_init(),result)
            self.assertEqual(self.flag.value,1-result)


if __name__ == '__main__': unittest.main()
