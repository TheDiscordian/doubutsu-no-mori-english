"""Current fire-sound cartridge, physical bindings, complete retention, and RAM."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import v3_fire_sound_runtime as runtime
from aflib import CODE_RAM, CODE_VROM, DMA_START, DMA_END, by_vrom, sha256, n64_checksum, u32
from v3_asset_loader import BLOB
from v3_fire_audio import NATIVE_VROMS

OUTPUT = ROOT / 'build/v3-fire-sound-runtime-01'


class FireRuntime(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.base = (runtime.BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report = json.loads((OUTPUT / 'build.json').read_text())
        cls.prior = json.loads((runtime.BASE / 'build.json').read_text())
        cls.sound = cls.report['fire_sound']
        cls.files, cls.old = by_vrom(cls.rom), by_vrom(cls.base)
        cls.code = cls.files[CODE_VROM].extract(cls.rom)
        cls.old_code = cls.old[CODE_VROM].extract(cls.base)

    def test_only_explicit_code_and_header_fields_change(self):
        restored = bytearray(self.code)
        for row in self.sound['code_patches']:
            at = row['address'] - CODE_RAM
            before, after = bytes.fromhex(row['before']), bytes.fromhex(row['after'])
            self.assertEqual(self.old_code[at:at + len(before)], before)
            self.assertEqual(self.code[at:at + len(after)], after)
            restored[at:at + len(before)] = before
        self.assertEqual(restored, self.old_code)
        self.assertEqual(self.report['runtime_abi'], 69)
        for key in ('save_runtime', 'catalogue', 'furniture', 'import_storage', 'tent_model', 'startup'):
            self.assertEqual(self.report[key], self.prior[key], key)
        self.assertEqual(self.code[0xEA944 + 0x80000000 - CODE_RAM:0xEA950 + 0x80000000 - CODE_RAM],
                         bytes.fromhex('8CD800100305C821ACD90010'))

    def test_whole_wave_file_retention_and_unsigned_external_binding(self):
        old_file = self.old[NATIVE_VROMS['wave']].extract(self.base)
        new_file = self.files[NATIVE_VROMS['wave']].extract(self.rom)
        self.assertEqual(new_file[:len(old_file)], old_file)
        self.assertEqual(len(new_file) - len(old_file), 21360)
        self.assertEqual(self.files[NATIVE_VROMS['wave']].pstart, 0x03800000)
        self.assertEqual(sha256(new_file), self.sound['wave_file']['sha256'])
        for row in self.sound['wave_headers']:
            header = self.code[row['address'] - CODE_RAM:row['address'] - CODE_RAM + 16]
            self.assertEqual(header.hex(), row['after'])
            self.assertEqual((u32(header, 0) + 0x03800000) & 0xFFFFFFFF, row['physical'])
            if row['index'] == 2:
                self.assertGreater(u32(header, 0), 0x80000000)
                self.assertEqual(row['physical'], row['physical_before'])
            else:
                self.assertEqual(header[:4], bytes.fromhex(row['before'])[:4])
            if row['index'] != 5:
                self.assertEqual(self.rom[row['physical']:row['physical'] + row['bytes']],
                                 self.base[row['physical_before']:row['physical_before'] + row['bytes']])
        old_start = self.sound['wave_file']['old_physical']
        self.assertEqual(self.rom[old_start:old_start + len(old_file)], old_file)

    def test_actual_allocations_grow_together_without_reducing_session_capacity(self):
        actual = struct.unpack_from('>3I', self.code, 0x80119A44 - CODE_RAM)
        self.assertEqual(actual, (0x47E00, 0x1DC00, 0x1AC00))
        for at, word in ((0x800D28D8, 0x34847E00), (0x800D28F8, 0x34A57E00)):
            self.assertEqual(u32(self.code, at - CODE_RAM), word)
        self.assertEqual(actual[0] - actual[1], 0x47A00 - 0x1D800)
        self.assertEqual(actual[1] - actual[2], 0x1D800 - 0x1A800)
        budget = self.sound['after_budget']
        self.assertEqual(budget['conservative_required'], 109312)
        self.assertEqual(budget['conservative_spare'], 256)
        self.assertEqual(budget['audio_heap_growth'], 1024)

    def test_complete_converted_resources_match_actual_native_headers(self):
        for kind, row in self.sound['resources'].items():
            payload = self.rom[row['physical']:row['physical'] + row['bytes']]
            self.assertEqual(payload, (runtime.AUDIO / f'fire.{kind}.bin').read_bytes())
            self.assertEqual(sha256(payload), row['sha256'])
            if kind in ('bank', 'seq'):
                entry = self.files[BLOB]
                self.assertEqual(row['physical'], entry.pstart + row['blob_offset'])
                offset = u32(self.code, row['header_address'] - CODE_RAM)
                self.assertEqual(offset + self.files[NATIVE_VROMS[kind]].pstart, row['physical'])
        self.assertEqual(self.sound['sound_ids'], {'bonfire': 92, 'campfire': 93})
        self.assertFalse(self.sound['furniture_callbacks_installed'])
        self.assertFalse(self.sound['web_patcher_changed'])

    def test_directory_and_every_other_resource_retained(self):
        self.assertEqual(set(self.files), set(self.old))
        self.assertEqual(len(self.files), 3389)
        self.assertEqual(self.rom[DMA_END - 16:DMA_END], bytes(16))
        changed = {CODE_VROM, BLOB, NATIVE_VROMS['wave']}
        for v, entry in self.files.items():
            if v not in changed:
                self.assertEqual(entry, self.old[v])
                expected = bytearray(self.old[v].extract(self.base))
                if not entry.pend and entry.pstart <= DMA_START < DMA_END <= entry.pstart + entry.size:
                    # This native resource contains the two deliberately updated
                    # directory rows; all its other data stays intact.
                    expected[DMA_START - entry.pstart:DMA_END - entry.pstart] = self.rom[DMA_START:DMA_END]
                self.assertEqual(entry.extract(self.rom), expected, f'{v:08X}')
        old_blob = self.old[BLOB].extract(self.base)
        blob = self.files[BLOB].extract(self.rom)
        self.assertEqual(blob[:len(old_blob)], old_blob)
        self.assertEqual(len(blob) - len(old_blob), 31456)
        self.assertEqual(sha256(blob), self.report['blob_sha256'])
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])
        self.assertEqual(struct.unpack_from('>II', self.rom, 16), n64_checksum(self.rom))
        restored = bytearray(self.rom)
        restored[16:24] = self.base[16:24]
        restored[DMA_START:DMA_END] = self.base[DMA_START:DMA_END]
        for at, size in ((self.files[CODE_VROM].pstart, len(self.code)),
                (self.files[BLOB].pstart, len(blob)),
                (self.files[NATIVE_VROMS['wave']].pstart, self.files[NATIVE_VROMS['wave']].size)):
            restored[at:at + size] = self.base[at:at + size]
        self.assertEqual(restored, self.base)


if __name__ == '__main__':
    unittest.main()
