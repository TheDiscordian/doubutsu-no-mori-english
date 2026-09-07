"""Planting scenarios use controller input and observed pocket assertions only."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from planting_test_scenario import scenario


class PlantingScenarioTests(unittest.TestCase):
    def test_slot_navigation_and_independent_pocket_assertions(self):
        pockets = ["0000"]*15
        pockets[2], pockets[10] = "2909", "2900"
        steps = scenario(pockets, [2, 10], "s")
        checks = [r["expect_inventory"]["pockets"] for r in steps if "expect_inventory" in r]
        self.assertEqual(checks[0], pockets)
        self.assertEqual(checks[1][2], "0000")
        self.assertEqual(checks[1][10], "2900")
        self.assertEqual(checks[2], ["0000"]*15)
        self.assertEqual(pockets[2], "2909")
        self.assertEqual(sum(r.get("key") == "g" for r in steps), 2)
        self.assertFalse(any(k in r for r in steps for k in ("write", "call", "command")))

    def test_invalid_or_nonplanting_slots_fail(self):
        for slots in ([], [0, 0], [-1], [15], [True], [0]):
            with self.assertRaises(ValueError):
                scenario(["0000"]*15, slots)
        with self.assertRaises(ValueError):
            scenario(["2900"]*14, [0])
        with self.assertRaises(ValueError):
            scenario(["2900"]*15, [0], "a")


if __name__ == "__main__":
    unittest.main()
