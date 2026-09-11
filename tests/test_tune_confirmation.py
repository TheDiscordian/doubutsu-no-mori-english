"""Complete tune-confirmation readers and preservation of RC5 behaviour/data."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_VROM, by_vrom, apply_ups, sha256
from catalogue_names import Image
from font import WIDTH_TABLE
from npc_mail_show import relocate_verified_data
import tune_confirmation as tune


@unittest.skipUnless((ROOT/'build/v1rc5/Animal Forest English V1RC5.z64').exists(), 'Local RC5 inputs required')
class TuneConfirmationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT/'build/v1rc5/Animal Forest English V1RC5.z64').read_bytes()
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.files = by_vrom(cls.base)
        cls.old = cls.files[tune.OWNER].extract(cls.base)
        cls.reloc = cls.files[tune.RELOC].extract(cls.base)
        cls.widths = cls.files[CODE_VROM].extract(cls.base)[WIDTH_TABLE:WIDTH_TABLE+256]
        cls.shared = cls.files[tune.SHARED].extract(cls.base)
        cls.image, cls.patch, cls.report = tune.build(cls.native, cls.base, cls.rel, cls.symbols)
        cls.changed = by_vrom(cls.image)[tune.OWNER].extract(cls.image)

    def test_complete_counted_text_and_only_five_reader_words_change(self):
        self.assertEqual(self.changed[0x1844:0x1858], b'Are you sure?YesNo\0\0')
        edits = {0x1304: 0x2406000D, 0x136C: 0x24A5A141, 0x137C: 0x24060003,
                 0x13EC: 0x24A5A144, 0x140C: 0x24060002}
        allowed = set(range(0x1844, 0x1858))
        for at, value in edits.items():
            self.assertEqual(struct.unpack_from('>I', self.changed, at)[0], value)
            allowed.update(range(at, at+4))
        self.assertEqual(len(self.old), len(self.changed))
        self.assertTrue(all(a == b or at in allowed for at, (a, b) in enumerate(zip(self.old, self.changed))))
        self.assertEqual(self.old[0x1858:], self.changed[0x1858:])
        for at in (0x131C, 0x13A4, 0x1418):
            self.assertEqual(self.changed[at:at+4], bytes.fromhex('0c0243a6'))

    def test_relocated_pointers_lengths_and_native_window_containment(self):
        sites = ((0x12CC, 0x12F8, 0x1304, b'Are you sure?'),
                 (0x1358, 0x136C, 0x137C, b'Yes'), (0x13C0, 0x13EC, 0x140C, b'No'))
        for base in (0x801A0010, 0x802F8010, 0x803D0010):
            image = relocate_verified_data(Image(0x808988F0, 6336, (5712, 544, 32, 48, 97)),
                                           self.changed, self.reloc, base)
            for high, low, count, text in sites:
                address = (struct.unpack_from('>I', image, high)[0] & 65535) * 65536
                address += struct.unpack_from('>h', image, low+2)[0]
                n = struct.unpack_from('>I', image, count)[0] & 65535
                self.assertEqual(n, len(text))
                self.assertEqual(image[address-base:address-base+n], text)
            self.assertEqual(image[-48:], bytes(48))
        self.assertEqual([r['width'] for r in self.report['strings']], [78, 18, 12])
        for opening in (0.125, 0.5, 1.0):
            centre = 175+16*opening
            left, right = centre-68*0.897059*opening, centre+68*0.897059*opening
            origin = 175-16*opening
            for width in (78, 18, 12):
                self.assertGreaterEqual(origin-left, 12*opening)
                self.assertGreaterEqual(right-(origin+width*opening), 12*opening)

    def test_complete_cartridge_and_patch_retain_all_other_resources(self):
        files = by_vrom(self.image)
        self.assertEqual(set(files), set(self.files))
        for vrom, entry in self.files.items():
            self.assertEqual((files[vrom].index, files[vrom].size), (entry.index, entry.size))
            if vrom == tune.OWNER:
                continue
            actual, expected = files[vrom].extract(self.image), entry.extract(self.base)
            if vrom == 0x19D40:
                actual, expected = actual[:16], expected[:16]
            self.assertEqual(actual, expected, f'{vrom:08X}')
        self.assertEqual(apply_ups(self.native, self.patch), self.image)
        self.assertEqual(sha256(self.image), self.report['output_sha256'])
        self.assertFalse(self.report['allocation_changed'])
        self.assertFalse(self.report['saved_format_changed'])
        self.assertFalse(self.report['save_readers_writers_changed'])
        self.assertFalse(self.report['original_hardware_verified'])

    def test_rejects_changed_owner_relocation_font_background_and_donors(self):
        arguments = [self.old, self.reloc, self.widths, self.shared, self.rel, self.symbols]
        for index in range(len(arguments)):
            damaged = arguments.copy()
            damaged[index] = bytes([damaged[index][0] ^ 1])+damaged[index][1:]
            with self.subTest(argument=index), self.assertRaises(ValueError):
                tune.patch_owner(*damaged)
        with self.assertRaises(ValueError):
            tune.build(self.native, self.base[:-1], self.rel, self.symbols)


if __name__ == '__main__':
    unittest.main()
