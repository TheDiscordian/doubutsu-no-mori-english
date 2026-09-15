"""Full-sized Western assets, source properties, water, and native cell rules."""
import json
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests import test_v3_furniture_art as static
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from gc_names import symbol_data
from v3_furniture_art import LARGE_WESTERN_PILOTS, native_profile, scalar_profile
from v3_western_items import identity_evidence, metadata
import v3_catalogue as catalogue
import v3_shops as shops


class LargeWesternArtTests(static.FurnitureArtLocalTests):
    output = static.ROOT / 'build/v3-western-large-art-01'
    pilots = LARGE_WESTERN_PILOTS
    expected_sizes = (3808, 4320, 4400)
    expected_hashes = (
        'e7fdb678242bedfff03b158b277407e0563b9574a37ff892fd09805de26cc65f',
        'ff24a96d8f22a87286b0cf3cb357e1224eb4c3903c5e0f96954a454f8275104e',
        '5b1902037f01f42b680a157a6f7a368686c971b78ee62315d40cfe17cad890fa',
    )

    def test_native_water_state_and_both_texture_coordinate_shifts(self):
        row = self.report['objects'][0]
        pilot = self.pilots[0]
        profile = native_profile(pilot, row['object_bytes'], row['model_offsets'], 0x23C2000)
        self.assertEqual(profile[48:64], scalar_profile(pilot))
        self.assertEqual(profile[56:64], bytes.fromhex('0301000200000000'))
        self.assertEqual(struct.unpack_from('>4I', profile, 16),
            (0x6000000 + row['model_offsets']['opaque'], 0, 0x6000000 + row['model_offsets']['translucent'], 0))
        water = next(m for m in row['models'] if m['layer'] == 'translucent')
        asset = (self.output / row['object_file']).read_bytes()
        commands = list(struct.iter_unpack('>II', asset[water['native_offset']:water['native_offset'] + water['bytes']]))
        self.assertIn((0xE3001001, 0), commands)  # Texture LUT disabled.
        self.assertNotIn((0xE3001001, 0x8000), commands)
        self.assertIn((0xD7000002, 0x0FA00FA0), commands)
        self.assertIn((0xFC309C04, 0x5FFEF7F8), commands)
        self.assertIn((0xFA00001E, 0x9B9BC864), commands)
        self.assertIn((0xFB000000, 0x6464AFFF), commands)
        self.assertIn((0xE200001C, 0xC8104A50), commands)
        self.assertIn((0xD9000000, 0x270405), commands)
        tiles = [(a, b) for a, b in commands if a >> 24 == 0xF5 and b >> 24 & 7 == 0]
        self.assertEqual(len(tiles), 1)
        a, b = tiles[0]
        self.assertEqual((a >> 21 & 7, a >> 19 & 3, a >> 9 & 511), (4, 0, 2))
        self.assertEqual((b >> 8 & 3, b >> 18 & 3, b >> 4 & 15, b >> 14 & 15,
                          b & 15, b >> 10 & 15), (0, 0, 5, 4, 1, 1))
        self.assertEqual(water['triangles'], 2)

    def test_wagon_24_pixel_rows_use_source_pitch_and_padded_tmem_pitch(self):
        row = self.report['objects'][1]
        asset = (self.output / row['object_file']).read_bytes()
        at = row['model_offsets']['opaque']
        commands = list(struct.iter_unpack('>II', asset[at:]))
        texture = next(r for r in row['resources'] if r['symbol'] == 'int_yaz_wagon_horo2_tex_txt')
        i = next(i for i, (a, b) in enumerate(commands) if a >> 24 == 0xFD
                 and b == 0x6000000 + texture['native_offset'])
        self.assertEqual(commands[i][0], 0xFD48000B)  # CI8 loading, twelve source bytes per row.
        self.assertEqual(commands[i + 3], (0xF4000000, 0x0702E05C))  # 24x24 CI4 tile.
        self.assertEqual(commands[i + 5][0] >> 9 & 511, 2)  # Sixteen-byte TMEM pitch.
        self.assertEqual(commands[i + 6], (0xF2000000, 0x0005C05C))
        self.assertEqual((commands[i + 5][1] >> 4 & 15, commands[i + 5][1] >> 14 & 15), (0, 0))
        # The different source/TMEM strides must not stretch, crop, or wrap a row.
        self.assertEqual(texture['bytes'], 24 * 24 // 2)

    def test_storefront_wraps_and_explicit_extents_are_not_texture_resizes(self):
        row = self.report['objects'][2]
        asset = (self.output / row['object_file']).read_bytes()
        commands = list(struct.iter_unpack('>II', asset[row['model_offsets']['opaque']:]))
        expected_extents = [r['words'] for r in self.prepared[2][3]['opaque']['rows'] if r['opcode'] == 0xF2]
        self.assertEqual(expected_extents, [(0xF2000000, v) for v in (0xFC07C, 0x1BC01C, 0xFC0FC, 0xFC07C, 0xBC01C)])
        for command in expected_extents: self.assertIn(command, commands)
        tiles = [(b >> 8 & 3, b >> 18 & 3) for a, b in commands if a >> 24 == 0xF5 and b >> 24 & 7 == 0]
        self.assertIn((0, 2), tiles)  # Wrapped S, clamped T.
        self.assertIn((1, 0), tiles)  # Mirrored S, wrapped T, standalone update.
        self.assertEqual(sum(p.vertex_count for p in self.pilots), 293)
        self.assertEqual(sum(m['triangles'] for r in self.report['objects'] for m in r['models']), 128)


class LargeWesternMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rel = (static.ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (static.ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()

    def test_all_properties_keep_lottery_route_and_actual_preview_values(self):
        records, rows = metadata(self.rel, self.symbols, large=True)
        self.assertEqual(sha256(records), '2ded48047745baf16753611617f29ff552b38fc61fc97fde69640494cf6b442f')
        self.assertEqual([struct.unpack_from('>HHHBB', records, i * 32) for i in range(3)],
            [(1201, 0x32C4, 1100, 1, 1), (1205, 0x32D4, 3800, 1, 1), (1206, 0x32D8, 3680, 1, 1)])
        self.assertEqual([r['native_hra_hex'] for r in rows], ['dc050200', 'dc050e00', 'dc050400'])
        self.assertEqual([r['donor_list'] for r in rows], ['ftr_listB', 'ftr_listLottery', 'ftr_listC'])
        self.assertEqual([r['preview_mode'] for r in rows], [0, 29, 6])
        self.assertEqual([struct.unpack('>2f', bytes.fromhex(r['donor_preview_scalar_hex'])) for r in rows],
            [struct.unpack('>2f', bytes.fromhex(v)) for v in ('3f666666c0400000', '3f5eb852c0a00000', '3f51eb85c0a00000')])
        self.assertTrue(all(r['footprint'] == '1x2' and not r['runtime_installed'] for r in rows))
        evidence = identity_evidence(static.ROOT / 'build/item-identity-megasheet.xlsx', large=True)
        self.assertEqual([r['item_id'] for r in evidence], ['32C4', '32D4', '32D8'])
        self.assertTrue(all(r['native_id_name_and_artwork_absent'] for r in evidence))

    def test_actual_native_and_donor_four_rotation_cell_tables_match(self):
        original = verified_rom((static.ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
        code = by_vrom(original)[CODE_VROM].extract(original)
        for direction, (name, dx, dz) in enumerate((('south', 1, 0), ('east', 0, -1), ('north', -1, 0), ('west', 0, 1))):
            data = symbol_data(self.rel, self.symbols.decode(), 'mRmTp_size_m_data_' + name)
            self.assertEqual(data, struct.pack('>BxhhBxhhBxhhBxhh',
                1, 0, 0, 1, dx, dz, 0, 0, 0, 0, 0, 0))
            at = 0x8010D28C + direction * 24 - CODE_RAM
            self.assertEqual(code[at:at + 24], data)

    def test_sanitized_actual_multi_cell_readers(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-large-items-') as directory:
            binary = Path(directory) / 'test'
            subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(static.ROOT / 'tests/v3_multi_cell_items_test.c'), '-o', str(binary)], check=True, capture_output=True)
            result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=20)
            self.assertIn('Two-cell rotations, guards, rejection, and original fallbacks pass', result.stdout)

    def test_guarded_catalogue_framing_and_complete_stock_lists(self):
        base = (static.ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        self.assertEqual(sha256(base), '8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507')
        prior = json.loads((static.ROOT / 'build/v3-western-runtime-02/build.json').read_bytes())
        new_rows = metadata(self.rel, self.symbols, large=True)[1]
        imports = prior['furniture']['imports'] + [{'item_id': '3350', 'runtime_index': 1236}] + new_rows
        table, rows = catalogue.table(base, self.rel, self.symbols, imports,
            expanded=True, garden=True, western=True, western_large=True)
        native = by_vrom(base)[catalogue.VROM].extract(base)
        at = catalogue.TABLE - catalogue.RAM
        self.assertEqual(table[:436 * 4], native[at:at + 436 * 4])
        self.assertEqual(len(table), 462 * 4)
        self.assertEqual(len(set(struct.iter_unpack('>HH', table))), 462)
        self.assertTrue(all(r['mode'] == 0 for r in rows))
        selected = {r['item_id']: r for r in rows if 'donor_preview_mode' in r}
        self.assertEqual({k: v['donor_preview_mode'] for k, v in selected.items()}, {'32C4': 0, '32D4': 29, '32D8': 6})
        self.assertEqual({k for k, v in selected.items() if v['preview_override']}, {'32D4', '32D8'})
        self.assertEqual(selected['32D4']['donor_acquisition_list'], 'ftr_listLottery')
        self.assertIsNone(selected['32D4']['ordinary_shop_list'])
        self.assertTrue(selected['32D4']['catalogue_orderable'])
        with self.assertRaisesRegex(ValueError, 'installed initializer override'):
            catalogue.install(base, b'', b'', {'symbols': {}, 'flags': []}, table, rows, {}, {}, {})
        with self.assertRaisesRegex(ValueError, 'reviewed preview'):
            catalogue.table(base, self.rel, self.symbols, new_rows, expanded=True)

        stock_imports = [r for r in imports if r['item_id'] != '3294']
        goods, pointer_at, stock_rows = shops.goods(base, self.rel, self.symbols, stock_imports,
            garden=True, western=True, western_large=True)
        old = by_vrom(base)[shops.VROM].extract(base)
        old_ptrs = struct.unpack_from('>12I', old, shops.TABLE)
        new_ptrs = struct.unpack_from('>12I', goods, pointer_at)

        def read_list(data, pointer):
            result = []
            offset = pointer & 0xFFFFFF
            while offset < len(data) - 1:
                item = struct.unpack_from('>H', data, offset)[0]
                if item == 0: return result
                result.append(item)
                offset += 2
            self.fail('Stock list lacks its terminator')

        for group, (before, after) in enumerate(zip(old_ptrs[:-1], new_ptrs[:-1])):
            original = read_list(old, before)
            appended = sorted(int(r['item_id'], 16) for r in stock_rows if r['group'] == group)
            self.assertEqual(read_list(goods, after), original + appended)
        self.assertEqual({r['item_id']: r['group'] for r in stock_rows if r['item_id'] in selected},
            {'32C4': 1, '32D4': 5, '32D8': 2})
        self.assertEqual(new_ptrs[-1], 0)
        with self.assertRaisesRegex(ValueError, 'lottery lists'):
            shops.goods(base, self.rel, self.symbols, new_rows, western=True, western_large=True)

    def test_sanitized_actual_catalogue_overrides_and_retained_clothing(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-large-catalogue-') as directory:
            binary = Path(directory) / 'test'
            subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-DAF_V3_WESTERN_LARGE=1', '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(static.ROOT / 'tests/v3_clothing_catalogue_test.c'), '-o', str(binary)], check=True, capture_output=True)
            result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=20)
            self.assertIn('Large Western exact previews, four rotations, selection, and lottery rules pass', result.stdout)

    def test_sanitized_relocated_readers_use_all_three_actual_roster_records(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-large-roster-') as directory:
            binary = Path(directory) / 'test'
            subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-DAF_V3_ROSTER_CLOTHING=1', '-DAF_V3_CLOTHING_PROFILE=1',
                '-DAF_V3_CONSTRUCTION_ITEMS=1', '-DAF_V3_WESTERN_LARGE=1',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(static.ROOT / 'tests/v3_multi_cell_items_test.c'), '-o', str(binary)], check=True, capture_output=True)
            result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=20)
            self.assertIn('All three dynamic clothing records retain names, prices, and non-furniture footprints', result.stdout)


if __name__ == '__main__': unittest.main()
