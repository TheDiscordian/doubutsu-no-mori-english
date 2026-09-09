/* Exercise actual bridge C with synthetic saves and instrumented native imports. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/hboard/editor.h"

const unsigned char af_hboard_native_default[64] = {0};
const unsigned char af_hboard_english_default[92] __attribute__((nonstring)) =
    "xxxxxxxxxxxxxxxxxx\xCD"
    "xxxxxxxxxxxxxxxxxxxxxxxxxx\xCD"
    "xxxxxxxxxxxxxxxxxxxxx\xCD"
    "xxxxxxxxxxxxxxxxxxxxxxx ";

static union { void *align; unsigned char data[0x10780]; } ovl;
static struct af_hboard_submenu_pointer submenu;
static struct af_hboard_native_editor ed;
static unsigned char saved[4][72];
static int init_calls, done_calls, destruct_calls, old_cursor_calls, matrix_calls;
static int draws, body_bytes, markers, width_error;
static unsigned char drawn[128];
static float mark_x, mark_y, end_x, end_y;
static char note[96];

unsigned char *af_hboard_test_saved(int home) { return saved[home]+4; }
int af_hboard_code_width(unsigned int code, int cut) {
    assert(code < 256 && cut == 1);
    return width_error && code == 'x' ? 0 : code == 'i' ? 4 : 6;
}
void af_hboard_original_init(void *sub, void *menu) {
    assert(sub == &submenu);
    ++init_calls;
    ed.input = *(unsigned char **)((unsigned char *)menu+0x40);
    ed.columns = 16; ed.rows = 4;
    ed.length = 64;
    while (ed.length && ed.input[ed.length-1] == ' ') --ed.length;
    ed.index = ed.column = ed.row = 0;
}
void af_hboard_original_done(void *sub, void *menu) {
    assert(sub == &submenu && menu == ovl.data+0x10358);
    ++done_calls;
    ed.processed = 1;
}
void af_hboard_original_destruct(void *sub) {
    assert(sub == &submenu);
    ++destruct_calls;
    *(struct af_hboard_native_editor **)(ovl.data+0x106E0) = NULL;
}
void af_hboard_original_cursor(struct af_hboard_native_editor *e, short *col, short *row, int index) {
    assert(e == &ed && index >= 0);
    ++old_cursor_calls; *col = 7; *row = 2;
}
static void matrix(void *graph) { assert(graph == (void *)0x1110); ++matrix_calls; }
static void cursor(void *sub, void *game, float x, float y) {
    assert(sub == &submenu && game == (void *)0x2220); ++markers; mark_x = x; mark_y = y;
}
static void end(void *sub, void *game, float x, float y) {
    assert(sub == &submenu && game == (void *)0x2220); ++markers; end_x = x; end_y = y;
}
void af_hboard_font_line(void *game, const unsigned char *text, int length, float x, float y,
                         int r, int g, int b, int a, int flag, int cut, float sx, float sy, int mode) {
    assert(game == (void *)0x2220 && x == 46.0f && r == 30 && !g && !b && a == 255 && !flag && cut == 1 && !mode);
    assert(sx == sy && (sx == 1.0f || sx == 0.5f));
    if (sx == 1.0f) {
        assert(y == 54.0f + draws*16.0f && length >= 0 && body_bytes+length <= 128);
        memcpy(drawn+body_bytes, text, (size_t)length); body_bytes += length; ++draws;
    } else {
        assert(y == 42.0f && length > 0 && length < 96);
        memcpy(note, text, (size_t)length); note[length] = 0;
    }
}
static void open_editor(int home, int mode) {
    memset(&ovl, 0, sizeof(ovl)); memset(&ed, 0, sizeof(ed));
    submenu.overlay = ovl.data;
    *(struct af_hboard_native_editor **)(ovl.data+0x106E0) = &ed;
    ((struct af_hboard_matrix_pointer *)(ovl.data+0x106B4))->function = matrix;
    *(int *)(ovl.data+0x10154) = home;
    *(int *)(ovl.data+0x10358+0x38) = mode;
    *(unsigned char **)(ovl.data+0x10358+0x40) = saved[home]+4;
    af_hboard_editor_init(&submenu, ovl.data+0x10358);
    ed.cursor_draw = cursor; ed.end_draw = end;
}
static void command(int code, int value) {
    ed.command = (unsigned char)code; ed.code = (unsigned char)value;
    af_hboard_editor_command(&submenu, ovl.data+0x10358);
}
static void draw(void) {
    draws = body_bytes = markers = 0; note[0] = 0;
    af_hboard_editor_draw(&submenu, (void *)0x1110, (void *)0x2220, 0, 0);
}
int main(void) {
    int home, before, i;
    short col, row;
    unsigned char copy[sizeof(saved)];
    for (home = 0; home < 4; ++home) {
        memset(saved, '!', sizeof(saved));
        memcpy(saved[home]+4, af_hboard_native_default, 64); memcpy(copy, saved, sizeof(saved));
        open_editor(home, 1);
        assert(af_hboard_context.active && ed.input == af_hboard_context.draft.text && ed.length == 91);
        assert(ed.columns == 32 && ed.rows == 4 && ed.hboard_draw == af_hboard_editor_draw);
        draw();
        assert(draws == 4 && body_bytes == 91 && markers == 2);
        assert(memcmp(drawn, af_hboard_english_default, 91) == 0);
        assert(mark_x == 39 && mark_y == 54 && end_x == 25 && end_y == 18);
        assert(strcmp(note, "Custom messages: 64 characters max.") == 0);
        af_hboard_editor_cursor(&ed, &col, &row, 19); assert(col == 0 && row == 1);
        command(8, 'a'); assert(ed.processed && ed.length == 92);
        before = done_calls; command(5, 0);
        assert(done_calls == before && !ed.processed && af_hboard_context.warning == -5);
        assert(memcmp(saved, copy, sizeof(saved)) == 0);
        draw(); assert(strstr(note, "64 characters"));
        command(6, 0); command(5, 0); assert(done_calls == before+1);
        assert(memcmp(saved, copy, sizeof(saved)) == 0);
        af_hboard_editor_destruct(&submenu);
        assert(!ed.hboard_draw && !af_hboard_context.active && !af_hboard_context.saved);
        memset(saved[home]+4, ' ', 64); memcpy(saved[home]+4, "Custom", 6); memcpy(copy, saved, sizeof(saved));
        open_editor(home, 1); command(8, 'x'); assert(ed.length == 7);
        assert(memcmp(saved, copy, sizeof(saved)) == 0);
        command(5, 0); memcpy(copy+home*72+4, "xCustom", 7);
        assert(memcmp(saved, copy, sizeof(saved)) == 0);
        open_editor(home, 1); assert(ed.length == 7 && memcmp(ed.input, "xCustom", 7) == 0);
        command(8, 'y'); af_hboard_editor_destruct(&submenu);
        assert(memcmp(saved, copy, sizeof(saved)) == 0); /* Discarded private draft. */
        open_editor(home, 1); saved[home][4] = 'q'; before = done_calls;
        command(5, 0); assert(af_hboard_context.warning == -6 && done_calls == before);
        draw(); assert(strstr(note, "without saving"));
        command(5, 0); assert(done_calls == before+1 && saved[home][4] == 'q');
    }
    for (i = 0; i < 5; ++i) {
        if (i == 1) continue;
        open_editor(0, i); assert(!af_hboard_context.active && !ed.hboard_draw && ed.input == saved[0]+4);
        before = old_cursor_calls; af_hboard_editor_cursor(&ed, &col, &row, 0);
        assert(old_cursor_calls == before+1 && col == 7 && row == 2);
        af_hboard_editor_destruct(&submenu);
    }
    width_error = 1; open_editor(0, 1);
    assert(!af_hboard_context.active && af_hboard_context.warning == -2);
    memcpy(copy, saved, sizeof(saved)); command(8, 'z'); draw(); assert(strstr(note, "without saving"));
    before = done_calls; command(5, 0); assert(done_calls == before+1);
    assert(memcmp(saved, copy, sizeof(saved)) == 0);
    assert(init_calls == 21 && destruct_calls == 12 && matrix_calls == 13);
    puts("Owner-editor bridge checks passed");
    return 0;
}
