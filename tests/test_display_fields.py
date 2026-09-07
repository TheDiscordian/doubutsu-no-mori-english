"""Wider display names preserve actor resolution and bounded dialogue insertion."""

import ctypes
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("gcc"), "Host GCC executes original display-name consumers")
class DisplayFieldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        library = Path(cls.temporary.name)/"display_fields.so"
        subprocess.run(["gcc", "-std=c99", "-Wall", "-Wextra", "-Werror", "-O2", "-shared", "-fPIC",
                        "-I", str(ROOT/"runtime"), str(ROOT/"runtime/display_name.c"),
                        str(ROOT/"runtime/display_fields.c"), str(ROOT/"tests/display_name_mock.c"),
                        "-o", str(library)], check=True, capture_output=True)
        cls.lib = ctypes.CDLL(str(library))
        cls.lib.af_get_display_name.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        cls.lib.af_get_display_name.restype = None
        cls.lib.af_copy_talk_name.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int]

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        self.enabled = ctypes.c_uint.in_dll(self.lib, "af_display_enabled")
        self.enabled.value = 1
        self.native = ctypes.c_uint.in_dll(self.lib, "af_display_native_calls")
        self.native.value = 0
        self.animal = (ctypes.c_ubyte*12).in_dll(self.lib, "af_display_animal")
        self.special = (ctypes.c_ushort*64).in_dll(self.lib, "af_display_special_ids")
        self.special[:] = range(0xD000, 0xD040)
        self.actor = ctypes.create_string_buffer(0x178)

    def setup_actor(self, part, fg, animal=None):
        self.actor[2], self.actor[6], self.actor[7] = part, fg >> 8, fg & 255
        self.actor[0x177] = int(animal is not None)
        if animal is not None:
            self.animal[0], self.animal[1] = animal >> 8, animal & 255

    def name(self, actor=True):
        guard = ctypes.create_string_buffer(b"!"*32, 32)
        self.lib.af_get_display_name(ctypes.byref(guard, 9), self.actor if actor else None)
        self.assertEqual(guard.raw[:9]+guard.raw[17:], b"!"*24)
        return guard.raw[9:17]

    @staticmethod
    def expected(index):
        return bytes(32+(index*8+i) % 95 for i in range(8))

    def test_every_animal_and_special_actor_branch(self):
        for npc in range(216):
            self.setup_actor(3, 0xD000, 0xE000+npc)
            self.assertEqual(self.name(), self.expected(npc))
        for part in (0, 2, 3, 7):
            for index in range(64):
                self.setup_actor(part, 0xD000+index)
                self.assertEqual(self.name(), self.expected(216+index))
        self.assertEqual(self.native.value, 0)

    def test_invalid_branch_nulls_and_disabled_resource_use_padded_native_name(self):
        for part, fg, animal in ((2, 0xE000, None), (3, 0xE000, None), (3, 0xD000, 0xD001),
                                 (3, 0xD000, 0xE0FF), (3, 0xFFFF, None)):
            self.setup_actor(part, fg, animal)
            self.assertEqual(self.name(), b"native  ")
        self.assertEqual(self.name(False), b"------  ")
        self.enabled.value = 0
        self.setup_actor(3, 0xE000, 0xE000)
        self.assertEqual(self.name(), b"native  ")
        calls = self.native.value
        self.lib.af_get_display_name(None, self.actor)
        self.assertEqual(self.native.value, calls)

    def insertion(self, actor, index, suffix, name):
        original = b"p"*index+b"\x7f\x1b"+suffix
        expected = b"p"*index+name.rstrip(b" ")+suffix
        data = ctypes.create_string_buffer(b"!"*16+original.ljust(1024, b" ")+b"!"*16, 1056)
        result = self.lib.af_copy_talk_name(actor, ctypes.byref(data, 16), index, len(original))
        self.assertEqual((result, data.raw[16:16+result]), (len(expected), expected))
        self.assertEqual(data.raw[:16]+data.raw[1040:], b"!"*32)

    def test_message_positions_exact_limit_null_actor_and_native_fallback(self):
        self.setup_actor(3, 0xE003, 0xE003)
        for index in (0, 1, 10, 100, 1012):
            self.insertion(self.actor, index, b"tail", self.expected(3))
        self.insertion(None, 1000, b"tail", b"")
        self.enabled.value = 0
        self.insertion(self.actor, 1014, b"tail", b"native")

    def test_invalid_lengths_cursor_command_and_overflow_do_not_write(self):
        self.setup_actor(3, 0xE003, 0xE003)
        for index, length in ((1013, 1019), (-1, 10), (10, 10), (9, 10), (0, 1025), (0, -1)):
            data = ctypes.create_string_buffer(b"!"*1056, 1056)
            if 0 <= index < 1024:
                ctypes.memmove(ctypes.byref(data, 16+index), b"\x7f\x1b", 2)
            before = data.raw
            self.assertEqual(self.lib.af_copy_talk_name(self.actor, ctypes.byref(data, 16), index, length), length)
            self.assertEqual(data.raw, before)
        self.assertEqual(self.lib.af_copy_talk_name(self.actor, None, 0, 2), 2)
        data = ctypes.create_string_buffer(b"\x7f\x50"+b"!"*30, 32)
        before = data.raw
        self.assertEqual(self.lib.af_copy_talk_name(self.actor, data, 0, 2), 2)
        self.assertEqual(data.raw, before)
