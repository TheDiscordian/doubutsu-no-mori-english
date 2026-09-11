"""Complete title warnings preserve controller checks, assets, and saved data."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_VROM, by_vrom, apply_ups
from font import WIDTH_TABLE
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
import title_warning_text as title


@unittest.skipUnless((ROOT/'build/v1rc6/Animal Forest English V1RC6.z64').exists(),
                     'Local packaged RC6 required')
class TitleWarningTextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT/'build/v1rc6/Animal Forest English V1RC6.z64').read_bytes()
        cls.files = by_vrom(cls.base)
        cls.old = cls.files[title.OWNER].extract(cls.base)
        cls.reloc = cls.files[title.RELOC].extract(cls.base)
        cls.widths = cls.files[CODE_VROM].extract(cls.base)[WIDTH_TABLE:WIDTH_TABLE+256]
        cls.image, cls.patch, cls.report = title.build(cls.native, cls.base)
        cls.changed = by_vrom(cls.image)[title.OWNER].extract(cls.image)

    def test_complete_wording_and_only_seven_reader_words_change(self):
        ram = 0x80A9FC70
        expected = bytearray(self.old)
        expected[0x80AA2118-ram:0x80AA2154-ram] = (
            b'Controller 1 is notconnected. Power off,then connect it.\0\0\0\0')
        expected[0x80AA205E-ram:0x80AA2071-ram] = b'  Erase Save Data  '
        for address, word in ((0x80AA0954, 0x24060013), (0x80AA0958, 0x3C0742D4),
                              (0x80AA09B8, 0x24A5212B), (0x80AA09C0, 0x24060015),
                              (0x80AA09C4, 0x3C0742C5), (0x80AA0A2C, 0x24060010),
                              (0x80AA0A30, 0x3C0742E3)):
            struct.pack_into('>I', expected, address-ram, word)
        self.assertEqual(self.changed, bytes(expected))
        self.assertEqual(self.changed[9952:], self.old[9952:])
        self.assertEqual(self.changed[0x80AA1AF4-ram:0x80AA1B14-ram], bytes.fromhex(
            '3c0c8013918c7950558000068e0d02ac0c2a823902202025100000138fa40020'))

    def test_actual_relocated_readers_select_centred_complete_lines(self):
        ram = 0x80A9FC70
        rows = ((0x80AA0918, 0x80AA094C, 0x80AA0954, 0x80AA0958, 0x80AA096C,
                 b'Controller 1 is not', 108, 106),
                (0x80AA0984, 0x80AA09B8, 0x80AA09C0, 0x80AA09C4, 0x80AA09D8,
                 b'connected. Power off,', 123, 98.5),
                (0x80AA09F0, 0x80AA0A24, 0x80AA0A2C, 0x80AA0A30, 0x80AA0A44,
                 b'then connect it.', 93, 113.5))
        spec = Image(ram, 292320, (292320, 0, 0, 0, 174))
        for base in (0x801A0010, 0x802C0010, 0x80400010):
            data = relocate_verified_data(spec, self.changed, self.reloc, base, memory_end=0x80800000)
            for hi, lo, count, x_at, call, text, width, origin in rows:
                high = struct.unpack_from('>I', data, hi-ram)[0] & 65535
                low = struct.unpack_from('>h', data, lo-ram+2)[0]
                pointer = (high << 16)+low
                n = struct.unpack_from('>I', data, count-ram)[0] & 65535
                self.assertEqual(n, len(text))
                self.assertEqual(data[pointer-base:pointer-base+n], text)
                x = struct.unpack('>f', data[x_at-ram+2:x_at-ram+4]+bytes(2))[0]
                self.assertEqual(x, origin)
                self.assertEqual(sum(12-self.widths[c] for c in text), width)
                self.assertEqual(x+width/2, 160)
                self.assertEqual(data[call-ram:call-ram+4], bytes.fromhex('0c024387'))
            self.assertLessEqual(base+len(data), 0x80800000)

    def test_retains_other_resources_and_complete_original_rom_patch(self):
        files = by_vrom(self.image)
        self.assertEqual(set(files), set(self.files))
        for vrom, before in self.files.items():
            self.assertEqual((files[vrom].index, files[vrom].size), (before.index, before.size))
            if vrom == title.OWNER:
                continue
            actual, expected = files[vrom].extract(self.image), before.extract(self.base)
            if vrom == 0x19D40:
                actual, expected = actual[:16], expected[:16]
            self.assertEqual(actual, expected, f'{vrom:08X}')
        self.assertEqual(apply_ups(self.native, self.patch), self.image)
        for flag in ('allocation_changed', 'relocation_changed', 'controller_detection_changed',
                     'menu_actions_changed', 'saved_format_changed', 'save_readers_writers_changed',
                     'native_rendering_verified', 'original_hardware_verified'):
            self.assertFalse(self.report[flag], flag)

    def test_rejects_unknown_owner_relocation_metrics_or_baseline(self):
        args = [self.old, self.reloc, self.widths]
        for index in range(len(args)):
            changed = args.copy()
            changed[index] = bytes([changed[index][0] ^ 1])+changed[index][1:]
            with self.subTest(argument=index), self.assertRaises(ValueError):
                title.patch_owner(*changed)
        with self.assertRaises(ValueError):
            title.build(self.native, self.base[:-1])


if __name__ == '__main__':
    unittest.main()
