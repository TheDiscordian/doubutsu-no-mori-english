"""The freestanding C snapshot codec agrees with the independent Python codec."""

import binascii
import ctypes as C
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from mail_record import Field, Record, pack, unpack


class CField(C.Structure):
    _fields_ = [("length", C.c_ubyte), ("article", C.c_ubyte), ("text", C.c_ubyte*16)]


class CRecord(C.Structure):
    _fields_ = [("catalog", C.c_ushort), ("kind", C.c_ubyte), ("reserved", C.c_ubyte),
                ("field_mask", C.c_uint), ("templates", C.c_ushort*5), ("fields", CField*20)]


@unittest.skipUnless(shutil.which("gcc"), "Host GCC executes the standalone mail codec")
class MailRecordCTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        library = Path(cls.temporary.name)/"mail-record.so"
        subprocess.run(["gcc", "-std=c99", "-Wall", "-Wextra", "-Werror", "-O2", "-shared", "-fPIC",
                        str(ROOT/"runtime/mail/record.c"), "-o", str(library)], check=True, capture_output=True)
        cls.lib = C.CDLL(str(library))
        cls.lib.af_mail_record_pack.argtypes = [C.c_void_p, C.c_uint, C.c_void_p]
        cls.lib.af_mail_record_unpack.argtypes = [C.c_void_p, C.c_void_p, C.c_uint, C.c_uint]

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def native(self, record):
        value = CRecord(catalog=record.catalog, kind=record.kind)
        for i, template in enumerate(record.templates):
            value.templates[i] = template
        for index, field in record.fields:
            value.field_mask |= 1 << index
            value.fields[index].length = len(field.text)
            value.fields[index].article = field.article
            value.fields[index].text[:len(field.text)] = field.text
        return value

    def roundtrip(self, record):
        expected = pack(record)
        native = self.native(record)
        original = bytes(native)
        output = C.create_string_buffer(b"!"*160, 160)
        self.assertEqual(self.lib.af_mail_record_pack(C.byref(output, 9), 122, C.byref(native)), 1)
        self.assertEqual(output.raw, b"!"*9+expected+b"!"*29)
        self.assertEqual(bytes(native), original)
        decoded = CRecord()
        self.assertEqual(self.lib.af_mail_record_unpack(C.byref(decoded), C.byref(output, 9), 122, record.catalog), 1)
        self.assertEqual(bytes(decoded), original)
        self.assertEqual(unpack(output.raw[9:131], expected_catalog=record.catalog), record)

    def test_every_slot_width_article_and_random_full_snapshots(self):
        for slot in range(20):
            for width in range(17):
                for article in range(5):
                    self.roundtrip(Record(1, 0, (543,), ((slot, Field(b" "*width, article)),)))
        rng = random.Random(0xAF02)
        for _ in range(500):
            slots = sorted(rng.sample(range(20), rng.randrange(7)))
            fields = tuple((i, Field(rng.randbytes(rng.randrange(17)), rng.randrange(5))) for i in slots)
            self.roundtrip(Record(rng.randrange(1, 65536), 1, tuple(rng.randrange(65536) for _ in range(5)), fields))
        self.roundtrip(Record(1, 1, (0, 1, 2, 3, 383), tuple((i, Field(bytes(range(16)), 4)) for i in range(6))))

    def reject(self, data, catalog=1, size=122):
        output = C.create_string_buffer(b"!"*(C.sizeof(CRecord)+32), C.sizeof(CRecord)+32)
        before = output.raw
        self.assertEqual(self.lib.af_mail_record_unpack(C.byref(output, 16), data, size, catalog), 0)
        self.assertEqual(output.raw, before)

    def test_invalid_records_never_partially_overwrite_destination(self):
        data = pack(Record(1, 0, (1,), ((0, Field(b"data")),)))
        for byte in range(122):
            for bit in range(8):
                changed = bytearray(data)
                changed[byte] ^= 1 << bit
                self.reject(bytes(changed))
        for catalog in (0, 2, 65536, 0xFFFFFFFF):
            self.reject(data, catalog=catalog)
        for size in (0, 121, 123, 0xFFFFFFFF):
            self.reject(data, size=size)
        self.reject(None)
        for offset, value in ((5, 16), (7, 0), (7, 3), (10, 17), (10, 0xA4), (10, 16)):
            changed = bytearray(data)
            changed[offset] = value
            used = changed[2]
            changed[used-2:used] = binascii.crc_hqx(changed[:used-2], 0xFFFF).to_bytes(2, "big")
            self.reject(bytes(changed))

    def test_encoder_bounds_and_aliasing(self):
        record = Record(1, 1, (0, 1, 2, 3, 4), tuple((i, Field(b"x"*16)) for i in range(6)))
        native = self.native(record)
        output = C.create_string_buffer(b"!"*128, 128)
        for capacity in (0, 121):
            self.assertEqual(self.lib.af_mail_record_pack(output, capacity, C.byref(native)), 0)
            self.assertEqual(output.raw, b"!"*128)
        for attr, value in (("catalog", 0), ("kind", 2), ("reserved", 1), ("field_mask", 0x100000), ("field_mask", 127)):
            old = getattr(native, attr)
            setattr(native, attr, value)
            self.assertEqual(self.lib.af_mail_record_pack(output, 122, C.byref(native)), 0)
            self.assertEqual(output.raw, b"!"*128)
            setattr(native, attr, old)
        self.assertEqual(self.lib.af_mail_record_pack(output, 122, None), 0)
        self.assertEqual(self.lib.af_mail_record_pack(None, 122, C.byref(native)), 0)
        # Both operations stage output before publishing, including when the
        # wire envelope overlaps the input or output structure.
        self.assertEqual(self.lib.af_mail_record_pack(C.byref(native), 122, C.byref(native)), 1)
        self.assertEqual(bytes(native)[:122], pack(record))
        self.assertEqual(self.lib.af_mail_record_unpack(C.byref(native), C.byref(native), 122, 1), 1)
        self.assertEqual(bytes(native), bytes(self.native(record)))
