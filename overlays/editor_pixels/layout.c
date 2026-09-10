#include "layout.h"

unsigned int af_edit_width(const unsigned char *text, unsigned int length) {
    AfMailLine line;
    if (!af_mail_next_line(&line, text, length) || line.consumed != length) return 0;
    return line.width;
}

int af_edit_position(const unsigned char *text, unsigned int length, unsigned int index,
                     struct af_edit_point *point) {
    AfMailLine line;
    unsigned int row, start = 0, end, column;
    if (!text || !point || length > 96u || index > length) return 0;
    for (row = 0; row < 6u; ++row) {
        if (!af_mail_next_line(&line, text+start, length-start)) return 0;
        end = start+line.consumed;
        if (index < end || (end == length && index == end &&
                (row == 5u || (!line.newline && line.width != 192u)))) {
            column = index-start;
            point->start = start; point->column = column; point->row = row;
            point->x = af_edit_width(text+start, column > line.drawn ? line.drawn : column);
            return 1;
        }
        start = end;
    }
    return 0;
}

int af_edit_nearest(const unsigned char *text, unsigned int length, unsigned int row,
                    unsigned int x) {
    AfMailLine line;
    struct af_edit_point point;
    unsigned int start = 0, current, i, width, delta, best_delta = 193u;
    int best = -1;
    if (!text || length > 96u || row >= 6u || x > 192u) return -1;
    for (current = 0; current <= row; ++current) {
        if (!af_mail_next_line(&line, text+start, length-start)) return -1;
        if (current != row) start += line.consumed;
    }
    for (i = 0; i <= line.drawn; ++i) {
        /* A wrapped end belongs to the following row, not this one. */
        if (!af_edit_position(text, length, start+i, &point) || point.row != row) continue;
        width = point.x;
        delta = width > x ? width-x : x-width;
        if (delta < best_delta) { best_delta = delta; best = (int)(start+i); }
    }
    return best;
}
