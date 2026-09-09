"""Check the frozen native storage batch without replaying passed game calls."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
from notice_storage_scenario import scenario

RUN = ROOT/'build/smoke-notice-storage-01'
BUILD = ROOT/'build/noticeboard-pilot'


@unittest.skipUnless((RUN/'results.json').is_file(), 'Completed local native notice batch required')
class NoticeStorageResultsTests(unittest.TestCase):
    def test_full_plan_native_calls_buffers_guards_and_restored_checkpoint(self):
        raw = (RUN/'results.json').read_bytes()
        self.assertEqual(sha256(raw), 'a177ce2031976e8cfae29398a722097c11d726c7b11442bab3a4f84fc5abe7a4')
        rows = json.loads(raw)
        info = json.loads((RUN/'run.json').read_text())
        plan_bytes = (ROOT/'build/noticeboard-reader/storage-scenario.json').read_bytes()
        self.assertEqual(sha256(plan_bytes), '54c616411ab15ead83eebfecd0b797824216d8197d187bdef7b15048106db9eb')
        plan = json.loads(plan_bytes)
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        self.assertEqual(plan, scenario((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(), built,
                                       json.loads((BUILD/'build.json').read_text())))
        self.assertEqual((len(rows), len(plan)), (112, 111))
        self.assertFalse(any('error' in r or r.get('assertion') == 'failed' for r in rows))
        calls = [r for r in rows if 'test_only_function_call' in r]
        reads = [r for r in rows if r.get('assertion') == 'passed']
        self.assertEqual((len(calls), len(reads)), (36, 46))
        for actual, expected in zip(calls, [a['call'] for a in plan if 'call' in a], strict=True):
            self.assertEqual(actual['test_only_function_call'], expected['address'])
            self.assertEqual(actual['arguments'], expected['arguments'])
            self.assertTrue(actual['stack_restored'])
            if 'expect_return' in expected: self.assertEqual(actual['return_value'], expected['expect_return'])
        for actual, expected in zip(reads, [a for a in plan if 'expect' in a], strict=True):
            self.assertEqual(actual['read'], expected['read'])
            self.assertEqual(actual['data'].lower(), expected['expect'].lower())
        self.assertEqual(info['rom_sha256'], sha256(built))
        self.assertEqual(info['scenario_sha256'], sha256(plan_bytes))
        self.assertEqual(info['audio'], 'disabled')
        self.assertEqual(info['seed_files'], [])
        for key in ('initial_screenshot', 'expansion_pak', 'allow_test_flash_write', 'allow_test_pak_write'):
            self.assertFalse(info[key])
        restored = max(i for i, row in enumerate(rows) if row.get('loaded_state') == 'test.bs1')
        self.assertTrue(any(r.get('read') == ['8019B000', 4] and r.get('data') == '00000000'
                            and r.get('assertion') == 'passed' for r in rows[restored+1:]))
        self.assertTrue(rows[-1]['graceful_shutdown'])
        for name, digest in (
            ('test.bs1', '2b6c081991096f407d4d2e92717857c1d29de1af6c455d81b9dd5e0f8a646ae1'),
            ('test.flash', 'b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260'),
            ('test.pak', 'ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51'),
        ):
            self.assertEqual(sha256((RUN/name).read_bytes()), digest)


if __name__ == '__main__': unittest.main()
