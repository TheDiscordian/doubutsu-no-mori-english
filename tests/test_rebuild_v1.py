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
from toolchain import profile_sha256
from build_keyboard_grid import source_bytes, sources


class RecipeTests(unittest.TestCase):
    def test_order_and_exclusive_outputs(self):
        stages = [row[0] for row in recipe.STAGES]
        self.assertEqual(len(stages), 27)
        self.assertEqual(len(set(stages)), 27)
        self.assertLess(stages.index('grid-replay-only'), stages.index('corrected-grid'))
        self.assertEqual(stages[-3:], ['stall', 'shop-interiors', 'title'])
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

    def test_generated_graphics_output_must_be_inside_checkout_build_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)/'source'
            root.mkdir()
            with patch.object(recipe, 'ROOT', root):
                good = root/'build/new'
                self.assertEqual(recipe.checked_output(good), good)
                for path in (root/'unignored', Path(temporary)/'outside'):
                    with self.assertRaisesRegex(ValueError, 'inside this source checkout'):
                        recipe.checked_output(path)
                    self.assertFalse(path.exists())
                good.mkdir(parents=True)
                with self.assertRaisesRegex(ValueError, 'fresh directory'):
                    recipe.checked_output(good)
                redirected = root/'build/link'
                redirected.symlink_to(Path(temporary)/'missing')
                with self.assertRaisesRegex(ValueError, 'fresh directory'):
                    recipe.checked_output(redirected)

    def test_source_inventory_binds_recipe_and_records_uncommitted_state(self):
        inventory = recipe.source_inventory()
        self.assertEqual(inventory['tools/rebuild_v1.py'], sha256((ROOT/'tools/rebuild_v1.py').read_bytes()))
        state = recipe.source_state()
        self.assertEqual(state['recipe_sha256'], inventory['tools/rebuild_v1.py'])
        self.assertIsInstance(state['worktree_modified'], bool)


@unittest.skipUnless((ROOT/'build/v1-rebuilt-02/rebuild.json').is_file(), 'Local committed recipe execution required')
class ActualRebuildTests(unittest.TestCase):
    def test_all_stages_and_exact_packaged_result(self):
        directory = ROOT/'build/v1-rebuilt-02'
        inputs = json.loads((directory/'inputs.json').read_text())
        self.assertFalse(inputs['worktree_modified'])
        self.assertEqual(inputs['recipe_sha256'], inputs['sources']['tools/rebuild_v1.py'])
        self.assertEqual(inputs['source_revision'], 'd54f2f89bd832bc59957441dc9101010fc52a740')
        report = json.loads((directory/'rebuild.json').read_text())
        self.assertTrue(report['complete'])
        self.assertEqual([r['stage'] for r in report['stages']],
                         [r[0] for r in recipe.STAGES if r[0] != 'shop-interiors'])
        final = directory/'final'
        image, patch_data = [(final/name).read_bytes() for name in
                            ('animal-forest-title-preview.z64', 'animal-forest-title-preview.ups')]
        # This immutable record proves package 03, not the new interior-sign build.
        self.assertEqual(sha256(image), '128f19b734565e5e0c3af15aaf1fef8fb066155039404a2bfdd29efe8010bf19')
        self.assertEqual(sha256(patch_data), '600ec4b132646673ae8f1894b5131b642439b0b82e171c96ba351175cc1ddef0')
        self.assertEqual(profile_sha256(json.loads((final/'preview.json').read_text())),
                         '20f970392d1d60136613ee439b3cc90bcc2abf77941fcf34f42f900b7877a815')
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


@unittest.skipUnless((ROOT/'build/v1-rebuilt-03/rebuild.json').is_file(), 'Current 27-stage execution required')
class CurrentRebuildTests(unittest.TestCase):
    def test_current_recipe_and_final_interiors_are_rebuilt_from_source(self):
        directory = ROOT/'build/v1-rebuilt-03'
        inputs = json.loads((directory/'inputs.json').read_text())
        self.assertFalse(inputs['worktree_modified'])
        self.assertEqual(inputs['recipe_sha256'], sha256((ROOT/'tools/rebuild_v1.py').read_bytes()))
        record = json.loads((directory/'rebuild.json').read_text())
        self.assertTrue(record['complete'])
        self.assertEqual([s['stage'] for s in record['stages']], [s[0] for s in recipe.STAGES])
        final = directory/'final'
        image, ups = [(final/name).read_bytes() for name in
                      ('animal-forest-title-preview.z64', 'animal-forest-title-preview.ups')]
        recipe.check_final(image, ups, json.loads((final/'preview.json').read_text()))
        import shop_interior_artwork as shop
        interior = json.loads((directory/'replay/26-shop-interiors/build.json').read_text())
        shop.verify_installed((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(), image, interior,
            (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())


if __name__ == '__main__':
    unittest.main()
