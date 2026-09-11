"""Pak heading English, centring, and unchanged deletion/save behaviour."""
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
import pak_erase_heading as pak


@unittest.skipUnless((ROOT/'build/tune-confirmation-01/animal-forest-tune-confirmation.z64').exists(),
                     'Local committed tune-confirmation build required')
class PakEraseHeadingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT/'build/tune-confirmation-01/animal-forest-tune-confirmation.z64').read_bytes()
        cls.files = by_vrom(cls.base)
        cls.old = cls.files[pak.OWNER].extract(cls.base)
        cls.reloc = cls.files[pak.RELOC].extract(cls.base)
        cls.widths = cls.files[CODE_VROM].extract(cls.base)[WIDTH_TABLE:WIDTH_TABLE+256]
        cls.image, cls.patch, cls.report = pak.build(cls.native, cls.base)
        cls.changed = by_vrom(cls.image)[pak.OWNER].extract(cls.image)

    def test_complete_heading_and_centred_reader_only(self):
        self.assertEqual(self.changed[0x171C:0x1730], b'Erase a Pak note\0\0\0\0')
        expected = bytearray(self.old)
        expected[0x171C:0x1730] = b'Erase a Pak note\0\0\0\0'
        struct.pack_into('>I', expected, 0x138C, 0x3C01429B)
        struct.pack_into('>I', expected, 0x1404, 0x24060010)
        self.assertEqual(self.changed, bytes(expected))
        self.assertEqual(self.changed[0x1730:], self.old[0x1730:])
        x_increment = struct.unpack('>f', self.changed[0x138E:0x1390]+b'\0\0')[0]
        x = -120+x_increment+160
        width = sum(12-self.widths[c] for c in b'Erase a Pak note')*0.875
        self.assertEqual((x, width), (117.5, 84))
        self.assertEqual(x+width/2, 65+18*12*0.875/2)
        self.assertEqual(self.changed[0x1418:0x141C], bytes.fromhex('0c0243a6'))

    def test_original_relocations_keep_pointer_and_bss(self):
        for base in (0x801A0010, 0x802F8010, 0x803D0010):
            data = relocate_verified_data(Image(0x808A4780, 6320, (5808, 144, 0, 368, 44)),
                                          self.changed, self.reloc, base)
            high = struct.unpack_from('>I', data, 0x13CC)[0] & 65535
            low = struct.unpack_from('>h', data, 0x13FE)[0]
            address = (high << 16)+low
            count = struct.unpack_from('>I', data, 0x1404)[0] & 65535
            self.assertEqual(count, 16)
            self.assertEqual(data[address-base:address-base+count], b'Erase a Pak note')
            self.assertEqual(data[-368:], bytes(368))

    def test_all_other_resources_and_complete_patch_retained(self):
        files = by_vrom(self.image)
        self.assertEqual(set(files), set(self.files))
        for vrom, entry in self.files.items():
            self.assertEqual((files[vrom].index, files[vrom].size), (entry.index, entry.size))
            if vrom == pak.OWNER:
                continue
            actual, expected = files[vrom].extract(self.image), entry.extract(self.base)
            if vrom == 0x19D40:
                actual, expected = actual[:16], expected[:16]
            self.assertEqual(actual, expected, f'{vrom:08X}')
        self.assertEqual(apply_ups(self.native, self.patch), self.image)
        self.assertFalse(self.report['allocation_changed'])
        self.assertFalse(self.report['pak_operations_changed'])
        self.assertFalse(self.report['saved_format_changed'])
        self.assertFalse(self.report['save_readers_writers_changed'])
        self.assertFalse(self.report['original_hardware_verified'])

    def test_refuses_changed_owner_relocation_metrics_or_baseline(self):
        arguments = [self.old, self.reloc, self.widths]
        for index in range(len(arguments)):
            values = arguments.copy()
            values[index] = bytes([values[index][0] ^ 1])+values[index][1:]
            with self.subTest(argument=index), self.assertRaises(ValueError):
                pak.patch_owner(*values)
        with self.assertRaises(ValueError):
            pak.build(self.native, self.base[:-1])


if __name__ == '__main__':
    unittest.main()
