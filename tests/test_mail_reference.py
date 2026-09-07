"""Source identity and unsupported-glyph failures cannot become approvals."""

from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from gc_names import rel_sections
from mail_reference import transcode, verify_semantics, SEMANTIC_FUNCTIONS
from textcodec import GLYPHS


class MailReferenceTests(unittest.TestCase):
    def test_exact_glyph_transcoding_and_complete_command_validation(self):
        tables = {'CHAR_MAP': [GLYPHS.get(i, '<unsupported>') for i in range(256)], 'CONT_SIZES': [2]*123}
        tables['CHAR_MAP'][0] = 'a'
        self.assertEqual(transcode(b'\0\xcd\x7f\x74\x7f\x75\x7f\x24', tables),
                         b'a\xcd\x7f\x74\x7f\x75\x7f\x24')
        allowed = {*range(0x24, 0x2E), *range(0x36, 0x40), 0x74, 0x75}
        for opcode in range(256):
            data = bytes((0x7F, opcode))
            if opcode in allowed:
                self.assertEqual(transcode(data, tables), data)
            else:
                with self.assertRaises(ValueError):
                    transcode(data, tables)
        for data in (b'\x7f', b'\x80'):
            with self.assertRaises(ValueError):
                transcode(data, tables)
        tables['CONT_SIZES'][0x75] = 3
        with self.assertRaisesRegex(ValueError, 'length'):
            transcode(b'\x7f\x75', tables)

    @unittest.skipUnless((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').is_file(),
                         'Local extracted English executable required')
    def test_every_guarded_reference_function_rejects_mutation(self):
        rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
        self.assertEqual(verify_semantics(rel, symbols), SEMANTIC_FUNCTIONS)
        text_offset = rel_sections(rel)[1][0]
        for name in SEMANTIC_FUNCTIONS:
            match = re.search(r'^'+re.escape(name)+r' = \.text:0x([0-9A-Fa-f]+);', symbols, re.MULTILINE)
            self.assertIsNotNone(match)
            damaged = bytearray(rel)
            damaged[text_offset+int(match[1], 16)] ^= 1
            with self.assertRaisesRegex(ValueError, name):
                verify_semantics(bytes(damaged), symbols)
