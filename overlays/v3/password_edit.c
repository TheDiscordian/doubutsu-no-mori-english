/* Two separate fourteen-character rows, matching mED_*pw_chk in GAFE01-r0. */
#include "password_editor.h"

static int code_character(unsigned int code) {
    return (code >= 'A' && code <= 'Z') || (code >= 'a' && code <= 'z') ||
        (code >= '0' && code <= '9') || code == '%' || code == '&' || code == '#' || code == '@';
}

int af_pw_edit(struct AfPasswordDraft *d, int command, unsigned int code) {
    unsigned char *row;
    int i;
    if (!d || d->line > 1 || d->cursor > 14 || d->finished)
        return AF_PW_EDIT_REJECT;
    row = d->text + 14*d->line;
    switch (command) {
    case AF_GRID_NONE: return AF_PW_EDIT_NONE;
    case AF_GRID_RIGHT:
        if (d->cursor == 14) return AF_PW_EDIT_REJECT;
        ++d->cursor; break;
    case AF_GRID_LEFT:
        if (!d->cursor) return AF_PW_EDIT_REJECT;
        --d->cursor; break;
    case AF_GRID_UP:
    case AF_GRID_DOWN:
        if (d->line == (command == AF_GRID_DOWN)) return AF_PW_EDIT_NONE;
        d->line = command == AF_GRID_DOWN; break;
    case AF_GRID_BACKSPACE:
        if (d->cursor) {
            --d->cursor;
            for (i=d->cursor; i<13; ++i) row[i]=row[i+1];
            row[13]=' ';
        } else if (d->line) {
            d->line=0; d->cursor=13; d->text[13]=' ';
        } else return AF_PW_EDIT_NONE;
        break;
    case AF_GRID_INSERT:
        if ((!code_character(code) && code != ' ') || row[13] != ' ' || d->cursor >= 14)
            return AF_PW_EDIT_REJECT;
        for (i=13; i>d->cursor; --i) row[i]=row[i-1];
        row[d->cursor++]=(unsigned char)code;
        if (d->cursor==14 && !d->line) { d->line=1; d->cursor=0; }
        break;
    case AF_GRID_DONE:
        /* The donor treats an unfinished second row as cancellation. */
        if (d->text[27] != ' ')
            for (i=0; i<28; ++i)
                if (!code_character(d->text[i])) return AF_PW_EDIT_REJECT;
        d->finished=1; return AF_PW_EDIT_DONE;
    default: return AF_PW_EDIT_REJECT;
    }
    return AF_PW_EDIT_CHANGED;
}
