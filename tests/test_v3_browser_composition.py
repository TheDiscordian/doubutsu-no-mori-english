"""Generated selection plan and browser/offline equivalence on the current build."""
import copy
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
import v3_optional_composition as composer
import v3_browser_composition as browser


class BrowserCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base, cls.report = composer.inputs()
        cls.catalog = composer.catalogue(cls.base, cls.report)
        cls.plan = browser.rules(cls.base, cls.report)

    def test_installed_records_generate_the_entire_browser_menu_and_dependencies(self):
        self.assertEqual([row['id'] for row in self.plan['options']], list(self.catalog))
        self.assertEqual(self.plan['runtime_abi'], self.report['runtime_abi'])
        for row in self.plan['options']:
            original = self.catalog[row['id']]
            for key in ('name', 'kind', 'dependencies'):
                self.assertEqual(row[key], original[key])
        self.assertFalse(self.plan['web_patcher_enabled'])
        self.assertEqual(self.plan['profile']['before'], self.report['save_runtime']['profile_hex'])

    def test_changed_pins_or_report_reject_before_export(self):
        damaged = bytearray(self.base); damaged[-1] ^= 1
        with self.assertRaisesRegex(ValueError, 'pinned'):
            browser.rules(damaged, self.report)
        changed = copy.deepcopy(self.report); changed['runtime_abi'] += 1
        with self.assertRaisesRegex(ValueError, 'pinned'):
            browser.rules(self.base, changed)
        with self.assertRaisesRegex(ValueError, 'fresh ignored'):
            browser.build(ROOT/'web')
        with self.assertRaisesRegex(ValueError, 'fresh ignored'):
            browser.build(composer.BASE)

    def test_browser_output_matches_authoritative_composition_for_representative_profiles(self):
        keys = list(self.catalog)
        grouped = {kind: [key for key, row in self.catalog.items() if row['kind'] == kind]
                   for kind in ('furniture', 'clothing', 'villager')}
        # These cases exercise shared selection structures, not one test per
        # donor item. Reward categories use the same generated enable records.
        profiles = [
            ('empty', []), ('all', keys), ('villagers', grouped['villager']),
            ('furniture', grouped['furniture']), ('shirts', grouped['clothing']),
            ('dependent-villager', ['GAFE01-r0/villager/00EB']),
            ('two-house-items', ['GAFE01-r0/villager/00E8']),
            ('last-shirt-and-camping', ['GAFE01-r0/item/241B', 'GAFE01-r0/item/31D4']),
            ('sparse-categories', ['GAFE01-r0/item/31A8', 'GAFE01-r0/item/31E0', 'GAFE01-r0/item/322C']),
            ('mixed', random.Random(93).sample(keys, 17)),
        ]
        cases = []
        for name, requested in profiles:
            selection = composer.resolve(self.catalog, requested)
            result, _, _ = composer.compose(self.base, self.report, self.catalog, selection)
            cases.append({'name': name, 'requested': requested, 'selection': selection, 'sha256': sha256(result)})
        cases.append({**cases[-1], 'name': 'order-and-duplicates',
                      'requested': list(reversed(cases[-1]['requested'])) + cases[-1]['requested'][:2]})
        with tempfile.TemporaryDirectory(prefix='v3-browser-equivalence-') as directory:
            path = Path(directory)/'fixture.json'
            path.write_bytes(composer.canonical({'plan': self.plan, 'cases': cases,
                'base': str(composer.BASE/'animal-forest-v3-asset-loader.z64'), 'stable': str(composer.STABLE)}))
            result = subprocess.run(['node', '--experimental-global-webcrypto',
                str(ROOT/'tests/v3_browser_equivalence.mjs'), str(path)], check=True,
                capture_output=True, text=True, timeout=90)
        self.assertEqual(len(json.loads(result.stdout)['passed']), len(cases))


if __name__ == '__main__':
    unittest.main()
