"""Actual clothing stock list conversion, selected seasons, and installation."""
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
from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom, sha256
from v3_asset_loader import BLOB, MODULE, CONFIG
from v3_clothing_stock import ABI, VROM, TABLE, SIZE, APPENDED, CALL, DESCRIPTOR, goods

OUTPUT, PARENT = (ROOT/'build'/p for p in ('v3-clothing-stock-01', 'v3-clothing-shop-category-01'))


class ClothingStockLogic(unittest.TestCase):
    def test_sanitized_seasons_selection_and_native_fallbacks(self):
        with tempfile.TemporaryDirectory(prefix='v3-clothing-stock-') as directory:
            binary = Path(directory)/'test'
            subprocess.run(['cc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_clothing_stock_test.c'), '-o', str(binary)],
                capture_output=True, text=True, check=True)
            result = subprocess.run([str(binary)], capture_output=True, text=True, check=True, timeout=20)
            self.assertIn('one RNG draw, and native lists pass', result.stdout)


@unittest.skipUnless((OUTPUT/'build.json').exists(), 'Current clothing stock build required')
class ClothingStockCartridge(unittest.TestCase):
    def test_actual_stock_and_complete_retained_resources(self):
        report, parent = (json.loads((p/'build.json').read_text()) for p in (OUTPUT, PARENT))
        rom, old_rom = ((p/'animal-forest-v3-asset-loader.z64').read_bytes() for p in (OUTPUT, PARENT))
        files, originals = by_vrom(rom), by_vrom(old_rom)
        data, old = files[VROM].extract(rom), originals[VROM].extract(old_rom)
        self.assertEqual(len(data), 720)
        restored = bytearray(data[:SIZE]); restored[TABLE:TABLE+4] = old[TABLE:TABLE+4]
        self.assertEqual(restored, old)
        expanded = data[APPENDED:APPENDED+146]
        self.assertEqual(expanded[:64]+expanded[66:], old[:144])
        self.assertEqual(expanded[64:66], bytes.fromhex('34BF'))
        self.assertEqual(struct.unpack_from('>I', data, TABLE)[0], 0x6000230)
        self.assertEqual(data[APPENDED+146:], bytes(14))
        base = (ROOT/'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        self.assertEqual(goods(base, rel, symbols, report['clothing']['imports'])[0], data)
        with self.assertRaises(ValueError): goods(base, rel, symbols, [])
        code = bytearray(files[CODE_VROM].extract(rom)); before = originals[CODE_VROM].extract(old_rom)
        self.assertEqual(code[CALL-CODE_RAM+4:CALL-CODE_RAM+8], before[CALL-CODE_RAM+4:CALL-CODE_RAM+8])
        self.assertEqual(struct.unpack_from('>3I', code, DESCRIPTOR-CODE_RAM), (VROM, VROM+720, 0x60001F0))
        code[CALL-CODE_RAM:CALL-CODE_RAM+4] = before[CALL-CODE_RAM:CALL-CODE_RAM+4]
        code[DESCRIPTOR-CODE_RAM+4:DESCRIPTOR-CODE_RAM+8] = before[DESCRIPTOR-CODE_RAM+4:DESCRIPTOR-CODE_RAM+8]
        self.assertEqual(code, before)
        blob, old_blob = files[BLOB].extract(rom), originals[BLOB].extract(old_rom)
        start = report['asset']['symbols']['af_v3_clothing_stock_index']-0x80460000
        self.assertEqual(start, 0xDE4)
        # Appended code moves the existing DMA diagnostic string. Its one
        # address immediate changes; the complete retained code and string do not.
        self.assertEqual(old_blob[0xB54:0xB58], bytes.fromhex('24420DE4'))
        self.assertEqual(blob[0xB54:0xB58], bytes.fromhex('24420F68'))
        retained = bytearray(blob[0x100:start])
        retained[0xA54:0xA58] = old_blob[0xB54:0xB58]
        self.assertEqual(retained, old_blob[0x100:start])
        self.assertEqual(old_blob[start:0xDF0], b'V3 clothing\0')
        self.assertEqual(blob[0xF68:0xF74], old_blob[start:0xDF0])
        self.assertEqual(struct.unpack_from('>4I', files[MODULE].extract(rom), CONFIG),
                         (BLOB, 0xC000, zlib.crc32(blob[:0xC000]), ABI))
        restored = bytearray(blob); restored[4:8], restored[0x100:0x1000] = old_blob[4:8], old_blob[0x100:0x1000]
        self.assertEqual(restored, old_blob)
        self.assertEqual(set(files), set(originals))
        for vrom in files:
            self.assertEqual(files[vrom].index, originals[vrom].index)
            self.assertEqual(files[vrom].size, originals[vrom].size+(160 if vrom == VROM else 0))
            if vrom not in (BLOB, MODULE, CODE_VROM, VROM, 0x19D40):
                self.assertEqual(files[vrom].extract(rom), originals[vrom].extract(old_rom), f'{vrom:08X}')
        for key, value in parent['clothing'].items(): self.assertEqual(report['clothing'][key], value, key)
        self.assertEqual(sha256(rom), report['output_sha256'])
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native, (OUTPUT/'asset-loader.ups').read_bytes()), rom)


if __name__ == '__main__': unittest.main()
