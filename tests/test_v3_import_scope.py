"""Current-cartridge V3 regular-pool selection and browser/offline equivalence."""
import copy
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
import v3_optional_composition as composer
import v3_browser_composition as browser
from v3_creature_choices import options as behaviour_options
from v3_holiday_selection import groups
from v3_import_scope import PIPELINE, FEATURE_CHOICES, availability, requested_options

LOCK = ROOT/os.environ.get('V3_IMPORT_SCOPE_LOCK', 'build/v3-post-office-bank-installed-05/build-lock.json')


class ImportScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous = (composer.BASE, composer.BASE_SHA, composer.REPORT_SHA, composer.ABI)
        composer.use_build_lock(LOCK)
        cls.image, cls.report = composer.inputs()
        cls.catalog = composer.catalogue(cls.image, cls.report)
        cls.states = availability(cls.catalog, cls.report)
        cls.choices = behaviour_options(cls.image, cls.report)
        cls.plan = browser.rules(cls.image, cls.report, scope=PIPELINE)

    @classmethod
    def tearDownClass(cls):
        composer.BASE, composer.BASE_SHA, composer.REPORT_SHA, composer.ABI = cls.previous

    def select(self, requested, behaviours=None):
        return composer.resolve(self.catalog, requested, scope=PIPELINE, report=self.report,
                                behaviour_options=self.choices, behaviours=behaviours)

    def test_regular_choices_follow_actual_installed_pools_and_all_villagers_remain(self):
        offered = requested_options(self.catalog, self.report)
        self.assertEqual(sum(self.catalog[k]['kind'] == 'villager' for k in offered), 20)
        pool = {r['item_id'] for r in self.report['shops']['imports'] if r['group'] in (0, 1, 2, 5)}
        self.assertEqual({r['item_id'] for k,r in self.catalog.items()
                          if r['kind'] == 'furniture' and k in offered},
                         pool & {r['item_id'] for r in self.catalog.values() if r['kind'] == 'furniture'})
        self.assertEqual([r['id'] for r in self.plan['options'] if not r.get('dependency_only')], offered)
        self.assertTrue(all(g['forced_disabled'] for g in self.plan['runtime_groups']))
        self.assertEqual({r['id'] for r in self.plan['behaviours'] if r.get('v4_only')}, FEATURE_CHOICES)
        self.assertTrue(all(not r['selectable'] and r['reason'] for r in self.plan['pending_options']))

    def test_existing_lottery_rewards_are_selectable_without_new_event_providers(self):
        by_item = {row['item_id']:key for key,row in self.catalog.items() if row['kind']=='furniture'}
        lottery = [by_item[row['item_id']] for row in self.report['shops']['imports'] if row['group']==5]
        self.assertEqual(len(lottery),7)
        self.assertIn('GAFE01-r0/item/1DDC',lottery)  # Excitebike's real lottery route.
        self.assertTrue(all(self.states[key]['selectable'] for key in lottery))
        selection=self.select(lottery)
        self.assertEqual(set(selection['requested']),set(lottery))
        self.assertTrue(all(group['forced_disabled'] for group in self.plan['runtime_groups']))
        self.assertTrue(all('deferred to V4' not in state['reason'] for state in self.states.values()))

    def test_special_items_and_feature_settings_reject_before_composition(self):
        rejected = [k for k,s in self.states.items() if not s['selectable']]
        self.assertIn('GAFE01-r0/item/3294', rejected)  # Savings mailbox, not regular stock.
        self.assertIn('GAFE01-r0/item/2530', rejected)  # Harvest cutlery.
        self.assertIn('GAFE01-r0/item/2239', rejected)  # Golden axe.
        for key in rejected:
            with self.assertRaisesRegex(ValueError, 'Unavailable standalone'):
                self.select([key])
        for key in FEATURE_CHOICES:
            with self.assertRaisesRegex(ValueError, 'outside the V3'):
                self.select([], {key:'GameCube'})
        with self.assertRaisesRegex(ValueError, 'Unknown import scope'):
            composer.resolve(self.catalog, [], scope='unrestricted-v3', report=self.report)

    def test_exclusive_outfits_are_only_resources_of_the_selected_villager(self):
        villagers = [k for k,r in self.catalog.items() if r['kind'] == 'villager']
        selected = self.select(villagers)
        resources = {k for k,s in self.states.items() if s['dependency_only']}
        self.assertEqual(len(resources), 2)
        self.assertLessEqual(resources, set(selected['required']))
        self.assertTrue(resources.isdisjoint(selected['requested']))
        self.assertTrue(all(self.catalog[k]['kind'] == 'clothing' for k in resources))

    def test_scope_disables_new_feature_groups_even_for_diaries_and_preserves_source(self):
        requested = requested_options(self.catalog, self.report)
        result, writes, blob = composer.compose(self.image, self.report, self.catalog, self.select(requested))
        self.assertIsNotNone(blob)
        for group in groups(self.image, self.report):
            for field in group['fields']:
                self.assertEqual(struct.unpack_from('>I', result, field['offset'])[0], field['disabled'])
        restored = composer.apply_writes(result, [{**r,'before':r['after'],'after':r['before']} for r in writes])
        self.assertEqual(restored, self.image)
        self.assertEqual(sha256(result), self.plan['all_selected_sha256'])
        changed = copy.deepcopy(self.select(requested))
        changed['behaviours']['birthday-presentation'] = 'GameCube'
        with self.assertRaisesRegex(ValueError, 'V4 feature'):
            composer.compose(self.image, self.report, self.catalog, changed)
        original = composer.inputs()[0]
        self.assertEqual(original, self.image)

    def test_browser_and_offline_match_for_connected_regular_profiles(self):
        offered = requested_options(self.catalog, self.report)
        villagers = [k for k in offered if self.catalog[k]['kind'] == 'villager']
        normal = next(k for k in offered if self.catalog[k]['kind'] == 'furniture')
        diary = next(k for k in offered if self.catalog[k]['kind'] == 'diary')
        fish = next(k for k in offered if self.catalog[k]['kind'] == 'fish')
        surface = next(k for k in offered if self.catalog[k]['kind'] == 'floor')
        profiles = [('empty', []), ('regular-all', offered), ('all-villagers', villagers),
                    ('regular-furniture', [normal]), ('diary-and-creature', [diary, fish, surface])]
        cases = []
        for name, requested in profiles:
            selection = self.select(requested)
            result, _, _ = composer.compose(self.image, self.report, self.catalog, selection)
            cases.append(dict(name=name, requested=requested, selection=selection, sha256=sha256(result)))
        with tempfile.TemporaryDirectory(prefix='v3-pipeline-scope-') as directory:
            path = Path(directory)/'fixture.json'
            path.write_bytes(composer.canonical(dict(plan=self.plan, cases=cases,
                base=str(ROOT/LOCK.parent/'animal-forest-v3-asset-loader.z64'),
                stable=str(composer.stable_reference(self.report)[0]))))
            process = subprocess.run(['node', '--experimental-global-webcrypto',
                str(ROOT/'tests/v3_browser_equivalence.mjs'), str(path)],
                capture_output=True, text=True, timeout=90)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(len(json.loads(process.stdout)['passed']), len(cases))


if __name__ == '__main__':
    unittest.main()
