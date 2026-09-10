"""Clock translation preserves native state while composing aligned English fields."""
import copy
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import apply_ups, by_vrom, sha256, u32
from check_keyboard_assembly import IMAGE
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
from textcodec import LATIN
from time_setting import (VROM, RELOC, RAM, SECTIONS, FIELDS, PATCHES, POSITIONS,
                          source, reference, patch_owner, widths, measure_text, build)
from translation_progress import CounterLedger


@unittest.skipUnless((ROOT/'build/time-setting-01/build.json').is_file(), 'Local clock candidate required')
class TimeSettingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.base = (ROOT/'build/inventory-artwork-02/animal-forest-halfwidth.z64').read_bytes()
        cls.base_report = json.loads((ROOT/'build/inventory-artwork-02/build.json').read_text())
        cls.built = (ROOT/'build/time-setting-01/animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((ROOT/'build/time-setting-01/build.json').read_text())

    def test_independent_mips_instructions(self):
        with tempfile.TemporaryDirectory(prefix='af-clock-assembly-') as directory:
            docker = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
                      '-v', f'{ROOT}/overlays/time_setting:/source:ro', '-v', f'{directory}:/out',
                      '-w', '/out', '--entrypoint']
            def run(tool, *args):
                subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool, IMAGE, *args],
                               check=True, capture_output=True, timeout=60)
            run('as', '-EB', '-mabi=32', '-march=vr4300', '/source/labels.s', '-o', 'labels.o')
            run('objcopy', '-O', 'binary', '-j', '.text', 'labels.o', 'labels.bin')
            data = (Path(directory)/'labels.bin').read_bytes()
            self.assertEqual(data[:44], struct.pack('>11I', *(p[2] for p in PATCHES)))
            self.assertFalse(any(data[44:]))

    def test_complete_words_bounded_fields_and_aligned_numbers(self):
        reference(self.rel, self.symbols)
        changed, reloc = patch_owner(self.native)
        advances = widths(self.built)
        for address, capacity, text in FIELDS:
            self.assertTrue(all(v in LATIN for v in text))
            self.assertEqual(changed[address-RAM:address-RAM+capacity], text+bytes(capacity-len(text)))
        date = FIELDS[1][2].decode()
        for i, index in enumerate((2, 5, 8)):
            self.assertEqual(POSITIONS[i], (122+sum(advances[c] for c in date[:index])*.875, 115))
        for value in range(100):
            self.assertEqual(sum(advances[c] for c in f'{value:02}')*.875, 10.5)
        self.assertEqual(POSITIONS[3][0]+10.5, 112.5)
        self.assertEqual(112.5+advances[':']*.875, POSITIONS[4][0])
        self.assertEqual(tuple(struct.iter_unpack('>2f', changed[0x1080:0x10A8])), POSITIONS)

    def test_only_display_changes_and_both_relocations_keep_state_and_code(self):
        original, reloc = source(self.native)
        changed, after_reloc = patch_owner(self.native)
        self.assertEqual(after_reloc, reloc)
        spec = Image(RAM, len(original)+SECTIONS[3], SECTIONS)
        allowed = {i for address, _, _ in PATCHES for i in range(address-RAM, address-RAM+4)}
        allowed.update(range(0x1040, 0x1068))
        allowed.update(range(0x1080, 0x10A8))
        for base in (0x801A0010, 0x802F8010):
            old = relocate_verified_data(spec, original, reloc, base)
            new = relocate_verified_data(spec, changed, reloc, base)
            self.assertEqual(len(new), len(original)+32)
            self.assertEqual(new[-32:], bytes(32))
            self.assertTrue(all(a == b or i in allowed for i, (a, b) in enumerate(zip(old, new))))
            for high, low, target in ((0x80883BBC, 0x80883BF4, 0x808841E0),
                                      (0x80883C2C, 0x80883C54, 0x808841F4),
                                      (0x80883C90, 0x80883CB8, 0x80884200),
                                      (0x80883DE8, 0x80883DF0, 0x80884204)):
                hi, lo = u32(new, high-RAM)&0xFFFF, u32(new, low-RAM)&0xFFFF
                self.assertEqual((hi<<16)+lo-(0x10000 if lo&0x8000 else 0), base+target-RAM)
        self.assertEqual(changed[0x1068:0x1080], original[0x1068:0x1080])  # selected/unselected colours

    def test_counter_uses_same_source_total_and_rejects_changed_installation(self):
        from post_v0_progress import predecessor, BASE_SHA
        base, previous = predecessor(self.built, self.report)
        self.assertEqual(sha256(base), BASE_SHA)
        self.assertEqual(previous['output_sha256'], BASE_SHA)
        altered = copy.deepcopy(self.report)
        altered['time_setting']['strings'][0]['english'] = 'Missing'
        for rom, metadata in ((self.built[:-1], self.report), (self.built, altered)):
            with self.assertRaisesRegex(ValueError, 'approved complete'):
                predecessor(rom, metadata)
        old, new = CounterLedger([(2, 0)]*0x77), CounterLedger([(2, 0)]*0x77)
        measure_text(old, self.native, self.base, self.base_report)
        measure_text(new, self.native, self.built, self.report)
        self.assertEqual(old.summary()['total_records'], 4)
        self.assertEqual(old.summary()['total_source_characters'], new.summary()['total_source_characters'])
        self.assertEqual(old.summary()['replaced_records'], 0)
        self.assertEqual(new.summary()['replaced_records'], 4)
        self.assertEqual(new.summary()['percent'], 100)
        with self.assertRaisesRegex(ValueError, 'Changed installed'):
            measure_text(CounterLedger([(2, 0)]*0x77), self.native, self.base, self.report)
        bad = copy.deepcopy(self.report)
        bad['time_setting']['strings'][0]['read_bytes'] -= 1
        with self.assertRaisesRegex(ValueError, 'Changed installed'):
            measure_text(CounterLedger([(2, 0)]*0x77), self.native, self.built, bad)

    def test_candidate_retains_prior_translation_and_rejects_wrong_sources(self):
        report_before = copy.deepcopy(self.base_report)
        image, ups, report = build(self.native, self.base, self.base_report, self.rel, self.symbols)
        self.assertEqual(self.base_report, report_before)
        self.assertEqual(image, self.built)
        self.assertEqual(report, self.report)
        self.assertEqual(sha256(image), '54a6d643d27cd36345e2298407f47f5bb51ddf2c6f947558391da968cbf717be')
        self.assertEqual(apply_ups(self.native, ups), image)
        files, old = by_vrom(image), by_vrom(self.base)
        self.assertEqual(len(image), 32*1024*1024)
        self.assertEqual(set(files), set(old))
        for vrom, entry in old.items():
            if vrom not in (VROM, 0x19D40):
                self.assertEqual(files[vrom].extract(image), entry.extract(self.base), f'{vrom:08X}')
        for rel, symbols in ((self.rel[:-1], self.symbols), (self.rel, self.symbols+b'\n')):
            with self.assertRaises(ValueError): reference(rel, symbols)
        with self.assertRaises(ValueError): patch_owner(self.native[:-1])
        with self.assertRaisesRegex(ValueError, 'baseline'):
            build(self.native, self.base[:-1], self.base_report, self.rel, self.symbols)


if __name__ == '__main__':
    unittest.main()
