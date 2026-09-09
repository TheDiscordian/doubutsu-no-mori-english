"""Compiled seasonal publication, coupled cartridge installation, and text credit."""

from copy import deepcopy
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, DMA_START, DMA_END, apply_ups, by_vrom, replace_dma, sha256
import notice_overlay as n
import notice_seasonal_owner as owner
import notice_treasure_owner as treasure
from notice_seasonal import IDS
from translation_progress import measure
from test_notice_install import allocation_registers

DIRECTORY = ROOT/'build/noticeboard-seasonal'
BUILD, PREVIOUS = ROOT/'build/notice-seasonal-pilot', ROOT/'build/notice-treasure-pilot'


@unittest.skipUnless((DIRECTORY/'owner/owner.json').is_file(), 'Compiled seasonal owner required')
class SeasonalOwnerArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.code = by_vrom(cls.native)[CODE_VROM].extract(cls.native)
        cls.module = json.loads((ROOT/'build/notice-seasonal-runtime/module.json').read_text())
        cls.data = (DIRECTORY/'owner/owner.bin').read_bytes()
        cls.report = json.loads((DIRECTORY/'owner/owner.json').read_text())

    def test_every_stored_dma_reference_to_reclaimed_helpers_is_accounted_for(self):
        self.assertEqual(owner.scan_references(self.native), owner.REFERENCES)
        external = [r for r in owner.REFERENCES if not owner.START <= r[1]+CODE_RAM < owner.HELPERS_END]
        self.assertEqual([r[1]+CODE_RAM for r in external], [0x800A66C8, 0x800A671C])
        # Both external preparer calls disappear; all other references occur
        # inside reclaimed helper code. No literal or paired address remains.
        self.assertEqual({r[2] for r in owner.REFERENCES}, {'jump', 'branch'})

    def test_independent_assembly_binds_every_instruction_and_padding(self):
        self.assertEqual((len(self.data), sha256(self.data)),
                         (448, 'aed66e47ee62fa79e6d0cb0a0417a598fad8fc10f865d2d2398e3a426bc58b3a'))
        self.assertEqual(self.data, owner.expected(0x80197BB4))
        owner.validate(self.data, self.report, self.module)
        for name in ('owner.bin', 'owner.json'):
            self.assertEqual((DIRECTORY/'owner'/name).read_bytes(), (DIRECTORY/'owner-repeat'/name).read_bytes())
        for offset in (0, 92, 124, 132, 156, 168, 444):
            data = bytearray(self.data); data[offset] ^= 1
            report = deepcopy(self.report); report['sha256'] = sha256(data)
            with self.assertRaises(ValueError): owner.validate(data, report, self.module)

    def test_only_helpers_and_success_gates_change_in_native_scheduler(self):
        changed = owner.patch(self.code, self.data, self.report, self.module)
        intervals = [(owner.START, owner.END), (0x800A66C4, 0x800A66D0),
                     (0x800A671C, 0x800A6720), (0x800A6778, 0x800A677C), (0x800A6780, 0x800A6788)]
        start = 0
        for lo, hi in sorted(intervals):
            self.assertEqual(changed[start:lo-CODE_RAM], self.code[start:lo-CODE_RAM])
            start = hi-CODE_RAM
        self.assertEqual(changed[start:], self.code[start:])
        # Failed creation exits before the pending-loop increment, completion
        # flag, checked-date copy, and writer. The branch delay slot is inert.
        branch = struct.unpack_from('>I', changed, 0x800A6780-CODE_RAM)[0]
        self.assertEqual(branch, 0x10400018)
        self.assertEqual(0x800A6784+(branch & 65535)*4, 0x800A67E4)
        self.assertEqual(changed[0x800A6784-CODE_RAM:0x800A6788-CODE_RAM], bytes(4))
        with self.assertRaises(ValueError): owner.patch(changed, self.data, self.report, self.module)
        for lo, hi, _ in owner.GUARDS:
            code = bytearray(self.code); code[lo-CODE_RAM] ^= 1
            with self.assertRaises(ValueError): owner.patch(code, self.data, self.report, self.module)


@unittest.skipUnless((DIRECTORY/'reader/overlay.json').is_file(), 'Compiled seasonal reader required')
class SeasonalReaderArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.module = json.loads((ROOT/'build/notice-seasonal-runtime/module.json').read_text())
        cls.catalog = (ROOT/'build/mail-glyph-resources/glyph-catalog.bin').read_bytes()
        cls.data, cls.reloc, cls.init = ((DIRECTORY/'reader'/name).read_bytes()
                                       for name in ('overlay.bin', 'relocation.bin', 'init.bin'))
        cls.report = json.loads((DIRECTORY/'reader/overlay.json').read_text())

    def test_independent_reader_builds_and_actual_20480_byte_growth_reservation(self):
        spec = n.validate(self.native, self.data, self.reloc, self.init, self.report, self.module, self.catalog)
        self.assertEqual((len(self.data), len(self.reloc)), (24304, 720))
        self.assertEqual(spec.sections[:4], (24304, 0, 0, 0))
        self.assertGreater(len(self.data)-n.RESIDENT, n.GROWTH)
        self.assertLess(len(self.data)-n.RESIDENT, n.SEASONAL_GROWTH)
        self.assertEqual(n.pool_sizes(True)['expanded'], 234880)
        self.assertEqual(n.pool_sizes(True)['additional_bytes']-n.pool_sizes()['additional_bytes'], 4096)
        code = bytearray(by_vrom(self.native)[CODE_VROM].extract(self.native))
        struct.pack_into('>I', code, n.POOL_PATCH-CODE_RAM, 0x25CEDB20)
        self.assertEqual(allocation_registers(code)[16], 234880)
        for name in ('overlay.bin', 'relocation.bin', 'init.bin', 'overlay.json'):
            self.assertEqual((DIRECTORY/'reader'/name).read_bytes(), (DIRECTORY/'reader-repeat'/name).read_bytes())
        for directory in ('build/noticeboard-reader', 'build/noticeboard-treasure/reader'):
            old = ROOT/directory
            n.validate(self.native, (old/'overlay.bin').read_bytes(), (old/'relocation.bin').read_bytes(),
                       (old/'init.bin').read_bytes(), json.loads((old/'overlay.json').read_text()), self.module, self.catalog)

    def test_rehashed_changed_code_data_profile_and_approval_rejected(self):
        for name in ('af_notice_complete_restore', 'af_notice_seasonal_data', 'af_notice_seasonal_entries'):
            data = bytearray(self.data); data[self.report['symbols'][name]] ^= 1
            report = deepcopy(self.report)
            report.update(overlay_sha256=sha256(data), suffix_sha256=sha256(data[n.RESIDENT:]))
            with self.assertRaises(ValueError): n.validate(self.native, data, self.reloc, self.init, report, self.module, self.catalog)
        for fault in ('profile', 'treasure', 'approval', 'symbol'):
            report = deepcopy(self.report)
            if fault == 'profile': report['seasonal'] = False
            elif fault == 'treasure': report['treasure'] = False
            elif fault == 'approval': report['approval']['seasonal'][0]['source_sha256'] = '0'*64
            else: report['symbols']['af_notice_seasonal_restore'] += 4
            with self.assertRaises(ValueError): n.validate(self.native, self.data, self.reloc, self.init, report, self.module, self.catalog)

    def test_missing_dependencies_rejected_before_rom_read(self):
        result = subprocess.run([sys.executable, 'tools/build.py', '--rom', 'not-read.z64',
                                 '--english-notice-seasonal', 'not-read'], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('--english-notice-seasonal requires', result.stderr)


@unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete local seasonal ROM required')
class SeasonalInstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        cls.previous = (PREVIOUS/'animal-forest-halfwidth.z64').read_bytes()
        cls.report, cls.prior = (json.loads((directory/'build.json').read_text()) for directory in (BUILD, PREVIOUS))
        cls.module = cls.report['runtime_module']
        cls.files, cls.old = by_vrom(cls.built), by_vrom(cls.previous)

    def fixture(self):
        moves = {int(k, 16): int(v, 16) for k, v in self.report['vrom_relocations'].items()}
        changes = {int(v, 16): self.files[moves.get(int(v, 16), int(v, 16))].extract(self.built)
                   for v in self.report['replacement_files']}
        additions = {int(v, 16): self.files[int(v, 16)].extract(self.built) for v in self.report['added_files']}
        for v in (n.VROM, n.RELOCATION): changes.pop(v); moves.pop(v)
        changes.pop(n.OWNER_VROM)
        original = by_vrom(self.native)[CODE_VROM].extract(self.native)
        code = bytearray(changes[CODE_VROM])
        for at, value in n.main_changes((DIRECTORY/'reader/init.bin').read_bytes(), True).items():
            code[at-CODE_RAM:at-CODE_RAM+len(value)] = original[at-CODE_RAM:at-CODE_RAM+len(value)]
        for start, end, _ in (*treasure.RANGES, *owner.GUARDS):
            code[start-CODE_RAM:end-CODE_RAM] = original[start-CODE_RAM:end-CODE_RAM]
        changes[CODE_VROM] = bytes(code)
        return changes, additions, moves, deepcopy(self.module)

    def test_atomic_complete_installation_reproduces_actual_resources(self):
        fixture = self.fixture()
        before = deepcopy(fixture)
        report = n.install(self.native, *fixture, DIRECTORY/'reader',
                           treasure_owner_directory=ROOT/'build/noticeboard-treasure/owners',
                           seasonal_owner_directory=DIRECTORY/'owner')
        self.assertEqual(report, self.report['noticeboard'])
        self.assertEqual(fixture[1], before[1]); self.assertEqual(fixture[3], before[3])
        for at, output in ((n.VROM, n.NEW_VROM), (n.RELOCATION, n.NEW_RELOCATION),
                           (n.OWNER_VROM, n.OWNER_VROM), (CODE_VROM, CODE_VROM)):
            self.assertEqual(fixture[0][at], self.files[output].extract(self.built))

    def test_partial_or_changed_installation_leaves_inputs_unchanged(self):
        for fault in ('no_owner', 'old_reader', 'old_creator', 'scheduler', 'pool'):
            fixture = self.fixture()
            reader, bridge = DIRECTORY/'reader', DIRECTORY/'owner'
            if fault == 'no_owner': bridge = None
            elif fault == 'old_reader': reader = ROOT/'build/noticeboard-treasure/reader'
            elif fault == 'old_creator': fixture[3]['npc_mail_loader']['overlay'].pop('notice_seasonal')
            else:
                code = bytearray(fixture[0][CODE_VROM])
                code[(0x800A66C4 if fault == 'scheduler' else n.POOL_PATCH)-CODE_RAM] ^= 1
                fixture[0][CODE_VROM] = bytes(code)
            before = deepcopy(fixture)
            with self.subTest(fault=fault), self.assertRaises((ValueError, KeyError)):
                n.install(self.native, *fixture, reader, treasure_owner_directory=ROOT/'build/noticeboard-treasure/owners',
                          seasonal_owner_directory=bridge)
            self.assertEqual(fixture, before)

    def test_complete_rom_ups_and_all_earlier_translation_resources_retained(self):
        n.verify_installation(self.built, self.native, self.module, self.report['noticeboard'])
        self.assertEqual(sha256(self.built), self.report['output_sha256'])
        self.assertEqual(apply_ups(self.native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), self.built)
        self.assertEqual(self.files.keys(), self.old.keys())
        changed = {v for v in self.files if self.files[v].extract(self.built) != self.old[v].extract(self.previous)}
        self.assertEqual(changed, {CODE_VROM, 0x19D40, n.OWNER_VROM, n.NEW_VROM, n.NEW_RELOCATION, 0x02800000, 0x03200000})
        old_table, new_table = self.old[0x19D40].extract(self.previous), self.files[0x19D40].extract(self.built)
        self.assertEqual(old_table[:DMA_START-0x19D40], new_table[:DMA_START-0x19D40])
        self.assertEqual(old_table[DMA_END-0x19D40:], new_table[DMA_END-0x19D40:])
        expected = bytearray(owner.patch(self.old[CODE_VROM].extract(self.previous),
                                         (DIRECTORY/'owner/owner.bin').read_bytes(),
                                         self.report['noticeboard']['seasonal_owner']['bridge'], self.module))
        struct.pack_into('>I', expected, n.POOL_PATCH-CODE_RAM, 0x25CEDB20)
        self.assertEqual(expected, self.files[CODE_VROM].extract(self.built))
        old, new = (files[0x02800000].extract(rom) for files, rom in ((self.old, self.previous), (self.files, self.built)))
        self.assertEqual(old[:0x48]+old[0x68:], new[:0x48]+new[0x68:])

    def test_actual_scheduler_success_gates_required_not_only_manifest(self):
        source = by_vrom(self.native)[CODE_VROM].extract(self.native)
        for at in (0x800A66C4, 0x800A66C8, 0x800A66CC, 0x800A671C, 0x800A6778, 0x800A6780):
            code = bytearray(self.files[CODE_VROM].extract(self.built))
            code[at-CODE_RAM:at-CODE_RAM+4] = source[at-CODE_RAM:at-CODE_RAM+4]
            changed = replace_dma(self.built, {CODE_VROM: bytes(code)})
            with self.assertRaises(ValueError):
                n.verify_seasonal_installation(changed, self.native, self.module, self.report['noticeboard']['seasonal_owner'])

    def test_combined_credit_adds_exactly_41_installed_source_bodies(self):
        old, new = measure(self.native, self.previous, self.prior), measure(self.native, self.built, self.report)
        ids = {f'mail:{number:04X}' for number in IDS}
        self.assertEqual(old.rows.keys(), new.rows.keys())
        for key in old.rows:
            if key not in ids: self.assertEqual(old.rows[key], new.rows[key])
        credited = {key for key, row in new.rows.items() if any(r['route'] == 'noticeboard' for r in row['replacements'])}
        self.assertEqual(credited, ids | {f'mail:{number:04X}' for number in (*n.INITIAL_IDS, *range(0x1F0, 0x202))})
        delta = sum(old.rows[key]['source_characters'] for key in ids if not old.rows[key]['replacements'])
        self.assertGreater(delta, 0)
        self.assertEqual(new.summary()['replaced_source_characters']-old.summary()['replaced_source_characters'], delta)
        self.assertEqual(old.summary()['total_source_characters'], new.summary()['total_source_characters'])


if __name__ == '__main__': unittest.main()
