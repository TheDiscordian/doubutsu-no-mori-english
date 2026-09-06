"""Name-reader inventory stays separate from destination-capacity approval."""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from audit_name_callers import name_audit
from test_retail import ROM_PATH


@unittest.skipUnless(ROM_PATH.is_file(), "Original ROM is a local-only test input")
class NameCallerTests(unittest.TestCase):
    def test_retail_direct_targets_and_counts(self):
        result = name_audit(ROM_PATH.read_bytes())
        for name, address, count, width in (("item_name", "80096740", 35, 10),
                                             ("villager_name", "800ACC38", 2, 6)):
            entry = result[name]
            self.assertEqual(entry["target_ram"], address)
            self.assertEqual(entry["native_write_bytes"], width)
            self.assertEqual(len(entry["callers"]), count)
            self.assertNotIn("capacity_counts", entry)
            for row in entry["callers"]:
                self.assertIn("name_id_argument", row)
                self.assertNotIn("destination_length", row)
                self.assertEqual(len(row["file_sha256"]), 64)
