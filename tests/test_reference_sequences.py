"""Reviewed sequence identity cannot bypass flow, completeness, or size guards."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from aflib import CODE_VROM, by_vrom, sha256
from reference_sequences import (audit_sequence, load_sequences, message_targets,
                                 reference_payloads, reference_sequence_edits, validate_sequences)
from textbanks import banks
from textcodec import command_info, encode
from textvalidate import validate_entry
from gc_adapter import adapt_reference
from runtime_module import module_command_info
from textvalidate import expanded_bound
from test_retail import ROM_PATH


class ReferenceSequenceTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x61
        for code in range(0x0E, 0x13):
            self.info[code] = (4, 0)
        self.info[0x09] = (5, 0)
        self.info[0x13], self.info[0x14], self.info[0x15] = (6, 0), (8, 0), (10, 0)
        self.original = b"A\x7f\x1a\x7f\x09\x00\x00\x03\x7f\x10\x00\x07\x7f\x0f\x00\x08\x7f\x01"
        self.source = [self.original, b"Reserved\x7f\x00"]
        self.texts = ["First{cmd:7F0E0001}{cmd:7F01}",
                      "Second{cmd:7F1A}{cmd:7F09000003}{cmd:7F0F0008}{cmd:7F100007}{cmd:7F01}"]
        self.references = {f"message:{i:04X}": {"id": f"message:{i:04X}", "text": text,
                                               "sha256": sha256(encode(text, self.info))}
                           for i, text in enumerate(self.texts)}
        self.groups = {"test_sequence": {"id": "test_sequence", "evidence": "Synthetic flow test",
                                        "members": [{"id": f"message:{i:04X}",
                                                     "source_sha256": sha256(self.source[i]),
                                                     "encoded_sha256": ref["sha256"],
                                                     "reference_sha256": ref["sha256"]}
                                                    for i, ref in enumerate(self.references.values())]}}
        self.edits, self.permits = reference_sequence_edits(self.references, self.source, self.info, self.groups)

    def test_complete_sequence_with_reordered_branch_assignments(self):
        for i, edit in enumerate(self.edits):
            validate_entry(self.source[i], encode(edit["translation"], self.info), self.info,
                           "message", "reviewed_sequence", sequence_permit=self.permits[edit["id"]])

    def test_partial_unknown_and_spurious_sequence_requests(self):
        for edits in (self.edits[:1], [{**self.edits[0], "reference_sequence": "unknown"}],
                      [{**self.edits[0], "control_policy": "exact"}],
                      [*self.edits, self.edits[0]],
                      [*self.edits, {**self.edits[0], "id": "message:0002"}]):
            with self.assertRaises(ValueError):
                validate_sequences(edits, self.source, self.info, self.groups)
        with self.assertRaisesRegex(ValueError, "complete hash-bound"):
            validate_entry(self.source[0], encode(self.texts[0], self.info), self.info,
                           "message", "reviewed_sequence")

    def test_changed_sources_references_and_payloads(self):
        for key, value in (("translation", "Changed{cmd:7F01}"), ("source_sha256", "0"*64)):
            edits = deepcopy(self.edits)
            edits[1][key] = value
            with self.assertRaises(ValueError):
                validate_sequences(edits, self.source, self.info, self.groups)
        with self.assertRaisesRegex(ValueError, "placeholder"):
            validate_sequences(self.edits, [self.original, b"Other"], self.info, self.groups)
        with self.assertRaisesRegex(ValueError, "reference"):
            reference_sequence_edits({}, self.source, self.info, self.groups)

    def test_native_incoming_branches_reserve_slots(self):
        for command in ("7F0E0001", "7F1300090001", "7F14000900080001", "7F150009000800070001"):
            data = bytes.fromhex(command)+b"\x7f\x01"
            self.assertIn(1, list(message_targets(data, self.info)))
            with self.assertRaisesRegex(ValueError, "reserved sequence slot"):
                validate_sequences(self.edits, [*self.source, data], self.info, self.groups)

    def test_structural_audit_independent_of_hashes(self):
        parts = [encode(text, self.info) for text in self.texts]
        for before, after in ((b"\x7f\x0f\x00\x08", b"\x7f\x0f\x00\x09"),
                              (b"\x7f\x1a", b"\x7f\x1b"),
                              (b"\x7f\x09\x00\x00\x03", b"\x7f\x09\x00\x00\x07"),
                              (b"\x7f\x01", b"\x7f\x00")):
            with self.assertRaises(ValueError):
                audit_sequence(self.original, [parts[0], parts[1].replace(before, after)], [0, 1], self.info)
        with self.assertRaisesRegex(ValueError, "continuation"):
            audit_sequence(self.original, [parts[0].replace(b"\x0e\x00\x01", b"\x0e\x00\x02"), parts[1]],
                           [0, 1], self.info)

    def test_capacity_guard_still_applies(self):
        refs, groups = deepcopy(self.references), deepcopy(self.groups)
        refs["message:0000"]["text"] = "A"*1024+self.texts[0]
        digest = sha256(encode(refs["message:0000"]["text"], self.info))
        refs["message:0000"]["sha256"] = digest
        groups["test_sequence"]["members"][0].update(reference_sha256=digest, encoded_sha256=digest)
        edits, permits = reference_sequence_edits(refs, self.source, self.info, groups)
        with self.assertRaisesRegex(ValueError, "1024"):
            validate_entry(self.source[0], encode(edits[0]["translation"], self.info), self.info,
                           "message", "reviewed_sequence", sequence_permit=permits["message:0000"])

    def test_non_expression_actor_requests_cannot_be_dropped_repeated_or_reordered(self):
        info = list(self.info); info[0x0C] = (5, 0)
        first, second = bytes.fromhex('7F0C030012'), bytes.fromhex('7F09090001')
        native = first+second+b'Native\x7f\x00'
        audit_sequence(native, [first+second+b'English\x7f\x00'], [0], info)
        for requests in (first, second, first+first+second, second+first):
            with self.assertRaisesRegex(ValueError, 'non-expression actor request'):
                audit_sequence(native, [requests+b'English\x7f\x00'], [0], info)
        mood, duration = bytes.fromhex('7F09020001'), bytes.fromhex('7F09080001')
        native = mood+duration+b'Native\x7f\x00'
        for requests in (mood, duration, mood+duration+mood, duration+mood):
            with self.assertRaisesRegex(ValueError, 'non-expression actor request'):
                audit_sequence(native, [requests+b'English\x7f\x00'], [0], info)

    def test_sequence_runtime_requirement_is_not_edit_metadata(self):
        groups = deepcopy(self.groups)
        groups['test_sequence']['requires_resident_runtime'] = True
        self.assertEqual(reference_sequence_edits({}, self.source, self.info, groups), ([], {}))
        with self.assertRaisesRegex(ValueError, 'requires the resident runtime'):
            validate_sequences(self.edits, self.source, self.info, groups)
        edits, permits = reference_sequence_edits(self.references, self.source, self.info, groups,
                                                  resident_runtime=True)
        self.assertEqual(edits, self.edits)
        self.assertEqual(permits, self.permits)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'sequences.json'
            groups['test_sequence']['requires_resident_runtime'] = 'true'
            path.write_text(json.dumps(list(groups.values())))
            with self.assertRaisesRegex(ValueError, 'runtime requirement'):
                load_sequences(path)

    def test_sequence_ampm_requires_native_hour_and_same_part_preparation(self):
        info = self.info+[(0, 0)]*(0x77-len(self.info))
        info[0x76] = (2, 2)
        native = b'Time\x7f\x21\x7f\x00'
        first = b'Clock\x7f\x21\x7f\x76\x7f\x0e\x00\x01\xcd\x7f\x01'
        last = b'Done\x7f\x00'
        audit_sequence(native, [first, last], [0, 1], info, resident_runtime=True)
        for root, parts, runtime, error in (
                (native, [first, last], False, 'unavailable text field'),
                (b'Time\x7f\x00', [first, last], True, 'unavailable text field'),
                (native, [first.replace(b'\x7f\x21\x7f\x76', b'\x7f\x76\x7f\x21'), last],
                 True, 'preceding hour'),
                (native, [first.replace(b'\x7f\x76', b''), b'\x7f\x76'+last], True, 'preceding hour'),
                (native, [first.replace(b'\x7f\x76', b'\x7f\x1b'), last], True, 'unavailable text field')):
            with self.assertRaisesRegex(ValueError, error):
                audit_sequence(root, parts, [0, 1], info, resident_runtime=runtime)

    @unittest.skipUnless(ROM_PATH.is_file() and (ROOT/'build/gamecube/text/message.jsonl').is_file(),
                         'Retail ROM and English text extraction are local-only test inputs')
    def test_complete_late_night_reference_split_and_unchanged_reserve(self):
        rom = ROM_PATH.read_bytes()
        info = module_command_info(rom)
        source = next(b for b in banks(rom) if b.name == 'message').entries()
        refs = {r['id']: r for r in map(json.loads, (ROOT/'build/gamecube/text/message.jsonl').read_text().splitlines())}
        name = 'resident_late_night_introduction'
        group = load_sequences()[name]
        edits, permits = reference_sequence_edits(refs, source, info, {name: group}, resident_runtime=True)
        parts = [encode(e['translation'], info) for e in edits]
        whole = encode(refs['message:04F7']['text'], info)
        self.assertEqual(expanded_bound(whole, info), 1174)
        self.assertEqual([expanded_bound(part, info) for part in parts], [773, 419])
        self.assertEqual(parts[0][-7:], bytes.fromhex('7F0E083ECD7F01'))
        self.assertEqual(parts[0][:-7]+bytes.fromhex('7F04CD7F02')+parts[1], whole)
        for edit, payload in zip(edits, parts):
            native = source[int(edit['id'].split(':')[1], 16)]
            validate_entry(native, payload, info, 'message', 'reviewed_sequence',
                           resident_runtime=True, sequence_permit=permits[edit['id']])
        self.assertEqual(len(reference_sequence_edits(refs, source, info, resident_runtime=True)[0]), 70)
        with self.assertRaisesRegex(ValueError, 'Partial'):
            validate_sequences(edits[:1], source, info, {name: group}, resident_runtime=True)
        # Scan the pinned executable/data section inventory, not arbitrary ROM
        # pixels or compressed bytes. This is evidence for this exact slot only.
        import struct
        from code_sections import code_segments
        files = by_vrom(rom)
        immediates, data_hits = [], []
        for vrom, segment in code_segments()[0].items():
            if vrom not in files:
                continue
            data = files[vrom].extract(rom)
            for offset in range(0, len(data)-3, 4):
                word = struct.unpack_from('>I', data, offset)[0]
                if (segment.is_text(offset) and word & 0xffff == 0x083e
                        and word >> 26 in (8, 9, 10, 11, 12, 13, 14)):
                    immediates.append((segment.name, segment.ram+offset))
            for offset in range(0, len(data)-1, 2):
                if not segment.is_text(offset) and data[offset:offset+2] == b'\x08\x3e':
                    data_hits.append((segment.name, segment.ram+offset))
        self.assertEqual(immediates, [])
        self.assertEqual(data_hits, [('code', 0x8010F664)])

    def test_additional_speaker_emotion_requires_exact_native_evidence(self):
        groups, edits = deepcopy(self.groups), deepcopy(self.edits)
        edits[1]["translation"] = edits[1]["translation"].replace("7F09000003", "7F09000007")
        groups["test_sequence"]["members"][1]["encoded_sha256"] = sha256(encode(edits[1]["translation"], self.info))
        source = [*self.source, b"Speaker\x7f\x09\x00\x00\x07\x7f\x00"]
        approval = {"id": "message:0002", "source_sha256": sha256(source[2]),
                    "commands": ["7F09000007"]}
        with self.assertRaisesRegex(ValueError, "actor argument"):
            validate_sequences(edits, source, self.info, groups)
        groups["test_sequence"]["actor_sources"] = [approval]
        self.assertEqual(len(validate_sequences(edits, source, self.info, groups)), 2)
        for change, error in (({"source_sha256": "0"*64}, "Stale"),
                              ({"id": "message:0003"}, "Stale"),
                              ({"commands": ["7F09000008"]}, "absent"),
                              ({"commands": ["7F09090001"]}, "speaker emotion"),
                              ({"commands": ["7F0E0001"]}, "speaker emotion")):
            altered = deepcopy(groups)
            altered["test_sequence"]["actor_sources"][0].update(change)
            with self.assertRaisesRegex(ValueError, error):
                validate_sequences(edits, source, self.info, altered)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"sequences.json"
            path.write_text(json.dumps(list(groups.values())))
            self.assertEqual(load_sequences(path), groups)
            groups["test_sequence"]["actor_sources"][0]["commands"] = ["7F09090001"]
            path.write_text(json.dumps(list(groups.values())))
            with self.assertRaisesRegex(ValueError, "speaker emotion"):
                load_sequences(path)

    def test_single_record_keeps_external_link_and_original_actor_tuples(self):
        native = self.original[:-2]+b"\x7f\x0e\x00\x09\x7f\x01"
        translated = native.replace(b"A", b"English\x7f\x09\x00\x00\x03")
        audit_sequence(native, [translated], [0], self.info)
        for altered in (translated.replace(b"\x0e\x00\x09", b"\x0e\x00\x08"),
                        translated.replace(b"\x7f\x0e\x00\x09", b""),
                        translated.replace(b"\x7f\x09\x00\x00\x03", b"\x7f\x09\x00\x00\x04")):
            with self.assertRaises(ValueError):
                audit_sequence(native, [altered], [0], self.info)
        parts = [b"Part one\x7f\x0e\x00\x01\x7f\x01", translated]
        audit_sequence(native, parts, [0, 1], self.info)
        with self.assertRaises(ValueError):
            audit_sequence(native, [parts[0], translated.replace(b"\x0e\x00\x09", b"\x0e\x00\x08")],
                           [0, 1], self.info)

    def test_approval_schema(self):
        record = self.groups["test_sequence"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"sequences.json"
            path.write_text(json.dumps([record]))
            self.assertEqual(load_sequences(path), self.groups)
            for records in ({}, [record, record], [{**record, "members": []}],
                            [{**record, "evidence": ""}]):
                path.write_text(json.dumps(records))
                with self.assertRaises(ValueError):
                    load_sequences(path)

    def test_reference_delivery_keeps_english_pages_and_gameplay_guards(self):
        native = b"A\x7f\x04\x7f\x02B\x7f\x09\x00\x00\x03\x7f\x0e\x00\x08\x7f\x01"
        text = "First{cmd:7F04}{cmd:7F02}Second{cmd:7F04}{cmd:7F02}Third{cmd:7F09000007}{cmd:7F0E0008}{cmd:7F01}"
        adapted, changes = adapt_reference(text, native, self.info, "reference_delivery")
        self.assertEqual(adapted, text.replace("7F09000007", "7F09000003"))
        self.assertEqual(changes[0]["gamecube"], {"page_clears": 2, "button_waits": 2})
        replacement = encode(adapted, self.info)
        validate_entry(native, replacement, self.info, "message", "reference_delivery")
        for altered in (replacement.replace(b"\x0e\x00\x08", b"\x0e\x00\x09"),
                        replacement.replace(b"\x7f\x01", b"\x7f\x00"),
                        replacement.replace(b"Third", b"Third\x7f\x1a"),
                        replacement.replace(b"\x7f\x09\x00\x00\x03", b"")):
            with self.assertRaises(ValueError):
                validate_entry(native, altered, self.info, "message", "reference_delivery")
        with self.assertRaises(ValueError):
            validate_entry(native, replacement, self.info, "select", "reference_delivery")
        with self.assertRaisesRegex(ValueError, "signature"):
            validate_entry(native, replacement, self.info, "message", "reference_text")

    def test_split_reference_preserves_one_wait_boundary_and_final_end(self):
        text = "First{cmd:7F04}\n{cmd:7F02}Second{cmd:7F00}"
        encoded = encode(text, self.info)
        digest = sha256(encoded)
        refs = {"message:0000": {"id": "message:0000", "text": text, "sha256": digest}}
        group = deepcopy(self.groups["test_sequence"])
        for member, span in zip(group["members"], [[0, 5], [10, len(encoded)]]):
            member.update(reference_id="message:0000", reference_sha256=digest, reference_slice=span)
        parts = reference_payloads(group, refs, self.info)
        self.assertEqual(parts, [b"First\x7f\x0e\x00\x01\xcd\x7f\x01", b"Second\x7f\x00"])
        audit_sequence(b"Original\x7f\x00", parts, [0, 1], self.info)
        for index, span in ((0, [1, 5]), (1, [10, len(encoded)-1]),
                            (0, [0, 6]), (1, [9, len(encoded)])):
            altered = deepcopy(group)
            altered["members"][index]["reference_slice"] = span
            with self.assertRaises(ValueError):
                reference_payloads(altered, refs, self.info)
        stale = {"message:0000": {**refs["message:0000"], "text": text.replace("First", "Other")}}
        with self.assertRaisesRegex(ValueError, "exact complete"):
            reference_payloads(group, stale, self.info)
        with self.assertRaisesRegex(ValueError, "terminator"):
            audit_sequence(b"Original\x7f\x00", [parts[0], parts[1][:-1]+b"\x01"], [0, 1], self.info)

    @unittest.skipUnless(ROM_PATH.is_file() and (ROOT/"build/gamecube/text/message.jsonl").is_file(),
                         "Retail ROM and English text extraction are local-only test inputs")
    def test_home_explanation_retail_slots_and_reference(self):
        rom = ROM_PATH.read_bytes()
        info = command_info(by_vrom(rom)[CODE_VROM].extract(rom))
        entries = next(b for b in banks(rom) if b.name == "message").entries()
        references = {row["id"]: row for row in map(json.loads, (ROOT/"build/gamecube/text/message.jsonl").read_text().splitlines())}
        edits, permits = reference_sequence_edits(references, entries, info)
        self.assertEqual(len(edits), 62)
        for edit in edits:
            original = entries[int(edit["id"].split(":")[1], 16)]
            validate_entry(original, encode(edit["translation"], info), info, "message", "reviewed_sequence",
                           sequence_permit=permits[edit["id"]])

    def test_complete_reference_then_fully_covering_split_reference(self):
        texts = ["Opening{cmd:7F0E0001}{cmd:7F01}",
                 "Second{cmd:7F04}\n{cmd:7F02}Third{cmd:7F00}"]
        refs = {f"message:{i:04X}": {"text": text, "sha256": sha256(encode(text, self.info))}
                for i, text in enumerate(texts)}
        group = {"members": [
            {"id": "message:0000", "reference_sha256": refs["message:0000"]["sha256"]},
            {"id": "message:0001", "reference_sha256": refs["message:0001"]["sha256"],
             "reference_slice": [0, 6]},
            {"id": "message:0002", "reference_id": "message:0001",
             "reference_sha256": refs["message:0001"]["sha256"],
             "reference_slice": [11, len(encode(texts[1], self.info))]}]}
        parts = reference_payloads(group, refs, self.info)
        self.assertEqual(parts, [encode(texts[0], self.info),
                                b"Second\x7f\x0e\x00\x02\xcd\x7f\x01", b"Third\x7f\x00"])
        audit_sequence(b"Original\x7f\x00", parts, [0, 1, 2], self.info)
        incomplete = deepcopy(group)
        incomplete["members"].pop()
        with self.assertRaisesRegex(ValueError, "complete reference"):
            reference_payloads(incomplete, refs, self.info)
        repeated = deepcopy(group)
        repeated["members"].append(deepcopy(group["members"][0]))
        with self.assertRaisesRegex(ValueError, "repeated"):
            reference_payloads(repeated, refs, self.info)
