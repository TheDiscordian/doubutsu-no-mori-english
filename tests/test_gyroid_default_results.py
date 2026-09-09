"""Frozen native gyroid acceptance evidence; never replay a completed batch."""

from collections import Counter
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
from gyroid_default_actor import RAM, SYMBOLS
from gyroid_default_scenario import scenario

RUN = ROOT/'build/smoke-gyroid-default-02'
BUILD = ROOT/'build/gyroid-default-pilot'
PLAN = ROOT/'build/gyroid-default-scenario.json'


@unittest.skipUnless((RUN/'results.json').is_file(), 'Completed native gyroid batch required')
class GyroidDefaultResultsTests(unittest.TestCase):
    def test_native_selector_all_homes_full_loads_and_restored_guards(self):
        rows = json.loads((RUN/'results.json').read_text()); plan = json.loads(PLAN.read_text())
        self.assertEqual(sha256((RUN/'results.json').read_bytes()),
                         '0f024263da89bf716dd1d96eb9a52b5ece519ab9408299a95ec5d79039719def')
        self.assertEqual((len(rows), len(plan)), (261, 8))
        self.assertFalse(any('error' in r or r.get('assertion') == 'failed' for r in rows))
        calls = [r for r in rows if 'test_only_function_call' in r]
        checks = [r for r in rows if r.get('assertion') == 'passed']
        self.assertEqual((len(calls), len(checks)), (112, 133))
        self.assertTrue(all(r['stack_restored'] for r in calls))
        base = next(r['return_value'] for r in calls if r['test_only_function_call'] == '8009BFC0')+16
        expected = {0x8009BFC0: 1, 0x800262D0: 1, 0x8009C0C0: 2, 0x8009C040: 1,
                    base+SYMBOLS['af_gyroid_default_select']: 73,
                    base+SYMBOLS['af_gyroid_default_demo']: 12,
                    base+0x8096B1A4-RAM: 8, base+0x8096B2D8-RAM: 8,
                    0x8009E558: 2, 0x800A21C0: 2, 0x8009E658: 2}
        self.assertEqual(Counter(int(r['test_only_function_call'], 16) for r in calls), expected)
        self.assertEqual([(r['gyroid_home'], r['default']) for r in rows if 'gyroid_home' in r],
                         [(home, default) for home in range(4) for default in (True, False)])
        for row in checks:
            if 'gyroid_check' in row:
                self.assertEqual(row['expected_sha256'], row['observed_sha256'])
        labels = Counter(r['gyroid_check'] for r in checks if 'gyroid_check' in r)
        self.assertEqual(labels['actual owner route preserves all saved bytes'], 8)
        self.assertEqual(labels['custom byte and source retained'], 64)
        self.assertEqual(labels['complete custom message still uses the native field'], 4)
        for label in ('complete cartridge-loaded actor', 'entire saved state restored',
                      'resident end guard', 'gyroid calls retain heap allocation'):
            self.assertEqual(labels[label], 1)
        summary, = [r for r in rows if 'gyroid_assertions' in r]
        self.assertEqual(summary['gyroid_assertions'], 132)
        self.assertEqual(summary['debugger_uploaded_production_bytes'], 0)
        for key in ('normal_interaction', 'editor_tested', 'game_save_validation', 'hardware_verified'):
            self.assertFalse(summary[key])
        self.assertTrue(any(r.get('loaded_state') == 'test.bs1' for r in rows))
        self.assertEqual(checks[-1]['data'], '00000000'); self.assertTrue(rows[-1]['graceful_shutdown'])
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text())
        self.assertEqual(scenario(native, built, report), plan)
        info = json.loads((RUN/'run.json').read_text())
        self.assertEqual(info['rom_sha256'], sha256(built))
        self.assertEqual(info['scenario_sha256'], sha256(PLAN.read_bytes()))
        self.assertEqual(info['scenario_sha256'], 'de92345355006f5673fd692acb0faa7f7c61ff84331e2154984f6a111b72015f')
        self.assertEqual(info['audio'], 'disabled'); self.assertEqual(info['seed_files'], [])
        for key in ('initial_screenshot', 'expansion_pak', 'allow_test_flash_write', 'allow_test_pak_write'):
            self.assertFalse(info[key])
        for name, digest in (
                ('test.bs1', '979e2a91b0e2085a234079aab8b6d51b56423db70451363fb2a5d1f3424879aa'),
                ('test.flash', 'b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260'),
                ('test.pak', 'ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51')):
            self.assertEqual(sha256((RUN/name).read_bytes()), digest)


if __name__ == '__main__': unittest.main()
