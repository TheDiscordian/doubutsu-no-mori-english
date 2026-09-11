"""Visitor-facing copy and measured input checksums; no cartridge rebuild."""
import hashlib
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import normalise_rom, verified_rom
from build_portal import DOWNLOAD_NAME, SAVE_NOTE


class PortalCopyTests(unittest.TestCase):
    def test_visitor_copy_and_branding(self):
        html = (ROOT/'web/index.html').read_text()
        script = (ROOT/'web/app.mjs').read_text()
        for old in ('V1 Final', 'RC3', 'LOCAL PREVIEW', 'local preview', 'Audio starts muted',
                    'save filename', 'corrected V2', 'Is this the public release?'):
            self.assertNotIn(old, html+script+SAVE_NOTE)
        self.assertIn('<title>Animal Crossing N64 · English Translation</title>', html)
        self.assertIn('<span>Animal Crossing N64<small>ENGLISH TRANSLATION</small></span>', html)
        self.assertEqual(DOWNLOAD_NAME, 'Animal Crossing N64 - English.z64')
        self.assertIn('id="trailer-play"', html)
        self.assertIn('https://www.youtube.com/watch?v=UloFru4K4Q8', html)
        self.assertNotIn('<video', html)
        self.assertNotIn('<iframe', html)
        self.assertNotIn('media/trailer.mp4', html)
        self.assertIn('https://www.youtube-nocookie.com/embed/UloFru4K4Q8?autoplay=1&mute=0', script)
        self.assertIn("frame.referrerPolicy = 'strict-origin-when-cross-origin'", script)
        self.assertNotIn('autoplay', html)
        self.assertNotIn("$('save-note')", script)
        self.assertNotIn("$('build-label')", script)

    @unittest.skipUnless((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').is_file(), 'Private input required')
    def test_all_displayed_md5s_match_verified_inputs(self):
        html = (ROOT/'web/index.html').read_text()
        hashes = dict(re.findall(r'data-input-md5="([^"]+)">([0-9a-f]{32})</code>', html))
        self.assertEqual(set(hashes), {'z64', 'v64', 'n64', 'ciso', 'iso-full', 'iso-scrubbed'})
        native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
        for fmt, order in (('z64', (0,1,2,3)), ('v64', (1,0,3,2)), ('n64', (3,2,1,0))):
            raw = bytearray(len(native))
            for i, j in enumerate(order):
                raw[i::4] = native[j::4]
            self.assertEqual(normalise_rom(raw), native)
            self.assertEqual(hashlib.md5(raw).hexdigest(), hashes[fmt])
        with (ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso').open('rb') as stream:
            self.assertEqual(hashlib.file_digest(stream, 'md5').hexdigest(), hashes['ciso'])
        iso = ROOT/'build/web-portal-check-03/donor.iso'
        if iso.is_file():
            with iso.open('rb') as stream:
                self.assertEqual(hashlib.file_digest(stream, 'md5').hexdigest(), hashes['iso-scrubbed'])
        self.assertEqual(hashes['iso-full'], '7853049ccd0c1e2bffeb5b12393a5409')
        self.assertIn('https://www.gametdb.com/Wii/GAFE01', html)
        self.assertNotIn('different checksums and still work', html)


if __name__ == '__main__':
    unittest.main()
