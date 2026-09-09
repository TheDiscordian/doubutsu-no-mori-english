"""Compact board snapshots retain full fields, without touching timestamps."""

import ctypes as C
from dataclasses import replace
from pathlib import Path
import os
import random
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from mail_record import Record, Field, pack as mail_pack
from notice_record import PREFIX, pack, expand, unpack, tagged
import test_mail_record_c as record_c


class NoticeRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='af-notice-record-')
        library = Path(cls.temporary.name)/'notice.so'
        flags = ['-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                 '-fno-omit-frame-pointer', '-g'] if os.environ.get('AF_NOTICE_SANITIZE') == '1' else []
        compiler_env = dict(os.environ)
        compiler_env.pop('LD_PRELOAD', None)
        subprocess.run(['gcc', '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
                        *flags,
                        str(ROOT/'runtime/mail/record.c'), str(ROOT/'runtime/notice/record.c'),
                        '-o', str(library)], check=True, capture_output=True, env=compiler_env)
        cls.lib = C.CDLL(str(library))
        cls.lib.af_notice_record_pack.argtypes = [C.c_void_p, C.c_uint, C.c_void_p]
        cls.lib.af_notice_record_expand.argtypes = [C.c_void_p, C.c_uint, C.c_void_p, C.c_uint, C.c_uint]
        cls.lib.af_notice_record_tagged.argtypes = [C.c_void_p, C.c_uint]

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def record(self, fields=()):
        return Record(4, 0, (0x1FC,), tuple(fields))

    def roundtrip(self, record):
        wire = pack(record)
        native = record_c.MailRecordCTests.native(self, record)
        original = bytes(native)
        # The last eight bytes model the complete neighbouring timestamp.
        output = C.create_string_buffer(b'!'*136, 136)
        self.assertEqual(self.lib.af_notice_record_pack(C.byref(output, 16), 96, C.byref(native)), 1)
        self.assertEqual(output.raw, b'!'*16+wire+b'!'*24)
        self.assertEqual(bytes(native), original)
        self.assertEqual(unpack(wire, expected_catalog=record.catalog), record)
        expanded = C.create_string_buffer(b'!'*154, 154)
        self.assertEqual(self.lib.af_notice_record_expand(C.byref(expanded, 16), 122,
                                                        wire, 96, record.catalog), 1)
        self.assertEqual(expanded.raw, b'!'*16+mail_pack(record)+b'!'*16)
        self.assertEqual(expand(wire, expected_catalog=record.catalog), mail_pack(record))
        return wire

    def test_all_field_positions_lengths_articles_and_random_bytes(self):
        for slot in range(20):
            for length in range(17):
                for article in range(5):
                    self.roundtrip(self.record(((slot, Field(bytes(range(length)), article)),)))
        rng = random.Random(0xAFB001)
        for _ in range(500):
            fields = tuple((i, Field(rng.randbytes(rng.randrange(17)), rng.randrange(5)))
                           for i in sorted(rng.sample(range(20), rng.randrange(5))))
            self.roundtrip(replace(self.record(fields), initial_capital=bool(rng.randrange(2))))

    def test_exact_capacity_then_one_more_byte_fails_without_writes(self):
        fields = tuple((i, Field(b'X'*16)) for i in range(4)) + ((19, Field(b'Y'*11)),)
        wire = self.roundtrip(self.record(fields))
        self.assertEqual(wire[6]+4, 96)
        record = self.record(fields[:-1]+((19, Field(b'Y'*12)),))
        with self.assertRaisesRegex(ValueError, 'exceeds'):
            pack(record)
        native = record_c.MailRecordCTests.native(self, record)
        output = C.create_string_buffer(b'!'*104, 104)
        self.assertEqual(self.lib.af_notice_record_pack(output, 96, C.byref(native)), 0)
        self.assertEqual(output.raw, b'!'*104)

    def reject(self, wire, size=96, catalog=4, capacity=122):
        output = C.create_string_buffer(b'!'*154, 154)
        self.assertEqual(self.lib.af_notice_record_expand(C.byref(output, 16), capacity,
                                                        wire, size, catalog), 0)
        self.assertEqual(output.raw, b'!'*154)

    def test_all_single_bit_corruptions_and_unsupported_versions_fail(self):
        wire = pack(self.record(((0, Field(b'Town')), (19, Field(b'item', 2)))))
        for i in range(96):
            for bit in range(8):
                damaged = bytearray(wire)
                damaged[i] ^= 1 << bit
                self.reject(bytes(damaged))
                with self.assertRaises(ValueError):
                    unpack(bytes(damaged), expected_catalog=4)
        future = wire[:3]+b'\x02'+wire[4:]
        self.assertTrue(tagged(future))
        self.assertEqual(self.lib.af_notice_record_tagged(future, 96), 1)
        self.reject(future)

    def test_wrong_kinds_catalogues_capacities_and_nulls_fail(self):
        record = self.record()
        wire = pack(record)
        for size in (0, 3, 95, 97, 0xFFFFFFFF):
            self.reject(wire, size=size)
        for catalog in (0, 2, 3, 65536, 0xFFFFFFFF):
            self.reject(wire, catalog=catalog)
        for capacity in (0, 121):
            self.reject(wire, capacity=capacity)
        self.reject(None)
        self.assertEqual(self.lib.af_notice_record_tagged(None, 96), 0)
        for kind in (1, 2):
            bad = replace(record, kind=kind, templates=(0,)*5)
            with self.assertRaises(ValueError):
                pack(bad)
            native = record_c.MailRecordCTests.native(self, bad)
            output = C.create_string_buffer(b'!'*104, 104)
            self.assertEqual(self.lib.af_notice_record_pack(output, 96, C.byref(native)), 0)
            self.assertEqual(output.raw, b'!'*104)
        composite = mail_pack(Record(4, 1, (0,)*5, ()))
        self.reject(PREFIX+composite[:92])
        native = record_c.MailRecordCTests.native(self, record)
        for capacity in (0, 95):
            output = C.create_string_buffer(b'!'*104, 104)
            self.assertEqual(self.lib.af_notice_record_pack(output, capacity, C.byref(native)), 0)
            self.assertEqual(output.raw, b'!'*104)
        self.assertEqual(self.lib.af_notice_record_pack(None, 96, C.byref(native)), 0)
        self.assertEqual(self.lib.af_notice_record_pack(C.byref(native), 96, None), 0)
        self.assertEqual(self.lib.af_notice_record_expand(None, 122, wire, 96, 4), 0)

    def test_codec_allows_overlapping_inputs_only_after_complete_validation(self):
        record = self.record(((3, Field(b'Literal')),))
        native = record_c.MailRecordCTests.native(self, record)
        self.assertEqual(self.lib.af_notice_record_pack(C.byref(native), 96, C.byref(native)), 1)
        self.assertEqual(bytes(native)[:96], pack(record))
        self.assertEqual(self.lib.af_notice_record_expand(C.byref(native), 122, C.byref(native), 96, 4), 1)
        self.assertEqual(bytes(native)[:122], mail_pack(record))


if __name__ == '__main__':
    unittest.main()
