"""Complete gamestate labels and bounded native display-copy changes."""
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
import gamestate_menu_text as menus


@unittest.skipUnless((ROOT/'build/title-warning-text-01/animal-forest-title-warning.z64').exists(),
                     'Local committed title-warning build required')
class GamestateMenuTextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT/'build/title-warning-text-01/animal-forest-title-warning.z64').read_bytes()
        cls.files = by_vrom(cls.base)
        cls.widths = cls.files[CODE_VROM].extract(cls.base)[WIDTH_TABLE:WIDTH_TABLE+256]
        cls.image, cls.patch, cls.report = menus.build(cls.native, cls.base)
        cls.built = by_vrom(cls.image)

    def data(self, name):
        vrom, reloc, ram, sections, *_ = menus.PARTS[name]
        return self.built[vrom].extract(self.image), self.files[reloc].extract(self.base), ram, sections

    def test_complete_labels_and_only_declared_reader_bytes_change(self):
        for name, (vrom, _, ram, *_rest) in menus.PARTS.items():
            original = self.files[vrom].extract(self.base)
            changed = self.built[vrom].extract(self.image)
            expected = bytearray(original)
            for address, before, after in menus.TEXT[name]:
                self.assertEqual(len(before), len(after))
                expected[address-ram:address-ram+len(after)] = after
            for address, before, after in menus.WORDS[name]:
                self.assertEqual(struct.unpack_from('>I', original, address-ram)[0], before)
                struct.pack_into('>I', expected, address-ram, after)
            self.assertEqual(changed, bytes(expected))
        player, _, ram, _ = self.data('player')
        for address, text in ((0x80829300, b'Select a player'), (0x8082930F, b'<Away>    '),
                              (0x80829319, b'<Home>   '), (0x80829322, b'Visitor   '),
                              (0x80829358, b'Unregistered'), (0x80829364, b'Resident   ')):
            self.assertEqual(player[address-ram:address-ram+len(text)], text)
        save, _, ram, _ = self.data('save')
        for address, text in ((0x80829F0C, b'Save Menu'), (0x80829F18, b'Push A Button'),
                              (0x80829F28, b'Select R Button'), (0x80829F38, b'Push B Button to EXIT'),
                              (0x80829F50, b'Save to FlashRAM'), (0x80829F60, b'Save to Pak')):
            self.assertEqual(save[address-ram:address-ram+len(text)], text)

    def test_relocated_pointers_retain_both_owner_ranges(self):
        for name in menus.PARTS:
            data, reloc, ram, sections = self.data(name)
            for base in (0x801A0010, 0x802F8010, 0x803D0010):
                shifted = relocate_verified_data(Image(ram, len(data), sections), data, reloc, base)
                self.assertEqual(len(shifted), len(data))
                for hi, lo, target in menus.POINTERS[name]:
                    high = struct.unpack_from('>I', shifted, hi-ram)[0] & 65535
                    low = struct.unpack_from('>h', shifted, lo-ram+2)[0]
                    self.assertEqual((high << 16)+low, base+target-ram)

    def test_complete_resident_rows_and_unchanged_display_capacity(self):
        data, _, ram, _ = self.data('player')
        word = lambda a: struct.unpack_from('>I', data, a-ram)[0]
        # Bind the actual stack/frame/copy instructions, not only a proposed layout.
        expected = {0x80828C98: 0x27BDFF38, 0x80828CE8: 0xAFAF00BC,
                    0x80828D34: 0x27B200A0, 0x80828D3C: 0x2405001B,
                    0x80828D48: 0x24080010, 0x80828D54: 0x8FA500BC,
                    0x80828D60: 0x2407000B, 0x80828D6C: 0xA3AA00A9,
                    0x80828DA8: 0x2406001B, 0x80828E44: 0x27BD00C8,
                    0x80829098: 0x2628000C, 0x808290A0: 0x24060010,
                    0x808290D0: 0x2404000C, 0x808290D4: 0x24E2000C,
                    0x8082919C: 0x2406000A, 0x808291B0: 0x24060009}
        self.assertEqual({at: word(at) for at in expected}, expected)
        self.assertEqual((menus.pointer(data, 0x80829078-ram, 0x80829088-ram)
                          - menus.pointer(data, 0x808290A4-ram, 0x808290A8-ram)), 12)
        self.assertEqual((menus.pointer(data, 0x808291F4-ram, 0x808291F8-ram)
                          - menus.pointer(data, 0x808291F0-ram, 0x808291FC-ram)), 10)
        prefix = data[0x80829364-ram:0x80829364-ram+11]
        unregistered = data[0x80829358-ram:0x80829364-ram]+b' '*4
        self.assertEqual(unregistered, b'Unregistered    ')
        variants = [unregistered, b'Visitor         ', b'Alex  <Away>    ', b'Alex  <Home>    ',
                    bytes.fromhex('001020304050')+b'<Away>    ']
        for number in range(4):
            for row in variants:
                self.assertEqual(len(row), 16)
                source_row = row
                stack = bytearray([0xA5]*200)
                stack[0xBC:0xC0] = struct.pack('>I', 0x80829364)
                untouched = bytes(stack)
                output = bytearray(prefix+row)
                output[9] = 0x30 | number
                self.assertEqual(output[:11], f'Resident {number} '.encode())
                stack[0xA0:0xBB] = output
                self.assertEqual(stack[:0xA0], untouched[:0xA0])
                self.assertEqual(stack[0xBB:], untouched[0xBB:])
                self.assertEqual(bytes(stack[0xAB:0xBB]), source_row)
        # Worst-case six full-width saved-name glyphs plus original padded status.
        self.assertLess(70+(sum(12-self.widths[c] for c in b'Resident 0 ')+6*12+60)*0.8, 300)
        self.assertLess(85+sum(12-self.widths[c] for c in b'Select a player')*1.2, 300)

    def test_save_heading_and_full_choices_fit_unchanged_stack_frames(self):
        data, _, ram, _ = self.data('save')
        word = lambda a: struct.unpack_from('>I', data, a-ram)[0]
        expected = {0x80829820: 0x27BDFFA8, 0x80829834: 0xAFAF004C,
                    0x80829838: 0, 0x8082983C: 0, 0x80829840: 0, 0x80829844: 0,
                    0x8082989C: 0x8FA5004C, 0x808298A0: 0x24060009,
                    0x808298D4: 0x27BD0058, 0x80829B60: 0x27BDFF90,
                    0x80829B7C: 0x27AE0050, 0x80829BA8: 0x8DF90018,
                    0x80829BB4: 0xADD90018, 0x80829BF4: 0x24060010,
                    0x80829C70: 0x27A50060, 0x80829C74: 0x2406000B,
                    0x80829CBC: 0x27BD0070}
        self.assertEqual({at: word(at) for at in expected}, expected)
        modes = menus.pointer(data, 0x80829B70-ram, 0x80829B74-ram)-ram
        copied = data[modes:modes+28]
        self.assertEqual(copied, b'Save to FlashRAMSave to Pak\0')
        stack = bytearray([0xA5]*112)
        stack[0x50:0x6C] = copied
        self.assertEqual(stack[:0x50], bytes([0xA5]*0x50))
        self.assertEqual(stack[0x6C:], bytes([0xA5]*4))
        self.assertEqual(stack[0x50:0x60], b'Save to FlashRAM')
        self.assertEqual(stack[0x60:0x6B], b'Save to Pak')
        for text, x, scale in ((b'Save Menu', 110, 1.1), (b'Save to FlashRAM', 60, 1.2),
                               (b'Save to Pak', 100, 1.2)):
            self.assertLess(x+sum(12-self.widths[c] for c in text)*scale, 300)

    def test_retains_all_other_resources_actions_and_patch_reconstruction(self):
        changed = {0x747AA0, 0x7486E0}
        self.assertEqual(set(self.built), set(self.files))
        for vrom, entry in self.files.items():
            self.assertEqual((self.built[vrom].index, self.built[vrom].size), (entry.index, entry.size))
            if vrom in changed:
                continue
            actual, expected = self.built[vrom].extract(self.image), entry.extract(self.base)
            if vrom == 0x19D40:
                actual, expected = actual[:16], expected[:16]
            self.assertEqual(actual, expected, f'{vrom:08X}')
        self.assertEqual(apply_ups(self.native, self.patch), self.image)
        self.assertEqual(self.data('save')[0][:0x3B0], self.files[0x7486E0].extract(self.base)[:0x3B0])
        for name, value in self.report.items():
            if name.endswith('_changed') or name.endswith('_verified'):
                self.assertFalse(value, name)

    def test_refuses_unknown_owners_relocations_or_baseline(self):
        for name, (vrom, reloc, *_rest) in menus.PARTS.items():
            original = self.files[vrom].extract(self.base)
            relocation = self.files[reloc].extract(self.base)
            for index in (0, 1):
                args = [original, relocation]
                args[index] = bytes([args[index][0] ^ 1])+args[index][1:]
                with self.subTest(part=name, argument=index), self.assertRaises(ValueError):
                    menus.patch_owner(name, *args)
        with self.assertRaises(ValueError):
            menus.build(self.native, self.base[:-1])


if __name__ == '__main__':
    unittest.main()
