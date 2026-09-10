"""English shop art retains exact donor indices and all native non-texture data."""
from dataclasses import replace
import json
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, apply_ups, sha256
from building_artwork import (OBJECT, OBJECT_SHA, TEXTURES, extract, build,
                              palette_equivalent, donor_texture_pointers, model_refs)
from texture_preview import decode, png_rgba, rgba5551, native_range
from title_assets import DATA_BASE, pack4, untile


class TexturePreviewTests(unittest.TestCase):
    def test_palette_colours_alpha_and_png_rows(self):
        self.assertEqual(rgba5551(0xFFFF), bytes([255]*4))
        self.assertEqual(rgba5551(0x0843), bytes([8, 8, 8, 255]))
        self.assertEqual(decode(bytes.fromhex('1f'), 2, 1, 'i4'), bytes([17]*3+[255]+[255]*4))
        rgba = decode(bytes.fromhex('1ffe'), 2, 1, 'ia8')
        self.assertEqual(rgba, bytes([17, 17, 17, 255, 255, 255, 255, 238]))
        png = png_rgba(2, 1, rgba, 2)
        at = 8
        chunks = {}
        while at < len(png):
            size, kind = struct.unpack_from('>I4s', png, at)
            data = png[at+8:at+8+size]
            self.assertEqual(zlib.crc32(kind+data), struct.unpack_from('>I', png, at+8+size)[0])
            chunks[kind] = data
            at += size+12
        self.assertEqual(struct.unpack_from('>2I', chunks[b'IHDR']), (4, 2))
        self.assertEqual(zlib.decompress(chunks[b'IDAT']), (b'\0'+rgba[:4]*2+rgba[4:]*2)*2)
        with self.assertRaises(ValueError): decode(b'', 8, 8, 'ci4', bytes(32))

    def test_visible_palette_changes_reject_but_hidden_rgb_does_not(self):
        native = struct.pack('>16H', 0x2108, *([0xFFFF]*15))
        gc = struct.pack('>16H', 0x0222, *([0xFFFF]*15))
        palette_equivalent(native, gc, {0, 1, 15})
        with self.assertRaisesRegex(ValueError, 'visible index'):
            palette_equivalent(native, bytes(32), {1})
        with self.assertRaisesRegex(ValueError, 'visible index'):
            palette_equivalent(native, struct.pack('>16H', 0x3222, *([0xFFFF]*15)), {0})


@unittest.skipUnless((ROOT/'build/v0-hardware-fixes-02/build.json').is_file(), 'Local supplied assets required')
class ShopAssetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        baseline = ROOT/'build/v0-hardware-fixes-02'
        cls.base = (baseline/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((baseline/'build.json').read_text())

    def test_all_seasons_shapes_palette_indices_geometry_and_non_texture_retention(self):
        output, textures, profile = extract(self.native, self.rel, self.symbols)
        old = by_vrom(self.native)[OBJECT].extract(self.native)
        restored = bytearray(output)
        self.assertEqual(sha256(old), OBJECT_SHA)
        self.assertEqual(len(textures), 12)
        self.assertEqual(sum(r['matched_vertex_uses'] for r in profile['textures']), 328)
        self.assertEqual(sum(r['changed_pixels'] for r in profile['textures']), 3154)
        self.assertEqual(len(profile['donor_model_texture_pointers']), 12)
        for row in TEXTURES:
            source = self.rel[DATA_BASE+row.gc:DATA_BASE+row.gc+2048]
            self.assertEqual(textures[row.native], pack4(untile(source, row.width, row.height, 4)))
            start = row.native-OBJECT
            self.assertEqual(output[start:start+2048], textures[row.native])
            restored[start:start+2048] = old[start:start+2048]
        self.assertEqual(restored, old)
        self.assertEqual(profile['object_sha256'], sha256(output))

    def test_changed_sources_equal_area_wrong_shape_and_wrong_bindings_reject(self):
        with self.assertRaises(ValueError): extract(self.native[:-1], self.rel, self.symbols)
        with self.assertRaises(ValueError): extract(self.native, self.rel[:-1], self.symbols)
        with self.assertRaises(ValueError): extract(self.native, self.rel, self.symbols+b'\n')
        rows = list(TEXTURES)
        rows[0] = replace(rows[0], width=64, height=64)
        with patch('building_artwork.TEXTURES', tuple(rows)), self.assertRaisesRegex(ValueError, 'dimensions/format'):
            extract(self.native, self.rel, self.symbols)
        rows[0] = replace(TEXTURES[0], gc_model=TEXTURES[1].gc_model)
        with patch('building_artwork.TEXTURES', (rows[0],)), self.assertRaisesRegex(ValueError, 'declared asset'):
            donor_texture_pointers(self.rel)
        native_object = by_vrom(self.native)[OBJECT].extract(self.native)
        with self.assertRaisesRegex(ValueError, 'coordinates'):
            model_refs(native_object, TEXTURES[0], bytes(TEXTURES[0].vertex_bytes))

    def test_complete_cartridge_retains_both_conversation_fixes_and_all_resources(self):
        original_report = json.dumps(self.report, sort_keys=True)
        image, ups, report, textures = build(self.native, self.base, self.report, self.rel, self.symbols)
        self.assertEqual(json.dumps(self.report, sort_keys=True), original_report)
        self.assertEqual(len(image), 32*1024*1024)
        self.assertEqual(apply_ups(self.native, ups), image)
        self.assertEqual(sha256(image), '507ddfe5ed585bcd6e20fbab44f7247315339a9c90b66dacec03b1e6b22fbc3a')
        self.assertEqual(report['first_job_progression'], self.report['first_job_progression'])
        self.assertEqual(report['map_names'], self.report['map_names'])
        files, previous = by_vrom(image), by_vrom(self.base)
        self.assertEqual(set(files), set(previous))
        for vrom, entry in previous.items():
            if vrom not in (OBJECT, 0x19D40):
                self.assertEqual(files[vrom].extract(image), entry.extract(self.base), f'{vrom:08X}')
        with self.assertRaisesRegex(ValueError, 'baseline'):
            build(self.native, self.base[:-1], self.report, self.rel, self.symbols)


if __name__ == '__main__':
    unittest.main()
