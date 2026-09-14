"""Actual all-villager draw integration and bounded attachment behaviour."""
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
from aflib import DMA_START, apply_ups, by_vrom, n64_checksum, sha256
from v3_accessory_runtime import (ABI, ART, BASE, BASE_SHA, BLOB, CONFIG, DRAW_OFFSET,
    GUARD, MAGIC, MODULE, OWNERS, PACKAGE_RAM, PACKAGE_SIZE, PACKAGE_VROM, RESIDENT,
    STRIDE, package_art, patch_owners, prepare_rows)
from v3_villager_assets_runtime import load_art

OUTPUT = ROOT/'build/v3-accessory-runtime-01'


class HostAttachment(unittest.TestCase):
    def run_host(self, source, extra, expected):
        with tempfile.TemporaryDirectory(prefix='af-v3-accessory-') as temp:
            executable = Path(temp)/'check'
            subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT/'tests'/source), *extra, '-o', str(executable)], check=True, capture_output=True)
            result = subprocess.run([str(executable)], check=True, capture_output=True, text=True, timeout=20)
            self.assertIn(expected, result.stdout)

    def test_matrix_scale_callbacks_lifetime_and_buffer_limits(self):
        self.run_host('v3_accessory_test.c', [], 'state restoration pass')

    def test_package_startup_and_rejection_before_execution(self):
        self.run_host('v3_accessory_startup_test.c', [str(ROOT/'runtime/crc32.c')], 'low-memory path pass')


@unittest.skipUnless((OUTPUT/'build.json').exists(), 'Current accessory runtime build required')
class ActualCartridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = (BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.rom = (OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report = json.loads((OUTPUT/'build.json').read_text())
        cls.old, cls.files = by_vrom(cls.base), by_vrom(cls.rom)
        cls.blob = cls.files[BLOB].extract(cls.rom)
        cls.package = cls.blob[PACKAGE_VROM-BLOB:PACKAGE_VROM-BLOB+PACKAGE_SIZE]
        cls.records, cls.resources = load_art(ART)

    def test_actual_assets_bind_the_fixed_actor_joint_and_shared_storage(self):
        self.assertEqual(struct.unpack_from('>4I', self.package), (MAGIC, 1, PACKAGE_SIZE, 20))
        self.assertEqual(self.package[-16:], struct.pack('>4I', GUARD, GUARD, GUARD, GUARD))
        self.assertEqual(sha256(self.package), self.report['accessory_runtime']['package_sha256'])
        installed = self.report['accessory_runtime']['imports']
        self.assertEqual(len(installed), 16)
        for row in installed:
            actor = int(row['actor_id'], 16)
            at = 0x1000+(actor-0xE0DA)*16
            self.assertEqual(struct.unpack_from('>HHIIBBH', self.package, at),
                (actor, row['bank'], int(row['resident_address'], 16),
                 int(row['display_list'], 16), row['joint'], 1, row['bytes']))
            off = int(row['resident_address'], 16)-PACKAGE_RAM
            self.assertEqual(self.package[off:off+row['bytes']], self.resources[row['bank']])
        code = (OUTPUT/'accessory/code.bin').read_bytes()
        package, _ = package_art(code, self.records, self.resources)
        self.assertEqual(package, self.package)
        with self.assertRaises(ValueError): package_art(bytes(0xF04), self.records, self.resources)

    def test_all_draw_rows_keep_donor_flags_models_skeletons_and_complete_voice_ids(self):
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        manifest = json.loads((ART/'art.json').read_text())
        draw, expected = prepare_rows(native, rel, symbols, manifest, self.records)
        self.assertEqual(self.blob[DRAW_OFFSET:DRAW_OFFSET+20*STRIDE], draw)
        self.assertEqual(self.report['npc_draw']['imports'], expected)
        original = self.old[BLOB].extract(self.base)
        for slot in (16, 19):
            at = DRAW_OFFSET+slot*STRIDE
            self.assertEqual(self.blob[at:at+STRIDE], original[at:at+STRIDE])
        yodel = next(r for r in expected if r['name'] == 'Yodel')
        self.assertEqual((yodel['model_bank'], yodel['skeleton'], yodel['accessory_bank']), (431, '06002770', 433))
        self.assertTrue(all(not r['move_in_enabled'] for r in expected))
        self.assertEqual(self.blob[0x1E60:0x1E74], bytes(20))

    def test_two_installed_calls_retain_all_overlay_relocations_and_native_callbacks(self):
        target = self.report['accessory_runtime']['code']['symbols']['af_v3_accessory_draw']
        changes, _ = patch_owners(self.base, target)
        for vrom, reloc, ram, start, end, call, _, _ in OWNERS:
            old, new = self.old[vrom].extract(self.base), self.files[vrom].extract(self.rom)
            self.assertEqual(new, changes[vrom])
            self.assertEqual(old[:call-ram], new[:call-ram])
            self.assertEqual(old[call-ram+4:], new[call-ram+4:])
            self.assertEqual(self.old[reloc].extract(self.base), self.files[reloc].extract(self.rom))
        self.assertEqual(self.report['accessory_runtime']['per_actor_allocation_bytes'], 0)

    def test_cartridge_memory_profile_and_audio_locations_are_preserved(self):
        self.assertEqual(len(self.rom), 32*1024*1024)
        self.assertEqual(set(self.old), set(self.files))
        expected = bytearray(self.base)
        for v in (MODULE, 0x8681F0, 0x8798C0):
            e = self.files[v]; self.assertEqual(e, self.old[v])
            expected[e.pstart:e.pstart+e.size] = e.extract(self.rom)
        entry = self.files[BLOB]
        expected[entry.pstart:entry.pstart+entry.size] = self.blob
        row = DMA_START+16*entry.index
        expected[row:row+16] = self.rom[row:row+16]
        expected[0x10:0x18] = self.rom[0x10:0x18]
        self.assertEqual(expected, self.rom)
        before = bytearray(self.old[BLOB].extract(self.base))
        after = self.blob[:len(before)]
        for start, end in ((4, 8), (0xF0, 0x100), (DRAW_OFFSET, DRAW_OFFSET+20*STRIDE)):
            before[start:end] = after[start:end]
        self.assertEqual(before, after)
        self.assertEqual(struct.unpack_from('>4I', self.blob, 0xF0),
                         (PACKAGE_VROM, PACKAGE_SIZE, zlib.crc32(self.package), PACKAGE_RAM))
        module = self.files[MODULE].extract(self.rom)
        self.assertEqual(struct.unpack_from('>4I', module, CONFIG),
                         (BLOB, RESIDENT, zlib.crc32(self.blob[:RESIDENT]), ABI))

    def test_source_identity_and_complete_patch_reconstruction(self):
        self.assertEqual(sha256(self.base), BASE_SHA)
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])
        self.assertEqual(n64_checksum(self.rom), struct.unpack_from('>2I', self.rom, 0x10))
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native, (OUTPUT/'asset-loader.ups').read_bytes()), self.rom)


if __name__ == '__main__':
    unittest.main()
