"""Focused real-browser checks for the current private builder interface."""
from functools import partial
import hashlib
from http.server import ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys
import tempfile
from threading import Thread
import unittest

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from serve_portal import StaticPortal, validate_export
import v3_optional_composition as composer
from v3_creature_choices import options as behaviour_options


class BuilderInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.site = ROOT/os.environ.get('V3_BUILDER_UI_SITE', 'build/v3-website-golden-copy-01/site')
        if not cls.site.exists():
            raise unittest.SkipTest('Current private interface export required')
        validate_export(cls.site)
        class Quiet(StaticPortal):
            def log_message(self, *args):
                pass
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(cls.site)))
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.origin = f'http://127.0.0.1:{cls.server.server_port}'
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--mute-audio'])

    @classmethod
    def tearDownClass(cls):
        cls.browser.close(); cls.playwright.stop()
        cls.server.shutdown(); cls.thread.join(timeout=3); cls.server.server_close()

    def setUp(self):
        self.context = self.browser.new_context(accept_downloads=True)
        self.addCleanup(self.context.close)
        self.page = self.context.new_page()
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.page.route('**/*', lambda route: route.continue_() if route.request.url.startswith(self.origin+'/') else route.abort())
        self.page.goto(self.origin)
        self.page.wait_for_function("() => !document.querySelector('#selection-controls').disabled || !document.querySelector('#error').hidden")
        self.assertTrue(self.page.locator('#error').is_hidden(), self.page.locator('#error').text_content())

    def tearDown(self):
        self.assertEqual(self.errors, [])

    def offline_sha256(self, requested, behaviours=None):
        """Compare the actual download with this export's checked offline build."""
        saved = composer.BASE, composer.BASE_SHA, composer.REPORT_SHA, composer.ABI
        try:
            composer.use_build_lock(ROOT/os.environ.get('V3_BUILDER_UI_LOCK',
                'build/v3-freshwater-patrol-installed-06/build-lock.json'))
            plan = json.loads((self.site/'data/composition.json').read_text())
            self.assertEqual(plan['base_sha256'], composer.BASE_SHA)
            self.assertEqual(plan['base_report_sha256'], composer.REPORT_SHA)
            image, report = composer.inputs()
            catalog = composer.catalogue(image, report)
            selection = composer.resolve(catalog, requested, scope='v3-pipeline',
                report=report, behaviour_options=behaviour_options(image, report),
                behaviours=behaviours)
            output, _, _ = composer.compose(image, report, catalog, selection)
            return hashlib.sha256(output).hexdigest()
        finally:
            composer.BASE, composer.BASE_SHA, composer.REPORT_SHA, composer.ABI = saved

    def test_consistent_windows_order_bounds_and_keyboard(self):
        page = self.page
        for width, height in ((320,800), (375,800), (768,950), (1440,950), (1280,600)):
            page.set_viewport_size(dict(width=width, height=height))
            self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            artifacts = os.environ.get('V3_BUILDER_UI_ARTIFACTS')
            if artifacts and width in (375,1440):
                page.screenshot(path=str(ROOT/artifacts/f'page-{width}.png'), full_page=True)
            self.assertTrue(page.evaluate('''() => {
                const r = id => document.getElementById(id).getBoundingClientRect();
                return r('game-inputs').bottom <= r('settings-export').top &&
                    r('settings-export').bottom <= r('choices-heading').top &&
                    r('select-all').bottom <= r('open-items').top &&
                    r('additions').bottom <= r('behaviour-controls').top &&
                    r('behaviour-controls').bottom <= r('build').top;
            }'''))
            for name, dialog, options, select, clear in (
                ('villagers','villager-dialog','villager-options','select-villagers','clear-villagers'),
                ('items','item-dialog','options','select-visible','clear-visible'),
            ):
                page.locator('#open-'+name).click()
                if artifacts and width in (375,1440):
                    page.screenshot(path=str(ROOT/artifacts/f'{name}-{width}.png'))
                self.assertTrue(page.evaluate('''([dialog,options,select,clear]) => {
                    const r = id => document.getElementById(id).getBoundingClientRect();
                    const box = r(dialog);
                    return box.left >= 0 && box.right <= innerWidth && box.top >= 0 && box.bottom <= innerHeight &&
                        r(select).bottom <= r(options).top && r(clear).bottom <= r(options).top &&
                        document.getElementById(dialog).scrollWidth <= box.width;
                }''', [dialog,options,select,clear]))
                page.keyboard.press('Escape')
                self.assertTrue(page.locator('#'+dialog).is_hidden())
                self.assertTrue(page.locator('#open-'+name).evaluate('(button) => button === document.activeElement'))
                page.locator('#open-'+name).click(); page.locator('#close-'+name).click()
                self.assertTrue(page.locator('#'+dialog).is_hidden())

    def test_feature_checkbox_cards_share_rows_and_stack_on_mobile(self):
        page=self.page
        for width,columns in ((320,1),(375,1),(768,2),(1440,2)):
            page.set_viewport_size(dict(width=width,height=950))
            geometry=page.locator('#behaviour-options').evaluate('''grid => {
                const rect = element => {
                    const r=element.getBoundingClientRect();
                    return {left:r.left,right:r.right,top:r.top,width:r.width};
                };
                return {
                    grid:rect(grid),
                    cards:[...grid.querySelectorAll('.feature-setting')].map(card => ({
                        ...rect(card),label:rect(card.querySelector('strong')),
                        checkbox:rect(card.querySelector('input')),
                        overflow:card.scrollWidth>card.clientWidth
                    }))
                };
            }''')
            plan=json.loads((self.site/'data/composition.json').read_text())
            self.assertEqual(len(geometry['cards']),len(plan['features']))
            first,second=geometry['cards'][:2]
            if columns==2:
                self.assertAlmostEqual(first['top'],second['top'],delta=1)
                self.assertLessEqual(first['right'],second['left'])
                self.assertLess(first['width'],geometry['grid']['width']*.55)
            else:
                self.assertGreater(second['top'],first['top'])
                self.assertAlmostEqual(first['width'],geometry['grid']['width'],delta=1)
            for card in geometry['cards']:
                self.assertFalse(card['overflow'])
                self.assertGreaterEqual(card['label']['left'],card['left'])
                self.assertLessEqual(card['label']['right'],card['checkbox']['left'])
                self.assertLessEqual(card['checkbox']['right'],card['right'])
                self.assertAlmostEqual(card['label']['top'],card['checkbox']['top'],delta=4)

    def test_item_categories_bulk_selection_and_dependencies(self):
        page = self.page
        page.locator('#open-items').click()
        page.locator('#kind').select_option('clothing')
        count = page.locator('#options .option:visible').count()
        self.assertGreater(count, 0)
        page.locator('#select-visible').click()
        self.assertEqual(page.locator('#options input:checked').count(), count)
        page.locator('#clear-visible').click()
        self.assertEqual(page.locator('#options input:checked').count(), 0)
        page.locator('#search').fill('not-an-item')
        self.assertTrue(page.locator('#no-results').is_visible())
        self.assertTrue(page.locator('#select-visible').is_disabled())
        page.locator('#close-items').click()
        page.locator('#open-villagers').click()
        page.locator('#villager-search').fill('Punchy')
        page.locator('#villager-options .option:visible input').first.check()
        self.assertIn('1 selected', page.locator('#villager-count').text_content())
        self.assertIn('cherry shirt', page.locator('#dependency-list').text_content())
        self.assertIn('speed bag', page.locator('#dependency-list').text_content())

    def test_four_decorations_and_settings_round_trip(self):
        page = self.page
        names = ('kadomatsu','kagamimochi','festive-candle','festive-flag')
        for mask in range(16):
            for bit, name in enumerate(names):
                page.locator('#stock-'+name).set_checked(bool(mask & (1 << bit)))
            with page.expect_download() as event:
                page.locator('#settings-export').click()
            with tempfile.TemporaryDirectory(prefix='v3-ui-settings-') as temp:
                path = Path(temp)/'settings.json'; event.value.save_as(path)
                value = json.loads(path.read_text())
                self.assertEqual(value['behaviours']['new-year-stock'], ('neither','kadomatsu','kagamimochi','both')[mask & 3])
                for bit, identity in ((2,'3298'), (3,'327C')):
                    self.assertEqual('GAFE01-r0/item/'+identity in value['requested'], bool(mask & (1 << bit)))
                page.locator('#clear-decorations').click()
                page.locator('#settings-import').set_input_files(str(path))
                page.wait_for_function("() => document.querySelector('#settings-status').textContent.startsWith('Settings imported.')")
                for bit, name in enumerate(names):
                    self.assertEqual(page.locator('#stock-'+name).is_checked(), bool(mask & (1 << bit)))
        page.locator('#select-decorations').click()
        self.assertTrue(all(page.locator('#stock-'+name).is_checked() for name in names))
        page.locator('#open-items').click(); page.locator('#search').fill('festive candle')
        page.locator('[data-id="GAFE01-r0/item/3298"] input').uncheck()
        page.locator('#close-items').click()
        self.assertFalse(page.locator('#stock-festive-candle').is_checked())

    def test_direct_copy(self):
        text = self.page.locator('body').inner_text()
        for unwanted in ('Nothing is uploaded', 'stay on your device', 'Both imports', 'your selected festive', 'Unselected replacements',
                         'Applies to original and imported insects.', 'Releasing an insect still works in either mode.'):
            self.assertNotIn(unwanted, text)
        self.assertNotIn('late-december-stock', self.page.locator('#behaviour-options').inner_html())
        self.assertIn('Nook’s shop sells New Year items from December 26–31.', text)
        self.assertIn('two are randomly selected each day during that period.', text)
        self.assertNotIn('other dates are unchanged', text)
        self.assertNotIn('existing furniture spaces', text)
        for unwanted in ('V3 preview','Experimental V3','test save','still being checked','unverified'):
            self.assertNotIn(unwanted,text)
        self.assertEqual(self.page.title(),'Animal Crossing N64 · English Translation')

    def test_build_has_no_save_warning_or_acknowledgement(self):
        page = self.page
        self.assertEqual(page.locator('#save-warning, #save-ack, #baseline-note, #behaviour-note').count(), 0)
        page.locator('#n64').set_input_files(dict(name='original.z64', mimeType='application/octet-stream', buffer=b'input'))
        page.locator('#gamecube').set_input_files(dict(name='original.iso', mimeType='application/octet-stream', buffer=b'input'))
        self.assertTrue(page.locator('#build').is_enabled())
        page.locator('#select-all').click()
        self.assertTrue(page.locator('#build').is_enabled())
        page.locator('#clear-all').click()
        page.locator('#stock-kadomatsu').uncheck()
        self.assertTrue(page.locator('#build').is_enabled())

    def test_fish_movement_is_separate_and_round_trips(self):
        page=self.page
        population=page.locator('select[aria-describedby="behaviour-description-fish-population"]')
        movement=page.locator('select[aria-describedby="behaviour-description-fish-movement"]')
        self.assertEqual(page.locator('select[aria-describedby="behaviour-description-coastal-fish-movement"]').count(),0)
        self.assertIn('GameCube swimming, waiting, and escape behaviour for river, pond, and ocean fish.',page.locator('#behaviour-description-fish-movement').inner_text())
        for first,second in (('N64','GameCube'),('GameCube','N64')):
            population.select_option(first);movement.select_option(second)
            with page.expect_download() as event:page.locator('#settings-export').click()
            with tempfile.TemporaryDirectory(prefix='v3-fish-settings-') as temp:
                path=Path(temp)/'settings.json';event.value.save_as(path)
                settings=json.loads(path.read_text())
                self.assertEqual(settings['behaviours']['fish-population'],first)
                self.assertEqual(settings['behaviours']['fish-movement'],second)
                population.select_option(second);movement.select_option(first)
                page.locator('#settings-import').set_input_files(str(path))
                page.wait_for_function("() => document.querySelector('#settings-status').textContent.startsWith('Settings imported.')")
                self.assertEqual(population.input_value(),first);self.assertEqual(movement.input_value(),second)

    def test_wisp_is_a_town_setting_not_an_item_choice(self):
        page = self.page
        wisp = page.get_by_role('checkbox', name='Enable Wisp', exact=True)
        self.assertEqual(page.locator('#behaviour-controls #enable-wisp').count(), 1)
        self.assertEqual(page.locator('#options [data-id="GAFE01-r0/item/2D28"]').count(), 0)
        self.assertEqual(page.locator('#item-dialog #enable-wisp').count(), 0)
        self.assertFalse(wisp.is_checked())
        page.locator('#open-items').click(); page.locator('#select-items').click()
        page.locator('#close-items').click()
        self.assertFalse(wisp.is_checked())
        page.locator('#clear-all').click()
        wisp.check()
        page.locator('#open-items').click()
        page.locator('#search').fill('spirit')
        self.assertEqual(page.locator('#options .option:visible').count(), 0)
        page.locator('#clear-items').click(); page.locator('#close-items').click()
        self.assertTrue(wisp.is_checked())
        with page.expect_download() as event:
            page.locator('#settings-export').click()
        with tempfile.TemporaryDirectory(prefix='v3-wisp-settings-') as temp:
            path = Path(temp)/'settings.json'; event.value.save_as(path)
            settings = json.loads(path.read_text())
            self.assertEqual(settings['requested'], ['feature/wisp'])
            wisp.uncheck()
            self.assertEqual(page.locator('#selection-heading').inner_text(), 'No imports selected')
            page.locator('#settings-import').set_input_files(str(path))
            page.wait_for_function("() => document.querySelector('#settings-status').textContent.startsWith('Settings imported.')")
            self.assertTrue(wisp.is_checked())
        page.locator('#clear-all').click(); self.assertFalse(wisp.is_checked())
        page.locator('#select-all').click(); self.assertTrue(wisp.is_checked())

    def test_features_supply_items_and_round_trip_as_features(self):
        plan=json.loads((self.site/'data/composition.json').read_text())
        page=self.page
        for feature in plan['features']:
            checkbox=page.locator('#enable-'+feature['id'].split('/')[1])
            self.assertEqual(page.locator('#behaviour-controls #'+checkbox.get_attribute('id')).count(),1)
            for identity in feature['required_imports']:
                self.assertEqual(page.locator(f'#options [data-id="{identity}"]').count(),0)
            page.locator('#clear-all').click(); checkbox.check()
            if feature['required_imports']:
                self.assertTrue(page.locator('#selection-summary').inner_text().startswith('0 chosen by you · '))
            else:
                self.assertEqual(page.locator('#selection-summary').inner_text(),
                    'No added items or villagers. Your build uses your chosen town settings.')
            with page.expect_download() as event:page.locator('#settings-export').click()
            with tempfile.TemporaryDirectory(prefix='v3-feature-settings-') as temp:
                path=Path(temp)/'settings.json';event.value.save_as(path)
                self.assertEqual(json.loads(path.read_text())['requested'],[feature['id']])
                page.locator('#clear-all').click()
                page.locator('#settings-import').set_input_files(str(path))
                page.wait_for_function("() => document.querySelector('#settings-status').textContent.startsWith('Settings imported.')")
                self.assertTrue(checkbox.is_checked())
                if feature['required_imports']:
                    self.assertTrue(page.locator('#selection-summary').inner_text().startswith('0 chosen by you · '))
            if feature['required_imports']:
                self.assertIn(feature['name'],page.locator('#dependency-list').text_content())
            page.locator('#open-items').click();page.locator('#clear-items').click();page.locator('#close-items').click()
            self.assertTrue(checkbox.is_checked())

    def test_chosen_counter_excludes_features_and_automatic_items(self):
        page=self.page
        plan=json.loads((self.site/'data/composition.json').read_text())
        for feature in plan['features']:
            page.locator('#enable-'+feature['id'].split('/')[1]).check()
        def check_count(chosen):
            required=page.locator('#dependency-list li').count()
            self.assertEqual(page.locator('#selection-summary').inner_text(),
                f'{chosen} chosen by you · {required} added as requirements')
            self.assertEqual(page.locator('#selection-heading').inner_text(),
                f'{chosen+required} imports included')
        check_count(0)
        page.locator('#open-items').click()
        fish=page.locator('[data-id="GAFE01-r0/item/2320"] input')
        fish.check();check_count(1)
        page.locator('#close-items').click()
        page.locator('#open-villagers').click()
        villager=page.locator('#villager-options input').first
        villager.check();check_count(2)
        villager.uncheck();check_count(1)
        page.locator('#close-villagers').click()
        page.locator('#open-items').click();fish.uncheck();check_count(0)
        page.locator('#close-items').click()

    def test_freshwater_fish_are_in_the_item_selector(self):
        page = self.page
        page.locator('#open-items').click(); page.locator('#kind').select_option('fish')
        self.assertEqual(page.locator('#options .option:visible').count(), 9)
        for name in ('brook trout', 'arapaima', 'crawfish', 'frog', 'killifish'):
            self.assertTrue(page.get_by_role('checkbox', name=name, exact=True).is_visible())

    def test_golden_tools_have_one_checkbox_and_no_individual_item_choices(self):
        page=self.page
        control=page.get_by_role('checkbox',name='Enable Golden tools',exact=True)
        self.assertEqual(page.locator('#behaviour-controls #enable-golden-tools').count(),1)
        self.assertEqual(page.locator('#enable-golden-trees').count(),0)
        self.assertEqual(page.locator('#enable-golden-tools-description').inner_text(),
                         'Add the golden shovel, net, rod, and axe, with their original acquisition routes.')
        self.assertFalse(control.is_checked())
        for identity in ('2239','223A','223B','223C'):
            self.assertEqual(page.locator(f'#options [data-id="GAFE01-r0/item/{identity}"]').count(),0)
        control.check()
        for name in ('golden shovel','golden net','golden rod','golden axe'):
            self.assertIn(name,page.locator('#dependency-list').text_content())
        with page.expect_download() as event:page.locator('#settings-export').click()
        with tempfile.TemporaryDirectory(prefix='v3-golden-settings-') as temp:
            path=Path(temp)/'settings.json';event.value.save_as(path)
            self.assertEqual(json.loads(path.read_text())['requested'],['feature/golden-tools'])
            control.uncheck()
            self.assertEqual(page.locator('#selection-heading').inner_text(),'No imports selected')
            page.locator('#settings-import').set_input_files(str(path))
            page.wait_for_function("() => document.querySelector('#settings-status').textContent.startsWith('Settings imported.')")
            self.assertTrue(control.is_checked())
        page.locator('#open-items').click();page.locator('#clear-items').click();page.locator('#close-items').click()
        self.assertTrue(control.is_checked())

    def test_summer_camping_is_a_feature_not_an_item_selection(self):
        page=self.page
        plan=json.loads((self.site/'data/composition.json').read_text())
        feature=next(row for row in plan['features'] if row['id']=='feature/summer-camping')
        control=page.get_by_role('checkbox',name='Enable Summer camping',exact=True)
        self.assertEqual(page.locator('#behaviour-controls #enable-summer-camping').count(),1)
        self.assertEqual(page.locator('#item-dialog #enable-summer-camping').count(),0)
        self.assertFalse(control.is_checked())
        for identity in feature['required_imports']:
            self.assertEqual(page.locator(f'#options [data-id="{identity}"]').count(),0)
        page.locator('#open-items').click();page.locator('#select-items').click();page.locator('#close-items').click()
        self.assertFalse(control.is_checked())
        page.locator('#clear-all').click();control.check()
        for identity in feature['required_imports']:
            name=next(row['name'] for row in plan['options'] if row['id']==identity)
            self.assertIn(name,page.locator('#dependency-list').text_content())
        page.locator('#open-items').click();page.locator('#clear-items').click();page.locator('#close-items').click()
        self.assertTrue(control.is_checked())
        page.locator('#clear-all').click();self.assertFalse(control.is_checked())
        page.locator('#select-all').click();self.assertTrue(control.is_checked())

    def test_actual_rom_download_uses_the_wisp_setting(self):
        expected = self.offline_sha256(['feature/wisp'])
        plan = json.loads((self.site/'data/composition.json').read_text())
        group = next(row for row in plan['runtime_groups'] if row['id']=='carried-quest')
        page = self.page
        page.locator('#enable-wisp').check()
        page.locator('#n64').set_input_files(str(ROOT/'local/rom/Doubutsu no Mori (Japan).z64'))
        page.locator('#gamecube').set_input_files(str(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso'))
        page.locator('#build').click()
        page.wait_for_function("() => !document.querySelector('#success').hidden || !document.querySelector('#error').hidden", timeout=90000)
        self.assertTrue(page.locator('#error').is_hidden(), page.locator('#error').text_content())
        with page.expect_download() as event:
            page.locator('#download').click()
        with tempfile.TemporaryDirectory(prefix='v3-wisp-rom-') as temp:
            rom = Path(temp)/'wisp.z64'; event.value.save_as(rom)
            with rom.open('rb') as stream:
                self.assertEqual(hashlib.file_digest(stream, 'sha256').hexdigest(), expected)
                for field in group['fields']:
                    stream.seek(field['offset'])
                    self.assertEqual(int.from_bytes(stream.read(4), 'big'), field['enabled'])
            with page.expect_download() as event:
                page.locator('#receipt').click()
            path = Path(temp)/'profile.json'; event.value.save_as(path)
            self.assertEqual(json.loads(path.read_text())['requested'], ['feature/wisp'])
        page.locator('#enable-wisp').uncheck()
        self.assertTrue(page.locator('#success').is_hidden())
        self.assertIsNone(page.locator('#download').get_attribute('href'))
        self.assertEqual(page.locator('#selection-heading').inner_text(), 'No imports selected')

    def test_actual_rom_download_uses_the_summer_camping_feature(self):
        expected=self.offline_sha256(['feature/summer-camping'])
        plan=json.loads((self.site/'data/composition.json').read_text())
        feature=next(row for row in plan['features'] if row['id']=='feature/summer-camping')
        page=self.page
        page.locator('#enable-summer-camping').check()
        page.locator('#n64').set_input_files(str(ROOT/'local/rom/Doubutsu no Mori (Japan).z64'))
        page.locator('#gamecube').set_input_files(str(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso'))
        page.locator('#build').click()
        page.wait_for_function("() => !document.querySelector('#success').hidden || !document.querySelector('#error').hidden",timeout=90000)
        self.assertTrue(page.locator('#error').is_hidden(),page.locator('#error').text_content())
        with page.expect_download() as event:page.locator('#download').click()
        with tempfile.TemporaryDirectory(prefix='v3-camping-rom-') as temp:
            rom=Path(temp)/'camping.z64';event.value.save_as(rom)
            with rom.open('rb') as stream:
                self.assertEqual(hashlib.file_digest(stream,'sha256').hexdigest(),expected)
                for identity in feature['required_imports']:
                    row=next(row for row in plan['options'] if row['id']==identity)
                    for field in row['disable']:
                        stream.seek(field['offset'])
                        self.assertEqual(stream.read(len(bytes.fromhex(field['before']))).hex(),field['before'])
            with page.expect_download() as event:page.locator('#receipt').click()
            profile=Path(temp)/'profile.json';event.value.save_as(profile)
            self.assertEqual(json.loads(profile.read_text())['requested'],[feature['id']])
        page.locator('#enable-summer-camping').uncheck()
        self.assertTrue(page.locator('#success').is_hidden())
        self.assertIsNone(page.locator('#download').get_attribute('href'))

    def test_actual_rom_download_uses_all_fish_movement(self):
        expected=self.offline_sha256(['GAFE01-r0/item/2320'],{'fish-movement':'GameCube'})
        page=self.page
        page.locator('#open-items').click();page.locator('#kind').select_option('fish')
        for identity in ('2320',):
            page.locator(f'[data-id="GAFE01-r0/item/{identity}"] input').check()
        page.locator('#close-items').click()
        page.locator('select[aria-describedby="behaviour-description-fish-movement"]').select_option('GameCube')
        page.locator('#n64').set_input_files(str(ROOT/'local/rom/Doubutsu no Mori (Japan).z64'))
        page.locator('#gamecube').set_input_files(str(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso'))
        page.locator('#build').click()
        page.wait_for_function("() => !document.querySelector('#success').hidden || !document.querySelector('#error').hidden",timeout=90000)
        self.assertTrue(page.locator('#error').is_hidden(),page.locator('#error').text_content())
        with page.expect_download() as event:page.locator('#download').click()
        with tempfile.TemporaryDirectory(prefix='v3-fish-rom-') as temp:
            rom=Path(temp)/'fish.z64';event.value.save_as(rom)
            with rom.open('rb') as stream:self.assertEqual(hashlib.file_digest(stream,'sha256').hexdigest(),expected)
            with page.expect_download() as event:page.locator('#receipt').click()
            profile=Path(temp)/'profile.json';event.value.save_as(profile)
            values=json.loads(profile.read_text())['behaviours']
            self.assertEqual(values['fish-movement'],'GameCube')
            self.assertEqual(values['fish-population'],'N64')

    def test_item_codes_have_an_independent_toggle_and_real_download(self):
        page=self.page
        plan=json.loads((self.site/'data/composition.json').read_text())
        feature=next(row for row in plan['features'] if row['id']=='feature/item-codes')
        checkbox=page.locator('#enable-item-codes')
        self.assertFalse(checkbox.is_checked())
        self.assertEqual(page.locator('#item-dialog #enable-item-codes').count(),0)
        page.locator('#n64').set_input_files(str(ROOT/'local/rom/Doubutsu no Mori (Japan).z64'))
        page.locator('#gamecube').set_input_files(str(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso'))
        for on in (True,False):
            if on:checkbox.check()
            else:
                checkbox.uncheck()
                page.locator('#open-items').click()
                page.locator('[data-id="GAFE01-r0/item/2320"] input').check()
                page.locator('#close-items').click()
            requested=['feature/item-codes'] if on else ['GAFE01-r0/item/2320']
            expected=self.offline_sha256(requested)
            self.assertEqual(page.locator('#build').inner_text(),'Build with selected options')
            page.locator('#build').click()
            page.wait_for_function("() => !document.querySelector('#success').hidden || !document.querySelector('#error').hidden",timeout=90000)
            self.assertTrue(page.locator('#error').is_hidden(),page.locator('#error').inner_text())
            with page.expect_download() as event:page.locator('#download').click()
            with tempfile.TemporaryDirectory(prefix='v3-item-code-rom-') as temp:
                rom=Path(temp)/'codes.z64';event.value.save_as(rom)
                with rom.open('rb') as stream:
                    self.assertEqual(hashlib.file_digest(stream,'sha256').hexdigest(),expected)
                    for field in feature['disable']:
                        value=bytes.fromhex(field['before' if on else 'after'])
                        stream.seek(field['offset']);self.assertEqual(stream.read(len(value)),value)
                with page.expect_download() as event:page.locator('#receipt').click()
                profile=Path(temp)/'profile.json';event.value.save_as(profile)
                self.assertEqual(json.loads(profile.read_text())['requested'],requested)

    def test_cancel_selection_change_archives_and_stale_worker(self):
        page=self.page
        page.evaluate('''() => {
          window.__workers=[];
          const NativeWorker=window.Worker;
          window.Worker=class extends NativeWorker {
            constructor(...args) { super(...args); window.__workers.push(this); }
          };
        }''')
        native=ROOT/'local/rom/Doubutsu no Mori (Japan).z64'
        disc=ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso'
        page.locator('#n64').set_input_files(str(native));page.locator('#gamecube').set_input_files(str(disc))
        for control in ('cancel','select-all'):
            page.locator('#build').click()
            page.wait_for_function("() => document.querySelector('#progress').value >= 4 || !document.querySelector('#error').hidden")
            self.assertTrue(page.locator('#error').is_hidden(),page.locator('#error').inner_text())
            page.locator('#'+control).click()
            self.assertTrue(page.locator('#working').is_hidden())
            self.assertTrue(page.locator('#success').is_hidden())
            page.evaluate("window.__workers.at(-1).onmessage({data:{type:'done'}})")
            self.assertTrue(page.locator('#error').is_hidden())
            self.assertTrue(page.locator('#build').is_enabled())
        page.locator('#n64').set_input_files(dict(name='rom.7z',mimeType='application/octet-stream',buffer=b'archive'))
        self.assertTrue(page.locator('#error').is_visible())
        self.assertIn('Extract archives',page.locator('#error').inner_text())
        self.assertTrue(page.locator('#build').is_disabled())
        page.locator('#n64').set_input_files(str(native))
        stale=page.evaluate('''() => new Promise((resolve,reject) => {
          const worker=new Worker('./experimental/imports/worker.mjs',{type:'module'});
          const timer=setTimeout(() => {worker.terminate();reject(Error('Stale-plan check timed out'));},10000);
          worker.onmessage=({data}) => {
            if (data.type==='error'||data.type==='done') {
              clearTimeout(timer);worker.terminate();resolve(data);
            }
          };
          worker.postMessage({requested:[],plan_sha256:'0'.repeat(64),
            n64:document.querySelector('#n64').files[0],gamecube:document.querySelector('#gamecube').files[0]});
        })''')
        self.assertEqual(stale['type'],'error');self.assertIn('catalogue changed',stale['message'])

    def test_actual_rom_download_uses_the_four_checkboxes(self):
        expected = self.offline_sha256(['GAFE01-r0/item/327C','GAFE01-r0/item/3298'],
            {'new-year-stock':'neither'})
        page = self.page
        page.locator('#stock-kadomatsu').uncheck(); page.locator('#stock-kagamimochi').uncheck()
        page.locator('#stock-festive-candle').check(); page.locator('#stock-festive-flag').check()
        page.locator('#n64').set_input_files(str(ROOT/'local/rom/Doubutsu no Mori (Japan).z64'))
        page.locator('#gamecube').set_input_files(str(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso'))
        page.locator('#build').click()
        page.wait_for_function("() => !document.querySelector('#success').hidden || !document.querySelector('#error').hidden", timeout=90000)
        self.assertTrue(page.locator('#error').is_hidden(), page.locator('#error').text_content())
        with page.expect_download() as event:
            page.locator('#download').click()
        with tempfile.TemporaryDirectory(prefix='v3-ui-rom-') as temp:
            rom = Path(temp)/'decorations.z64'; event.value.save_as(rom)
            with rom.open('rb') as stream:
                self.assertEqual(hashlib.file_digest(stream, 'sha256').hexdigest(), expected)
        with page.expect_download() as event:
            page.locator('#receipt').click()
        with tempfile.TemporaryDirectory(prefix='v3-ui-profile-') as temp:
            profile = Path(temp)/'profile.json'; event.value.save_as(profile)
            result = json.loads(profile.read_text())
            self.assertEqual(result['output_sha256'], expected)
            self.assertEqual(result['behaviours']['new-year-stock'], 'neither')
            self.assertEqual(result['requested'], ['GAFE01-r0/item/327C','GAFE01-r0/item/3298'])


if __name__ == '__main__':
    unittest.main()
