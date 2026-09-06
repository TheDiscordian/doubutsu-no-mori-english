"""Fixed-width item imports preserve complete references and rotation identities."""

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
from item_candidates import FURNITURE_COUNT, item_candidates
from item_names_test_scenario import ordinary_item
from textbanks import Bank, banks
from textcodec import command_info, encode
from test_retail import ROM_PATH


class ItemCandidateTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x61
        self.bank = Bank("item_22", 0, None, b"Source    "*2, None, fixed_size=10)
        self.inventory = [{"id": f"item_22:{i:04X}", "source_sha256": sha256(b"Source    "),
                           "legacy": "Net ", "legacy_entry_id": f"item_22:{i:04X}"} for i in range(2)]
        self.references = [{"id": r["id"], "text": "net", "source_sha256": sha256(b"net".ljust(16, b" "))}
                           for r in self.inventory]

    def test_case_only_match_keeps_reference_spelling_and_padding(self):
        edits, manifests, remaining, report = item_candidates(self.bank, self.inventory, self.references, self.info)
        self.assertEqual([e["translation"] for e in edits], ["net", "net"])
        self.assertEqual(remaining, [])
        self.assertEqual(report["accepted_reference_identities"], 2)
        self.assertEqual(manifests[0]["stored_sha256"], sha256(b"net       "))

    def test_long_name_and_word_change_are_withheld(self):
        for legacy, reference, reason in (("Fishing Rod", "fishing rod", "full_reference_name_exceeds_native_ten_bytes"),
                                           ("Fishing Pole", "fishing rod", "item_identity_not_confirmed_by_legacy")):
            rows, refs = deepcopy(self.inventory), deepcopy(self.references)
            rows[0]["legacy"] = legacy
            refs[0].update(text=reference, source_sha256=sha256(reference.encode().ljust(16, b" ")))
            edits, _, remaining, _ = item_candidates(self.bank, rows, refs, self.info)
            self.assertEqual(len(edits), 1)
            self.assertEqual(remaining[0]["reason"], reason)

    def test_stale_duplicate_wrong_donor_and_nonplain_inputs_fail(self):
        for rows in (self.inventory[1:], [*self.inventory, self.inventory[0]],
                     [{**self.inventory[0], "source_sha256": "0"*64}, self.inventory[1]],
                     [{**self.inventory[0], "legacy_entry_id": "item_22:0001"}, self.inventory[1]]):
            with self.assertRaises(ValueError):
                item_candidates(self.bank, rows, self.references, self.info)
        refs = deepcopy(self.references)
        refs[0]["source_sha256"] = "0"*64
        with self.assertRaisesRegex(ValueError, "reference hash"):
            item_candidates(self.bank, self.inventory, refs, self.info)
        refs[0].update(text="む", source_sha256=sha256(encode("む", self.info).ljust(16, b" ")))
        rows = deepcopy(self.inventory)
        rows[0]["legacy"] = "む"
        with self.assertRaisesRegex(ValueError, "plain Latin"):
            item_candidates(self.bank, rows, refs, self.info)

    def test_furniture_groups_and_filler(self):
        bank = Bank("item_10", 0, None, b"Source    "*(FURNITURE_COUNT*4)+b"Filler    ", None, fixed_size=10)
        rows = [{"id": f"item_10:{i:04X}", "source_sha256": sha256(b"Source    "),
                 "legacy": "Chair", "legacy_entry_id": f"item_10:{i//4:04X}"} for i in range(FURNITURE_COUNT*4)]
        refs = [{"id": f"furniture:{i:04X}", "text": "chair", "source_sha256": sha256(b"chair".ljust(16, b" "))}
                for i in range(FURNITURE_COUNT)]
        edits, _, remaining, report = item_candidates(bank, rows, refs, self.info)
        self.assertEqual((len(edits), remaining), (FURNITURE_COUNT*4, []))
        self.assertEqual(report["excluded_filler_slots"], 1)
        self.assertEqual(report["accepted_reference_identities"], FURNITURE_COUNT)
        bank.data = b"Changed   "+bank.data[10:]
        rows[0]["source_sha256"] = sha256(b"Changed   ")
        with self.assertRaisesRegex(ValueError, "rotation names"):
            item_candidates(bank, rows, refs, self.info)

    def test_original_override(self):
        edits, _, _, report = item_candidates(self.bank, self.inventory, self.references, self.info, {"item_22:0000"})
        self.assertEqual([e["id"] for e in edits], ["item_22:0001"])
        self.assertEqual(report["original_draft_override"], 1)

    def test_placed_item_conversion_boundaries_and_rotations(self):
        for start, end, base in ((0x17AC, 0x1BA8, 0x2400), (0x1BA8, 0x1C28, 0x2D00),
                                  (0x1C28, 0x1CA8, 0x2300), (0x1CA8, 0x1D28, 0x2204)):
            for index in range((end-start)//4):
                for rotation in range(4):
                    self.assertEqual(ordinary_item(start+index*4+rotation), base+index)
        for item in (0, 0x1000, 0x17AB, 0x1D28, 0x1ECB, 0x2000, 0xFFFF):
            self.assertEqual(ordinary_item(item), item)

    @unittest.skipUnless(ROM_PATH.is_file() and (ROOT/"build/gamecube/names/furniture.jsonl").is_file(),
                         "Native ROM and English item references are local-only test inputs")
    def test_retail_import_preserves_every_other_byte(self):
        rom = ROM_PATH.read_bytes()
        files = by_vrom(rom)
        info = command_info(files[CODE_VROM].extract(rom))
        selected = [b for b in banks(rom) if b.name.startswith("item_")]
        edits = []
        expected = bytearray(files[0x10F4000].extract(rom))
        for bank in selected:
            reference_name = "furniture" if bank.name == "item_10" else bank.name
            rows = list(map(json.loads, (ROOT/"build/inventory"/(bank.name+".jsonl")).read_text().splitlines()))
            refs = list(map(json.loads, (ROOT/"build/gamecube/names"/(reference_name+".jsonl")).read_text().splitlines()))
            accepted, _, _, _ = item_candidates(bank, rows, refs, info)
            edits.extend(accepted)
            for edit in accepted:
                offset = bank.data_offset+int(edit["id"].split(":")[1], 16)*10
                expected[offset:offset+10] = encode(edit["translation"], info).ljust(10, b" ")
        self.assertGreater(len(edits), 10)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"items.json"
            path.write_text(json.dumps(edits))
            replacements = {}
            count, relocations = apply_translations(rom, replacements, path)
        self.assertEqual(count, len(edits))
        self.assertEqual(relocations, {})
        self.assertEqual(set(replacements), {0x10F4000})
        self.assertEqual(replacements[0x10F4000], bytes(expected))
