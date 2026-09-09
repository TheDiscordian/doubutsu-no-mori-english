"""Bind complete treasure creator artifacts without repeating native batches."""

import copy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
from npc_mail_capture import validate, source_hashes, creator_imports
from npc_mail_loader import configuration
from runtime_module import resident_c_sources, runtime_source_hashes

DIRECTORY = ROOT/'build/noticeboard-treasure/article-creator'


@unittest.skipUnless((DIRECTORY/'overlay.json').is_file(), 'Local compiled treasure creator required')
class NoticeTreasureArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = (DIRECTORY/'overlay.bin').read_bytes()
        cls.reloc = (DIRECTORY/'relocation.bin').read_bytes()
        cls.report = json.loads((DIRECTORY/'overlay.json').read_text())
        cls.module = json.loads((ROOT/'build/notice-treasure-runtime/module.json').read_text())

    def test_independent_builds_and_loader_entry(self):
        self.assertEqual((len(self.data), sha256(self.data)),
                         (46592, 'eda487cce42ace3d63bbbc1709377bc7a51471f0232d11c1add8c80b059be980'))
        self.assertEqual((len(self.reloc), sha256(self.reloc)),
                         (672, '2f7a3e1fb6bc95c9c1d63fbe218f5f34581edabfeb291138eb84b71fc9b76212'))
        for filename in ('overlay.bin', 'relocation.bin', 'overlay.json'):
            self.assertEqual((DIRECTORY/filename).read_bytes(),
                             (ROOT/'build/noticeboard-treasure/article-creator-repeat'/filename).read_bytes())
        validate(self.data, self.reloc, self.report, self.module)
        config = configuration(self.data, self.reloc, self.report, self.module)
        self.assertEqual(config[1:4], [47264, 46592, 672])
        self.assertEqual(config[4], self.report['symbols']['af_notice_treasure_create'])
        text, data, rodata, bss, _ = struct.unpack_from('>5I', self.reloc)
        self.assertEqual((data, bss, text+rodata), (0, 0, len(self.data)))

    def test_unchanged_resident_code_and_complete_source_inventory(self):
        for name in ('module.bin', 'bootstrap.bin'):
            self.assertEqual((ROOT/'build/notice-treasure-runtime'/name).read_bytes(),
                             (ROOT/'build/noticeboard-runtime'/name).read_bytes())
        self.assertEqual(self.module['runtime_sources'], runtime_source_hashes(ROOT/'runtime'))
        sources = [p.relative_to(ROOT/'runtime').as_posix() for p in resident_c_sources(ROOT/'runtime')]
        self.assertNotIn('notice/treasure.c', sources)
        self.assertIn('notice/treasure.c', self.module['runtime_sources'])
        for name in ('af_crc32', 'af_mail_format', 'af_mail_record_unpack', 'af_item_name_index'):
            self.assertIn(name, self.report['imports'])
            self.assertEqual(self.report['imports'][name], int(self.module['symbols'][name], 16))

    def test_unknown_variants_and_missing_dependencies_rejected(self):
        for value in (False, 1, 'true'):
            changed = copy.deepcopy(self.report)
            changed['notice_treasure'] = value
            with self.assertRaises(ValueError): validate(self.data, self.reloc, changed, self.module)
        changed = copy.deepcopy(self.report)
        del changed['mail_glyphs']
        with self.assertRaises(ValueError): validate(self.data, self.reloc, changed, self.module)
        with self.assertRaises(ValueError): source_hashes(notice_treasure=True)
        self.assertNotIn('af_mail_format', creator_imports())

    def test_previous_creator_manifest_remains_valid(self):
        old = ROOT/'build/quest-reply-creator'
        validate((old/'overlay.bin').read_bytes(), (old/'relocation.bin').read_bytes(),
                 json.loads((old/'overlay.json').read_text()), self.module)

    def test_compiled_articles_bound_to_full_names_and_external_approval(self):
        from item_articles import verify, SIZE, NAMES_HASH
        at = self.report['symbols']['af_item_article_data']
        verify(self.data[at:at+SIZE])
        self.assertEqual(self.report['item_names_sha256'], NAMES_HASH)
        for field in ('item_names_sha256', 'item_articles_sha256'):
            report = copy.deepcopy(self.report); report[field] = '0'*64
            with self.assertRaises(ValueError): validate(self.data, self.reloc, report, self.module)
        data = bytearray(self.data); data[at+48] ^= 1
        report = copy.deepcopy(self.report); report['overlay_sha256'] = sha256(data)
        with self.assertRaises(ValueError): validate(data, self.reloc, report, self.module)


if __name__ == '__main__': unittest.main()
