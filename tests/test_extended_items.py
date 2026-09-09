"""Capacity-aware item resource and portable runtime contracts."""

from copy import deepcopy
import ctypes
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = Path(os.environ.get('AF_TEST_RUNTIME_MODULE', str(ROOT/'build/runtime-module')))
sys.path.insert(0, str(ROOT/"tools"))
from aflib import sha256
from extended_items import COUNTS, HEADER, WIDTH, VROM, install, resource
from runtime_module import MODULE_VROM, add_runtime_module
from item_names_test_scenario import ordinary_item
from test_retail import ROM_PATH


@unittest.skipUnless(shutil.which("gcc"), "Host GCC executes the original portable item runtime")
class ExtendedItemRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        library = Path(cls.temporary.name)/"item_name.so"
        subprocess.run(["gcc", "-std=c99", "-Wall", "-Wextra", "-Werror", "-O2", "-shared", "-fPIC",
                        "-I", str(ROOT/"runtime"), str(ROOT/"runtime/item_name.c"),
                        str(ROOT/"tests/item_name_mock.c"), "-o", str(library)], check=True, capture_output=True)
        cls.lib = ctypes.CDLL(str(library))
        cls.lib.af_load_item_name.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint]
        cls.lib.af_load_item_name.restype = ctypes.c_int
        cls.lib.af_item_name_index.argtypes = [ctypes.c_uint]
        cls.lib.af_item_name_index.restype = ctypes.c_int
        cls.lib.af_item_header_valid.argtypes = [ctypes.c_void_p]
        cls.lib.af_item_header_valid.restype = ctypes.c_int

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        self.enabled = ctypes.c_uint.in_dll(self.lib, "af_test_enabled")
        self.enabled.value = 1
        self.calls = ctypes.c_uint.in_dll(self.lib, "af_test_dma_calls")
        self.calls.value = 0
        self.error = ctypes.c_uint.in_dll(self.lib, "af_test_dma_error")
        self.error.value = 0
        self.header = (ctypes.c_uint*8).in_dll(self.lib, "af_test_header")
        self.header[:] = (0x4146494E, 1, 16, 4544, 0, 0, 0, 0)

    def test_every_native_item_and_invalid_index(self):
        indices, offset = {}, 0
        for group, count in zip([*range(0x20, 0x30), 0x10], COUNTS):
            for index in range(count):
                item = 0x1000+index if group == 0x10 else (group << 8)+index
                indices[item] = offset+index
            offset += count
        for item in range(65536):
            self.assertEqual(self.lib.af_item_name_index(item), indices.get(item, -1))
            guard = ctypes.create_string_buffer(b"!"*40, 40)
            result = self.lib.af_load_item_name(ctypes.byref(guard, 7), 24, item)
            index = indices.get(ordinary_item(item))
            if item == 0:
                expected = b" "*16
            elif index is not None:
                expected = bytes(32+(index+i) % 95 for i in range(16))
            else:
                expected = b"!"*16
            self.assertEqual(result, int(item == 0 or index is not None))
            self.assertEqual(guard.raw, b"!"*7+expected+b"!"*17)
        self.assertEqual(self.error.value, 0)

    def test_bad_capacities_pointer_resource_and_header_do_not_write(self):
        for capacity in range(16):
            guard = ctypes.create_string_buffer(b"!"*40, 40)
            self.assertEqual(self.lib.af_load_item_name(guard, capacity, 0x2200), 0)
            self.assertEqual(guard.raw, b"!"*40)
        self.assertEqual(self.lib.af_load_item_name(None, 16, 0x2200), 0)
        self.assertEqual(self.lib.af_item_name_index(0x12200), -1)
        self.assertEqual(self.calls.value, 0)
        guard = ctypes.create_string_buffer(b"!"*40, 40)
        self.enabled.value = 0
        self.assertEqual(self.lib.af_load_item_name(guard, 16, 0x2200), 0)
        self.assertEqual(self.calls.value, 0)
        self.enabled.value = 1
        for index in range(8):
            self.header[index] ^= 1
            for item in (0, 0x2200):
                self.assertEqual(self.lib.af_load_item_name(guard, 16, item), 0)
                self.assertEqual(guard.raw, b"!"*40)
            self.header[index] ^= 1
        self.assertEqual(self.lib.af_item_header_valid(None), 0)
        self.assertEqual(self.lib.af_load_item_name(guard, 16, 0x12200), 0)
        self.assertEqual(guard.raw, b"!"*40)


@unittest.skipUnless(ROM_PATH.is_file(), "Native ROM is a local-only resource test input")
class ExtendedItemResourceTests(unittest.TestCase):
    def test_native_resource_layout_and_long_reference_guards(self):
        from textbanks import banks
        rom = ROM_PATH.read_bytes()
        original = resource(rom, [])
        self.assertEqual(original[:32], HEADER)
        self.assertEqual(len(original), 32+4544*16)
        bank = next(b for b in banks(rom) if b.name == "item_22")
        native = bank.entries()[3]
        edit = {"id": "item_22:0003", "source_sha256": sha256(native), "translation": "fishing rod",
                "provenance": {"reference_id": "item_22:0003",
                               "reference_sha256": sha256(b"fishing rod".ljust(16, b" "))}}
        # Retain the complete approved reference identity as well as its hash.
        result = resource(rom, [edit])
        offset = 32+(64+4+3)*16
        self.assertEqual(result[:offset], original[:offset])
        self.assertEqual(result[offset:offset+16], b"fishing rod     ")
        self.assertEqual(result[offset+16:], original[offset+16:])
        for edits in ([edit, edit], [{**edit, "source_sha256": "0"*64}],
                      [{**edit, "translation": "A"*17}], [{**edit, "id": "item_22:FFFF"}]):
            with self.assertRaises(ValueError):
                resource(rom, edits)
        changed = deepcopy(edit)
        changed["provenance"]["reference_sha256"] = "0"*64
        with self.assertRaisesRegex(ValueError, "complete exact English reference"):
            resource(rom, [changed])

    @unittest.skipUnless((MODULE_DIR/"module.json").is_file(), "Build the resident module first")
    def test_installation_requires_exact_resource_and_module(self):
        rom = ROM_PATH.read_bytes()
        additions, module = add_runtime_module(rom, {}, MODULE_DIR)
        data = resource(rom, [])
        manifest = {"source_sha256": sha256(rom), "data_sha256": sha256(data), "edits": []}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path/"names.bin").write_bytes(data)
            (path/"names.json").write_text(json.dumps(manifest))
            for incorrect, report in (({}, module), (additions, None)):
                with self.assertRaisesRegex(ValueError, "capable resident"):
                    install(rom, dict(incorrect), report, path)
            configured = dict(additions)
            report = install(rom, configured, module, path)
            self.assertEqual(configured[VROM], data)
            expected = bytearray(additions[MODULE_VROM])
            expected[56:60] = VROM.to_bytes(4, "big")
            self.assertEqual(configured[MODULE_VROM], bytes(expected))
            self.assertEqual(report["configured_module_sha256"], sha256(expected))
            with self.assertRaises(ValueError):
                install(rom, configured, module, path)
            bad = bytearray(additions[MODULE_VROM])
            bad[512] ^= 1
            with self.assertRaisesRegex(ValueError, "verified module"):
                install(rom, {MODULE_VROM: bytes(bad)}, module, path)
            (path/"names.bin").write_bytes(data[:-16])
            with self.assertRaisesRegex(ValueError, "resource"):
                install(rom, dict(additions), module, path)
            bad = bytearray(data)
            bad[32] ^= 1
            manifest["data_sha256"] = sha256(bad)
            (path/"names.bin").write_bytes(bad)
            (path/"names.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "resource"):
                install(rom, dict(additions), module, path)
