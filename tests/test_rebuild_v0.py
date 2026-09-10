"""Focused orchestration checks; the actual clean build is separate evidence."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import rebuild_v0 as rebuild


class BaseRecipeTests(unittest.TestCase):
    def test_stages_have_unique_owned_outputs_and_existing_tools(self):
        self.assertEqual(len(rebuild.STAGES), len({row[0] for row in rebuild.STAGES}))
        self.assertEqual(len(rebuild.STAGES), len({row[2] for row in rebuild.STAGES}))
        for name, tool, output, args in rebuild.STAGES:
            with self.subTest(stage=name):
                self.assertTrue(output.startswith('build/'))
                self.assertNotIn('..', Path(output).parts)
                suffix = '' if tool.endswith('.sh') else '.py'
                self.assertTrue((rebuild.ROOT/'tools'/(tool+suffix)).is_file())
                self.assertNotIn('--output', args)

    def test_arguments_bind_to_isolated_checkout(self):
        source = Path('/isolated/source')
        command = rebuild.command(rebuild.STAGES[0], source)
        self.assertIn(str(source/rebuild.NATIVE), command)
        self.assertIn(str(source/rebuild.LEGACY), command)
        self.assertEqual(command[-2:], ['--output', str(source/'build/inspect')])
        wrapper = next(row for row in rebuild.STAGES if row[0] == 'integration')
        self.assertEqual(rebuild.command(wrapper, source), ['bash', 'tools/build_apology_input_pilot.sh'])

    def test_candidate_font_does_not_require_installed_world_items(self):
        rows = {row[0]: row for row in rebuild.STAGES}
        font = rows['candidate-font']
        self.assertNotIn('--world-names', font[3])
        args = rows['candidates'][3]
        self.assertEqual(args[args.index('--extended-font')+1], font[2])
        self.assertIn('--world-names', rows['world-font'][3])

    def test_output_inventory_rejects_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root/'build/test'
            target.mkdir(parents=True)
            (target/'test.bin').write_bytes(b'test')
            self.assertEqual(rebuild.output_files(root, 'build/test'),
                             {'build/test/test.bin': rebuild.sha256(b'test')})
            (target/'alias.bin').symlink_to('test.bin')
            with self.assertRaisesRegex(ValueError, 'symlink'):
                rebuild.output_files(root, 'build/test')

    def test_final_requires_corrected_cartridge_not_any_generated_rom(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp)
            base = source/'build/v0-hardware-fixes-02'
            base.mkdir(parents=True)
            (base/'animal-forest-halfwidth.z64').write_bytes(b'not a ROM')
            (base/'build.json').write_text(json.dumps({}))
            with self.assertRaisesRegex(ValueError, 'differs'):
                rebuild.check_final(source)


if __name__ == '__main__':
    unittest.main()
