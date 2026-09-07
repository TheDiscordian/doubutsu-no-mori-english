"""Complete default display strings must not alter four-byte saved catchphrases."""

from copy import deepcopy
import ctypes
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from aflib import sha256, replace_dma
from catchphrases import HEADER, VROM, candidates, install, native_table, resource, validate_saved_defaults
from runtime_module import MODULE_VROM, add_runtime_module
from textbanks import banks
from test_retail import ROM_PATH


@unittest.skipUnless(shutil.which("gcc"), "Host GCC executes the original catchphrase runtime")
class CatchphraseRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        library = Path(cls.temporary.name)/"catchphrase.so"
        subprocess.run(["gcc", "-std=c99", "-Wall", "-Wextra", "-Werror", "-O2", "-shared", "-fPIC",
            "-I", str(ROOT/"runtime"), str(ROOT/"runtime/catchphrase.c"), str(ROOT/"runtime/catchphrase_fields.c"),
            str(ROOT/"tests/catchphrase_mock.c"), "-o", str(library)], check=True, capture_output=True)
        cls.lib = ctypes.CDLL(str(library))
        cls.lib.af_load_catchphrase.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p]
        cls.lib.af_get_catchphrase.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        cls.lib.af_get_catchphrase.restype = None
        cls.lib.af_copy_catchphrase.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int, ctypes.c_int]
        cls.lib.af_catchphrase_header_valid.argtypes = [ctypes.c_void_p]

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        self.header = (ctypes.c_uint*8).in_dll(self.lib, "af_catchphrase_header")
        self.header[:] = struct.unpack(">8I", HEADER)
        self.enabled = ctypes.c_uint.in_dll(self.lib, "af_catchphrase_enabled")
        self.enabled.value = 1
        self.calls = ctypes.c_uint.in_dll(self.lib, "af_catchphrase_dma_calls")
        self.calls.value = 0
        self.error = ctypes.c_uint.in_dll(self.lib, "af_catchphrase_dma_error")
        self.error.value = 0
        self.rows = (ctypes.c_ubyte*(216*16)).in_dll(self.lib, "af_catchphrase_rows")
        self.data = b"".join(struct.pack(">IH", 0xF0000000+i, 0xE000+i)+f"phrase-{i:03d}".encode() for i in range(216))
        self.rows[:] = self.data
        self.animal = (ctypes.c_ubyte*0x528).in_dll(self.lib, "af_catchphrase_animal")
        self.animal[:] = bytes(0x528)
        self.actor = ctypes.create_string_buffer(0x178)
        self.actor[2], self.actor[0x177] = 3, 1
        self.animal[0:2] = b"\xe0\x00"
        self.animal[0x4E5:0x4E9] = self.data[:4]

    def load(self, key, npc=0xE000, expected=None, capacity=10):
        saved = ctypes.create_string_buffer(b"!"+key+b"!", 6)
        output = ctypes.create_string_buffer(b"!"*32, 32)
        result = self.lib.af_load_catchphrase(ctypes.byref(output, 7), capacity, npc, ctypes.byref(saved, 1))
        self.assertEqual(saved.raw, b"!"+key+b"!")
        self.assertEqual(result, int(expected is not None))
        self.assertEqual(output.raw, b"!"*7+(expected if expected is not None else b"!"*10)+b"!"*15)
        self.assertEqual(self.error.value, 0)

    def test_every_native_id_and_sorted_key_boundary(self):
        for index in range(216):
            row = self.data[index*16:(index+1)*16]
            for npc in (0xE000+index, 0xE000+(index+1)%216):
                before = self.calls.value
                self.load(row[:4], npc, row[6:])
                self.assertLessEqual(self.calls.value-before, 12)
        for npc in range(65536):
            if not 0xE000 <= npc < 0xE0D8:
                before = self.calls.value
                self.load(self.data[:4], npc)
                self.assertEqual(self.calls.value, before)
        for key in (bytes(4), b"\xff"*4, b"test"):
            self.load(key)

    def test_duplicate_keys_prefer_own_identity_and_refuse_ambiguous_borrowing(self):
        key = self.data[:4]
        changed = bytearray(self.data)
        changed[16:20] = key
        self.rows[:] = changed
        self.load(key, 0xE000, b"phrase-000")
        self.load(key, 0xE001, b"phrase-001")
        self.load(key, 0xE002)
        changed[22:32] = b"phrase-000"
        self.rows[:] = changed
        self.load(key, 0xE002, b"phrase-000")

    @unittest.skipUnless((ROOT/"build/catchphrases/catchphrases.json").is_file() and ROM_PATH.is_file(),
                         "Complete default reference data are local-only")
    def test_every_real_default_on_every_villager(self):
        edits = json.loads((ROOT/"build/catchphrases/catchphrases.json").read_text())["edits"]
        data = resource(ROM_PATH.read_bytes(), edits)[32:]
        self.rows[:] = data
        rows = [data[i:i+16] for i in range(0, len(data), 16)]
        groups = {}
        for row in rows:
            groups.setdefault(row[:4], []).append(row)
        for key, values in groups.items():
            variants = {r[6:] for r in values}
            owners = {int.from_bytes(r[4:6], "big"): r[6:] for r in values}
            for npc in range(0xE000, 0xE0D8):
                expected = owners.get(npc, next(iter(variants)) if len(variants) == 1 else None)
                self.load(key, npc, expected)

    def test_capacity_nulls_disabled_and_header_guards(self):
        for capacity in range(10):
            self.load(self.data[:4], capacity=capacity)
        output = ctypes.create_string_buffer(b"!"*16, 16)
        for dst, src in ((None, self.data[:4]), (output, None)):
            self.assertEqual(self.lib.af_load_catchphrase(dst, 10, 0xE000, src), 0)
        self.enabled.value = 0
        self.load(self.data[:4])
        self.assertEqual(self.calls.value, 0)
        self.enabled.value = 1
        for index in range(8):
            self.header[index] ^= 1
            self.load(self.data[:4])
            self.header[index] ^= 1
        self.assertEqual(self.lib.af_catchphrase_header_valid(None), 0)

    def test_actor_resolution_custom_fallback_and_saved_data_guards(self):
        def resolve(actor, expected):
            before = bytes(self.animal)
            output = ctypes.create_string_buffer(b"!"*32, 32)
            self.lib.af_get_catchphrase(ctypes.byref(output, 7), actor)
            self.assertEqual(output.raw, b"!"*7+expected+b"!"*15)
            self.assertEqual(bytes(self.animal), before)
        resolve(self.actor, b"phrase-000")
        self.enabled.value = 0
        resolve(self.actor, self.data[:4]+b" "*6)
        self.enabled.value = 1
        self.animal[0x4E5:0x4E9] = b"Yup!"
        resolve(self.actor, b"Yup!      ")
        self.actor[0x177] = 0
        resolve(self.actor, b"none      ")
        self.actor[2], self.actor[0x177] = 2, 1
        resolve(self.actor, b"none      ")
        resolve(None, b" "*10)
        self.lib.af_get_catchphrase(None, self.actor)

    def test_main_message_insertion_limits_and_invalid_commands(self):
        for index, length in ((0, 6), (1, 7), (100, 106), (1010, 1016), (1011, 1017)):
            original = b"p"*index+b"\x7f\x1c"+b"tail"
            expected = b"p"*index+b"phrase-000tail"
            output = ctypes.create_string_buffer(b"!"*16+original.ljust(1024, b" ")+b"!"*16, 1056)
            before, saved = output.raw, bytes(self.animal)
            result = self.lib.af_copy_catchphrase(self.actor, ctypes.byref(output, 16), index, length)
            if len(expected) > 1024:
                self.assertEqual((result, output.raw), (length, before))
            else:
                self.assertEqual((result, output.raw[16:16+result]), (len(expected), expected))
            self.assertEqual(output.raw[:16]+output.raw[1040:], b"!"*32)
            self.assertEqual(bytes(self.animal), saved)
        for index, length in ((-1, 10), (10, 10), (9, 10), (0, 1025), (0, -1), (0, 2)):
            output = ctypes.create_string_buffer(b"\x7f\x50"+b"!"*1022, 1024)
            before = output.raw
            self.assertEqual(self.lib.af_copy_catchphrase(self.actor, output, index, length), length)
            self.assertEqual(output.raw, before)
        self.assertEqual(self.lib.af_copy_catchphrase(self.actor, None, 0, 2), 2)
        output = ctypes.create_string_buffer(b"\x7f\x1ctail"+b"!"*10, 16)
        self.assertEqual(self.lib.af_copy_catchphrase(None, output, 0, 6), 4)
        self.assertEqual(output.raw[:4], b"tail")


@unittest.skipUnless(ROM_PATH.is_file() and (ROOT/"build/gamecube/files/foresta.rel.szs.decoded").is_file(),
                     "Catchphrase source/reference data are local-only")
class CatchphraseResourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM_PATH.read_bytes()
        cls.edits = candidates(cls.rom, ROOT/"build/inventory", ROOT/"build/gamecube/names",
                               ROOT/"build/gamecube/text", ROOT/"build/gamecube/files", ROOT/"local/ac-decomp")

    def test_complete_hash_bound_reference_rows(self):
        data = resource(self.rom, self.edits)
        self.assertEqual((len(data), data[:32]), (3488, HEADER))
        rows = [data[i:i+16] for i in range(32, len(data), 16)]
        self.assertEqual(rows, sorted(rows))
        self.assertEqual(len({r[:4] for r in rows}), 214)
        self.assertEqual({int.from_bytes(r[4:6], "big") for r in rows}, set(range(0xE000, 0xE0D8)))
        for edits in (self.edits[:-1], [*self.edits, self.edits[0]]):
            with self.assertRaises(ValueError):
                resource(self.rom, edits)
        for field, value in (("source_sha256", "0"*64), ("translation", "a"*11), ("translation", "{cmd:7F01}")):
            edited = deepcopy(self.edits)
            edited[0][field] = value
            with self.assertRaises(ValueError):
                resource(self.rom, edited)
        for field in ("reference_id", "reference_sha256", "default_table_sha256"):
            edited = deepcopy(self.edits)
            edited[0]["provenance"][field] = "wrong"
            with self.assertRaisesRegex(ValueError, "identity/hash"):
                resource(self.rom, edited)

    def test_saved_defaults_allow_only_native_or_complete_short_english(self):
        bank = next(b for b in banks(self.rom) if b.name == "string")
        entries = bank.entries()
        validate_saved_defaults(self.rom, {}, self.edits)
        index = native_table(self.rom)[0][1]
        entries[index] = b"test"
        data, table = bank.rebuild(entries)
        with self.assertRaisesRegex(ValueError, "complete verified default"):
            validate_saved_defaults(self.rom, {bank.data_vrom: data, bank.table_vrom: table}, self.edits)

    @unittest.skipUnless((ROOT/"build/runtime-module/module.json").is_file()
                         and (ROOT/"build/catchphrases/catchphrases.json").is_file(),
                         "Native-call scenarios bind to the local experimental ROM")
    def test_native_scenario_uses_unsigned_o32_arguments_and_restores_checkpoint(self):
        from catchphrase_test_scenario import scenario
        replacements = {}
        additions, module = add_runtime_module(self.rom, replacements, ROOT/"build/runtime-module")
        reference = json.loads((ROOT/"build/catchphrases/catchphrases.json").read_text())
        install(self.rom, additions, module, ROOT/"build/catchphrases")
        # Bind the current source-built module and resource together; a historical
        # pilot ROM must not accidentally provide stale symbols for this test.
        actions = scenario(replace_dma(self.rom, replacements, additions=additions), module, reference)
        calls = [a["call"] for a in actions if "call" in a]
        self.assertGreaterEqual(len(calls), 216)
        for call in calls:
            self.assertTrue(0x80051A80 <= int(call["address"], 16) <= 0x8019A8E0)
            self.assertTrue(all(type(value) is int and 0 <= value <= 0xFFFFFFFF for value in call["arguments"]))
        self.assertTrue(any(0xFFFFFFFF in call["arguments"] for call in calls))
        self.assertTrue(any(a.get("load_state") for a in actions))
        self.assertEqual(actions[2], {"pause_game_thread": True})

    @unittest.skipUnless((ROOT/"build/runtime-module/module.json").is_file(), "Build the resident module first")
    def test_resource_configuration_and_mutation_guards(self):
        from display_names import install as display_install
        from extended_items import install as item_install
        additions, module = add_runtime_module(self.rom, {}, ROOT/"build/runtime-module")
        data = resource(self.rom, self.edits)
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory/"catchphrases.bin").write_bytes(data)
            (directory/"catchphrases.json").write_text(json.dumps({"source_sha256": sha256(self.rom),
                "data_sha256": sha256(data), "edits": self.edits}))
            for invalid, report in (({}, module), (additions, None)):
                with self.assertRaisesRegex(ValueError, "capable resident"):
                    install(self.rom, dict(invalid), report, directory)
            enabled = dict(additions)
            install(self.rom, enabled, module, directory)
            self.assertEqual(enabled[VROM], data)
            self.assertEqual(enabled[MODULE_VROM][64:68], VROM.to_bytes(4, "big"))
            self.assertEqual(enabled[MODULE_VROM][:64], additions[MODULE_VROM][:64])
            self.assertEqual(enabled[MODULE_VROM][68:], additions[MODULE_VROM][68:])
            with self.assertRaises(ValueError):
                install(self.rom, enabled, module, directory)
            changed = bytearray(additions[MODULE_VROM])
            changed[512] ^= 1
            with self.assertRaisesRegex(ValueError, "verified module"):
                install(self.rom, {MODULE_VROM: changed}, module, directory)
            if (ROOT/"build/alias-items/names.json").is_file() and (ROOT/"build/display-names/names.json").is_file():
                enabled = dict(additions)
                item_install(self.rom, enabled, module, ROOT/"build/alias-items")
                display_install(self.rom, enabled, module, ROOT/"build/display-names")
                install(self.rom, enabled, module, directory)
                self.assertEqual(enabled[MODULE_VROM][56:68], struct.pack(">3I", 0x02A00000, 0x02C00000, VROM))
            (directory/"catchphrases.bin").write_bytes(data[:-16])
            with self.assertRaisesRegex(ValueError, "resource"):
                install(self.rom, dict(additions), module, directory)
