"""Focused new diagnostic-string checks, without game or historical build runs."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, by_vrom, verified_rom
from main_diagnostic_text import TEXT, FUNCTIONS, POINTER_TABLE, encoded_slot, patch_main


class SlotTests(unittest.TestCase):
    def test_rejects_truncation_controls_and_changed_formats(self):
        for original, english, capacity in (('x', 'too long', 4), ('x', 'A\nB', 8),
            ('x', 'A\0B', 8), ('x', '\x7f', 8), ('x', '', 8), ('%d', '%s', 8), ('x', '%', 8)):
            with self.subTest(english=english), self.assertRaises(ValueError):
                encoded_slot(original, english, capacity)
        self.assertEqual(encoded_slot('%d', 'No. %d', 8), b'No. %d\0\0')

    def test_complete_recipe_includes_new_final_stage(self):
        makefile = (ROOT/'Makefile').read_text().split('\ncomplete:\n', 1)[1]
        self.assertLess(makefile.index('rebuild_v1_current.py'), makefile.index('main_diagnostic_text.py'))
        self.assertIn('source/build/v1-current/final/Animal Forest English V1-current.z64', makefile)
        self.assertIn('source/build/v1-final', makefile)


@unittest.skipUnless((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').exists(), 'Original native input required')
class MainTextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
        cls.code = by_vrom(native)[CODE_VROM].extract(native)

    def test_all_strings_and_only_their_existing_slots_change(self):
        changed, records = patch_main(self.code)
        self.assertEqual(len(records), 13)
        self.assertEqual(len(changed), len(self.code))
        allowed = set()
        for address, size, original, english in TEXT:
            offset = address-CODE_RAM
            self.assertEqual(changed[offset:offset+size], encoded_slot(original, english, size))
            allowed.update(range(offset, offset+size))
        self.assertTrue(all(a == b or i in allowed for i, (a, b) in enumerate(zip(self.code, changed))))
        pointers = struct.unpack_from('>11I', changed, POINTER_TABLE-CODE_RAM)
        self.assertEqual(pointers, tuple(row[0] for row in TEXT[:11]))
        for pointer, row in zip(pointers, TEXT[:11]):
            offset = pointer-CODE_RAM
            self.assertEqual(changed[offset:changed.index(b'\0', offset)].decode(), row[3])
            self.assertLessEqual(3+len('RandomStep ')+len(row[3]), 40)
        for start, end, _ in FUNCTIONS:
            self.assertEqual(changed[start-CODE_RAM:end-CODE_RAM], self.code[start-CODE_RAM:end-CODE_RAM])

    def test_rejects_changed_slots_reader_or_table(self):
        offsets = [row[0]-CODE_RAM for row in TEXT]+[POINTER_TABLE-CODE_RAM, FUNCTIONS[0][0]-CODE_RAM]
        for offset in offsets:
            changed = bytearray(self.code)
            changed[offset] ^= 1
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                patch_main(bytes(changed))


if __name__ == '__main__':
    unittest.main()
