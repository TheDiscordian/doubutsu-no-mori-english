"""Resident date preparation preserves conversion, storage, and native controls."""

from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
from dialogue_dates import (SPEC, CALLS, LEAP_HIGH, LEAP_LOW, REMOVED_RELOCATIONS,
                            REQUIREMENT, changes, patch, relocated, install, verify_requirements)
from npc_mail_show import source
from runtime_layout import MODULE_RAM, MODULE_VROM
from runtime_module import module_command_info
from textbanks import banks
from textcodec import encode, tokenize
from textvalidate import validate_entry
from reference_candidates import select_drafts
from test_retail import ROM_PATH


class DialogueDateDraftSelectionTests(unittest.TestCase):
    def test_unconfigured_candidates_withhold_only_dependent_drafts(self):
        drafts = json.loads((ROOT/'translations/n64-festivals.json').read_text())
        selected, withheld = select_drafts(drafts)
        self.assertEqual({r['id'] for r in selected}, {'message:119C', 'message:27C0'})
        self.assertEqual({r['id'] for r in withheld}, {'message:11AC', 'message:180B'})
        self.assertTrue(all(r['reason'] == 'runtime_requirement_unavailable' for r in withheld))
        self.assertEqual(select_drafts(drafts, english_dialogue_dates=True), (drafts, []))

    def test_malformed_requirements_fail_even_when_feature_is_enabled(self):
        for requirements in (None, REQUIREMENT, ['unknown'], [REQUIREMENT, REQUIREMENT]):
            for enabled in (False, True):
                with self.assertRaisesRegex(ValueError, 'runtime requirements'):
                    select_drafts([{'id': 'message:0000', 'runtime_requirements': requirements}],
                                  english_dialogue_dates=enabled)


@unittest.skipUnless(ROM_PATH.is_file() and (ROOT/'build/runtime-module/module.json').is_file(),
                     'Retail ROM and compiled runtime remain local')
class DialogueDateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM_PATH.read_bytes()
        cls.data, cls.reloc = source(cls.rom, 'ordinary')
        cls.module = json.loads((ROOT/'build/runtime-module/module.json').read_text())
        cls.binary = (ROOT/'build/runtime-module/module.bin').read_bytes()

    def test_only_six_words_and_two_relocations_change(self):
        data, reloc = patch(self.data, self.reloc, self.module)
        self.assertEqual(len(data), len(self.data))
        self.assertEqual(len(reloc), len(self.reloc))
        allowed = set()
        for address, before, after in changes(self.module):
            at = address-SPEC.ram
            self.assertEqual(struct.unpack_from('>I', self.data, at)[0], before)
            self.assertEqual(struct.unpack_from('>I', data, at)[0], after)
            allowed.update(range(at, at+4))
        self.assertEqual(len(allowed), 24)
        self.assertTrue(all(a == b or i in allowed for i, (a, b) in enumerate(zip(data, self.data))))
        self.assertEqual(reloc[:16], self.reloc[:16])
        count = struct.unpack_from('>I', reloc, 16)[0]
        self.assertEqual(count, 550)
        original = struct.unpack_from('>552I', self.reloc, 20)
        self.assertEqual(struct.unpack_from('>550I', reloc, 20),
                         tuple(v for v in original if v not in REMOVED_RELOCATIONS))
        self.assertEqual(reloc[20+count*4:], bytes(len(reloc)-20-count*4))

    def test_original_source_and_relocation_hashes_are_mandatory(self):
        for which in range(2):
            for offset in (0, 20, 500):
                blobs = [bytearray(self.data), bytearray(self.reloc)]
                blobs[which][offset] ^= 1
                with self.assertRaisesRegex(ValueError, 'Unexpected NPC'):
                    patch(bytes(blobs[0]), bytes(blobs[1]), self.module)

    def test_fixed_targets_survive_two_relocation_bases(self):
        for base in (0x801A0000, 0x802F8010):
            data = relocated(self.data, self.reloc, self.module, base)
            self.assertEqual(len(data), SPEC.resident_bytes)
            self.assertEqual(data[SPEC.file_bytes:], bytes(SPEC.sections[3]))
            for at, _, symbol in CALLS:
                word = struct.unpack_from('>I', data, at-SPEC.ram)[0]
                self.assertEqual(0x80000000 | ((word & 0x3FFFFFF) << 2), int(self.module['symbols'][symbol], 16))
            hi = struct.unpack_from('>I', data, LEAP_HIGH-SPEC.ram)[0] & 0xFFFF
            lo = struct.unpack_from('>h', data, LEAP_LOW-SPEC.ram+2)[0]
            self.assertEqual((hi << 16)+lo, int(self.module['symbols']['af_leap_month'], 16))

    def test_install_requires_full_module_literal_and_no_overlap(self):
        for binary, module in ((self.binary[:-1], self.module), (self.binary, None),
                               (self.binary, {**self.module, 'source_sha256': '0'*64})):
            replacements = {}
            with self.assertRaises(ValueError):
                install(self.rom, replacements, {MODULE_VROM: binary}, module)
            self.assertEqual(replacements, {})
        at = int(self.module['symbols']['af_leap_month'], 16)-MODULE_RAM
        binary = bytearray(self.binary)
        binary[at] ^= 1
        with self.assertRaisesRegex(ValueError, 'leap-month literal'):
            install(self.rom, {}, {MODULE_VROM: bytes(binary)}, {**self.module, 'module_sha256': sha256(binary)})
        with self.assertRaisesRegex(ValueError, 'overlaps'):
            install(self.rom, {SPEC.vrom: b'other'}, {MODULE_VROM: self.binary}, self.module)
        replacements = {}
        report = install(self.rom, replacements, {MODULE_VROM: self.binary}, self.module)
        self.assertEqual(set(replacements), {SPEC.vrom, SPEC.relocation})
        self.assertEqual(report['relocations'], 550)

    def test_symbols_must_stay_in_complete_resident_bounds(self):
        for symbol in ('af_format_year', 'af_format_month', 'af_format_day', 'af_leap_month'):
            for address in ('0', '80000000', '8019FFFF'):
                module = deepcopy(self.module)
                module['symbols'][symbol] = address
                with self.assertRaises(ValueError):
                    patch(self.data, self.reloc, module)

    def test_translation_requirements_check_both_installed_files(self):
        edits = [{'runtime_requirements': [REQUIREMENT]}]
        additions = {MODULE_VROM: self.binary}
        with self.assertRaisesRegex(ValueError, 'complete English dialogue-date patch'):
            verify_requirements(edits, self.rom, {}, additions, self.module)
        replacements = {}
        install(self.rom, replacements, additions, self.module)
        verify_requirements(edits, self.rom, replacements, additions, self.module)
        for key in replacements:
            damaged = {**replacements, key: replacements[key]+b'!'}
            with self.assertRaisesRegex(ValueError, 'complete English dialogue-date patch'):
                verify_requirements(edits, self.rom, damaged, additions, self.module)
        for requirements in (None, REQUIREMENT, ['unknown'], [REQUIREMENT, REQUIREMENT]):
            with self.assertRaisesRegex(ValueError, 'runtime requirements'):
                verify_requirements([{'runtime_requirements': requirements}], self.rom, {}, {}, None)

    def test_four_festival_drafts_preserve_all_native_commands(self):
        info = module_command_info(self.rom)
        sources = next(b for b in banks(self.rom) if b.name == 'message').entries()
        drafts = json.loads((ROOT/'translations/n64-festivals.json').read_text())
        self.assertEqual({r['id'] for r in drafts}, {'message:'+n for n in ('119C', '27C0', '11AC', '180B')})
        for draft in drafts:
            number = int(draft['id'].split(':')[1], 16)
            original, output = sources[number], encode(draft['translation'], info)
            commands = lambda value: [t.data for t in tokenize(value, info) if t.kind == 'cmd']
            self.assertEqual(sha256(original), draft['source_sha256'])
            self.assertEqual(commands(output), commands(original), draft['id'])
            validate_entry(original, output, info, 'message', 'exact', resident_runtime=True)
            self.assertEqual(draft['status'], 'draft')
            if number in (0x11AC, 0x180B):
                self.assertEqual(draft['runtime_requirements'], [REQUIREMENT])
                self.assertIn(bytes.fromhex('7F3C207F3D'), output)
            if number == 0x27C0:
                self.assertIn(bytes.fromhex('7F1600100018'), output)
                self.assertIn(bytes.fromhex('7F0F27E87F1027E97F19'), output)


if __name__ == '__main__':
    unittest.main()
