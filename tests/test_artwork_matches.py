"""Read-only material discovery, exact texels, and explicit unresolved cases."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, sha256
import artwork_matches as art


class ArtworkMatchTests(unittest.TestCase):
    def material(self, pointer=0x06000100):
        obj = bytearray(0x200)
        commands = ((0xFD500000, pointer), (0xF5500000, 0x07000000),
                    (0xE6000000, 0), (0xF3000000, 0x07000000),
                    (0xE7000000, 0), (0xF5400200, 0), (0xF2000000, 0x0001C01C))
        for at, (a, b) in enumerate(commands):
            struct.pack_into('>II', obj, at*8, a, b)
        obj[0x100:0x120] = bytes(range(32))
        return bytes(obj)

    def test_material_uses_render_size_not_load_size(self):
        row, reason = art.native_material(self.material(), 0)
        self.assertIsNone(reason)
        self.assertEqual((row['offset'], row['width'], row['height'], row['format'], row['bytes']),
                         (0x100, 8, 8, 'ci4', 32))
        self.assertEqual(row['texel_sha256'], sha256(bytes(range(32))))

    def test_unknown_segments_bounds_and_sequences_are_not_matches(self):
        for pointer, reason in ((0x04000100, 'external_segment'),
                                (0x060001F8, 'texture_outside_local_storage'),
                                (0x06000000, 'texture_outside_local_storage')):
            row, actual = art.native_material(self.material(pointer), 0)
            self.assertIsNone(row)
            self.assertEqual(actual, reason)
        broken = bytearray(self.material())
        struct.pack_into('>I', broken, 16, 0xDE000000)
        self.assertEqual(art.native_material(bytes(broken), 0)[1], 'no_supported_short_material_sequence')

    def test_named_objects_bind_ranges_and_reject_overlap(self):
        objects = art.objects(b'foo_model = .data:0x00000100; // type:object size:0x40 scope:global\n'
                              b'pixels = .data:0x00000200; // type:object size:0x80 scope:global\n')
        starts = [r[0] for r in objects]
        self.assertEqual(art.owner_at(objects, starts, 0x220, 0x60), (0x200, 0x80, 'pixels'))
        self.assertIsNone(art.owner_at(objects, starts, 0x220, 0x61))
        self.assertIsNone(art.owner_at(objects, starts, 0x80, 8))
        with self.assertRaises(ValueError):
            art.objects(b'a = .data:0x00000100; // type:object size:0x40 x\n'
                        b'b = .data:0x00000120; // type:object size:0x20 x\n')

    def test_unknown_gamecube_input_is_rejected_before_discovery(self):
        with self.assertRaisesRegex(ValueError, 'Changed supplied GC'):
            art.gc_inventory(b'not the supplied REL', b'not the pinned symbols')

    def test_complete_tiled_data_and_format_are_part_of_match(self):
        data = bytes(range(64))
        # Two horizontal GX I8 tiles: each tile is eight pixels by four rows.
        expected = b''.join(data[y*8:y*8+8]+data[32+y*8:40+y*8] for y in range(4))
        self.assertEqual(art.converted(data, 16, 4, 'i8', 8), expected)
        ia = art.converted(data, 16, 4, 'ia8', 8)
        self.assertEqual(ia, bytes((v << 4 & 240) | v >> 4 for v in expected))
        self.assertEqual(art.converted(bytes(range(32)), 8, 8, 'ci4', 4), bytes(range(32)))
        with self.assertRaises(ValueError):
            art.converted(data[:-1], 16, 4, 'i8', 8)
        row = {'texture': '00001000', 'symbol': 'fixture', 'symbol_offset': 0,
               'format': 'i8', 'width': 16, 'height': 4, 'texel_sha256': sha256(expected)}
        result = art.match([row, {**row, 'width': 8, 'height': 8}, {**row, 'format': 'ia8'}], [row])
        self.assertEqual([bool(r['gc_matches']) for r in result], [True, False, False])


@unittest.skipUnless((ROOT/'build/artwork-matches-01.json').is_file(), 'Local source inventory required')
class ActualInventoryTests(unittest.TestCase):
    def test_known_native_and_english_civic_images_and_deduplicated_readers(self):
        report = json.loads((ROOT/'build/artwork-matches-01.json').read_text())
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(report['source_rom_sha256'], sha256(native))
        self.assertEqual(report['source_rel_sha256'], art.REL_SHA256)
        self.assertFalse(report['cartridge_modified'])
        self.assertFalse(report['translation_credit_awarded'])
        rows = report['native_candidates']
        keys = [(r['texture'], r['width'], r['height'], r['format']) for r in rows]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertTrue(any(len(r['commands']) > 1 for r in rows))
        wanted = next(r for r in rows if r['texture'] == '012AF968')
        self.assertEqual((wanted['width'], wanted['height'], wanted['format']), (48, 32, 'ci4'))
        self.assertEqual(wanted['commands'], ['012ADC10'])
        self.assertFalse(wanted['gc_matches'])
        built = (ROOT/'build/title-civic-interior-combined-01/animal-forest-title-preview.z64').read_bytes()
        obj = by_vrom(built)[0x12AC000].extract(built)
        installed = {**wanted, 'texel_sha256': sha256(obj[0x3968:0x3C68])}
        matches = art.match([installed], report['gc_sources'])[0]['gc_matches']
        self.assertIn({'texture': '0093A9E0', 'symbol': 'rom_koban_us_pos1', 'symbol_offset': 0}, matches)
        welcome = next(r for r in rows if r['texture'] == '013D1658')
        obj = by_vrom(built)[0x13CD000].extract(built)
        installed = {**welcome, 'texel_sha256': sha256(obj[0x4658:0x4C58])}
        matches = art.match([installed], report['gc_sources'])[0]['gc_matches']
        self.assertIn({'texture': '00954BA0', 'symbol': 'rom_shop4_1_us_sign03_tex', 'symbol_offset': 0}, matches)
        window = next(r for r in rows if r['texture'] == '00D82FD8')
        self.assertTrue(any(m['symbol'] == 'obj_s_house1_window_txt' for m in window['gc_matches']))
        self.assertTrue(report['skipped']['native']['external_segment'])


if __name__ == '__main__':
    unittest.main()
