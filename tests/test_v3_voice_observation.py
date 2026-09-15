"""Keep the optional speech fixture bounded and separate from real navigation."""
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from v3_voice_observation import observe, place_player


class Memory:
    def __init__(self):
        self.writes = {}

    def pause_game_thread(self):
        return {'paused': True}

    def write_memory(self, address, data):
        self.writes[address] = data

    def read_memory(self, address, size):
        return self.writes[address][:size]


class VoiceObservationTests(unittest.TestCase):
    def fixture(self, *, loaded=0, x=2622, y=160, count=1):
        player = {'player_pointer': '80250B40', 'world_position': {'x':3017, 'y':160, 'z':2243}}
        npc = {'animal_id':'E0DA', 'world_position': {'x':x, 'y':y, 'z':2150}}
        return (patch('emulator_smoke.message_snapshot', return_value={'loaded':loaded}),
                patch('emulator_smoke.player_snapshot', return_value=player),
                patch('emulator_smoke.npc_actors_snapshot', return_value={'live_npc_actors':[npc]*count}))

    def test_only_player_positions_and_yaws_change(self):
        memory, records = Memory(), []
        first, second, third = self.fixture()
        with first, second, third:
            place_player(memory, 'E0DA', records.append)
        position = struct.pack('>3f', 2622, 160, 2180)
        self.assertEqual(memory.writes, {0x80250B68:position, 0x80250B7C:position,
                                       0x80250B76:b'\x80\x00', 0x80250C1E:b'\x80\x00'})
        self.assertFalse(records[-1]['normal_navigation'])
        self.assertFalse(records[-1]['npc_schedule_or_audio_writes'])

    def test_reject_unloaded_ambiguous_cross_acre_and_active_dialogue(self):
        for kwargs in ({'loaded':1}, {'count':0}, {'count':2}, {'x':1000}, {'y':40}):
            memory = Memory()
            first, second, third = self.fixture(**kwargs)
            with first, second, third, self.assertRaises(ValueError):
                place_player(memory, 'E0DA', lambda value:None)
            self.assertEqual(memory.writes, {})
        with self.assertRaises(ValueError):
            place_player(Memory(), 'E0ED', lambda value:None)

    def test_unbounded_observation_rejected_before_any_io(self):
        for frames in (False, 0, -1, 241, 1.5, '120'):
            with self.assertRaises(ValueError):
                observe(None, None, None, frames)
