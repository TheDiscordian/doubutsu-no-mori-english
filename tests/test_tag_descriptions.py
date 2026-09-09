"""Focused full-description, native ABI/relocation, cartridge, and counter checks."""
import copy
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom, sha256
from npc_mail_show import relocate_verified_data
import inventory_english as inv
import inventory_menu_text as menu
import tag_descriptions as d

OUT = ROOT/'build/tag-descriptions-overlay'
BUILD = ROOT/'build/tag-descriptions-pilot'
PREVIOUS = ROOT/'build/inventory-menu-text-pilot'


class DescriptionCoreTests(unittest.TestCase):
    def test_complete_line_composition_full_names_guards_and_real_widths_under_sanitizers(self):
        from font import make_halfwidth, WIDTH_TABLE
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        with tempfile.TemporaryDirectory(prefix='af-description-host-') as tmp:
            binary, widths = Path(tmp)/'check', Path(tmp)/'widths.bin'
            widths.write_bytes(make_halfwidth(native)[0][CODE_VROM][WIDTH_TABLE:WIDTH_TABLE+256])
            subprocess.run(['gcc', '-std=c99', '-Wall', '-Wextra', '-Werror', '-O1', '-g',
                            '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                            str(ROOT/'overlays/tag/descriptions.c'), str(ROOT/'tests/tag_descriptions_check.c'),
                            '-o', str(binary)], check=True, capture_output=True, timeout=30)
            result = subprocess.run([str(binary), str(widths)], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)


@unittest.skipUnless((OUT/'overlay.json').is_file(), 'Compiled description overlay required')
class DescriptionArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.module = json.loads((ROOT/'build/notice-seasonal-runtime/module.json').read_text())
        cls.report = json.loads((OUT/'overlay.json').read_text())
        cls.data, cls.reloc = (OUT/'overlay.bin').read_bytes(), (OUT/'relocation.bin').read_bytes()
        cls.base = (ROOT/'build/inventory-menu-text-overlay/overlay.bin').read_bytes()

    def test_original_prefix_references_and_complete_quest_control_flow(self):
        spec = d.validate(self.native, self.data, self.reloc, self.report, self.module)
        symbols = d.APPROVED['symbols']
        self.assertEqual(d.restore_base(self.native, self.data, symbols), self.base)
        # Direct jumps and relocated data words have no other drawer reference.
        original, rel, _, _ = inv.native_sources(self.native)
        pairs = inv.original_relocations(rel)
        for at, kind in pairs:
            if d.DRAW_START <= at < d.DRAW_END: continue
            word = struct.unpack_from('>I', original, at)[0]
            target = 0x80000000 | (word & 0x3FFFFFF) << 2 if kind == 4 else word if kind == 2 else 0
            if inv.RAM+d.DRAW_START <= target < inv.RAM+d.DRAW_END:
                self.assertEqual((at+inv.RAM, target), (0x808784EC, 0x80877B0C))
        quest = d.quest_source(self.native)
        clone = self.data[symbols['af_tag_quest_names']:symbols['af_tag_quest_names']+d.QUEST_SIZE]
        for at in range(0, d.QUEST_SIZE, 4):
            if at not in d.QUEST_CALLS: self.assertEqual(clone[at:at+4], quest[at:at+4])
        hook = symbols['af_tag_description_hook']
        words = list(struct.unpack_from('>9I', self.data, hook))
        self.assertEqual(words[:2], [0x02002025, 0x8FA50044])
        self.assertEqual(words[3:7], [0x8FA6003C, 0x00403025, 0x02002025, 0x24050001])
        self.assertEqual(words[8], 0)
        # Original width save, original .75 scaling, and 16-pixel line interval.
        for a, b in ((0x80870164, 0x808701C8), (0x808784AC, 0x808784EC)):
            self.assertEqual(self.data[a-inv.RAM:b-inv.RAM], self.base[a-inv.RAM:b-inv.RAM])
        self.assertEqual(inv.allocation(spec.resident_bytes)['shared_growth_used'], 8064)
        self.assertEqual(self.report['lines_bytes'], 928)

    def test_all_relocations_and_unchanged_prefix_at_three_bases(self):
        spec = d.validate(self.native, self.data, self.reloc, self.report, self.module)
        base_rel = menu.relocation_data(self.native)
        base_spec = inv.Image(inv.RAM, menu.SIZE, struct.unpack_from('>5I', base_rel))
        symbols = d.APPROVED['symbols']
        hooks = d.prefix_words(symbols)
        for base in (0x801A0000, 0x802F8010, (0x80400000-len(self.data)) & ~15):
            data = relocate_verified_data(spec, self.data, self.reloc, base)
            prior = relocate_verified_data(base_spec, self.base, base_rel, base)
            for at in range(0, menu.SIZE, 4):
                if at not in hooks and not d.DRAW_START <= at < d.DRAW_END:
                    self.assertEqual(data[at:at+4], prior[at:at+4], hex(at))
            for at, _, target, _ in self.report['elf_relocations']:
                word = struct.unpack_from('>I', self.data, at)[0]
                if word >> 26 not in (2, 3): continue
                linked = 0x80000000 | (word & 0x3FFFFFF) << 2
                expected = linked+base-inv.RAM if inv.RAM <= target < inv.RAM+len(data) else linked
                self.assertEqual(struct.unpack_from('>I', data, at)[0] & 0x3FFFFFF, (expected >> 2) & 0x3FFFFFF)
            for at, (name, _) in d.QUEST_CALLS.items():
                word = struct.unpack_from('>I', data, symbols['af_tag_quest_names']+at)[0]
                self.assertEqual(word, 0x0C000000 | ((base+symbols[name]) >> 2) & 0x3FFFFFF)

    def test_rehashed_changes_and_partial_dependencies_are_rejected(self):
        for at in (0, d.DRAW_START, d.DRAW_END-1, 0x808700A0-inv.RAM, menu.SIZE, len(self.data)-1):
            data = bytearray(self.data); data[at] ^= 1
            report = copy.deepcopy(self.report); report['overlay_sha256'] = sha256(data)
            report['description_code_sha256'] = sha256(data[d.DRAW_START:d.DRAW_END]+data[menu.SIZE:])
            with self.assertRaises(ValueError): inv.validate(self.native, data, self.reloc, report, self.module)
        module = copy.deepcopy(self.module); module['symbols']['af_load_display_name'] = '80196048'
        with self.assertRaises(ValueError): inv.validate(self.native, self.data, self.reloc, self.report, module)
        report = copy.deepcopy(self.report); report['descriptions'] = False
        with self.assertRaises(ValueError): inv.validate(self.native, self.data, self.reloc, report, self.module)


@unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete description cartridge required')
class DescriptionCartridgeTests(unittest.TestCase):
    def test_rom_ups_allocation_and_all_other_resources_retained(self):
        import catalogue_names
        from notice_overlay import verify_installation
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        built, before = [(p/'animal-forest-halfwidth.z64').read_bytes() for p in (BUILD, PREVIOUS)]
        report = json.loads((BUILD/'build.json').read_text())
        inv.verify_shared_parts(built, native, report['runtime_module'], report['inventory_english'])
        catalogue_names.verify_shared_parts(built, native, report['runtime_module'], report['catalogue_names'])
        verify_installation(built, native, report['runtime_module'], report['noticeboard'])
        self.assertEqual(apply_ups(native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), built)
        files, old = by_vrom(built), by_vrom(before)
        self.assertEqual(files.keys(), old.keys())
        for v in files:
            if v not in (0x19D40, inv.OWNER, inv.NEW_VROM, inv.NEW_RELOC):
                self.assertEqual(files[v].extract(built), old[v].extract(before), hex(v))
        self.assertEqual(files[CODE_VROM].extract(built), old[CODE_VROM].extract(before))

    def test_eight_source_records_count_once_and_all_other_credit_remains(self):
        from translation_progress import measure
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        before, after = [measure(native, (p/'animal-forest-halfwidth.z64').read_bytes(),
                                json.loads((p/'build.json').read_text())) for p in (PREVIOUS, BUILD)]
        ids = {'ui_inventory_description:'+row[0] for row in d.SOURCES}
        self.assertEqual(len(ids), 8); self.assertEqual(before.rows.keys(), after.rows.keys())
        for key in before.rows.keys()-ids: self.assertEqual(before.rows[key], after.rows[key], key)
        for key in ids:
            self.assertFalse(before.rows[key]['replacements'])
            self.assertEqual([x['route'] for x in after.rows[key]['replacements']], ['inventory_descriptions'])
            self.assertEqual(before.rows[key]['source_sha256'], after.rows[key]['source_sha256'])


if __name__ == '__main__': unittest.main()
