import struct
import sys
import tempfile
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from gamecube import Disc, rarc_files
from gc_names import rel_sections, symbol_data
from emulator_smoke import expand_actions


def disc_fixture():
    data = bytearray(0x1800)
    data[:6] = b"TEST01"
    struct.pack_into(">I", data, 0x1C, 0xC2339F3D)
    struct.pack_into(">2I", data, 0x424, 0x500, 26)
    struct.pack_into(">3I", data, 0x500, 0x01000000, 0, 2)
    struct.pack_into(">3I", data, 0x50C, 0, 0x1100, 3)
    data[0x518:0x51A] = b"x\0"
    data[0x1100:0x1103] = b"abc"
    return data


class DiscTests(unittest.TestCase):
    def test_raw_and_sparse_disc_match(self):
        data = disc_fixture()
        header = bytearray(0x8000)
        header[:4] = b"CISO"
        struct.pack_into("<I", header, 4, 0x800)
        header[8:11] = bytes([1, 0, 1])
        with tempfile.TemporaryDirectory() as directory:
            for name, encoded in (("raw.iso", data), ("sparse.ciso", header+data[:0x800]+data[0x1000:])):
                path = Path(directory)/name
                path.write_bytes(encoded)
                with Disc(path) as disc:
                    self.assertEqual(disc.files(), [{"path": "x", "offset": 0x1100, "size": 3}])
                    self.assertEqual(disc.read(0x7FF, 0x904), data[0x7FF:0x1103])

    def test_unsafe_fst_names_rejected(self):
        data = disc_fixture()
        data[0x518] = ord("/")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"bad.iso"
            path.write_bytes(data)
            with Disc(path) as disc, self.assertRaisesRegex(ValueError, "Unsafe"):
                disc.files()


def rarc_fixture():
    data = bytearray(0x100)
    data[:4] = b"RARC"
    struct.pack_into(">I", data, 4, len(data))
    struct.pack_into(">I", data, 12, 0xC0)
    struct.pack_into(">6I", data, 0x20, 1, 0x20, 1, 0x30, 2, 0x44)
    struct.pack_into(">H", data, 0x4A, 1)
    struct.pack_into(">I", data, 0x4C, 0)
    struct.pack_into(">2H2I", data, 0x54, 0x0100, 0, 0, 3)
    data[0x64:0x66] = b"x\0"
    data[0xE0:0xE3] = b"abc"
    return data


class ArchiveTests(unittest.TestCase):
    def test_rarc_file_bounds_and_cycles(self):
        data = rarc_fixture()
        self.assertEqual(list(rarc_files(data)), [("x", b"abc")])
        struct.pack_into(">I", data, 0x5C, 1000)
        with self.assertRaisesRegex(ValueError, "exceeds"):
            list(rarc_files(data))
        data = rarc_fixture()
        struct.pack_into(">H", data, 0x54, 0x0200)
        with self.assertRaisesRegex(ValueError, "cyclic"):
            list(rarc_files(data))

    def test_rel_symbol_mapping(self):
        data = bytearray(0x110)
        struct.pack_into(">2I", data, 12, 7, 0x48)
        struct.pack_into(">2I", data, 0x48+5*8, 0x100, 16)
        data[0x100:0x103] = b"abc"
        self.assertEqual(symbol_data(data, "word = .data:0x0000; // size:0x3", "word"), b"abc")
        with self.assertRaisesRegex(ValueError, "outside"):
            symbol_data(data, "word = .data:0x000F; // size:0x3", "word")
        struct.pack_into(">I", data, 12, 1000)
        with self.assertRaises(ValueError):
            rel_sections(data)

    def test_scenario_expansion_is_bounded(self):
        self.assertEqual(list(expand_actions([{"repeat": 2, "actions": [{"capture": "{index:02d}.png"}]}])),
                         [{"capture": "00.png"}, {"capture": "01.png"}])
        with self.assertRaises(ValueError):
            list(expand_actions([{"repeat": 1000, "actions": []}]))
