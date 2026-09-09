"""Retain the completed source-bound native name batch without replaying it."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256, verified_rom

RUN = ROOT/'build/smoke-sheet-items-01'
BUILD = ROOT/'build/sheet-items-pilot'
PLAN = ROOT/'build/sheet-items-scenario.json'


@unittest.skipUnless((RUN/'results.json').is_file(), 'Local completed sheet-name evidence required')
class SheetItemResultsTests(unittest.TestCase):
    def test_every_native_call_full_buffer_guard_checkpoint_and_blank_save(self):
        raw = (RUN/'results.json').read_bytes()
        self.assertEqual(sha256(raw), 'efdd15c82fabdc0dcf2be5d7367e53085345f8d0a4b7eede61aff2c9ccd677d9')
        rows = json.loads(raw)
        info = json.loads((RUN/'run.json').read_text())
        plan = json.loads(PLAN.read_text())
        self.assertEqual((len(plan), len(rows)), (1580, 1581))
        self.assertFalse(any('error' in r or r.get('assertion') == 'failed' for r in rows))
        calls = [r for r in rows if 'test_only_function_call' in r]
        self.assertEqual(len(calls), 527)
        for actual, expected in zip(calls, [a['call'] for a in plan if 'call' in a], strict=True):
            self.assertEqual(actual['test_only_function_call'], expected['address'])
            self.assertEqual(actual['arguments'], expected['arguments'])
            self.assertTrue(actual['stack_restored'])
            if 'expect_return' in expected:
                self.assertEqual(actual['return_value'], expected['expect_return'])
        reads = [r for r in rows if r.get('assertion') == 'passed']
        self.assertEqual(len(reads), 519)
        for actual, expected in zip(reads, [a for a in plan if 'expect' in a], strict=True):
            self.assertEqual(actual['read'], expected['read'])
            self.assertEqual(actual['data'].lower(), expected['expect'].lower())
        self.assertEqual(info['rom_sha256'], sha256((BUILD/'animal-forest-halfwidth.z64').read_bytes()))
        self.assertEqual(info['scenario_sha256'], sha256(PLAN.read_bytes()))
        self.assertEqual(info['scenario_sha256'], '5600df713f14f1452707ec36fd3ac73df51c51b3503beccb88d556e2099d5050')
        self.assertEqual(info['audio'], 'disabled')
        self.assertEqual(info['seed_files'], [])
        for key in ('initial_screenshot', 'expansion_pak', 'allow_test_flash_write', 'allow_test_pak_write'):
            self.assertFalse(info[key])
        restored = max(i for i, r in enumerate(rows) if r.get('loaded_state') == 'test.bs1')
        self.assertTrue(any(r.get('read') == ['8019B000', 4] and r.get('data') == '00000000'
                            and r.get('assertion') == 'passed' for r in rows[restored+1:]))
        self.assertTrue(rows[-1]['graceful_shutdown'])
        for name, digest in (
                ('test.bs1', '48684b83ae2f04cc0b499d9655e3b3ea492c2f57fd4626735d1db63ed5feab35'),
                ('test.flash', 'b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260'),
                ('test.pak', 'ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51')):
            self.assertEqual(sha256((RUN/name).read_bytes()), digest)

    def test_completed_plan_reconstructs_from_all_new_source_bound_names(self):
        from sheet_item_scenario import scenario
        native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        module = json.loads((BUILD/'runtime-module.json').read_text())
        names = json.loads((ROOT/'build/sheet-items-resource/names.json').read_text())
        self.assertEqual(scenario(native, built, module, names), json.loads(PLAN.read_text()))
        selected = next(r for r in names['edits'] if r.get('item_reference_match') == 'item_10:0060')
        missing = {**names, 'edits': [r for r in names['edits'] if r is not selected]}
        with self.assertRaisesRegex(ValueError, '834 complete fields'):
            scenario(native, built, module, missing)


if __name__ == '__main__': unittest.main()
