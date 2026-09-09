"""Retain complete native seasonal reading without replaying the emulator batch."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
from notice_seasonal_reader_scenario import scenario

DIRECTORY = ROOT/'build/smoke-notice-seasonal-reader-01'
RESULTS = '99ff132454c32a72b7c1f1a92d54fa731d689fc3712cf2d93e2391ba21d94687'
PLAN = '05f816f7aad1c4a4fa9fb079a8f944fb250d5ee80d180fee95a129e916d9bd4c'


@unittest.skipUnless((DIRECTORY/'results.json').is_file(), 'Completed local seasonal reader evidence required')
class SeasonalReaderResultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = (DIRECTORY/'results.json').read_bytes()
        if sha256(raw) != RESULTS: raise ValueError('Changed frozen seasonal reader results')
        cls.rows = json.loads(raw)
        plan = (ROOT/'build/noticeboard-seasonal/native-reader-scenario.json').read_bytes()
        if sha256(plan) != PLAN: raise ValueError('Changed seasonal reader scenario')
        cls.plan = json.loads(plan)

    def test_every_complete_body_capital_and_continuation_page_reaches_native_glyphs(self):
        cases = iter(self.plan[3]['test_notice_reader']['cases'])
        text = b''
        completed = []
        pages = 0
        for row in self.rows:
            if row.get('notice_native_draw'):
                for line in row['lines']:
                    if line['scale'] == 1: text += bytes.fromhex(line['text'])
                    elif bytes.fromhex(line['text']).startswith(b'L/R: page 2/'):
                        pages += 1
            if 'notice_seasonal_body' in row:
                case = next(cases)
                self.assertEqual((row['notice_seasonal_body'], row['capital']), (case['template'], case['capital']))
                self.assertTrue(row['passed'])
                self.assertEqual(text, bytes.fromhex(case['body']).replace(b'\xCD', b''))
                text = b''
                completed.append((case['template'], case['capital']))
        self.assertIsNone(next(cases, None))
        self.assertEqual(completed, [(number, capital) for number in range(0x1A4, 0x1CD) for capital in (0, 1)])
        self.assertEqual(pages, 2)
        draws = [row for row in self.rows if row.get('notice_native_draw')]
        self.assertEqual(len(draws), 84)
        self.assertEqual(sum(row['glyphs_verified'] for row in draws), 11930)
        self.assertEqual(sum(row['vertex_positions_verified'] for row in draws), 47720)
        self.assertFalse(any('notice_initial_body' in row or 'notice_treasure_body' in row for row in self.rows))

    def test_all_calls_assertions_restoration_and_blank_isolated_saves(self):
        self.assertEqual(len(self.rows), 824)
        self.assertEqual(sum('test_only_function_call' in row for row in self.rows), 183)
        self.assertEqual(sum(row.get('assertion') == 'passed' for row in self.rows), 466)
        self.assertFalse(any(row.get('assertion') == 'failed' for row in self.rows))
        summary = next(row for row in self.rows if 'notice_reader_assertions' in row)
        self.assertEqual((summary['notice_seasonal_bodies'], summary['notice_reader_assertions']), (82, 465))
        self.assertTrue(summary['actual_owner_loader'])
        self.assertEqual(summary['debugger_uploaded_reader_bytes'], 0)
        for key in ('normal_submenu_initialization', 'save_io_tested', 'hardware_verified'):
            self.assertFalse(summary[key])
        labels = {row.get('notice_reader_check') for row in self.rows}
        for label in ('native linked allocation advances by complete aligned size',
                      'native destructor releases notice ownership', 'complete batch retains heap accounting',
                      'fixture and stack guard', 'complete saved payload restored', 'native global or input restored'):
            self.assertIn(label, labels)
        restored = next(i for i, row in enumerate(self.rows) if row.get('loaded_state') == 'test.bs1')
        self.assertTrue(any(row.get('read') == ['8019B000', 4] and row.get('data') == '00000000'
                            and row.get('assertion') == 'passed' for row in self.rows[restored+1:]))
        self.assertTrue(self.rows[-1]['graceful_shutdown'])
        for name, digest in (
            ('test.bs1', '07fdc7af40011006cfa1ebd3f1fb52dc1d4b5cbaf278542e0447d90f5816909c'),
            ('test.flash', 'b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260'),
            ('test.pak', 'ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51')):
            self.assertEqual(sha256((DIRECTORY/name).read_bytes()), digest)

    def test_frozen_plan_binds_actual_installed_rom_and_silent_scope(self):
        directory = ROOT/'build/notice-seasonal-pilot'
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        built = (directory/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((directory/'build.json').read_text())
        self.assertEqual(self.plan, scenario(native, built, report))
        info = json.loads((DIRECTORY/'run.json').read_text())
        self.assertEqual(info['rom_sha256'], sha256(built)); self.assertEqual(info['scenario_sha256'], PLAN)
        self.assertEqual(info['audio'], 'disabled'); self.assertEqual(info['seed_files'], [])
        for key in ('initial_screenshot', 'expansion_pak', 'allow_test_flash_write', 'allow_test_pak_write'):
            self.assertFalse(info[key])

    def test_invalid_continuation_is_rejected_before_sources(self):
        for value in (-1, 83, True, 1.5):
            with self.assertRaises(ValueError): scenario(b'', b'', {}, skip_complete=value)


if __name__ == '__main__': unittest.main()
