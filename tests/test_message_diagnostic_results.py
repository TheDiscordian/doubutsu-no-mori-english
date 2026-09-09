"""Frozen native diagnostic continuation evidence; no completed batch replay."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
from sequence_test_scenario import scenario

RUN = ROOT/'build/smoke-message-diagnostic-01'
BUILD = ROOT/'build/message-diagnostic-pilot'
PLAN = ROOT/'build/message-diagnostic-scenario.json'


@unittest.skipUnless((RUN/'results.json').is_file(), 'Completed diagnostic continuation batch required')
class MessageDiagnosticResultsTests(unittest.TestCase):
    def test_complete_loads_continuation_state_fields_and_restored_checkpoint(self):
        rows, plan = json.loads((RUN/'results.json').read_text()), json.loads(PLAN.read_text())
        self.assertEqual(sha256((RUN/'results.json').read_bytes()),
                         '9b58e38eecc179a2bbae599736cf10c5eb3c3f0944910379d4dfaf6700c0d01e')
        self.assertEqual((len(rows), len(plan)), (106, 105))
        self.assertFalse(any('error' in r or r.get('assertion') == 'failed' for r in rows))
        calls = [r for r in rows if 'test_only_function_call' in r]
        reads = [r for r in rows if r.get('assertion') == 'passed']
        self.assertEqual((len(calls), len(reads)), (17, 51))
        for actual, expected in zip(calls, [r['call'] for r in plan if 'call' in r], strict=True):
            self.assertEqual(actual['test_only_function_call'], expected['address'])
            self.assertEqual(actual['arguments'], expected['arguments'])
            if 'expect_return' in expected:
                self.assertEqual(actual['return_value'], expected['expect_return'])
            self.assertTrue(actual['stack_restored'])
        for actual, expected in zip(reads, [r for r in plan if 'expect' in r], strict=True):
            self.assertEqual(actual['read'], expected['read'])
            self.assertEqual(actual['data'].lower(), expected['expect'].lower())
        self.assertEqual(sum(r['test_only_function_call'] == '8009E658' for r in calls), 2)
        self.assertEqual(sum(r['test_only_function_call'] == '800A04E4' for r in calls), 2)
        self.assertEqual(sum(r['read'] == ['8019B038', 318] for r in reads), 4)
        self.assertTrue(any(r.get('loaded_state') == 'test.bs1' for r in rows))
        self.assertEqual(reads[-1]['data'], bytes(4).hex()); self.assertTrue(rows[-1]['graceful_shutdown'])
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text())
        self.assertEqual(scenario(built, 'native_message_diagnostic', report['runtime_module']), plan)
        info = json.loads((RUN/'run.json').read_text())
        self.assertEqual(info['rom_sha256'], sha256(built))
        self.assertEqual(info['scenario_sha256'], sha256(PLAN.read_bytes()))
        self.assertEqual(info['scenario_sha256'], 'd6c069d399a3451d7f816d908ea7f7ded629f538c9af205de4182138b4a84f42')
        self.assertEqual(info['audio'], 'disabled'); self.assertEqual(info['seed_files'], [])
        for key in ('initial_screenshot', 'expansion_pak', 'allow_test_flash_write', 'allow_test_pak_write'):
            self.assertFalse(info[key])
        for name, digest in (
                ('test.bs1', '59a6a62c560aadf476d5a68165a9112bf8162c37aad3da81ec9d9976103af3b4'),
                ('test.flash', 'b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260'),
                ('test.pak', 'ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51')):
            self.assertEqual(sha256((RUN/name).read_bytes()), digest)


if __name__ == '__main__': unittest.main()
