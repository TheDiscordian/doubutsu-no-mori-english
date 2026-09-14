"""The shop fixture must not pre-award the item it is meant to buy."""
import json
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from v3_clothing_gameplay_fixture import create
from v3_save_codec import BANK, PAYLOAD

OUTPUT = ROOT/'build/v3-clothing-shop-floor-01'
SOURCE = ROOT/'local/rc2-save-report-g3O4lU/test.flash'


@unittest.skipUnless((OUTPUT/'build.json').is_file() and SOURCE.is_file(),
                     'Preserved town and current clothing cartridge required')
class ShopFixture(unittest.TestCase):
    def test_only_stock_wallet_and_checked_format_change(self):
        source = SOURCE.read_bytes()
        rom = (OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        report = json.loads((OUTPUT/'build.json').read_text())
        fixture, receipt = create(source, rom, report, shop_stock=True)
        self.assertFalse(receipt['seeded_ownership'])
        self.assertIsNone(receipt['pocket_slot'])
        self.assertTrue(receipt['seeded_shop_stock'])
        for index in range(2):
            bank = fixture[index*BANK:(index+1)*BANK]
            restored = bytearray(bank[:PAYLOAD])
            original = source[index*BANK:index*BANK+PAYLOAD]
            self.assertEqual(bank[0xED26:0xED28], bytes.fromhex('34BF'))
            self.assertEqual(struct.unpack_from('>I', bank, 0x58)[0], 1000)
            self.assertEqual(bank[PAYLOAD+0xC0:PAYLOAD+0x2C0], bytes(512))
            self.assertEqual(bank[PAYLOAD+0x2E0:PAYLOAD+0x360], bytes(128))
            self.assertEqual(sum(struct.unpack('>'+str(PAYLOAD//2)+'H', restored)) & 0xFFFF, 0)
            restored[0x12:0x14] = bytes(2)
            self.assertEqual(zlib.crc32(restored), struct.unpack_from('>I', bank, PAYLOAD+12)[0])
            for start, end in ((4, 8), (0x12, 0x14), (0x58, 0x5C), (0xED26, 0xED28)):
                restored[start:end] = original[start:end]
            self.assertEqual(restored, original)
        self.assertEqual(SOURCE.read_bytes(), source)


if __name__ == '__main__': unittest.main()
