"""Original item-field storage and bounded message insertion execute on the host."""

import ctypes
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("gcc"), "Host GCC executes the original item-field implementation")
class ItemFieldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        library = Path(cls.temporary.name)/"item_fields.so"
        subprocess.run(["gcc", "-std=c99", "-Wall", "-Wextra", "-Werror", "-O2", "-shared", "-fPIC",
                        "-I", str(ROOT/"runtime"), str(ROOT/"runtime/item_name.c"),
                        str(ROOT/"runtime/item_fields.c"), str(ROOT/"tests/item_name_mock.c"),
                        "-o", str(library)], check=True, capture_output=True)
        cls.lib = ctypes.CDLL(str(library))
        cls.lib.af_set_item_str.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_int]
        cls.lib.af_set_item_str.restype = None
        cls.lib.af_copy_item_string.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
        cls.lib.af_copy_item_string.restype = ctypes.c_int
        cls.lib.af_quest_set_item.argtypes = [ctypes.c_uint, ctypes.c_int]
        cls.lib.af_quest_set_item.restype = None

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        self.window = (ctypes.c_ubyte*0x300).in_dll(self.lib, "af_test_window")
        ctypes.memset(self.window, 0x47, len(self.window))
        self.enabled = ctypes.c_uint.in_dll(self.lib, "af_test_enabled")
        self.enabled.value = 1
        self.native_calls = ctypes.c_uint.in_dll(self.lib, "af_test_native_calls")
        self.native_calls.value = 0
        for slot in range(5):
            self.lib.af_set_item_str(self.window, slot, b"", 0)

    def inserted(self, slot, name, window=None, index=0, suffix=b"tail"):
        if window is None:
            window = self.window
        original = b"p"*index+b"\x7f\x31"+suffix
        data = ctypes.create_string_buffer(b"!"*16+original.ljust(1024, b" ")+b"!"*16, 1056)
        expected = b"p"*index+name.rstrip(b" ")+suffix
        result = self.lib.af_copy_item_string(window, slot, ctypes.byref(data, 16), index, len(original))
        self.assertEqual(result, len(expected))
        self.assertEqual(data.raw[:16], b"!"*16)
        self.assertEqual(data.raw[1040:], b"!"*16)
        self.assertEqual(data.raw[16:16+result], expected)

    def test_all_fields_lengths_positions_and_shorter_replacement(self):
        for slot in range(5):
            for size in (16, 11, 10, 1, 0):
                name = b"abcdefghijklmnoP"[:size]
                before = bytes(self.window)
                self.lib.af_set_item_str(self.window, slot, name, len(name))
                offset = 0x100+slot*10
                self.assertEqual(bytes(self.window), before[:offset]+name[:10].ljust(10, b" ")+before[offset+10:])
                for index in (0, 1, 100, 990):
                    self.inserted(slot, name, index=index)
        self.lib.af_set_item_str(self.window, 0, b"first", 5)
        self.inserted(-1, b"first")
        self.inserted(5, b"first")

    def test_invalid_setters_no_write_and_alias_source(self):
        self.lib.af_set_item_str(self.window, 0, b"abcdefghijklmnop", 16)
        before = bytes(self.window)
        for window, slot, source, length in ((None, 0, b"x", 1), (self.window, -1, b"x", 1),
                                           (self.window, 5, b"x", 1), (self.window, 0, None, 1),
                                           (self.window, 0, b"x"*17, 17)):
            self.lib.af_set_item_str(window, slot, source, length)
            self.assertEqual(bytes(self.window), before)
            self.inserted(0, b"abcdefghijklmnop")
        self.lib.af_set_item_str(self.window, 0, ctypes.byref(self.window, 0x100), 10)
        self.inserted(0, b"abcdefghij")
        self.lib.af_set_item_str(self.window, 0, b"x", -1)
        self.inserted(0, b"")

    def test_other_windows_retain_ten_byte_capacity(self):
        other = ctypes.create_string_buffer(b"G"*0x300, 0x300)
        self.lib.af_set_item_str(other, 2, b"abcdefghijklmnop", 16)
        self.assertEqual(other.raw, b"G"*0x300)
        self.lib.af_set_item_str(other, 2, b"short", 5)
        self.inserted(2, b"short", other)
        self.assertEqual(other.raw[0x114:0x11E], b"short     ")

    def test_message_limit_and_invalid_inputs_do_not_write(self):
        self.lib.af_set_item_str(self.window, 0, b"abcdefghijklmnop", 16)
        self.inserted(0, b"abcdefghijklmnop", index=1004, suffix=b"tail")
        for index, length, window, pointer in ((1005, 1011, self.window, True), (-1, 20, self.window, True),
                                              (20, 20, self.window, True), (19, 20, self.window, True),
                                              (0, 1025, self.window, True), (0, -1, self.window, True),
                                              (0, 20, None, True), (0, 20, self.window, False)):
            data = ctypes.create_string_buffer(b"G"*1056, 1056)
            if index >= 0 and index < 1024:
                ctypes.memmove(ctypes.byref(data, 16+index), b"\x7f\x31", 2)
            before = data.raw
            result = self.lib.af_copy_item_string(window, 0, ctypes.byref(data, 16) if pointer else None, index, length)
            self.assertEqual(result, length)
            self.assertEqual(data.raw, before)

    def test_item_wrapper_full_resource_and_native_fallback(self):
        self.lib.af_quest_set_item(0x2200, 4)
        self.inserted(4, bytes(32+(68+i) % 95 for i in range(16)))
        self.assertEqual(self.native_calls.value, 0)
        self.enabled.value = 0
        self.lib.af_quest_set_item(0x2200, 4)
        expected = bytes(65+(0x2200+i) % 26 for i in range(10))
        self.inserted(4, expected)
        self.assertEqual(self.native_calls.value, 1)
        before = bytes(self.window)
        for item, slot in ((0, 4), (0xFFFF, 4), (0x2200, -1), (0x2200, 5)):
            self.lib.af_quest_set_item(item, slot)
            self.assertEqual(bytes(self.window), before)
            self.inserted(4, expected)
        self.assertEqual(self.native_calls.value, 1)
