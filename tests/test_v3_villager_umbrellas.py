"""Current umbrella identity and asset verification; no ROM changes are needed."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from v3_villager_umbrellas import verify


class UmbrellaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        output = ROOT/'build/v3-villager-rewards-01'
        cls.rom = (output/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report = json.loads((output/'build.json').read_text())

    def test_complete_current_art_and_defaults_without_rom_changes(self):
        result = verify(self.native, self.rom, self.rel, self.symbols, self.report)
        self.assertFalse(result['rom_changes_needed'])
        self.assertEqual([r['installed_umbrella'] for r in result['verified_defaults']], [3, 13])
        self.assertEqual([r['tool_number'] for r in result['artwork']], [3, 13])
        for row in result['artwork']:
            self.assertEqual(row['compared_pixels'], 2048)
            self.assertEqual(row['compared_vertices'], 56)
            self.assertEqual(row['matrix_flags_removed'], 56)
            self.assertEqual(row['canopy_handle_triangles'], [18, 15])

    def test_changed_inputs_are_rejected(self):
        with self.assertRaises(ValueError):
            verify(self.native, self.rom, self.rel[:-1]+b'!', self.symbols, self.report)
        with self.assertRaises(ValueError):
            verify(self.native, self.rom[:-1]+b'!', self.rel, self.symbols, self.report)


if __name__ == '__main__': unittest.main()
