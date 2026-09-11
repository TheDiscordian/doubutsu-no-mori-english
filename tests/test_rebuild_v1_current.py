"""Current-candidate recipe ordering, explicit inputs, resume safety, and output."""
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256, make_ups
from apply_translation import write_new
import rebuild_v1_current as recipe


class CurrentRecipeTests(unittest.TestCase):
    def test_every_correction_group_chains_to_the_current_scene_translation(self):
        names = [stage[0] for stage in recipe.STAGES]
        self.assertEqual(names, ['rc1', 'rc2', 'rc3', 'rc4', 'catalogue-repayment',
            'tune-confirmation', 'pak-heading', 'title-warning', 'gamestate-menu', 'scene-menu'])
        self.assertEqual(sum(stage[4] for stage in recipe.STAGES), 19)
        previous = recipe.BASE_SHA
        for name, module_name, _, result, _ in recipe.STAGES:
            module = importlib.import_module('font_expansion_memory' if name == 'rc4' else module_name)
            self.assertEqual(module.BASE_SHA, previous, name)
            previous = result
        self.assertEqual(previous, recipe.FINAL_SHA)
        makefile = (ROOT/'Makefile').read_text()
        complete = makefile.split('\ncomplete:\n', 1)[1].split('\n\n', 1)[0]
        self.assertLess(complete.index('rebuild_v0.py'), complete.index('rebuild_v1.py'))
        self.assertLess(complete.index('rebuild_v1.py'), complete.index('rebuild_v1_current.py'))

    @unittest.skipUnless((ROOT/'build/v1-rebuilt-04/rebuild.json').exists(), 'Checked artwork build required')
    def test_artwork_input_reader_needs_no_retained_candidate_rom(self):
        original = Path.read_bytes
        def read(path):
            self.assertNotIn('/build/v1rc', str(path))
            return original(path)
        with patch.object(Path, 'read_bytes', read):
            inputs = recipe.read_inputs(ROOT/'build/v1-rebuilt-04',
                ROOT/'local/rom/Doubutsu no Mori (Japan).z64',
                ROOT/'build/gamecube/files/foresta.rel.szs.decoded',
                ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt')
        identities = inputs[-1]
        self.assertEqual(set(identities), {'native', 'rel', 'symbols', 'artwork_rom', 'title_report', 'translation_report'})
        self.assertEqual(identities['artwork_rom']['sha256'], recipe.BASE_SHA)
        self.assertEqual(inputs[3]['output_sha256'], inputs[2]['baseline_sha256'])

    def test_dirty_sources_and_redirected_outputs_stop_before_compilation(self):
        inputs = (b'native', b'base', {}, {}, b'rel', b'symbols', {})
        with tempfile.TemporaryDirectory(dir=ROOT/'build', prefix='current-recipe-test-') as temporary:
            directory = Path(temporary)
            with patch.object(recipe, 'source_state', return_value={'worktree_modified': True}), \
                    patch.object(recipe, 'verify_toolchain') as compiler:
                with self.assertRaises(ValueError):
                    recipe.rebuild(inputs, directory/'new')
                compiler.assert_not_called()
                self.assertFalse((directory/'new').exists())
            redirected = directory/'link'
            redirected.symlink_to(directory, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, 'symlink'):
                recipe.rebuild(inputs, redirected, resume=True)

    def test_completed_boundary_checks_all_artifacts_and_source_binding(self):
        native, image = b'original test bytes', b'new test bytes'
        stage = ('group', 'fixture_builder', 'replay-only', sha256(image), 1)
        sources = {'tools/fixture_builder.py': '4'*64}
        ups = make_ups(native, image)
        with tempfile.TemporaryDirectory(prefix='current-boundary-test-') as temporary:
            output = Path(temporary)
            (output/'group').mkdir()
            for name, value in {'replay-only.z64': image, 'replay-only.ups': ups,
                                'compiled.bin': b'compiled fixture'}.items():
                write_new(output/'group'/name, value)
            saved = {'name': 'group', 'module': 'fixture_builder', 'input_sha256': sha256(native),
                     'output_sha256': sha256(image), 'patch_sha256': sha256(ups), 'correction_stages': 1,
                     'builder_sha256': '4'*64, 'outputs': recipe.output_files(output, 'group')}
            write_new(output/'stage-01.json', recipe.json_bytes(saved))
            self.assertEqual(recipe.completed_stage(output, 1, stage, sha256(native), sources, native)[1:], (image, ups))
            for field, value in (('module', 'other'), ('input_sha256', '0'*64), ('builder_sha256', '0'*64),
                                 ('outputs', {}), ('patch_sha256', '0'*64)):
                wrong = {**saved, field: value}
                with self.subTest(field=field), patch.object(Path, 'read_text', return_value=json.dumps(wrong)):
                    with self.assertRaises(ValueError):
                        recipe.completed_stage(output, 1, stage, sha256(native), sources, native)
            # Fixture-only modification: retained user/build artifacts are never written.
            (output/'group/compiled.bin').write_bytes(b'altered fixture')
            with self.assertRaises(ValueError):
                recipe.completed_stage(output, 1, stage, sha256(native), sources, native)

    def test_changed_resume_manifest_stops_without_running_a_builder(self):
        inputs = (b'native', b'base', {}, {}, b'rel', b'symbols', {})
        with tempfile.TemporaryDirectory(dir=ROOT/'build', prefix='current-resume-test-') as temporary:
            output = Path(temporary)
            write_new(output/'inputs.json', b'{}\n')
            with patch.object(recipe, 'source_state', return_value={'worktree_modified': False}), \
                    patch.object(recipe, 'construct') as builder:
                with self.assertRaisesRegex(ValueError, 'cannot resume'):
                    recipe.rebuild(inputs, output, resume=True)
                builder.assert_not_called()
            self.assertEqual(list(output.iterdir()), [output/'inputs.json'])

    def test_unknown_final_rom_is_not_published(self):
        with tempfile.TemporaryDirectory(prefix='current-final-test-') as temporary:
            output = Path(temporary)
            with self.assertRaises(ValueError):
                recipe.publish_final(output, b'native', b'wrong', b'wrong', {}, [])
            self.assertFalse((output/'final').exists())


OUT = ROOT/'build/v1-current-01'


@unittest.skipUnless((OUT/'rebuild.json').exists(), 'Executed complete current correction recipe required')
class ActualCurrentRecipeTests(unittest.TestCase):
    def test_complete_execution_and_exact_current_rom(self):
        inputs = json.loads((OUT/'inputs.json').read_text())
        report = json.loads((OUT/'rebuild.json').read_text())
        self.assertTrue(report['complete'])
        self.assertEqual((report['groups'], report['correction_stages']), (10, 19))
        self.assertEqual(inputs['retained_rc_inputs'], [])
        self.assertEqual(report['recipe_sha256'], inputs['sources']['tools/rebuild_v1_current.py'])
        self.assertEqual(inputs['source_revision'], report['source_revision'])
        self.assertEqual([row['name'] for row in report['stages']], [row[0] for row in recipe.STAGES])
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        previous = recipe.BASE_SHA
        for i, stage in enumerate(recipe.STAGES, 1):
            saved, image, ups = recipe.completed_stage(OUT, i, stage, previous, inputs['sources'], native)
            self.assertEqual(saved, report['stages'][i-1])
            previous = stage[3]
        self.assertEqual(sha256(image), recipe.FINAL_SHA)
        self.assertEqual(sha256(ups), recipe.PATCH_SHA)
        self.assertEqual((OUT/'final'/recipe.ROM_NAME).read_bytes(), image)
        self.assertEqual((OUT/'final/animal-forest-english.ups').read_bytes(), ups)
        for key in ('worktree_modified', 'save_format_changed', 'native_tests_run', 'original_hardware_verified'):
            self.assertFalse(report[key])


if __name__ == '__main__':
    unittest.main()
