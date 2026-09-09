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
CREATORS = all((ROOT/'build'/name/'overlay.json').is_file()
               for name in ('mail-glyph-creator','academy-score-mail-creator'))


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

    def creator_fixture(self):
        from extended_items import install as install_items
        from mail_view_patch import install as install_reader
        from npc_mail_loader import install as install_loader
        install_reader(self.native,self.replacements,self.additions,self.module,snapshots=True)
        install_items(self.native,self.additions,self.module,ROOT/'build/mapped-items-final-resource')
        install_catalog(self.native,self.additions,self.module,CATALOG,glyph_font=FONT)
        install_loader(self.native,self.replacements,self.additions,self.module,ROOT/'build/mail-glyph-creator',glyph_font=FONT)
        install_font(self.native,self.replacements,self.additions,self.module,FONT)

    @unittest.skipUnless(CREATORS,'Both current compiled creator variants required')
    def test_compiled_creator_flag_cannot_be_added_removed_or_coerced(self):
        from npc_mail_capture import validate
        for name,enabled in (('academy-score-mail-creator',False),('mail-glyph-creator',True)):
            directory = ROOT/'build'/name
            data,reloc = ((directory/n).read_bytes() for n in ('overlay.bin','relocation.bin'))
            report = json.loads((directory/'overlay.json').read_text())
            validate(data,reloc,report,self.module)
            for value in (False,0,1,'true',None):
                wrong = copy.deepcopy(report);wrong['mail_glyphs'] = value
                with self.subTest(name=name,value=value),self.assertRaises(ValueError):
                    validate(data,reloc,wrong,self.module)
            wrong = copy.deepcopy(report)
            if enabled: wrong.pop('mail_glyphs')
            else: wrong['mail_glyphs'] = True
            with self.assertRaises(ValueError): validate(data,reloc,wrong,self.module)

    @unittest.skipUnless(CREATORS,'Both current compiled creator variants required')
    def test_creator_requires_exact_font_and_catalogue_before_publication(self):
        from mail_view_patch import install as install_reader
        from npc_mail_loader import install as install_loader
        install_reader(self.native,self.replacements,self.additions,self.module,snapshots=True)
        install_catalog(self.native,self.additions,self.module,CATALOG,glyph_font=FONT)
        for fault in ('missing_font','old_font','missing_catalog','wrong_catalog'):
            replacements,additions,module = dict(self.replacements),dict(self.additions),copy.deepcopy(self.module)
            font = None if fault=='missing_font' else ROOT/'build/extended-font-cartridge' if fault=='old_font' else FONT
            if fault=='missing_catalog': additions.pop(0x030A0000)
            if fault=='wrong_catalog': additions[0x030A0000] = additions[0x03000000]
            before = copy.deepcopy((replacements,additions,module))
            with self.subTest(fault=fault),self.assertRaises(ValueError):
                install_loader(self.native,replacements,additions,module,ROOT/'build/mail-glyph-creator',glyph_font=font)
            self.assertEqual((replacements,additions,module),before)

    @unittest.skipUnless(CREATORS,'Both current compiled creator variants required')
    def test_all_system_routes_use_complete_catalogue_and_verify_actual_rom(self):
        import mother_letters,departed_letters,villager_event_letters,academy_letters,academy_score_letters
        self.creator_fixture()
        reports = []
        for owner in (mother_letters,departed_letters,villager_event_letters,academy_letters,academy_score_letters):
            report = owner.install(self.native,self.replacements,self.additions,self.module)
            self.assertEqual(report['catalog'],4)
            self.assertEqual(report['classic_templates'],list(owner.TEMPLATES))
            if 'complete_templates' in report:
                self.assertEqual(report['complete_templates'],list(owner.TEMPLATES))
                self.assertEqual(report['unavailable_templates'],[])
            self.assertFalse(any('unavailable' in part for part in report['parts']))
            reports.append((owner,report))
        built = replace_dma(self.native,self.replacements,additions=self.additions)
        verify_test_module(built,self.module)
        for owner,report in reports:
            owner.verify_installation(built,self.native,self.module,report)
            wrong = copy.deepcopy(report);wrong['catalog'] = 2
            with self.assertRaises(ValueError): owner.verify_installation(built,self.native,self.module,wrong)

    @unittest.skipUnless(CREATORS,'Both current compiled creator variants required')
    def test_system_route_refuses_missing_or_changed_installed_font_atomically(self):
        import mother_letters
        from extended_font_cartridge import VROM
        self.creator_fixture()
        for fault in ('missing','bytes','capability','configuration'):
            replacements,additions,module = dict(self.replacements),dict(self.additions),copy.deepcopy(self.module)
            if fault=='missing': additions.pop(VROM)
            elif fault=='bytes':
                blob = bytearray(additions[VROM]);blob[-1] ^= 1;additions[VROM] = bytes(blob)
            elif fault=='capability': module['extended_font']['font'].pop('mail_glyphs')
            else:
                binary = bytearray(additions[0x02800000]);binary[0x68] ^= 1;additions[0x02800000] = bytes(binary)
            before = copy.deepcopy((replacements,additions,module))
            with self.subTest(fault=fault),self.assertRaises(ValueError):
                mother_letters.install(self.native,replacements,additions,module)
            self.assertEqual((replacements,additions,module),before)


if __name__ == '__main__':
    unittest.main()
