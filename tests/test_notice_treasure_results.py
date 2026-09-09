"""Retain completed native treasure evidence without replaying game calls."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
from notice_treasure_scenario import scenario

OWNER_DIGEST = '352d439d23a1fec0107fa0486bb3a00698d43d9011a1eba29379adccd156a3b7'
READER_DIGEST = 'adc8c1ad1ba716ba23b3b557316d4895dcb8bfa1b794490e581d79b1d798beef'
FAULTS = ('phase1_alloc', 'phase2_alloc', 'catalog', 'names', 'creator_crc', 'no_hole',
          'no_unit', 'early', 'recent', 'checked', 'unfamiliar')


@unittest.skipUnless((ROOT/'build/smoke-notice-treasure-05/results.json').is_file(),
                     'Local completed native treasure evidence required')
class TreasureOwnerResultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = ROOT/'build/smoke-notice-treasure-05'
        raw = (cls.directory/'results.json').read_bytes()
        if sha256(raw) != OWNER_DIGEST: raise ValueError('Changed frozen treasure owner evidence')
        cls.rows = json.loads(raw)

    def test_all_72_publications_match_complete_source_bound_records(self):
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        build = ROOT/'build/notice-treasure-pilot'
        built = (build/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((build/'build.json').read_text())
        plan = scenario(native, built, report)
        plan_raw = (ROOT/'build/noticeboard-treasure/native-scenario.json').read_bytes()
        self.assertEqual(json.loads(plan_raw), plan)
        info = json.loads((self.directory/'run.json').read_text())
        self.assertEqual(info['scenario_sha256'], sha256(plan_raw))
        self.assertEqual(info['rom_sha256'], sha256(built))
        self.assertEqual(info['audio'], 'disabled')
        self.assertEqual(info['seed_files'], [])
        for key in ('initial_screenshot', 'expansion_pak', 'allow_test_flash_write', 'allow_test_pak_write'):
            self.assertFalse(info[key])
        rows = [r for r in self.rows if 'native_treasure_complete' in r]
        cases = plan[3]['test_notice_treasure']['cases']
        self.assertEqual(len(rows), 72)
        for i, (row, case) in enumerate(zip(rows, cases)):
            self.assertEqual(row['native_treasure_complete'], i)
            for key in ('template', 'capital', 'item', 'hole', 'wire'):
                self.assertEqual(row[key], case[key])
            self.assertTrue(row['passed'])
        self.assertEqual({r['hole'] for r in rows if r['item'] == 0x2512}, set(range(25)))

    def test_original_burial_undo_and_actual_null_allocations_are_observed(self):
        faults = [r for r in self.rows if 'native_treasure_fault' in r]
        self.assertEqual(tuple(r['native_treasure_fault'] for r in faults), FAULTS)
        self.assertTrue(all(r['passed'] for r in faults))
        for name in ('phase1_alloc', 'phase2_alloc'):
            allocated = [r['treasure_native_malloc_return'] for r in self.rows
                         if 'treasure_native_malloc_return' in r and r['fault'] == name]
            self.assertEqual(allocated[-1], '00000000')
            self.assertTrue(all(value != '00000000' for value in allocated[:-1]))
        labels = {r.get('treasure_check') for r in self.rows}
        for label in ('actual native buried foreground', 'actual native buried flags',
                      'native stack-only undo', 'burial never publishes a partial post',
                      'only complete treasure publication changes save state',
                      'native RNG consumes the original draws', 'native treasure retains heap accounting',
                      'treasure fixture and stack guard', 'complete saved payload restored',
                      'treasure global restored'):
            self.assertIn(label, labels)
        self.assertEqual(len(self.rows), 2711)
        self.assertEqual(sum('test_only_function_call' in r for r in self.rows), 171)
        self.assertEqual(sum(r.get('assertion') == 'passed' for r in self.rows), 1829)
        self.assertFalse(any(r.get('assertion') == 'failed' for r in self.rows))

    def test_restoration_blank_saves_and_honest_execution_limits(self):
        summary = next(r for r in self.rows if 'native_treasure_cases' in r)
        self.assertEqual((summary['native_treasure_cases'], summary['native_treasure_faults'],
                          summary['treasure_assertions']), (72, 11, 1828))
        self.assertTrue(summary['actual_burial_and_publication'])
        self.assertTrue(summary['ordinary_item_substitution_at_original_call'])
        self.assertEqual(summary['debugger_uploaded_creator_bytes'], 0)
        for key in ('normal_random_furniture_selection', 'full_reader_executed', 'normal_gameplay',
                    'save_io_tested', 'hardware_verified'):
            self.assertFalse(summary[key])
        restored = next(i for i, r in enumerate(self.rows) if r.get('loaded_state') == 'test.bs1')
        self.assertTrue(any(r.get('read') == ['8019B000', 4] and r.get('data') == '00000000'
                            and r.get('assertion') == 'passed' for r in self.rows[restored+1:]))
        self.assertTrue(self.rows[-1]['graceful_shutdown'])
        for name, digest in (
            ('test.bs1', '441127269857d9a9aae3c03c3bf7e79133ececbf08557e098ef2eba43e48a368'),
            ('test.flash', 'b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260'),
            ('test.pak', 'ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51'),
        ):
            self.assertEqual(sha256((self.directory/name).read_bytes()), digest)


@unittest.skipUnless((ROOT/'build/smoke-notice-treasure-reader-01/results.json').is_file(),
                     'Local completed native treasure reader evidence required')
class TreasureReaderResultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = ROOT/'build/smoke-notice-treasure-reader-01'
        raw = (cls.directory/'results.json').read_bytes()
        if sha256(raw) != READER_DIGEST: raise ValueError('Changed frozen treasure reader evidence')
        cls.rows = json.loads(raw)

    def test_every_created_record_is_read_completely_with_native_glyph_positions(self):
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        build = ROOT/'build/notice-treasure-pilot'
        built = (build/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((build/'build.json').read_text())
        plan = scenario(native, built, report, reader_only=True)
        plan_raw = (ROOT/'build/noticeboard-treasure/native-reader-scenario.json').read_bytes()
        self.assertEqual(json.loads(plan_raw), plan)
        info = json.loads((self.directory/'run.json').read_text())
        self.assertEqual(info['scenario_sha256'], sha256(plan_raw))
        self.assertEqual(info['rom_sha256'], sha256(built))
        self.assertEqual(info['audio'], 'disabled')
        self.assertEqual(info['seed_files'], [])
        for key in ('initial_screenshot', 'expansion_pak', 'allow_test_flash_write', 'allow_test_pak_write'):
            self.assertFalse(info[key])
        creator_raw = (ROOT/'build/smoke-notice-treasure-05/results.json').read_bytes()
        self.assertEqual(sha256(creator_raw), OWNER_DIGEST)
        created = [r for r in json.loads(creator_raw) if 'native_treasure_complete' in r]
        complete = [r for r in self.rows if 'notice_treasure_body' in r]
        draws = [r for r in self.rows if r.get('notice_native_draw')]
        cases = plan[3]['test_notice_reader']['cases']
        self.assertEqual((len(created), len(complete), len(draws), len(cases)), (72,)*4)
        for before, after, draw, case in zip(created, complete, draws, cases):
            self.assertEqual(before['wire'], case['wire'])
            self.assertEqual(after['notice_treasure_body'], case['template'])
            self.assertEqual((after['capital'], after['item']), (case['capital'], case['item']))
            self.assertTrue(after['passed'])
            # These real-name fixtures fit one page. Manual blank rows produce
            # no glyph call; joining preserves every actual displayed character.
            rendered = b''.join(bytes.fromhex(line['text']) for line in draw['lines'])
            self.assertEqual(rendered, bytes.fromhex(case['body']).replace(b'\xcd', b''))
        self.assertEqual(sum(r['glyphs_verified'] for r in draws), 9148)
        self.assertEqual(sum(r['vertex_positions_verified'] for r in draws), 36592)

    def test_owner_cleanup_restores_checkpoint_without_replaying_initial_bodies(self):
        self.assertEqual(len(self.rows), 720)
        self.assertEqual(sum('test_only_function_call' in r for r in self.rows), 157)
        self.assertEqual(sum(r.get('assertion') == 'passed' for r in self.rows), 410)
        self.assertFalse(any(r.get('assertion') == 'failed' for r in self.rows))
        self.assertFalse(any('notice_initial_body' in r or 'notice_native_page_control' in r for r in self.rows))
        summary = next(r for r in self.rows if 'notice_reader_assertions' in r)
        self.assertEqual((summary['notice_initial_bodies'], summary['notice_treasure_bodies'],
                          summary['notice_native_draws'], summary['notice_reader_assertions']), (0, 72, 72, 409))
        self.assertTrue(summary['actual_owner_loader'])
        self.assertEqual(summary['debugger_uploaded_reader_bytes'], 0)
        for key in ('normal_submenu_initialization', 'save_io_tested', 'hardware_verified'):
            self.assertFalse(summary[key])
        labels = {r.get('notice_reader_check') for r in self.rows}
        for label in ('native destructor releases notice ownership', 'complete batch retains heap accounting',
                      'fixture and stack guard', 'complete saved payload restored', 'native global or input restored'):
            self.assertIn(label, labels)
        restored = next(i for i, r in enumerate(self.rows) if r.get('loaded_state') == 'test.bs1')
        self.assertTrue(any(r.get('read') == ['8019B000', 4] and r.get('data') == '00000000'
                            and r.get('assertion') == 'passed' for r in self.rows[restored+1:]))
        self.assertTrue(self.rows[-1]['graceful_shutdown'])
        for name, digest in (
            ('test.bs1', '09c837cabb70d93a0c81e3808336fe7aee22c265a5eeccf3a5a67cde494ae6d9'),
            ('test.flash', 'b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260'),
            ('test.pak', 'ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51'),
        ):
            self.assertEqual(sha256((self.directory/name).read_bytes()), digest)


if __name__ == '__main__': unittest.main()
