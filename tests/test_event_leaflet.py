"""Complete selected-item capture and publication; not native owner-hook proof."""

import ctypes as C
from copy import deepcopy
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from leaflet_date_scenario import reference_fields
from leaflet_letters import SALE, REDD, fields
from mail_record import Field, Record, pack


@unittest.skipUnless(shutil.which('gcc') and (ROOT/'build/mail-catalog/catalog.bin').is_file(),
                     'Host GCC and local complete catalogue required')
class EventLeafletTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='af-event-leaflet-')
        output = Path(cls.temp.name)/'event.so'
        sources = ('overlays/mail_generation/generate.c', 'overlays/mail_generation/leaflet.c',
                   'overlays/mail_generation/event_leaflet.c', 'overlays/leaflet_dates/hour.c',
                   'runtime/dateformat.c', 'runtime/mail/catalog.c', 'runtime/mail/format.c','runtime/crc32.c',
                   'runtime/mail/record.c', 'tests/mail_catalog_mock.c', 'tests/event_leaflet_mock.c')
        result = subprocess.run(['gcc', '-std=c99', '-Wall', '-Wextra', '-Werror', '-O2', '-shared', '-fPIC',
                                 *(str(ROOT/p) for p in sources), '-o', str(output)], capture_output=True, text=True)
        if result.returncode:
            raise ValueError(result.stderr)
        cls.lib = C.CDLL(str(output))
        cls.lib.af_event_leaflet_publish.argtypes = [C.c_void_p, C.c_uint, C.c_uint, C.c_uint,
                                                   C.c_void_p, C.c_void_p]
        cls.words = reference_fields()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def flag(self, name):
        return C.c_uint.in_dll(self.lib, 'af_event_test_'+name)

    def setUp(self):
        for name in ('loads', 'receipts', 'fail_load', 'fail_receipt', 'bad_mode'):
            self.flag(name).value = 0
        for name, value in (('enabled', 1), ('reads', 0), ('fail_read', 0), ('dma_error', 0)):
            C.c_uint.in_dll(self.lib, 'af_mail_catalog_'+name).value = value
        catalogue = (ROOT/'build/mail-catalog/catalog.bin').read_bytes()
        rom = (C.c_ubyte*0x100000).in_dll(self.lib, 'af_mail_catalog_rom')
        C.memmove(rom, catalogue, len(catalogue))
        self.destination = (C.c_ubyte*168).in_dll(self.lib, 'af_event_test_destination')
        self.destination[:] = bytes(range(168))
        self.source = C.create_string_buffer(bytes(range(156)), 156)
        self.capital = C.c_uint(0)
        self.size = self.lib.af_event_test_work_size()
        self.storage = C.create_string_buffer(b'!'*(self.size+64))
        self.work = (C.addressof(self.storage)+31)&~15
        self.fixture()

    def fixture(self, count=1, hour=0, month=1):
        self.ids = (0x1000, 0x2500, 0x2600)[:count]
        source = bytearray(range(156))
        for at in (0, 12):
            source[at:at+8] = bytes((0, 0, hour, 21, 0, month, 7, 208))
        for i, item in enumerate(self.ids):
            struct.pack_into('>H', source, 28+i*2, item)
        self.source.raw = bytes(source)

    def invoke(self, template=2, count=1, expected=1, source=None, size=156, work=None, capital=None):
        before, state, original = bytes(self.destination), self.capital.value, self.source.raw
        result = self.lib.af_event_leaflet_publish(self.source if source is None else source, size,
                    template, count, C.byref(self.capital) if capital is None else capital,
                    self.work if work is None else work)
        self.assertEqual(result, expected)
        self.assertEqual(self.source.raw, original)
        self.assertEqual(self.capital.value, state)
        self.assertEqual(C.string_at(self.work-16, 16), b'!'*16)
        self.assertEqual(C.string_at(self.work+self.size, 16), b'!'*16)
        self.assertEqual(self.flag('bad_mode').value, 0)
        if not expected:
            self.assertEqual(bytes(self.destination), before)
            return
        source_time = 12 if template in SALE else 0
        hour, day, month = (original[source_time+i] for i in (2, 3, 5))
        slot = 17 if template in SALE else 0
        values = {slot: Field(self.words['months'][month-1].encode().ljust(9, b' ')),
                  slot+1: Field(self.words['days'][day-1].encode().ljust(4, b' ')),
                  slot+2: Field(f'{hour%12 or 12} {self.words["ampm"][hour>=12]}'.encode())}
        if count:
            values[0] = Field(str(count).encode())
            for i, item in enumerate(self.ids):
                values[7+i] = Field(bytes(65+(item+j)%26 for j in range(16)))
        record = Record(2, 0, (template,), tuple((i, values[i]) for i in sorted(fields(template))), bool(state))
        expected_mail = bytearray(164)
        expected_mail[:12] = expected_mail[18:30] = b' '*12
        expected_mail[12:16] = expected_mail[30:34] = b'\xff'*4
        expected_mail[16] = expected_mail[34] = 255
        expected_mail[38:42] = bytes((0, 128, 3 if template in REDD else 2, 54 if template in REDD else 55))
        expected_mail[42:] = pack(record)
        self.assertEqual(bytes(self.destination), bytes(expected_mail)+b'\0\0'+before[166:])
        loaded_ids = (C.c_uint*3).in_dll(self.lib, 'af_event_test_ids')
        self.assertEqual(tuple(loaded_ids)[:count], self.ids)

    def test_all_sale_and_redd_templates_retain_complete_selected_names_and_times(self):
        for template in SALE+REDD:
            count = min(3, 1+(template-2)//4) if template in SALE else 0
            for capital in (0, 1):
                for hour in (0, 11, 12, 23):
                    self.setUp()
                    self.fixture(count, hour, 9)
                    self.capital.value = capital
                    self.invoke(template, count)

    def test_every_item_load_failure_preserves_destination_and_can_retry(self):
        for failure in (1, 2, 3):
            self.setUp()
            self.fixture(3)
            self.flag('fail_load').value = failure
            self.invoke(10, 3, 0)
            self.assertEqual(self.flag('receipts').value, 0)
            self.flag('fail_load').value = self.flag('loads').value = 0
            self.invoke(10, 3)

    def test_catalogue_and_receipt_failures_retain_previous_notice_and_capital(self):
        for failure in ('disabled', 'read', 'receipt'):
            self.setUp()
            self.capital.value = 1
            if failure == 'disabled':
                C.c_uint.in_dll(self.lib, 'af_mail_catalog_enabled').value = 0
            elif failure == 'read':
                C.c_uint.in_dll(self.lib, 'af_mail_catalog_fail_read').value = 1
            else:
                self.flag('fail_receipt').value = 1
            self.invoke(expected=0)

    def test_invalid_and_overlapping_inputs_reject_before_publication(self):
        for arguments in ({'template': 24}, {'count': 0}, {'count': 4}, {'size': 155},
                          {'template': 49, 'count': 1}, {'source': 0}, {'work': self.work+1},
                          {'source': self.work}, {'capital': self.work}, {'capital': 0}):
            self.invoke(expected=0, **arguments)
        self.assertEqual(self.flag('receipts').value, 0)


@unittest.skipUnless((ROOT/'build/event-leaflet-probe/generate.json').is_file(),
                     'Compiled native event publication artifact required')
class EventLeafletArtifactTests(unittest.TestCase):
    def test_current_native_sources_imports_and_relocations_are_bound(self):
        from event_leaflet_sources import evidence
        from mail_generate_probe import validate, relocate
        directory = ROOT/'build/event-leaflet-probe'
        code = (directory/'generate.bin').read_bytes()
        report = json.loads((directory/'generate.json').read_text())
        module = json.loads((ROOT/'build/runtime-module/module.json').read_text())
        self.assertEqual(evidence((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())['receipt_flag_bytes'], 2)
        validate(code, report, module, event_leaflets=True)
        for base in (0x801A0010, 0x802F8010, 0x803FE000):
            self.assertEqual(len(relocate(code, report, module, base, event_leaflets=True)), len(code))
        for options in ({}, {'leaflets': True}, {'fortune_slip': True},
                        {'leaflets': True, 'event_leaflets': True}):
            with self.assertRaises(ValueError):
                validate(code, report, module, **options)
        for key, value in (('sources', {}), ('imports', {}), ('module_sha256', '0'*64),
                           ('jump_relocations', []), ('variant', 'leaflets')):
            changed = deepcopy(report)
            changed[key] = value
            with self.assertRaises(ValueError):
                validate(code, changed, module, event_leaflets=True)


if __name__ == '__main__':
    unittest.main()
