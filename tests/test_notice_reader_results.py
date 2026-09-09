"""Keep native board evidence without replaying completed body and edge batches."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
from notice_reader_scenario import scenario

RUNS = {
    2: ('0944c4332de9155cf30bb13df97c7e71d9238874ebc915d414e4387abcbcf285', 38, 10, 21),
    3: ('36f0d17f36017fbacb6edeb72685a2be6d0a2127cb701b16340d1099ffe27834', 129, 30, 74),
    4: ('0424b85d56bbc0aa928201c06fcf574672e6043b9f405c361c9d22513c554618', 137, 40, 65),
}


@unittest.skipUnless((ROOT/'build/smoke-notice-reader-04/results.json').is_file(),
                     'Local native notice reader evidence required')
class NoticeReaderResultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = {}
        for number, (digest, count, calls, checks) in RUNS.items():
            raw = (ROOT/f'build/smoke-notice-reader-{number:02d}/results.json').read_bytes()
            if sha256(raw) != digest: raise ValueError('Changed frozen native notice evidence')
            cls.rows[number] = json.loads(raw)

    def test_all_eight_complete_bodies_and_33_native_draws(self):
        rows = sum(self.rows.values(), [])
        completed = [r for r in rows if 'notice_initial_body' in r]
        self.assertEqual([(r['notice_initial_body'], r['capital']) for r in completed],
                         [(number, capital) for number in range(0x1E, 0x22) for capital in (0, 1)])
        self.assertTrue(all(r['passed'] for r in completed))
        draws = [r for r in rows if r.get('notice_native_draw')]
        self.assertEqual(len(draws), 33)
        self.assertEqual(sum(r['glyphs_verified'] for r in draws), 2210)
        self.assertEqual(sum(r['vertex_positions_verified'] for r in draws), 8840)
        for number, (_, count, calls, checks) in RUNS.items():
            batch = self.rows[number]
            self.assertEqual(len(batch), count)
            self.assertEqual(sum('test_only_function_call' in r for r in batch), calls)
            self.assertEqual(sum(r.get('assertion') == 'passed' for r in batch), checks)
            self.assertFalse(any(r.get('assertion') == 'failed' for r in batch))
        # Partial runs stop on fixture assertions, not complete acceptance.
        self.assertFalse(any(r.get('graceful_shutdown') for r in self.rows[2]))
        self.assertFalse(any(r.get('graceful_shutdown') for r in self.rows[3]))
        for number, label in ((2, 'Missing or duplicate notice cache owner'),
                              (3, 'expected 0')):
            name = 'native-reader-retry.log' if number == 2 else 'native-reader-resume.log'
            self.assertIn(label, (ROOT/'build/noticeboard-reader'/name).read_text())

    def test_final_edges_controls_labels_cleanup_and_blank_saves(self):
        rows = self.rows[4]
        controls = [r for r in rows if 'notice_native_page_control' in r]
        self.assertEqual([(r['notice_native_page_control'], r['page']) for r in controls],
                         [(0x10, 1), (0x10, 1), (0x20, 0), (0x30, 0)])
        draw_lines = [line for r in rows if r.get('notice_native_draw') for line in r['lines']]
        for month in 'January February March April May June July August September October November December'.split():
            text = f'{month} 31, 2001'.encode().hex()
            self.assertEqual(sum(line['text'] == text for line in draw_lines), 1)
        summary = next(r for r in rows if 'notice_reader_assertions' in r)
        self.assertEqual((summary['notice_initial_bodies'], summary['notice_native_draws'],
                          summary['notice_reader_assertions']), (0, 19, 64))
        self.assertTrue(summary['actual_owner_loader'])
        for key in ('normal_submenu_initialization', 'save_io_tested', 'hardware_verified'):
            self.assertFalse(summary[key])
        self.assertEqual(summary['debugger_uploaded_reader_bytes'], 0)
        labels = {r.get('notice_reader_check') for r in rows}
        for label in ('complete batch retains heap accounting', 'fixture and stack guard',
                      'complete saved payload restored', 'native global or input restored',
                      'native destructor releases notice ownership'):
            self.assertIn(label, labels)
        restored = next(i for i, r in enumerate(rows) if r.get('loaded_state') == 'test.bs1')
        self.assertTrue(any(r.get('read') == ['8019B000', 4] and r.get('data') == '00000000'
                            and r.get('assertion') == 'passed' for r in rows[restored+1:]))
        self.assertTrue(rows[-1]['graceful_shutdown'])
        directory = ROOT/'build/smoke-notice-reader-04'
        for name, digest in (
            ('test.bs1', '71ca08c9264340b24a97adc19139168507650be0c017ebfb0ebacb1b4124644b'),
            ('test.flash', 'b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260'),
            ('test.pak', 'ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51'),
        ):
            self.assertEqual(sha256((directory/name).read_bytes()), digest)

    def test_completed_edge_plan_still_binds_the_installed_cartridge(self):
        build = ROOT/'build/noticeboard-pilot'
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        built = (build/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((build/'build.json').read_text())
        plan_raw = (ROOT/'build/noticeboard-reader/reader-edges-scenario.json').read_bytes()
        self.assertEqual(sha256(plan_raw), 'beca0a3527c5fc9178f29546d4fc8441a258ebcfab9f477060b193a571df037c')
        self.assertEqual(json.loads(plan_raw), scenario(native, built, report, skip_initial=8, edges_only=True))
        info = json.loads((ROOT/'build/smoke-notice-reader-04/run.json').read_text())
        self.assertEqual(info['scenario_sha256'], sha256(plan_raw))
        self.assertEqual(info['rom_sha256'], sha256(built))
        self.assertEqual(info['audio'], 'disabled')
        self.assertEqual(info['seed_files'], [])
        for key in ('initial_screenshot', 'expansion_pak', 'allow_test_flash_write', 'allow_test_pak_write'):
            self.assertFalse(info[key])

    def test_reject_invalid_continuation_before_reading_sources(self):
        for value in (-1, 9, True, 1.5):
            with self.assertRaises(ValueError): scenario(b'', b'', {}, skip_initial=value)
        with self.assertRaises(ValueError): scenario(b'', b'', {}, edges_only=True)


if __name__ == '__main__': unittest.main()
