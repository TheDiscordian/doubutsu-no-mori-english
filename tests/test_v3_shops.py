"""Imported ordinary goods retain complete native lists and rarity logic."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom, sha256
from v3_asset_loader import BLOB, compose
from v3_shops import BRIDGE, CODE, DESCRIPTOR, END, ENTRY, LIMIT, TABLE, VROM, goods

OUTPUT = ROOT / 'build/v3-shops-01'


def lists(data, table):
    output = []
    for pointer in struct.unpack_from('>12I', data, table):
        if not pointer:
            output.append(None)
            continue
        at, row = pointer & 0xFFFFFF, []
        while at + 2 <= table:
            item = struct.unpack_from('>H', data, at)[0]
            if item == 0:
                break
            row.append(item); at += 2
        else:
            raise ValueError('Unterminated goods list')
        output.append(row)
    return output


class ShopsHostTests(unittest.TestCase):
    def test_sanitized_category_contract(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-shops-test-') as directory:
            binary = Path(directory) / 'test'
            subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT / 'tests/v3_shops_test.c'), '-o', str(binary)], check=True, capture_output=True)
            result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=20)
            self.assertIn('original fallbacks pass', result.stdout)


@unittest.skipUnless((OUTPUT / 'build.json').exists(), 'Current shop cartridge required')
class ShopsCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUTPUT / 'build.json').read_text())
        cls.shop = cls.report['shops']
        cls.rom = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        cls.files, cls.old_files = by_vrom(cls.rom), by_vrom(cls.base)

    def test_actual_lists_and_odd_subset_pointer_alignment(self):
        rel = (ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        imports = self.report['furniture']['imports']
        old = self.old_files[VROM].extract(self.base)
        native_lists = lists(old, TABLE)
        for selected in ([], imports[:1], imports[1:], imports):
            data, table, records = goods(self.base, rel, symbols, selected)
            expected = [None if row is None else row.copy() for row in native_lists]
            for row in records:
                expected[row['group']].append(int(row['item_id'], 16))
            self.assertEqual(lists(data, table), expected)
            self.assertEqual(table % 4, 0)
            self.assertEqual(len(data) % 16, 0)
            if not selected:
                self.assertEqual(data, old)
            if selected == imports:
                self.assertEqual(data, self.files[VROM].extract(self.rom))
                self.assertEqual(len(data), 976)
        with self.assertRaises(ValueError):
            goods(self.base, rel, symbols, imports + imports[:1])

    def test_native_selection_and_loader_contract(self):
        code = self.files[CODE_VROM].extract(self.rom)
        old = self.old_files[CODE_VROM].extract(self.base)
        blob = self.files[BLOB].extract(self.rom)
        helper = (OUTPUT / 'shops/code.bin').read_bytes()
        self.assertLessEqual(CODE + len(helper), LIMIT)
        self.assertEqual(blob[CODE:CODE + len(helper)], helper)
        jump = lambda address: 0x08000000 | (address >> 2 & 0x3FFFFFF)
        self.assertEqual(struct.unpack_from('>4I', blob, BRIDGE),
                         (0xAFA40000, 0x3084FFFF, jump(ENTRY + 8), 0))
        self.assertEqual(struct.unpack_from('>II', code, ENTRY - CODE_RAM),
                         (jump(0x80460000 + CODE), 0))
        self.assertEqual(code[ENTRY + 8 - CODE_RAM:END - CODE_RAM], old[ENTRY + 8 - CODE_RAM:END - CODE_RAM])
        self.assertEqual(struct.unpack_from('>3I', code, DESCRIPTOR - CODE_RAM),
                         (VROM, VROM + 976, 0x06000390))
        for row in self.shop['retained_owners']:
            self.assertEqual(sha256(code[row['start'] - CODE_RAM:row['end'] - CODE_RAM]), row['sha256'])
        self.assertFalse(self.shop['save_format_changed'])

    def test_current_composition_and_import_free_v2(self):
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])
        changes = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['changed_resources']}
        added = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['added_resources']}
        resized = tuple(int(v, 16) for v in self.report['resized_resources'])
        self.assertEqual(compose(self.native, self.base, changes, added, resized=resized), self.rom)
        self.assertEqual(compose(self.native, self.base, {}, {}), self.base)
        self.assertEqual(apply_ups(self.native, (OUTPUT / 'asset-loader.ups').read_bytes()), self.rom)


if __name__ == '__main__':
    unittest.main()
