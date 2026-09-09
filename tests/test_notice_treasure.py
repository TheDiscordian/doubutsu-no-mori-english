"""Complete treasure bodies, original clues, compact storage, and atomic failure."""

import ctypes as C
from dataclasses import replace
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from mail_catalog import parse
from mail_record import Field, Record
from notice_record import pack
from notice_treasure import body, fields_for, valid
import test_notice_initial as initial

NoticeText, CATALOG = initial.NoticeText, initial.CATALOG


@unittest.skipUnless(CATALOG.is_file(), 'Supplied complete local catalogue required')
class NoticeTreasureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = CATALOG.read_bytes()
        cls.banks = parse(cls.catalog)[1]
        cls.temporary = tempfile.TemporaryDirectory(prefix='af-notice-treasure-')
        library = Path(cls.temporary.name)/'treasure.so'
        sources = ['runtime/mail/record.c', 'runtime/mail/format.c', 'runtime/mail/catalog.c',
                   'runtime/crc32.c', 'runtime/notice/record.c', 'runtime/notice/treasure.c',
                   'tests/mail_catalog_mock.c', 'tests/notice_workspace_mock.c']
        flags = ['-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                 '-fno-omit-frame-pointer', '-g'] if os.environ.get('AF_NOTICE_SANITIZE') == '1' else []
        environment = dict(os.environ)
        environment.pop('LD_PRELOAD', None)
        result = subprocess.run(['gcc', '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
                                 *flags, *(str(ROOT/p) for p in sources), '-o', str(library)],
                                capture_output=True, text=True, env=environment)
        if result.returncode: raise ValueError(result.stderr)
        cls.lib = C.CDLL(str(library))
        cls.restore = cls.lib.af_notice_treasure_restore
        cls.restore.argtypes = [C.c_void_p, C.c_void_p, C.c_uint, C.c_void_p]
        cls.workspace_size = cls.lib.af_notice_workspace_size()
        cls.rom = (C.c_ubyte*0x100000).in_dll(cls.lib, 'af_mail_catalog_rom')

    @classmethod
    def tearDownClass(cls): cls.temporary.cleanup()

    setUp = initial.NoticeInitialTests.setUp
    fixtures = initial.NoticeInitialTests.fixtures

    def record(self, number, capital=0, article=0):
        samples = {1: Field(b'ABCDEFGHIJKLMNOP'), 2: Field(b'abcdefghijklmnop', article),
                   3: Field(b'6'), 4: Field(b'5'), 5: Field(b'town  ')}
        return Record(4, 0, (number,), tuple((i, samples[i]) for i in fields_for(number)), bool(capital))

    def restored(self, value):
        wire = pack(value)
        source = C.create_string_buffer(b'@'*16+wire+b'@'*24, 136)
        output, work = self.fixtures()
        self.assertEqual(self.restore(C.byref(output, 16), C.byref(source, 16), 96, C.byref(work, 16)), 1)
        result = NoticeText.from_buffer_copy(output.raw[16:-16])
        expected = body(value, self.banks)
        self.assertEqual(result.length, len(expected))
        self.assertEqual(bytes(result.text), expected.ljust(1024, b'\0'))
        self.assertEqual(source.raw, b'@'*16+wire+b'@'*24)
        self.assertEqual(output.raw[:16]+output.raw[-16:], b'!'*32)
        self.assertEqual(work.raw[:16]+work.raw[-16:], b'?'*32)
        self.assertEqual(C.c_uint.in_dll(self.lib, 'af_mail_catalog_dma_error').value, 0)
        return expected

    def test_all_eighteen_bodies_all_articles_and_both_capitals(self):
        for number in range(0x1F0, 0x202):
            for capital in (0, 1):
                for article in range(5):
                    value = self.record(number, capital, article)
                    self.assertEqual(valid(value), pack(value))
                    text = self.restored(value)
                    self.assertEqual(text.count(b'\xcd'), self.banks['mail'][number].count(b'\xcd'))
                    self.assertEqual(text.endswith(b'\xcd'), self.banks['mail'][number].endswith(b'\xcd'))

    def test_native_specific_post_keeps_town_and_row_but_never_reveals_item(self):
        for capital in (0, 1):
            text = self.restored(self.record(0x1F4, capital))
            self.assertTrue(text.startswith((b'Town' if capital else b'town')+b"'s Treasure Hunt!\xcd"))
            self.assertIn(b'6 acres', text)
            self.assertNotIn(b'abcdefghijklmnop', text)
            self.assertEqual(text.split(b'\xcd')[2], b'')
            self.assertTrue(text.endswith(b'      +ABCDEFGHIJKLMNOP+\xcd'))

    def rejected(self, wire, size=96):
        source = C.create_string_buffer(wire, len(wire))
        output, work = self.fixtures()
        self.assertEqual(self.restore(C.byref(output, 16), source, size, C.byref(work, 16)), 0)
        self.assertEqual(output.raw, b'!'*len(output))
        self.assertEqual(source.raw, wire)
        self.assertEqual(work.raw[:16]+work.raw[-16:], b'?'*32)

    def test_malformed_semantic_fields_do_not_publish_partial_output(self):
        value = self.record(0x1F0)
        for index, field in ((1, Field(b'')), (1, Field(b' '*16)), (1, Field(b'name', 1)),
                             (2, Field(b'bad\xcditem')), (3, Field(b'A')), (3, Field(b'0')),
                             (3, Field(b'7')), (3, Field(b'12')), (4, Field(b'6'))):
            fields = tuple((i, field if i == index else old) for i, old in value.fields)
            changed = replace(value, fields=fields)
            with self.assertRaises(ValueError): valid(changed)
            self.rejected(pack(changed))
        for number in (0x1EF, 0x202, 0x1E): self.rejected(pack(replace(value, templates=(number,))))
        self.rejected(pack(replace(value, fields=value.fields+((5, Field(b'town')),))))
        self.rejected(pack(replace(self.record(0x1F4), fields=((1, Field(b'name')), (3, Field(b'1')), (5, Field(b'toolong'))))))
        wire = bytearray(pack(value))
        for index in (0, 3, 15, 95):
            wire[index] ^= 1
            self.rejected(bytes(wire))
            wire[index] ^= 1
        for size in (0, 95, 97): self.rejected(bytes(wire), size)

    def test_every_cartridge_read_failure_retains_output_then_retries(self):
        reads = C.c_uint.in_dll(self.lib, 'af_mail_catalog_reads')
        failure = C.c_uint.in_dll(self.lib, 'af_mail_catalog_fail_read')
        for number in range(0x1F0, 0x202):
            value = self.record(number, 1, 2)
            reads.value = 0
            self.restored(value)
            count = reads.value
            for index in range(1, count+1):
                reads.value, failure.value = 0, index
                self.rejected(pack(value))
            failure.value = 0
            self.restored(value)

    def test_output_input_overlap_supported_and_workspace_overlap_rejected(self):
        value = self.record(0x1F4, 1)
        wire = pack(value)
        output, work = self.fixtures()
        C.memmove(C.byref(output, 16), wire, 96)
        self.assertEqual(self.restore(C.byref(output, 16), C.byref(output, 16), 96, C.byref(work, 16)), 1)
        result = NoticeText.from_buffer_copy(output.raw[16:-16])
        self.assertEqual(bytes(result.text[:result.length]), body(value, self.banks))
        C.memmove(C.byref(work, 16), wire, 96)
        before = work.raw
        self.assertEqual(self.restore(C.byref(output, 16), C.byref(work, 16), 96, C.byref(work, 16)), 0)
        self.assertEqual(work.raw, before)
        source = C.create_string_buffer(wire, 96)
        self.assertEqual(self.restore(C.byref(work, 16), source, 96, C.byref(work, 16)), 0)
        self.assertEqual(work.raw, before)


if __name__ == '__main__': unittest.main()
