"""The new catalogue requires its exact font and retains old cartridge resources."""

import copy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,replace_dma,sha256
from build_mail_glyph_catalog import bundle
from extended_font_cartridge import install as install_font
from font import make_halfwidth
from mail_catalog import install as install_catalog
from runtime_module import add_runtime_module,verify_test_module
from test_retail import ROM_PATH

MODULE = ROOT/'build/mail-glyph-runtime'
CATALOG = ROOT/'build/mail-glyph-resources'
FONT = ROOT/'build/mail-font-cartridge'


@unittest.skipUnless(ROM_PATH.is_file() and (MODULE/'module.json').is_file()
                     and (CATALOG/'catalog.json').is_file() and (FONT/'font.json').is_file(),
                     'Locally built complete glyph resources required')
class MailGlyphInstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = ROM_PATH.read_bytes()

    def setUp(self):
        self.replacements,_ = make_halfwidth(self.native)
        self.additions,self.module = add_runtime_module(self.native,self.replacements,MODULE)

    def test_missing_base_only_or_stale_font_fails_without_configuring_catalogues(self):
        before = dict(self.additions)
        for font in (None,ROOT/'build/extended-font-cartridge'):
            with self.assertRaises(ValueError):
                install_catalog(self.native,self.additions,self.module,CATALOG,glyph_font=font)
            self.assertEqual(self.additions,before)
        changed = copy.deepcopy(self.module)
        changed['runtime_sources']['mail/glyph.h'] = '0'*64
        with self.assertRaises(ValueError):
            install_catalog(self.native,self.additions,changed,CATALOG,glyph_font=FONT)
        self.assertEqual(self.additions,before)

    def test_complete_bundle_retains_old_resources_and_has_exact_startup_font(self):
        report = install_catalog(self.native,self.additions,self.module,CATALOG,glyph_font=FONT)
        font = install_font(self.native,self.replacements,self.additions,self.module,FONT)
        self.assertEqual(font['blob_sha256'],report['glyph_font_sha256'])
        self.assertEqual(report['glyph_catalog']['catalog'],4)
        self.assertEqual(self.additions[0x03000000],(ROOT/'build/mail-catalog/catalog.bin').read_bytes())
        self.assertEqual(self.additions[0x03050000],(ROOT/'build/fortune-slip-resources/fortune-catalog.bin').read_bytes())
        built = replace_dma(self.native,self.replacements,additions=self.additions)
        verify_test_module(built,self.module)
        files = by_vrom(built)
        for vrom,data in self.additions.items():
            self.assertEqual(files[vrom].extract(built),data)

    def test_bundle_reproduction_and_untracked_or_corrupted_resources_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            hashes = bundle(self.native,ROOT/'build/fortune-slip-resources',ROOT/'build/mail-glyph-catalog',out)
            for name,digest in hashes.items():
                self.assertEqual(digest,sha256((CATALOG/name).read_bytes()))
            manifest = json.loads((out/'catalog.json').read_text())
            for mutation in ('hash','untracked','address','identity'):
                changed = copy.deepcopy(manifest)
                if mutation == 'hash': changed['glyph_catalog']['sha256'] = '0'*64
                elif mutation == 'untracked': del changed['glyph_catalog']
                elif mutation == 'address': changed['glyph_catalog']['vrom'] = '03050000'
                else: changed['glyph_catalog']['catalog'] = 3
                (out/'catalog.json').write_text(json.dumps(changed))
                with self.assertRaises(ValueError):
                    install_catalog(self.native,self.additions,self.module,out,glyph_font=FONT)
            (out/'catalog.json').write_text(json.dumps(manifest))
            data = bytearray((out/'glyph-catalog.bin').read_bytes());data[-1] ^= 1
            (out/'glyph-catalog.bin').write_bytes(data)
            with self.assertRaises(ValueError):
                install_catalog(self.native,self.additions,self.module,out,glyph_font=FONT)


if __name__ == '__main__':
    unittest.main()
