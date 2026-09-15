"""Actual donor properties, exactly scoped installation, and retained saves."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from aflib import by_vrom, n64_checksum, sha256
from v3_asset_loader import BLOB, MODULE
from v3_aloha_scoring import BASE, BASE_SHA, metadata
import v3_hra as hra
import v3_feng_shui as feng

OUTPUT = ROOT / 'build/v3-aloha-scoring-01'


class AlohaScoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.base = (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report = json.loads((OUTPUT / 'build.json').read_text())
        cls.prior = json.loads((BASE / 'build.json').read_text())
        cls.files, cls.old_files = by_vrom(cls.rom), by_vrom(cls.base)

    def test_real_source_metadata_and_installed_display_identity(self):
        rel = (ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        rows = metadata(rel, symbols, self.report['aloha_display']['rows'])
        self.assertEqual([(r['item_id'], r['runtime_index'], r['donor_runtime_index']) for r in rows],
                         [('3868', 1562, 517), ('386C', 1563, 518)])
        self.assertEqual(rows, self.report['aloha_scoring']['imports'])
        altered = [dict(row) for row in self.report['aloha_display']['rows']]
        altered[-1]['runtime_index'] = 1727
        with self.assertRaises(ValueError): metadata(rel, symbols, altered)

    def test_complete_scoring_tables_preserve_every_other_row(self):
        for key, tool, width in (('hra', hra, 4), ('feng_shui', feng, 2)):
            data, before = (self.files[tool.NEW_VROM].extract(self.rom), self.old_files[tool.NEW_VROM].extract(self.base))
            at = self.report[key]['metadata_address'] - tool.RAM
            expected = bytearray(before)
            for index in (1562, 1563):
                expected[at + index * width:at + (index + 1) * width] = bytes.fromhex('D4051000') if width == 4 else bytes(2)
            self.assertEqual(data, expected)
            self.assertEqual(self.files[tool.NEW_RELOC].extract(self.rom), self.old_files[tool.NEW_RELOC].extract(self.base))
            self.assertEqual([r['item_id'] for r in self.report[key]['imports'][-2:]], ['3868', '386C'])
            self.assertEqual(data[at + 1727 * width:at + 1728 * width], before[at + 1727 * width:at + 1728 * width])

    def test_only_two_words_change_no_allocation_profile_or_resource_crc_changes(self):
        self.assertEqual(sha256(self.base), BASE_SHA)
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])
        self.assertEqual(self.files, self.old_files)
        self.assertEqual(self.report['save_runtime'], self.prior['save_runtime'])
        self.assertEqual(self.files[MODULE].extract(self.rom), self.old_files[MODULE].extract(self.base))
        self.assertEqual(struct.unpack_from('>2I', self.rom, 16), n64_checksum(self.rom))
        restored = bytearray(self.rom)
        for row in self.report['aloha_scoring']['writes']:
            at = row['offset']
            self.assertEqual(self.rom[at:at + 4].hex(), row['after'])
            self.assertEqual(self.base[at:at + 4].hex(), row['before'])
            restored[at:at + 4] = bytes.fromhex(row['before'])
        self.assertEqual(restored, self.base)
        self.assertEqual(self.files[BLOB].extract(self.rom)[:0xC000], self.old_files[BLOB].extract(self.base)[:0xC000])


if __name__ == '__main__': unittest.main()
