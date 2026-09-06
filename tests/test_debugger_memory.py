"""Exact test reads/writes despite the debugger's short-access alignment."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from emulator_smoke import RSP


class AlignedDebugger(RSP):
    def __init__(self):
        self.memory = bytearray(range(128))

    def command(self, command):
        parts = command[1:].split(":")
        address, size = [int(value, 16) for value in parts[0].split(",")]
        # Observed ares short reads align down; model writes the same way to
        # verify byte-edge operations do not depend on unaligned word support.
        if size in (2, 4):
            address &= ~(size-1)
        if command.startswith("m"):
            return self.memory[address:address+size].hex()
        if command.startswith("M"):
            data = bytes.fromhex(parts[1])
            self.memory[address:address+size] = data
            return "OK"
        raise AssertionError(command)


class DebuggerMemoryTests(unittest.TestCase):
    def test_every_alignment_and_short_length_is_exact(self):
        for address in range(16, 24):
            for length in range(1, 34):
                debug = AlignedDebugger()
                self.assertEqual(debug.read_memory(address, length), bytes(range(address, address+length)))
                before = bytes(debug.memory)
                debug.write_memory(address, b"!"*length)
                self.assertEqual(bytes(debug.memory), before[:address]+b"!"*length+before[address+length:])

    def test_bad_ranges_and_truncated_reads_fail(self):
        debug = AlignedDebugger()
        for address, length in ((0, 0), (-1, 4), (0xFFFFFFFF, 2), (126, 5)):
            with self.assertRaises(ValueError):
                debug.read_memory(address, length)
        for address, data in ((0, b""), (-1, b"x"), (0xFFFFFFFF, b"xx")):
            with self.assertRaises(ValueError):
                debug.write_memory(address, data)


if __name__ == "__main__":
    unittest.main()
