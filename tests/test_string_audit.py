"""Straight-line argument hints stay conservative across control flow."""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from audit_string_callers import immediate_argument


class StringAuditTests(unittest.TestCase):
    def test_delay_slot_and_immediate(self):
        call = 0x0C030FDC
        self.assertEqual(immediate_argument([0x2405000A, call, 0], 1, 5)["value"], 10)
        self.assertEqual(immediate_argument([0x2405000A, call, 0x24050040], 1, 5)["value"], 64)
        self.assertEqual(immediate_argument([0x2405FFFF, call, 0], 1, 5)["value"], -1)

    def test_unknown_writes_and_control_flow_stop_search(self):
        for barrier in (0x14400002, 0x0C012345, 0x8FA50010, 0x02002825,
                        0x45010002, 0xE0850000, 0x70002802):
            self.assertIsNone(immediate_argument([0x2405000A, barrier, 0x0C030FDC, 0], 2, 5))
