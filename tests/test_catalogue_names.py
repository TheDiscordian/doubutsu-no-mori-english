"""Focused catalogue storage, native-patch, and complete-cartridge checks."""
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
import catalogue_names as c
from aflib import by_vrom, sha256, apply_ups, CODE_VROM
from npc_mail_show import relocate_verified_data

OUT = ROOT/'build/catalogue-names-overlay'
BUILD = ROOT/'build/catalogue-names-pilot'
PREVIOUS = ROOT/'build/inventory-english-pilot'


class CatalogueCoreTests(unittest.TestCase):
    def test_all_native_slots_reset_update_failure_and_draw_contract_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='af-catalogue-host-') as tmp:
            target = str(Path(tmp)/'check')
            subprocess.run(['gcc', '-std=c99', '-Wall', '-Wextra', '-Werror', '-O1', '-g',
                            '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                            str(ROOT/'overlays/catalog/names.c'), str(ROOT/'tests/catalogue_names_check.c'),
                            '-o', target], check=True, capture_output=True, timeout=30)
            subprocess.run([target], check=True, capture_output=True, timeout=10)


@unittest.skipUnless((OUT/'overlay.json').is_file(), 'Compiled catalogue overlay required')
class CatalogueArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.module = json.loads((ROOT/'build/notice-seasonal-runtime/module.json').read_text())
        cls.report = json.loads((OUT/'overlay.json').read_text())
        cls.data, cls.reloc = (OUT/'overlay.bin').read_bytes(), (OUT/'relocation.bin').read_bytes()
        cls.original, cls.old_reloc, _, _ = c.native_sources(cls.native)

    def test_exact_native_callers_and_owned_state(self):
        c.validate(self.native, self.data, self.reloc, self.report, self.module)
        changes = {c.RAM+i for i in range(0, c.PREFIX, 4) if self.data[i:i+4] != self.original[i:i+4]}
        self.assertEqual(changes, set(c.HOOKS))
        self.assertEqual(self.data[c.PREFIX:c.START], bytes(c.BSS))
        self.assertEqual(self.data[52320:52320+63*20], bytes(63*20))
        # Native page widths/strides and font geometry arguments stay unchanged.
        for at, word in ((0x808A6C34, 0x2631000A), (0x808A9630, 0x2610000A),
                         (0x808A8AC0, 0x24A5000A), (0x808A8A90, 0x2406000A),
                         (0x808A8A50, 0x3C013F60), (0x808A8AA8, 0x3C014190)):
            self.assertEqual(struct.unpack_from('>I', self.data, at-c.RAM)[0], word)
        self.assertEqual(self.report['code_end']-c.START, 532)
        self.assertEqual(c.allocation()['catalogue_growth'], 1856)
        self.assertLess(c.allocation()['alternative_required'], c.allocation()['combined_pool'])

    def test_relocation_preserves_original_bss_and_external_imports_at_three_bases(self):
        spec = c.validate(self.native, self.data, self.reloc, self.report, self.module)
        old_spec = c.Image(c.RAM, c.START, c.SECTIONS)
        for base in (0x801A0000, 0x802F8010, (0x80400000-len(self.data)) & ~15):
            old = relocate_verified_data(old_spec, self.original, self.old_reloc, base)
            new = relocate_verified_data(spec, self.data, self.reloc, base)
            for at in range(0, c.START, 4):
                if c.RAM+at not in c.HOOKS: self.assertEqual(new[at:at+4], old[at:at+4])
            for at, (name, _) in c.HOOKS.items():
                self.assertEqual(struct.unpack_from('>I', new, at-c.RAM)[0],
                                 0x0C000000 | ((base+c.APPROVED['symbols'][name]) >> 2) & 0x3FFFFFF)
            for at, kind, target, _ in self.report['elf_relocations']:
                if kind == 4:
                    expected = base+target-c.RAM if c.RAM <= target < c.RAM+len(self.data) else target
                    self.assertEqual(struct.unpack_from('>I', new, at)[0] & 0x3FFFFFF, (expected >> 2) & 0x3FFFFFF)
            self.assertEqual(new[52320:52320+63*20], bytes(63*20))

    def test_rehashed_changes_cannot_bypass_independent_pins(self):
        for at in (0, 0x808A6C20-c.RAM, c.PREFIX, c.START, 52320):
            data = bytearray(self.data); data[at] ^= 1
            report = {**self.report, 'overlay_sha256': sha256(data), 'suffix_sha256': sha256(data[c.START:])}
            with self.assertRaises(ValueError): c.validate(self.native, bytes(data), self.reloc, report, self.module)
        reloc = self.reloc[:-1]+bytes([self.reloc[-1]^1])
        with self.assertRaises(ValueError):
            c.validate(self.native, self.data, reloc, {**self.report, 'relocation_sha256': sha256(reloc)}, self.module)
        report = copy.deepcopy(self.report); report['elf_relocations'][0][0] += 4
        with self.assertRaises(ValueError): c.validate(self.native, self.data, self.reloc, report, self.module)


@unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete catalogue cartridge required')
class CatalogueCartridgeTests(unittest.TestCase):
    def test_complete_name_consumer_does_not_double_count_existing_text(self):
        from translation_progress import measure
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        rows = []
        for path in (PREVIOUS, BUILD):
            report = json.loads((path/'build.json').read_text())
            rows.append(measure(native, (path/'animal-forest-halfwidth.z64').read_bytes(), report).rows)
        self.assertEqual(rows[0], rows[1])

    def test_whole_patch_and_unchanged_prior_translation_resources(self):
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        previous = (PREVIOUS/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text())
        c.verify_shared_parts(built, native, report['runtime_module'], report['catalogue_names'])
        from notice_overlay import verify_installation
        verify_installation(built, native, report['runtime_module'], report['noticeboard'])
        self.assertEqual(apply_ups(native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), built)
        files, old = by_vrom(built), by_vrom(previous)
        for v in files.keys() & old.keys():
            if v not in (0x19D40, c.OWNER): self.assertEqual(files[v].extract(built), old[v].extract(previous), hex(v))
        self.assertEqual(files[CODE_VROM].extract(built), old[CODE_VROM].extract(previous))


if __name__ == '__main__': unittest.main()
