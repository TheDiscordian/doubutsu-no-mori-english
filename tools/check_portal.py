"""Silent, isolated browser checks against the local portal and real private inputs."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import time
from threading import Thread
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright
from aflib import sha256
from build_portal import TARGET_SHA
from gamecube import Disc

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8073/')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if not out.is_relative_to(ROOT/'build') or out.exists():
        raise ValueError('Choose a fresh ignored browser-check directory')
    out.mkdir(parents=True)
    native = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'
    ciso = ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso'
    # Sparse ISO fixture from the same supplied CISO; never touch the original.
    iso = out/'donor.iso'
    with Disc(ciso) as disc, iso.open('xb') as target:
        target.truncate(1459978240)
        for block, physical in enumerate(disc.blocks):
            if physical is not None:
                at = block*disc.block_size
                if at >= 1459978240:
                    continue
                target.seek(at)
                target.write(disc.read(at, min(disc.block_size, 1459978240-at)))
    results, requests, errors = {}, [], []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--mute-audio'])
        context = browser.new_context(viewport={'width': 1440, 'height': 1050}, accept_downloads=True)
        context.on('request', lambda r: requests.append({'url': r.url, 'method': r.method,
            'body_bytes': len(r.post_data_buffer or b'')}))
        page = context.new_page()
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(args.url)
        page.wait_for_function("() => document.getElementById('status').textContent.includes('Choose both')")
        assert page.title() == 'Animal Crossing N64 · English Translation'
        assert 'Animal Crossing N64' in page.locator('.brand').inner_text()
        body = page.locator('body').inner_text()
        assert not any(old in body for old in ('V1 Final', 'LOCAL PREVIEW', 'Is this the public release?', 'Audio starts muted'))
        assert page.locator('#build').is_disabled()
        assert page.locator('video').evaluate('(v) => v.paused && v.muted && !v.autoplay')
        page.screenshot(path=out/'desktop.png', full_page=True)
        results['initial_state'] = 'passed'
        page.locator('#n64').set_input_files(str(native))
        page.locator('#gamecube').set_input_files(str(ciso))
        page.locator('#build').click()
        page.locator('#cancel').click()
        assert page.locator('#success').is_hidden() and not page.locator('#download').get_attribute('href')
        assert 'Cancelled' in page.locator('#status').inner_text()
        results['cancel'] = 'passed'

        def patch_current(label):
            start = time.monotonic()
            page.locator('#build').click()
            page.wait_for_function("() => !document.getElementById('success').hidden || !document.getElementById('error').hidden", timeout=90000)
            assert page.locator('#error').is_hidden(), page.locator('#error').inner_text()
            with page.expect_download() as event:
                page.locator('#download').click()
            download = event.value
            path = out/(label+'.z64')
            download.save_as(path)
            digest = sha256(path.read_bytes())
            assert digest == TARGET_SHA
            assert download.suggested_filename == 'Animal Crossing N64 - English.z64'
            results[label] = {'sha256': digest, 'seconds': round(time.monotonic()-start, 2),
                'download_filename': download.suggested_filename}
            print(json.dumps({label: results[label]}), flush=True)

        patch_current('ciso-browser-output')
        page.screenshot(path=out/'success.png', full_page=True)
        page.locator('#gamecube').set_input_files(str(iso))
        assert page.locator('#success').is_hidden() and not page.locator('#download').get_attribute('href')
        results['input_change_clears_download'] = 'passed'
        patch_current('iso-browser-output')

        bad = bytearray(native.read_bytes()); bad[100] ^= 1
        page.locator('#n64').set_input_files({'name': 'modified.z64', 'mimeType': 'application/octet-stream', 'buffer': bytes(bad)})
        page.locator('#build').click()
        page.locator('#error').wait_for(state='visible')
        assert 'N64 checksum' in page.locator('#error').inner_text()
        assert page.locator('#success').is_hidden()
        results['wrong_n64_rejected'] = 'passed'
        page.locator('#n64').set_input_files({'name': 'archive.7z', 'mimeType': 'application/octet-stream', 'buffer': b'archive'})
        assert 'Extract archives' in page.locator('#error').inner_text()
        assert page.locator('#build').is_disabled()
        results['archive_rejected'] = 'passed'
        page.reload()
        page.wait_for_function("() => document.getElementById('status').textContent.includes('Choose both')")
        page.locator('#input-checksums summary').click()
        assert page.locator('[data-input-md5]').count() == 6
        assert all(node.is_visible() for node in page.locator('[data-input-md5]').all())
        results['visitor_copy_and_visible_hashes'] = 'passed'
        for width in (375, 768, 1440):
            page.set_viewport_size({'width': width, 'height': 900})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'Overflow at {width}'
            page.screenshot(path=out/f'layout-{width}.png', full_page=True)
        results['responsive_widths'] = [375, 768, 1440]
        # A Pages-style project subpath must resolve scripts, workers, and patch
        # data without root-relative URLs. This temporary root contains only the
        # exported site and its build receipt, never ROMs or test fixtures.
        class QuietHandler(SimpleHTTPRequestHandler):
            def log_message(self, *args):
                pass
        export_parent = ROOT/'build/web-portal-02'
        with ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(export_parent))) as server:
            thread = Thread(target=server.serve_forever, daemon=True); thread.start()
            subpath_origin = f'127.0.0.1:{server.server_port}'
            try:
                page.goto(f'http://{subpath_origin}/site/')
                page.wait_for_function("() => document.getElementById('status').textContent.includes('Choose both')")
                page.locator('#n64').set_input_files(str(native))
                page.locator('#gamecube').set_input_files(str(ciso))
                patch_current('subpath-browser-output')
            finally:
                server.shutdown(); thread.join(timeout=3)
        # All browser requests, including workers, must remain body-free local GETs.
        origin = urlsplit(args.url).netloc
        assert all(r['method'] == 'GET' and not r['body_bytes'] and urlsplit(r['url']).netloc in {origin, subpath_origin} for r in requests)
        assert not errors, errors
        results['local_get_requests_only'] = True
        results['browser_errors'] = errors
        results['requests'] = requests
        browser.close()
    (out/'results.json').write_text(json.dumps(results, indent=2)+'\n')
    print(json.dumps({k:v for k,v in results.items() if k!='requests'}, indent=2))


if __name__ == '__main__':
    main()
