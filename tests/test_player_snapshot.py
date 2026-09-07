"""Navigation observations use validated read-only native actor pointers."""

from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from emulator_smoke import RSP, player_snapshot


class ReadOnlyMemory(RSP):
    def __init__(self):
        self.game, self.actor = 0x80200000, 0x80300000
        self.memory = {0x8010EF90: struct.pack(">II", self.game, 0),
                       self.game+0x1C90: struct.pack(">II", self.actor, 0)}
        state = bytearray(0x40)
        state[2] = 2
        struct.pack_into(">bb", state, 8, 2, -1)
        struct.pack_into(">3f", state, 0x28, 120.5, 0, -50.25)
        self.memory[self.actor] = bytes(state)

    def command(self, command):
        if not command.startswith("m"):
            raise AssertionError("Player snapshots must only read memory")
        address, length = [int(value, 16) for value in command[1:].split(",")]
        return self.memory[address][:length].hex()


class PlayerSnapshotTests(unittest.TestCase):
    def test_reads_world_and_signed_blocks(self):
        snapshot = player_snapshot(ReadOnlyMemory())
        self.assertEqual(snapshot["world_position"], {"x": 120.5, "y": 0, "z": -50.25})
        self.assertEqual((snapshot["block_x"], snapshot["block_z"]), (2, -1))
        self.assertTrue(snapshot["read_only"])

    def test_bad_pointers_part_coordinates_and_short_reads_fail(self):
        for address, data in ((0x8010EF90, bytes(8)),
                              (0x80201C90, struct.pack(">II", 0x803FFFF0, 0)),
                              (0x80201C90, struct.pack(">II", 0x80300001, 0)),
                              (0x8010EF90, b"x")):
            debug = ReadOnlyMemory()
            debug.memory[address] = data
            with self.assertRaises(ValueError):
                player_snapshot(debug)
        for offset, data in ((2, b"\x03"), (0x28, struct.pack(">f", float("nan")))):
            debug = ReadOnlyMemory()
            state = bytearray(debug.memory[debug.actor])
            state[offset:offset+len(data)] = data
            debug.memory[debug.actor] = bytes(state)
            with self.assertRaises(ValueError):
                player_snapshot(debug)


if __name__ == "__main__":
    unittest.main()
