"""Silent worker check in a temporary private server; never switch a V2 service."""
import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
from threading import Thread
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright
from aflib import sha256
import v3_optional_composition as composer

ROOT = composer.ROOT
PROBE = b'<!doctype html><meta charset="utf-8"><title>Private worker check</title><input id="n64" type="file"><input id="disc" type="file">'


def check_interface(page, origin, out, expected, catalog, review):
    """Exercise the actual UI; keep native gameplay checks out of this batch."""
    results = {}
    page.add_init_script('''(() => {
      const state = window.__lifecycle = {created: [], revoked: [], workers: [], terminations: 0};
      const create = URL.createObjectURL.bind(URL), revoke = URL.revokeObjectURL.bind(URL);
      URL.createObjectURL = value => { const url = create(value); state.created.push(url); return url; };
      URL.revokeObjectURL = url => { state.revoked.push(url); revoke(url); };
      const NativeWorker = window.Worker;
      window.Worker = class extends NativeWorker {
        constructor(...args) { super(...args); state.workers.push(this); }
        terminate() { state.terminations++; super.terminate(); }
      };
    })()''')
    page.goto(origin+'/preview/')
    page.wait_for_function("() => !document.querySelector('#selection-controls').disabled")
    assert page.locator('.option').count() == len(catalog)
    assert page.locator('.option input:checked').count() == 0
    assert page.locator('#build').is_disabled()
    assert 'No imports selected' in page.locator('#selection-heading').inner_text()
    assert page.locator('iframe, video, audio').count() == 0
    results['optional_by_default'] = True

    page.locator('#select-all').click()
    assert page.locator('.option input:checked').count() == len(catalog)
    page.locator('#clear-all').click()
    page.locator('#kind').select_option('clothing')
    page.locator('#select-visible').click()
    assert page.locator('.option input:checked').count() == 3
    page.locator('#clear-visible').click()
    assert page.locator('.option input:checked').count() == 0
    equipment=[key for key,row in catalog.items() if row['kind']=='equipment']
    if equipment:
        page.locator('#kind').select_option('equipment')
        assert page.locator('.option:visible').count()==len(equipment)
        page.locator('#select-visible').click()
        assert page.locator('.option input:checked').count()==len(equipment)
        page.locator('#clear-visible').click()
        assert page.locator('.option input:checked').count()==0
        results['equipment_category_select_and_clear']=len(equipment)
    page.locator('#kind').select_option('all')
    pending=review['unavailable'][0]
    page.locator('#search').fill(pending['id'])
    page.locator('#review summary').click()
    assert page.locator('.unavailable:visible').count() == 1
    assert pending['reason'] in page.locator('.unavailable:visible').inner_text()
    assert page.locator('.unavailable input, .unavailable button').count() == 0
    results['search_category_all_clear_and_review_reasons'] = True

    page.locator('#search').fill('Punchy')
    punchy = page.locator('[data-id="GAFE01-r0/villager/00EB"] input')
    punchy.focus(); punchy.press('Space')
    assert page.locator('.option input:checked').count() == 3
    for item in ('24BF', '3350'):
        required = page.locator(f'[data-id="GAFE01-r0/item/{item}"] input')
        assert required.is_checked() and required.is_disabled()
    assert 'cherry shirt' in page.locator('#dependency-list').inner_text()
    assert 'speed bag' in page.locator('#dependency-list').inner_text()
    punchy.uncheck()
    assert page.locator('.option input:checked').count() == 0
    punchy.check()
    page.locator('#search').fill('31D4')
    page.locator('[data-id="GAFE01-r0/item/31D4"] input').check()
    assert page.locator('.option input:checked').count() == 4
    results['keyboard_selection_dependencies_and_removal'] = True

    native = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'
    disc = ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso'
    page.locator('#n64').set_input_files(str(native))
    page.locator('#gamecube').set_input_files(str(disc))
    assert page.locator('#build').is_disabled()
    page.locator('#save-ack').check()
    assert page.locator('#build').is_enabled()
    page.locator('#build').click()
    page.wait_for_function("() => document.querySelector('#progress').value >= 4")
    page.locator('#cancel').click()
    assert page.locator('#working').is_hidden() and page.locator('#success').is_hidden()
    assert 'Cancelled' in page.locator('#status').inner_text()
    page.evaluate("window.__lifecycle.workers.at(-1).onmessage({data: {type: 'done'}})")
    assert page.locator('#error').is_hidden() and page.locator('#success').is_hidden()
    results['cancel_and_late_result_discard'] = True

    def build_and_download(label):
        page.locator('#build').click()
        page.wait_for_function("() => !document.querySelector('#success').hidden || !document.querySelector('#error').hidden", timeout=90000)
        assert page.locator('#error').is_hidden(), page.locator('#error').inner_text()
        with page.expect_download() as event:
            page.locator('#download').click()
        rom = out/(label+'.z64')
        event.value.save_as(rom)
        with page.expect_download() as event:
            page.locator('#receipt').click()
        profile = out/(label+'.json')
        event.value.save_as(profile)
        selection = json.loads(profile.read_bytes())
        assert sha256(rom.read_bytes()) == expected[label] == selection['output_sha256']
        assert page.locator('#output-sha').text_content() == expected[label]
        assert selection['experimental'] and not selection['web_patcher_enabled']
        results[label] = {'sha256': expected[label], 'profile_sha256': sha256(profile.read_bytes()),
                          'enabled': selection['enabled']}
        print(json.dumps({'interface_case': label, 'sha256': expected[label], 'downloads_verified': True}), flush=True)

    build_and_download('villager-and-seasonal-subset')
    old_urls = page.evaluate('window.__lifecycle.created.slice()')
    page.locator('#clear-all').click()
    assert page.locator('#success').is_hidden() and not page.locator('#download').get_attribute('href')
    assert set(old_urls) <= set(page.evaluate('window.__lifecycle.revoked'))
    assert page.locator('#save-warning').is_hidden()
    results['selection_change_revokes_downloads'] = True
    if equipment:
        page.locator('#search').fill('')
        page.locator('#kind').select_option('equipment')
        for key in (equipment[1],equipment[-1]):
            page.locator(f'[data-id="{key}"] input').check()
        assert page.locator('.option input:checked').count()==2
        assert page.locator('#dependencies').is_hidden()
        page.locator('#save-ack').check()
        build_and_download('equipment-subset')
        page.locator('#clear-all').click()
        page.locator('#kind').select_option('all')
    build_and_download('no-imports')
    old_urls = page.evaluate('window.__lifecycle.created.slice()')
    # Actually change the input. Re-selecting the identical file can leave the
    # native file-input value unchanged and does not prove a change-event path.
    page.locator('#gamecube').set_input_files([])
    assert page.locator('#success').is_hidden() and not page.locator('#receipt').get_attribute('href')
    assert set(old_urls) <= set(page.evaluate('window.__lifecycle.revoked'))
    results['file_change_revokes_downloads'] = True
    page.locator('#gamecube').set_input_files(str(disc))

    page.locator('#search').fill('')
    page.locator('#build').click()
    page.wait_for_function("() => document.querySelector('#progress').value >= 4")
    page.locator('#select-all').click()
    assert page.locator('#working').is_hidden() and page.locator('#success').is_hidden()
    assert page.locator('#build').is_disabled() and not page.locator('#save-ack').is_checked()
    page.evaluate("window.__lifecycle.workers.at(-1).onmessage({data: {type: 'done'}})")
    assert page.locator('#error').is_hidden()
    results['selection_change_cancels_active_build'] = True

    page.locator('#n64').set_input_files({'name': 'rom.7z', 'mimeType': 'application/octet-stream', 'buffer': b'archive'})
    assert page.locator('#error').is_visible() and 'Extract archives' in page.locator('#error').inner_text()
    page.locator('#gamecube').set_input_files(str(disc))
    page.locator('#save-ack').check()
    assert page.locator('#build').is_disabled()
    assert page.locator('#error').is_visible()
    results['invalid_either_input_blocks_build'] = True
    page.locator('#n64').set_input_files(str(native))
    stale = page.evaluate('''() => new Promise((resolve, reject) => {
      const worker = new Worker('/preview/experimental/imports/worker.mjs', {type: 'module'});
      const timer = setTimeout(() => {worker.terminate(); reject(Error('Stale-plan check timed out'));}, 10000);
      worker.onmessage = ({data}) => { if (data.type === 'error' || data.type === 'done') {
        clearTimeout(timer); worker.terminate(); resolve({type: data.type, message: data.message});
      }};
      worker.postMessage({requested: [], plan_sha256: '0'.repeat(64),
        n64: document.querySelector('#n64').files[0], gamecube: document.querySelector('#gamecube').files[0]});
    })''')
    assert stale['type'] == 'error' and 'catalogue changed' in stale['message'], stale
    results['stale_menu_rejected_by_worker'] = True
    for width in (320, 375, 768, 1440):
        page.set_viewport_size({'width': width, 'height': 950})
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), width
    results['no_horizontal_overflow'] = [320, 375, 768, 1440]
    results['download_urls_all_revoked'] = set(page.evaluate('window.__lifecycle.created')) <= set(page.evaluate('window.__lifecycle.revoked'))
    assert results['download_urls_all_revoked']
    assert page.evaluate('window.__lifecycle.terminations') >= 4
    return results


def check(export, output, *, interface=False, selected=None):
    focused=selected is not None
    export, out = export.resolve(), output.resolve()
    if (not export.is_relative_to(ROOT/'build') or not out.is_relative_to(ROOT/'build') or out.exists()):
        raise ValueError('Use an ignored export and a fresh ignored check directory')
    receipt = json.loads((export/'build.json').read_bytes())
    if receipt['served'] or not receipt['recipes_included'] or receipt['base_sha256'] != composer.BASE_SHA:
        raise ValueError('Expected the unserved current-build export with recipes')
    allowed = {'data/composition.json', 'data/manifest.json', 'data/v2/patch.afwp.gz',
               'data/v3/patch.afwp.gz', 'experimental/imports/composer.mjs',
               'experimental/imports/worker.mjs', 'web/core.mjs', 'data/review.json',
               'experimental/imports/bundle.mjs', 'experimental/imports/app.mjs',
               'experimental/imports/style.css', 'index.html'}
    if set(receipt['files']) != allowed:
        raise ValueError('Unexpected export file set; do not serve inputs or the repository')
    site = export/'site'
    resources = {path: (site/path).read_bytes() for path in receipt['files']}
    if any(sha256(data) != receipt['files'][path] for path, data in resources.items()):
        raise ValueError('Export files differ from their receipt')
    manifest = json.loads(resources['data/manifest.json'])
    # No directory listing and no route to inputs, saves, results, or the repo.
    state = {'corrupt_plan': False}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_GET(self):
            path = urlsplit(self.path).path
            if path == '/preview/': path += 'index.html'
            if path == '/check/':
                data, content_type = PROBE, 'text/html'
            elif path.startswith('/preview/') and path[len('/preview/'):] in resources:
                name = path[len('/preview/'):]
                data = resources[name]
                content_type = mimetypes.guess_type(name)[0] or 'application/octet-stream'
                if state['corrupt_plan'] and name == 'data/composition.json':
                    data = bytes([data[0] ^ 1]) + data[1:]
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Content-Security-Policy', "default-src 'none'; script-src 'self'; style-src 'self'; worker-src 'self'; connect-src 'self'")
            self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass  # Cancellation terminates outstanding worker reads.

    base, report = composer.inputs()
    catalog = composer.catalogue(base, report)
    profiles = [('no-imports', []), ('all-installed', list(catalog)),
                ('villager-and-seasonal-subset', ['GAFE01-r0/villager/00EB', 'GAFE01-r0/item/31D4'])]
    equipment=[key for key,row in catalog.items() if row['kind']=='equipment']
    if equipment:profiles.append(('equipment-subset',[equipment[1],equipment[-1]]))
    if focused:
        if interface:raise ValueError('Choose a focused worker profile or the complete interface check')
        composer.resolve(catalog,selected)
        profiles=[('focused-selection',selected)]
    expected = {}
    for name, selected in profiles:
        if interface and name == 'all-installed': continue
        result, _, _ = composer.compose(base, report, catalog, composer.resolve(catalog, selected))
        expected[name] = sha256(result)
    requests, errors, results = [], [], {}
    out.mkdir(parents=True)
    with ThreadingHTTPServer(('127.0.0.1', 0), Handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        origin = f'http://127.0.0.1:{server.server_port}'
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--mute-audio'])
                context = browser.new_context(accept_downloads=True, viewport={'width': 1440, 'height': 950})
                context.on('request', lambda r: requests.append({'url': r.url, 'method': r.method,
                    'body_bytes': len(r.post_data_buffer or b'')}))
                page = context.new_page()
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(origin+'/check/')
                page.locator('#n64').set_input_files(str(ROOT/'local/rom/Doubutsu no Mori (Japan).z64'))
                page.locator('#disc').set_input_files(str(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso'))

                def worker(selected, cancel=False):
                    # A real module Worker reads File objects and disc slices.
                    # No private game input is fetched from or uploaded to HTTP.
                    return page.evaluate('''({selected, cancel, plan_sha256}) => new Promise((resolve, reject) => {
                      const worker = new Worker('/preview/experimental/imports/worker.mjs', {type: 'module'});
                      const timer = setTimeout(() => { worker.terminate(); reject(Error('Worker check timed out')); }, 90000);
                      const finish = result => { clearTimeout(timer); worker.terminate(); resolve(result); };
                      worker.onerror = event => { clearTimeout(timer); worker.terminate(); reject(Error(event.message)); };
                      worker.onmessage = async ({data}) => {
                        if (cancel && data.type === 'progress') return finish({type: 'cancelled', last_progress: data.value});
                        if (data.type === 'error') return finish(data);
                        if (data.type === 'done') {
                          const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', data.buffer))]
                            .map(n => n.toString(16).padStart(2, '0')).join('');
                          finish({type: 'done', sha256: hash, bytes: data.buffer.byteLength, receipt: data.receipt});
                        }
                      };
                      worker.postMessage({requested: selected, plan_sha256, n64: document.querySelector('#n64').files[0],
                        gamecube: document.querySelector('#disc').files[0]});
                    })''', {'selected': selected, 'cancel': cancel, 'plan_sha256': manifest['plan']['sha256']})

                if interface:
                    results['interface'] = check_interface(page, origin, out, expected, catalog,
                        json.loads(resources['data/review.json']))
                else:
                    if not focused:
                        cancelled = worker(profiles[-1][1], cancel=True)
                        assert cancelled['type'] == 'cancelled', cancelled
                        results['worker_termination'] = cancelled
                    for name, selected in profiles:
                        result = worker(selected)
                        assert result['type'] == 'done', result
                        assert result['sha256'] == expected[name] == result['receipt']['output_sha256'], name
                        for key in ('enabled', 'required', 'profile_hex'):
                            assert result['receipt'][key] == composer.resolve(catalog, selected)[key], (name, key)
                        selection=composer.resolve(catalog,selected)
                        if 'surface_profile_hex' in selection:
                            for key in ('surface_profile_hex','surface_profile_sha256'):
                                assert result['receipt'][key]==selection[key],(name,key)
                            if selected:assert result['receipt']['save_compatibility']==composer.save_compatibility(report)
                        results[name] = result
                        print(json.dumps({'case': name, 'sha256': result['sha256'], 'matched_offline': True}), flush=True)
                    if focused:
                        ui=context.new_page();ui.on('pageerror',lambda error:errors.append(str(error)))
                        ui.goto(origin+'/preview/')
                        ui.wait_for_function("() => !document.querySelector('#selection-controls').disabled")
                        counts={}
                        for kind in sorted({catalog[k]['kind'] for k in profiles[0][1]}):
                            count=sum(r['kind']==kind for r in catalog.values())
                            ui.locator('#kind').select_option(kind)
                            assert ui.locator('.option:visible').count()==count
                            ui.locator('#select-visible').click()
                            assert ui.locator('.option:visible input:checked').count()==count
                            ui.locator('#clear-all').click();counts[kind]=count
                        results['focused_category_controls']=counts;ui.close()
                    else:
                        unknown = worker(['GAFE01-r0/item/0000'])
                        assert unknown['type'] == 'error' and 'Unknown or unimplemented' in unknown['message'], unknown
                        results['unknown_option_rejected'] = unknown
                        state['corrupt_plan'] = True
                        corrupt = worker(profiles[-1][1])
                        assert corrupt['type'] == 'error' and 'plan checksum mismatch' in corrupt['message'], corrupt
                        results['corrupt_plan_rejected'] = corrupt
                assert not errors, errors
                assert all(r['method'] == 'GET' and not r['body_bytes'] and
                           urlsplit(r['url']).netloc == urlsplit(origin).netloc for r in requests)
                browser.close()
        finally:
            server.shutdown()
            thread.join(timeout=3)
    results.update(base_sha256=composer.BASE_SHA, export_receipt_sha256=sha256((export/'build.json').read_bytes()),
                   requests=requests, browser_errors=errors, local_body_free_gets_only=True,
                   server_stopped=True, served_patchers_changed=False)
    (out/'results.json').write_bytes(composer.canonical(results))
    return {'checks': list(results)[:6], 'results_sha256': sha256((out/'results.json').read_bytes())}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--interface', action='store_true', help='Check the real selection page and downloads instead of the worker probe')
    parser.add_argument('--base-lock',type=Path,help='Explicit checked proposal lock for this isolated test')
    parser.add_argument('--select',action='append',help='Check only this current profile and its category controls; repeat for more identities')
    args = parser.parse_args()
    if args.base_lock:composer.use_build_lock(args.base_lock)
    print(json.dumps(check(args.export, args.output, interface=args.interface,selected=args.select), indent=2))
