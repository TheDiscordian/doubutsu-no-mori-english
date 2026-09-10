"""Display names are independent of saved names and all native six-byte APIs."""

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
sys.path.insert(0, str(ROOT/"tools"))
from aflib import sha256
from display_names import HEADER, SPECIAL_HASH, VROM, candidates, install, resource, special_table
from runtime_module import MODULE_VROM, add_runtime_module
from test_retail import ROM_PATH

MODULE_DIR = Path(os.environ.get('AF_TEST_RUNTIME_MODULE', str(ROOT/'build/notice-seasonal-runtime')))


@unittest.skipUnless(shutil.which("gcc"), "Host GCC executes the original display-name API")
class DisplayNameRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        library = Path(cls.temporary.name)/"display_name.so"
        subprocess.run(["gcc", "-std=c99", "-Wall", "-Wextra", "-Werror", "-O2", "-shared", "-fPIC",
                        "-I", str(ROOT/"runtime"), str(ROOT/"runtime/display_name.c"),
                        str(ROOT/"tests/display_name_mock.c"), "-o", str(library)], check=True, capture_output=True)
        cls.lib = ctypes.CDLL(str(library))
        cls.lib.af_load_display_name.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint]
        cls.lib.af_display_name_index.argtypes = [ctypes.c_uint]
        cls.lib.af_display_name_header_valid.argtypes = [ctypes.c_void_p]

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        self.enabled = ctypes.c_uint.in_dll(self.lib, "af_display_enabled")
        self.enabled.value = 1
        self.calls = ctypes.c_uint.in_dll(self.lib, "af_display_dma_calls")
        self.calls.value = 0
        self.error = ctypes.c_uint.in_dll(self.lib, "af_display_dma_error")
        self.error.value = 0
        self.header = (ctypes.c_uint*8).in_dll(self.lib, "af_display_header")
        self.header[:] = (0x41464E4E, 1, 8, 280, 216, 64, 0, 0)
        self.special = (ctypes.c_ushort*64).in_dll(self.lib, "af_display_special_ids")
        self.special[:] = range(0xD000, 0xD040)

    def test_every_id_pair_alignment_capacity_and_adjacent_guards(self):
        indices = {0xE000+i: i for i in range(216)}
        indices.update({npc: 216+i for i, npc in enumerate(self.special)})
        for npc in range(65536):
            self.assertEqual(self.lib.af_display_name_index(npc), indices.get(npc, -1))
            guard = ctypes.create_string_buffer(b"!"*40, 40)
            result = self.lib.af_load_display_name(ctypes.byref(guard, 7), 16, npc)
            if npc in indices:
                expected = bytes(32+(indices[npc]*8+i) % 95 for i in range(8))
                self.assertEqual(result, 1)
                self.assertEqual(guard.raw, b"!"*7+expected+b"!"*25)
            else:
                self.assertEqual((result, guard.raw), (0, b"!"*40))
        self.assertEqual(self.error.value, 0)

    def test_no_writes_for_bad_capacity_disabled_resource_or_header(self):
        guard = ctypes.create_string_buffer(b"!"*40, 40)
        for capacity in range(8):
            self.assertEqual(self.lib.af_load_display_name(guard, capacity, 0xE000), 0)
        self.assertEqual(self.lib.af_load_display_name(None, 8, 0xE000), 0)
        self.assertEqual(self.lib.af_load_display_name(guard, 8, 0x1E000), 0)
        self.assertEqual(self.calls.value, 0)
        self.enabled.value = 0
        self.assertEqual(self.lib.af_load_display_name(guard, 8, 0xE000), 0)
        self.assertEqual(self.calls.value, 0)
        self.enabled.value = 1
        for index in range(8):
            self.header[index] ^= 1
            self.assertEqual(self.lib.af_load_display_name(guard, 8, 0xE000), 0)
            self.header[index] ^= 1
        self.assertEqual(self.lib.af_display_name_header_valid(None), 0)
        self.assertEqual(guard.raw, b"!"*40)

    @unittest.skipUnless(ROM_PATH.is_file(), "Native special actor table is local-only")
    def test_actual_special_ids_and_all_other_native_ids(self):
        self.special[:] = [r[0] for r in special_table(ROM_PATH.read_bytes())]
        indices = {0xE000+i: i for i in range(216)}
        indices.update({npc: 216+i for i, npc in enumerate(self.special)})
        for npc in range(65536):
            self.assertEqual(self.lib.af_display_name_index(npc), indices.get(npc, -1))


@unittest.skipUnless(ROM_PATH.is_file() and (ROOT/"build/gamecube/names/npc_names.jsonl").is_file(),
                     "ROM and extracted references are local-only inputs")
class DisplayNameResourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM_PATH.read_bytes()
        cls.edits = candidates(cls.rom, ROOT/"build/inventory", ROOT/"build/gamecube/names", ROOT/"build/gamecube/text")

    def test_all_confirmed_names_and_resource_guards(self):
        data = resource(self.rom, self.edits)
        self.assertEqual(len(self.edits), 280)
        self.assertEqual(len(data), 2272)
        self.assertEqual(data[:32], HEADER)
        self.assertEqual(data[32+216*8:32+217*8], b"Tom Nook")
        self.assertEqual(data[32+0x52*8:32+0x53*8], b"Cousteau")
        for edits in (self.edits[:-1], [*self.edits, self.edits[0]],
                      [{**self.edits[0], "translation": "A"*9}, *self.edits[1:]],
                      [{**self.edits[0], "source_sha256": "0"*64}, *self.edits[1:]]):
            with self.assertRaises(ValueError):
                resource(self.rom, edits)
        for field, value in (("reference_id", "npc_names:00FF"), ("reference_sha256", "0"*64)):
            changed = deepcopy(self.edits)
            changed[0]["provenance"][field] = value
            with self.assertRaisesRegex(ValueError, "identity/hash"):
                resource(self.rom, changed)

    @unittest.skipUnless((MODULE_DIR/"module.json").is_file(), "Build the current resident module first")
    def test_module_configuration_and_combined_item_resource(self):
        from extended_items import install as item_install, VROM as ITEM_VROM
        additions, module = add_runtime_module(self.rom, {}, MODULE_DIR)
        data = resource(self.rom, self.edits)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            manifest = {"source_sha256": sha256(self.rom), "data_sha256": sha256(data),
                        "special_table_sha256": SPECIAL_HASH, "edits": self.edits}
            (path/"names.bin").write_bytes(data)
            (path/"names.json").write_text(json.dumps(manifest))
            for invalid, report in (({}, module), (additions, None)):
                with self.assertRaisesRegex(ValueError, "capable resident"):
                    install(self.rom, dict(invalid), report, path)
            result = dict(additions)
            install(self.rom, result, module, path)
            self.assertEqual(result[VROM], data)
            expected = bytearray(additions[MODULE_VROM])
            expected[60:64] = VROM.to_bytes(4, "big")
            self.assertEqual(result[MODULE_VROM], bytes(expected))
            with self.assertRaises(ValueError):
                install(self.rom, result, module, path)
            bad = bytearray(additions[MODULE_VROM])
            bad[512] ^= 1
            with self.assertRaisesRegex(ValueError, "verified module"):
                install(self.rom, {MODULE_VROM: bytes(bad)}, module, path)
            if (ROOT/"build/design-items-resource/names.json").is_file():
                result = dict(additions)
                item_install(self.rom, result, module, ROOT/"build/design-items-resource")
                install(self.rom, result, module, path)
                self.assertIn(ITEM_VROM, result)
                self.assertEqual(result[MODULE_VROM][56:64], ITEM_VROM.to_bytes(4, "big")+VROM.to_bytes(4, "big"))
            (path/"names.bin").write_bytes(data[:-8])
            with self.assertRaisesRegex(ValueError, "resource"):
                install(self.rom, dict(additions), module, path)
