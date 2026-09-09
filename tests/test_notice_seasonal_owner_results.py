"""Retain native seasonal publication evidence without replaying game calls."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
from mail_record import Field, Record
from notice_record import pack, unpack
from notice_seasonal import complete_body
from notice_seasonal_scenario import scenario

DIRECTORY = ROOT/'build/smoke-notice-seasonal-owner-01'
RESULTS = '17941ccc6c0e645412958fdeeec97fe425c3562a06992d94fa4c75330052bc96'
PLAN = '170cf2d074294519048b732d1dda43c4debe7cda180b0286904ac3d2ecf773a4'


@unittest.skipUnless((DIRECTORY/'results.json').is_file(), 'Completed local seasonal owner evidence required')
class SeasonalOwnerResultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = (DIRECTORY/'results.json').read_bytes()
        if sha256(raw) != RESULTS: raise ValueError('Changed frozen seasonal owner results')
        cls.rows = json.loads(raw)
        raw = (ROOT/'build/noticeboard-seasonal/native-owner-scenario.json').read_bytes()
        if sha256(raw) != PLAN: raise ValueError('Changed seasonal owner scenario')
        cls.plan = json.loads(raw)

    def test_complete_native_records_capture_actual_calendar_shop_and_town(self):
        request = self.plan[3]['test_notice_seasonal']
        templates = {entry['template']: entry for entry in request['templates']}
        calendars = [r for r in self.rows if 'seasonal_native_calendar' in r]
        self.assertEqual([(r['seasonal_native_calendar'], r['field'], r['converted'], r['native_output'])
                          for r in calendars], [(2001, 2, 1, '07d10a01'), (2001, 3, 1, '07d10a1d')])
        week = next(r for r in self.rows if r.get('test_only_function_call') == '800D5CF8')
        self.assertEqual((week['arguments'], week['return_value']), ([2001, 10, 14], 0))
        fields = {0: b'TownXX', 1: bytes.fromhex(request['shops'][3]),
                  2: b'October 1st', 3: b'October 29th', 4: b'October 8th'}
        rows = [r for r in self.rows if 'native_seasonal_complete' in r]
        self.assertEqual([(r['template'], r['capital']) for r in rows],
                         [(number, capital) for number in range(0x1A4, 0x1CB) for capital in (0, 1)])
        for row in rows:
            entry = templates[row['template']]
            expected = Record(4, 0, (row['template'],),
                              tuple((i, Field(fields[i])) for i in entry['fields']), bool(row['capital']))
            self.assertEqual(row['native_seasonal_complete'], row['template']-0x1A4)
            self.assertEqual(bytes.fromhex(row['wire']), pack(expected))
            self.assertEqual(complete_body(unpack(bytes.fromhex(row['wire']), expected_catalog=4), entry),
                             complete_body(expected, entry))
            self.assertTrue(row['passed'])
        direct = [r for r in self.rows if 'native_seasonal_direct' in r]
        self.assertEqual([(r['native_seasonal_direct'], r['capital']) for r in direct],
                         [(number, capital) for number in (0x1CB, 0x1CC) for capital in (0, 1)])
        self.assertTrue(all(r['passed'] for r in direct))

    def test_each_failed_backlog_position_preserves_prefix_then_retries_suffix(self):
        faults = [r for r in self.rows if 'native_seasonal_pending_failure' in r]
        self.assertEqual([r['native_seasonal_pending_failure'] for r in faults], list(range(5)))
        self.assertTrue(all(r['passed'] and r['retry_completed'] for r in faults))
        for label, count in (
            ('native pending list chooses the expected next ID', 15),
            ('only complete board posts and native checked time change saved payload', 88),
            ('pending common cursor advances only through published prefix', 88),
            ('native free fields remain unchanged', 88),
            ('creator session detaches', 88), ('seasonal creator releases allocation', 88),
            ('unscheduled complete creator output', 4),
            ('direct creation does not publish a fictitious event', 4),
        ):
            rows = [r for r in self.rows if r.get('seasonal_check') == label]
            self.assertEqual(len(rows), count, label)
            self.assertTrue(all(r['expected_sha256'] == r['observed_sha256'] for r in rows), label)

    def test_all_assertions_cleanup_and_execution_limits(self):
        self.assertEqual(len(self.rows), 999)
        self.assertEqual(sum('test_only_function_call' in r for r in self.rows), 359)
        self.assertEqual(sum(r.get('assertion') == 'passed' for r in self.rows), 513)
        self.assertFalse(any(r.get('assertion') == 'failed' for r in self.rows))
        summary = next(r for r in self.rows if 'native_seasonal_cases' in r)
        self.assertEqual((summary['native_seasonal_cases'], summary['native_seasonal_direct_cases'],
                          summary['native_seasonal_prefix_failures'], summary['seasonal_assertions']),
                         (78, 4, 5, 512))
        self.assertTrue(summary['actual_calendar_and_scheduler'])
        self.assertEqual(summary['debugger_uploaded_creator_bytes'], 0)
        for key in ('pending_retry_across_save', 'full_reader_executed', 'normal_gameplay',
                    'save_io_tested', 'hardware_verified'):
            self.assertFalse(summary[key])
        labels = {r.get('seasonal_check') for r in self.rows}
        for label in ('seasonal code retained after batch', 'seasonal scratch and stack guard',
                      'resident module guard', 'complete saved payload restored', 'seasonal global restored'):
            self.assertIn(label, labels)
        restored = next(i for i, r in enumerate(self.rows) if r.get('loaded_state') == 'test.bs1')
        self.assertTrue(any(r.get('read') == ['8019B000', 4] and r.get('data') == '00000000'
                            and r.get('assertion') == 'passed' for r in self.rows[restored+1:]))
        self.assertTrue(self.rows[-1]['graceful_shutdown'])
        for name, digest in (
            ('test.bs1', '3f739ca7f557a3314c6c8a3ed07050a40baf4b4a42612a1de3f8ee7aadd6156a'),
            ('test.flash', 'b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260'),
            ('test.pak', 'ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51'),
        ):
            self.assertEqual(sha256((DIRECTORY/name).read_bytes()), digest)

    def test_source_bound_plan_and_silent_isolated_run(self):
        directory = ROOT/'build/notice-seasonal-pilot'
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        built = (directory/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((directory/'build.json').read_text())
        self.assertEqual(self.plan, json.loads(json.dumps(scenario(native, built, report))))
        info = json.loads((DIRECTORY/'run.json').read_text())
        self.assertEqual(info['rom_sha256'], sha256(built))
        self.assertEqual(info['scenario_sha256'], PLAN)
        self.assertEqual(info['audio'], 'disabled')
        self.assertEqual(info['seed_files'], [])
        for key in ('initial_screenshot', 'expansion_pak', 'allow_test_flash_write', 'allow_test_pak_write'):
            self.assertFalse(info[key])


if __name__ == '__main__': unittest.main()
