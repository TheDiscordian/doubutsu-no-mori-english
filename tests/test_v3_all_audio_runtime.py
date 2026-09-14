"""Installed all-villager audio, direct cartridge addresses, and resource bounds."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, DMA_START, apply_ups, by_vrom, n64_checksum, sha256
from v3_all_audio_runtime import (BASE, BASE_SHA, BLOB, BLOB_RAM, CONFIG, MELODY_START,
    MELODY_END, MODULE, PACKAGE_BYTES, PACKAGE_RAM, PACKAGE_VROM, RESIDENT, TABLE, load_audio)
from v3_speed_bag_sound_runtime import permanent_budget

OUTPUT = ROOT/'build/v3-all-audio-runtime-01'


class HostRuntime(unittest.TestCase):
    def test_expanded_melody_range_with_native_protocol_and_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-all-melody-') as temp:
            binary = Path(temp)/'check'
            subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                f'-DAF_V3_MELODY_BEGIN={MELODY_START}u', f'-DAF_V3_MELODY_END={MELODY_END}u',
                str(ROOT/'tests/v3_melody_test.c'), '-o', str(binary)], check=True, capture_output=True)
            result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=20)
            self.assertIn('guards pass', result.stdout)


@unittest.skipUnless((OUTPUT/'build.json').exists(), 'Current complete audio cartridge required')
class Cartridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = (BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.rom = (OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report = json.loads((OUTPUT/'build.json').read_text())
        cls.before, cls.files = by_vrom(cls.base), by_vrom(cls.rom)
        cls.blob = cls.files[BLOB].extract(cls.rom)
        cls.code = cls.files[CODE_VROM].extract(cls.rom)
        cls.audio, cls.resources = load_audio()

    def test_complete_melodies_resident_package_and_startup_descriptor(self):
        imports = {r['voice']: r for r in self.report['villager_audio']['imports']}
        self.assertEqual(set(imports), set(range(260, 278)) | {285, 286})
        package_offset = PACKAGE_VROM-BLOB
        package = self.blob[package_offset:package_offset+PACKAGE_BYTES]
        for row in self.audio['villagers']:
            source, size = struct.unpack_from('>II', self.blob, TABLE+8*(row['voice']-256))
            self.assertEqual(source, int(imports[row['voice']]['ram'], 16))
            self.assertTrue(MELODY_START <= source <= MELODY_END-size)
            self.assertEqual(package[source-PACKAGE_RAM:source-PACKAGE_RAM+size], self.resources[row['file']])
        for voice in set(range(256, 299))-set(imports):
            self.assertEqual(self.blob[TABLE+8*(voice-256):TABLE+8*(voice-255)], bytes(8))
        self.assertEqual(struct.unpack_from('>4I', self.blob, 0xF0),
                         (PACKAGE_VROM, PACKAGE_BYTES, zlib.crc32(package), PACKAGE_RAM))
        self.assertEqual(package[-16:], bytes.fromhex('AFACC0DE')*4)
        module = self.files[MODULE].extract(self.rom)
        self.assertEqual(struct.unpack_from('>4I', module, CONFIG), (BLOB, RESIDENT, zlib.crc32(self.blob[:RESIDENT]), 53))
        old = self.before[BLOB].extract(self.base)
        self.assertEqual(package[0x100:0x500], old[package_offset+0x100:package_offset+0x500])
        self.assertEqual(package[0x1000:0xC000], old[package_offset+0x1000:])
        prefix = bytearray(old[:RESIDENT])
        for at, end in ((4, 8), (0xF0, 0x100), (TABLE, TABLE+43*8)):
            prefix[at:end] = self.blob[at:end]
        self.assertEqual(prefix, self.blob[:RESIDENT])

    def test_streamed_assets_actual_header_addresses_and_complete_audio_budget(self):
        complete = self.report['complete_villager_audio']
        for kind, resource in (('bank', 'font'), ('wave', 'wave')):
            row = complete['files'][kind]
            physical, size = row['physical_rom'], row['bytes']
            self.assertEqual(self.rom[physical:physical+size], self.resources[resource])
            self.assertEqual(row['initializer_base']+row['source_offset'], physical)
            self.assertEqual(physical, self.files[BLOB].pstart+row['blob_offset'])
            at = row['header_address']-CODE_RAM
            self.assertEqual(self.code[at:at+16].hex(), row['header_after'])
        self.assertEqual(permanent_budget(self.code), complete['after_budget'])
        self.assertEqual(complete['after_budget']['conservative_spare'], 32)
        self.assertEqual(complete['after_budget']['audio_heap_growth'], 0)

    def test_only_required_native_hooks_headers_and_physical_resource_spans_change(self):
        expected_code = bytearray(self.before[CODE_VROM].extract(self.base))
        for row in self.report['complete_villager_audio']['files'].values():
            at = row['header_address']-CODE_RAM
            expected_code[at:at+16] = bytes.fromhex(row['header_after'])
        for address, name in ((0x800FCEEC, 'af_v3_melody_start'), (0x800FD0D4, 'af_v3_melody_count')):
            target = self.report['complete_villager_audio']['code']['symbols'][name]
            struct.pack_into('>II', expected_code, address-CODE_RAM, 0x08000000 | (target >> 2 & 0x3FFFFFF), 0)
        self.assertEqual(expected_code, self.code)
        self.assertEqual(set(self.before), set(self.files))
        expected = bytearray(self.base)
        for vrom in (MODULE, CODE_VROM, BLOB):
            row = self.files[vrom]
            self.assertEqual(row.pstart, self.before[vrom].pstart)
            expected[row.pstart:row.pstart+row.size] = row.extract(self.rom)
        at = DMA_START+self.files[BLOB].index*16
        expected[at:at+16] = self.rom[at:at+16]
        expected[0x10:0x18] = self.rom[0x10:0x18]
        self.assertEqual(expected, self.rom)
        for vrom in (0x01920000, 0x019F0000, 0x01A50000):
            self.assertEqual(self.files[vrom], self.before[vrom])
            self.assertEqual(self.files[vrom].extract(self.rom), self.before[vrom].extract(self.base))

    def test_checksums_and_complete_patch_reconstruction(self):
        self.assertEqual(sha256(self.base), BASE_SHA)
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])
        self.assertEqual(len(self.rom), 32*1024*1024)
        self.assertEqual(n64_checksum(self.rom), struct.unpack_from('>II', self.rom, 0x10))
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native, (OUTPUT/'asset-loader.ups').read_bytes()), self.rom)


if __name__ == '__main__': unittest.main()
