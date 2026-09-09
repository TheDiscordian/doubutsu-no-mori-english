#include "view.h"
#include "glyph.h"

#ifdef __mips__
static unsigned char *board(void *submenu) {
    unsigned char *overlay = *(unsigned char **)((unsigned char *)submenu+0x2C);
    return *(unsigned char **)(overlay+0x106E4);
}
static int code_width(unsigned char code) {
    return ((int (*)(unsigned int, int))0x8009028Cu)(code, 0);
}
#else
extern unsigned char *af_mail_view_test_board(void *);
extern int af_mail_view_test_width(unsigned char);
extern void af_mail_view_test_draw(void *, const unsigned char *, unsigned int,
                                   float, float, const unsigned char *);
#define board af_mail_view_test_board
#define code_width af_mail_view_test_width
#endif

void af_mail_draw(void *game, const unsigned char *text, unsigned int length,
                   float x, float y, const unsigned char *colour) {
#ifdef __mips__
    ((float (*)(void *, const unsigned char *, int, float, float,
                int, int, int, int, int, int, float, float, int))0x80090E98u)
        (game, text, length, x, y, colour[0], colour[1], colour[2], 255, 0, 0, 1.0f, 1.0f, 0);
#else
    af_mail_view_test_draw(game,text,length,x,y,colour);
#endif
}
#define draw af_mail_draw

int af_mail_next_line(AfMailLine *line, const unsigned char *text, unsigned int length) {
    AfMailLine result = {0, 0, 0, 0};
    int advance;
    unsigned int size;
    if (!line || !text || length > 1024u)
        return 0;
    while (result.consumed < length) {
        if (text[result.consumed] == 0xCDu) {
            ++result.consumed;
            result.newline = 1;
            break;
        }
        size = 1;
        if (text[result.consumed] == 0x80u) {
            if (result.consumed+1u == length)
                return 0;
            advance = (int)af_mail_glyph_width(text[result.consumed+1u]);
            size = 2;
        } else {
            advance = code_width(text[result.consumed]);
        }
        if (advance <= 0 || advance > 192)
            return 0;
        if (result.width+(unsigned int)advance > 192u)
            break;
        result.width += (unsigned int)advance;
        result.drawn += size;
        result.consumed += size;
    }
    *line = result;
    return 1;
}

void af_mail_read_body(void *submenu, void *menu, void *game, float x,
                       float *y, float *end_x, float *end_y, const unsigned char *colour) {
    const unsigned char *text;
    unsigned char *state;
    AfMailLine lines[6];
    unsigned int length, used = 0, i;
    (void)menu;
    if (!submenu || !game || !y || !end_x || !end_y || !colour)
        return;
    state = board(submenu);
    if (!state || state[6] > 96u)
        return;
    text = state+0x3C;
    length = state[6];
    /* Validate all visible lines before emitting any graphics. */
    for (i = 0; i < 6u; ++i) {
        if (!af_mail_next_line(&lines[i], text+used, length-used))
            return;
        used += lines[i].consumed;
    }
    used = 0;
    for (i = 0; i < 6u; ++i) {
        AfMailLine *line = &lines[i];
        if (line->drawn)
            draw(game, text+used, line->drawn, x, *y, colour);
        used += line->consumed;
        if (used == length && line->consumed) {
            int next = i < 5u && (line->newline || line->width == 192u);
            *end_x = x+1.0f+(next ? 0.0f : (float)line->width)-160.0f;
            *end_y = 120.0f-(*y+(next ? 16.0f : 0.0f));
        }
        *y += 16.0f;
    }
}

void af_mail_read_footer(void *submenu, void *game, float x, float y,
                         const unsigned char *colour) {
    unsigned char *state;
    AfMailLine line;
    if (!submenu || !game || !colour)
        return;
    state = board(submenu);
    if (!state || state[7] > 16u)
        return;
    if (!af_mail_next_line(&line,state+0x9C,state[7]) || line.drawn != state[7])
        return;
    if (state[7])
        draw(game, state+0x9C, state[7], x+192.0f-(float)line.width, y, colour);
}
