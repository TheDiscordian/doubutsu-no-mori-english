"""Approved appended code retains strict preceding font and creator profiles."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from classic_letter_profiles import wrap, validate
from aflib import sha256

BUILD = ROOT/'build/classic-letters-candidate'
CHECK = ROOT/'build/classic-letters-candidate-check'


@unittest.skipUnless((BUILD/'font/profile.json').is_file(), 'Compiled classic adapter required')
class ClassicProfileTests(unittest.TestCase):
    def test_both_exact_profiles_retain_preceding_code_state_and_glyphs(self):
        for kind in ('font', 'creator'):
            path = BUILD/kind
            extension = json.loads((path/'profile.json').read_text())
            data, reloc = (path/'image.bin').read_bytes(), (path/'relocation.bin').read_bytes()
            report = wrap(extension)
            old, oldrel, previous = validate(kind, data, reloc, report)
            self.assertEqual(sha256(old), extension['previous_sha256'])
            self.assertEqual(sha256(oldrel), extension['previous_relocation_sha256'])
            self.assertLessEqual(len(data), 0x3000 if kind == 'font' else 0x10000)
            self.assertEqual(data[8:len(old)] if kind == 'font' else data[:len(old)],
                             old[8:] if kind == 'font' else old)
            if kind == 'font':
                for name in ('world_pixels', 'world_name', 'glyph_resource', 'active_glyph', 'af_font_resource'):
                    self.assertEqual(report['symbols'][name], previous['symbols'][name])

    def test_mutated_metadata_code_and_relocation_are_rejected(self):
        for kind in ('font', 'creator'):
            path = BUILD/kind
            report = wrap(json.loads((path/'profile.json').read_text()))
            data, reloc = (path/'image.bin').read_bytes(), (path/'relocation.bin').read_bytes()
            for at in (0, report['classic_letters']['prefix_bytes'], len(data)-1):
                broken = bytearray(data); broken[at] ^= 1
                with self.assertRaisesRegex(ValueError, 'approved classic'):
                    validate(kind, bytes(broken), reloc, report)
            broken = bytearray(reloc); broken[20] ^= 1
            with self.assertRaisesRegex(ValueError, 'approved classic'):
                validate(kind, data, bytes(broken), report)
            broken = deepcopy(report); broken['classic_letters']['entry_offset'] += 4
            with self.assertRaisesRegex(ValueError, 'approved classic'):
                validate(kind, data, reloc, broken)

    @unittest.skipUnless((CHECK/'font/profile.json').is_file(), 'Independent compilation required')
    def test_independent_compilations_match(self):
        for kind in ('font', 'creator'):
            for name in ('image.bin', 'relocation.bin', 'profile.json'):
                self.assertEqual((BUILD/kind/name).read_bytes(), (CHECK/kind/name).read_bytes())


if __name__ == '__main__':
    unittest.main()
