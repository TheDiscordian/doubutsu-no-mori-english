"""Actual REL bindings, source geometry, and native-compatible animation sizes."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from title_model import bindings, title_pointers


@unittest.skipUnless((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').is_file(),
                     'Supplied English title extraction required')
class TitleModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.report = bindings(cls.rel, cls.symbols)

    def test_complete_models_and_three_animation_trees(self):
        self.assertEqual(len(self.report['pointer_fixups']), 97)
        self.assertEqual(len(self.report['models']), 23)
        self.assertFalse(self.report['installed'])
        self.assertEqual([(s['name'], len(s['joints']), s['shown_joints'], s['joint_work_entries'],
                           s['dynamic_tracks'], s['keyframes'], s['animation_duration'])
                          for s in self.report['skeletons']],
                         [('animal', 21, 8, 22, 39, 221, 121),
                          ('cros', 14, 5, 15, 27, 264, 121),
                          ('sing', 14, 5, 15, 27, 281, 121)])

    def test_source_crop_winding_and_distinct_palettes_are_preserved(self):
        models = {row['offset']: row for row in self.report['models']}
        cropped = models['005EA0D0']
        self.assertEqual((cropped['width'], cropped['height']), (64, 64))
        self.assertEqual(cropped['texture_bounds'], [0, 0, 1920, 2048])
        self.assertEqual({row['palette'] for row in models.values()},
                         {None, '005E6A20', '005EEB40', '005F1760'})
        self.assertTrue(all(row['triangles'] == [[0, 1, 2], [0, 2, 3]] for row in models.values()))
        self.assertEqual(models['005EA040']['vertices'][0],
                         [0, -2000, 1000, 1, 0, 3072, 255, 255, 255, 255])

    def test_changed_sources_and_missing_actual_fixup_reject(self):
        with self.assertRaises(ValueError): bindings(self.rel[:-1], self.symbols)
        with self.assertRaises(ValueError): bindings(self.rel, self.symbols+b'\n')
        pointers = title_pointers(self.rel)
        pointers.pop(0x5EA2C0)
        with patch('title_model.title_pointers', return_value=pointers), self.assertRaisesRegex(ValueError, 'Missing actual'):
            bindings(self.rel, self.symbols)

    def test_equal_sized_wrong_scoped_palette_and_wrong_joint_shape_reject(self):
        pointers = title_pointers(self.rel)
        pointers[0x5EA044] = 0x5EEB40
        with patch('title_model.title_pointers', return_value=pointers), self.assertRaisesRegex(ValueError, 'scoped title palette'):
            bindings(self.rel, self.symbols)
        pointers = title_pointers(self.rel)
        pointers[0x5EA1C0+3*12] = 0x5E6A40
        with patch('title_model.title_pointers', return_value=pointers), self.assertRaisesRegex(ValueError, 'skeleton tree'):
            bindings(self.rel, self.symbols)


if __name__ == '__main__':
    unittest.main()
