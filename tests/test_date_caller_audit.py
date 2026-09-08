"""Date caller inventories distinguish real installed targets from intentions."""

import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, replace_dma
from audit_date_callers import call_target, inventory


class DateCallTargetTests(unittest.TestCase):
    def test_only_direct_jump_words_are_accepted(self):
        for opcode in (2, 3):
            self.assertEqual(call_target((opcode << 26) | (0x800C4084 & 0x0FFFFFFF) >> 2), 0x800C4084)
        for word in (0, 0x03E00008, 0x0320F809, 0x800C4084):
            with self.assertRaises(ValueError):
                call_target(word)


@unittest.skipUnless((ROOT/'build/fortune-recovery-pilot/build.json').is_file(),
                     'Installed recovery cartridge required')
class DateCallerAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.installed = (ROOT/'build/fortune-recovery-pilot/animal-forest-halfwidth.z64').read_bytes()
        cls.build = json.loads((ROOT/'build/fortune-recovery-pilot/build.json').read_text())

    def test_current_direct_calls_are_classified_from_installed_instructions(self):
        result = inventory(self.native, self.installed, self.build)
        self.assertFalse(result['completion_claim'])
        self.assertEqual(result['states'], {'resident_formatter_installed': 10, 'native_formatter_remaining': 13})
        remaining = {(r['field'], r['call_ram']) for r in result['callers']
                     if r['state'] == 'native_formatter_remaining'}
        self.assertEqual(remaining, {
            ('year','809584F0'), ('month','800A639C'), ('month','809584B8'),
            ('month','8095BB0C'), ('month','8095BB94'), ('day','800A63BC'),
            ('day','809584D4'), ('day','8095BB2C'), ('day','8095BBB4'),
            ('hour','8095BB4C'), ('hour','8095BBD4'),
            ('number_unit','809D6724'), ('number_unit','80A902EC')})

    def test_unexpected_overlay_target_is_rejected_even_with_correct_module(self):
        files = by_vrom(self.installed)
        changed = bytearray(files[0x84D180].extract(self.installed))
        struct.pack_into('>I', changed, 0x809584B8-0x809583B0, 0x0C000000 | (0x800C41B8 & 0x0FFFFFFF) >> 2)
        with self.assertRaisesRegex(ValueError, 'Unrecognised installed date target'):
            inventory(self.native, replace_dma(self.installed, {0x84D180: bytes(changed)}), self.build)

    @unittest.skipUnless((ROOT/'build/leaflet-dates-pilot/build.json').is_file(),
                         'Installed full leaflet date fixture required')
    def test_same_address_hour_body_is_counted_only_when_its_complete_english_code_is_verified(self):
        from aflib import CODE_RAM,CODE_VROM
        from leaflet_dates import HOUR
        directory = ROOT/'build/leaflet-dates-pilot'
        rom = (directory/'animal-forest-halfwidth.z64').read_bytes()
        build = json.loads((directory/'build.json').read_text())
        result = inventory(self.native,rom,build)
        self.assertEqual(result['states'], {'resident_formatter_installed':17,
                         'english_leaflet_formatter_installed':2,'native_formatter_remaining':4})
        data = bytearray(by_vrom(rom)[CODE_VROM].extract(rom));data[HOUR-CODE_RAM+4] ^= 1
        with self.assertRaises(ValueError):
            inventory(self.native,replace_dma(rom,{CODE_VROM:bytes(data)}),build)


if __name__ == '__main__':
    unittest.main()
