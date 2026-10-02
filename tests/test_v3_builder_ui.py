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
        cls.site = ROOT/os.environ.get('V3_BUILDER_UI_SITE', 'build/v3-website-design-01/site')
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
        for unwanted in ('Nothing is uploaded', 'stay on your device', 'Both imports', 'your selected festive', 'Unselected replacements'):
            self.assertNotIn(unwanted, text)
        self.assertNotIn('late-december-stock', self.page.locator('#behaviour-options').inner_html())
        self.assertIn('decorations Nook can sell from December 26–31', text)

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
        page.locator('#save-ack').check(); page.locator('#build').click()
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
