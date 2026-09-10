"""Source-bound title installation retains v0 text, runtime, and native transitions."""
from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, sha256, apply_ups, CODE_RAM, CODE_VROM
from title_overlay import build, validate, ACTOR, RELOC, SIZE, NEW_ACTOR, NEW_RELOC
from build_title_overlay import compile_overlay, PREFIX, PROFILE
from title_press_start import POSITIONS, RAM
from title_memory import BASE, BOOT, CALL, HELPER, HELPER_END, LIMIT, install as install_memory
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
from toolchain import IMAGE, comparison_profile


PREVIEW = ROOT/'build/title-logo-expansion-preview-03'


@unittest.skipUnless((PREVIEW/'preview.json').is_file(), 'Compiled English title preview required')
class TitleOverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.base = (ROOT/'build/classic-letters-pilot/animal-forest-halfwidth.z64').read_bytes()
        cls.base_report = json.loads((ROOT/'build/classic-letters-pilot/build.json').read_text())
        cls.report = json.loads((PREVIEW/'preview.json').read_text())
        cls.profile = cls.report['actor']
        image = (PREVIEW/'animal-forest-title-preview.z64').read_bytes()
        files = by_vrom(image)
        cls.overlay, cls.reloc = [files[v].extract(image) for v in (NEW_ACTOR, NEW_RELOC)]

    def test_independent_compilation_and_relocation_match(self):
        with tempfile.TemporaryDirectory(prefix='af-title-overlay-') as directory:
            out = Path(directory)
            report = compile_overlay(self.native, self.rel, self.symbols, out)
            # Both registered immutable images contain the verified same
            # compiler. Retain actual provenance and compare historical metadata
            # through the existing narrow identity mapping; binary checks remain.
            self.assertEqual(report['toolchain'], IMAGE)
            self.assertEqual(comparison_profile(report), comparison_profile(self.profile))
            self.assertEqual((out/'overlay.bin').read_bytes(), self.overlay)
            self.assertEqual((out/'relocation.bin').read_bytes(), self.reloc)

    def test_only_expected_prefix_sites_change_and_native_transitions_remain(self):
        original = by_vrom(self.native)[ACTOR].extract(self.native)
        restored = bytearray(self.overlay[:PREFIX])
        changes = self.profile['patches']
        expected = {PROFILE+12, PROFILE+16, 0x80AA1ED8-RAM, 0x80AA1AD4-RAM,
                    *(at-RAM for at in range(0x80AA1A24, 0x80AA1A75, 16)),
                    *(POSITIONS+i*4 for i in range(6))}
        self.assertEqual({p['offset'] for p in changes}, expected)
        for row in changes:
            self.assertEqual(struct.unpack_from('>I', restored, row['offset'])[0], row['after'])
            struct.pack_into('>I', restored, row['offset'], row['before'])
        self.assertEqual(restored, original)
        self.assertEqual(struct.unpack_from('>I', self.overlay, PROFILE+12)[0], 1968)
        # Original destructor, update, and draw callbacks retain their linked addresses.
        self.assertEqual(self.overlay[PROFILE+20:PROFILE+32], original[PROFILE+20:PROFILE+32])

    def test_corrupt_artifacts_and_source_profile_reject(self):
        validate(self.overlay, self.reloc, self.profile)
        for at in (0, PREFIX, self.profile['asset_offset'], SIZE-1):
            bad = bytearray(self.overlay); bad[at] ^= 1
            with self.assertRaises(ValueError): validate(bad, self.reloc, self.profile)
        with self.assertRaises(ValueError): validate(self.overlay, self.reloc[:-1], self.profile)
        for key, value in (('state_bytes', 1148), ('actor_instance_bytes', 808), ('sources', {})):
            with self.assertRaises(ValueError): validate(self.overlay, self.reloc, {**self.profile, key: value})

    def test_complete_rom_patch_and_all_preceding_resources(self):
        image, patch, report = build(self.native, self.base, self.base_report, self.rel, self.symbols,
                                     self.overlay, self.reloc, self.profile)
        self.assertEqual(report, self.report)
        self.assertEqual(apply_ups(self.native, patch), image)
        self.assertEqual(sha256(image), self.report['output_sha256'])
        files = by_vrom(image)
        self.assertEqual(files[NEW_RELOC].index, files[NEW_ACTOR].index+1)
        self.assertFalse(report['resident_runtime_changed'])
        self.assertFalse(report['save_layout_changed'])
        boot = files[BOOT].extract(image)
        physical = by_vrom(self.native)[BOOT].pstart
        self.assertEqual(image[physical:physical+len(boot)], boot)
        self.assertEqual(boot[0xA8:0xAC], bytes(4))
        self.assertEqual(report['memory']['ordinary_heap_end'], 0x80400000)
        self.assertEqual(report['memory']['required_ram_bytes'], 0x800000)
        stale = deepcopy(self.base_report); stale['replacement_files'].remove('00D07000')
        with self.assertRaisesRegex(ValueError, 'previous resource'):
            build(self.native, self.base, stale, self.rel, self.symbols, self.overlay, self.reloc, self.profile)

    def test_expansion_reservation_relocates_only_with_explicit_memory_contract(self):
        spec = Image(RAM, SIZE, struct.unpack_from('>5I', self.reloc))
        with self.assertRaises(ValueError):
            relocate_verified_data(spec, self.overlay, self.reloc, BASE)
        result = relocate_verified_data(spec, self.overlay, self.reloc, BASE, memory_end=0x80800000)
        self.assertEqual(len(result), SIZE)
        self.assertEqual(struct.unpack_from('>I', result, PROFILE+24)[0], BASE+0x80AA1E58-RAM)
        at = self.profile['asset_offset']
        self.assertEqual(result[at:], self.overlay[at:])
        for limit in (True, 0x80450000, 0x80800001):
            with self.assertRaises(ValueError):
                relocate_verified_data(spec, self.overlay, self.reloc, BASE, memory_end=limit)

    def test_allocation_ownership_and_bootstrap_conflicts_reject(self):
        code = by_vrom(self.base)[CODE_VROM].extract(self.base)
        for address in (CALL, HELPER, HELPER_END-1, 0x800578E0, 0x800577F8, 0x800D94F0):
            bad = bytearray(code); bad[address-CODE_RAM] ^= 1
            with self.assertRaises(ValueError):
                install_memory(self.native, self.base, bad, SIZE)
        for size in (0, SIZE+1, LIMIT-BASE):
            with self.assertRaises(ValueError):
                install_memory(self.native, self.base, bytearray(code), size)


if __name__ == '__main__':
    unittest.main()
