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
from v3_import_scope import PIPELINE, UNAVAILABLE_BEHAVIOURS, availability, requested_options

LOCK = ROOT/os.environ.get('V3_IMPORT_SCOPE_LOCK', 'build/v3-seasonal-stock-installed-03/build-lock.json')


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
        pool = {r['item_id'] for r in self.report['shops']['imports'] if r['group'] in (0, 1, 2, 3, 5)}
        seasonal = self.report['equipment_resources'].get('seasonal_stock', {})
        if seasonal.get('installed'):
            pool.update(r['item_id'] for r in seasonal['source']['imports'])
        from v3_furniture_rewards import existing_system_items
        pool.update(existing_system_items(self.report))
        self.assertEqual({r['item_id'] for k,r in self.catalog.items()
                          if r['kind'] == 'furniture' and k in offered},
                         pool & {r['item_id'] for r in self.catalog.values() if r['kind'] == 'furniture'})
        self.assertEqual([r['id'] for r in self.plan['options'] if not r.get('dependency_only')], offered)
        self.assertTrue(all(g['forced_disabled'] for g in self.plan['runtime_groups']))
        self.assertEqual({r['id'] for r in self.plan['behaviours'] if r.get('pipeline_unavailable')}, UNAVAILABLE_BEHAVIOURS)
        self.assertTrue(all('v4_only' not in r for r in self.plan['behaviours']))
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
        self.assertTrue(all('deferred to V4' not in self.states[key]['reason'] for key in lottery))

    def test_installed_golden_routes_are_independent_and_require_their_providers(self):
        golden = self.report['equipment_resources']['golden_tools']['items']
        self.assertEqual(len(golden), 4)
        for key in golden:
            self.assertTrue(self.states[key]['selectable'])
            selected = self.select([key])
            self.assertEqual(selected['enabled'], [key])
            result, _, _ = composer.compose(self.image, self.report, self.catalog, selected)
            for group in groups(self.image, self.report):
                for field in group['fields']:
                    self.assertEqual(struct.unpack_from('>I', result, field['offset'])[0], field['disabled'])
            bad = copy.deepcopy(self.report)
            bad['equipment_resources']['golden_tools']['items'][key]['pending'] = ['acquisition']
            self.assertFalse(availability(self.catalog, bad)[key]['selectable'])
        bad = copy.deepcopy(self.report)
        bad['equipment_resources']['carried_items']['quest']['rewards']['installed'] = False
        self.assertTrue(all(not availability(self.catalog, bad)[key]['selectable'] for key in golden))
        self.assertTrue(all(self.states[key]['selectable'] for key in self.catalog
                            if self.catalog[key]['kind'] == 'equipment' and key not in golden))

    def test_native_redd_consumes_group_three_without_imported_event_providers(self):
        from aflib import by_vrom
        # Complete retail initializer, retaining the checked English mail-return
        # gate correction; no holiday-provider code is needed to generate stock.
        manager = by_vrom(self.image)[0x3800000].extract(self.image)
        start, end, ram = 0x8095C09C, 0x8095C264, 0x8095B8B0
        routine = bytearray(manager[start-ram:end-ram])
        self.assertEqual(sha256(routine), '34a608591329ec90dd188697f0edc0707854a4167d2dc9d68b9999b7846849e4')
        self.assertEqual(struct.unpack_from('>I', routine, 0x8095C24C-start)[0], 0)
        struct.pack_into('>I', routine, 0x8095C24C-start, 0x24020001)
        self.assertEqual(sha256(routine), '535e47fa896d5dfba8972b1857cbfb2e96d2cfdfb808c944ac4377ccc878d0f8')
        for group_at, call_at in ((0x8095C198,0x8095C1AC), (0x8095C1D8,0x8095C1EC), (0x8095C224,0x8095C238)):
            self.assertEqual(struct.unpack_from('>I',routine,group_at-start)[0],0x24020003)
            self.assertEqual(struct.unpack_from('>2I',routine,call_at-start),(0x0C02FF3C,0xAFA20018))
        redd = [composer.furniture_key(r) for r in self.report['shops']['imports'] if r['group']==3]
        self.assertEqual(len(redd),12)
        self.assertTrue(all(self.states[k]['selectable'] for k in redd))
        self.assertTrue(all(g['forced_disabled'] for g in self.plan['runtime_groups']))

    def test_existing_gulliver_and_igloo_rewards_require_their_actual_providers(self):
        from v3_furniture_rewards import existing_system_items
        by_item = {r['item_id']:key for key,r in self.catalog.items() if r['kind']=='furniture'}
        rewards = self.report['furniture_rewards']
        categories = {route:[by_item[r['item_id']] for r in rewards['imports'] if r['route']==route]
                      for route in (12,19,23)}
        self.assertEqual({route:len(keys) for route,keys in categories.items()}, {12:20,19:8,23:10})
        self.assertTrue(all(self.states[key]['selectable'] for route in (12,19) for key in categories[route]))
        self.assertTrue(all(not self.states[key]['selectable'] for key in categories[23]))
        self.assertTrue(all('new summer-camping building and scene' in self.states[key]['reason']
                            for key in categories[23]))
        for route in (12,19):
            for key in (categories[route][0], categories[route][-1]):
                selection = self.select([key])
                self.assertEqual(selection['enabled'],[key])
                result, _, _ = composer.compose(self.image,self.report,self.catalog,selection)
                for group in groups(self.image,self.report):
                    for field in group['fields']:
                        self.assertEqual(struct.unpack_from('>I',result,field['offset'])[0],field['disabled'])
        bad = copy.deepcopy(self.report); bad['furniture_rewards']['selected_profile_aware'] = False
        self.assertEqual(existing_system_items(bad),set())
        self.assertTrue(all(not availability(self.catalog,bad)[key]['selectable']
                            for route in (12,19) for key in categories[route]))
        bad = copy.deepcopy(self.report); bad['camper_trade']['winter_selection_installed'] = False
        self.assertTrue(all(not availability(self.catalog,bad)[key]['selectable'] for key in categories[19]))
        self.assertTrue(all(availability(self.catalog,bad)[key]['selectable'] for key in categories[12]))
        bad = copy.deepcopy(self.report); bad['furniture_rewards']['routes'] = []
        self.assertTrue(all(not availability(self.catalog,bad)[key]['selectable'] for key in categories[12]))
        bad = copy.deepcopy(self.report)
        item = next(r for r in bad['furniture']['imports'] if r['item_id'] == self.catalog[categories[12][0]]['item_id'])
        item['remaining'] = ['native interaction']
        self.assertFalse(availability(self.catalog,bad)[categories[12][0]]['selectable'])

    def test_existing_reward_admission_authenticates_complete_installed_resources(self):
        from aflib import by_vrom
        from v3_asset_loader import BLOB
        from v3_furniture_rewards import FIRST, RAM, verify_existing_system_items
        from v3_import_storage import PACKAGE, PACKAGE_RAM
        from v3_camper_trade import QUEST
        files = by_vrom(self.image)
        self.assertEqual(len(verify_existing_system_items(self.image,self.report)),28)
        broken = bytearray(self.image); broken[files[BLOB].pstart+PACKAGE+FIRST-PACKAGE_RAM] ^= 1
        with self.assertRaisesRegex(ValueError,'reward helper'):
            verify_existing_system_items(broken,self.report)
        route = self.report['furniture_rewards']['routes'][0]
        broken = bytearray(self.image); broken[files[route['vrom']].pstart] ^= 1
        with self.assertRaisesRegex(ValueError,'Gulliver owner'):
            verify_existing_system_items(broken,self.report)
        broken = bytearray(self.image); broken[files[QUEST].pstart+0x2460+3] ^= 1
        with self.assertRaisesRegex(ValueError,'winter trade allocation'):
            verify_existing_system_items(broken,self.report)
        bad = copy.deepcopy(self.report)
        bad['furniture_rewards']['routes'][0]['donor_list_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError,'membership or metadata'):
            verify_existing_system_items(self.image,bad)

    def test_stock_composition_removes_every_unselected_import_and_preserves_native_lists(self):
        from aflib import by_vrom
        from v3_shops import VROM
        from v3_surface_stock import list_items
        tables = composer.furniture_stock_tables(self.image,self.report,self.catalog)
        data = by_vrom(self.image)[VROM].extract(self.image)
        pointers = struct.unpack_from('>12I',data,self.report['shops']['table_offset'])
        for selected in (set(), {t['rows'][-1]['id'] for t in tables}, set(self.catalog)):
            writes = composer.furniture_stock_selection(self.image,self.report,self.catalog,selected)
            result = composer.apply_writes(self.image,writes)
            changed = by_vrom(result)[VROM].extract(result)
            for table in tables:
                group = table['group']; before = list_items(data,pointers[group]&0xFFFFFF)
                native = before[:-len(table['rows'])]
                expected = native + [int(r['hex'],16) for r in table['rows'] if r['id'] in selected]
                self.assertEqual(list_items(changed,pointers[group]&0xFFFFFF),expected)
            allowed = {i for t in tables for i in range(t['offset'],t['offset']+len(t['before'])//2)}
            self.assertTrue(all(i in allowed or a==b for i,(a,b) in enumerate(zip(self.image,result))))
        bad = copy.deepcopy(self.report)
        bad['shops']['imports'][0]['group']=0
        with self.assertRaisesRegex(ValueError,'native prefix'):
            composer.furniture_stock_tables(self.image,bad,self.catalog)
        bad = copy.deepcopy(self.report)
        bad['shops']['descriptor']+=4
        with self.assertRaisesRegex(ValueError,'descriptor'):
            composer.furniture_stock_tables(self.image,bad,self.catalog)

    def test_unavailable_acquisition_and_behaviour_settings_reject_before_composition(self):
        rejected = [k for k,s in self.states.items() if not s['selectable']]
        self.assertIn('GAFE01-r0/item/3294', rejected)  # Savings mailbox, not regular stock.
        self.assertIn('GAFE01-r0/item/2530', rejected)  # Harvest cutlery.
        for key in rejected:
            with self.assertRaisesRegex(ValueError, 'Unavailable standalone'):
                self.select([key])
        for key in UNAVAILABLE_BEHAVIOURS:
            with self.assertRaisesRegex(ValueError, 'not admitted'):
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
        from aflib import by_vrom
        from v3_asset_loader import BLOB
        base = by_vrom(result)[BLOB].pstart
        summer = {r['item_id'] for r in self.report['furniture_rewards']['imports'] if r['route']==23}
        for row in self.catalog.values():
            if row['kind']=='furniture' and row['item_id'] in summer:
                # Both preserved summer calendar/manager admission predicates
                # read these actual four-byte furniture flags.
                self.assertEqual(struct.unpack_from('>I',result,base+row['enable_offset'])[0],0)
        for group in groups(self.image, self.report):
            for field in group['fields']:
                self.assertEqual(struct.unpack_from('>I', result, field['offset'])[0], field['disabled'])
        restored = composer.apply_writes(result, [{**r,'before':r['after'],'after':r['before']} for r in writes])
        self.assertEqual(restored, self.image)
        self.assertEqual(sha256(result), self.plan['all_selected_sha256'])
        changed = copy.deepcopy(self.select(requested))
        changed['behaviours']['birthday-presentation'] = 'GameCube'
        with self.assertRaisesRegex(ValueError, 'Unavailable behaviour'):
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
        golden = list(self.report['equipment_resources']['golden_tools']['items'])
        redd = [composer.furniture_key(r) for r in self.report['shops']['imports'] if r['group']==3]
        rewards = self.report['furniture_rewards']['imports']
        by_item = {r['item_id']:key for key,r in self.catalog.items() if r['kind']=='furniture'}
        profiles = [('empty', []), ('regular-all', offered), ('all-villagers', villagers),
                    ('regular-furniture', [normal]), ('diary-and-creature', [diary, fish, surface]),
                    ('redd-stock', redd), ('one-redd-item', redd[-1:]),
                    *((key.rsplit('/',1)[-1], [key]) for key in golden)]
        for route in (12,19):
            keys = [by_item[r['item_id']] for r in rewards if r['route']==route]
            profiles.extend([(f'reward-route-{route}',keys),(f'sparse-reward-{route}',keys[-1:])])
        cases = []
        seasonal = self.report['equipment_resources'].get('seasonal_stock')
        if seasonal:
            for mode in ('N64', 'GameCube'):
                for row in seasonal['source']['imports']:
                    profiles.append((mode+'-'+row['donor_item_id'], [row['id']], {'late-december-stock':mode}))
        for profile in profiles:
            name, requested = profile[:2]
            selection = self.select(requested, profile[2] if len(profile)>2 else None)
            result, _, _ = composer.compose(self.image, self.report, self.catalog, selection)
            cases.append(dict(name=name, requested=requested, selection=selection, sha256=sha256(result),
                              behaviours=profile[2] if len(profile)>2 else {}))
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
