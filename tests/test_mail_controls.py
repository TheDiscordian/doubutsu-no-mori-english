"""Dialogue-only commands must never reach the separate mail assembly loop."""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from mail_controls import BANKS, NATIVE_CODES, native_handlers
from textvalidate import validate_entry
from test_retail import ROM_PATH


class MailControlTests(unittest.TestCase):
    def test_every_opcode_has_an_independent_mail_capability_check(self):
        info = [(2, 0)]*0x7B
        for bank in BANKS:
            for opcode in range(len(info)):
                data = b"\x7f"+bytes([opcode])
                if opcode in NATIVE_CODES:
                    validate_entry(data, data, info, bank, resident_runtime=True)
                else:
                    with self.assertRaisesRegex(ValueError, "Unsupported native mail command"):
                        validate_entry(data, data, info, bank, resident_runtime=True)
        # The same opcode still has its intended main-dialogue interpretation.
        validate_entry(b"\x7f\x75", b"\x7f\x75", info, "message", resident_runtime=True)

    @unittest.skipUnless(ROM_PATH.is_file(), "Native dispatch table is a local-only input")
    def test_all_twenty_handlers_match_the_actual_native_table(self):
        handlers = native_handlers(ROM_PATH.read_bytes())
        self.assertEqual(set(handlers), set(NATIVE_CODES))
        self.assertEqual((handlers[0x24], handlers[0x3F]), (0x800930B0, 0x800933F0))
