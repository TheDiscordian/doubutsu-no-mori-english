"""Treasure reader/owner installation, retained resources, and combined credit."""

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
import notice_treasure_owner as owner
from audit_notice_treasure import IDS
from translation_progress import measure

READER = ROOT/'build/noticeboard-treasure/reader'
OWNERS = ROOT/'build/noticeboard-treasure/owners'
BUILD = ROOT/'build/notice-treasure-pilot'
PREVIOUS = ROOT/'build/noticeboard-pilot'


@unittest.skipUnless((READER/'overlay.json').is_file(), 'Local compiled treasure reader required')
class TreasureReaderArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.module = json.loads((ROOT/'build/notice-treasure-runtime/module.json').read_text())
        cls.catalog = (ROOT/'build/mail-glyph-resources/glyph-catalog.bin').read_bytes()
        cls.data, cls.reloc, cls.init = ((READER/name).read_bytes() for name in ('overlay.bin', 'relocation.bin', 'init.bin'))
        cls.report = json.loads((READER/'overlay.json').read_text())

    def test_independent_reader_builds_fit_retained_reservation(self):
        spec = n.validate(self.native, self.data, self.reloc, self.init, self.report, self.module, self.catalog)
        self.assertEqual((len(self.data), len(self.reloc)), (15984, 640))
        self.assertEqual(spec.sections[:4], (15984, 0, 0, 0))
        self.assertLess(spec.resident_bytes-n.RESIDENT, n.GROWTH)
        for name in ('overlay.bin', 'relocation.bin', 'init.bin', 'overlay.json'):
            self.assertEqual((READER/name).read_bytes(), (ROOT/'build/noticeboard-treasure/reader-repeat'/name).read_bytes())
        self.assertEqual(self.init, (ROOT/'build/noticeboard-reader/init.bin').read_bytes())
        for directory in ('build/noticeboard-reader', 'build/noticeboard-reader-repeat'):
            old = ROOT/directory
            n.validate(self.native, (old/'overlay.bin').read_bytes(), (old/'relocation.bin').read_bytes(),
                       (old/'init.bin').read_bytes(), json.loads((old/'overlay.json').read_text()), self.module, self.catalog)

    def test_rehashed_corruption_wrong_profile_and_changed_approval_are_rejected(self):
        for fault in ('code', 'relocation', 'initial', 'profile', 'decoder', 'import', 'source', 'approval'):
            report = deepcopy(self.report)
            data, reloc, init = bytearray(self.data), bytearray(self.reloc), bytearray(self.init)
            if fault == 'code':
                data[report['symbols']['af_notice_complete_restore']] ^= 1
                report.update(overlay_sha256=sha256(data), suffix_sha256=sha256(data[n.RESIDENT:]))
            elif fault == 'relocation':
                reloc[20] ^= 1
                report['relocation_sha256'] = sha256(reloc)
            elif fault == 'initial':
                init[0] ^= 1
                report['init_sha256'] = sha256(init)
            elif fault == 'profile': report['treasure'] = False
            elif fault == 'decoder': report['symbols']['af_notice_treasure_restore'] += 4
            elif fault == 'import': report['imports']['af_mail_format'] += 4
            elif fault == 'source': report['sources']['overlays/notice/reader_treasure.c'] = '0'*64
            else: report['approval']['treasure']['parts'][0]['source_sha256'] = '0'*64
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                n.validate(self.native, data, reloc, init, report, self.module, self.catalog)

    def test_missing_treasure_dependencies_fail_before_reading_rom(self):
        result = subprocess.run([sys.executable, 'tools/build.py', '--rom', 'not-read.z64',
                                 '--english-notice-treasure', 'not-read'], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('--english-notice-treasure requires', result.stderr)


@unittest.skipUnless((BUILD/'build.json').is_file(), 'Completed local treasure ROM required')
class TreasureInstallTests(unittest.TestCase):
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
        moves = {int(k, 16): int(v, 16) for k, v in self.report['vrom_relocations'].items()}
        changes = {int(v, 16): self.files[moves.get(int(v, 16), int(v, 16))].extract(self.built)
                   for v in self.report['replacement_files']}
        additions = {int(v, 16): self.files[int(v, 16)].extract(self.built) for v in self.report['added_files']}
        for v in (n.VROM, n.RELOCATION):
            changes.pop(v)
            moves.pop(v)
        changes.pop(n.OWNER_VROM)
        original = by_vrom(self.native)[CODE_VROM].extract(self.native)
        code = bytearray(changes[CODE_VROM])
        for at, value in n.main_changes((READER/'init.bin').read_bytes()).items():
            code[at-CODE_RAM:at-CODE_RAM+len(value)] = original[at-CODE_RAM:at-CODE_RAM+len(value)]
        for start, end, _ in owner.RANGES:
            code[start-CODE_RAM:end-CODE_RAM] = original[start-CODE_RAM:end-CODE_RAM]
        changes[CODE_VROM] = bytes(code)
        return changes, additions, moves, deepcopy(self.module)

    def test_atomic_complete_installation_reproduces_actual_rom_resources(self):
        fixture = self.fixture()
        before = deepcopy(fixture)
        report = n.install(self.native, *fixture, READER, treasure_owner_directory=OWNERS)
        self.assertEqual(report, self.report['noticeboard'])
        self.assertEqual(fixture[1], before[1])
        self.assertEqual(fixture[3], before[3])
        for address, output in ((n.VROM, n.NEW_VROM), (n.RELOCATION, n.NEW_RELOCATION),
                                (n.OWNER_VROM, n.OWNER_VROM), (CODE_VROM, CODE_VROM)):
            self.assertEqual(fixture[0][address], self.files[output].extract(self.built))
        with self.assertRaises(ValueError): n.install(self.native, *fixture, READER, treasure_owner_directory=OWNERS)

    def test_incomplete_or_changed_installation_does_not_publish_changes(self):
        for fault in ('no_owner', 'old_reader', 'old_creator', 'config', 'names', 'scheduler', 'placement'):
            fixture = self.fixture()
            directory, bridges = READER, OWNERS
            if fault == 'no_owner': bridges = None
            elif fault == 'old_reader': directory = ROOT/'build/noticeboard-reader'
            elif fault == 'old_creator': fixture[3]['npc_mail_loader']['overlay'].pop('notice_owner')
            elif fault in ('config', 'names'):
                at = {'config': 0x02800000, 'names': 0x02A00000}[fault]
                data = bytearray(fixture[1][at]); data[56 if fault == 'config' else 48] ^= 1
                fixture[1][at] = bytes(data)
            else:
                data = bytearray(fixture[0][CODE_VROM])
                data[{'scheduler': 0x800A6170, 'placement': 0x8008EC44}[fault]-CODE_RAM] ^= 1
                fixture[0][CODE_VROM] = bytes(data)
            before = deepcopy(fixture)
            with self.subTest(fault=fault), self.assertRaises((ValueError, KeyError)):
                n.install(self.native, *fixture, directory, treasure_owner_directory=bridges)
            self.assertEqual(fixture, before)

    def test_complete_rom_ups_retains_all_other_translation_resources(self):
        n.verify_installation(self.built, self.native, self.module, self.report['noticeboard'])
        self.assertEqual(sha256(self.built), self.report['output_sha256'])
        self.assertEqual(apply_ups(self.native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), self.built)
        self.assertEqual(self.files.keys(), self.old.keys())
        changed = {v for v in self.files if self.files[v].extract(self.built) != self.old[v].extract(self.previous)}
        self.assertEqual(changed, {CODE_VROM, 0x19D40, n.OWNER_VROM, n.NEW_VROM, n.NEW_RELOCATION, 0x02800000, 0x03200000})
        old_table, new_table = self.old[0x19D40].extract(self.previous), self.files[0x19D40].extract(self.built)
        self.assertEqual(old_table[:DMA_START-0x19D40], new_table[:DMA_START-0x19D40])
        self.assertEqual(old_table[DMA_END-0x19D40:], new_table[DMA_END-0x19D40:])
        original = self.old[CODE_VROM].extract(self.previous)
        expected = owner.patch(original, (OWNERS/'owners.bin').read_bytes(),
                               json.loads((OWNERS/'owners.json').read_text()), self.module)
        self.assertEqual(expected, self.files[CODE_VROM].extract(self.built))
        old_module, new_module = self.old[0x02800000].extract(self.previous), self.files[0x02800000].extract(self.built)
        self.assertEqual(old_module[:0x48]+old_module[0x68:], new_module[:0x48]+new_module[0x68:])

    def test_actual_native_owner_code_is_required_not_just_manifest(self):
        original_code = by_vrom(self.native)[CODE_VROM].extract(self.native)
        code = bytearray(self.files[CODE_VROM].extract(self.built))
        at = 0x800A62A0-CODE_RAM
        code[at:at+4] = original_code[at:at+4]
        changed = replace_dma(self.built, {CODE_VROM: bytes(code)})
        with self.assertRaises(ValueError):
            n.verify_treasure_installation(changed, self.native, self.module, self.report['noticeboard']['treasure_owner'])
        for part in ('treasure_owner', 'complete_templates'):
            report = deepcopy(self.report['noticeboard']); report.pop(part)
            with self.assertRaises(ValueError): n.verify_installation(self.built, self.native, self.module, report)

    def test_combined_credit_adds_only_eighteen_installed_treasure_bodies(self):
        old, new = measure(self.native, self.previous, self.prior), measure(self.native, self.built, self.report)
        ids = {f'mail:{number:04X}' for number in IDS}
        expected = ids | {f'mail:{number:04X}' for number in n.INITIAL_IDS}
        credited = {key for key, row in new.rows.items() if any(r['route'] == 'noticeboard' for r in row['replacements'])}
        self.assertEqual(credited, expected)
        self.assertEqual(old.rows.keys(), new.rows.keys())
        for key in old.rows:
            if key not in ids: self.assertEqual(old.rows[key], new.rows[key])
        delta = sum(old.rows[key]['source_characters'] for key in ids if not old.rows[key]['replacements'])
        self.assertGreater(delta, 0)
        self.assertEqual(new.summary()['replaced_source_characters']-old.summary()['replaced_source_characters'], delta)
        self.assertEqual(old.summary()['total_source_characters'], new.summary()['total_source_characters'])


if __name__ == '__main__': unittest.main()
