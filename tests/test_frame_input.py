"""Frame-bounded controller holds release buttons even if stepping fails."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from emulator_smoke import Keyboard


class FakeKeyboard(Keyboard):
    def __init__(self):self.events=[];self.fail=False
    def set_pressed(self,name,pressed):self.events.append(('key',name,pressed))
    def advance_frames(self,frames):
        self.events.append(('frames',frames))
        if self.fail and frames==4:raise RuntimeError('fixture frame failure')


class FrameInputTests(unittest.TestCase):
    @patch('emulator_smoke.time.sleep')
    def test_pause_hold_and_release_are_separate_from_wall_clock_duration(self,pause):
        keyboard=FakeKeyboard();keyboard.press_frames('b',4)
        self.assertEqual(keyboard.events,[('frames',1),('key','b',True),('frames',4),
                                         ('key','b',False),('frames',4)])
        keyboard=FakeKeyboard();keyboard.fail=True
        with self.assertRaises(RuntimeError):keyboard.press_frames('b',4)
        self.assertEqual(keyboard.events[-1],('key','b',False))

    @patch('emulator_smoke.time.sleep')
    def test_bounded_counts_and_separate_hotkey_edges(self,pause):
        keyboard=FakeKeyboard();Keyboard.advance_frames(keyboard,3)
        self.assertEqual(keyboard.events,[('key','F7',True),('key','F7',False)]*3)
        for count in (0,-1,301,1.5,True):
            with self.assertRaises(ValueError):Keyboard.advance_frames(keyboard,count)
        for count in (0,121,False):
            with self.assertRaises(ValueError):keyboard.press_frames('a',count)
        with self.assertRaises(ValueError):keyboard.press_frames(['a','F7'],4)


if __name__=='__main__':unittest.main()
