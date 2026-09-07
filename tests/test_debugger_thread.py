"""Injected native calls cannot block idle or interrupt-management threads."""

from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from emulator_smoke import RSP
from runtime_layout import RESERVATION


class ThreadDebugger(RSP):
    def __init__(self):
        self.registers = [0]*71
        self.registers[37] = 0xFFFFFFFF80026084
        self.pointer, self.thread_id = 0x80300000, 1
        self.force_wrong_thread = False
        self.reserved, self.used = RESERVATION, 0x1800
        self.entry = bytes.fromhex("27BDFFE0")
        self.breakpoint, self.commands = None, []

    def read_memory(self, address, size):
        if address == 0x8003CE30:
            return struct.pack(">I", self.pointer)
        if address == self.pointer:
            return bytes(16)+struct.pack(">HHI", 4, 0, self.thread_id)
        if address == 0x800D334C:
            return self.entry
        if address == 0x801948E0:
            return struct.pack(">5I", 0x41465254, 1, self.reserved, self.used, 1)
        raise AssertionError((address, size))

    def command(self, command):
        self.commands.append(command)
        if command == "?":
            return "S05"
        if command == "g":
            return "".join(f"{value:016x}" for value in self.registers)
        if command.startswith("G"):
            self.registers = [int(command[i:i+16], 16) for i in range(1, len(command), 16)]
            return "OK"
        if command.startswith("Z"):
            self.breakpoint = int(command.split(",")[1], 16)
            return "OK"
        if command.startswith("z"):
            self.breakpoint = None
            return "OK"
        if command == "c":
            self.registers[37] = 0xFFFFFFFF00000000 | self.breakpoint
            if self.breakpoint == 0x800D334C and not self.force_wrong_thread:
                self.pointer, self.thread_id = 0x80145630, 4
            if self.breakpoint == 0x8019A8E0:
                self.registers[2] = 55
            return "S05"
        raise AssertionError(command)


class DebuggerThreadTests(unittest.TestCase):
    def test_frame_entry_records_origin_and_calls_restore_registers(self):
        debug = ThreadDebugger()
        record = debug.pause_game_thread()
        self.assertEqual(record["previous_context"]["thread"]["id"], 1)
        self.assertEqual(record["thread"]["id"], 4)
        before = list(debug.registers)
        result = debug.call("80096740", [0x8019B000, 0x2200])
        self.assertEqual(result["return_value"], 55)
        self.assertEqual(result["return_breakpoint"], "8019A8E0")
        self.assertEqual(result["thread"]["id"], 4)
        self.assertEqual(debug.registers, before)
        self.assertIsNone(debug.breakpoint)

    def test_arbitrary_thread_calls_and_changed_entry_fail(self):
        debug = ThreadDebugger()
        with self.assertRaisesRegex(ValueError, "pause_game_thread"):
            debug.call("80096740", [0x8019B000, 0x2200])
        self.assertFalse(any(command.startswith("G") for command in debug.commands))
        debug.entry = bytes(4)
        with self.assertRaisesRegex(ValueError, "entry guard"):
            debug.pause_game_thread()
        debug = ThreadDebugger()
        debug.force_wrong_thread = True
        with self.assertRaisesRegex(ValueError, "graph-thread"):
            debug.pause_game_thread()
        self.assertIsNone(debug.breakpoint)

    def test_bad_running_thread_pointer_fails(self):
        for pointer in (0, 0x80300001, 0x803FFFF0):
            debug = ThreadDebugger()
            debug.pointer = pointer
            with self.assertRaisesRegex(ValueError, "running-thread pointer"):
                debug.pause_game_thread()

    def test_old_or_overlapping_layout_and_unlinked_targets_fail(self):
        for reserved, used in ((0x4000, 0x1800), (RESERVATION, 0), (RESERVATION, 0x6004)):
            debug = ThreadDebugger()
            debug.reserved, debug.used = reserved, used
            with self.assertRaisesRegex(ValueError, 'scratch RAM'):
                debug.call('80096740', [])
            self.assertFalse(any(command.startswith('G') for command in debug.commands))
        debug = ThreadDebugger()
        with self.assertRaisesRegex(ValueError, 'outside linked'):
            debug.call('8019A000', [])
