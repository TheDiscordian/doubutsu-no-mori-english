"""Check the actual combined V2 deliverable and its published output identity."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import apply_ups, by_vrom, n64_checksum, sha256
from build_portal import TARGET_SHA
from credits_title_fix import BASES, DATA, TABLE, TITLE
from prepare_pages import OUTPUT_SHA
from textbanks import Bank
from dresser_menu_fix import ROOM, DECISION, ROOM_RAM, AFTER

OUTPUT = ROOT/'build/v2-dresser-14'
NAME = 'Animal Forest English V2'


class PublishedIdentityTests(unittest.TestCase):
    def test_export_and_pages_agree_on_current_v2(self):
        manifest = json.loads((ROOT/'web/release/manifest.json').read_text())
        self.assertEqual(manifest['build'], 'V2-14')
        self.assertEqual(manifest['output_sha256'], TARGET_SHA)
        self.assertEqual(OUTPUT_SHA, TARGET_SHA)


@unittest.skipUnless((OUTPUT/(NAME+'.z64')).is_file(), 'Private build required')
class CombinedCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (OUTPUT/(NAME+'.z64')).read_bytes()
        cls.files = by_vrom(cls.image)

    def test_title_and_museum_fix_are_in_same_image(self):
        bank = Bank('string', DATA, TABLE, self.files[DATA].extract(self.image),
                    self.files[TABLE].extract(self.image))
        self.assertEqual(bank.entries()[TITLE], b'Animal Crossing')
        folder, _, digest = BASES['v2-13']
        base = (ROOT/folder/(NAME+'.z64')).read_bytes()
        self.assertEqual(sha256(base), digest)
        previous = json.loads((ROOT/folder/'build.json').read_text())
        for vrom, expected in previous['changed_resources'].items():
            self.assertEqual(sha256(self.files[int(vrom, 16)].extract(self.image)), expected)
        old = by_vrom(base)
        rows = Bank('string', DATA, TABLE, old[DATA].extract(base), old[TABLE].extract(base)).entries()
        rows[TITLE] = b'Animal Crossing'
        self.assertEqual(bank.entries(), rows)
        self.assertEqual(set(self.files), set(old))
        for vrom, entry in old.items():
            if vrom not in (DATA, TABLE, 0x19D40, 0x2000000, ROOM):
                self.assertEqual(entry.extract(base), self.files[vrom].extract(self.image), hex(vrom))
        messages = Bank('message',0x2000000,0xCF9000,self.files[0x2000000].extract(self.image),
                        self.files[0xCF9000].extract(self.image)).entries()
        self.assertIn(AFTER,messages[0xA0B])
        self.assertEqual(struct.unpack_from('>I',self.files[ROOM].extract(self.image),DECISION-ROOM_RAM)[0],0x24010002)

    def test_current_hash_checksum_and_patch_reconstruction(self):
        self.assertEqual(sha256(self.image), TARGET_SHA)
        self.assertEqual(struct.unpack_from('>2I', self.image, 0x10), n64_checksum(self.image))
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native, (OUTPUT/(NAME+'.ups')).read_bytes()), self.image)
        report = json.loads((OUTPUT/'build.json').read_text())
        self.assertEqual(report['build'], 'V2-14')
        self.assertFalse(report['save_format_changed'])
        self.assertFalse(report['delivery_code_changed'])
        self.assertFalse(report['credits_title']['executable_code_changed'])


if __name__ == '__main__':
    unittest.main()
