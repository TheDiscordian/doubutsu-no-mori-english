"""Native resident records support navigation without editing progression."""

from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from emulator_smoke import RSP, villagers_snapshot


class VillageMemory(RSP):
    def __init__(self):
        self.maximum = 5
        self.animals, self.listing = bytearray(15*0x528), bytearray(15*0x38)
        struct.pack_into(">H", self.animals, 0, 0xE005)
        self.animals[10:12] = b"\x05\x02"
        self.animals[0x4E0:0x4E5] = bytes([1, 2, 3, 4, 5])
        self.animals[0x524:0x526] = b"\x01\x01"
        struct.pack_into(">2H6f", self.listing, 0, 0xE005, 0x1000, 1440, 0, 2120, 1460, 80, 2100)

    def command(self, command):
        if not command.startswith("m"):
            raise AssertionError("Villager observations must be read-only")
        address, length = [int(value, 16) for value in command[1:].split(",")]
        data = {0x80126EB8: bytes([self.maximum, 0, 0, 0]),
                0x80130DB8: self.animals, 0x80137000: self.listing}[address]
        return data[:length].hex()


class VillagerSnapshotTests(unittest.TestCase):
    def test_resident_home_and_recorded_position(self):
        result = villagers_snapshot(VillageMemory())
        self.assertTrue(result["read_only"])
        self.assertEqual(len(result["villagers"]), 1)
        resident = result["villagers"][0]
        self.assertEqual((resident["npc_id"], resident["name_id"], resident["personality"]), ("E005", 5, 2))
        self.assertEqual(resident["home"]["acre_z"], 3)
        self.assertEqual(resident["recorded_position"], {"x": 1460.0, "y": 80.0, "z": 2100.0})

    def test_invalid_population_ids_coordinates_and_short_reads_fail(self):
        memory = VillageMemory()
        memory.maximum = 16
        with self.assertRaises(ValueError):
            villagers_snapshot(memory)
        for id in (0xEFFF, 0xE005):
            memory = VillageMemory()
            struct.pack_into(">H", memory.animals, 0x528, id)
            with self.assertRaises(ValueError):
                villagers_snapshot(memory)
        memory = VillageMemory()
        struct.pack_into(">f", memory.listing, 4, float("nan"))
        with self.assertRaises(ValueError):
            villagers_snapshot(memory)
        memory = VillageMemory()
        memory.animals = bytes(8)
        with self.assertRaises(ValueError):
            villagers_snapshot(memory)
