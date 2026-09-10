"""First-job continuation ownership, exact MIPS words, and cartridge retention."""
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
from aflib import by_vrom, sha256, apply_ups
from check_keyboard_assembly import IMAGE
from npc_mail_show import source, relocate_verified_data
from first_job_progression import SPEC, PATCHES, LETTER_PATCH, patch

BASE = ROOT/'build/classic-letters-pilot'
BUILD = ROOT/'build/v0-first-job-fix-01'
ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'


@unittest.skipUnless(ROM.is_file(), 'Supplied native ROM required')
class FirstJobProgressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = ROM.read_bytes()
        cls.original, cls.reloc = source(cls.native, 'first_job')

    def test_independent_mips_assembly(self):
        with tempfile.TemporaryDirectory(prefix='af-first-job-') as directory:
            docker = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
                      '-v', f'{ROOT}/overlays/first_job:/source:ro', '-v', f'{directory}:/out',
                      '-w', '/out', '--entrypoint']
            def run(tool, *args):
                subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool, IMAGE, *args],
                               check=True, capture_output=True, timeout=60)
            run('as', '-EB', '-mabi=32', '-march=vr4300', '/source/reward.s', '-o', 'reward.o')
            run('objcopy', '-O', 'binary', '-j', '.text', 'reward.o', 'reward.bin')
            data = (Path(directory)/'reward.bin').read_bytes()
            self.assertEqual(data[:12], struct.pack('>3I', *(p[2] for p in PATCHES)))
            self.assertFalse(any(data[12:]))

    def test_only_owner_step_and_index_read_change_at_both_heap_bases(self):
        changed = patch(self.native, self.original, self.reloc)
        expected = bytearray(self.original)
        for at, before, after in PATCHES:
            self.assertEqual(struct.unpack_from('>I', expected, at-SPEC.ram)[0], before)
            struct.pack_into('>I', expected, at-SPEC.ram, after)
        self.assertEqual(changed, expected)
        # Existing table step eleven is the actual no-operation handler.
        self.assertEqual(struct.unpack_from('>I', changed, 0x8091D620-SPEC.ram+11*4)[0], 0x8091D544)
        self.assertEqual(changed[0x8091D544-SPEC.ram:0x8091D550-SPEC.ram],
                         bytes.fromhex('afa4000003e0000800000000'))
        for base in (0x801A0010, 0x802F8010):
            moved = relocate_verified_data(SPEC, changed, self.reloc, base)
            old = bytearray(relocate_verified_data(SPEC, self.original, self.reloc, base))
            for at, _, after in PATCHES:
                struct.pack_into('>I', old, at-SPEC.ram, after)
            self.assertEqual(moved, old)

    def test_wrong_source_changed_owner_or_relocation_rejected(self):
        for at in (0, 0x8091D2E0-SPEC.ram, len(self.original)-1):
            data = bytearray(self.original)
            data[at] ^= 1
            with self.assertRaises(ValueError):
                patch(self.native, bytes(data), self.reloc)
        reloc = bytearray(self.reloc)
        reloc[20] ^= 1
        with self.assertRaises(ValueError):
            patch(self.native, self.original, bytes(reloc))

    @unittest.skipUnless((BUILD/'build.json').is_file(), 'Correction candidate required')
    def test_serialized_native_fixture_covers_all_six_advice_endings(self):
        from first_job_smoke import scenario
        from textcodec import tokenize
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text())
        request = json.loads(json.dumps(scenario(self.native, built, report)))[3]['test_first_job_progression']
        expected = {0x8F4: 0x921, 0x8F8: 0x2B05, 0x8FA: 0x2B06}
        for root in range(0x8F0, 0x8FB, 2):
            tokens = [t for t in tokenize(bytes.fromhex(request['messages'][str(root)]), request['info']) if t.kind == 'cmd']
            links = [int.from_bytes(t.data[2:], 'big') for t in tokens if t.data[1] == 14]
            self.assertEqual(links, [expected[root]] if root in expected else [])
            self.assertEqual(tokens[-1].data, b'\x7f\x01' if links else b'\x7f\x00')
            if links:
                final = [t for t in tokenize(bytes.fromhex(request['messages'][str(links[0])]), request['info']) if t.kind == 'cmd']
                self.assertEqual(final[-1].data, b'\x7f\x00')

    @unittest.skipUnless((ROOT/'build/v0-first-job-native-02/results.json').is_file(), 'Recorded native run required')
    def test_recorded_native_run_reproduces_loop_and_closes_six_corrected_paths(self):
        records = json.loads((ROOT/'build/v0-first-job-native-02/results.json').read_text())
        self.assertEqual(records[0]['rom_sha256'], sha256((BUILD/'animal-forest-halfwidth.z64').read_bytes()))
        self.assertEqual(records[0]['audio'], 'disabled')
        self.assertFalse(records[0]['expansion_pak'])
        summary = next(r for r in records if 'first_job_corrected_conversations' in r)
        self.assertTrue(summary['first_job_original_loop_reproduced'])
        self.assertEqual(summary['native_calls'], 70)
        self.assertEqual(summary['assertions'], 170)
        self.assertFalse(summary['normal_actor_gameplay'])
        self.assertEqual([r['looks'] for r in summary['first_job_corrected_conversations']], list(range(6)))
        self.assertTrue(all(r['final_disappear_requested'] for r in summary['first_job_corrected_conversations']))
        self.assertEqual(next(r for r in records if r.get('first_job_original_loop_reproduced') and 'messages' in r)['messages'],
                         [0x8F8, 0x8F8])
        self.assertTrue(all(r['assertion'] == 'passed' for r in records if 'assertion' in r))
        self.assertTrue(any(r.get('loaded_state') == 'test.bs1' for r in records))
        self.assertTrue(records[-1]['graceful_shutdown'])

    @unittest.skipUnless((BUILD/'build.json').is_file(), 'Correction candidate required')
    def test_complete_rom_and_patch_retain_every_other_resource(self):
        before = (BASE/'animal-forest-halfwidth.z64').read_bytes()
        after = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text())
        old, new = by_vrom(before), by_vrom(after)
        self.assertEqual(set(old), set(new))
        self.assertEqual(len(before), len(after))
        self.assertEqual(sha256(after), report['output_sha256'])
        self.assertEqual(apply_ups(self.native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), after)
        for vrom in old:
            self.assertEqual(old[vrom].index, new[vrom].index)
            expected = patch(self.native, self.original, self.reloc) if vrom == SPEC.vrom else old[vrom].extract(before)
            actual = new[vrom].extract(after)
            if vrom == 0x19D40:
                actual, expected = actual[:16], expected[:16]
            self.assertEqual(actual, expected, f'Resource {vrom:08X}')
        self.assertIn(f'{SPEC.vrom:08X}', report['replacement_files'])


@unittest.skipUnless((ROOT/'build/v0-hardware-fixes-02/build.json').is_file(), 'Complete first-job correction required')
class FirstJobLetterAdviceTests(unittest.TestCase):
    def test_independent_letter_state_instruction(self):
        with tempfile.TemporaryDirectory(prefix='af-first-job-letter-') as directory:
            docker = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
                      '-v', f'{ROOT}/overlays/first_job:/source:ro', '-v', f'{directory}:/out',
                      '-w', '/out', '--entrypoint']
            def run(tool, *args):
                subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool, IMAGE, *args],
                               check=True, capture_output=True, timeout=60)
            run('as', '-EB', '-mabi=32', '-march=vr4300', '/source/letter_advice.s', '-o', 'letter.o')
            run('objcopy', '-O', 'binary', '-j', '.text', 'letter.o', 'letter.bin')
            data = (Path(directory)/'letter.bin').read_bytes()
            self.assertEqual(data[:4], struct.pack('>I', LETTER_PATCH[2]))
            self.assertFalse(any(data[4:]))

    def test_installed_letter_variant_changes_one_word_and_retains_every_other_resource(self):
        native = ROM.read_bytes()
        before = (ROOT/'build/v0-hardware-fixes-01/animal-forest-halfwidth.z64').read_bytes()
        after = (ROOT/'build/v0-hardware-fixes-02/animal-forest-halfwidth.z64').read_bytes()
        old, new = by_vrom(before), by_vrom(after)
        original, reloc = source(native, 'first_job')
        expected = bytearray(old[SPEC.vrom].extract(before))
        at, original_word, after_word = LETTER_PATCH
        self.assertEqual(struct.unpack_from('>I', expected, at-SPEC.ram)[0], original_word)
        struct.pack_into('>I', expected, at-SPEC.ram, after_word)
        self.assertEqual(patch(native, original, reloc, letter_advice=True), expected)
        self.assertEqual(set(old), set(new))
        for vrom in old:
            a, b = old[vrom].extract(before), new[vrom].extract(after)
            if vrom == SPEC.vrom:
                self.assertEqual(b, expected)
            elif vrom == 0x19D40:
                self.assertEqual(a[:16], b[:16])
            else:
                self.assertEqual(a, b, f'Resource {vrom:08X}')

    @unittest.skipUnless((ROOT/'build/v0-first-job-letter-native-01/results.json').is_file(), 'Native letter run required')
    def test_native_comparison_preserves_both_long_letters_and_normal_final_end(self):
        records = json.loads((ROOT/'build/v0-first-job-letter-native-01/results.json').read_text())
        built = ROOT/'build/v0-hardware-fixes-02/animal-forest-halfwidth.z64'
        self.assertEqual(records[0]['rom_sha256'], sha256(built.read_bytes()))
        summary = next(r for r in records if 'first_job_corrected_conversations' in r)
        self.assertTrue(summary['first_job_original_letter_target_overwritten'])
        self.assertEqual((summary['native_calls'], summary['assertions']), (43, 99))
        self.assertEqual([r['messages'] for r in summary['first_job_corrected_conversations']],
                         [[0x90C], [0x910, 0xA26], [0x912, 0x2B47]])
        self.assertTrue(all(r['final_disappear_requested'] for r in summary['first_job_corrected_conversations']))
        self.assertTrue(all(r['assertion'] == 'passed' for r in records if 'assertion' in r))
        self.assertTrue(any(r.get('actual_target') == 0 and r.get('expected_target') == 0xA26 for r in records))
        self.assertTrue(any(r.get('loaded_state') == 'test.bs1' for r in records))
        self.assertTrue(records[-1]['graceful_shutdown'])


if __name__ == '__main__':
    unittest.main()
