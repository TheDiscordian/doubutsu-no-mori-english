"""Exact test reads/writes despite the debugger's short-access alignment."""

from pathlib import Path
import sys
import json
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from emulator_smoke import RSP, DebuggerMemoryError, capture_debugger_failure


class AlignedDebugger(RSP):
    def __init__(self):
        self.memory = bytearray(range(128))

    def command(self, command):
        parts = command[1:].split(":")
        address, size = [int(value, 16) for value in parts[0].split(",")]
        # Observed ares short reads align down; model writes the same way to
        # verify byte-edge operations do not depend on unaligned word support.
        if size in (2, 4, 8):
            address &= ~(size-1)
        if command.startswith("m"):
            return self.memory[address:address+size].hex()
        if command.startswith("M"):
            data = bytes.fromhex(parts[1])
            self.memory[address:address+size] = data
            return "OK"
        raise AssertionError(command)


class DebuggerMemoryTests(unittest.TestCase):
    def test_transport_failure_captures_once_and_preserves_original_error(self):
        from unittest.mock import Mock
        debug = RSP.__new__(RSP)
        error = TimeoutError('native continuation timed out')
        debug.send = Mock()
        debug.receive = Mock(side_effect=[error, 'OK', error])
        debug.failure_handler = Mock()
        handler = debug.failure_handler
        with self.assertRaises(TimeoutError) as caught:
            debug.command('c')
        self.assertIs(caught.exception, error)
        handler.assert_called_once_with(debug, 'c', error)
        self.assertEqual(debug.command('?'), 'OK')
        with self.assertRaises(TimeoutError):
            debug.command('g')
        handler.assert_called_once()

    def test_transport_snapshot_keeps_pending_replies_and_does_not_write_game_state(self):
        from unittest.mock import Mock
        debug = RSP.__new__(RSP)
        debug.sock = Mock()
        debug.sock.gettimeout.return_value = 5
        registers = ['0000000000000000']*71
        registers[37] = 'ffffffff80647928'
        debug.send = Mock()
        debug.receive = Mock(side_effect=['S05', 'T05', ''.join(registers), '00'*32,
                                         '00'*432, '00'*64])
        debug.ram_end = 0x80800000
        with tempfile.TemporaryDirectory() as directory:
            capture_debugger_failure(debug, Path(directory), 'c', TimeoutError('timeout'))
            data = json.loads((Path(directory)/'debugger-transport-failure.json').read_text())
        self.assertEqual(data['pc'], '80647928')
        self.assertEqual(data['replies'][0], dict(command='?', response='S05'))
        self.assertEqual(data['replies'][1], dict(command='?', response='T05'))
        self.assertEqual(data['registers'], ''.join(registers))
        self.assertTrue(all(call.args[0] in ('?', 'g') or call.args[0].startswith('m')
                            for call in debug.send.call_args_list))
        debug.sock.sendall.assert_called_once_with(b'\x03')
        self.assertEqual(debug.sock.settimeout.call_args_list[-1].args, (5,))

    def test_bad_reply_preserves_exact_command_and_raw_response(self):
        from unittest.mock import Mock
        debug = AlignedDebugger()
        for response in ('T05thread:4;', 'E14', '', '0011', '00 '*8, 'g0'*8):
            debug.command = Mock(return_value=response)
            with self.assertRaises(DebuggerMemoryError) as caught:
                debug.read_memory(0x8010EF94, 4)
            self.assertEqual(caught.exception.command, 'm8010ef90,8')
            self.assertEqual(caught.exception.response, response)
            debug.command.assert_called_once_with('m8010ef90,8')

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
