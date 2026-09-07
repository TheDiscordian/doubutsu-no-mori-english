"""Live actor observations reject corrupt lists and never write emulator state."""

from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from emulator_smoke import npc_actors_snapshot


class NpcMemory:
    def __init__(self):
        self.game, self.actor, self.animal = 0x80200000, 0x80300000, 0x80130DB8
        game, actor, animal = bytearray(0x1C9C), bytearray(0x178), bytearray(12)
        struct.pack_into(">2I", game, 0x1C94, 1, self.actor)
        actor[2], actor[0xB5] = 3, 1
        struct.pack_into(">H", actor, 6, 0xE052)
        struct.pack_into(">3f", actor, 0x28, 160, 40, 80)
        struct.pack_into(">I", actor, 0x174, self.animal)
        struct.pack_into(">H", animal, 0, 0xE052)
        self.memory = {0x8010EF90: struct.pack(">I", self.game), self.game: game,
                       self.actor: actor, self.animal: animal}

    def read_memory(self, address, size):
        return bytes(self.memory[address][:size])


class NpcActorSnapshotTests(unittest.TestCase):
    def test_live_position_identity_and_empty_list(self):
        memory = NpcMemory()
        result = npc_actors_snapshot(memory)
        self.assertTrue(result["read_only"])
        actor = result["live_npc_actors"][0]
        self.assertEqual((actor["fg_name"], actor["animal_id"], actor["is_drawn"]), ("E052", "E052", 1))
        self.assertEqual(actor["world_position"], {"x": 160, "y": 40, "z": 80})
        struct.pack_into(">2I", memory.memory[memory.game], 0x1C94, 0, 0)
        self.assertEqual(npc_actors_snapshot(memory)["live_npc_actors"], [])

    def test_bad_actor_part_pointer_cycle_count_or_coordinates_fail(self):
        for location, offset, data in (("actor", 2, b"\x02"), ("actor", 0x28, struct.pack(">f", float("nan"))),
                                       ("actor", 0x158, struct.pack(">I", 0x80300000)),
                                       ("actor", 0x174, struct.pack(">I", 0x803FFFFC)),
                                       ("game", 0x1C94, struct.pack(">I", 33)),
                                       ("game", 0x1C94, struct.pack(">I", 2)),
                                       ("game", 0x1C98, struct.pack(">I", 0x80300001))):
            memory = NpcMemory()
            memory.memory[getattr(memory, location)][offset:offset+len(data)] = data
            with self.assertRaises(ValueError):
                npc_actors_snapshot(memory)
        memory = NpcMemory()
        memory.memory[memory.actor] = bytes(16)
        with self.assertRaisesRegex(ValueError, "Truncated"):
            npc_actors_snapshot(memory)
