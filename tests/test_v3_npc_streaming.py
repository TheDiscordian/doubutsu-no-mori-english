"""The actual NPC reserved-bank loaders use the expanded table without arena changes."""
import json
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom, sha256, verified_rom
from npc_mail_show import relocate_verified_data
from v3_asset_loader import BLOB, CONFIG, MODULE, compose
from v3_npc_draw import OWNERS, STREAMING, STREAMING_ABI, patch_streaming

OUTPUT = ROOT/'build/v3-npc-streaming-01'


class StreamingGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
        cls.files = by_vrom(cls.native)

    def test_both_complete_functions_change_only_the_table_address(self):
        for vrom, rel, ram, *_ in OWNERS:
            before = self.files[vrom].extract(self.native)
            data = bytearray(before)
            reloc = self.files[rel].extract(self.native)
            row = patch_streaming(data, reloc, vrom, ram)
            at = STREAMING[vrom][2]-ram
            self.assertEqual(data[:at], before[:at])
            self.assertEqual(data[at+8:], before[at+8:])
            self.assertEqual(data[at:at+8].hex(), '3c0f804625ef1000')
            sections = struct.unpack_from('>5I', reloc)
            spec = SimpleNamespace(ram=ram, resident_bytes=len(data)+sections[3], sections=sections)
            constants = (0x80969690 if vrom == 0x8681F0 else 0x80989060, ram+spec.resident_bytes)
            moved = relocate_verified_data(spec, bytes(data), reloc, 0x802DC000, address_constants=constants)
            self.assertEqual(moved[at:at+8], data[at:at+8])
            self.assertTrue(row['allocation_and_dma_unchanged'])

    def test_unknown_function_or_relocation_is_rejected_before_writing(self):
        for vrom, rel, ram, *_ in OWNERS:
            data = bytearray(self.files[vrom].extract(self.native))
            reloc = self.files[rel].extract(self.native)
            data[STREAMING[vrom][0]-ram] ^= 1
            before = bytes(data)
            with self.assertRaisesRegex(ValueError, 'Changed native NPC streaming'):
                patch_streaming(data, reloc, vrom, ram)
            self.assertEqual(data, before)
            data = bytearray(self.files[vrom].extract(self.native))
            changed_rel = bytearray(reloc)
            struct.pack_into('>I', changed_rel, 20, 0x45000000 | (STREAMING[vrom][2]-ram))
            before = bytes(data)
            with self.assertRaises(ValueError):
                patch_streaming(data, bytes(changed_rel), vrom, ram)
            self.assertEqual(data, before)


@unittest.skipUnless((OUTPUT/'build.json').exists(), 'Current streaming build required')
class StreamingCartridge(unittest.TestCase):
    def test_current_cartridge_tables_config_and_unchanged_dependencies(self):
        report = json.loads((OUTPUT/'build.json').read_text())
        parent = json.loads((ROOT/'build/v3-villager-rewards-01/build.json').read_text())
        rom = (OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        files = by_vrom(rom)
        self.assertEqual(sha256(rom), report['output_sha256'])
        blob = bytearray(files[BLOB].extract(rom)[:0xC000])
        self.assertEqual(struct.unpack_from('>4I', files[MODULE].extract(rom), CONFIG),
                         (BLOB, len(blob), zlib.crc32(blob), STREAMING_ABI))
        self.assertEqual(struct.unpack_from('>I', blob, 4)[0], STREAMING_ABI)
        for bank, vrom in ((426, 0x3F30000), (429, 0x3F36000)):
            self.assertEqual(struct.unpack_from('>II', blob, 0x1000+bank*8), (vrom, vrom+0x1620))
        struct.pack_into('>I', blob, 4, 26)
        self.assertEqual(sha256(blob), parent['blob_sha256'])
        for vrom, digest in parent['changed_resources'].items():
            v = int(vrom, 16)
            if v == MODULE: continue
            actual = int(report['relocated_resources'].get(vrom, vrom), 16)
            data = bytearray(files[actual].extract(rom))
            if v in STREAMING:
                ram = next(row[2] for row in OWNERS if row[0] == v)
                at = STREAMING[v][2]-ram
                self.assertEqual(data[at:at+8].hex(), '3c0f804625ef1000')
                data[at:at+8] = bytes.fromhex('3c0f801125efddd0')
            self.assertEqual(sha256(data), digest, vrom)
        native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
        base = (ROOT/'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        native_table = by_vrom(base)[CODE_VROM].extract(base)
        at = 0x8010DDD0-CODE_RAM
        self.assertEqual(blob[0x1000:0x1000+410*8], native_table[at:at+410*8])
        self.assertEqual(compose(native, base, {}, {}), base)
        self.assertEqual(apply_ups(native, (OUTPUT/'asset-loader.ups').read_bytes()), rom)
        self.assertFalse(report['new_villager_ids_enabled'])


if __name__ == '__main__': unittest.main()
