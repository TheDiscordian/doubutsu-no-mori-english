"""Placed-item aliases require the native conversion and equal source fields."""

import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from aflib import sha256
from item_aliases import confirmed_aliases, ordinary_item, update_alias_reports
from textbanks import Bank


class ItemAliasTests(unittest.TestCase):
    def setUp(self):
        self.native = b"native    "
        self.banks = {name: Bank(name, 0, None, self.native*count, None, fixed_size=10)
                      for name, count in (("item_10", 3789), ("item_24", 255), ("item_2D", 32),
                                           ("item_23", 32), ("item_22", 36))}
        self.info = [(2, 0)]*0x61
        self.donor = {"id": "item_10:0A84", "source_sha256": sha256(self.native),
                      "translation": "W shirt", "control_policy": "exact", "status": "candidate",
                      "provenance": {"reference_id": "furniture:02A1",
                                     "reference_sha256": sha256(b"W shirt".ljust(16, b" "))}}

    def test_four_rotations_produce_one_complete_destination(self):
        donors = [{**self.donor, "id": f"item_10:{index:04X}"} for index in range(0xA84, 0xA88)]
        aliases = confirmed_aliases(self.banks, donors, self.info)
        self.assertEqual(len(aliases), 1)
        self.assertEqual(aliases[0]["id"], "item_24:00B6")
        self.assertEqual(aliases[0]["translation"], "W shirt")
        self.assertEqual(aliases[0]["provenance"]["native_equivalent_id"], self.donor["id"])
        self.assertEqual(ordinary_item(0x1A84), 0x24B6)
        remaining = {"item_24": [{"id": "item_24:00B6", "reason": "unmatched"}]}
        reports = {"item_24": {"rejected": 1}}
        update_alias_reports(donors, aliases, remaining, reports)
        self.assertEqual(remaining["item_24"], [])
        self.assertEqual(reports["item_24"]["accepted_candidates"], 1)
        self.assertEqual(reports["item_24"]["rejected"], 0)

    def test_short_capacity_and_original_overrides_are_preserved(self):
        donor = copy.deepcopy(self.donor)
        donor["translation"] = "watermelon shirt"
        donor["provenance"]["reference_sha256"] = sha256(b"watermelon shirt")
        self.assertEqual(confirmed_aliases(self.banks, [donor], self.info), [])
        self.assertEqual(len(confirmed_aliases(self.banks, [donor], self.info, 16)), 1)
        self.assertEqual(confirmed_aliases(self.banks, [self.donor], self.info, skip_ids={"item_24:00B6"}), [])

    def test_stale_donor_bad_reference_and_conflicts_fail(self):
        for donor in ({**self.donor, "source_sha256": "0"*64},
                      {**self.donor, "provenance": {}}, {**self.donor, "provenance": "unverified"}):
            with self.assertRaises(ValueError):
                confirmed_aliases(self.banks, [donor], self.info)
        conflict = {**self.donor, "id": "item_24:00B6", "translation": "different"}
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            confirmed_aliases(self.banks, [self.donor, conflict], self.info)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            confirmed_aliases(self.banks, [self.donor, self.donor], self.info)

    def test_different_native_source_does_not_transfer(self):
        self.banks["item_24"] = Bank("item_24", 0, None, b"different "*255, None, fixed_size=10)
        self.assertEqual(confirmed_aliases(self.banks, [self.donor], self.info), [])


if __name__ == "__main__":
    unittest.main()
