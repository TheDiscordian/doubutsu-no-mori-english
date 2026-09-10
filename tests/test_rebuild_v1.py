"""Full post-v0 recipe identities, exclusive outputs, and final corrected grid."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import rebuild_v1 as recipe
from aflib import sha256
from build_keyboard_grid import source_bytes, sources


class RecipeTests(unittest.TestCase):
    def test_order_and_exclusive_outputs(self):
        stages = [row[0] for row in recipe.STAGES]
        self.assertEqual(len(stages), 26)
        self.assertEqual(len(set(stages)), 26)
        self.assertLess(stages.index('grid-replay-only'), stages.index('corrected-grid'))
        self.assertEqual(stages[-2:], ['stall', 'title'])
        with tempfile.TemporaryDirectory(prefix='af-v1-output-') as directory:
            out = Path(directory)/'result'
            recipe.publish(out, b'rom fixture', b'patch fixture', {})
            self.assertEqual((out/'replay-only.z64').read_bytes(), b'rom fixture')
            with self.assertRaises(FileExistsError):
                recipe.publish(out, b'changed', b'changed', {})
            self.assertEqual((out/'replay-only.z64').read_bytes(), b'rom fixture')

    def test_only_two_reviewed_source_changes_and_invalid_version_rejection(self):
        old, current = sources(1), sources(2)
        self.assertEqual(set(old), set(current))
        self.assertEqual({p for p in old if old[p] != current[p]},
                         {'overlays/keyboard_grid/core.h', 'overlays/keyboard_grid/overlay.ld'})
        path = ROOT/'overlays/keyboard_grid/core.h'
        self.assertEqual(source_bytes(path, 2), path.read_bytes())
        with self.assertRaises(ValueError):
            source_bytes(path, 3)
        with patch.object(Path, 'read_bytes', return_value=b'unknown header'), self.assertRaises(ValueError):
            source_bytes(path, 1)

    def test_unknown_final_result_is_rejected(self):
        with self.assertRaises(ValueError):
            recipe.check_final(b'wrong cartridge', b'wrong patch', {})

    def test_source_inventory_binds_recipe_and_records_uncommitted_state(self):
        inventory = recipe.source_inventory()
        self.assertEqual(inventory['tools/rebuild_v1.py'], sha256((ROOT/'tools/rebuild_v1.py').read_bytes()))
        state = recipe.source_state()
        self.assertEqual(state['recipe_sha256'], inventory['tools/rebuild_v1.py'])
        self.assertIsInstance(state['worktree_modified'], bool)


@unittest.skipUnless((ROOT/'build/v1-rebuilt-01/rebuild.json').is_file(), 'Local complete recipe execution required')
class ActualRebuildTests(unittest.TestCase):
    def test_all_stages_and_exact_packaged_result(self):
        directory = ROOT/'build/v1-rebuilt-01'
        report = json.loads((directory/'rebuild.json').read_text())
        self.assertTrue(report['complete'])
        self.assertEqual([r['stage'] for r in report['stages']], [r[0] for r in recipe.STAGES])
        final = directory/'final'
        image, patch_data = [(final/name).read_bytes() for name in
                            ('animal-forest-title-preview.z64', 'animal-forest-title-preview.ups')]
        recipe.check_final(image, patch_data, json.loads((final/'preview.json').read_text()))
        self.assertEqual(sha256(image), recipe.ROM_SHA)
        self.assertFalse(report['clean_clone_base_translation_recipe'])
        self.assertFalse(report['hardware_acceptance'])
        from keyboard_grid_overlay import validate
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        for name, version in (('grid-replay-only', 1), ('corrected-grid', 2)):
            compiled = directory/'compiled'/name
            metadata = json.loads((compiled/'overlay.json').read_text())
            self.assertEqual(metadata['version'], version)
            validate(native, (compiled/'overlay.bin').read_bytes(),
                     (compiled/'relocation.bin').read_bytes(), metadata)


if __name__ == '__main__':
    unittest.main()
