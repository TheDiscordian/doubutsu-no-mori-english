"""A generated-letter snapshot must survive fixed-size native copies intact."""

import binascii
from dataclasses import replace
from pathlib import Path
import random
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from mail_record import Field, Record, pack, unpack, snapshot_size, RECORD_BYTES


class MailRecordTests(unittest.TestCase):
    def record(self, kind=0, fields=()):
        return Record(1, kind, (543,) if kind == 0 else (0, 32, 64, 96, 383), tuple(fields))

    def roundtrip(self, record):
        data = pack(record)
        self.assertEqual(len(data), RECORD_BYTES)
        self.assertEqual(unpack(data, expected_catalog=record.catalog), record)
        self.assertEqual(pack(unpack(data, expected_catalog=record.catalog)), data)
        # Native Mail_c and Anmplmail_c retain contiguous 10/96/16 fields.
        copied = data[:10] + data[10:106] + data[106:122]
        self.assertEqual(unpack(copied, expected_catalog=record.catalog), record)
        return data

    def test_complete_six_field_composite_exactly_fills_saved_text(self):
        fields = tuple((i*3, Field(bytes(range(i*16, (i+1)*16)), i % 5)) for i in range(6))
        data = self.roundtrip(self.record(1, fields))
        self.assertEqual((data[2], snapshot_size(1, [16]*6)), (122, 122))
        with self.assertRaisesRegex(ValueError, "exceeds"):
            pack(self.record(1, fields+((19, Field(b"")),)))

    def test_every_slot_length_article_and_empty_field_is_distinct(self):
        self.roundtrip(self.record())
        self.roundtrip(self.record(1))
        for index in range(20):
            for length in range(17):
                for article in range(5):
                    self.roundtrip(self.record(fields=((index, Field(b" "*length, article)),)))
        all_empty = tuple((i, Field(b"", i % 5)) for i in range(20))
        self.assertEqual(unpack(self.roundtrip(self.record(1, all_empty)), expected_catalog=1).fields, all_empty)

    def test_random_literal_bytes_are_never_regenerated_or_normalized(self):
        rng = random.Random(0xAF01)
        for _ in range(1000):
            slots = sorted(rng.sample(range(20), rng.randrange(7)))
            fields = tuple((i, Field(rng.randbytes(rng.randrange(17)), rng.randrange(5))) for i in slots)
            self.roundtrip(self.record(rng.randrange(2), fields))

    def test_all_single_bit_corruptions_and_wrong_catalog_are_rejected(self):
        record = self.record(1, ((0, Field(b"town ")), (19, Field(b"an item", 2))))
        data = self.roundtrip(record)
        for byte in range(len(data)):
            for bit in range(8):
                damaged = bytearray(data)
                damaged[byte] ^= 1 << bit
                with self.assertRaises(ValueError):
                    unpack(bytes(damaged), expected_catalog=1)
        with self.assertRaisesRegex(ValueError, "different immutable catalog"):
            unpack(data, expected_catalog=2)
        for size in (0, 121, 123, 244):
            with self.assertRaises(ValueError):
                unpack(bytes(size), expected_catalog=1)

    def test_rechecks_structure_even_with_a_valid_checksum(self):
        data = self.roundtrip(self.record(fields=((0, Field(b"test")),)))
        def mutate(index, value):
            changed = bytearray(data)
            changed[index] = value
            size = changed[2]
            changed[size-2:size] = binascii.crc_hqx(changed[:size-2], 0xFFFF).to_bytes(2, "big")
            with self.assertRaises(ValueError):
                unpack(bytes(changed), expected_catalog=1)
        mutate(5, 0x10)  # Reserved upper field bit.
        mutate(7, 3)    # Claims a second field without a second payload.
        mutate(7, 0)    # Leaves an unclaimed payload.
        mutate(10, 17)  # Exceeds the sixteen-byte field contract.
        mutate(10, 0xA4)  # Invalid article, with an otherwise correct length.
        mutate(10, 16)  # Valid width, but incomplete actual payload.

    def test_encoder_rejects_invalid_noncanonical_or_overlength_records(self):
        base = self.record()
        bad = [replace(base, catalog=value) for value in (0, 65536, True)]
        bad += [replace(base, kind=value) for value in (-1, 2, True)]
        bad += [replace(base, templates=value) for value in ((), (1, 2), (-1,), (65536,), (True,))]
        for fields in (((20, Field(b"x")),), ((0, Field(b"x"*17)),),
                       ((0, Field(b"x", 5)),), ((0, Field(b"x", True)),),
                       ((1, Field(b"x")), (0, Field(b"y"))),
                       ((0, Field(b"x")), (0, Field(b"x"))),
                       ((0, Field("not bytes")),)):
            bad.append(replace(base, fields=fields))
        for record in bad:
            with self.assertRaises(ValueError):
                pack(record)
        with self.assertRaisesRegex(ValueError, "Too many"):
            snapshot_size(0, [0]*21)
