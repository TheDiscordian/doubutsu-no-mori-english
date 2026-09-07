"""A slow debugger startup is retried only while the exact emulator is alive."""

from pathlib import Path
from types import SimpleNamespace
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from emulator_smoke import connect_debugger


class DebuggerStartupTests(unittest.TestCase):
    def test_waits_for_live_socket_with_a_deadline_without_restarting(self):
        clock, calls, timeouts = [0.0], [], []
        ready = SimpleNamespace(sock=SimpleNamespace(settimeout=timeouts.append))
        def connect(port, timeout):
            calls.append((port, timeout))
            if len(calls) < 3:
                raise ConnectionRefusedError()
            return ready
        result = connect_debugger(SimpleNamespace(poll=lambda: None), 1234, 1,
            connect=connect, now=lambda: clock[0], pause=lambda n: clock.__setitem__(0, clock[0]+n))
        self.assertIs(result, ready)
        self.assertEqual(len(calls), 3)
        self.assertEqual(timeouts, [5])
        self.assertTrue(all(0 < timeout <= 1 for _, timeout in calls))

    def test_exit_deadline_and_unexpected_errors_are_terminal(self):
        clock, calls = [0.0], []
        def connect(port, timeout):
            calls.append(port)
            raise ConnectionRefusedError()
        with self.assertRaisesRegex(RuntimeError, 'exited'):
            connect_debugger(SimpleNamespace(poll=lambda: 1), 1, connect=connect)
        self.assertEqual(calls, [])
        with self.assertRaisesRegex(TimeoutError, 'ready'):
            connect_debugger(SimpleNamespace(poll=lambda: None), 1, 0.25,
                connect=connect, now=lambda: clock[0], pause=lambda n: clock.__setitem__(0, clock[0]+n))
        self.assertEqual(clock[0], 0.25)
        self.assertEqual(len(calls), 3)
        def invalid(port, timeout):
            raise ValueError('invalid protocol')
        with self.assertRaisesRegex(ValueError, 'invalid protocol'):
            connect_debugger(SimpleNamespace(poll=lambda: None), 1, connect=invalid)
