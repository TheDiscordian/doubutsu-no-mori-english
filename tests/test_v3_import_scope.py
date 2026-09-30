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
from v3_holiday_selection import groups,active
from v3_import_scope import PIPELINE, UNAVAILABLE_BEHAVIOURS, availability, requested_options

LOCK = ROOT/os.environ.get('V3_IMPORT_SCOPE_LOCK', 'build/v3-nook-font-repaired-02/build-lock.json')


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
        from v3_holiday_acquisition import installed_items
        pool.update(installed_items(self.report))
        from v3_holiday_acquisition import exercise_items
        pool.update(self.catalog[k]['item_id'] for k in exercise_items(self.report)
                    if self.catalog[k]['kind']=='furniture')
        from v3_harvest_acquisition import installed_items as harvest_items
        pool.update(self.catalog[k]['item_id'] for k in harvest_items(self.report)
                    if self.catalog[k]['kind']=='furniture')
        from v3_password_acquisition import installed_items as password_items
        password_ids=password_items(self.report)
        pool.update(r['item_id'] for r in self.catalog.values() if r['id'] in password_ids and r['kind']=='furniture')
        self.assertEqual({r['item_id'] for k,r in self.catalog.items()
                          if r['kind'] == 'furniture' and k in offered},
                         pool & {r['item_id'] for r in self.catalog.values() if r['kind'] == 'furniture'})
        self.assertEqual([r['id'] for r in self.plan['options'] if not r.get('dependency_only')], offered)
        self.assertEqual({g['id']:g['forced_disabled'] for g in self.plan['runtime_groups']},
                         {'diary-holidays':False,'carried-quest':False})
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
        self.assertFalse(any(active(g,selection['enabled'],selection['behaviours'],scope=PIPELINE,
                                   report=self.report) for g in groups(self.image,self.report)))
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
        self.assertFalse(any(active(g,redd,{},scope=PIPELINE,report=self.report)
                             for g in groups(self.image,self.report)))

    def test_existing_gulliver_and_igloo_rewards_require_their_actual_providers(self):
        from v3_furniture_rewards import existing_system_items
        by_item = {r['item_id']:key for key,r in self.catalog.items() if r['kind']=='furniture'}
        rewards = self.report['furniture_rewards']
        categories = {route:[by_item[r['item_id']] for r in rewards['imports'] if r['route']==route]
                      for route in (12,19,23)}
        self.assertEqual({route:len(keys) for route,keys in categories.items()}, {12:20,19:8,23:10})
        self.assertTrue(all(self.states[key]['selectable'] for route in (12,19) for key in categories[route]))
        self.assertTrue(all(not self.states[key]['selectable'] for key in categories[23]))
        self.assertTrue(all('summer-camping acquisition path is unfinished' in self.states[key]['reason']
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

    def test_built_mayor_gifts_are_independent_and_activate_only_their_provider(self):
        from v3_holiday_acquisition import installed_items
        gifts=[r for r in self.report['furniture']['imports'] if r['item_id'] in installed_items(self.report)]
        self.assertEqual(len(gifts),50)
        self.assertEqual(sum(r['catalogue_orderable'] for r in gifts),12)
        self.assertTrue(all(self.states[r['id']]['selectable'] for r in gifts))
        self.assertTrue(self.states['GAFE01-r0/item/1FCC']['selectable'])
        for key in ('GAFE01-r0/item/1FC0','GAFE01-r0/item/30A8','GAFE01-r0/item/3378'):
            for mode in ('N64','GameCube'):
                selection=self.select([key],{'holiday-calendar':mode})
                self.assertEqual(selection['enabled'],[key]);self.assertEqual(selection['required'],[])
                result,_,_=composer.compose(self.image,self.report,self.catalog,selection)
                for group in groups(self.image,self.report):
                    on=group['id']=='diary-holidays'
                    for field in group['fields']:
                        self.assertEqual(struct.unpack_from('>I',result,field['offset'])[0],
                                         field['enabled'] if on else field['disabled'])
        for family,field in (('world','installed'),('optional_dialogue','installed'),
                             ('lifecycle','callbacks_installed')):
            bad=copy.deepcopy(self.report);bad['equipment_resources']['npc_extra'][family][field]=False
            self.assertEqual(installed_items(bad),set())
        bad=copy.deepcopy(self.report)
        bad['equipment_resources']['npc_extra']['events']['participants']['unbound_services']=['missing actor']
        self.assertEqual(installed_items(bad),set())
        bad=copy.deepcopy(self.report)
        row=next(r for r in bad['furniture']['imports'] if r['id']==gifts[0]['id'])
        row['remaining']=['native interaction']
        self.assertFalse(availability(self.catalog,bad)[row['id']]['selectable'])

    def test_mayor_admission_authenticates_providers_source_text_and_metadata(self):
        from v3_holiday_acquisition import verify_installed_items
        from v3_import_storage import ITEMS
        from aflib import by_vrom
        from v3_asset_loader import BLOB
        self.assertEqual(len(verify_installed_items(self.image,self.report)),50)
        n=self.report['equipment_resources']['npc_extra']
        for part in (n['packet'],n['events']['sky']['packet'],n['events']['festivals']['packet']):
            broken=bytearray(self.image);broken[part['physical']+123]^=1
            with self.assertRaisesRegex(ValueError,'complete holiday acquisition packet'):
                verify_installed_items(broken,self.report)
        key='GAFE01-r0/item/1FC0';row=self.catalog[key]
        broken=bytearray(self.image)
        broken[by_vrom(self.image)[BLOB].pstart+ITEMS+(row['runtime_index']-1024)*32+24]=8
        with self.assertRaisesRegex(ValueError,'gift identity'):
            verify_installed_items(broken,self.report)
        bad=copy.deepcopy(self.report)
        next(r for r in bad['furniture']['imports'] if r['id']==key)['donor_list_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'gift identity'):
            verify_installed_items(self.image,bad)
        bad=copy.deepcopy(self.report)
        bad['equipment_resources']['npc_extra']['events']['selection']['groups'][0]['fields'].pop()
        with self.assertRaisesRegex(ValueError,'provider activation fields'):
            verify_installed_items(self.image,bad)

    def test_exercise_pair_uses_complete_controller_and_mutual_selection(self):
        from v3_holiday_acquisition import exercise_items,bind_exercise_selection
        from v3_carried_selection import masks
        pair={'GAFE01-r0/item/2523','GAFE01-r0/item/1FCC'}
        self.assertEqual(exercise_items(self.report),pair)
        warning=composer.save_compatibility(self.report)
        self.assertIn('Carried-item saves require every carried family',warning)
        self.assertIn('Removing a family is not a save migration',warning)
        self.assertEqual(self.plan['save_compatibility'],warning)
        self.assertEqual(self.plan['import_groups'],[dict(id='summer-exercise',members=sorted(pair))])
        for key in sorted(pair):
            selected=self.select([key])
            self.assertEqual(set(selected['enabled']),pair)
            self.assertEqual(selected['required'],sorted(pair-{key}))
            result,_,_=composer.compose(self.image,self.report,self.catalog,selected)
            for mask in masks(self.image,self.report):
                expected=sum(r['mask'] for r in mask['members'] if r['id'] in pair)
                self.assertEqual(struct.unpack_from('>I',result,mask['offset'])[0],expected)
            for group in groups(self.image,self.report):
                for field in group['fields']:
                    self.assertEqual(struct.unpack_from('>I',result,field['offset'])[0],
                        field['enabled'] if group['id']=='diary-holidays' else field['disabled'])
        for part in ('action_installed','prepared_core_installed'):
            bad=copy.deepcopy(self.report)
            bad['equipment_resources']['player_motion']['exercise'][part]=False
            if part=='action_installed':self.assertEqual(exercise_items(bad),set())
            else:
                with self.assertRaisesRegex(ValueError,'player exercise dependencies'):
                    bind_exercise_selection(self.image,bad,copy.deepcopy(self.catalog))
        bad=copy.deepcopy(self.report)
        next(r for r in bad['furniture']['imports'] if r['id']=='GAFE01-r0/item/1FCC')['donor_list_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'exercise card/prize identity'):
            bind_exercise_selection(self.image,bad,copy.deepcopy(self.catalog))
        part=self.report['equipment_resources']['npc_extra']['events']['exercise']['packet']
        broken=bytearray(self.image);broken[part['physical']+123]^=1
        with self.assertRaisesRegex(ValueError,'complete holiday acquisition packet'):
            bind_exercise_selection(broken,self.report,copy.deepcopy(self.catalog))

    def test_unavailable_acquisition_and_behaviour_settings_reject_before_composition(self):
        rejected = [k for k,s in self.states.items() if not s['selectable']]
        self.assertIn('GAFE01-r0/item/3294', rejected)  # Savings mailbox, not regular stock.
        self.assertNotIn('GAFE01-r0/item/2530', rejected)  # Installed table-pickup route.
        for key in rejected:
            with self.assertRaisesRegex(ValueError, 'Unavailable standalone'):
                self.select([key])
        for key in UNAVAILABLE_BEHAVIOURS:
            with self.assertRaisesRegex(ValueError, 'not admitted'):
                self.select([], {key:'GameCube'})
        with self.assertRaisesRegex(ValueError, 'Unknown import scope'):
            composer.resolve(self.catalog, [], scope='unrestricted-v3', report=self.report)

    def test_spirit_uses_complete_independent_wisp_services_and_selection(self):
        from v3_carried_selection import quest_items,verify_quest_items
        key='GAFE01-r0/item/2D28'
        self.assertEqual(quest_items(self.report),{key})
        self.assertEqual(verify_quest_items(self.image,self.report),{key})
        self.assertEqual(self.catalog[key]['dependencies'],[])
        for keys in ([key],['GAFE01-r0/item/1FC0'],[key,'GAFE01-r0/item/1FC0']):
            selection=self.select(keys)
            result,_,_=composer.compose(self.image,self.report,self.catalog,selection)
            self.assertEqual(selection['required'],[])
            for group in groups(self.image,self.report):
                on={'carried-quest':key in keys,
                    'diary-holidays':'GAFE01-r0/item/1FC0' in keys}[group['id']]
                self.assertEqual(active(group,selection['enabled'],selection['behaviours'],scope=PIPELINE,report=self.report),on)
                for field in group['fields']:
                    self.assertEqual(struct.unpack_from('>I',result,field['offset'])[0],field['enabled'] if on else field['disabled'])
            self.assertEqual(selection['carried_mask'],64 if key in keys else 0)
        for owner,field in (('npc','installed'),('npc','native_services_bound'),('manager','npc_registered')):
            bad=copy.deepcopy(self.report);bad['equipment_resources']['carried_items']['quest'][owner][field]=False
            self.assertFalse(availability(self.catalog,bad)[key]['selectable'])
        n=self.report['equipment_resources']['carried_items']['quest']['npc']
        bad=copy.deepcopy(self.report);bad['equipment_resources']['carried_items']['quest']['npc']['unbound_services']=['missing']
        self.assertFalse(availability(self.catalog,bad)[key]['selectable'])
        bad=copy.deepcopy(self.report);bad['equipment_resources']['carried_items']['quest']['npc']['reward_destinations']['rows'][0]['item']^=4
        with self.assertRaisesRegex(ValueError,'actual spirit reward destinations'):
            verify_quest_items(self.image,bad)
        bad=copy.deepcopy(self.report);bad['equipment_resources']['carried_items']['quest']['npc']['text']['rows'][0]['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'official spirit dialogue'):
            verify_quest_items(self.image,bad)
        p=n['packet'];broken=bytearray(self.image);broken[p['physical']+123]^=1
        with self.assertRaisesRegex(ValueError,'complete spirit acquisition dependency packet'):
            verify_quest_items(broken,self.report)

    def test_password_only_choices_use_real_frontend_and_live_selection_gates(self):
        from v3_password_acquisition import installed_items,verify_installed_items
        from aflib import by_vrom
        from v3_asset_loader import BLOB
        from v3_import_storage import ITEMS
        ids=installed_items(self.report)
        self.assertEqual(len(ids),18)
        self.assertEqual(verify_installed_items(self.image,self.report,self.catalog),ids)
        self.assertTrue(all(self.states[k]['selectable'] for k in ids))
        bad=copy.deepcopy(self.report)
        bad['equipment_resources']['passwords']['conversation']['native_bindings_installed']=False
        self.assertEqual(installed_items(bad),set())
        bad=copy.deepcopy(self.report)
        next(r for r in bad['furniture']['imports'] if r['id']=='GAFE01-r0/item/331C')['remaining']=['item behaviour']
        self.assertNotIn('GAFE01-r0/item/331C',installed_items(bad))
        for key in ('GAFE01-r0/item/331C','GAFE01-r0/item/1DCC','GAFE01-r0/item/2640'):
            selected=self.select([key]);self.assertEqual(selected['enabled'],[key])
            result,_,blob=composer.compose(self.image,self.report,self.catalog,selected)
            for candidate in ids:
                row=self.catalog[candidate];at=row['enable_offset'];width=row['enable_bytes']
                self.assertEqual(int.from_bytes(blob[at:at+width],'big'),int(candidate==key))
            self.assertFalse(any(active(g,selected['enabled'],selected['behaviours'],scope=PIPELINE,
                report=self.report) for g in groups(self.image,self.report)))
        bad=copy.deepcopy(self.report)
        next(r for r in bad['equipment_resources']['passwords']['source']['destinations']['rows']
            if r['id']=='GAFE01-r0/item/331C')['enable_ram']+=4
        with self.assertRaisesRegex(ValueError,'live selection/destination'):
            verify_installed_items(self.image,bad,self.catalog)
        bad=bytearray(self.image);row=self.catalog['GAFE01-r0/item/331C']
        bad[by_vrom(self.image)[BLOB].pstart+ITEMS+(row['runtime_index']-1024)*32+24]=8
        with self.assertRaisesRegex(ValueError,'metadata or ordering'):
            verify_installed_items(bad,self.report,self.catalog)

    def test_harvest_rewards_require_cutlery_and_only_their_built_provider(self):
        from v3_harvest_acquisition import installed_items,verify_installed_items
        from v3_carried_selection import masks
        cutlery='GAFE01-r0/item/2530';h=self.report['equipment_resources']['harvest']
        wanted=set(h['reward_choices'])|{cutlery}
        self.assertEqual(len(wanted),13)
        self.assertEqual(installed_items(self.report),wanted)
        self.assertEqual(verify_installed_items(self.image,self.report,self.catalog),wanted)
        self.assertTrue(all(self.states[k]['selectable'] for k in wanted))
        for key in ('GAFE01-r0/item/32D0','GAFE01-r0/item/2642','GAFE01-r0/item/2742',cutlery):
            selected=self.select([key])
            self.assertEqual(set(selected['enabled']),{key,cutlery})
            self.assertEqual(selected['required'],[] if key==cutlery else [cutlery])
            result,_,blob=composer.compose(self.image,self.report,self.catalog,selected)
            for reward in h['reward_choices']:
                row=self.catalog[reward]
                self.assertEqual(int.from_bytes(blob[row['enable_offset']:row['enable_offset']+4],'big'),int(reward==key))
            for mask in masks(self.image,self.report):
                expected=sum(r['mask'] for r in mask['members'] if r['id']==cutlery)
                self.assertEqual(struct.unpack_from('>I',result,mask['offset'])[0],expected)
            for group in groups(self.image,self.report):
                for field in group['fields']:
                    self.assertEqual(struct.unpack_from('>I',result,field['offset'])[0],
                        field['enabled'] if group['id']=='diary-holidays' else field['disabled'])
        for part in ('hiding','registry','shared_motions','manager','text','npc'):
            bad=copy.deepcopy(self.report);bad['equipment_resources']['harvest'][part]['installed']=False
            self.assertEqual(installed_items(bad),set())
        bad=copy.deepcopy(self.report)
        bad['equipment_resources']['holiday_items']['pickup']['installed']=False
        self.assertEqual(installed_items(bad),set())

    def test_harvest_retains_controls_text_and_exact_superseding_native_hooks(self):
        from v3_harvest_acquisition import verify_installed_items
        from aflib import by_vrom,CODE_VROM,CODE_RAM,sha256
        from v3_asset_loader import BLOB
        from v3_import_storage import ITEMS
        e=self.report['equipment_resources'];h=e['harvest'];m=h['manager'];files=by_vrom(self.image)
        for address in (0x8007F630,0x8007F640,0x8007F660,0x80057E4C):
            broken=bytearray(self.image);broken[files[CODE_VROM].pstart+address-CODE_RAM+3]^=1
            with self.assertRaisesRegex(ValueError,'Harvest calendar binding'):
                verify_installed_items(broken,self.report,self.catalog)
        # Even a matching forged outer receipt cannot hide a changed retained prefix.
        broken=bytearray(self.image);owner=files[m['vrom']]
        broken[owner.pstart+128]^=1;bad=copy.deepcopy(self.report)
        bad['equipment_resources']['harvest']['manager']['sha256']=sha256(owner.extract(broken))
        with self.assertRaisesRegex(ValueError,'retained Harvest controls'):
            verify_installed_items(broken,bad,self.catalog)
        broken=bytearray(self.image);row=self.catalog['GAFE01-r0/item/32D0']
        broken[files[BLOB].pstart+ITEMS+(row['runtime_index']-1024)*32+24]=8
        with self.assertRaisesRegex(ValueError,'Harvest furniture identity'):
            verify_installed_items(broken,self.report,self.catalog)
        bad=copy.deepcopy(self.report)
        next(r for r in bad['room_surfaces']['stock']['harvest'] if r['id']=='GAFE01-r0/item/2642')['harvest_acquisition']['destination_item']='264B'
        from v3_harvest_acquisition import installed_items
        self.assertNotIn('GAFE01-r0/item/2642',installed_items(bad))
        bad_catalog=copy.deepcopy(self.catalog);bad_catalog['GAFE01-r0/item/2642']['item_id']='264B'
        with self.assertRaisesRegex(ValueError,'Harvest surface identity'):
            verify_installed_items(self.image,self.report,bad_catalog)
        bad=copy.deepcopy(self.report);bad['equipment_resources']['harvest']['text']['rows'][0]['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'retained official Harvest dialogue'):
            verify_installed_items(self.image,bad,self.catalog)
        bad=copy.deepcopy(self.report)
        bad['equipment_resources']['npc_extra']['events']['demo']['hooks'][1]['before']='0'*16
        with self.assertRaisesRegex(ValueError,'Harvest cutlery native service'):
            verify_installed_items(self.image,bad,self.catalog)

    def test_exclusive_outfits_are_only_resources_of_the_selected_villager(self):
        villagers = [k for k,r in self.catalog.items() if r['kind'] == 'villager']
        selected = self.select(villagers)
        resources = {k for k,s in self.states.items() if s['dependency_only']}
        self.assertEqual(len(resources), 2)
        self.assertLessEqual(resources, set(selected['required']))
        self.assertTrue(resources.isdisjoint(selected['requested']))
        self.assertTrue(all(self.catalog[k]['kind'] == 'clothing' for k in resources))

    def test_scope_retains_built_providers_and_preserves_unfinished_resources(self):
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
            on=active(group,requested,self.select(requested)['behaviours'],scope=PIPELINE,report=self.report)
            for field in group['fields']:
                self.assertEqual(struct.unpack_from('>I', result, field['offset'])[0],
                                 field['enabled'] if on else field['disabled'])
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
        for key in ('GAFE01-r0/item/1FC0','GAFE01-r0/item/30A8','GAFE01-r0/item/3378'):
            profiles.append(('mayor-'+key.rsplit('/',1)[-1],[key]))
        profiles.append(('mayor-calendar-gc',['GAFE01-r0/item/1FC0'],{'holiday-calendar':'GameCube'}))
        for key in ('GAFE01-r0/item/331C','GAFE01-r0/item/1DCC','GAFE01-r0/item/2640'):
            profiles.append(('password-'+key.rsplit('/',1)[-1],[key]))
        for key in ('GAFE01-r0/item/2523','GAFE01-r0/item/1FCC'):
            profiles.append(('exercise-'+key.rsplit('/',1)[-1],[key]))
        for key in ('GAFE01-r0/item/32D0','GAFE01-r0/item/2642','GAFE01-r0/item/2742','GAFE01-r0/item/2530'):
            profiles.append(('harvest-'+key.rsplit('/',1)[-1],[key]))
        cases = []
        profiles.extend([('spirit-only',['GAFE01-r0/item/2D28']),
                         ('spirit-with-mayor',['GAFE01-r0/item/2D28','GAFE01-r0/item/1FC0'])])
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
                capture_output=True, text=True, timeout=180)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(len(json.loads(process.stdout)['passed']), len(cases))


if __name__ == '__main__':
    unittest.main()
