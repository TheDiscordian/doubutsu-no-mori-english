"""Read-only loopback server for an exported static portal, never the repository."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

CSP = ("default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; "
       "media-src 'self' blob:; frame-src https://www.youtube-nocookie.com; "
       "connect-src 'self'; worker-src 'self'; object-src 'none'; "
       "base-uri 'self'; form-action 'none'; frame-ancestors 'none'")


class StaticPortal(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, '.mjs': 'text/javascript',
                      '.svg': 'image/svg+xml', '.webp': 'image/webp'}

    def send_head(self):
        raw = unquote(urlsplit(self.path).path)
        target = (Path(self.directory)/raw.lstrip('/')).resolve()
        if '\\' in raw or not target.is_relative_to(Path(self.directory).resolve()):
            self.send_error(403); return None
        return super().send_head()

    def list_directory(self, path):
        self.send_error(403, 'Directory listing is disabled'); return None

    def end_headers(self):
        self.send_header('Content-Security-Policy', CSP)
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Cross-Origin-Resource-Policy', 'same-origin')
        super().end_headers()

    def do_POST(self):
        self.send_error(405, 'This static server accepts no uploads')

    do_PUT = do_PATCH = do_DELETE = do_POST


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8073)
    args = parser.parse_args()
    root = args.directory.resolve()
    if not (root/'index.html').is_file() or not (root/'release/manifest.json').is_file():
        raise ValueError('Serve only a completed portal export with its release manifest')
    if any(p.suffix.lower() in {'.z64', '.n64', '.v64', '.iso', '.gcm', '.ciso', '.fla', '.sra'}
           or p.is_symlink() for p in root.rglob('*')):
        raise ValueError('Portal exports must not contain ROMs, saves, or symbolic links')
    handler = partial(StaticPortal, directory=str(root))
    with ThreadingHTTPServer(('127.0.0.1', args.port), handler) as server:
        print(f'Animal Forest portal: http://127.0.0.1:{args.port}/', flush=True)
        server.serve_forever()


if __name__ == '__main__':
    main()
