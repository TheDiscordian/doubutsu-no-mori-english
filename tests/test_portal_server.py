"""Read-only export boundaries using generated synthetic web files."""
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
import sys
import tempfile
from threading import Thread
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from serve_portal import StaticPortal


class PortalServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='af-portal-server-')
        cls.parent = Path(cls.temporary.name)
        cls.site = cls.parent/'site'; cls.site.mkdir()
        (cls.site/'index.html').write_text('<!doctype html><title>test</title>')
        (cls.site/'module.mjs').write_text('export const test = 1;')
        (cls.site/'folder').mkdir()
        (cls.parent/'private.txt').write_text('Not a web resource')
        (cls.site/'outside').symlink_to(cls.parent/'private.txt')
        class Quiet(StaticPortal):
            def log_message(self, *args):
                pass
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(cls.site)))
        cls.thread = Thread(target=cls.server.serve_forever, daemon=True); cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.thread.join(timeout=3); cls.server.server_close()
        cls.temporary.cleanup()

    def test_static_headers_and_module_type(self):
        with urlopen(self.url+'/module.mjs', timeout=5) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers['Content-Type'], 'text/javascript')
            self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
            self.assertIn("connect-src 'self'", response.headers['Content-Security-Policy'])
            self.assertIn('frame-src https://www.youtube-nocookie.com;', response.headers['Content-Security-Policy'])
            self.assertEqual(response.headers['Cache-Control'], 'no-store')

    def test_no_uploads(self):
        for method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            with self.assertRaises(HTTPError) as error:
                urlopen(Request(self.url+'/', data=b'test', method=method), timeout=5)
            self.assertEqual(error.exception.code, 405)
            error.exception.close()

    def test_no_traversal_symlinks_or_directory_listing(self):
        for path in ('/%2e%2e/private.txt', '/outside', '/folder/'):
            with self.assertRaises(HTTPError) as error:
                urlopen(self.url+path, timeout=5)
            self.assertEqual(error.exception.code, 403)
            error.exception.close()


if __name__ == '__main__':
    unittest.main()
