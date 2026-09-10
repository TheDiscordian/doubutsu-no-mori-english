"""The title integrates current fixes and fails safely with a readable low-memory screen."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, sha256, apply_ups, CODE_RAM, CODE_VROM
from title_overlay import build, ACTOR, RELOC, ASSETS, NEW_ACTOR, NEW_RELOC, SIZE
from title_memory import BOOT, HELPER, HELPER_END, compile_helper
from title_logo_smoke import COMBINED_SHA256


@unittest.skipUnless((ROOT/'build/title-combined-01/preview.json').is_file(), 'Combined title required')
class CombinedTitleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.base = (ROOT/'build/collection-artwork-01/animal-forest-halfwidth.z64').read_bytes()
        cls.previous = json.loads((ROOT/'build/collection-artwork-01/build.json').read_text())
        folder = ROOT/'build/title-combined-01'
        cls.image = (folder/'animal-forest-title-preview.z64').read_bytes()
        cls.report = json.loads((folder/'preview.json').read_text())

    def test_combined_candidate_retains_all_current_screens_and_both_conversation_fixes(self):
        files = by_vrom(self.image)
        overlay, reloc = files[NEW_ACTOR].extract(self.image), files[NEW_RELOC].extract(self.image)
        before = copy.deepcopy(self.previous)
        image, patch, report = build(self.native, self.base, self.previous, self.rel, self.symbols,
                                     overlay, reloc, self.report['actor'])
        self.assertEqual(image, self.image)
        self.assertEqual(report, self.report)
        self.assertEqual(self.previous, before)
        self.assertEqual(sha256(image), COMBINED_SHA256)
        self.assertEqual(apply_ups(self.native, patch), image)
        old = by_vrom(self.base)
        for vrom, entry in old.items():
            if vrom not in (ACTOR, RELOC, ASSETS, CODE_VROM, BOOT, 0x19D40):
                self.assertEqual(files[vrom].extract(image), entry.extract(self.base), f'{vrom:08X}')
        self.assertEqual(report['memory']['required_ram_bytes'], 0x800000)
        self.assertEqual(report['memory']['ordinary_heap_end'], 0x80400000)
        self.assertIn('instruction screen', report['memory']['missing_expansion_pak'])

    def test_warning_compiles_inside_exact_bootstrap_tail_and_keeps_supported_path(self):
        warning, original = compile_helper(warning=True), compile_helper()
        self.assertEqual(len(warning), 204)
        self.assertLessEqual(len(warning), HELPER_END-HELPER)
        # Only the unsupported branch and ordinary tail location differ in the
        # prefix. The supported allocation and eight guard stores stay intact.
        self.assertEqual(warning[16:92], original[16:92])
        self.assertIn(b'Expansion Pak required.\n\nPower off and install it.\0', warning)
        self.assertEqual(sha256(warning), self.report['memory']['helper_sha256'])
        code = by_vrom(self.image)[CODE_VROM].extract(self.image)
        self.assertEqual(code[HELPER-CODE_RAM:HELPER_END-CODE_RAM], warning+bytes(HELPER_END-HELPER-len(warning)))
        # The new unsupported path calls drawer routines and osStopThread,
        # never fault_AddHungupAndCrash or a deliberate BREAK instruction.
        words = list(struct.unpack('>38I', warning[:152]))
        for address in (0x800292F4, 0x80027CF8, 0x8002A448, 0x8002DE10):
            self.assertIn(0x0C000000|((address>>2)&0x3FFFFFF), words)
        self.assertNotIn(0x0000000D, words)
        self.assertNotIn(0x0C000000|((0x80029AB4>>2)&0x3FFFFFF), words)

    def test_unreviewed_baseline_and_damaged_source_report_reject(self):
        files = by_vrom(self.image)
        overlay, reloc = files[NEW_ACTOR].extract(self.image), files[NEW_RELOC].extract(self.image)
        for base, report in ((self.base[:-1], self.previous),
                              (self.base, dict(self.previous, output_sha256='0'*64))):
            with self.assertRaisesRegex(ValueError, 'reviewed complete'):
                build(self.native, base, report, self.rel, self.symbols, overlay, reloc, self.report['actor'])

    def test_recorded_native_supported_and_missing_pak_paths(self):
        for folder, expansion in (('title-combined-native-01', True), ('title-warning-native-01', False)):
            records = json.loads((ROOT/'build'/folder/'results.json').read_text())
            self.assertEqual(records[0]['rom_sha256'], COMBINED_SHA256)
            self.assertEqual(records[0]['audio'], 'disabled')
            self.assertEqual(records[0]['expansion_pak'], expansion)
            self.assertTrue(records[-1]['graceful_shutdown'])
            self.assertTrue(all(row['assertion'] in ('passed', 'not_requested')
                                for row in records if 'assertion' in row))
            if expansion:
                result = next(row for row in records if 'title_logo_memory' in row)
                self.assertEqual(result['animation_frames'], [121.0]*3)
                self.assertEqual(result['error'], 0)
            else:
                result = next(row for row in records if 'title_expansion_warning' in row)
                self.assertEqual(result['verified_pixels'], 3072)
                self.assertTrue(result['graph_thread_stopped'])
                self.assertFalse(result['faulted_thread'])


if __name__ == '__main__':
    unittest.main()
