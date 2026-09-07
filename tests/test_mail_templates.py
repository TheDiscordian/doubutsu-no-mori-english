"""Snapshot budgets cover every field union, not a sample of random letters."""

import itertools
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from audit_mail_templates import audit, reachable_fields, reply_groups, template_fields
from mail_controls import NATIVE_CODES
from test_retail import ROM_PATH
from aflib import CODE_RAM, CODE_VROM, by_vrom
from unittest.mock import patch


class MailTemplateTests(unittest.TestCase):
    def test_all_mail_commands_and_malformed_tokens(self):
        for opcode in range(256):
            data = b"x\x7f"+bytes([opcode])+b"y"
            if opcode in NATIVE_CODES:
                index = opcode-0x24 if opcode <= 0x2D else opcode-0x36+10
                self.assertEqual(template_fields(data), frozenset((index,)))
            elif opcode in (0x74, 0x75):
                self.assertEqual(template_fields(data), frozenset())
            else:
                with self.assertRaises(ValueError):
                    template_fields(data)
        with self.assertRaisesRegex(ValueError, "Truncated"):
            template_fields(b"text\x7f")
        self.assertEqual(template_fields(b"\x80\xcd\xff"), frozenset())

    def test_reachable_unions_match_every_explicit_combination_and_witness(self):
        parts = [[(i, frozenset((i % 3, (i+j) % 5))) for i in range(4)] for j in range(5)]
        expected = {frozenset().union(*(fields for _, fields in combination))
                    for combination in itertools.product(*parts)}
        result = reachable_fields(parts)
        self.assertEqual(set(result), expected)
        for fields, witness in result.items():
            self.assertEqual(fields, frozenset().union(*(dict(part)[index] for part, index in zip(parts, witness))))
        with self.assertRaises(ValueError):
            reachable_fields([[]])

    @unittest.skipUnless(ROM_PATH.is_file(), "Native reply code is a local-only input")
    def test_group_limits_are_bound_to_native_code_and_tables(self):
        rom = ROM_PATH.read_bytes()
        self.assertEqual(sorted(sum(reply_groups(rom), ())), list(range(0, 384, 32)))
        code = bytearray(by_vrom(rom)[CODE_VROM].extract(rom))
        class Entry:
            def extract(self, ignored):
                return code
        for address in (0x800A8E88, 0x800A8E98, 0x800A8F0C, 0x8010B880, 0x8010B850, 0x8010B868):
            code[address-CODE_RAM+3] ^= 1
            with patch("audit_mail_templates.by_vrom", return_value={CODE_VROM: Entry()}):
                with self.assertRaises(ValueError):
                    reply_groups(rom)
            code[address-CODE_RAM+3] ^= 1

    @unittest.skipUnless(ROM_PATH.is_file() and (ROOT/"build/gamecube/files/forest_1st.arc.unpacked/data/mail_data.bin").is_file(),
                         "English reference letter banks are local-only")
    def test_all_actual_english_template_groups_and_static_letters(self):
        report = audit(ROM_PATH.read_bytes(), ROOT/"build/gamecube/files/forest_1st.arc.unpacked/data")
        self.assertEqual(report["summary"]["composite_groups"], 12)
        self.assertTrue(report["summary"]["all_composite_groups_fit"])
        self.assertEqual(report["summary"]["max_composite_snapshot_bytes"], 122)
        self.assertEqual(report["summary"]["classic_require_actual_field_bounds"], [1])
        self.assertEqual(report["summary"]["classic_fit_at_max_field_width"], 981)
        self.assertEqual(report["summary"]["native_numeric_records_fit_at_max_field_width"], 543)
