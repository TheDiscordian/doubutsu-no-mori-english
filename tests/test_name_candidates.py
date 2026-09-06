"""Villager names keep exact reference identity and native six-byte storage."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from aflib import CODE_VROM, by_vrom, sha256
from build import apply_translations
from name_candidates import NPC_COUNT, npc_candidates
from textbanks import Bank, banks
from textcodec import command_info, encode
from test_retail import ROM_PATH


class NameCandidateTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x61
        self.bank = Bank("npc_names", 0, None, b"Source"*220, None, fixed_size=6)
        self.inventory = [{"id": f"npc_names:{i:04X}", "source_sha256": sha256(b"Source"), "legacy": "Bob     "}
                          for i in range(NPC_COUNT)]
        self.references = [{"id": r["id"], "text": "Bob", "source_sha256": sha256(b"Bob     ")}
                           for r in self.inventory]

    def test_complete_plain_names_and_storage_padding(self):
        edits, manifests, remaining, report = npc_candidates(self.bank, self.inventory, self.references, self.info)
        self.assertEqual(len(edits), 216)
        self.assertEqual(remaining, [])
        self.assertEqual(report["excluded_reserve_slots"], 4)
        self.assertEqual(edits[0]["translation"], "Bob")
        self.assertEqual(manifests[0]["stored_sha256"], sha256(b"Bob   "))
        self.assertEqual(manifests[0]["stored_bytes"], 6)

    def test_long_and_unmatched_names_are_withheld_not_shortened(self):
        for text, legacy, reason in (("Monique", "Monique ", "full_reference_name_exceeds_native_six_bytes"),
                                      ("Olivia", "Other   ", "name_identity_not_confirmed_by_legacy")):
            rows, refs = deepcopy(self.inventory), deepcopy(self.references)
            rows[0]["legacy"] = legacy
            refs[0].update(text=text, source_sha256=sha256(text.encode().ljust(8, b" ")))
            edits, _, remaining, _ = npc_candidates(self.bank, rows, refs, self.info)
            self.assertEqual(len(edits), 215)
            self.assertEqual(remaining, [{"id": "npc_names:0000", "reason": reason}])

    def test_stale_duplicate_and_nonplain_inputs_fail(self):
        for rows in (self.inventory[1:], [*self.inventory, self.inventory[0]],
                     [{**self.inventory[0], "source_sha256": "0"*64}, *self.inventory[1:]]):
            with self.assertRaises(ValueError):
                npc_candidates(self.bank, rows, self.references, self.info)
        refs = deepcopy(self.references)
        refs[0]["source_sha256"] = "0"*64
        with self.assertRaisesRegex(ValueError, "reference hash"):
            npc_candidates(self.bank, self.inventory, refs, self.info)
        refs[0].update(text="む", source_sha256=sha256(encode("む", self.info).ljust(8, b" ")))
        rows = deepcopy(self.inventory)
        rows[0]["legacy"] = "む"
        with self.assertRaisesRegex(ValueError, "plain Latin"):
            npc_candidates(self.bank, rows, refs, self.info)

    def test_explicit_original_override_is_not_duplicated(self):
        edits, _, _, report = npc_candidates(self.bank, self.inventory, self.references, self.info,
                                             {"npc_names:0000"})
        self.assertEqual(len(edits), 215)
        self.assertEqual(report["original_draft_override"], 1)

    @unittest.skipUnless(ROM_PATH.is_file() and (ROOT/"build/gamecube/names/npc_names.jsonl").is_file(),
                         "Native ROM and English name extraction are local-only test inputs")
    def test_retail_name_counts_and_unchanged_file_spans(self):
        rom = ROM_PATH.read_bytes()
        files = by_vrom(rom)
        bank = next(b for b in banks(rom) if b.name == "npc_names")
        info = command_info(files[CODE_VROM].extract(rom))
        inventory = list(map(json.loads, (ROOT/"build/inventory/npc_names.jsonl").read_text().splitlines()))
        references = list(map(json.loads, (ROOT/"build/gamecube/names/npc_names.jsonl").read_text().splitlines()))
        edits, _, remaining, _ = npc_candidates(bank, inventory, references, info)
        self.assertEqual((len(edits), len(remaining)), (178, 38))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"names.json"
            path.write_text(json.dumps(edits))
            replacements = {}
            count, relocations = apply_translations(rom, replacements, path)
        self.assertEqual(count, 178)
        self.assertEqual(relocations, {})
        self.assertEqual(set(replacements), {0xE04000})
        original = files[0xE04000].extract(rom)
        result = replacements[0xE04000]
        self.assertEqual(len(result), len(original))
        approved = {int(e["id"].split(":")[1], 16): encode(e["translation"], info).ljust(6, b" ") for e in edits}
        self.assertEqual(result[:8], original[:8])
        self.assertEqual(result[8+216*6:], original[8+216*6:])
        for i in range(216):
            self.assertEqual(result[8+i*6:14+i*6], approved.get(i, original[8+i*6:14+i*6]))
