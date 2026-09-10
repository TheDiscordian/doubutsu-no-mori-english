#include <assert.h>
#include <stddef.h>
#include <string.h>
#include "../overlays/editor_pixels/layout.h"
#include "../overlays/keyboard_grid/editor.h"

void af_pixel_position(struct af_hboard_native_editor *, short *, short *, int);
void af_pixel_up(struct af_hboard_native_editor *);
void af_pixel_down(struct af_hboard_native_editor *);
void af_pixel_grid_input(void *);
void af_pixel_letter_cursor(void *, void *, float, float);
void af_pixel_notice_body(void *, void *, const unsigned char *, int, float, float, float *, float *);
void af_pixel_notice_cursor(void *, void *, float, float);

struct af_grid_context af_grid_context;
static struct af_hboard_native_editor ed;
static struct af_hboard_submenu_pointer submenu;
static union { max_align_t alignment; unsigned char bytes[0x50]; } menu;
static unsigned char board[192], overlay[32];
static int fallback, sounds, input_calls, draw_count, letter_calls, movement;
static float cursor_x, cursor_y;
static struct { unsigned int length; float x, y; unsigned char text[96]; } draws[6];

int af_mail_view_test_width(unsigned char c) { return c == 'i' || c == 'I' || c == '\'' ? 2 : c < 128 ? 6 : 12; }
unsigned char *af_mail_view_test_board(void *s) { assert(s == &submenu); return board; }
void af_mail_view_test_draw(void *g, const unsigned char *text, unsigned int length,
                            float x, float y, const unsigned char *colour) {
    assert(g == &ed && length <= 96u && colour && draw_count < 6);
    draws[draw_count].length = length; draws[draw_count].x = x; draws[draw_count].y = y;
    memcpy(draws[draw_count].text, text, length); ++draw_count;
}
void *af_pixel_state(void *s, unsigned int at) {
    assert(s == &submenu);
    assert(at == 0x106E0u || at == 0x106E4u);
    return at == 0x106E0u ? (void *)&ed : board;
}
void af_pixel_original_position(struct af_hboard_native_editor *e, short *x, short *y, int index) {
    assert(e == &ed); ++fallback; *x = (short)index; *y = 9;
}
void af_pixel_original_up(struct af_hboard_native_editor *e) { assert(e == &ed); ++fallback; }
void af_pixel_original_down(struct af_hboard_native_editor *e) { assert(e == &ed); ++fallback; }
void af_pixel_native_insert(struct af_hboard_native_editor *e) {
    unsigned char proposed[96], *original;
    short column, row;
    assert(e == &ed && e->index >= 0 && e->index <= e->length);
    if (e->length >= 96) return;
    memcpy(proposed, e->input, (size_t)e->index); proposed[e->index] = e->code;
    memcpy(proposed+e->index+1, e->input+e->index, (size_t)(e->length-e->index));
    original = e->input; e->input = proposed;
    af_pixel_position(e, &column, &row, e->length+1); e->input = original;
    if (row >= e->rows) return;
    memcpy(e->input, proposed, (size_t)++e->length); ++e->index; e->processed = 1;
}
int af_grid_owned(void *s) {
    return s == af_grid_context.submenu && af_grid_context.editor == &ed && af_grid_context.input == ed.input;
}
void af_grid_editor_input(void *s) {
    ++input_calls;
    if (!af_grid_owned(s)) { af_grid_context.error = 1; return; }
    af_grid_context.state.moved = movement == 1;
    if (movement == 2) af_grid_context.state.page ^= 1u;
}
void af_pixel_sound(unsigned int sound) { assert(sound == 0x32u); ++sounds; }
void af_letter_cursor(void *s, void *g, float x, float y) {
    assert(s == &submenu && g == &ed); ++letter_calls; cursor_x = x; cursor_y = y;
}
static void mark(void *s, void *g, float x, float y) {
    assert(s == &submenu && g == &ed); cursor_x = x; cursor_y = y;
}
static void point(const unsigned char *text, unsigned int length, unsigned int index,
                   unsigned int row, unsigned int column, unsigned int x) {
    struct af_edit_point p;
    assert(af_edit_position(text, length, index, &p));
    assert(p.row == row && p.column == column && p.x == x);
}
static void fresh(const unsigned char *text, unsigned int length) {
    memset(&ed, 0, sizeof(ed)); memset(board, 0xA5, sizeof(board));
    memset(board+0x3C, ' ', 96); memcpy(board+0x3C, text, length);
    board[0] = 1; board[6] = (unsigned char)length;
    ed.input = board+0x3C; ed.columns = 16; ed.rows = 6; ed.length = (short)length;
    ed.cursor_draw = mark; draw_count = 0;
    submenu.overlay = overlay;
}
int main(void) {
    unsigned char text[96], snapshot[192];
    struct af_edit_point p;
    short x, y;
    float ex, ey, draw_y;
    int i, n;
    memset(text, 'A', sizeof(text));
    point(text, 96, 16, 0, 16, 96); point(text, 96, 32, 1, 0, 0);
    point(text, 96, 95, 2, 31, 186); point(text, 96, 96, 3, 0, 0);
    text[32] = 0xCD;
    point(text, 33, 32, 0, 32, 192); point(text, 33, 33, 1, 0, 0);
    memset(text, 'i', sizeof(text)); point(text, 95, 95, 0, 95, 190);
    memset(text, 0xA1, sizeof(text)); point(text, 96, 96, 5, 16, 192);
    memset(text, 0xCD, sizeof(text)); point(text, 6, 6, 5, 1, 0);
    assert(!af_edit_position(text, 7, 7, &p));
    assert(!af_edit_position(text, 97, 0, &p)); assert(!af_edit_position(text, 1, 2, &p));
    point((const unsigned char *)"", 0, 0, 0, 0, 0);

    /* Insertion uses pixel fit but the fixed 96-byte destination stays bounded. */
    fresh((const unsigned char *)"", 0);
    for (i = 0; i < 96; ++i) { ed.code = 'A'; ed.processed = 0; af_pixel_native_insert(&ed); assert(ed.processed); }
    memcpy(snapshot, board, sizeof(board)); ed.processed = 0; af_pixel_native_insert(&ed);
    assert(!ed.processed && !memcmp(snapshot, board, sizeof(board)));
    af_pixel_position(&ed, &x, &y, 16); assert(x == 16 && y == 0);
    ed.rows = 1; n = fallback; af_pixel_position(&ed, &x, &y, 3);
    af_pixel_up(&ed); af_pixel_down(&ed); assert(fallback == n+3 && x == 3 && y == 9);

    /* Vertical travel follows pixels, keeps explicit blank lines, and signals
       an unprocessed edge to the original mail field selector. */
    fresh((const unsigned char *)"AAAA\xCDiiiiiiiiiiii\xCD" "AAAA", 22);
    ed.index = 2; af_pixel_position(&ed, &ed.column, &ed.row, ed.index);
    af_pixel_down(&ed); assert(ed.index == 11 && ed.processed); /* 12px -> six i glyphs. */
    ed.processed = 0; af_pixel_up(&ed); assert(ed.index == 2 && ed.processed);
    ed.processed = 0; af_pixel_up(&ed); assert(ed.index == 2 && !ed.processed);
    ed.index = ed.length; af_pixel_down(&ed); assert(ed.length == 23 && ed.input[22] == 0xCD);
    assert(ed.command == AF_GRID_INSERT);

    /* Draft rendering and the saved read path emit identical body spans. */
    memset(text, 'A', sizeof(text)); text[20] = 0xCD; fresh(text, 96);
    memcpy(snapshot, board, sizeof(board));
    af_pixel_notice_body(menu.bytes, &ed, ed.input, ed.length, 63, 63, &ex, &ey);
    assert(draw_count == 4 && draws[0].length == 20 && draws[1].length == 32 && draws[2].length == 32);
    assert(draws[3].length == 11 && draws[3].y == 111 && ex == -31 && ey == 9);
    draw_count = 0; draw_y = 63;
    af_mail_read_body(&submenu, menu.bytes, &ed, 63, &draw_y, &ex, &ey, (const unsigned char *)"abc");
    assert(draw_count == 4 && draws[3].length == 11 && draw_y == 159);
    assert(!memcmp(snapshot, board, sizeof(board)));
    ed.index = 37; af_pixel_position(&ed, &ed.column, &ed.row, ed.index);
    af_pixel_notice_cursor(&submenu, &ed, 100+(float)ed.column*12, 80);
    assert(cursor_x == 196 && cursor_y == 80);
    af_pixel_letter_cursor(&submenu, &ed, 0, 0);
    assert(cursor_x == -96 && cursor_y == 0 && letter_calls == 1);
    board[0] = 2; board[7] = 4; memcpy(board+0x9C, "AiI'", 4); ed.index = ed.column = 2;
    af_pixel_letter_cursor(&submenu, &ed, 0, 0); assert(cursor_x == 20);
    board[0] = 0; af_pixel_letter_cursor(&submenu, &ed, 17, 19); assert(cursor_x == 17 && cursor_y == 19);

    /* A native field switch changes ed.input; the keyboard must keep ownership
       only when the pointer is exactly that selected board field. */
    memset(&af_grid_context, 0, sizeof(af_grid_context));
    af_grid_context.submenu = &submenu; af_grid_context.menu = menu.bytes;
    af_grid_context.editor = &ed; af_grid_context.input = board+0x3C;
    for (i = 0; i < 3; ++i) {
        board[0] = (unsigned char)i; ed.input = board+(i == 0 ? 0x32 : i == 1 ? 0x3C : 0x9C);
        movement = 0; af_pixel_grid_input(&submenu);
        assert(af_grid_owned(&submenu) && !af_grid_context.error && !sounds);
    }
    movement = 1; af_pixel_grid_input(&submenu); assert(sounds == 1);
    movement = 2; af_pixel_grid_input(&submenu); assert(sounds == 2);
    movement = 0; af_pixel_grid_input(&submenu); assert(sounds == 2 && input_calls == 6);
    ed.input = text; af_pixel_grid_input(&submenu);
    assert(af_grid_context.error && af_grid_context.input != text && sounds == 2);
    return 0;
}
