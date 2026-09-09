"""Frozen complete diagnostic loads without executing test sounds or states."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
from rendering_diagnostics_scenario import scenario

RUN = ROOT/'build/smoke-rendering-diagnostics-01'
BUILD = ROOT/'build/rendering-diagnostics-pilot'
PLAN = ROOT/'build/rendering-diagnostics-scenario.json'


@unittest.skipUnless((RUN/'results.json').is_file(), 'Completed diagnostic native loads required')
class RenderingDiagnosticResultsTests(unittest.TestCase):
    def test_complete_native_loads_buffers_guards_and_checkpoint(self):
        rows, plan = json.loads((RUN/'results.json').read_text()), json.loads(PLAN.read_text())
        self.assertEqual(sha256((RUN/'results.json').read_bytes()),
                         'db5f6d82a97cba9232ae9fc698a90e823a71dddb4dba31e95a6b329245a3d774')
        self.assertEqual((len(rows), len(plan)), (29, 28))
        self.assertFalse(any('error' in r or r.get('assertion') == 'failed' for r in rows))
        calls = [r for r in rows if 'test_only_function_call' in r]
        reads = [r for r in rows if r.get('assertion') == 'passed']
        self.assertEqual((len(calls), len(reads)), (4, 14))
        for actual, expected in zip(calls, [r['call'] for r in plan if 'call' in r], strict=True):
            self.assertEqual(actual['test_only_function_call'], '8009E558')
            self.assertEqual(actual['arguments'], expected['arguments'])
            self.assertEqual(actual['return_value'], 1); self.assertTrue(actual['stack_restored'])
        for actual, expected in zip(reads, [r for r in plan if 'expect' in r], strict=True):
            self.assertEqual(actual['read'], expected['read'])
            self.assertEqual(actual['data'].lower(), expected['expect'].lower())
        self.assertTrue(any(r.get('loaded_state') == 'test.bs1' for r in rows))
        self.assertEqual(reads[-1]['data'], bytes(4).hex()); self.assertTrue(rows[-1]['graceful_shutdown'])
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text())
        self.assertEqual(scenario(native, built, report), plan)
        info = json.loads((RUN/'run.json').read_text())
        self.assertEqual(info['rom_sha256'], sha256(built))
        self.assertEqual(info['scenario_sha256'], sha256(PLAN.read_bytes()))
        self.assertEqual(info['scenario_sha256'], '51715bcddf14953b8fc0fab3423af8bbb8f065566c2ff9a73671023e1506eb19')
        self.assertEqual(info['audio'], 'disabled'); self.assertEqual(info['seed_files'], [])
        for key in ('initial_screenshot', 'expansion_pak', 'allow_test_flash_write', 'allow_test_pak_write'):
            self.assertFalse(info[key])
        for name, digest in (
                ('test.bs1', 'd88d10d4b05d0ba3ab52ef420b77c88c81d9146b963839342b297d353e171965'),
                ('test.flash', 'b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260'),
                ('test.pak', 'ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51')):
            self.assertEqual(sha256((RUN/name).read_bytes()), digest)


if __name__ == '__main__': unittest.main()
