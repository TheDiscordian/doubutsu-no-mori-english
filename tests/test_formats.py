import random
import struct
import sys
from pathlib import Path
import unittest
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from aflib import (apply_ups, make_ups, normalise_rom, read_varint, varint,
                   verified_rom, yaz0_decode)
from textbanks import Bank
from textcodec import decode, encode, tokenize
from font import glyph_metrics
from textvalidate import expanded_bound, signature, validate_entry


class PatchTests(unittest.TestCase):
    def test_varints(self):
        for n in (0, 1, 127, 128, 255, 16383, 16384, 0x2000000, 2**63):
            encoded = varint(n)
            self.assertEqual(read_varint(encoded, 0, len(encoded)), (n, len(encoded)))
        with self.assertRaises(ValueError):
            read_varint(b"\0", 0, 1)

    def test_patch_size_changes_and_end_runs(self):
        rng = random.Random(42)
        cases = [(b"", b""), (b"abc", b"abcdef"), (b"abc", b"x"),
                 (b"a", b"b"), (b"abc", b"abc"), (bytes(500), b"x")]
        cases += [(rng.randbytes(rng.randrange(100)), rng.randbytes(rng.randrange(100)))
                  for _ in range(100)]
        for source, target in cases:
            self.assertEqual(apply_ups(source, make_ups(source, target)), target)

    def test_corrupt_patch_and_wrong_source_rejected(self):
        patch = bytearray(make_ups(b"source", b"target"))
        with self.assertRaisesRegex(ValueError, "source"):
            apply_ups(b"wrong!", patch)
        patch[7] ^= 1
        with self.assertRaisesRegex(ValueError, "patch CRC"):
            apply_ups(b"source", patch)

    def test_patch_overrun_rejected_even_with_valid_crc(self):
        patch = bytearray(b"UPS1" + varint(1) + varint(1) + varint(50) + b"\1\0")
        patch.extend(struct.pack("<2I", zlib.crc32(b"a"), zlib.crc32(b"b")))
        patch.extend(struct.pack("<I", zlib.crc32(patch)))
        with self.assertRaisesRegex(ValueError, "outside"):
            apply_ups(b"a", patch)


class Yaz0Tests(unittest.TestCase):
    def test_literal_and_overlapping_backref(self):
        header = b"Yaz0" + struct.pack(">I", 6) + bytes(8)
        self.assertEqual(yaz0_decode(header + b"\x80a\x30\x00"), b"aaaaaa")

    def test_malformed_data(self):
        for payload in (b"", b"\0", b"\0\x10\0", b"\x80"):
            with self.assertRaises(ValueError):
                yaz0_decode(b"Yaz0" + struct.pack(">I", 6) + bytes(8) + payload)


class TextTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x61
        self.info[3] = (3, 0)
        self.info[5] = (5, 0)

    def test_controls_do_not_decode_as_letters(self):
        data = b"Hi\x7f\x05ABC\x80\x42\xcd\x7f\0"
        text = decode(data, self.info)
        self.assertEqual(text, "Hi{cmd:7F05414243}{glyph:8042}\n{cmd:7F00}")
        self.assertEqual(encode(text, self.info), data)

    def test_all_single_byte_glyphs_roundtrip(self):
        for value in set(range(256)) - {0x7F, 0x80}:
            data = bytes([value])
            self.assertEqual(encode(decode(data, self.info), self.info), data)

    def test_unknown_and_truncated_commands_are_not_importable(self):
        for data in (b"\x7f", b"\x80", b"\x7f\x61", b"\x7f\x05\x10"):
            with self.assertRaises(ValueError):
                list(tokenize(data, self.info))
            text = decode(data, self.info, strict=False)
            self.assertEqual(encode(text, self.info, allow_raw=True), data)
            with self.assertRaises(ValueError):
                encode(text, self.info)

    def test_ascii_collisions_and_unicode_rejected(self):
        for text in ("[", "#", "$", "\\", "é", "—", "{cmd:7F}", "{glyph:4142}"):
            with self.assertRaises(ValueError):
                encode(text, self.info)

    def test_cumulative_end_table_rebuild(self):
        table = struct.pack(">4I", 3, 6, 0, 0)
        bank = Bank("test", 0, 1, b"abcdefTAIL", table)
        self.assertEqual(bank.entries(), [b"abc", b"def"])
        self.assertEqual(bank.rebuild(bank.entries()), (bank.data, table))
        data, rebuilt = bank.rebuild([b"x", b"yz"])
        self.assertEqual(Bank("test", 0, 1, data, rebuilt).entries(), [b"x", b"yz"])
        with self.assertRaises(ValueError):
            bank.rebuild([b"x"*100, b"y"])
        with self.assertRaises(ValueError):
            Bank("bad", 0, 1, b"abc", struct.pack(">2I", 4, 0)).entries()

    def test_expansion_accounts_for_repeated_insertions(self):
        data = b"\x7f\x24"*32
        self.assertGreater(expanded_bound(data, self.info), 1024)
        with self.assertRaisesRegex(ValueError, "Expanded message"):
            validate_entry(data, data, self.info, "message")
        self.assertEqual(expanded_bound(b"Hi\x7f\x00", self.info), 20)

    def test_presentation_policy_never_drops_branch_or_button_commands(self):
        a = b"Hi\x7f\x03\x04\x7f\x04\x7f\x00"
        b = b"Hello\x7f\x04\x7f\x00"
        validate_entry(a, b, self.info, "message", "presentation")
        with self.assertRaisesRegex(ValueError, "signature"):
            validate_entry(a, b.replace(b"\x7f\x04", b""), self.info, "message", "presentation")
        with self.assertRaisesRegex(ValueError, "signature"):
            validate_entry(a, b, self.info, "message")

    def test_choice_limit_is_runtime_limit_not_source_length(self):
        validate_entry(b"Yes", b"Certainly!", self.info, "select")
        with self.assertRaisesRegex(ValueError, "10-byte"):
            validate_entry(b"Yes", b"Absolutely!", self.info, "select")


class RomTests(unittest.TestCase):
    def test_byte_orders(self):
        data = bytes.fromhex("80371240") + bytes(range(60))
        swapped = bytearray(len(data))
        swapped[::2], swapped[1::2] = data[1::2], data[::2]
        self.assertEqual(normalise_rom(bytes(swapped)), data)
        words = b"".join(data[i:i+4][::-1] for i in range(0, len(data), 4))
        self.assertEqual(normalise_rom(words), data)
        with self.assertRaisesRegex(ValueError, "Unsupported source"):
            verified_rom(data)


class FontTests(unittest.TestCase):
    def test_narrow_glyph_spacing_uses_ink_width(self):
        glyph = [[0]*5+[15]*3+[0]*4 for _ in range(16)]
        self.assertEqual(glyph_metrics(glyph), (5, 8, 3, 4))
        wide = [[0]+[15]*10+[0] for _ in range(16)]
        self.assertEqual(glyph_metrics(wide), (1, 11, 5, 6))
        self.assertEqual(glyph_metrics([[0]*12 for _ in range(16)]), (0, 0, 0, 6))


if __name__ == "__main__":
    unittest.main()
