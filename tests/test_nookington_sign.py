"""Sign-only changes preserve the shared building stream and every earlier fix."""
import copy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, sha256, apply_ups, u32
from hboard_overlay import Image
from npc_mail_show import relocate_verified_data
from nookington_sign import (OBJECT, NEW_OBJECT, STRUCTURE, STRUCTURE_RAM, DEPART, TABLE,
    SEASONS, POINTERS, ACTOR_POINTERS, OLD_SIZE, NEW_SIZE, SLOT_SIZE, commands,
    source_sign, patch_assets, expected_commands, build)
from title_assets import DATA_BASE, untile, pack4


@unittest.skipUnless((ROOT/'build/keyboard-grid-01/build.json').is_file(), 'Local supplied sources required')
class NookingtonSignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT/'build/keyboard-grid-01/animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((ROOT/'build/keyboard-grid-01/build.json').read_text())
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.files = by_vrom(cls.base)
        with tempfile.TemporaryDirectory(prefix='af-nookington-gbi-') as directory:
            cls.compiled = commands(Path(directory))
        cls.changed, cls.expanded, cls.profile = patch_assets(cls.native, cls.base, cls.rel, cls.symbols, cls.compiled)

    def test_exact_donor_sign_pixels_and_only_sign_uv_and_draw_changes(self):
        prior = self.files[OBJECT].extract(self.base)
        self.assertEqual(self.expanded[:len(prior)], prior)
        pixels = untile(self.rel[DATA_BASE+0x58D7C0:DATA_BASE+0x58DFC0], 128, 32, 4)
        sign = pack4(bytes(pixels[y*128+x] for y in range(32) for x in range(32, 128)))
        self.assertEqual(source_sign(self.native, self.rel, self.symbols)[0], sign)
        self.assertEqual(self.profile['building_ranges_checked'], 92)
        for name, old, new, _, _ in SEASONS:
            original = prior[old:old+OLD_SIZE]
            changed = self.expanded[new:new+NEW_SIZE]
            self.assertEqual(changed[OLD_SIZE:OLD_SIZE+1536], sign)
            self.assertEqual(changed[OLD_SIZE+1536:], expected_commands(0x06000000+new))
            restored = bytearray(changed[:OLD_SIZE])
            for at, target in POINTERS:
                self.assertEqual(u32(restored, at), 0x06000000+new+target)
                restored[at:at+4] = original[at:at+4]
            self.assertEqual(struct.unpack_from('>2I', restored, 0xAC8), (0xDE000000, 0x06000000+new+0x2BD0))
            restored[0xAC8:0xAD0] = original[0xAC8:0xAD0]
            for i in range(4):
                at = 0xB0+i*16+8
                self.assertEqual(struct.unpack_from('>h', restored, at)[0], 31 if i < 2 else 2528)
                restored[at:at+2] = original[at:at+2]
            self.assertEqual(restored, original)
            # Original atlas and tile-1 state are restored after the two sign triangles.
            dl = self.compiled[name]
            self.assertEqual(dl[96:152], changed[0xA50:0xA88])
            self.assertEqual(dl[152:168], changed[0xA90:0xAA0])
            self.assertEqual(dl[80:88], original[0xAC8:0xAD0])

    def test_native_slot_addresses_sizes_and_cpu_rsp_segment_resolution(self):
        for index, (_, _, new, start_at, end_at) in enumerate(SEASONS):
            table = self.changed[TABLE]
            offset = u32(table, start_at)-0x06000000+8
            size = (u32(table, end_at)-u32(table, start_at)-8+15)&~15
            self.assertEqual((offset, size), (new, NEW_SIZE))
            self.assertEqual(SLOT_SIZE-size, 384)
            for first_slot in (0x801B0000, 0x80300000):
                for slot_index in range(8):
                    slot = first_slot+slot_index*SLOT_SIZE
                    segment = slot-offset
                    self.assertGreaterEqual(segment, 0x80000000)
                    self.assertLess(slot+size, 0x80400000)
                    for target in [v for _, v in POINTERS]+[0x25D0, 0x2BD0]:
                        pointer = 0x06000000+new+target
                        cpu = ((segment+0x80000000+(pointer&0xFFFFFF))&0xFFFFFFFF)|0x80000000
                        rsp = ((segment&0xFFFFFF)+(pointer&0xFFFFFF))&0xFFFFFF
                        self.assertEqual(cpu, slot+target)
                        self.assertEqual(rsp, slot-0x80000000+target)
                    for at, target in ACTOR_POINTERS:
                        self.assertEqual(u32(self.changed[DEPART], at+index*4), 0x06000000+new+target)

    def test_unchanged_native_actor_relocations_preserve_new_constants(self):
        for vrom, reloc_vrom, ram in ((STRUCTURE, 0x8CD350, STRUCTURE_RAM), (DEPART, 0x8D1DD0, 0x80A02050)):
            original, changed = self.files[vrom].extract(self.base), self.changed[vrom]
            reloc = self.files[reloc_vrom].extract(self.base)
            sections = struct.unpack_from('>5I', reloc)
            spec = Image(ram, len(changed)+sections[3], sections)
            # Native compiler array-base/loop-sentinel constants. Neither is a
            # new pointer or a dereference without its existing index arithmetic.
            constants = (0x809BD87C, 0x80A03528) if vrom == STRUCTURE else ()
            modified = {i for i in range(0, len(original), 4) if original[i:i+4] != changed[i:i+4]}
            self.assertEqual(len(modified), 2 if vrom == STRUCTURE else 6)
            for base in (0x801B0000, 0x802F8010):
                before = relocate_verified_data(spec, original, reloc, base, address_constants=constants)
                after = relocate_verified_data(spec, changed, reloc, base, address_constants=constants)
                for at in range(0, len(after), 4):
                    self.assertEqual(after[at:at+4], changed[at:at+4] if at in modified else before[at:at+4])

    def test_source_and_command_rejections(self):
        with self.assertRaisesRegex(ValueError, 'source'):
            source_sign(self.native, self.rel[:-1], self.symbols)
        with self.assertRaisesRegex(ValueError, 'source'):
            source_sign(self.native, self.rel, self.symbols+b'\n')
        bad = dict(self.compiled, winter=bytes(176))
        with self.assertRaisesRegex(ValueError, 'Compiled sign'):
            patch_assets(self.native, self.base, self.rel, self.symbols, bad)
        with self.assertRaisesRegex(ValueError, 'baseline'):
            build(self.native, self.base[:-16], self.report, self.rel, self.symbols, self.compiled)

    def test_complete_cartridge_ups_and_all_previous_resources_retained(self):
        before = copy.deepcopy(self.report)
        image, ups, report = build(self.native, self.base, self.report, self.rel, self.symbols, self.compiled)
        self.assertEqual(self.report, before)
        self.assertEqual(sha256(image), '28c551708dbbc1d78333abc7ebf81d5001663859775ca9f85427ced8208b0020')
        self.assertEqual(len(image), 32*1024*1024)
        self.assertEqual(apply_ups(self.native, ups), image)
        files = by_vrom(image)
        self.assertEqual(set(files), set(self.files)|{NEW_OBJECT})
        self.assertEqual(files[NEW_OBJECT].extract(image), self.expanded)
        for vrom, entry in self.files.items():
            if vrom != 0x19D40:
                self.assertEqual(files[vrom].extract(image), self.changed.get(vrom, entry.extract(self.base)))
            self.assertEqual(files[vrom].index, entry.index)
            self.assertEqual(files[vrom].size, entry.size)
        for key, value in self.report.items():
            if key not in ('output_sha256', 'patch_sha256', 'replacement_files', 'added_files', 'release_status'):
                self.assertEqual(report[key], value, key)


if __name__ == '__main__':
    unittest.main()
