"""Compiled notice ownership, allocation arithmetic, installation, and counting."""

from copy import deepcopy
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, DMA_START, DMA_END, apply_ups, by_vrom, sha256
import notice_overlay as n
from runtime_module import resident_c_sources, runtime_source_hashes
from translation_progress import measure

OVERLAY = ROOT/'build/noticeboard-reader'
BUILD, PREVIOUS = ROOT/'build/noticeboard-pilot', ROOT/'build/native-items-pilot'


def allocation_registers(code):
    """Evaluate the actual constant-only retail allocation instructions.

    This is a restricted arithmetic/branch test, not native execution. Stop
    before the first global load; no native allocator or game state is mocked.
    """
    registers = [0]*32
    pc, pending = 0x800C49E4, None
    for _ in range(256):
        if pc == 0x800C4BB0: return registers
        word = struct.unpack_from('>I', code, pc-CODE_RAM)[0]
        op, rs, rt, rd = word >> 26, word >> 21 & 31, word >> 16 & 31, word >> 11 & 31
        immediate = (word & 65535)-(65536 if word & 32768 else 0)
        next_pc, pending = (pending if pending is not None else pc+4), None
        if op == 15: registers[rt] = (word & 65535) << 16
        elif op == 9: registers[rt] = (registers[rs]+immediate) & 0xFFFFFFFF
        elif op == 4:
            pending = pc+4+immediate*4 if registers[rs] == registers[rt] else pc+8
        elif op == 0:
            function = word & 63
            a, b = registers[rs], registers[rt]
            if function == 33: value = a+b
            elif function == 35: value = a-b
            elif function == 36: value = a & b
            elif function == 37: value = a | b
            elif function == 43: value = int(a < b)
            else: raise ValueError(f'Unexpected native arithmetic at {pc:08X}')
            registers[rd] = value & 0xFFFFFFFF
        else: raise ValueError(f'Unexpected native allocation instruction at {pc:08X}')
        registers[0] = 0
        pc = next_pc
    raise ValueError('Allocation arithmetic failed to terminate')


@unittest.skipUnless((OVERLAY/'overlay.json').is_file(), 'Local compiled notice image required')
class NoticeOverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.module = json.loads((ROOT/'build/shop-notice-runtime/module.json').read_text())
        cls.catalog = (ROOT/'build/mail-glyph-resources/glyph-catalog.bin').read_bytes()
        cls.data, cls.reloc, cls.init = ((OVERLAY/name).read_bytes() for name in ('overlay.bin', 'relocation.bin', 'init.bin'))
        cls.report = json.loads((OVERLAY/'overlay.json').read_text())

    def test_linked_image_and_independent_build_agree(self):
        spec = n.validate(self.native, self.data, self.reloc, self.init, self.report, self.module, self.catalog)
        self.assertEqual((spec.resident_bytes, spec.sections), (13840, (13840, 0, 0, 0, 134)))
        self.assertLess(spec.resident_bytes-n.RESIDENT, n.GROWTH)
        self.assertEqual(len(self.init), 236)
        self.assertEqual(self.init[188:], bytes(48))
        for name in ('overlay.bin', 'relocation.bin', 'init.bin', 'overlay.json'):
            self.assertEqual((OVERLAY/name).read_bytes(), (ROOT/'build/noticeboard-reader-repeat'/name).read_bytes())

    def test_corrupted_rehashed_code_relocations_init_and_entry_points_are_rejected(self):
        for fault in ('prefix', 'bss', 'suffix', 'reloc', 'init', 'constructor', 'import', 'source'):
            data, reloc, init = bytearray(self.data), bytearray(self.reloc), bytearray(self.init)
            report = deepcopy(self.report)
            if fault in ('prefix', 'bss', 'suffix'):
                data[{'prefix': 0, 'bss': n.PREFIX, 'suffix': n.RESIDENT}[fault]] ^= 1
                report.update(overlay_sha256=sha256(data), suffix_sha256=sha256(data[n.RESIDENT:]))
            elif fault == 'reloc':
                reloc[20] ^= 1
                report['relocation_sha256'] = sha256(reloc)
            elif fault == 'init':
                init[0] ^= 1
                report['init_sha256'] = sha256(init)
            elif fault == 'constructor': report['symbols']['af_notice_construct'] += 4
            elif fault == 'import': report['imports']['af_mail_restore'] += 4
            else: report['sources']['overlays/notice/reader.c'] = '0'*64
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                n.validate(self.native, bytes(data), bytes(reloc), bytes(init), report, self.module, self.catalog)

    def test_actual_native_allocation_arithmetic_matches_expanded_pool(self):
        code = by_vrom(self.native)[CODE_VROM].extract(self.native)
        old = allocation_registers(code)
        patched = bytearray(code)
        struct.pack_into('>I', patched, n.POOL_PATCH-CODE_RAM, 0x25CECB20)
        new = allocation_registers(patched)
        sizes = n.pool_sizes()
        self.assertEqual((old[16], new[16]), (sizes['native'], sizes['expanded']))
        self.assertEqual((old[3], old[9]), (sizes['player'], sizes['alternative']))
        self.assertEqual(new[16]-old[16], 16384)

    def test_all_native_palette_and_conversion_outputs_exclude_record_tags(self):
        proof = n.audit_editor(self.native)
        self.assertEqual(proof['reachable_bytes'], 253)
        self.assertEqual(proof['reserved_prefixes_excluded'], [127, 128])
        from keyboard import english_editor
        data = english_editor(by_vrom(self.native)[0x78CB80].extract(self.native))
        self.assertEqual(n.audit_editor(self.native, data), proof)
        data = bytearray(data)
        data[0x35D0] = 127
        with self.assertRaises(ValueError): n.audit_editor(self.native, bytes(data))

    def test_on_demand_helpers_are_hashed_but_not_resident_compilation_units(self):
        source = ROOT/'runtime'
        compiled = {path.relative_to(source).as_posix() for path in resident_c_sources(source)}
        all_c = {path.relative_to(source).as_posix() for path in source.rglob('*.c')}
        excluded = {'notice/initial.c', 'notice/page.c', 'notice/record.c', 'notice/treasure.c'}
        self.assertEqual(all_c-compiled, excluded)
        self.assertTrue(excluded <= runtime_source_hashes(source).keys())

    def test_missing_build_dependencies_fail_before_reading_any_rom(self):
        result = subprocess.run([sys.executable, 'tools/build.py', '--rom', 'not-read.z64',
                                 '--english-noticeboard', 'not-read'], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('--english-noticeboard requires', result.stderr)


@unittest.skipUnless((BUILD/'build.json').is_file(), 'Completed local notice ROM required')
class NoticeInstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        cls.previous = (PREVIOUS/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((BUILD/'build.json').read_text())
        cls.prior = json.loads((PREVIOUS/'build.json').read_text())
        cls.module = cls.report['runtime_module']
        cls.files, cls.old = by_vrom(cls.built), by_vrom(cls.previous)

    def fixture(self):
        moves = {int(k, 16): int(v, 16) for k, v in self.prior['vrom_relocations'].items()}
        changes = {int(v, 16): self.old[moves.get(int(v, 16), int(v, 16))].extract(self.previous)
                   for v in self.prior['replacement_files']}
        additions = {int(v, 16): self.old[int(v, 16)].extract(self.previous) for v in self.prior['added_files']}
        return changes, additions, moves, deepcopy(self.module)

    def test_installer_is_atomic_and_retains_resources(self):
        fixture = self.fixture()
        before = deepcopy(fixture)
        result = n.install(self.native, *fixture, OVERLAY)
        self.assertEqual(result, self.report['noticeboard'])
        self.assertEqual(fixture[1], before[1])
        self.assertEqual(fixture[3], before[3])
        self.assertEqual(fixture[2], {**before[2], n.VROM: n.NEW_VROM, n.RELOCATION: n.NEW_RELOCATION})
        for address, output in ((n.VROM, n.NEW_VROM), (n.RELOCATION, n.NEW_RELOCATION),
                                (n.OWNER_VROM, n.OWNER_VROM), (CODE_VROM, CODE_VROM)):
            self.assertEqual(fixture[0][address], self.files[output].extract(self.built))
        with self.assertRaises(ValueError): n.install(self.native, *fixture, OVERLAY)

    def test_failed_installation_does_not_publish_any_map_changes(self):
        for fault in ('overlap', 'initial', 'pool', 'module', 'catalog'):
            fixture = self.fixture()
            if fault == 'overlap': fixture[2][n.VROM] = n.NEW_VROM
            elif fault in ('initial', 'pool'):
                data = bytearray(fixture[0][CODE_VROM])
                data[({'initial': n.INIT_START, 'pool': n.POOL_PATCH}[fault])-CODE_RAM] ^= 1
                fixture[0][CODE_VROM] = bytes(data)
            else: fixture[1].pop({'module': 0x02800000, 'catalog': 0x030A0000}[fault])
            before = deepcopy(fixture)
            with self.subTest(fault=fault), self.assertRaises((ValueError, KeyError)):
                n.install(self.native, *fixture, OVERLAY)
            self.assertEqual(fixture, before)

    def test_complete_rom_ups_and_unrelated_files_are_retained(self):
        n.verify_installation(self.built, self.native, self.module, self.report['noticeboard'])
        self.assertEqual(sha256(self.built), self.report['output_sha256'])
        self.assertEqual(apply_ups(self.native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), self.built)
        self.assertEqual(self.old.keys()-self.files.keys(), {n.VROM, n.RELOCATION})
        self.assertEqual(self.files.keys()-self.old.keys(), {n.NEW_VROM, n.NEW_RELOCATION})
        changed = {v for v in self.old.keys() & self.files.keys()
                   if self.old[v].extract(self.previous) != self.files[v].extract(self.built)}
        self.assertEqual(changed, {CODE_VROM, n.OWNER_VROM, 0x19D40})
        # The bootstrap DMA-table file necessarily changes physical addresses
        # and the two relocated virtual ranges; bytes outside that table do not.
        old_table = self.old[0x19D40].extract(self.previous)
        new_table = self.files[0x19D40].extract(self.built)
        self.assertEqual(old_table[:DMA_START-0x19D40], new_table[:DMA_START-0x19D40])
        self.assertEqual(old_table[DMA_END-0x19D40:], new_table[DMA_END-0x19D40:])
        original = self.old[CODE_VROM].extract(self.previous)
        code = bytearray(original)
        init = (OVERLAY/'init.bin').read_bytes()
        for at, value in n.main_changes(init).items(): code[at-CODE_RAM:at-CODE_RAM+len(value)] = value
        self.assertEqual(code, self.files[CODE_VROM].extract(self.built))
        for name in ('module.bin', 'bootstrap.bin'):
            self.assertEqual((ROOT/'build/noticeboard-runtime'/name).read_bytes(),
                             (ROOT/'build/shop-notice-runtime'/name).read_bytes())

    def test_combined_counter_credits_only_four_installed_bodies(self):
        old = measure(self.native, self.previous, self.prior)
        new = measure(self.native, self.built, self.report)
        ids = {f'mail:{number:04X}' for number in n.INITIAL_IDS}
        credited = {key for key, row in new.rows.items() if any(r['route'] == 'noticeboard' for r in row['replacements'])}
        self.assertEqual(credited, ids)
        self.assertEqual(old.rows.keys(), new.rows.keys())
        for key in old.rows:
            if key not in ids: self.assertEqual(old.rows[key], new.rows[key])
        delta = sum(old.rows[key]['source_characters'] for key in ids if not old.rows[key]['replacements'])
        self.assertGreater(delta, 0)
        self.assertEqual(new.summary()['replaced_source_characters']-old.summary()['replaced_source_characters'], delta)
        self.assertEqual(old.summary()['total_source_characters'], new.summary()['total_source_characters'])


if __name__ == '__main__': unittest.main()
