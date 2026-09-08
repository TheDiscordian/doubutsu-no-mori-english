"""Reviewed menu adaptations preserve native actions and complete English text."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from aflib import sha256
from build import apply_translations
from gc_adapter import adapt_reference
from reference_choices import adapt_choice_reference, validate_choice_approval, validate_choice_candidate
from reference_matches import load_matches
from runtime_module import module_command_info
from textbanks import banks
from textcodec import decode, encode, tokenize
from textvalidate import validate_entry
from test_retail import ROM_PATH


class ReferenceChoiceTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x61
        self.info[0x18] = (10, 0)
        self.before = bytes.fromhex("7F18000A01C40009000B")
        self.after = bytes.fromhex("7F180009000A01C4000B")
        self.source = b"Native"+self.after+b"\x7f\x01"
        self.raw = b"English\xcd"+self.before+b"\x7f\x01"
        self.expected = b"English\xcd"+self.after+b"\x7f\x01"
        self.reference = {"id": "message:0000", "sha256": sha256(self.raw), "text": decode(self.raw, self.info)}
        self.record = {"id": "message:0000", "reference_id": "message:0000",
                       "source_sha256": sha256(self.source), "reference_sha256": sha256(self.raw),
                       "native_choices": {"offset": 8, "reference_command": self.before.hex().upper(),
                                          "native_command": self.after.hex().upper(),
                                          "adapted_sha256": sha256(self.expected)}}

    def test_exact_native_menu_and_untouched_surrounding_reference(self):
        text, changes = adapt_choice_reference(self.reference, self.source, self.record, self.info)
        self.assertEqual(encode(text, self.info), self.expected)
        self.assertEqual(changes[0]["operation"], "preserve_approved_native_choices")
        validate_choice_candidate(self.record["id"], self.source, self.expected, {self.record["id"]: self.record})
        validate_entry(self.source, self.expected, self.info, "message", "reference_layout")
        self.assertEqual(adapt_choice_reference(self.reference, self.source, None, self.info),
                         (self.reference["text"], []))

    def test_source_reference_offset_and_payload_guards(self):
        for ref, source in ((self.reference, b"Other"),
                            ({**self.reference, "id": "message:0001"}, self.source),
                            ({**self.reference, "sha256": "0"*64}, self.source),
                            ({**self.reference, "text": "Other"}, self.source)):
            with self.assertRaisesRegex(ValueError, "Stale"):
                adapt_choice_reference(ref, source, self.record, self.info)
        for rule in ({"offset": 7}, {"native_command": "7F180008000A01C4000B"}):
            record = deepcopy(self.record)
            record["native_choices"].update(rule)
            with self.assertRaisesRegex(ValueError, "unique native/reference menu"):
                adapt_choice_reference(self.reference, self.source, record, self.info)
        for candidate in (self.raw, self.expected+b" ", self.expected.replace(b"\xcd", b" ")):
            with self.assertRaisesRegex(ValueError, "complete approval"):
                validate_choice_candidate(self.record["id"], self.source, candidate, {self.record["id"]: self.record})
        doubled = self.source+self.after
        with self.assertRaisesRegex(ValueError, "unique native/reference menu"):
            adapt_choice_reference(self.reference, doubled,
                                   {**self.record, "source_sha256": sha256(doubled)}, self.info)

    def test_choice_approval_cannot_add_actions_or_other_controls(self):
        for rule in ({"offset": True}, {"offset": -1}, {"offset": 1024},
                     {"adapted_sha256": None}, {"native_command": "7F0E0001"},
                     {"native_command": "7F1600010002"}, {"native_command": "7F180001"},
                     {"native_command": self.before.hex().upper()}, {"reference_command": []},
                     {"unapproved": True}):
            record = deepcopy(self.record)
            record["native_choices"].update(rule)
            with self.assertRaises(ValueError):
                validate_choice_approval(record)
        with self.assertRaises(ValueError):
            validate_choice_approval({**self.record, "controller": {}})

    def test_reference_article_is_retained_until_the_existing_audited_adapter(self):
        reference_info = self.info+[(0, 0)]*(0x75-len(self.info))
        reference_info[0x74] = (2, 0)
        source = b'Native \x7f\x31'+self.after+b'\x7f\x01'
        raw = b'English \x7f\x74\x7f\x31'+self.before+b'\x7f\x01'
        expected = b'English \x7f\x31'+self.after+b'\x7f\x01'
        reference = {'id': self.record['id'], 'sha256': sha256(raw), 'text': decode(raw, reference_info)}
        record = deepcopy(self.record)
        record.update(source_sha256=sha256(source), reference_sha256=sha256(raw))
        record['native_choices'].update(offset=raw.index(self.before), adapted_sha256=sha256(expected))
        text, _ = adapt_choice_reference(reference, source, record, self.info)
        self.assertIn('{cmd:7F74}{cmd:7F31}', text)
        with self.assertRaisesRegex(ValueError, 'Unsupported command 7F74'):
            encode(text, self.info)
        text, changes = adapt_reference(text, source, self.info, 'reference_text')
        self.assertEqual(encode(text, self.info), expected)
        self.assertEqual([r['operation'] for r in changes], ['remove_redundant_cutarticle'])
        validate_choice_candidate(record['id'], source, expected, {record['id']: record})
        # Parsing the reference is not permission to erase arbitrary instances.
        with self.assertRaisesRegex(ValueError, 'Unsupported command 7F74'):
            adapt_reference(reference['text'].replace('{cmd:7F74}{cmd:7F31}',
                '{cmd:7F74}A{cmd:7F31}'), source, self.info, 'reference_text')

    @unittest.skipUnless(ROM_PATH.is_file() and (ROOT/"build/gamecube/text/message.jsonl").is_file(),
                         "Retail and English reference inputs remain local")
    def test_all_approved_menu_records_and_native_price_label(self):
        rom = ROM_PATH.read_bytes()
        info = module_command_info(rom)
        source_banks = {b.name: b.entries() for b in banks(rom)}
        refs = {r["id"]: r for r in map(json.loads, (ROOT/"build/gamecube/text/message.jsonl").read_text().splitlines())}
        matches = load_matches(ROOT/"translations/reference_matches.json")
        approved = [r for r in matches.values() if "native_choices" in r]
        self.assertEqual(len(approved), 159)
        for record in approved:
            source = source_banks["message"][int(record["id"].split(":")[1], 16)]
            text, _ = adapt_choice_reference(refs[record["reference_id"]], source, record, info)
            text, _ = adapt_reference(text, source, info, "reference_layout", resident_runtime=True)
            output = encode(text, info)
            validate_choice_candidate(record["id"], source, output, matches)
            validate_entry(source, output, info, "message", "reference_layout", resident_runtime=True)
            def choices(data):
                return [t.data for t in tokenize(data, info) if t.kind == "cmd" and 0x16 <= t.data[1] <= 0x18]
            self.assertEqual(choices(output), choices(source))
        edits = [r for r in json.loads((ROOT/"translations/n64-shop-menus.json").read_text())
                 if r["id"].startswith("select:")]
        self.assertEqual([r["id"] for r in edits], ["select:0009"])
        source = source_banks["select"][9]
        self.assertEqual(edits[0]["source_sha256"], sha256(source))
        self.assertEqual(edits[0]["translation"], "Turnip prices?")
        validate_entry(source, encode(edits[0]["translation"], info), info, "select", choice_bytes=20, resident_runtime=True)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"unadapted.json"
            record = matches["message:1092"]
            path.write_text(json.dumps([{"id": record["id"], "source_sha256": record["source_sha256"],
                                         "translation": refs[record["id"]]["text"], "control_policy": "reference_layout"}]))
            with self.assertRaisesRegex(ValueError, "Native-choice candidate"):
                apply_translations(rom, {}, path)

    @unittest.skipUnless(ROM_PATH.is_file(), "Retail ROM remains a local test input")
    def test_native_shop_drafts_preserve_all_commands_and_purchase_exits(self):
        rom = ROM_PATH.read_bytes()
        info = module_command_info(rom)
        source = next(b for b in banks(rom) if b.name == "message").entries()
        edits = [r for r in json.loads((ROOT/"translations/n64-shop-menus.json").read_text())
                 if r["id"].startswith("message:")]
        self.assertEqual({r["id"].split(":")[1] for r in edits},
                         {"02DD", "02E0", "02E1", "02E2", "02E3", "02E4", "02EB", "02EC", "02EE", "02EF", "02F0"})
        for edit in edits:
            native = source[int(edit["id"].split(":")[1], 16)]
            self.assertEqual(sha256(native), edit["source_sha256"])
            payload = encode(edit["translation"], info)
            validate_entry(native, payload, info, "message", "exact", resident_runtime=True)
            if edit["id"] in ("message:02E4", "message:02EF", "message:02F0"):
                self.assertIn(bytes.fromhex("7F0F02E6"), payload)
                self.assertIn(bytes.fromhex("7F1002E5"), payload)


if __name__ == "__main__":
    unittest.main()
