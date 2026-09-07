"""Injected native calls cannot block idle or interrupt-management threads."""

from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from emulator_smoke import RSP, require_program_counter
from runtime_layout import RESERVATION, TEST_RETURN, TEST_STACK


class ThreadDebugger(RSP):
    def __init__(self):
        self.registers = [0]*71
        self.registers[37] = 0xFFFFFFFF80026084
        self.pointer, self.thread_id = 0x80300000, 1
        self.force_wrong_thread = False
        self.reserved, self.used = RESERVATION, 0x1800
        self.entry = bytes.fromhex("27BDFFE0")
        self.breakpoint, self.commands = None, []
        self.code_base, self.code_bytes = 0x80200000, bytes.fromhex('03E0000800000000')

    def read_memory(self, address, size):
        if address == self.code_base and size == len(self.code_bytes):
            return self.code_bytes
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
            if TEST_RETURN <= self.breakpoint <= TEST_STACK-0x100:
                self.registers[2] = 55
            return "S05"
        raise AssertionError(command)


class DebuggerThreadTests(unittest.TestCase):
    def test_verified_overlay_calls_require_complete_matching_bounded_code(self):
        debug = ThreadDebugger()
        debug.pause_game_thread()
        before = list(debug.registers)
        proof = (debug.code_base,debug.code_bytes)
        with self.assertRaisesRegex(ValueError,'Invalid test function'):
            debug.call('80200000',[])
        self.assertEqual(debug.call('80200000',[],verified_code=proof)['return_value'],55)
        self.assertEqual(debug.registers,before)
        with self.assertRaisesRegex(ValueError,'differs from resident'):
            debug.call('80200000',[],verified_code=(debug.code_base,b'\0'*8))
        for base,data in ((0,bytes(8)),(0x80200001,bytes(8)),(0x803FFFFC,bytes(8)),
                          (0x801948E0,bytes(8)),(0x80200000,bytes(3)),
                          (0x80200000,bytes(0x20004)),(0x80200000,bytearray(8))):
            debug.commands.clear()
            with self.assertRaisesRegex(ValueError,'code range'):
                debug.call(f'{base&~3:08X}',[],verified_code=(base,data))
            self.assertFalse(any(command.startswith('G') for command in debug.commands))
        with self.assertRaisesRegex(ValueError,'code range'):
            debug.call('80200008',[],verified_code=proof)

    def test_observed_pc_requires_complete_registers_and_exact_target(self):
        registers = [0]*71
        registers[37] = 0xFFFFFFFF80194C5C
        reply = ''.join(f'{v:016x}' for v in registers)
        self.assertEqual(require_program_counter(reply,'80194C5C'),'80194C5C')
        for value in ('S05',reply[:-1],'Z'+reply[1:]):
            with self.assertRaisesRegex(ValueError,'register layout'):
                require_program_counter(value,'80194C5C')
        with self.assertRaisesRegex(ValueError,'observed PC'):
            require_program_counter(reply,'80194C80')

    def test_frame_entry_records_origin_and_calls_restore_registers(self):
        debug = ThreadDebugger()
        record = debug.pause_game_thread()
        self.assertEqual(record["previous_context"]["thread"]["id"], 1)
        self.assertEqual(record["thread"]["id"], 4)
        before = list(debug.registers)
        result = debug.call("80096740", [0x8019B000, 0x2200])
        self.assertEqual(result["return_value"], 55)
        self.assertEqual(result['return_value_v1'],0)
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

    def test_alternate_return_is_bounded_and_restores_the_original_context(self):
        debug = ThreadDebugger()
        debug.pause_game_thread()
        before = list(debug.registers)
        result = debug.call('80096740', [], return_address=f'{TEST_RETURN+0x900:08X}')
        self.assertEqual(result['return_value'], 55)
        self.assertEqual(result['return_breakpoint'], f'{TEST_RETURN+0x900:08X}')
        self.assertEqual(debug.registers, before)
        for address in (0, TEST_RETURN-4, TEST_RETURN+1, TEST_STACK-0xFC, 0x80400000, True):
            debug.commands.clear()
            with self.assertRaisesRegex(ValueError, 'return breakpoint'):
                debug.call('80096740', [], return_address=address)
            self.assertEqual(debug.commands, [])

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
