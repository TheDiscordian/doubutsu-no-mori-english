from copy import deepcopy
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom, replace_dma, sha256
import hboard_overlay as h
from hboard_editor import EDITOR, EDITOR_RELOC, HBOARD, HBOARD_RELOC, OWNER, OWNER_RELOC, METADATA
from keyboard import english_editor
import notice_overlay as n
from runtime_module import resident_c_sources, runtime_source_hashes
from test_notice_install import allocation_registers

ARTIFACTS = ROOT/'build/hboard-editor-overlay'
BUILD = ROOT/'build/hboard-editor-pilot'
PREVIOUS = ROOT/'build/gyroid-default-pilot'


@unittest.skipUnless(shutil.which('gcc'), 'Host GCC required')
class HboardBridgeTests(unittest.TestCase):
    def test_complete_native_bridge_contract_under_sanitizers(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = str(Path(directory)/'check')
            result = subprocess.run(['gcc', '-std=c99', '-Wall', '-Wextra', '-Werror', '-O1', '-g',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer', 'runtime/hboard_editor.c',
                'overlays/hboard/editor.c', 'tests/hboard_overlay_check.c', '-o', executable],
                cwd=ROOT, capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([executable], capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            self.assertEqual(result.stdout.strip(), 'Owner-editor bridge checks passed')


@unittest.skipUnless((ARTIFACTS/'overlay.json').is_file(), 'Compiled owner-editor required')
class HboardArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.data = (ARTIFACTS/'overlay.bin').read_bytes(); cls.reloc = (ARTIFACTS/'relocation.bin').read_bytes()
        cls.report = json.loads((ARTIFACTS/'overlay.json').read_text())

    def test_independent_builds_relocation_and_exact_retained_native_prefix(self):
        spec = h.validate(self.native, self.data, self.reloc, self.report)
        self.assertEqual(spec.resident_bytes, 20416)
        old = english_editor(by_vrom(self.native)[EDITOR].extract(self.native))
        changed = [i+h.RAM for i in range(0, h.PREFIX, 4) if old[i:i+4] != self.data[i:i+4]]
        self.assertEqual(changed, sorted(h.HOOKS))
        self.assertEqual(struct.unpack_from('>I', self.data, 0x8088882C-h.RAM)[0], 0x808862EC)
        repro = ROOT/'build/hboard-editor-overlay-repro'
        for name in ('overlay.bin', 'relocation.bin', 'overlay.json', 'window.bin'):
            self.assertEqual((ARTIFACTS/name).read_bytes(), (repro/name).read_bytes(), name)
        self.assertEqual((ARTIFACTS/'window.bin').read_bytes(), h.window_bytes())
        # Metadata references another allocation; none may be relocated as
        # though it pointed inside the submenu owner's own image.
        reloc = by_vrom(self.native)[OWNER_RELOC].extract(self.native)
        sections = struct.unpack_from('>5I', reloc)
        at = METADATA[EDITOR][0]
        for entry in struct.unpack_from('>'+str(sections[4])+'I', reloc, 20):
            section, offset = entry >> 30, entry & 0xFFFFFF
            offset += (0, sections[0], sections[0]+sections[1])[section-1]
            self.assertFalse(at <= offset < at+32)

    def test_rehashed_code_data_state_and_relocation_changes_are_rejected(self):
        for at in (0, 0x76C, 0x80888828-h.RAM, 0x8088882C-h.RAM, h.PREFIX,
                   h.CODE_START, self.report['symbols']['af_hboard_editor_draw'],
                   self.report['symbols']['af_hboard_english_default'], len(self.data)-1):
            changed = bytearray(self.data); changed[at] ^= 1
            report = deepcopy(self.report); report['overlay_sha256'] = sha256(changed)
            report['suffix_sha256'] = sha256(changed[h.CODE_START:])
            with self.assertRaises(ValueError): h.validate(self.native, changed, self.reloc, report)
        changed = bytearray(self.reloc); changed[24] ^= 1
        report = deepcopy(self.report); report['relocation_sha256'] = sha256(changed)
        with self.assertRaises(ValueError): h.validate(self.native, self.data, changed, report)
        for key in ('symbols', 'sources', 'elf_relocations', 'approval'):
            report = deepcopy(self.report); report[key] = [] if key == 'elf_relocations' else {}
            with self.assertRaises(ValueError): h.validate(self.native, self.data, self.reloc, report)

    def test_separate_resident_inventory_and_unchanged_resident_machine_code(self):
        runtime = ROOT/'build/notice-seasonal-runtime'
        report = json.loads((runtime/'module.json').read_text())
        self.assertEqual(report['runtime_sources'], runtime_source_hashes(ROOT/'runtime'))
        self.assertIn('hboard_editor.c', report['runtime_sources'])
        self.assertNotIn(ROOT/'runtime/hboard_editor.c', resident_c_sources(ROOT/'runtime'))
        self.assertEqual(sha256((runtime/'module.bin').read_bytes()),
                         '493bc25a922bbd9d321759677134520bbb179413985f0e047df45e6e432664c6')
        self.assertEqual(sha256((runtime/'bootstrap.bin').read_bytes()),
                         '9c20b82708856897c19301bb23e35b84335482f9c10d4dd5ba5c3a3f7fb1d10f')


@unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete owner-editor cartridge required')
class HboardCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.before = (PREVIOUS/'animal-forest-halfwidth.z64').read_bytes()
        cls.previous = json.loads((PREVIOUS/'build.json').read_text())
        cls.built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((BUILD/'build.json').read_text())

    def test_complete_rom_patch_and_every_unrelated_resource_are_retained(self):
        h.verify_shared_parts(self.built, self.native)
        n.verify_installation(self.built, self.native, self.report['runtime_module'], self.report['noticeboard'])
        self.assertEqual(sha256(self.built), self.report['output_sha256'])
        self.assertEqual(apply_ups(self.native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), self.built)
        old, new = by_vrom(self.before), by_vrom(self.built)
        self.assertEqual(old.keys()-new.keys(), {EDITOR, EDITOR_RELOC})
        self.assertEqual(new.keys()-old.keys(), {h.NEW_VROM, h.NEW_RELOCATION})
        self.assertEqual({v for v in old.keys() & new.keys() if old[v].extract(self.before) != new[v].extract(self.built)},
                         {0x19D40, CODE_VROM, OWNER, HBOARD})
        before, after = old[CODE_VROM].extract(self.before), new[CODE_VROM].extract(self.built)
        at = n.POOL_PATCH-CODE_RAM
        self.assertEqual(after, before[:at]+bytes.fromhex('25CEFB20')+before[at+4:])
        before, after = old[OWNER].extract(self.before), new[OWNER].extract(self.built)
        at = METADATA[EDITOR][0]
        self.assertEqual(after, before[:at]+h.metadata()+before[at+32:])

    def test_actual_combined_submenu_arithmetic_reserves_both_extensions(self):
        code = by_vrom(self.built)[CODE_VROM].extract(self.built)
        self.assertEqual(allocation_registers(code)[16], 243072)
        self.assertEqual(self.report['hboard_editor']['combined_submenu_pool_bytes'], 243072)
        self.assertEqual(self.report['hboard_editor']['additional_editor_bytes'], 5600)
        align = lambda value: (value+63) & ~63
        self.assertEqual(align(h.APPROVED['bytes'])-align(h.ORIGINAL_RESIDENT), 5568)
        self.assertGreater(h.POOL_EXTRA, 5568)
        self.assertEqual(n.pool_sizes(True)['expanded']+h.POOL_EXTRA, 243072)

    def test_partial_installation_is_rejected_by_shared_notice_verification(self):
        files = by_vrom(self.built)
        original = by_vrom(self.native)
        for vrom, at in ((HBOARD, h.WINDOW_BRIDGE-h.HBOARD_RAM),
                          (OWNER, METADATA[EDITOR][0]), (CODE_VROM, n.POOL_PATCH-CODE_RAM),
                          (h.NEW_VROM, h.APPROVED['symbols']['af_hboard_editor_command'])):
            changed = bytearray(files[vrom].extract(self.built)); changed[at] ^= 1
            damaged = replace_dma(self.built, {vrom: bytes(changed)})
            with self.assertRaises(ValueError):
                n.verify_installation(damaged, self.native, self.report['runtime_module'], self.report['noticeboard'])
        damaged = replace_dma(self.built, {HBOARD: original[HBOARD].extract(self.native)})
        with self.assertRaises(ValueError): h.verify_shared_parts(damaged, self.native)

    def test_failed_installs_leave_all_caller_maps_unchanged(self):
        files = by_vrom(self.before)
        moves = {int(a, 16): int(b, 16) for a, b in self.previous['vrom_relocations'].items()}
        replacements = {int(v, 16): files[moves.get(int(v, 16), int(v, 16))].extract(self.before)
                        for v in self.previous['replacement_files']}
        additions = {int(v, 16): files[int(v, 16)].extract(self.before) for v in self.previous['added_files']}
        for failure in ('missing_default', 'overlap', 'wrong_pool'):
            repl, add, mov = deepcopy((replacements, additions, moves))
            default = self.previous['gyroid_default']
            if failure == 'missing_default': default = {}
            elif failure == 'overlap': add[h.NEW_VROM] = b'occupied'
            else:
                data = bytearray(repl[CODE_VROM]); data[n.POOL_PATCH-CODE_RAM] ^= 1; repl[CODE_VROM] = bytes(data)
            before = deepcopy((repl, add, mov))
            with self.assertRaises(ValueError):
                h.install(self.native, repl, add, mov, self.previous['runtime_module'], ARTIFACTS,
                          self.previous['noticeboard'], default)
            self.assertEqual((repl, add, mov), before)


if __name__ == '__main__': unittest.main()
