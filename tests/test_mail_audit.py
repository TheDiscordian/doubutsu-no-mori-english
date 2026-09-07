"""Mail capacity evidence is separate from approval to widen saved records."""

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from aflib import CODE_RAM, CODE_VROM, by_vrom
from audit_mail import CAPACITY_GUARDS, audit, capacity_evidence
from test_retail import ROM_PATH
from mail_viewer import GUARDS as VIEWER_GUARDS, RAM as VIEWER_RAM, VROM as VIEWER_VROM, evidence as viewer_evidence


@unittest.skipUnless(ROM_PATH.is_file(), "Native mail code is a local-only input")
class MailAuditTests(unittest.TestCase):
    def test_native_viewer_limits_and_mutation_guards(self):
        rom = ROM_PATH.read_bytes()
        result = viewer_evidence(rom)
        self.assertEqual(result["embedded_mail_offset"]+164, result["persistent_mail_pointer_offset"])
        self.assertEqual(result["text_offsets"], {"header": 50, "body": 60, "footer": 156})
        self.assertEqual((result["line_character_limit"], result["body_lines"]), (16, 6))
        data = bytearray(by_vrom(rom)[VIEWER_VROM].extract(rom))
        class Entry:
            def extract(self, ignored):
                return data
        for address in VIEWER_GUARDS:
            data[address-VIEWER_RAM+3] ^= 1
            with patch("mail_viewer.by_vrom", return_value={VIEWER_VROM: Entry()}):
                with self.assertRaisesRegex(ValueError, "mail-viewer"):
                    viewer_evidence(rom)
            data[address-VIEWER_RAM+3] ^= 1

    def test_native_mail_size_and_every_instruction_guard(self):
        rom = ROM_PATH.read_bytes()
        result = capacity_evidence(rom)
        self.assertEqual(result["text_start"]+result["header_bytes"], result["body_offset"])
        self.assertEqual(result["body_offset"]+result["body_bytes"], result["footer_offset"])
        self.assertEqual(result["footer_offset"]+result["footer_bytes"], result["record_bytes"])
        self.assertEqual((result["record_bytes"], result["body_bytes"]), (164, 96))
        code = bytearray(by_vrom(rom)[CODE_VROM].extract(rom))
        class Entry:
            def extract(self, rom):
                return code
        for address in CAPACITY_GUARDS:
            offset = address-CODE_RAM
            code[offset+3] ^= 1
            with patch("audit_mail.by_vrom", return_value={CODE_VROM: Entry()}):
                with self.assertRaisesRegex(ValueError, "capacity instruction"):
                    capacity_evidence(rom)
            code[offset+3] ^= 1

    @unittest.skipUnless((ROOT/"build/gamecube/text/mail.jsonl").is_file(), "GameCube letter data are local-only")
    def test_reference_inventory_keeps_gc_extra_records_and_consumer_counts_distinct(self):
        result = audit(ROM_PATH.read_bytes(), ROOT/"build/gamecube/text")
        for name, count in (("load_letter", 17), ("load_letter_sized_edges", 3),
                             ("load_header", 2), ("load_footer", 2), ("load_body", 2),
                             ("load_composite_letter", 1), ("set_message_mail", 2),
                             ("set_free_string", 54), ("clear_mail", 39), ("copy_mail", 30)):
            self.assertEqual(len(result["references"][name]["callers"]), count)
        self.assertTrue(all(not r["literal_pointers"] for r in result["references"].values()))
        for name in ("super", "mail", "ps"):
            bank = result["banks"][name]
            self.assertEqual((bank["native_records"], bank["reference_records"]), (544, 982))
            self.assertEqual(bank["reference_records_with_native_numeric_id"], 544)
            self.assertGreater(bank["reference_raw_records_exceeding_destination"], 0)
        self.assertTrue(all(result["banks"][name]["native_destination_bytes"] is None
                            for name in ("superz", "maila", "mailb", "mailc", "psz")))
