import ctypes as C
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_VROM, by_vrom, sha256
from font import WIDTH_TABLE
from gyroid_default import DEFAULT, native_sources, reference_payloads
from hboard_editor import audit, reference_sources
from runtime_module import module_command_info


class Point(C.Structure):
    _fields_ = [('column', C.c_ushort), ('row', C.c_ushort), ('x', C.c_ushort)]


class Line(C.Structure):
    _fields_ = [('start', C.c_ushort), ('length', C.c_ushort), ('width', C.c_ushort)]


class Layout(C.Structure):
    _fields_ = [('lines', Line*4), ('cursor', Point), ('end', Point), ('rows', C.c_ushort)]


class Draft(C.Structure):
    _fields_ = [('text', C.c_ubyte*128), ('original', C.c_ubyte*64),
                ('length', C.c_ushort), ('cursor', C.c_ushort)]


@unittest.skipUnless(shutil.which('gcc'), 'Host GCC required')
class HboardEditorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.path = Path(cls.temp.name)
        library = cls.path/'editor.so'
        subprocess.run(['gcc', '-std=c99', '-Wall', '-Wextra', '-Werror', '-O2', '-shared', '-fPIC',
                        str(ROOT/'runtime/hboard_editor.c'), '-o', str(library)], check=True, capture_output=True)
        cls.lib = C.CDLL(str(library))
        cls.lib.af_hboard_begin.argtypes = [C.POINTER(Draft), C.c_void_p, C.c_void_p, C.c_void_p]
        cls.lib.af_hboard_layout.argtypes = [C.c_void_p, C.c_int, C.c_int, C.c_void_p, C.POINTER(Layout)]
        cls.lib.af_hboard_command.argtypes = [C.POINTER(Draft), C.c_int, C.c_int, C.c_void_p]
        for name in ('af_hboard_pack', 'af_hboard_commit'):
            getattr(cls.lib, name).argtypes = [C.POINTER(Draft), C.c_void_p, C.c_void_p, C.c_void_p]

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def setUp(self):
        self.widths = (C.c_ubyte*256)(*([12]*256))
        for c in range(32, 127): self.widths[c] = 4 if c in b"iIl'" else 6
        self.native = bytes(range(128, 192))
        self.english = b'x'*18+b'\xcd'+b'x'*26+b'\xcd'+b'x'*21+b'\xcd'+b'x'*23+b' '
        self.assertEqual(len(self.english), 92)

    def begin(self, saved=None):
        saved = self.native if saved is None else saved.ljust(64, b' ')
        self.assertEqual(len(saved), 64)
        state = Draft()
        self.assertEqual(self.lib.af_hboard_begin(C.byref(state), saved, self.native, self.english), 1)
        self.assertEqual(bytes(state.original), saved)
        return state

    def layout(self, text, cursor=None):
        out = Layout()
        result = self.lib.af_hboard_layout(text, len(text), len(text) if cursor is None else cursor,
                                           self.widths, C.byref(out))
        return result, out

    def command(self, draft, command, code=0):
        return self.lib.af_hboard_command(C.byref(draft), command, code, self.widths)

    def pack(self, draft, expected=1):
        out = C.create_string_buffer(b'!'*64)
        result = self.lib.af_hboard_pack(C.byref(draft), self.native, self.english, out)
        self.assertEqual(result, expected)
        if expected != 1: self.assertEqual(out.raw, b'!'*64+b'\0')
        return out.raw[:64]

    def test_default_full_draft_and_unchanged_custom_round_trip(self):
        draft = self.begin()
        self.assertEqual(bytes(draft.text), self.english.ljust(128, b' '))
        self.assertEqual((draft.length, draft.cursor), (91, 0))
        self.assertEqual(self.pack(draft), self.native)
        # Every one-byte change, including padding and non-Latin bytes, must
        # remain a custom message, not be mistaken for the saved default.
        for at in range(64):
            for code in range(256):
                if code == self.native[at]: continue
                saved = bytearray(self.native); saved[at] = code
                draft = self.begin(bytes(saved))
                self.assertEqual(bytes(draft.text[:64]), saved)
                self.assertEqual(self.pack(draft), saved)
        for text in (b'', b'Custom text', b'\xcd a\xcd', b'a'*64, bytes(64)):
            draft = self.begin(text)
            self.assertEqual(self.pack(draft), text.ljust(64, b' '))

    def test_manual_lines_width_boundaries_and_full_buffer_end(self):
        text = b'x'*32
        status, out = self.layout(text)
        self.assertEqual(status, 1)
        self.assertEqual((out.lines[0].length, out.lines[0].width), (32, 192))
        self.assertEqual((out.end.row, out.end.x), (1, 0))
        for text in (b'', b'\xcd', b'a\xcd\xcdb', b"iI'a\xcdx", b'a'*128):
            status, out = self.layout(text)
            self.assertEqual(status, 1)
            recovered = b''.join(text[line.start:line.start+line.length] for line in out.lines)
            self.assertEqual(recovered, text)
            self.assertTrue(all(line.width <= 192 for line in out.lines))
        status, out = self.layout(b'a'*128)
        self.assertEqual((status, out.end.row, out.end.x), (1, 3, 192))
        self.assertEqual(self.layout(b'a\xcd'*4)[0], -3)
        self.assertEqual(self.layout(b'\xa1'*65)[0], -3)
        self.assertEqual(self.layout(b'a'*129)[0], -1)
        status, out = self.layout(b'a'*32+b'b', 32)
        self.assertEqual((status, out.cursor.row, out.cursor.x), (1, 1, 0))

    def test_edit_rejection_is_transactional_and_delete_repairs(self):
        draft = self.begin(b'a'*64)
        draft.cursor = 64
        self.assertEqual(self.command(draft, 8, ord('b')), 1)
        self.pack(draft, -5)
        self.assertEqual(self.command(draft, 6), 1)
        self.assertEqual(self.pack(draft), b'a'*64)
        for code in (-2, 256, 127, 128):
            old = bytes(draft)
            self.assertEqual(self.command(draft, 8, code), -1)
            self.assertEqual(bytes(draft), old)
        draft = self.begin(b'\xa1'*64); draft.cursor = 64
        old = bytes(draft)
        self.assertEqual(self.command(draft, 8, ord('x')), -3)
        self.assertEqual(bytes(draft), old)
        self.widths[ord('b')] = 0
        self.assertEqual(self.command(draft, 7, ord('b')), -2)
        self.assertEqual(bytes(draft), old)
        self.assertEqual(self.command(draft, 6), 1)
        self.assertEqual(draft.length, 63)
        draft.text[:] = b'a'*128; draft.length = draft.cursor = 128
        old = bytes(draft)
        self.assertEqual(self.command(draft, 8, ord('a')), -4)
        self.assertEqual(bytes(draft), old)

    def test_default_edit_warning_recovery_and_saved_conflict(self):
        draft = self.begin()
        saved = C.create_string_buffer(b'EDGE'+self.native+b'BELLS')
        pointer = C.byref(saved, 4)
        self.assertEqual(self.command(draft, 8, ord('x')), 1)
        self.assertEqual(self.lib.af_hboard_commit(C.byref(draft), self.native, self.english, pointer), -5)
        self.assertEqual(saved.raw, b'EDGE'+self.native+b'BELLS\0')
        self.assertEqual(self.command(draft, 6), 1)
        self.assertEqual(self.lib.af_hboard_commit(C.byref(draft), self.native, self.english, pointer), 1)
        self.assertEqual(saved.raw, b'EDGE'+self.native+b'BELLS\0')
        saved[4] = b'?'
        old = saved.raw
        self.assertEqual(self.lib.af_hboard_commit(C.byref(draft), self.native, self.english, pointer), -6)
        self.assertEqual(saved.raw, old)
        draft = self.begin(b'original')
        saved = C.create_string_buffer(b'original'.ljust(64, b' '))
        self.assertEqual(self.command(draft, 8, ord('x')), 1)
        self.assertEqual(saved.raw, b'original'.ljust(64, b' ')+b'\0')
        self.assertEqual(self.lib.af_hboard_commit(C.byref(draft), self.native, self.english, saved), 1)
        self.assertEqual(saved.raw, b'xoriginal'.ljust(64, b' ')+b'\0')

    def test_horizontal_vertical_navigation_and_case(self):
        draft = self.begin(b'iiii\xcdxxx')
        self.assertEqual(self.command(draft, 1), 0)
        draft.cursor = 2
        self.assertEqual(self.command(draft, 2), 1)
        self.assertEqual(draft.cursor, 6)  # x=8 -> closest boundary x=6.
        self.assertEqual(self.command(draft, 3), 1)
        self.assertEqual(draft.cursor, 2)  # x=6 -> tie chooses following x=8.
        draft.cursor = draft.length
        self.assertEqual(self.command(draft, 4), 1)
        self.assertEqual(bytes(draft.text[:draft.length]), b'iiii\xcdxxx ')
        self.assertEqual(self.command(draft, 2), 1)
        self.assertEqual(bytes(draft.text[:draft.length]), b'iiii\xcdxxx \xcd')
        self.assertEqual(self.command(draft, 1), 1)
        self.assertEqual(self.command(draft, 7, ord('X')), 1)
        self.assertEqual(bytes(draft.text[:draft.length]), b'iiii\xcdxxxX\xcd')
        self.assertEqual(self.command(draft, 5), -1)

    def test_invalid_layout_outputs_and_state_are_unchanged(self):
        out = Layout()
        C.memset(C.byref(out), 0xA5, C.sizeof(out)); old = bytes(out)
        for text, length, cursor in ((b'a', -1, 0), (b'a', 1, -1), (b'a', 1, 2), (None, 0, 0),
                                     (b'\xcd'*4, 4, 0)):
            self.assertLess(self.lib.af_hboard_layout(text, length, cursor, self.widths, C.byref(out)), 0)
            self.assertEqual(bytes(out), old)
        for width in (0, 13, 255):
            self.widths[ord('a')] = width
            self.assertEqual(self.lib.af_hboard_layout(b'a', 1, 0, self.widths, C.byref(out)), -2)
            self.assertEqual(bytes(out), old)
        draft = self.begin(b'a')
        for length, cursor in ((129, 0), (1, 2), (0, 0)):
            draft.length, draft.cursor = length, cursor
            old = bytes(draft)
            self.assertEqual(self.command(draft, 8, ord('x')), -1)
            self.assertEqual(bytes(draft), old)
            self.pack(draft, -1)

    @unittest.skipUnless((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').is_file(), 'Local ROM required')
    def test_real_default_native_sources_and_installed_proportional_widths(self):
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        report = audit(native)
        self.assertEqual((report['saved_bytes'], report['draft_bytes'], report['line_pixels']), (64, 128, 192))
        self.native = native_sources(native)['string'][DEFAULT]
        self.english = reference_payloads(native, module_command_info(native))[0]
        built = (ROOT/'build/gyroid-default-pilot/animal-forest-halfwidth.z64').read_bytes()
        code = by_vrom(built)[CODE_VROM].extract(built)
        self.widths[:] = [12-v for v in code[WIDTH_TABLE:WIDTH_TABLE+256]]
        draft = self.begin()
        status, layout = self.layout(bytes(draft.text[:draft.length]))
        self.assertEqual((status, layout.rows), (1, 4))
        self.assertEqual(draft.length, 92)
        self.assertEqual([v.length for v in layout.lines], [19, 28, 23, 22])
        self.assertEqual(self.pack(draft), self.native)

    @unittest.skipUnless((ROOT/'local/ac-decomp/src/game/m_editor_ovl.c').is_file(), 'Local GC source required')
    def test_layout_and_cursor_against_pinned_gamecube_source(self):
        sources = reference_sources()
        source = sources['m_editor_ovl.c']
        source = source[source.index('static int mED_get_col_line_width('):
                        source.index('static void mED_set_idxcol_inLineWidth(')]
        board = sources['m_hboard_ovl.c']
        source += board[board.index('static int mHB_strLineCheck('):board.index('static void mHB_move_Move(')]
        prefix = '''#include <stddef.h>
typedef unsigned char u8;
typedef short s16;
#define TRUE 1
#define FALSE 0
#define CHAR_NEW_LINE 205
#define mED_TYPE_PASSWORDCHK 7
#define mED_LINE_OK 0
#define mED_LINE_NEWLINE 1
#define mED_LINE_WIDTH_OVER 2
#define mED_LINE_NUM_OVER 3
#define mHB_LINE_CHECK_OK 0
#define mHB_LINE_CHECK_NEWLINE 1
#define mHB_LINE_CHECK_OVER_WIDTH 2
#define mHB_LINE_CHECK_OVER_STR_LEN 3
#define mHB_LINE_WIDTH_MAX 192
typedef struct { int data0; } mSM_MenuInfo_c;
typedef struct { u8 *input_str; int line_width, max_line_no, cursor_idx; s16 _22, _24, _26; } mED_Ovl_c;
unsigned char widths[256];
int mFont_GetCodeWidth(u8 c, int cut) { (void)cut; return widths[c]; }
'''
        suffix = '''
void reference_cursor(u8 *text, int cursor, s16 *out) {
    mSM_MenuInfo_c menu = {1};
    mED_Ovl_c editor = {text, 192, 4, cursor, 0, 0, 0};
    mED_get_col_line_width(&menu, &editor, &editor._22, &editor._24, &editor._26, cursor);
    mED_check_line_over(&editor);
    out[0] = editor._22; out[1] = editor._24; out[2] = editor._26;
}
void reference_lines(u8 *text, int length, s16 *out) {
    u8 *p = text;
    int row;
    for (row = 0; row < 4; ++row) {
        int width = 0, count = 0, result;
        out[row*2] = (s16)(p-text);
        do { result = mHB_strLineCheck(&p, text+length, &width, &count); } while (result == 0);
        out[row*2+1] = (s16)count;
    }
}
'''
        path = self.path/'reference.c'; path.write_text(prefix+source+suffix)
        library = self.path/'reference.so'
        subprocess.run(['gcc', '-std=c99', '-Wall', '-Wextra', '-Werror', '-O2', '-shared', '-fPIC',
                        str(path), '-o', str(library)], check=True, capture_output=True)
        gc = C.CDLL(str(library))
        gc.reference_cursor.argtypes = [C.c_void_p, C.c_int, C.c_void_p]
        gc.reference_lines.argtypes = [C.c_void_p, C.c_int, C.c_void_p]
        gc_widths = (C.c_ubyte*256).in_dll(gc, 'widths')
        rng = random.Random(748044)
        checked = 0
        texts = [b'a'*n for n in (0, 31, 32, 33, 64, 96, 127, 128)]
        texts += [bytes(rng.choice(b"iiiiWWW a'\xcd\xa1") for _ in range(rng.randrange(129))) for _ in range(500)]
        for case, text in enumerate(texts):
            if case % 50 == 0 and case:
                self.widths[:] = [rng.randrange(1, 13) for _ in range(256)]
            gc_widths[:] = self.widths[:]
            if self.layout(text)[0] != 1: continue
            expected_lines = (C.c_short*8)()
            gc.reference_lines(text+b' ', len(text), expected_lines)
            actual_lines = self.layout(text)[1].lines
            for row, line in enumerate(actual_lines):
                self.assertEqual(line.length, expected_lines[row*2+1])
                if line.length: self.assertEqual(line.start, expected_lines[row*2])
            for cursor in range(len(text)+1):
                actual = self.layout(text, cursor)[1].cursor
                expected = (C.c_short*3)()
                gc.reference_cursor(text+b' ', cursor, expected)
                self.assertEqual((actual.column, actual.row, actual.x), tuple(expected), (case, cursor, text))
                checked += 1
        self.assertGreater(checked, 3000)

    @unittest.skipUnless((ROOT/'build/hboard-editor-core/core.json').is_file(), 'Build MIPS core first')
    def test_compiled_core_and_local_reference_files_match_current_sources(self):
        path = ROOT/'build/hboard-editor-core'
        report = json.loads((path/'core.json').read_text())
        self.assertFalse(report['cartridge_installed'])
        self.assertEqual(report['unresolved_imports'], [])
        self.assertEqual(sha256((path/'core.o').read_bytes()), report['object_sha256'])
        for name, digest in report['source_sha256'].items():
            self.assertEqual(sha256((ROOT/name).read_bytes()), digest, name)
        for name in ('saved-default', 'english-default'):
            key = 'native_default_sha256' if name == 'saved-default' else 'english_default_sha256'
            self.assertEqual(sha256((path/(name+'.bin')).read_bytes()), report[key])
        self.assertIn('.bss                 0', report['sections'])


if __name__ == '__main__': unittest.main()
