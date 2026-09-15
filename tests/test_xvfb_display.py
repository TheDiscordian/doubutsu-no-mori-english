"""Emulator display allocation must preserve desktop and other test sockets."""

from pathlib import Path
import os
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from emulator_smoke import read_x_display, reserve_x_display


class XvfbDisplayTests(unittest.TestCase):
    def test_waits_for_the_complete_newline_terminated_readiness_reply(self):
        with patch('emulator_smoke.select.select', return_value=([7], [], [])), \
             patch('emulator_smoke.os.read', side_effect=[b'2', b'00', b'\n']) as read:
            self.assertEqual(read_x_display(7), '200')
            self.assertEqual(read.call_count, 3)

    def test_rejects_incomplete_or_invalid_readiness(self):
        for chunks in ([b'200', b''], [b'200\n201\n'], [b'\n'], [b'x\n'], [b'1'*32]):
            with patch('emulator_smoke.select.select', return_value=([7], [], [])), \
                 patch('emulator_smoke.os.read', side_effect=chunks), self.assertRaises(RuntimeError):
                read_x_display(7)
        with patch('emulator_smoke.select.select', return_value=([], [], [])), self.assertRaises(RuntimeError):
            read_x_display(7)

    def test_skips_locks_sockets_and_broken_symlinks_without_replacing_them(self):
        with tempfile.TemporaryDirectory() as directory:
            tmp = Path(directory)
            sockets = tmp/".X11-unix"
            sockets.mkdir()
            (tmp/".X200-lock").write_text(str(os.getpid()))
            (sockets/"X202_").touch()
            (sockets/"X203").symlink_to(tmp/"missing")
            with socket.socket(socket.AF_UNIX) as server:
                server.bind(str(sockets/"X201"))
                server.listen()
                inode = (sockets/"X201").stat().st_ino
                with reserve_x_display(tmp) as display:
                    self.assertEqual(display, "204")
                self.assertEqual((sockets/"X201").stat().st_ino, inode)
                with socket.socket(socket.AF_UNIX) as client:
                    client.connect(str(sockets/"X201"))
                self.assertEqual((tmp/".X200-lock").read_text(), str(os.getpid()))
                self.assertTrue((sockets/"X203").is_symlink())

    def test_skips_display_created_during_previous_startup(self):
        with tempfile.TemporaryDirectory() as directory:
            tmp = Path(directory)
            (tmp/".X11-unix").mkdir()
            with reserve_x_display(tmp) as first:
                (tmp/f".X11-unix/X{first}").touch()
            with reserve_x_display(tmp) as second:
                self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
