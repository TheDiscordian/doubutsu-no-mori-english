#include "layout.h"
#include "state.h"

void af_pixel_notice_body(void *menu, void *game, const unsigned char *text,
                           int length, float x, float y, float *end_x, float *end_y) {
    static const unsigned char colour[3] = {30, 0, 0};
    struct af_edit_point end;
    AfMailLine line;
    unsigned int row, start = 0;
    (void)menu;
    if (!game || !end_x || !end_y ||
            !af_edit_position(text, (unsigned int)length, (unsigned int)length, &end)) return;
    *end_x = x+(float)end.x-160.0f;
    *end_y = 120.0f-y-(float)end.row*16.0f;
    for (row = 0; row < 6u; ++row) {
        if (!af_mail_next_line(&line, text+start, (unsigned int)length-start)) return;
        if (line.drawn) af_mail_draw(game, text+start, line.drawn, x, y+(float)row*16.0f, colour);
        start += line.consumed;
    }
}

void af_pixel_notice_cursor(void *submenu, void *game, float x, float y) {
    struct af_hboard_native_editor *ed;
    struct af_edit_point point;
    if (!submenu) return;
    ed = af_pixel_state(submenu, 0x106E0);
    if (!ed || !ed->cursor_draw ||
            !af_edit_position(ed->input, (unsigned int)ed->length, (unsigned int)ed->index, &point)) return;
    x += (float)point.x-(float)(ed->column*12);
    ed->cursor_draw(submenu, game, x, y);
}
