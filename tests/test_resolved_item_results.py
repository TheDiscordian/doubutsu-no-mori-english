"""Retain the completed source-bound native name batch without replaying it."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256, verified_rom

RUN = ROOT/'build/smoke-resolved-items-01'
BUILD = ROOT/'build/resolved-items-pilot'
PLAN = ROOT/'build/resolved-items-scenario.json'


@unittest.skipUnless((RUN/'results.json').is_file(), 'Local completed resolved-name evidence required')
class ResolvedItemResultsTests(unittest.TestCase):
    def test_every_native_call_full_buffer_guard_checkpoint_and_blank_save(self):
        raw = (RUN/'results.json').read_bytes()
        self.assertEqual(sha256(raw), '2d225ebe7ed71e5aaa21c4fc42844dcb378e8eb130139acb45a15435e16c5fdf')
        rows = json.loads(raw)
        info = json.loads((RUN/'run.json').read_text())
        plan = json.loads(PLAN.read_text())
        self.assertEqual((len(plan), len(rows)), (470, 471))
        self.assertFalse(any('error' in r or r.get('assertion') == 'failed' for r in rows))
        calls = [r for r in rows if 'test_only_function_call' in r]
        self.assertEqual(len(calls), 157)
        for actual, expected in zip(calls, [a['call'] for a in plan if 'call' in a], strict=True):
            self.assertEqual(actual['test_only_function_call'], expected['address'])
            self.assertEqual(actual['arguments'], expected['arguments'])
            self.assertTrue(actual['stack_restored'])
            if 'expect_return' in expected:
                self.assertEqual(actual['return_value'], expected['expect_return'])
        reads = [r for r in rows if r.get('assertion') == 'passed']
        self.assertEqual(len(reads), 149)
        for actual, expected in zip(reads, [a for a in plan if 'expect' in a], strict=True):
            self.assertEqual(actual['read'], expected['read'])
            self.assertEqual(actual['data'].lower(), expected['expect'].lower())
        self.assertEqual(info['rom_sha256'], sha256((BUILD/'animal-forest-halfwidth.z64').read_bytes()))
        self.assertEqual(info['scenario_sha256'], sha256(PLAN.read_bytes()))
        self.assertEqual(info['scenario_sha256'], '2a04f126c688ea3653890bcd5825e1b34939fe0e7d314038c5177fdcde7d54c2')
        self.assertEqual(info['audio'], 'disabled')
        self.assertEqual(info['seed_files'], [])
        for key in ('initial_screenshot', 'expansion_pak', 'allow_test_flash_write', 'allow_test_pak_write'):
            self.assertFalse(info[key])
        restored = max(i for i, r in enumerate(rows) if r.get('loaded_state') == 'test.bs1')
        self.assertTrue(any(r.get('read') == ['8019B000', 4] and r.get('data') == '00000000'
                            and r.get('assertion') == 'passed' for r in rows[restored+1:]))
        self.assertTrue(rows[-1]['graceful_shutdown'])
        for name, digest in (
                ('test.bs1', '24fda5c96a635cbbc64d26efd3bb206d32e625dd79ab9472a2c89d66862e90fa'),
                ('test.flash', 'b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260'),
                ('test.pak', 'ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51')):
            self.assertEqual(sha256((RUN/name).read_bytes()), digest)

    def test_completed_plan_reconstructs_from_all_new_source_bound_names(self):
        from resolved_item_scenario import scenario
        native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        module = json.loads((BUILD/'runtime-module.json').read_text())
        names = json.loads((ROOT/'build/resolved-items-resource/names.json').read_text())
        self.assertEqual(scenario(native, built, module, names), json.loads(PLAN.read_text()))
        selected = next(r for r in names['edits'] if r.get('item_reference_match') == 'item_20:000F')
        missing = {**names, 'edits': [r for r in names['edits'] if r is not selected]}
        with self.assertRaisesRegex(ValueError, '65 complete fields'):
            scenario(native, built, module, missing)


if __name__ == '__main__': unittest.main()
