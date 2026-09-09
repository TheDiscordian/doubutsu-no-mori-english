"""Bounded map name storage, relocation, and full cartridge regression checks."""
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
import map_names as m
from aflib import by_vrom, sha256, apply_ups, CODE_VROM
from npc_mail_show import relocate_verified_data

OUT = ROOT/'build/map-names-overlay'
BUILD = ROOT/'build/map-names-pilot'
PREVIOUS = ROOT/'build/actor-names-pilot'


class MapCoreTests(unittest.TestCase):
    def test_packed_records_player_names_failure_reset_and_draw_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='af-map-host-') as tmp:
            target = str(Path(tmp)/'check')
            subprocess.run(['gcc', '-std=c99', '-Wall', '-Wextra', '-Werror', '-O1', '-g',
                            '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                            str(ROOT/'overlays/map/names.c'), str(ROOT/'tests/map_names_check.c'),
                            '-o', target], check=True, capture_output=True, timeout=30)
            subprocess.run([target], check=True, capture_output=True, timeout=10)


@unittest.skipUnless((OUT/'overlay.json').is_file(), 'Compiled map overlay required')
class MapArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.module = json.loads((ROOT/'build/notice-seasonal-runtime/module.json').read_text())
        cls.report = json.loads((OUT/'overlay.json').read_text())
        cls.data, cls.reloc = (OUT/'overlay.bin').read_bytes(), (OUT/'relocation.bin').read_bytes()
        cls.original, cls.old_reloc, _, _ = m.native_sources(cls.native)

    def test_only_four_calls_change_and_original_packed_fields_remain(self):
        m.validate(self.native, self.data, self.reloc, self.report, self.module)
        changes = {m.RAM+i for i in range(0, m.PREFIX, 4) if self.data[i:i+4] != self.original[i:i+4]}
        self.assertEqual(changes, set(m.HOOKS))
        self.assertEqual(self.data[m.PREFIX:m.START], bytes(m.BSS))
        self.assertEqual(self.data[26352:], bytes(len(self.data)-26352))
        # Native record stride, sex/house fields, draw lengths, and every
        # instruction after each changed call (including delay slots) survive.
        for at in (0x8088E040, 0x8088E104, 0x8088E170, 0x8088F298, 0x8088F29C,
                   0x8088F2D8, 0x8088F2F4, 0x8088F330, 0x8088FC9C):
            off = at-m.RAM
            self.assertEqual(self.data[off:off+4], self.original[off:off+4])
        self.assertEqual(m.allocation()['map_growth'], 768)
        self.assertLess(m.allocation()['conservative_required'], m.allocation()['combined_pool'])

    def test_relocation_retains_native_bss_and_fixed_imports(self):
        spec = m.validate(self.native, self.data, self.reloc, self.report, self.module)
        old_spec = m.Image(m.RAM, m.START, m.SECTIONS)
        for base in (0x801A0000, 0x802F8010):
            old = relocate_verified_data(old_spec, self.original, self.old_reloc, base)
            new = relocate_verified_data(spec, self.data, self.reloc, base)
            for at in range(0, m.START, 4):
                if m.RAM+at not in m.HOOKS: self.assertEqual(new[at:at+4], old[at:at+4])
            for at, (name, _) in m.HOOKS.items():
                self.assertEqual(struct.unpack_from('>I', new, at-m.RAM)[0],
                                 0x0C000000 | ((base+m.APPROVED['symbols'][name]) >> 2) & 0x3FFFFFF)
            for at, kind, target, _ in self.report['elf_relocations']:
                if kind == 4:
                    expected = base+target-m.RAM if m.RAM <= target < m.RAM+len(self.data) else target
                    self.assertEqual(struct.unpack_from('>I', new, at)[0] & 0x3FFFFFF, (expected >> 2) & 0x3FFFFFF)

    def test_rehashed_damage_still_rejected(self):
        for at in (0, 0x8088E030-m.RAM, m.PREFIX, m.START, 26352):
            data = bytearray(self.data); data[at] ^= 1
            report = {**self.report, 'overlay_sha256': sha256(data)}
            with self.assertRaises(ValueError): m.validate(self.native, bytes(data), self.reloc, report, self.module)
        report = copy.deepcopy(self.report); report['elf_relocations'][0][0] += 4
        with self.assertRaises(ValueError): m.validate(self.native, self.data, self.reloc, report, self.module)


@unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete map cartridge required')
class MapCartridgeTests(unittest.TestCase):
    def test_map_application_is_verified_in_combined_accounting(self):
        from translation_progress import measure, pending_name_consumers
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        ledgers = []
        for path in (PREVIOUS, BUILD):
            report = json.loads((path/'build.json').read_text())
            ledgers.append(measure(native, (path/'animal-forest-halfwidth.z64').read_bytes(), report))
        self.assertEqual(ledgers[0].summary(), ledgers[1].summary())
        self.assertIn('map names are connected', pending_name_consumers(report)['display_names'])
        broken = copy.deepcopy(report); broken['map_names']['complete_name_slots'] = 14
        with self.assertRaises(ValueError):
            measure(native, (BUILD/'animal-forest-halfwidth.z64').read_bytes(), broken)

    def test_whole_patch_and_retained_translation_resources(self):
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        previous = (PREVIOUS/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text())
        m.verify_shared_parts(built, native, report['runtime_module'], report['map_names'])
        from notice_overlay import verify_installation
        verify_installation(built, native, report['runtime_module'], report['noticeboard'])
        self.assertEqual(apply_ups(native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), built)
        files, old = by_vrom(built), by_vrom(previous)
        self.assertEqual(set(old)-set(files), {m.VROM, m.RELOC})
        self.assertEqual(set(files)-set(old), {m.NEW_VROM, m.NEW_RELOC})
        for v in files.keys() & old.keys():
            if v not in (0x19D40, m.OWNER): self.assertEqual(files[v].extract(built), old[v].extract(previous), hex(v))
        self.assertEqual(files[CODE_VROM].extract(built), old[CODE_VROM].extract(previous))


if __name__ == '__main__': unittest.main()
