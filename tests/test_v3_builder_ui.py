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


class BuilderInterfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.site = ROOT/os.environ.get('V3_BUILDER_UI_SITE', 'build/v3-website-release-copy-01/site')
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
        self.assertIn('River and pond fish make wider turns.',page.locator('#behaviour-description-fish-movement').inner_text())
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
            with page.expect_download() as event:page.locator('#settings-export').click()
            with tempfile.TemporaryDirectory(prefix='v3-feature-settings-') as temp:
                path=Path(temp)/'settings.json';event.value.save_as(path)
                self.assertEqual(json.loads(path.read_text())['requested'],[feature['id']])
                page.locator('#clear-all').click()
                page.locator('#settings-import').set_input_files(str(path))
                page.wait_for_function("() => document.querySelector('#settings-status').textContent.startsWith('Settings imported.')")
                self.assertTrue(checkbox.is_checked())
            self.assertIn(feature['name'],page.locator('#dependency-list').text_content())
            page.locator('#open-items').click();page.locator('#clear-items').click();page.locator('#close-items').click()
            self.assertTrue(checkbox.is_checked())

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

    def test_actual_rom_download_uses_the_wisp_setting(self):
        evidence = ROOT/'build/v3-feature-wisp-browser-02/results.json'
        if not evidence.exists():
            self.skipTest('Checked current Wisp offline comparison required')
        expected = json.loads(evidence.read_text())['focused-selection']['sha256']
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

    def test_actual_rom_download_uses_all_fish_movement(self):
        evidence=ROOT/'build/v3-fish-movement-browser-01/results.json'
        if not evidence.exists():self.skipTest('Current fish offline comparison required')
        expected=json.loads(evidence.read_text())['focused-selection']['sha256']
        page=self.page
        page.locator('#open-items').click();page.locator('#kind').select_option('fish')
        for identity in ('2301','2324'):
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
        evidence = ROOT/'build/v3-new-year-stock-browser-02/results.json'
        if not evidence.exists():
            self.skipTest('Checked current offline comparison required')
        expected = json.loads(evidence.read_text())['focused-selection']
        manifest = json.loads((self.site/'data/composition.json').read_text())
        self.assertEqual(manifest['base_sha256'], json.loads(evidence.read_text())['base_sha256'])
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
                self.assertEqual(hashlib.file_digest(stream, 'sha256').hexdigest(), expected['sha256'])
        with page.expect_download() as event:
            page.locator('#receipt').click()
        with tempfile.TemporaryDirectory(prefix='v3-ui-profile-') as temp:
            profile = Path(temp)/'profile.json'; event.value.save_as(profile)
            result = json.loads(profile.read_text())
            self.assertEqual(result['output_sha256'], expected['sha256'])
            self.assertEqual(result['behaviours']['new-year-stock'], 'neither')
            self.assertEqual(result['requested'], ['GAFE01-r0/item/327C','GAFE01-r0/item/3298'])


if __name__ == '__main__':
    unittest.main()
