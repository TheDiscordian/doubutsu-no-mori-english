"""Draft layout, native fallback contracts, and exact combined ROM retention."""
import ctypes as C
import json
from pathlib import Path
import subprocess
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, apply_ups
from editor_pixel_fix import PARTS, BASE_SHA, POOL_AT, POOL_BEFORE, POOL_EXTRA, sources, jump
from title_start_fix import reconstruct
from font import WIDTH_TABLE
from npc_mail_show import relocate_verified_data
from catalogue_names import Image

OUT = ROOT/'build/v1-editor-pixel-fix-03'


class EditorPixelHostTests(unittest.TestCase):
    def test_layout_cursor_navigation_save_limits_field_switches_and_silent_sound_calls(self):
        with tempfile.TemporaryDirectory(prefix='af-pixel-check-') as temporary:
            exe = str(Path(temporary)/'check')
            source = ROOT/'overlays/editor_pixels'
            result = subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                *(str(source/(name+'.c')) for name in ('layout', 'editor', 'letter', 'notice')),
                str(ROOT/'runtime/mail/view.c'), str(ROOT/'tests/editor_pixels_check.c'), '-o', exe],
                capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([exe], capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)

    def test_caret_matches_installed_font_and_read_scanner(self):
        class Point(C.Structure):
            _fields_ = [(name, C.c_uint) for name in ('start', 'column', 'row', 'x')]
        base = (ROOT/'build/v1-playtest-fixes-01/animal-forest-title-preview.z64').read_bytes()
        widths = by_vrom(base)[CODE_VROM].extract(base)[WIDTH_TABLE:WIDTH_TABLE+256]
        with tempfile.TemporaryDirectory(prefix='af-pixel-width-') as temporary:
            lib = Path(temporary)/'layout.so'
            subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-O2', '-shared', '-fPIC',
                str(ROOT/'overlays/editor_pixels/layout.c'), str(ROOT/'runtime/mail/view.c'),
                str(ROOT/'tests/mail_view_mock.c'), '-o', str(lib)], check=True, capture_output=True, timeout=30)
            dll = C.CDLL(str(lib)); table = (C.c_int*256).in_dll(dll, 'af_mail_view_widths')
            for code, cut in enumerate(widths): table[code] = 12-cut
            dll.af_edit_position.argtypes = [C.c_char_p, C.c_uint, C.c_uint, C.POINTER(Point)]
            for text in (b"I'm enjoying the English keyboard!"*2,
                         b'First line.\xcd\xcdKeep the blank line.', b'A'*96, b'i'*96):
                start = row = px = 0
                for index in range(len(text)+1):
                    # Independent per-glyph reference, including lookahead at a
                    # wrap boundary and the scanner's newline-before-wrap rule.
                    if index and text[index-1] == 0xCD:
                        start = index; row += 1; px = 0
                    elif index:
                        px += table[text[index-1]]
                    if index < len(text) and text[index] != 0xCD and px+table[text[index]] > 192:
                        start = index; row += 1; px = 0
                    if index == len(text) and px == 192 and row < 5:
                        start = index; row += 1; px = 0
                    point = Point()
                    self.assertEqual(dll.af_edit_position(text, len(text), index, C.byref(point)), 1)
                    self.assertEqual((point.start, point.row, point.x), (start, row, px), (text, index))


@unittest.skipUnless((OUT/'fixes.json').is_file(), 'Compiled pixel-editor candidate required')
class EditorPixelArtifactTests(unittest.TestCase):
    def test_installed_hooks_relocations_pool_and_all_unrelated_resources(self):
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        before = (ROOT/'build/v1-playtest-fixes-01/animal-forest-title-preview.z64').read_bytes()
        image = (OUT/'animal-forest-title-preview.z64').read_bytes()
        report = json.loads((OUT/'fixes.json').read_text())
        self.assertEqual(sha256(before), BASE_SHA); self.assertEqual(sha256(image), report['output_sha256'])
        self.assertEqual(report['sources'], sources()); self.assertEqual(len(image), 0x2000000)
        self.assertEqual(apply_ups(native, (OUT/'animal-forest-title-preview.ups').read_bytes()), image)
        old, files = by_vrom(before), by_vrom(image)
        changed = {v for spec in PARTS.values() for v in (spec['vrom'], spec['reloc'])}
        changed |= {0x19D40, 0x7749C0, CODE_VROM}
        self.assertEqual(set(files), set(old))
        for vrom in files:
            self.assertEqual(files[vrom].index, old[vrom].index)
            if vrom not in changed: self.assertEqual(files[vrom].extract(image), old[vrom].extract(before), hex(vrom))
        for name, spec in PARTS.items():
            p = report['parts'][name]; data = files[spec['vrom']].extract(image); rel = files[spec['reloc']].extract(image)
            prior = old[spec['vrom']].extract(before)
            self.assertEqual(sha256(data), p['overlay_sha256']); self.assertEqual(sha256(rel), p['relocation_sha256'])
            self.assertEqual({at for at in range(0, len(prior), 4) if data[at:at+4] != prior[at:at+4]}, set(p['touched_offsets']))
            for load_at in (0x80200010, 0x80370010):
                relocated = relocate_verified_data(Image(spec['ram'], len(data), struct.unpack_from('>5I', rel)), data, rel, load_at)
                for address, (symbol, _, _) in {**spec['entries'], **spec['calls']}.items():
                    target = spec['imports'].get(symbol, load_at+p['symbols'].get(symbol, 0))
                    self.assertEqual(struct.unpack_from('>I', relocated, address-spec['ram'])[0], jump(target, address in spec['calls']))
            self.assertLessEqual(files[spec['vrom']].vend, spec['reloc'])
        code = files[CODE_VROM].extract(image); prior = old[CODE_VROM].extract(before); at = POOL_AT-CODE_RAM
        self.assertEqual(code, prior[:at]+struct.pack('>I', POOL_BEFORE+POOL_EXTRA)+prior[at+4:])
        self.assertLessEqual(report['shared_growth_bytes'], POOL_EXTRA)
        from test_notice_install import allocation_registers
        self.assertEqual(allocation_registers(code)[16]-allocation_registers(prior)[16], POOL_EXTRA)
        boot = by_vrom(native)[0x1060]
        self.assertEqual(image[boot.pstart:boot.pstart+boot.size], files[0x1060].extract(image))

    def test_resize_requires_explicit_ownership_and_no_overlap(self):
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        base = (ROOT/'build/v1-playtest-fixes-01/animal-forest-title-preview.z64').read_bytes()
        vrom = PARTS['editor']['vrom']; data = by_vrom(base)[vrom].extract(base)
        with self.assertRaisesRegex(ValueError, 'allocation'): reconstruct(native, base, {vrom: data+bytes(16)})
        with self.assertRaisesRegex(ValueError, 'overlaps'): reconstruct(native, base, {vrom: bytes(0x8001)}, resized=(vrom,))
        with self.assertRaisesRegex(ValueError, 'Missing'): reconstruct(native, base, {vrom: data}, resized=(1,))


if __name__ == '__main__': unittest.main()
