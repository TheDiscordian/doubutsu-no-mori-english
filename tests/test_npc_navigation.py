"""Adaptive villager approach uses only bounded ordinary controller inputs."""

from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from emulator_smoke import approach_npc


class NpcNavigationTests(unittest.TestCase):
    def run_navigation(self, message=None, npc=True, steps=20):
        keyboard, debug = Mock(), object()
        actor = {"animal_id": "E052", "fg_name": "E052", "world_position": {"x": 10, "y": 0, "z": 20}}
        with patch("emulator_smoke.message_snapshot", return_value=message or {"loaded": 0}), \
             patch("emulator_smoke.player_snapshot", return_value={"world_position": {"x": 0, "y": 0, "z": 0}}), \
             patch("emulator_smoke.npc_actors_snapshot", return_value={"live_npc_actors": [actor] if npc else []}), \
             patch("emulator_smoke.time.sleep"):
            result = approach_npc(debug, keyboard, "E052", steps)
        return result, keyboard

    def test_stall_is_bounded_and_near_target_uses_a(self):
        result, keyboard = self.run_navigation()
        self.assertEqual(result["outcome"], "navigation_stalled")
        self.assertFalse(result["position_or_schedule_writes"])
        self.assertEqual(len(result["observations"]), 8)
        self.assertEqual(keyboard.press.call_count, 16)
        self.assertEqual(keyboard.press.call_args_list[0].args, ("s", 0.025))
        self.assertEqual(keyboard.press.call_args_list[1].args, ("a", 0.06))

    def test_active_dialogue_missing_target_and_bad_limits_do_not_move(self):
        for message, npc, expected in (({"loaded": 1}, True, "dialogue_active"),
                                        ({"loaded": 0}, False, "target_not_uniquely_loaded")):
            result, keyboard = self.run_navigation(message, npc)
            self.assertEqual(result["outcome"], expected)
            keyboard.press.assert_not_called()
        for target, steps in (("E052", 0), ("E052", 121), ("bad", 20), ("XXXX", 20)):
            with self.assertRaises(ValueError):
                approach_npc(object(), Mock(), target, steps)
        result, keyboard = self.run_navigation(steps=2)
        self.assertEqual(result["outcome"], "step_limit")
        self.assertEqual(keyboard.press.call_count, 4)
