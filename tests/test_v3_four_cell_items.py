"""The bonfire retains all four cells, with no unsupported shape substitution."""
import json
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.test_v3_furniture_art import ROOT
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from v3_four_cell_items import CELLS, source_evidence


class FourCellItemTests(unittest.TestCase):
    def test_original_and_donor_tables_and_actual_native_selector(self):
        original = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        rel = (ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        result = source_evidence(original, rel, symbols)
        self.assertEqual(result['cells'], [[1, 0, 0], [1, 1, 0], [1, 1, 1], [1, 0, 1]])
        self.assertEqual(result['size_query_result'], 2)
        self.assertFalse(result['rotation_changes_footprint'])
        current = (ROOT / 'build/v3-camping-runtime-01/animal-forest-v3-asset-loader.z64').read_bytes()
        self.assertEqual(sha256(current), '3967dedabca6e65a97f57273028aaa19b0b24ed72b405f2498d5a4fce6a1cd29')
        code = by_vrom(current)[CODE_VROM].extract(current)
        self.assertEqual(code[0x8010D2FC - CODE_RAM:0x8010D314 - CODE_RAM],
                          b''.join(struct.pack('>Bxhh', *row) for row in CELLS))
        self.assertEqual(sha256(code[0x800BE6D8 - CODE_RAM:0x800BE72C - CODE_RAM]),
                          result['native_selector_sha256'])

    def test_sanitized_actual_shared_item_and_sparse_profile_readers(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-four-cells-') as directory:
            binary = Path(directory) / 'test'
            subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT / 'tests/v3_four_cell_items_test.c'), '-o', str(binary)], check=True, capture_output=True)
            result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=20)
            self.assertIn('Four-cell size, all rotations, sparse selection, signed boundaries, and original fallbacks pass',
                          result.stdout)

    def test_compiled_native_reservation_and_all_public_entry_points(self):
        output = ROOT / 'build/v3-four-cell-items-01'
        report = json.loads((output / 'items.json').read_bytes())
        code = (output / 'items/code.bin').read_bytes()
        compiled = report['code']
        self.assertEqual(sha256(code), compiled['sha256'])
        self.assertEqual(len(code), compiled['bytes'])
        self.assertLessEqual(len(code), 0x1000)
        self.assertFalse(report['runtime_installed'])
        self.assertFalse(report['web_patcher_enabled'])
        for name in ('name', 'type', 'size', 'place', 'price'):
            address = compiled['symbols']['af_v3_item_' + name + '_extended']
            self.assertEqual(address & 3, 0)
            self.assertTrue(0x80483000 <= address < 0x80483000 + len(code))
        self.assertIn('-DAF_V3_FOUR_CELL_ITEMS=1', compiled['flags'])


if __name__ == '__main__':
    unittest.main()
