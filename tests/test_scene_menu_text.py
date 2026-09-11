"""Complete scene-selector text, native pointers, bounded layout, and retention."""
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, by_vrom, apply_ups
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
import scene_menu_text as scene


@unittest.skipUnless((ROOT/'build/v1rc7/Animal Forest English V1RC7.z64').exists(), 'Local RC7 required')
class SceneMenuTextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT/'build/v1rc7/Animal Forest English V1RC7.z64').read_bytes()
        cls.files = by_vrom(cls.base)
        cls.old = cls.files[scene.VROM].extract(cls.base)
        cls.reloc = cls.files[scene.RELOC].extract(cls.base)
        cls.image, cls.ups, cls.report = scene.build(cls.native, cls.base)
        cls.built = by_vrom(cls.image)
        cls.data = cls.built[scene.VROM].extract(cls.image)
        cls.rows = {row['original_offset']: row for row in cls.report['records']}

    def text(self, original):
        row = self.rows[original]
        return self.data[row['offset']:].split(b'\0', 1)[0].decode('ascii')

    def test_complete_inventory_and_existing_english(self):
        originals = scene.strings(self.old)
        self.assertEqual(len(self.rows), 101)
        self.assertEqual(set(self.rows), set(originals))
        self.assertEqual(self.report['translated_records'], 76)
        for at, before, after in scene.OTHER:
            self.assertEqual(scene.visible(originals[at]), before)
            self.assertEqual(self.text(at), after)
        for i, (before, after) in enumerate(scene.SCENES):
            at, callback, destination = struct.unpack_from('>3I', self.data, 0x1B60+i*12)
            text = self.data[at-scene.RAM:].split(b'\0', 1)[0].decode('ascii')
            self.assertEqual(text, f'{i+1:2}:'+after)
            self.assertEqual((callback, destination), (scene.RAM, i))
        for original, row in self.rows.items():
            self.assertEqual(self.text(original), row['english'])
            if not row['translated']:
                self.assertEqual(row['source'], row['english'])
        self.assertEqual(self.text(0x223C), 'Please insert Side B.')
        self.assertEqual(self.text(0x22A0).count('no rush'), 1)
        self.assertIn('No rush, no rush.', self.text(0x22A0))
        self.assertIn('Take a break, take a break.', self.text(0x22A0))
        end = scene.TEXT_START+self.report['text_bytes_used']
        self.assertEqual(self.data[end:scene.TEXT_END], bytes(scene.TEXT_END-end))
        self.assertGreaterEqual(scene.TEXT_END-end, 0)

    def test_relocated_native_references_and_callbacks_at_three_bases(self):
        refs = scene.references(self.old, self.reloc)
        for base in (0x801A6010, 0x802F8010, 0x803D0010):
            loaded = relocate_verified_data(Image(scene.RAM, len(self.data), scene.SECTIONS),
                                             self.data, self.reloc, base)
            for hi, at, original in refs:
                if hi is None:
                    target = struct.unpack_from('>I', loaded, at)[0]
                else:
                    target = ((struct.unpack_from('>I', loaded, hi)[0] & 65535) << 16)
                    target += struct.unpack_from('>h', loaded, at+2)[0]
                self.assertEqual(target, base+self.rows[original]['offset'])
                self.assertEqual(loaded[target-base:].split(b'\0', 1)[0].decode('ascii'), self.text(original))
            for i in range(35):
                self.assertEqual(struct.unpack_from('>II', loaded, 0x1B64+i*12), (base, i))
            self.assertLess(base+len(loaded), 0x80400000)

    def test_native_draw_positions_complete_formats_and_screen_bounds(self):
        # Bind actual call/argument words to the font-grid model, not just prose.
        expected = {0xF6C: 0x24050001, 0xF70: 0x0C00ABBB, 0xF74: 0x26060004,
                    0xF5C: 0x241E000F, 0xE44: 0x2405000A, 0xE48: 0x0C00ABBB,
                    0xE4C: 0x2406000F, 0x1624: 0x24050017, 0x1628: 0x0C00ABBB,
                    0x162C: 0x24060010, 0x1740: 0x2405001A, 0x1744: 0x0C00ABBB}
        self.assertEqual({at: scene.word(self.data, at) for at in expected}, expected)
        for _, text in scene.SCENES:
            self.assertLessEqual(1+3+len(text), 23)
        for original in (0x2188, 0x21A4, 0x21B8, 0x21D0, 0x21E4, 0x21F8,
                         0x220C, 0x2224, 0x223C, 0x225C, 0x2280, 0x22A0):
            lines = self.text(original).split('\n')
            for i, line in enumerate(lines):
                self.assertLessEqual((10 if i == 0 else 0)+len(line), 40)
                self.assertLess(15+i, 30)
            if len(lines) > 1:
                self.assertTrue(lines[1].startswith(' '*10))
        cases = [
            (0x23B0, [self.text(at) for at in (0x2384, 0x238C, 0x2394, 0x239C, 0x23A4)]),
            (0x23D8, [self.text(at) for at in (0x23C0, 0x23CC)]),
            (0x24B4, [self.text(0x2454+i*12) for i in range(8)]),
            (0x23E8, [0, 255]),  # Existing clothing range and unchanged integer directive.
            (0x2518, [self.text(at) for at in (0x24C0, 0x24C8, 0x24D4, 0x24E4, 0x24F0, 0x24FC, 0x250C)]),
        ]
        for original, values in cases:
            for value in values:
                for line_no, line in enumerate((self.text(original) % value).split('\n')):
                    self.assertLessEqual((23 if line_no == 0 else 0)+len(line), 40)
                    if line_no:
                        self.assertTrue(line.startswith(' '*23))
        for original in (0x2370, 0x23F8, 0x2410, 0x2428, 0x243C):
            self.assertLessEqual(23+len(self.text(original)), 40)
        self.assertLessEqual(26+len(self.text(0x2528)), 40)

    def test_only_text_references_and_one_coordinate_change(self):
        allowed = set(range(scene.TEXT_START, scene.TEXT_END))
        for hi, at, _ in scene.references(self.old, self.reloc):
            allowed.update(range(at, at+4))
            if hi is not None:
                allowed.update(range(hi, hi+4))
                self.assertEqual(scene.word(self.old, hi) & 0xFFFF0000,
                                 scene.word(self.data, hi) & 0xFFFF0000)
                self.assertEqual(scene.word(self.old, at) & 0xFFFF0000,
                                 scene.word(self.data, at) & 0xFFFF0000)
        for at, before, after in scene.LAYOUT_WORDS:
            self.assertEqual((scene.word(self.old, at), scene.word(self.data, at)), (before, after))
            allowed.update(range(at, at+4))
        self.assertEqual(len(self.old), len(self.data))
        for i, (before, after) in enumerate(zip(self.old, self.data)):
            if i not in allowed:
                self.assertEqual(before, after, f'{i:04X}')
        # Initialization can change player state in the native debug menu.
        # It and every navigation/action routine stay untouched and unexecuted.
        self.assertEqual(self.data[:0xE34], self.old[:0xE34])
        self.assertEqual(self.data[0x1A28:0x1B60], self.old[0x1A28:0x1B60])
        self.assertEqual(self.data[scene.TEXT_END:], self.old[scene.TEXT_END:])

    def test_all_other_cartridge_resources_metadata_and_ups_retained(self):
        self.assertEqual(set(self.files), set(self.built))
        for vrom, before in self.files.items():
            after = self.built[vrom]
            self.assertEqual((before.index, before.size), (after.index, after.size))
            if vrom == scene.VROM:
                continue
            expected, actual = before.extract(self.base), after.extract(self.image)
            if vrom == 0x19D40:
                expected, actual = expected[:16], actual[:16]
            self.assertEqual(actual, expected, f'{vrom:08X}')
        code = self.built[CODE_VROM].extract(self.image)
        self.assertEqual(code[0x80106E50-CODE_RAM:0x80106E80-CODE_RAM], scene.METADATA)
        self.assertEqual(apply_ups(self.native, self.ups), self.image)
        for name, value in self.report.items():
            if name.endswith('_changed') or name.endswith('_verified'):
                self.assertFalse(value, name)

    def test_rejects_changed_inputs_and_incomplete_or_unsafe_english(self):
        for owner, reloc in ((self.old[:-1], self.reloc), (self.old, self.reloc[:-1])):
            with self.assertRaises(ValueError):
                scene.patch_owner(owner, reloc)
        with self.assertRaises(ValueError):
            scene.build(self.native, self.base[:-1])
        for replacement in ('日本語', 'Bad %s', '\x01', '\x7f', 'a'*2000):
            rows = list(scene.OTHER)
            at, before, _ = rows[0]
            rows[0] = (at, before, replacement)
            with self.subTest(text=replacement[:16]), patch.object(scene, 'OTHER', tuple(rows)):
                with self.assertRaises(ValueError):
                    scene.patch_owner(self.old, self.reloc)
        with patch.object(scene, 'OTHER', scene.OTHER[1:]):
            with self.assertRaises(ValueError):
                scene.patch_owner(self.old, self.reloc)


if __name__ == '__main__':
    unittest.main()
