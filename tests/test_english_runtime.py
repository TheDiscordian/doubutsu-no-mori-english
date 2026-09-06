"""Source-independent guards and optional verified-retail integration tests."""

from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from build import apply_translations
from english_runtime import (CHOICE_ROWS, CHOICE_SELECTED, ChoiceLayout, GuardedCode, PLAYER_SELECT_RAM,
                             PLAYER_SELECT_VROM, QUEST_RAM, QUEST_VROM, TOWN_RETURN,
                             WIDTH_CODE, make_english_runtime, verify_english_runtime)
from runtime_module import add_runtime_module
from font import make_halfwidth
from textbanks import banks
from textcodec import command_info, tokenize
from textvalidate import validate_entry
from test_retail import ROM_PATH


class RuntimeGuardTests(unittest.TestCase):
    def test_instruction_and_source_guards(self):
        source = struct.pack(">2I", 0x2405000A, 0x2406000B)
        guard = GuardedCode(source, source, 0x80000000, sha256(source))
        guard.immediate(0x80000000, 10, 16)
        self.assertEqual(guard.data[:4], bytes.fromhex("24050010"))
        with self.assertRaisesRegex(ValueError, "Overlapping"):
            guard.immediate(0x80000000, 10, 16)
        with self.assertRaisesRegex(ValueError, "immediate"):
            guard.immediate(0x80000004, 10, 16)
        with self.assertRaisesRegex(ValueError, "source"):
            GuardedCode(source, source, 0, "bad")
        corrupt = bytearray(source)
        corrupt[3] = 12
        guard = GuardedCode(source, corrupt, 0x80000000, sha256(source))
        with self.assertRaisesRegex(ValueError, "instruction guard"):
            guard.immediate(0x80000000, 10, 16)

    def test_capacity_requires_plain_bounded_choices(self):
        info = [(2, 0)]*0x61
        validate_entry(b"A", b"A"*16, info, "select", choice_bytes=16)
        for size in (17, 100):
            with self.assertRaisesRegex(ValueError, "16-byte"):
                validate_entry(b"A", b"A"*size, info, "select", choice_bytes=16)
        with self.assertRaisesRegex(ValueError, "10-byte"):
            validate_entry(b"A", b"A"*16, info, "select")
        for data in (b"\x7f\x1a", b"\x80\x42"):
            with self.assertRaisesRegex(ValueError, "plain text"):
                validate_entry(data, data, info, "select", choice_bytes=16)
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            validate_entry(b"A", b"B", info, "select", choice_bytes=64)
        validate_entry(b"A", b"A"*20, info, "select", choice_bytes=20, resident_runtime=True)
        with self.assertRaisesRegex(ValueError, "20-byte"):
            validate_entry(b"A", b"A"*21, info, "select", choice_bytes=20, resident_runtime=True)
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            validate_entry(b"A", b"A"*20, info, "select", choice_bytes=20)
        with self.assertRaisesRegex(ValueError, "plain text"):
            validate_entry(b"\x7f\x1a", b"\x7f\x1a", info, "select", choice_bytes=20, resident_runtime=True)

    def test_invalid_resident_layouts(self):
        for values in ((20, 20, 0x80196000, 0x80196080), (20, 32, 0x80196001, 0x80196081),
                       (20, 32, 0x80198840, 0x801988C0), (20, 32, 0x80096000, 0x80096080)):
            with self.assertRaisesRegex(ValueError, "layout"):
                ChoiceLayout(*values)


@unittest.skipUnless(ROM_PATH.is_file(), "Retail ROM is a local-only optional test input")
class RuntimeRetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM_PATH.read_bytes()
        cls.files = by_vrom(cls.rom)
        cls.font, _ = make_halfwidth(cls.rom)
        cls.runtime, cls.report = make_english_runtime(cls.rom, cls.font)

    def test_runtime_storage_bounds_and_preserved_file_sizes(self):
        self.assertEqual(CHOICE_SELECTED-CHOICE_ROWS, 64)
        self.assertLessEqual(CHOICE_SELECTED+16, 0x8009F50C)
        for vrom, current in self.runtime.items():
            original = self.font.get(vrom, self.files[vrom].extract(self.rom))
            self.assertEqual(len(current), len(original))
            ram = {CODE_VROM: CODE_RAM, QUEST_VROM: QUEST_RAM, PLAYER_SELECT_VROM: PLAYER_SELECT_RAM}[vrom]
            allowed = set()
            for change in self.report["files"][f"{vrom:08X}"]["changes"]:
                offset = int(change["ram"], 16)-ram
                allowed.update(range(offset, offset+change["bytes"]))
            self.assertFalse(any(a != b and i not in allowed for i, (a, b) in enumerate(zip(original, current))))
        code = self.runtime[CODE_VROM]
        self.assertEqual(code[0x8009F4A4-CODE_RAM:CHOICE_ROWS-CODE_RAM], TOWN_RETURN)
        self.assertEqual(code[CHOICE_ROWS-CODE_RAM:CHOICE_SELECTED+16-CODE_RAM], b" "*80)
        self.assertEqual(code[0x80065348-CODE_RAM:0x800653CC-CODE_RAM], WIDTH_CODE)

    def test_expanded_actor_frames_and_lengths(self):
        quest = self.runtime[QUEST_VROM]
        player = self.runtime[PLAYER_SELECT_VROM]
        def word(data, address, base):
            return struct.unpack_from(">I", data, address-base)[0]
        self.assertEqual(word(quest, 0x80955814, QUEST_RAM), 0x27BDFF38)
        self.assertEqual(word(quest, 0x8095593C, QUEST_RAM), 0x27BD00C8)
        self.assertEqual(word(player, 0x809BF244, PLAYER_SELECT_RAM), 0x27BDFF60)
        self.assertEqual(word(player, 0x809BF3D8, PLAYER_SELECT_RAM), 0x27BD00A0)
        self.assertEqual(word(player, 0x809BF3E4, PLAYER_SELECT_RAM), 0x27BDFF68)
        self.assertEqual(word(player, 0x809BF4B4, PLAYER_SELECT_RAM), 0x27BD0098)
        # Pointer immediately above each expanded array and incoming arguments.
        self.assertEqual(word(player, 0x809BF264, PLAYER_SELECT_RAM), 0xAFA2009C)
        self.assertEqual(word(player, 0x809BF260, PLAYER_SELECT_RAM), 0x8FAE00A0)
        self.assertEqual(word(player, 0x809BF404, PLAYER_SELECT_RAM), 0xAFA20094)
        self.assertEqual(word(player, 0x809BF418, PLAYER_SELECT_RAM), 0x8FB9009C)

    def test_retained_choices_are_plain_and_capability_is_verified(self):
        info = command_info(self.files[CODE_VROM].extract(self.rom))
        choices = next(bank for bank in banks(self.rom) if bank.name == "select").entries()
        self.assertEqual(len(choices), 460)
        self.assertTrue(all(token.kind == "text" for choice in choices for token in tokenize(choice, info)))
        verify_english_runtime(self.rom, self.runtime)
        for vrom in self.runtime:
            incomplete = dict(self.runtime)
            incomplete.pop(vrom)
            with self.assertRaisesRegex(ValueError, "complete English runtime"):
                verify_english_runtime(self.rom, incomplete)
        with self.assertRaisesRegex(ValueError, "English runtime"):
            apply_translations(self.rom, self.font.copy(), None, english_runtime=True)
        replacements = {**self.font, **self.runtime}
        apply_translations(self.rom, replacements, ROOT/"translations/opening.json", english_runtime=True)
        verify_english_runtime(self.rom, replacements)  # Bank relocation coexists.

    def test_double_application_rejected(self):
        with self.assertRaisesRegex(ValueError, "instruction guard"):
            make_english_runtime(self.rom, self.runtime)

    def test_twenty_byte_frames_strides_and_loader(self):
        layout = ChoiceLayout(20, 32, 0x80196000, 0x80196080)
        runtime, report = make_english_runtime(self.rom, self.font, layout)
        self.assertEqual(report["largest_added_stack_bytes"], 40)
        def word(vrom, ram, address):
            return struct.unpack_from(">I", runtime[vrom], address-ram)[0]
        for vrom, ram, pairs in (
            (CODE_VROM, CODE_RAM, ((0x800A0F14, 0x26310020), (0x80066D00, 0x26B50020),
                                 (0x80065204, 0x0009C140), (0x80066150, 0x24850080),
                                 (0x80065D90, 0x27BDFF90), (0x80065E18, 0x27A40048),
                                 (0x80065E1C, 0x8FA30068))),
            (QUEST_VROM, QUEST_RAM, ((0x80955814, 0x27BDFF28), (0x8095593C, 0x27BD00D8),
                                    (0x80955880, 0x0018C080), (0x80955884, 0x00084080))),
            (PLAYER_SELECT_VROM, PLAYER_SELECT_RAM,
             ((0x809BF244, 0x27BDFF50), (0x809BF3D8, 0x27BD00B0),
              (0x809BF3E4, 0x27BDFF58), (0x809BF4B4, 0x27BD00A8),
              (0x809BF264, 0xAFA200AC), (0x809BF404, 0xAFA200A4))),
        ):
            for address, expected in pairs:
                self.assertEqual(word(vrom, ram, address), expected, f"{address:08X}")
        # Staging ends before the live length temporary for every ROM alignment.
        self.assertTrue(all(((offset+20+7) & ~7) <= 0x68-0x48 for offset in range(8)))
        verify_english_runtime(self.rom, runtime, layout)
        with self.assertRaisesRegex(ValueError, "Missing English runtime"):
            verify_english_runtime(self.rom, runtime)

    @unittest.skipUnless((ROOT/"build/runtime-module/module.json").is_file(), "Build resident module first")
    def test_resident_choice_capability_requires_both_patch_sets(self):
        directory = ROOT/"build/runtime-module"
        replacements = dict(self.font)
        additions, report = add_runtime_module(self.rom, replacements, directory)
        layout = ChoiceLayout(**report["choice_layout"])
        with self.assertRaisesRegex(ValueError, "English runtime"):
            apply_translations(self.rom, replacements, None, english_runtime=True,
                               runtime_module=directory, module_additions=additions)
        runtime, _ = make_english_runtime(self.rom, replacements, layout)
        replacements.update(runtime)
        apply_translations(self.rom, replacements, None, english_runtime=True,
                           runtime_module=directory, module_additions=additions)
        with self.assertRaisesRegex(ValueError, "complete resident"):
            apply_translations(self.rom, replacements, None, english_runtime=True,
                               runtime_module=directory, module_additions={})
