"""Candidate classic snapshots preserve whole text, metadata, and native fallback."""
import ctypes as C
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from audit_mail_templates import template_fields
from mail_catalog import templates
from mail_format import format_letter
from mail_record import Field, Record, pack, unpack
from test_npc_mail_capture import Work, Session
from test_mail_format import CText

IDS = (0, 1, 0x4D, *range(0x53, 0x57), *range(0x58, 0x5C), 0xBF, 0x182, 0x183, *range(0x186, 0x18A))
CATALOG = ROOT/'build/mail-glyph-catalog/catalog.bin'


@unittest.skipUnless(shutil.which('gcc') and CATALOG.is_file(), 'Host compiler and local verified catalogue required')
class ClassicLettersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='af-classic-letters-')
        output = Path(cls.temp.name)/'classic.so'
        sources = ['overlays/classic_letters/creator.c', 'overlays/classic_letters/hook.c',
                   'overlays/mail_generation/npc_creator.c', 'runtime/mail/record.c', 'runtime/crc32.c',
                   'tests/classic_letters_mock.c', 'tests/accent_mail_mock.c']
        sources += ['overlays/accent_mail/'+n+'.c' for n in ('format', 'catalog', 'generate', 'literal', 'view', 'install')]
        flags = ['-Daf_mail_capture_set=af_accent_capture_set', '-Daf_mail_generate=af_accent_mail_generate']
        result = subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-O2', '-shared', '-fPIC',
                                 *flags, *(str(ROOT/p) for p in sources), '-o', str(output)], capture_output=True, text=True)
        if result.returncode:
            raise ValueError(result.stderr)
        cls.lib = C.CDLL(str(output))
        cls.lib.af_classic_load.argtypes = [C.c_void_p]*4+[C.c_uint]
        cls.lib.af_classic_mail_create.argtypes = [C.c_void_p]*4
        cls.lib.af_classic_test_mask.argtypes = [C.c_uint]
        cls.lib.af_classic_test_mask.restype = C.c_uint
        cls.size = cls.lib.af_classic_test_work_bytes()
        cls.text = cls.lib.af_classic_test_text_offset()
        cls.catalog = CATALOG.read_bytes()

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def scalar(self, name):
        return C.c_uint.in_dll(self.lib, 'af_classic_test_'+name)

    def setUp(self):
        for name in ('loads', 'fallbacks', 'delegations', 'fail_load', 'capital', 'flushes', 'errors'):
            self.scalar(name).value = 0
        self.fields = (C.c_ubyte*200).in_dll(self.lib, 'af_classic_test_fields')
        self.fields[:] = b'English   '*20
        self.rom = (C.c_ubyte*0x200000).in_dll(self.lib, 'af_mail_catalog_rom')
        C.memmove(C.addressof(self.rom)+0xA0000, self.catalog, len(self.catalog))
        for name in ('af_mail_catalog_reads', 'af_mail_catalog_fail_read', 'af_mail_catalog_dma_error'):
            C.c_uint.in_dll(self.lib, name).value = 0

    def tearDown(self):
        self.assertEqual(self.scalar('errors').value, 0)

    def expected(self, number):
        parts = templates(self.catalog, Record(4, 0, (number,), ()))
        slots = sorted(set().union(*(template_fields(p, extended_glyphs=True) for p in parts.parts)))
        return Record(4, 0, (number,), tuple((i, Field(b'English   ')) for i in slots)), parts

    def test_all_selected_parts_masks_snapshots_and_metadata_retention(self):
        self.assertEqual(tuple(n for n in range(544) if self.lib.af_classic_test_mask(n) != 0xFFFFFFFF), IDS)
        for number in IDS:
            record, parts = self.expected(number)
            self.assertEqual(self.lib.af_classic_test_mask(number), sum(1 << i for i, _ in record.fields))
            memory = C.create_string_buffer(b'!'*16+bytes(range(164))+b'!'*16, 196)
            before = memory.raw
            split = C.c_uint(0xA5A5)
            self.lib.af_classic_load(C.byref(memory, 58), C.byref(split), C.byref(memory, 164), C.byref(memory, 68), number)
            self.assertEqual(split.value, 128)
            self.assertEqual(memory.raw[58:180], pack(record))
            self.assertEqual(unpack(memory.raw[58:180], expected_catalog=4), record)
            self.assertEqual(memory.raw[:58]+memory.raw[180:], before[:58]+before[180:])
            self.assertTrue(format_letter(record, parts).body)
        self.assertEqual(self.scalar('loads').value, len(IDS))
        self.assertEqual(self.scalar('fallbacks').value, 0)

    def test_native_fallback_preserves_argument_order_and_sizes(self):
        header, body, footer = (C.create_string_buffer(b'!'*(n+32), n+32) for n in (10, 96, 16))
        split = C.c_uint(9)
        self.lib.af_classic_load(C.byref(header, 16), C.byref(split), C.byref(footer, 16), C.byref(body, 16), 0x182)
        self.assertEqual(header.raw, b'!'*16+b'H'*10+b'!'*16)
        self.assertEqual(body.raw, b'!'*16+b'B'*96+b'!'*16)
        self.assertEqual(footer.raw, b'!'*16+b'F'*16+b'!'*16)
        self.assertEqual(split.value, 3)
        self.assertEqual(self.scalar('loads').value, 0)
        for number, fail in ((0xC0, 0), (0x182, 1)):
            self.scalar('fail_load').value = fail
            memory = C.create_string_buffer(b'!'*154, 154)
            self.lib.af_classic_load(C.byref(memory, 16), C.byref(split), C.byref(memory, 122), C.byref(memory, 26), number)
            self.assertEqual(memory.raw, b'!'*16+b'H'*10+b'B'*96+b'F'*16+b'!'*16)
            self.assertEqual(split.value, 3)
        self.assertEqual(self.scalar('fallbacks').value, 3)

    def fixture(self, number=0x53):
        memory = C.create_string_buffer(b'!'*(self.size+64), self.size+64)
        address = (C.addressof(memory)+31)&~15
        capture = Work.from_address(address)
        player = C.create_string_buffer(b'P'*16, 16)
        request = C.create_string_buffer(b'AFCL'+number.to_bytes(2, 'big')+bytes(5)+b'\xf0', 12)
        capture.session = Session(None, None, C.addressof(player), C.addressof(request), None, 0, 0, 0)
        output = C.create_string_buffer(b'!'*196, 196)
        active, capital = C.c_void_p(), C.c_uint(0)
        return memory, address, capture, player, request, output, active, capital

    def test_creator_rejects_bad_inputs_and_delegates_other_markers(self):
        for failure in ('descriptor', 'id', 'capital', 'active', 'literal', 'dma', 'overlap'):
            fixture = self.fixture()
            memory, address, capture, player, request, output, active, capital = fixture
            if failure == 'descriptor': request[8] = b'X'
            if failure == 'id': request[5] = b'\xc0'
            if failure == 'capital': capital.value = 2
            if failure == 'active': active.value = address
            if failure == 'literal': self.fields[10] = 0xF7
            if failure == 'dma': C.c_uint.in_dll(self.lib, 'af_mail_catalog_fail_read').value = 1
            destination = address if failure == 'overlap' else C.addressof(output)+16
            before = output.raw, capital.value, active.value
            self.assertEqual(self.lib.af_classic_mail_create(address, destination, C.byref(active), C.byref(capital)), 0)
            self.assertEqual((output.raw, capital.value, active.value), before)
            lead = address-C.addressof(memory)
            self.assertEqual(memory.raw[:lead]+memory.raw[lead+self.size:], b'!'*64)
            self.fields[:] = b'English   '*20
            C.c_uint.in_dll(self.lib, 'af_mail_catalog_fail_read').value = 0
            C.c_uint.in_dll(self.lib, 'af_mail_catalog_reads').value = 0
        fixture = self.fixture()
        fixture[4][11] = b'\xf3'
        self.assertEqual(self.lib.af_classic_mail_create(fixture[1], C.byref(fixture[5], 16), C.byref(fixture[6]), C.byref(fixture[7])), 7)
        self.assertEqual(self.scalar('delegations').value, 1)

    def test_complete_formatted_output_matches_frozen_catalogue(self):
        for number in (1, 0x53, 0x182):
            fixture = self.fixture(number)
            self.assertEqual(self.lib.af_classic_mail_create(fixture[1], C.byref(fixture[5], 16), C.byref(fixture[6]), C.byref(fixture[7])), 1)
            record, parts = self.expected(number)
            expected = format_letter(record, parts)
            actual = CText.from_address(fixture[1]+self.text)
            self.assertEqual(tuple(bytes(actual.text[o:o+n]) for o, n in zip(actual.offsets, actual.lengths)),
                             (expected.header, expected.body, expected.footer))

    def test_startup_guard_precedes_existing_font_install_and_cache_publication(self):
        entry = (C.c_uint*2).in_dll(self.lib, 'af_classic_test_entry')
        world = C.c_uint.in_dll(self.lib, 'af_accent_test_world_calls')
        world.value = 0
        for index in range(2):
            entry[:] = (0x27BDFFE8, 0xAFA60020)
            entry[index] ^= 1
            before = tuple(entry)
            self.assertEqual(self.lib.af_classic_install(), 0)
            self.assertEqual(tuple(entry), before)
            self.assertEqual(world.value, 0)
        entry[:] = (0x27BDFFE8, 0xAFA60020)
        hooks = (C.c_uint*8).in_dll(self.lib, 'af_accent_test_hooks')
        hooks[:] = (0x27BDFB38, 0xAFBF04C4, 0x14800003, 0, 0x1080003A, 0x1025, 0x14800003, 0x1025)
        ready = C.c_uint.in_dll(self.lib, 'af_accent_test_world_ok')
        ready.value = 0
        self.assertEqual(self.lib.af_classic_install(), 0)
        self.assertEqual(tuple(entry), (0x27BDFFE8, 0xAFA60020))
        self.assertEqual(self.scalar('flushes').value, 0)
        ready.value = 1
        self.assertEqual(self.lib.af_classic_install(), 1)
        self.assertEqual((entry[0] >> 26, entry[1]), (2, 0))
        self.assertEqual(self.scalar('flushes').value, 2)


if __name__ == '__main__':
    unittest.main()
