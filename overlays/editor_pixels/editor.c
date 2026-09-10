#include "layout.h"
#include "../keyboard_grid/editor.h"
#include "state.h"

extern void af_pixel_original_position(struct af_hboard_native_editor *, short *, short *, int);
extern void af_pixel_original_up(struct af_hboard_native_editor *);
extern void af_pixel_original_down(struct af_hboard_native_editor *);
extern void af_pixel_native_insert(struct af_hboard_native_editor *);
extern void af_pixel_sound(unsigned int);

static int multiline(const struct af_hboard_native_editor *ed) {
    /* Native modes 0 (mail body) and 2 (notice draft) alone use 16 by 6.
       Gyroid drafts use 32 by 4; names, headers, footers, and apologies one row. */
    return ed && ed->columns == 16 && ed->rows == 6 && ed->input;
}

void af_pixel_position(struct af_hboard_native_editor *ed, short *column, short *row, int index) {
    struct af_edit_point point;
    unsigned int length;
    if (!multiline(ed)) { af_pixel_original_position(ed, column, row, index); return; }
    if (!column || !row) return;
    /* Native insertion temporarily substitutes its bounded proposed-text buffer
       and asks for length+1 before updating ed->length. */
    length = ed->length < index ? (unsigned int)index : (unsigned int)ed->length;
    if (af_edit_position(ed->input, length, (unsigned int)index, &point)) {
        *column = (short)point.column; *row = (short)point.row;
    } else { *column = 0; *row = 6; }
}

static void vertical(struct af_hboard_native_editor *ed, int direction) {
    struct af_edit_point here, end;
    int next;
    if (!af_edit_position(ed->input, (unsigned int)ed->length, (unsigned int)ed->index, &here)
            || !af_edit_position(ed->input, (unsigned int)ed->length, (unsigned int)ed->length, &end)) return;
    if ((direction < 0 && here.row) || (direction > 0 && here.row < end.row)) {
        next = af_edit_nearest(ed->input, (unsigned int)ed->length,
                              (unsigned int)((int)here.row+direction), here.x);
        if (next >= 0) { ed->index = (short)next; ed->processed = 1; }
    } else if (direction > 0 && ed->index == ed->length) {
        ed->code = 0xCD;
        af_pixel_native_insert(ed);
        if (ed->processed) ed->command = AF_GRID_INSERT;
    }
    /* An unsuccessful edge move deliberately remains unprocessed: the native
       mail dispatcher uses that result to select the header/body/footer. */
}

void af_pixel_up(struct af_hboard_native_editor *ed) {
    if (multiline(ed)) vertical(ed, -1); else af_pixel_original_up(ed);
}
void af_pixel_down(struct af_hboard_native_editor *ed) {
    if (multiline(ed)) vertical(ed, 1); else af_pixel_original_down(ed);
}

void af_pixel_grid_input(void *submenu) {
    struct af_grid_context *ctx = &af_grid_context;
    unsigned char *ovl, *board, *expected = 0;
    unsigned int old_page, old_upper, old_order;
    if (submenu && ctx->submenu == submenu && ctx->menu && ctx->editor) {
        ovl = ((struct af_hboard_submenu_pointer *)submenu)->overlay;
        if (ovl && *(int *)((unsigned char *)ctx->menu+0x38) == 0 &&
                af_pixel_state(submenu, 0x106E0) == ctx->editor) {
            board = af_pixel_state(submenu, 0x106E4);
            if (board && board[0] < 3u) {
                expected = board+(board[0] == 0 ? 0x32 : board[0] == 1 ? 0x3C : 0x9C);
                if (ctx->editor->input == expected) ctx->input = expected;
            }
        }
    }
    old_page = ctx->state.page; old_upper = ctx->state.upper; old_order = ctx->state.alphabetical;
    af_grid_editor_input(submenu);
    if (af_grid_owned(submenu) && (ctx->state.moved || ctx->state.page != old_page ||
            ctx->state.upper != old_upper || ctx->state.alphabetical != old_order))
        af_pixel_sound(0x32u);
    /* Successful typing/delete/Done/caret feedback remains the native processed
       command handler. Do not play it again from the key-selection wrapper. */
}
