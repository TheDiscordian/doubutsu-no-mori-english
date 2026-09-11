"""Held-button display captures must not leave controller inputs pressed."""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, call

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from emulator_smoke import hold_capture_keys


class CaptureKeysTest(unittest.TestCase):
    def test_ordinary_capture_has_no_input(self):
        keyboard, pause = Mock(), Mock()
        with hold_capture_keys(keyboard, None, pause=pause):
            pass
        keyboard.set_pressed.assert_not_called()
        pause.assert_not_called()

    def test_capture_holds_and_releases(self):
        keyboard, pause = Mock(), Mock()
        with hold_capture_keys(keyboard, ["q", "z"], pause=pause):
            keyboard.set_pressed.assert_called_once_with(["q", "z"], True)
        self.assertEqual(keyboard.set_pressed.call_args_list,
                         [call(["q", "z"], True), call(["q", "z"], False)])
        pause.assert_called_once_with(0.12)

    def test_capture_failure_releases(self):
        keyboard = Mock()
        with self.assertRaisesRegex(RuntimeError, "capture failed"):
            with hold_capture_keys(keyboard, "a", pause=Mock()):
                raise RuntimeError("capture failed")
        self.assertEqual(keyboard.set_pressed.call_args_list,
                         [call("a", True), call("a", False)])

    def test_invalid_keys_never_press(self):
        for keys in ("", [], ["a", None], 1):
            keyboard = Mock()
            with self.assertRaises(ValueError):
                with hold_capture_keys(keyboard, keys, pause=Mock()):
                    self.fail("invalid input reached capture")
            keyboard.set_pressed.assert_not_called()


if __name__ == "__main__":
    unittest.main()
