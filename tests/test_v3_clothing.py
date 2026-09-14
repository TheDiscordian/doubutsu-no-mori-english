"""Actual additive shirt artwork, bounded DMA, and current cartridge ownership."""
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
from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom, sha256, verified_rom
from v3_asset_loader import BLOB, CONFIG, MODULE, compose
from v3_clothing import ABI, DATA, ENTRY, END, SOURCE_SHA, convert
from v3_registry import clothing_slot

OUTPUT = ROOT/'build/v3-clothing-resources-01'


class Clothing(c.Structure):
    _fields_ = [('item', c.c_ushort), ('index', c.c_ushort), ('vrom', c.c_uint),
                ('price', c.c_ushort), ('enabled', c.c_ubyte), ('reserved', c.c_ubyte),
                ('name', c.c_ubyte*16), ('padding', c.c_uint)]


class ClothingLogic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='v3-clothing-')
        library = Path(cls.temp.name)/'clothing.so'
        fixture = r'''
struct Clothing { unsigned short item, index; unsigned int vrom;
unsigned short price; unsigned char enabled, reserved, name[16]; unsigned int padding; };
struct Clothing af_v3_clothing;
unsigned int calls, sources[2], sizes[2];
int fail;
int af_v3_clothing_dma(void *out, unsigned int vrom, unsigned int bytes) {
    unsigned char *p = out;
    if (calls >= 2) return -1;
    sources[calls] = vrom; sizes[calls++] = bytes;
    if (fail) return -1;
    for (unsigned int i=0; i<bytes; ++i) p[i] = (unsigned char)i;
    return 0;
}
'''
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
            str(ROOT/'overlays/v3/clothing.c'), '-x', 'c', '-', '-o', str(library)],
            input=fixture, text=True, capture_output=True, check=True)
        cls.api = c.CDLL(str(library))
        cls.api.af_v3_clothing_source.argtypes = [c.c_int, c.c_uint]
        cls.api.af_v3_clothing_source.restype = c.c_uint
        cls.api.af_v3_load_clothing.argtypes = [c.c_void_p, c.c_void_p, c.c_int]

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def setUp(self):
        self.row = Clothing.in_dll(self.api, 'af_v3_clothing')
        c.memset(c.addressof(self.row), 0, c.sizeof(self.row))
        self.row.item, self.row.index, self.row.vrom = clothing_slot(0x24BF)
        self.row.enabled = 1
        c.c_uint.in_dll(self.api, 'calls').value = 0
        c.c_int.in_dll(self.api, 'fail').value = 0

    def test_all_native_sources_and_distinct_additive_shirt(self):
        for i in range(256):
            self.assertEqual(self.api.af_v3_clothing_source(i, 0), 0xB68000+i*512)
            self.assertEqual(self.api.af_v3_clothing_source(i, 1), 0xB88000+i*32)
        self.assertEqual(self.api.af_v3_clothing_source(0x10BF, 0), 0x3F0F000)
        self.assertEqual(self.api.af_v3_clothing_source(0x10BF, 1), 0x3F0F200)
        for i in (-1, 256, 0xBF+256, 0x10BE, 0x10C0, 65535):
            self.assertEqual(self.api.af_v3_clothing_source(i, 0), 0)
        self.assertEqual(self.api.af_v3_clothing_source(0, 2), 0)

    def test_disabled_or_invalid_import_metadata_does_not_alias_native(self):
        for field, invalid in (('enabled', 0), ('enabled', 2), ('item', 0x24BF),
            ('index', 0xBF), ('vrom', 0x3F0F008), ('reserved', 1), ('padding', 1)):
            old = getattr(self.row, field)
            setattr(self.row, field, invalid)
            self.assertEqual(self.api.af_v3_clothing_source(0x10BF, 0), 0, field)
            self.assertEqual(self.api.af_v3_clothing_source(0xBF, 0), 0xB7FE00)
            setattr(self.row, field, old)

    def test_complete_bounded_transfers_null_and_failed_dma(self):
        texture, palette = (c.c_ubyte*528)(*([0xA5]*528)), (c.c_ubyte*48)(*([0xA5]*48))
        self.api.af_v3_load_clothing(c.byref(texture, 8), c.byref(palette, 8), 0x10BF)
        self.assertEqual(bytes(texture), bytes([0xA5]*8)+bytes(range(256))*2+bytes([0xA5]*8))
        self.assertEqual(bytes(palette), bytes([0xA5]*8)+bytes(range(32))+bytes([0xA5]*8))
        self.assertEqual(list((c.c_uint*2).in_dll(self.api, 'sources')), [0x3F0F000, 0x3F0F200])
        self.assertEqual(list((c.c_uint*2).in_dll(self.api, 'sizes')), [512, 32])
        c.c_uint.in_dll(self.api, 'calls').value = 0
        before = bytes(texture), bytes(palette)
        self.api.af_v3_load_clothing(None, palette, 0x10BF)
        self.api.af_v3_load_clothing(texture, None, 0x10BF)
        self.api.af_v3_load_clothing(texture, palette, 0x10C0)
        self.assertEqual(c.c_uint.in_dll(self.api, 'calls').value, 0)
        c.c_int.in_dll(self.api, 'fail').value = 1
        self.api.af_v3_load_clothing(texture, palette, 0x10BF)
        self.assertEqual(c.c_uint.in_dll(self.api, 'calls').value, 1)
        self.assertEqual((bytes(texture), bytes(palette)), before)


@unittest.skipUnless((OUTPUT/'build.json').exists(), 'Current clothing build required')
class ClothingCartridge(unittest.TestCase):
    def test_current_resource_metadata_shared_reader_and_preserved_content(self):
        report = json.loads((OUTPUT/'build.json').read_text())
        parent = json.loads((ROOT/'build/v3-npc-streaming-01/build.json').read_text())
        rom = (OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        files = by_vrom(rom)
        blob_file = files[BLOB].extract(rom)
        blob = bytearray(blob_file[:0xC000])
        self.assertEqual(sha256(rom), report['output_sha256'])
        self.assertEqual(struct.unpack_from('>4I', files[MODULE].extract(rom), CONFIG),
            (BLOB, len(blob), zlib.crc32(blob), ABI))
        self.assertEqual(struct.unpack_from('>HHI', blob, DATA), clothing_slot(0x24BF))
        row = report['clothing']['imports'][0]
        self.assertEqual(sha256(blob_file[0xF000:0xF220]), row['resource_sha256'])
        self.assertEqual(len(blob_file), 0xF220)
        code = bytearray(files[CODE_VROM].extract(rom))
        at = ENTRY-CODE_RAM
        self.assertEqual(code[at:at+8].hex(), report['clothing']['after'])
        code[at:at+8] = bytes.fromhex(report['clothing']['before'])
        self.assertEqual(sha256(code[at:END-CODE_RAM]), SOURCE_SHA)
        self.assertEqual(sha256(code), parent['changed_resources'][f'{CODE_VROM:08X}'])
        for vrom, digest in parent['changed_resources'].items():
            if int(vrom, 16) in (MODULE, CODE_VROM): continue
            actual = int(report['relocated_resources'].get(vrom, vrom), 16)
            self.assertEqual(sha256(files[actual].extract(rom)), digest, vrom)
        self.assertEqual(report['save_runtime']['profile_hex'], parent['save_runtime']['profile_hex'])
        self.assertFalse(report['clothing']['punchy_defaults_enabled'])
        self.assertFalse(row['playable'])
        native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
        base = (ROOT/'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        self.assertEqual(compose(native, base, {}, {}), base)
        self.assertEqual(apply_ups(native, (OUTPUT/'asset-loader.ups').read_bytes()), rom)


if __name__ == '__main__': unittest.main()
