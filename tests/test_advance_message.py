"""Ordinary gameplay arrival waits for evidence, not a fixed button count."""

from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from emulator_smoke import advance_to_message


class AdvanceMessageTests(unittest.TestCase):
    def run_messages(self, messages, options=None, choices=None):
        calls, records = [], []
        keyboard = SimpleNamespace(press=lambda *args: calls.append(args))
        with patch('emulator_smoke.message_snapshot', side_effect=messages), \
             patch('emulator_smoke.choice_snapshot', side_effect=choices,
                   return_value={'choice_state': 0, 'choice_count': 4}):
            advance_to_message(None, keyboard, options or {'message_id': '07DD'},
                               records.append, pause=lambda seconds: None)
        return calls, records

    def test_stops_on_live_target_without_an_extra_press(self):
        target = {'message_id': '07DD', 'loaded': 1}
        calls, records = self.run_messages([{'message_id': '07DD', 'loaded': 0},
                                            {'message_id': '2AD2', 'loaded': 1}, target])
        self.assertEqual(calls, [('a', 0.08)]*2)
        self.assertEqual(records[-1], {'advanced_to_message': '07DD', 'presses': 2})
        self.assertEqual(self.run_messages([target])[0], [])

    def test_choice_and_exhausted_budget_fail(self):
        pending = {'message_id': '2AD2', 'loaded': 1}
        with self.assertRaisesRegex(ValueError, 'active choice'):
            self.run_messages([pending], choices=[{'choice_state': 2, 'choice_count': 2}])
        with self.assertRaisesRegex(ValueError, 'press limit'):
            self.run_messages([pending]*3, {'message_id': '07DD', 'max_presses': 2})

    def test_invalid_bounds_fail_before_input(self):
        for options in ({'message_id': '7DD'}, {'message_id': '07dd'},
                        {'message_id': 0x07DD}, {'message_id': '07DD', 'max_presses': True},
                        {'message_id': '07DD', 'max_presses': 101},
                        {'message_id': '07DD', 'settle_seconds': float('nan')},
                        {'message_id': '07DD', 'settle_seconds': 0}):
            with self.assertRaises(ValueError):
                self.run_messages([], options)

    def test_only_explicit_live_first_choices_are_selected(self):
        options = {'message_id': '07DD', 'choose_first_in': ['2AE4']}
        pending = {'message_id': '2AE4', 'loaded': 1}
        target = {'message_id': '07DD', 'loaded': 1}
        choice = {'choice_state': 2, 'choice_count': 2, 'choice_cursor': 0}
        calls, records = self.run_messages([pending, target], options, [choice, choice])
        self.assertEqual(calls, [('a', 0.08)])
        self.assertIn({'choose_first_in_message': '2AE4'}, records)
        for message, current in (({**pending, 'loaded': 0}, choice),
                                  (pending, {**choice, 'choice_cursor': 1}),
                                  ({**pending, 'message_id': '2ACC'}, choice)):
            with self.assertRaisesRegex(ValueError, 'active choice'):
                self.run_messages([message], options, [current])

    def test_bad_choice_permissions_fail_before_input(self):
        for choices in ('2AE4', [None], [0x2AE4], ['2AE4', '2AE4'], ['2ae4'], ['2AE4']*17):
            with self.assertRaisesRegex(ValueError, 'first-choice message list'):
                self.run_messages([], {'message_id': '07DD', 'choose_first_in': choices})
