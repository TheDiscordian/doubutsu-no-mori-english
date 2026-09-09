"""Frozen complete design-name and ordinary-word native evidence."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256

RUN = ROOT/'build/smoke-design-items-02'
BUILD = ROOT/'build/design-items-pilot'
PLAN = ROOT/'build/design-items-scenario.json'


@unittest.skipUnless((RUN/'results.json').is_file(), 'Completed native design-name evidence required')
class DesignItemResultsTests(unittest.TestCase):
    def test_all_calls_complete_buffers_guards_checkpoint_and_isolated_saves(self):
        raw = (RUN/'results.json').read_bytes()
        self.assertEqual(sha256(raw), '7e0e767b69e44090b9bae4700d2d890d98c4bd983d65b911875fd1d618f3310f')
        rows, plan = json.loads(raw), json.loads(PLAN.read_text())
        self.assertEqual((len(plan), len(rows)), (410, 411))
        self.assertFalse(any('error' in r or r.get('assertion') == 'failed' for r in rows))
        calls = [r for r in rows if 'test_only_function_call' in r]
        self.assertEqual(len(calls), 137)
        for actual, expected in zip(calls, [r['call'] for r in plan if 'call' in r], strict=True):
            self.assertEqual(actual['test_only_function_call'], expected['address'])
            self.assertEqual(actual['arguments'], expected['arguments'])
            self.assertTrue(actual['stack_restored'])
            if 'expect_return' in expected: self.assertEqual(actual['return_value'], expected['expect_return'])
        reads = [r for r in rows if r.get('assertion') == 'passed']
        self.assertEqual(len(reads), 129)
        for actual, expected in zip(reads, [r for r in plan if 'expect' in r], strict=True):
            self.assertEqual(actual['read'], expected['read'])
            self.assertEqual(actual['data'].lower(), expected['expect'].lower())
        self.assertEqual(calls[-1]['test_only_function_call'], '800C3F70')
        words = [r for r in reads if r['read'] == ['8019B000', 48]]
        self.assertEqual(len(words), 1)
        self.assertEqual(words[0]['data'], (b'G'*16+b'herabuna        '+b'G'*16).hex())
        info = json.loads((RUN/'run.json').read_text())
        self.assertEqual(info['rom_sha256'], sha256((BUILD/'animal-forest-halfwidth.z64').read_bytes()))
        self.assertEqual(info['scenario_sha256'], sha256(PLAN.read_bytes()))
        self.assertEqual(info['scenario_sha256'], '5c4aceee50b538a5709adc004fd94d2dcdedff2da77a44c130269bfacad60edf')
        self.assertEqual(info['audio'], 'disabled'); self.assertEqual(info['seed_files'], [])
        for key in ('initial_screenshot', 'expansion_pak', 'allow_test_flash_write', 'allow_test_pak_write'):
            self.assertFalse(info[key])
        restored = max(i for i, r in enumerate(rows) if r.get('loaded_state') == 'test.bs1')
        self.assertTrue(any(r.get('read') == ['8019B000', 4] and r.get('data') == '00000000'
                            and r.get('assertion') == 'passed' for r in rows[restored+1:]))
        self.assertTrue(rows[-1]['graceful_shutdown'])
        for name, digest in (
                ('test.bs1', '49311d1f879cd8232efa9508f900a2d9faedcfaae029279a033ee62a28f872d8'),
                ('test.flash', 'b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260'),
                ('test.pak', 'ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51')):
            self.assertEqual(sha256((RUN/name).read_bytes()), digest)


if __name__ == '__main__': unittest.main()
