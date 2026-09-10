"""The drawing-only branch removes SP markers without changing input or the caret."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import apply_ups, by_vrom
from catalogue_names import Image
from name_space_markers import BRANCH, TARGET, OLD, NEW, DELAY, VROM, RELOC, RAM, build, patch_overlay
from npc_mail_show import relocate_verified_data


def after_branch(word, code):
    # Execute the actual BEQ/BNE operands, then its retained LUI delay slot.
    registers = [0]*32
    registers[24], registers[1] = code, 0x20
    op, rs, rt = word >> 26, word >> 21 & 31, word >> 16 & 31
    if op not in (4, 5):
        raise AssertionError('Unexpected branch opcode')
    equal = registers[rs] == registers[rt]
    taken = equal if op == 4 else not equal
    registers[1] = (DELAY & 0xFFFF) << 16
    offset = struct.unpack('>h', struct.pack('>H', word & 0xFFFF))[0]
    return BRANCH + 4 + offset*4 if taken else BRANCH + 8


@unittest.skipUnless((ROOT/'build/v1rc3/Animal Forest English V1RC3.z64').is_file(), 'V1RC3 required')
class NameSpaceMarkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT/'build/v1rc3/Animal Forest English V1RC3.z64').read_bytes()
        cls.image, cls.patch, cls.report = build(cls.native, cls.base)

    def test_bound_control_flow_for_leading_middle_trailing_and_repeated_spaces(self):
        old = by_vrom(self.base)[VROM].extract(self.base)
        new = by_vrom(self.image)[VROM].extract(self.image)
        native = by_vrom(self.native)[VROM].extract(self.native)
        self.assertEqual(old[0x444:0x584], native[0x444:0x584])
        before, delay = struct.unpack_from('>2I', old, BRANCH-RAM)
        after, new_delay = struct.unpack_from('>2I', new, BRANCH-RAM)
        self.assertEqual((before, after, delay, new_delay), (OLD, NEW, DELAY, DELAY))
        for text in (b' A', b'A B', b'Wi ', b'i  I', b'      ', b'NoSpace'):
            original = bytes(text)
            self.assertEqual(sum(after_branch(before, b) == BRANCH+8 for b in text), text.count(b' '))
            self.assertTrue(all(after_branch(after, b) == TARGET for b in text))
            self.assertEqual(text, original)
        self.assertTrue(all(after_branch(after, b) == TARGET for b in range(256)))

    def test_exact_single_instruction_and_every_other_resource_retained(self):
        old, new = by_vrom(self.base), by_vrom(self.image)
        self.assertEqual(set(old), set(new))
        for vrom, entry in old.items():
            self.assertEqual((entry.index, entry.size), (new[vrom].index, new[vrom].size))
            before, after = entry.extract(self.base), new[vrom].extract(self.image)
            if vrom == VROM:
                expected = bytearray(before)
                struct.pack_into('>I', expected, BRANCH-RAM, NEW)
                self.assertEqual(after, expected)
            elif vrom != 0x19D40:
                self.assertEqual(before, after, hex(vrom))
        for field in ('allocation_changed', 'input_code_changed', 'caret_code_changed', 'save_format_changed'):
            self.assertFalse(self.report[field])

    def test_native_relocations_keep_branch_and_continuation_in_the_same_window(self):
        files = by_vrom(self.base)
        old, relocation = files[VROM].extract(self.base), files[RELOC].extract(self.base)
        new = by_vrom(self.image)[VROM].extract(self.image)
        sections = struct.unpack_from('>5I', relocation)
        for address in (0x80200010, 0x80370010):
            image = Image(RAM, sum(sections[:4]), sections)
            before = relocate_verified_data(image, old, relocation, address)
            after = relocate_verified_data(image, new, relocation, address)
            expected = bytearray(before)
            struct.pack_into('>I', expected, BRANCH-RAM, NEW)
            self.assertEqual(after, expected)

    def test_complete_ups_and_changed_input_rejection(self):
        self.assertEqual(apply_ups(self.native, self.patch), self.image)
        self.assertEqual(len(self.image), 0x2000000)
        with self.assertRaises(ValueError):
            build(self.native, self.native)
        old = by_vrom(self.base)[VROM].extract(self.base)
        relocation = by_vrom(self.base)[RELOC].extract(self.base)
        for bad, rel in ((old[:-1], relocation), (old, relocation[:-1])):
            with self.assertRaises(ValueError):
                patch_overlay(bad, rel)


if __name__ == '__main__':
    unittest.main()
