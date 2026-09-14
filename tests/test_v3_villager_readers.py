"""Focused complete imported-name capture and current cartridge integration."""
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
sys.path.insert(0, str(ROOT / 'tools'))
from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom, sha256
from v3_asset_loader import BLOB, CONFIG, MODULE, compose
import v3_villager_readers as readers

OUTPUT = ROOT / 'build/v3-villager-readers-01'


class Sources(c.Structure):
    _fields_ = [('words', c.c_void_p), ('aliases', c.c_void_p), ('ready', c.c_uint)]


class ReaderLogicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = '''
unsigned int enabled = 1, duplicate = 0;
int af_v3_reader_name(unsigned char *out, unsigned int size, unsigned int npc) {
    const unsigned char *name; unsigned int i;
    if (!enabled || size < 8 || (npc != 0xe0ea && npc != 0xe0ed)) return 0;
    name = (const unsigned char *)(npc == 0xe0ea || duplicate ? "Cheri   " : "Punchy  ");
    for (i = 0; i < 8; ++i) out[i] = name[i];
    return 1;
}
'''
        cls.temp = tempfile.TemporaryDirectory(prefix='v3-villager-readers-')
        library = Path(cls.temp.name) / 'readers.so'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
                        str(ROOT / 'overlays/v3/villager_readers.c'), '-x', 'c', '-', '-o', str(library)],
                       input=fixture, text=True, capture_output=True, check=True)
        cls.api = c.CDLL(str(library))
        cls.api.af_v3_mail_source_name.argtypes = [c.c_void_p, c.POINTER(Sources), c.c_uint]
        cls.api.af_v3_mail_source_alias.argtypes = [c.c_void_p, c.POINTER(Sources), c.c_void_p]
        cls.native = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        creator = by_vrom(cls.native)[readers.CREATOR].extract(cls.native)
        cls.alias_data = creator[0xCA40:0xCA40+6368]
        cls.word_data = creator[0x9E00:0x9E00+11328]

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.words, self.aliases = c.create_string_buffer(self.word_data), c.create_string_buffer(self.alias_data)
        self.sources = Sources(c.addressof(self.words), c.addressof(self.aliases), 0x41464353)
        c.c_uint.in_dll(self.api, 'enabled').value = 1
        c.c_uint.in_dll(self.api, 'duplicate').value = 0

    def invoke(self, value, expected=None, alias=False, sources=None):
        out = c.create_string_buffer(b'!' * 50, 50)
        fn = self.api.af_v3_mail_source_alias if alias else self.api.af_v3_mail_source_name
        supplied = c.create_string_buffer(value) if alias else value
        result = fn(c.addressof(out)+16, c.byref(sources or self.sources), supplied)
        self.assertEqual(result, int(expected is not None))
        self.assertEqual(out.raw, b'!'*16 + (b'\x08\0'+expected+bytes(8) if expected else b'!'*18) + b'!'*16)

    def test_native_and_imported_complete_fields(self):
        for npc, text in ((0xE0EA, b'Cheri   '), (0xE0ED, b'Punchy  ')):
            self.invoke(npc, text)
            self.invoke(text[:6], text, alias=True)
        row = self.alias_data[64:80]
        self.invoke(0xE000+struct.unpack_from('>H', row, 6)[0], row[8:])
        self.invoke(row[:6], row[8:], alias=True)

    def test_disabled_unknown_test_and_ambiguous_are_no_write(self):
        for npc in (0, 0xD000, 0xE0D8, 0xE0D9, 0xE0DA, 0xE0EE, 0xFFFFFFFF):
            self.invoke(npc)
        self.invoke(b'Absent', alias=True)
        c.c_uint.in_dll(self.api, 'enabled').value = 0
        self.invoke(0xE0EA)
        self.invoke(b'Cheri ', alias=True)
        c.c_uint.in_dll(self.api, 'enabled').value = 1
        c.c_uint.in_dll(self.api, 'duplicate').value = 1
        self.invoke(b'Cheri ', alias=True)

    def test_source_guards_and_original_alias_precedence(self):
        self.sources.ready = 0
        self.invoke(0xE0EA)
        self.sources.ready = 0x41464353
        for address in (c.addressof(self.sources), c.addressof(self.words)+1, c.addressof(self.aliases)+3):
            before = c.string_at(address, 18)
            self.assertEqual(self.api.af_v3_mail_source_name(address, c.byref(self.sources), 0xE0EA), 0)
            self.assertEqual(c.string_at(address, 18), before)
        self.assertEqual(self.api.af_v3_mail_source_name(None, c.byref(self.sources), 0xE0EA), 0)
        self.assertEqual(self.api.af_v3_mail_source_name(c.addressof(self.words), None, 0xE0EA), 0)
        # A native alias always takes precedence over added spelling candidates.
        rows = [self.alias_data[at:at+16] for at in range(64, 6368, 16)]
        rows[0] = b'Cheri '+rows[0][6:8]+b'Native  '
        rows.sort(key=lambda row: row[:6])
        self.aliases = c.create_string_buffer(self.alias_data[:64]+b''.join(rows))
        self.sources.aliases = c.addressof(self.aliases)
        self.invoke(b'Cheri ', b'Native  ', alias=True)


@unittest.skipUnless((OUTPUT / 'build.json').exists(), 'Current reader cartridge required')
class ReaderCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUTPUT / 'build.json').read_text())
        cls.readers = cls.report['villager_readers']
        cls.rom = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.base = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        cls.files = by_vrom(cls.rom)
        cls.parent = json.loads((ROOT / 'build/v3-house-layout-01/build.json').read_text())

    def test_exact_owner_edits_and_retained_relocations(self):
        original = by_vrom(self.base)
        for row in self.readers['owners']:
            vrom = int(row['vrom'], 16)
            data = bytearray(self.files[vrom].extract(self.rom))
            self.assertEqual(sha256(data), row['output_sha256'])
            for patch in row['patches']:
                at, before, after = patch['offset'], bytes.fromhex(patch['before']), bytes.fromhex(patch['after'])
                self.assertEqual(data[at:at+len(after)], after)
                data[at:at+len(before)] = before
            self.assertEqual(sha256(data), row['input_sha256'])
            relocation = row['relocation']
            if relocation > len(data):
                self.assertEqual(self.files[relocation].extract(self.rom), original[relocation].extract(self.base))
            else:
                self.assertEqual(data[relocation:], original[vrom].extract(self.base)[relocation:])

    def test_crcs_bounds_and_retained_foundation(self):
        blob = self.files[BLOB].extract(self.rom)[:0xC000]
        code = (OUTPUT / 'villager_readers/code.bin').read_bytes()
        self.assertEqual(blob[readers.CODE:readers.CODE+len(code)], code)
        self.assertLessEqual(len(code), readers.LIMIT-readers.CODE)
        module = self.files[MODULE].extract(self.rom)
        self.assertEqual(struct.unpack_from('>4I', module, CONFIG), (BLOB, 0xC000, zlib.crc32(blob), readers.ABI))
        self.assertEqual(struct.unpack_from('>I', module, 0x60)[0], zlib.crc32(self.files[readers.CREATOR].extract(self.rom)))
        main = self.files[CODE_VROM].extract(self.rom)
        high, low = struct.unpack_from('>II', main, 0x8009D758-CODE_RAM)
        actual = ((high & 0xFFFF) << 16) + struct.unpack('>h', struct.pack('>H', low & 0xFFFF))[0]
        self.assertEqual(actual & 0xFFFFFFFF, zlib.crc32(self.files[readers.TEXT].extract(self.rom)))
        previous_blob = bytearray(blob)
        previous_blob[readers.CODE:readers.CODE+len(code)] = bytes(len(code))
        struct.pack_into('>I', previous_blob, 4, 23)
        self.assertEqual(sha256(previous_blob), self.parent['blob_sha256'])
        changed = {CODE_VROM, MODULE, *readers.OWNERS}
        for v, digest in self.parent['changed_resources'].items():
            if int(v, 16) in changed: continue
            actual = int(self.report['relocated_resources'].get(v, v), 16)
            self.assertEqual(sha256(self.files[actual].extract(self.rom)), digest)
        self.assertFalse(self.report['new_villager_ids_enabled'])

    def test_patch_composition_and_import_free_v2(self):
        native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        moved = {int(v, 16): int(t, 16) for v, t in self.report['relocated_resources'].items()}
        changes = {int(v, 16): self.files[moved.get(int(v, 16), int(v, 16))].extract(self.rom)
                   for v in self.report['changed_resources']}
        added = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['added_resources']}
        self.assertEqual(compose(native, self.base, changes, added,
                                 resized=tuple(int(v, 16) for v in self.report['resized_resources']), relocated=moved), self.rom)
        self.assertEqual(compose(native, self.base, {}, {}), self.base)
        self.assertEqual(apply_ups(native, (OUTPUT / 'asset-loader.ups').read_bytes()), self.rom)


if __name__ == '__main__':
    unittest.main()
