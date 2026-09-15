"""Bounded house-ID changes must retain every unrelated native instruction."""
import json
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import DMA_START, apply_ups, by_vrom, n64_checksum, sha256
from v3_house_exterior import BASE, BASE_SHA, BLOB, CONFIG, MODULE, OWNERS, STARTUP, patch_owner

OUTPUT = ROOT/'build/v3-house-exterior-01'


@unittest.skipUnless((OUTPUT/'build.json').exists(), 'Current exterior cartridge required')
class HouseExteriorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = (OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.base = (BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report = json.loads((OUTPUT/'build.json').read_text())
        cls.files, cls.old = by_vrom(cls.rom), by_vrom(cls.base)

    def test_six_instructions_change_only_declared_house_decisions(self):
        for owner in OWNERS:
            original = self.old[owner[0]].extract(self.base)
            actual = self.files[owner[0]].extract(self.rom)
            expected, report = patch_owner(original, owner)
            self.assertEqual(actual, expected)
            self.assertIn(report, self.report['house_exterior']['owners'])
            changed = bytearray(original)
            for at, before, after, _ in owner[3]:
                struct.pack_into('>I', changed, at, after)
                # All callers load a u16 house ID before this signed comparison.
                # Preserve every native/other decision outside the twenty imports.
                for item in range(65536):
                    old_value, new_value = item < (before & 65535), item < (after & 65535)
                    if 0x50DA <= item < 0x50EE:
                        self.assertTrue(new_value)
                    else:
                        self.assertEqual(old_value, new_value)
            self.assertEqual(actual, changed)
            with self.assertRaises(ValueError):
                patch_owner(bytes([original[0]^1])+original[1:], owner)
        # F0DF is the first native player-house marker, not a free NPC marker.
        npc = self.files[0x8681F0].extract(self.rom)
        self.assertEqual(npc[0x3B44:0x3B48].hex(), '3412f0df')
        self.assertEqual(self.files[0x8D4A20].extract(self.rom), self.old[0x8D4A20].extract(self.base))

    def test_storage_profile_and_complete_patch(self):
        blob = self.files[BLOB].extract(self.rom)
        expected_blob = bytearray(self.old[BLOB].extract(self.base))
        struct.pack_into('>I', expected_blob, 4, 59)
        expected_blob.extend(bytes((-len(expected_blob))&15))
        self.assertEqual(len(expected_blob), self.report['house_exterior']['grow_blob_offset'])
        expected_blob.extend(self.files[0x970920].extract(self.rom))
        self.assertEqual(blob, expected_blob)
        self.assertLessEqual(self.files[BLOB].pstart+len(blob), len(self.rom))
        self.assertEqual(self.files[0x970920].pstart,
                         self.files[BLOB].pstart+self.report['house_exterior']['grow_blob_offset'])
        self.assertEqual(self.files[0x970920].pend, 0)
        self.assertEqual(blob[0x20:0xE0], bytes.fromhex(self.report['save_runtime']['profile_hex']))
        self.assertFalse(self.report['house_exterior']['save_profile_changed'])
        expected = bytearray(self.base)
        for vrom in (BLOB, MODULE, 0x7AC420, 0x8681F0, 0x8CB690):
            entry = self.files[vrom]
            self.assertEqual(entry.pstart, self.old[vrom].pstart)
            expected[entry.pstart:entry.pstart+entry.size] = entry.extract(self.rom)
        for vrom in (BLOB, 0x970920):
            at = DMA_START+self.files[vrom].index*16
            expected[at:at+16] = self.rom[at:at+16]
        expected[0x10:0x18] = self.rom[0x10:0x18]
        self.assertEqual(self.rom, expected)
        module = self.files[MODULE].extract(self.rom)
        old_module = bytearray(self.old[MODULE].extract(self.base))
        old_module[STARTUP:CONFIG+16] = module[STARTUP:CONFIG+16]
        self.assertEqual(module, old_module)
        self.assertEqual(struct.unpack_from('>4I', module, CONFIG),
                         (BLOB, 0xC000, zlib.crc32(blob[:0xC000]), 59))
        self.assertEqual(sha256(self.base), BASE_SHA)
        self.assertEqual(n64_checksum(self.rom), struct.unpack_from('>2I', self.rom, 0x10))
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native, (OUTPUT/'asset-loader.ups').read_bytes()), self.rom)


if __name__ == '__main__':
    unittest.main()
