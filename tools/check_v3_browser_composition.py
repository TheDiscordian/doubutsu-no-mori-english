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


def check(export, output):
    export, out = export.resolve(), output.resolve()
    if (not export.is_relative_to(ROOT/'build') or not out.is_relative_to(ROOT/'build') or out.exists()):
        raise ValueError('Use an ignored export and a fresh ignored check directory')
    receipt = json.loads((export/'build.json').read_bytes())
    if receipt['served'] or not receipt['recipes_included'] or receipt['base_sha256'] != composer.BASE_SHA:
        raise ValueError('Expected the unserved current-build export with recipes')
    allowed = {'data/composition.json', 'data/manifest.json', 'data/v2/patch.afwp.gz',
               'data/v3/patch.afwp.gz', 'experimental/imports/composer.mjs',
               'experimental/imports/worker.mjs', 'web/core.mjs'}
    if set(receipt['files']) != allowed:
        raise ValueError('Unexpected export file set; do not serve inputs or the repository')
    site = export/'site'
    resources = {path: (site/path).read_bytes() for path in receipt['files']}
    if any(sha256(data) != receipt['files'][path] for path, data in resources.items()):
        raise ValueError('Export files differ from their receipt')
    # No directory listing and no route to inputs, saves, results, or the repo.
    state = {'corrupt_plan': False}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_GET(self):
            path = urlsplit(self.path).path
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
            self.send_header('Content-Security-Policy', "default-src 'none'; script-src 'self'; worker-src 'self'; connect-src 'self'")
            self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass  # Cancellation terminates outstanding worker reads.

    base, report = composer.inputs()
    catalog = composer.catalogue(base, report)
    profiles = [('no-imports', []), ('all-installed', list(catalog)),
                ('villager-and-seasonal-subset', ['GAFE01-r0/villager/00EB', 'GAFE01-r0/item/31D4'])]
    expected = {}
    for name, selected in profiles:
        result, _, _ = composer.compose(base, report, catalog, composer.resolve(catalog, selected))
        expected[name] = sha256(result)
    requests, errors, results = [], [], {}
    with ThreadingHTTPServer(('127.0.0.1', 0), Handler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        origin = f'http://127.0.0.1:{server.server_port}'
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--mute-audio'])
                context = browser.new_context()
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
                    return page.evaluate('''({selected, cancel}) => new Promise((resolve, reject) => {
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
                      worker.postMessage({requested: selected, n64: document.querySelector('#n64').files[0],
                        gamecube: document.querySelector('#disc').files[0]});
                    })''', {'selected': selected, 'cancel': cancel})

                cancelled = worker(profiles[-1][1], cancel=True)
                assert cancelled['type'] == 'cancelled', cancelled
                results['worker_termination'] = cancelled
                for name, selected in profiles:
                    result = worker(selected)
                    assert result['type'] == 'done', result
                    assert result['sha256'] == expected[name] == result['receipt']['output_sha256'], name
                    for key in ('enabled', 'required', 'profile_hex'):
                        assert result['receipt'][key] == composer.resolve(catalog, selected)[key], (name, key)
                    results[name] = result
                    print(json.dumps({'case': name, 'sha256': result['sha256'], 'matched_offline': True}), flush=True)
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
    out.mkdir(parents=True)
    (out/'results.json').write_bytes(composer.canonical(results))
    return {'checks': list(results)[:6], 'results_sha256': sha256((out/'results.json').read_bytes())}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--export', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.export, args.output), indent=2))
