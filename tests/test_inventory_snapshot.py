"""Read-only native pocket and clothing observations are bounded and decoded."""

from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from emulator_smoke import RSP, inventory_snapshot


class InventoryMemory(RSP):
    def __init__(self):
        self.pointer = 0x80126EC0
        self.data = bytearray(0xA80)
        self.data[0x10:0x12] = b"\x01\x07"
        struct.pack_into(">15H", self.data, 0x14, *range(0x2200, 0x220F))
        struct.pack_into(">3I", self.data, 0x34, sum((i % 4) << (2*i) for i in range(15)), 12, 18800)
        struct.pack_into(">2H", self.data, 0xA76, 16, 0x2410)
        struct.pack_into('>H', self.data, 0x3EC, 0x2255)

    def command(self, command):
        if not command.startswith("m"):
            raise AssertionError("Inventory observations must be read-only")
        address, length = [int(value, 16) for value in command[1:].split(",")]
        if address == 0x80136FD8:
            return (struct.pack(">I", self.pointer)+bytes(4))[:length].hex()
        if address == self.pointer:
            return self.data[:length].hex()
        raise AssertionError(command)


class InventorySnapshotTests(unittest.TestCase):
    def test_pockets_conditions_money_and_uniform(self):
        result = inventory_snapshot(InventoryMemory())
        self.assertEqual(result["pockets"], [f"{item:04X}" for item in range(0x2200, 0x220F)])
        self.assertEqual(result["item_conditions"], [i % 4 for i in range(15)])
        self.assertEqual((result["wallet"], result["loan"], result["cloth_item"]), (12, 18800, "2410"))
        self.assertEqual(result['equipment_item'], '2255')

    def test_invalid_pointers_identity_and_short_reads_fail(self):
        for pointer in (0, 0x803FFFF0, 0x80126EC1):
            debug = InventoryMemory()
            debug.pointer = pointer
            with self.assertRaises(ValueError):
                inventory_snapshot(debug)
        for offset, value in ((0x10, 2), (0x11, 8)):
            debug = InventoryMemory()
            debug.data[offset] = value
            with self.assertRaises(ValueError):
                inventory_snapshot(debug)
        debug = InventoryMemory()
        debug.data = bytes(16)
        with self.assertRaises(ValueError):
            inventory_snapshot(debug)


if __name__ == "__main__":
    unittest.main()
