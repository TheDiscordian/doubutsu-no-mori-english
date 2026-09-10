#include "layout.h"
#include "state.h"
extern void af_letter_cursor(void *, void *, float, float);

void af_pixel_letter_cursor(void *submenu, void *game, float x, float y) {
    unsigned char *board;
    struct af_hboard_native_editor *ed;
    struct af_edit_point point;
    if (!submenu) return;
    board = af_pixel_state(submenu, 0x106E4);
    ed = af_pixel_state(submenu, 0x106E0);
    if (!board || !ed) return;
    if (board[0] == 1u) {
        if (!af_edit_position(board+0x3C, board[6], (unsigned int)ed->index, &point)) return;
        x += (float)point.x-(float)(ed->column*12);
    } else if (board[0] == 2u) {
        if (board[7] > 16u || ed->index < 0 || ed->index > board[7]) return;
        x += (float)af_edit_width(board+0x9C, (unsigned int)ed->index)-(float)(ed->column*12);
        x += (float)(board[7]*12u)-(float)af_edit_width(board+0x9C, board[7]);
    }
    af_letter_cursor(submenu, game, x, y);
}
