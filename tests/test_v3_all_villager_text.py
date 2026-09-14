"""Complete donor text, native aliases, profile compatibility, and cartridge bounds."""
import ctypes as c
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
from aflib import CODE_VROM, apply_ups, by_vrom, n64_checksum, sha256
from v3_all_villager_text import (BASE, BASE_SHA, BLOB, CONFIG, MODULE, STARTUP,
                                compatibility_aliases, install_metadata)
from v3_villager_text import DATA, STRIDE, metadata, read_text_donor
from v3_import_catalog import read_donor
from tests.test_v3_save_clothing import fixture, reference_pack, PROFILE, STATE

OUTPUT = ROOT/'build/v3-all-villager-text-01'


@unittest.skipUnless((OUTPUT/'build.json').exists(), 'Current complete-text build required')
class CompleteText(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = (OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.base = (BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.report = json.loads((OUTPUT/'build.json').read_text())
        cls.previous = json.loads((BASE/'build.json').read_text())
        cls.files, cls.old = by_vrom(cls.rom), by_vrom(cls.base)
        cls.blob = cls.files[BLOB].extract(cls.rom)
        cls.data = cls.blob[DATA:DATA+20*STRIDE]
        cls.donor = read_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
        cls.first = read_text_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()

    def test_actual_twenty_text_rows_and_complete_source_reconstruction(self):
        blob, report, profile = install_metadata(self.base, self.previous, self.native,
                                                self.donor, self.first, self.symbols)
        self.assertEqual(blob, self.blob)
        # Execution evidence is added to the receipt after construction.
        self.assertEqual({k: v for k, v in report.items() if k != 'native_test'},
                         {k: v for k, v in self.report['villager_text'].items() if k != 'native_test'})
        self.assertEqual(profile.hex(), self.report['save_runtime']['profile_hex'])
        rows = report['imports']
        self.assertEqual(len(rows), 20)
        self.assertEqual({r['actor_id'] for r in rows}, {f'{0xE0DA+i:04X}' for i in range(20)})
        for i, row in enumerate(rows):
            data = self.data[i*32:(i+1)*32]
            self.assertEqual(data[8:16], row['name'].encode().ljust(8, b' '))
            self.assertEqual(data[16:26], row['catchphrase'].encode().ljust(10, b' '))
            self.assertEqual(sha256(data), row['record_sha256'])
            self.assertEqual(data[6], 0 if row['actor_id'] in ('E0EA', 'E0ED') else 2)
            if data[6] == 2:
                self.assertEqual(data[30:], bytes(2))
                self.assertFalse(row['initial_defaults_applied'])
        self.assertEqual([r['name'] for r in rows if len(r['name']) > 6], ['Flossie', 'Annalise'])
        self.assertEqual(next(r['catchphrase'] for r in rows if r['name']=='Plucky'), 'chicky poo')
        keys = {self.data[i*32+26:i*32+30] for i in range(20)}
        original_phrases = self.files[0x2E00000].extract(self.rom)
        original_keys = {original_phrases[i:i+4] for i in range(32, len(original_phrases), 16)}
        self.assertEqual(len(keys), 20)
        self.assertTrue(keys.isdisjoint(original_keys))
        self.assertEqual(self.blob[0x1E60:0x1E74], bytes(20))

    def test_pilot_data_retained_and_two_actual_aloha_shirts_remain_dependencies(self):
        pilot, _ = metadata(self.native, self.donor, self.first, self.symbols)
        for i in range(20):
            if i not in (16, 19): self.assertEqual(pilot[i*32:(i+1)*32], bytes(32))
        before = self.old[BLOB].extract(self.base)
        for i in (16, 19):
            self.assertEqual(self.data[i*32:(i+1)*32], before[DATA+i*32:DATA+(i+1)*32])
        islanders = [r for r in self.report['villager_text']['imports'] if r['donor_growth_permission']==2]
        self.assertEqual({r['donor_clothing_id'] for r in islanders}, {'241A', '241B'})
        for row in islanders:
            clothing = row['clothing_identity']
            self.assertIsNone(clothing['native_item_id'])
            self.assertEqual(clothing['native_candidates_checked'], 256)
            self.assertEqual(clothing['compared_pixels'], 1024)

    def test_actual_data_through_sanitized_text_and_mail_alias_readers(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-complete-text-') as directory:
            binary = Path(directory)/'test'
            subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_all_villager_text_test.c'), '-o', str(binary)],
                check=True, capture_output=True)
            creator = self.files[0x03200000].extract(self.rom)
            at = creator.index(b'AFNA')
            result = subprocess.run([str(binary)], input=self.data+creator[at:at+6368],
                                    check=True, capture_output=True, timeout=20)
            self.assertIn(b'All twenty actual names', result.stdout)

    def test_complete_aliases_are_unique_and_collisions_are_rejected(self):
        report = compatibility_aliases(self.base, self.data)
        self.assertEqual(report['native_alias_rows'], 394)
        self.assertEqual(report['collisions'], 0)
        changed = bytearray(self.data)
        changed[8:16] = b'Bob     '
        with self.assertRaisesRegex(ValueError, 'conflicts'):
            compatibility_aliases(self.base, bytes(changed))
        changed[8:16] = changed[40:48]
        with self.assertRaisesRegex(ValueError, 'conflicts'):
            compatibility_aliases(self.base, bytes(changed))

    def test_unchanged_codec_accepts_previous_subset_and_rejects_missing_text_profile(self):
        current = bytes.fromhex(self.report['save_runtime']['profile_hex'])
        previous = bytes.fromhex(self.previous['save_runtime']['profile_hex'])
        self.assertEqual(current[32:], previous[32:])
        self.assertEqual({i for i in range(256) if current[i//8] & 1 << (i&7)}, set(range(218, 238)))
        with tempfile.TemporaryDirectory(prefix='af-v3-text-save-') as directory:
            library = Path(directory)/'codec.so'
            subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
                '-DAF_V3_CLOTHING_PROFILE=1', str(ROOT/'overlays/v3/save_codec.c'), '-o', str(library)],
                check=True, capture_output=True)
            api = c.CDLL(str(library))
            api.af_v3_save_check.argtypes = (c.c_void_p, c.c_uint, c.c_void_p, c.c_void_p)
            api.af_v3_save_pack.argtypes = (c.c_void_p, c.c_uint, c.c_void_p)
            bank, _ = fixture()
            old = bytes(reference_pack(bank, previous+bytes(640)))
            out = c.create_string_buffer(b'!'*STATE, STATE)
            self.assertEqual(api.af_v3_save_check(c.create_string_buffer(old), len(old),
                c.create_string_buffer(current), out), 1)
            self.assertEqual(out.raw, current+bytes(640))
            packed = c.create_string_buffer(bytes(bank), len(bank))
            self.assertEqual(api.af_v3_save_pack(packed, len(bank), out), 1)
            self.assertEqual(packed.raw, reference_pack(bank, current+bytes(640)))
            untouched = c.create_string_buffer(b'!'*STATE, STATE)
            self.assertEqual(api.af_v3_save_check(packed, len(bank),
                c.create_string_buffer(previous), untouched), -7)
            self.assertEqual(untouched.raw, b'!'*STATE)
            before = packed.raw
            self.assertEqual(api.af_v3_save_check(packed, len(bank),
                c.create_string_buffer(current), untouched), 1)
            self.assertEqual(packed.raw, before)

    def test_only_metadata_profile_startup_and_checksums_change(self):
        expected = bytearray(self.old[BLOB].extract(self.base))
        for begin, end in ((4, 8), (0x20, 0xE0), (DATA, DATA+20*STRIDE)):
            expected[begin:end] = self.blob[begin:end]
        self.assertEqual(expected, self.blob)
        module = self.files[MODULE].extract(self.rom)
        expected_module = bytearray(self.old[MODULE].extract(self.base))
        expected_module[STARTUP:CONFIG+16] = module[STARTUP:CONFIG+16]
        self.assertEqual(expected_module, module)
        self.assertEqual(struct.unpack_from('>4I', module, CONFIG),
                         (BLOB, 0xC000, zlib.crc32(self.blob[:0xC000]), 54))
        self.assertEqual(self.old, self.files)
        expected_rom = bytearray(self.base)
        for vrom, data in ((BLOB, self.blob), (MODULE, module)):
            entry = self.files[vrom]
            expected_rom[entry.pstart:entry.pstart+entry.size] = data
        expected_rom[0x10:0x18] = self.rom[0x10:0x18]
        self.assertEqual(expected_rom, self.rom)
        self.assertEqual(sha256(self.base), BASE_SHA)
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])
        self.assertEqual(n64_checksum(self.rom), struct.unpack_from('>II', self.rom, 0x10))
        self.assertEqual(apply_ups(self.native, (OUTPUT/'asset-loader.ups').read_bytes()), self.rom)


if __name__ == '__main__': unittest.main()
