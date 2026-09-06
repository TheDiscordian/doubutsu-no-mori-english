"""Bounded page advancement must stop before it selects a menu entry."""

from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from emulator_smoke import advance_to_choice


class GameplayScenarioTests(unittest.TestCase):
    def run_choices(self, choices, limit):
        keyboard, record, pause = Mock(), Mock(), Mock()
        with patch("emulator_smoke.message_snapshot", return_value={"message_id": "0001"}), \
                patch("emulator_smoke.choice_snapshot", side_effect=choices):
            advance_to_choice(None, keyboard, {"max_presses": limit}, record, pause)
        return keyboard, record

    def test_stale_and_opening_rows_do_not_count_as_an_active_choice(self):
        keyboard, record = self.run_choices([
            {"choice_count": 4, "choice_state": 0},
            {"choice_count": 2, "choice_state": 1},
            {"choice_count": 2, "choice_state": 2}], 5)
        self.assertEqual(keyboard.press.call_count, 2)
        self.assertEqual(record.call_args.args[0]["presses"], 2)

    def test_already_active_choice_is_never_confirmed(self):
        keyboard, _ = self.run_choices([{"choice_count": 2, "choice_state": 2}], 1)
        keyboard.press.assert_not_called()

    def test_limit_is_enforced(self):
        with self.assertRaisesRegex(ValueError, "declared page-advance limit"):
            self.run_choices([{"choice_count": 0, "choice_state": 0}]*3, 2)
        for options in ({"max_presses": 0}, {"max_presses": 101}, {"max_presses": True},
                        {"settle_seconds": 0}, {"settle_seconds": 11}):
            with self.assertRaises(ValueError):
                advance_to_choice(None, None, options, None)
