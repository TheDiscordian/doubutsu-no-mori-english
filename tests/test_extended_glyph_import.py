"""Dialogue capability, exact English source reconstruction, and byte budgets."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256, verified_rom
from glyph_codes import ENCODINGS, WIDTHS
from gc_adapter import adapt_reference
from gc_text import decoder_tables, decode_gc
from reference_content import (adapt_content_reference, validate_content_approval,
                               validate_content_candidate, validate_glyph_candidate)
from reference_matches import load_matches
from runtime_module import module_command_info, add_runtime_module
from textbanks import Bank, banks
from textcodec import encode, decode, tokenize
from textvalidate import expanded_bound, layout_issues, validate_entry
from test_retail import ROM_PATH

IDS = {'message:'+n for n in '04D2 04FA 08A2 08A6 0A15 0E2A'.split()}
CURRENT_MODULE = ROOT/'build/notice-seasonal-runtime'


class GlyphImportTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x77; self.info[3] = (3, 0)
        self.text = 'A;☃/{cmd:7F0380}\n{cmd:7F00}'
        self.native = encode(self.text, self.info, extended_glyphs=True)
        self.original = b'A\xd0\xab\xae\x7f\x03\x80\xcd\x7f\x00'
        self.source = b'Native\x7f\x00'
        self.reference = {'id': 'message:0000', 'text': self.text, 'sha256': sha256(self.original)}
        self.record = {'id': 'message:0000', 'reference_id': 'message:0000',
                       'source_sha256': sha256(self.source), 'reference_sha256': sha256(self.original),
                       'complete_reference': {'adapted_sha256': sha256(self.native),
                                              'gamecube_glyph_offsets': [1, 3, 5]}}

    def test_only_explicit_capability_encodes_registered_unicode(self):
        for character, encoded in ENCODINGS.items():
            with self.assertRaisesRegex(ValueError, 'Unrepresentable'):
                encode(character, self.info)
            self.assertEqual(encode(character, self.info, extended_glyphs=True), encoded)
            self.assertEqual(encode(decode(encoded, self.info), self.info), encoded)
        with self.assertRaises(ValueError): encode('☂', self.info, extended_glyphs=True)

    def test_only_main_dialogue_can_enable_complete_known_tokens(self):
        for bank in ('message', 'select', 'string', 'mail', 'npc_names'):
            with self.assertRaises(ValueError):
                validate_entry(self.source, self.native, self.info, bank, 'presentation', resident_runtime=True)
            if bank != 'message':
                with self.assertRaises(ValueError):
                    validate_entry(self.source, self.native, self.info, bank, 'presentation',
                                   resident_runtime=True, extended_glyphs=True)
        validate_entry(self.source, self.native, self.info, 'message', 'presentation',
                       resident_runtime=True, extended_glyphs=True)
        for payload in (b'\x80', b'\x80\x42', b'\x80\x7f'):
            with self.assertRaises(ValueError): expanded_bound(payload, self.info, extended_glyphs=True)
        with self.assertRaises(ValueError):
            validate_entry(self.source, self.native, self.info, 'message', 'presentation', extended_glyphs=True)

    def test_expansion_counts_both_bytes_and_layout_uses_resource_widths(self):
        self.assertEqual(expanded_bound(self.native, self.info, extended_glyphs=True), len(self.native)+16)
        for token, width in WIDTHS.items():
            self.assertEqual(layout_issues(token, self.info, {}, max_width=width, extended_glyphs=True), [])
            self.assertIn(f'page_0_line_1_width_{width}',
                          layout_issues(token, self.info, {}, max_width=width-1, extended_glyphs=True))
        for length in (1006, 1007):
            payload = b'A'*length+b'\x80\xd0'
            if length == 1006:
                validate_entry(b'A', payload, self.info, 'message', resident_runtime=True, extended_glyphs=True)
            else:
                with self.assertRaisesRegex(ValueError, '1024'):
                    validate_entry(b'A', payload, self.info, 'message', resident_runtime=True, extended_glyphs=True)

    def test_complete_disc_hash_preserves_command_arguments_and_each_token(self):
        self.assertEqual(adapt_content_reference(self.reference, self.source, self.record, self.info), (self.text, []))
        validate_glyph_candidate(self.record['id'], self.source, self.native, {self.record['id']:self.record}, self.info)
        with self.assertRaises(ValueError): validate_glyph_candidate(self.record['id'], self.source, self.native, {}, self.info)
        for offsets in ([1], [2, 3, 5], [1, 3, 5, 9]):
            record = deepcopy(self.record); record['complete_reference']['gamecube_glyph_offsets'] = offsets
            with self.assertRaises(ValueError): adapt_content_reference(self.reference, self.source, record, self.info)
        with self.assertRaises(ValueError):
            adapt_content_reference({**self.reference, 'text': self.text+' '}, self.source, self.record, self.info)

    def test_offsets_and_other_permissions_cannot_be_combined(self):
        for value in ([], None, [True], [-1], [1024], [1, 1], [3, 1]):
            record = deepcopy(self.record); record['complete_reference']['gamecube_glyph_offsets'] = value
            with self.assertRaises(ValueError): validate_content_approval(record)
        for key in ('spans', 'native_mood', 'native_random', 'gamecube_plus_offsets'):
            record = deepcopy(self.record); record['complete_reference'][key] = [1]
            with self.assertRaises(ValueError): validate_content_approval(record)


@unittest.skipUnless(ROM_PATH.is_file() and (ROOT/'build/gamecube/text/message.jsonl').is_file(),
                     'Supplied game data stays local')
class RetailGlyphImportTests(unittest.TestCase):
    @unittest.skipUnless((ROOT/'build/extended-font-cartridge/font.json').is_file()
                         and (CURRENT_MODULE/'module.json').is_file(), 'Generated runtime stays local')
    def test_builder_requires_verified_resource_even_if_edit_metadata_is_omitted(self):
        from build import apply_translations
        from font import make_halfwidth
        from english_runtime import make_english_runtime, ChoiceLayout
        rom=verified_rom(ROM_PATH.read_bytes())
        replacements,_=make_halfwidth(rom)
        module_path=CURRENT_MODULE;font_path=ROOT/'build/extended-font-cartridge'
        additions,module=add_runtime_module(rom,replacements,module_path)
        runtime,_=make_english_runtime(rom,replacements,ChoiceLayout(**module['choice_layout']))
        replacements.update(runtime)
        matches=load_matches(ROOT/'translations/reference_matches.json')
        references={r['id']:r for r in map(json.loads,(ROOT/'build/gamecube/text/message.jsonl').read_text().splitlines())}
        edits=[{'id':id,'source_sha256':matches[id]['source_sha256'],
                'translation':references[id]['text'],'control_policy':'reference_layout'} for id in sorted(IDS)]
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'edits.json';path.write_text(json.dumps(edits))
            kwargs={'english_runtime':True,'runtime_module':module_path,'module_additions':additions}
            with self.assertRaises(ValueError): apply_translations(rom,dict(replacements),path,**kwargs)
            with self.assertRaises((ValueError,FileNotFoundError)):
                apply_translations(rom,dict(replacements),path,extended_font=Path(tmp),**kwargs)
            changed=dict(replacements)
            count,_=apply_translations(rom,changed,path,extended_font=font_path,**kwargs)
            self.assertEqual(count,6)
            from extended_font_cartridge import planned_capability,verify_configuration,install,VROM
            from runtime_layout import MODULE_VROM
            original=dict(additions)
            planned_capability(rom,replacements,additions,module,font_path)
            self.assertEqual(additions,original);self.assertNotIn('extended_font',module)
            configured=dict(additions);report=deepcopy(module)
            install(rom,changed,configured,report,font_path)
            verify_configuration(configured[MODULE_VROM],configured[VROM],report)
            for offset in range(0x68,0x88,4):
                bad=bytearray(configured[MODULE_VROM]);bad[offset]^=1
                with self.assertRaises(ValueError): verify_configuration(bytes(bad),configured[VROM],report)
            bad=bytearray(configured[VROM]);bad[100]^=1
            with self.assertRaises(ValueError): verify_configuration(configured[MODULE_VROM],bytes(bad),report)

    def test_all_six_complete_source_references_and_unchanged_presentation(self):
        rom = verified_rom(ROM_PATH.read_bytes()); info = module_command_info(rom)
        sources = next(b for b in banks(rom) if b.name == 'message').entries()
        base = ROOT/'build/gamecube/files/forest_2nd.arc.unpacked/data'
        originals = Bank('message', 0, 0, (base/'message_data.bin').read_bytes(),
                         (base/'message_data_table.bin').read_bytes()).entries()
        gc = {r['id']:r for r in map(json.loads,(ROOT/'build/gamecube/text/message.jsonl').read_text().splitlines())}
        matches = load_matches(ROOT/'translations/reference_matches.json')
        selected = {id for id,r in matches.items() if 'gamecube_glyph_offsets' in r.get('complete_reference', {})}
        self.assertEqual(selected, IDS)
        decoder = decoder_tables(ROOT/'local/ac-decomp/tools/msg_tool.py')
        for id in sorted(IDS):
            n = int(id[8:], 16); source, original, reference = sources[n], originals[n], gc[id]
            self.assertEqual(sha256(original), reference['sha256'])
            self.assertEqual(decode_gc(original, decoder), reference['text'])
            text, edits = adapt_content_reference(reference, source, matches[id], info)
            self.assertEqual(edits, []); self.assertEqual(text, reference['text'])
            final, _ = adapt_reference(text, source, info, 'reference_layout', True, extended_glyphs=True)
            self.assertEqual(final, text)
            data = encode(text, info, extended_glyphs=True)
            self.assertEqual(b''.join(t.data[1:] if t.kind == 'glyph' else t.data
                                     for t in tokenize(data, info)), original)
            validate_content_candidate(id, source, data, matches)
            validate_entry(source, data, info, 'message', 'reference_layout', resident_runtime=True, extended_glyphs=True)


if __name__ == '__main__': unittest.main()
