#include "reader.h"
#include "view.h"
#include "../display_name.h"

AfMailReader af_mail_reader;

#ifdef __mips__
static unsigned char *board(void *submenu) {
    unsigned char *overlay = *(unsigned char **)((unsigned char *)submenu+0x2C);
    return *(unsigned char **)(overlay+0x106E4);
}
static void copy_mail(unsigned char *destination, const unsigned char *source) {
    ((void (*)(void *, const void *))0x8009C67Cu)(destination, source);
}
static unsigned int trigger(void) {
    return ((unsigned int (*)(void))0x80078DF4u)();
}
static int width(unsigned char code) {
    return ((int (*)(unsigned int, int))0x8009028Cu)(code, 0);
}
static void draw(void *game, const unsigned char *text, unsigned int length,
                 float x, float y, const unsigned char *colour) {
    ((float (*)(void *, const unsigned char *, int, float, float,
                int, int, int, int, int, int, float, float, int))0x80090E98u)
        (game, text, length, x, y, colour[0], colour[1], colour[2], 255, 0, 0, 1.0f, 1.0f, 0);
}
#else
extern unsigned char *af_mail_view_test_board(void *);
extern void af_mail_reader_test_copy(unsigned char *, const unsigned char *);
extern unsigned int af_mail_reader_test_trigger(void);
extern int af_mail_view_test_width(unsigned char);
extern void af_mail_view_test_draw(void *, const unsigned char *, unsigned int, float, float, const unsigned char *);
#define board af_mail_view_test_board
#define copy_mail af_mail_reader_test_copy
#define trigger af_mail_reader_test_trigger
#define width af_mail_view_test_width
#define draw af_mail_view_test_draw
#endif

static int active(const void *state) {
    return state && af_mail_reader.status && af_mail_reader.owner == state;
}

/* The native mail identity packs the villager index into byte 0C and its
 * palette into 0D. Only recipient type one uses that representation. Resolve
 * the immutable English name for display; never rewrite the saved identity.
 */
static unsigned int header_name(unsigned char *destination, const unsigned char *mail, unsigned int length) {
    unsigned int i;
    if (mail[0x10] == 1u && mail[0x0C] < AF_VILLAGER_COUNT &&
            af_load_display_name(destination, AF_DISPLAY_NAME_WIDTH, 0xE000u|mail[0x0C]))
        length = AF_DISPLAY_NAME_WIDTH;
    else
        for (i = 0; i < length; ++i) destination[i] = mail[i];
    while (length && destination[length-1u] == ' ') --length;
    return length;
}

static int select_page(unsigned int number) {
    AfMailReader *r = &af_mail_reader;
    const unsigned char *parts[3] = {r->header, r->letter.text+r->letter.offsets[1],
                                    r->letter.text+r->letter.offsets[2]};
    if (!af_mail_page(&r->layout, parts, r->lengths, number))
        return 0;
    r->page = number;
    r->total = r->layout.total;
    return 1;
}

static void error_letter(void) {
    static const unsigned char message[] = "Unable to read this letter.";
    unsigned int i;
    AfMailReader *r = &af_mail_reader;
    r->lengths[0] = r->lengths[2] = 0;
    r->lengths[1] = sizeof(message)-1u;
    r->letter.offsets[1] = r->letter.offsets[2] = 0;
    for (i = 0; i < sizeof(message)-1u; ++i)
        r->letter.text[i] = message[i];
    r->status = 2;
    select_page(0);
}

void af_mail_reader_copy(unsigned char *destination, const unsigned char *source, void *menu) {
    AfMailReader *r = &af_mail_reader;
    unsigned int i, name, split, length, type;
    if (!destination || !source || !menu)
        return;
    r->status = r->page = r->total = 0;
    r->owner = 0;
    copy_mail(destination, source);
    if (source[0x27] != AF_MAIL_SNAPSHOT_SPLIT)
        return;
    /* The hooked call is inside board initialization, before any scans or
     * footer normalization. Opaque bytes never reach those native routines.
     * Generated snapshots remain read-only until lossless editing is connected.
     */
    *(unsigned int *)((unsigned char *)menu+0x38) = 1;
    r->owner = destination-8;
    if (source[0x26] == 255u || !af_mail_restore(&r->letter, source+0x2A, 122, &r->workspace)) {
        error_letter();
    } else {
        type = source[0x28];
        length = r->letter.lengths[0];
        split = r->letter.header_split;
        if (split > length || length+AF_DISPLAY_NAME_WIDTH > sizeof(r->header)) {
            error_letter();
        } else {
            name = (type == 2u || type == 3u || type == 5u) ? 0u : header_name(r->header+split,source,6);
            for (i = 0; i < split; ++i)
                r->header[i] = r->letter.text[r->letter.offsets[0]+i];
            for (i = split; i < length; ++i)
                r->header[name+i] = r->letter.text[r->letter.offsets[0]+i];
            r->lengths[0] = length+name;
            r->lengths[1] = r->letter.lengths[1];
            r->lengths[2] = r->letter.lengths[2];
            r->status = 1;
            if (!select_page(0))
                error_letter();
        }
    }
    destination[0x27] = 0;
    for (i = 0x2A; i < 164u; ++i)
        destination[i] = ' ';
}

unsigned int af_mail_reader_trigger(void *submenu, void *menu) {
    unsigned int buttons = trigger(), page = af_mail_reader.page;
    if (submenu && menu && *(unsigned int *)((unsigned char *)menu+0x38) == 1u
            && active(board(submenu)) && af_mail_reader.total > 1u && !(buttons & 0xD000u)) {
        if ((buttons & 0x0200u) && page)
            select_page(page-1u);
        else if ((buttons & 0x0100u) && page+1u < af_mail_reader.total)
            select_page(page+1u);
    }
    return buttons;
}

static unsigned int decimal(unsigned char *destination, unsigned int number) {
    unsigned char reverse[4];
    unsigned int count = 0, i;
    do {
        reverse[count++] = (unsigned char)('0'+number%10u);
        number /= 10u;
    } while (number);
    for (i = 0; i < count; ++i)
        destination[i] = reverse[count-1u-i];
    return count;
}

void af_mail_snapshot_header(void *submenu, void *game, void *menu, float x,
                             float y, const unsigned char *colour) {
    unsigned char *state, header[18], hint[24];
    unsigned int i, j, split, name, length, pixels;
    const unsigned char *text;
    AfMailReader *r = &af_mail_reader;
    (void)menu;
    if (!submenu || !game || !colour)
        return;
    state = board(submenu);
    if (!state)
        return;
    if (!active(state)) {
        length = state[5];
        split = state[0x2F];
        name = state[3];
        if (length > 10u || split > length || name > 6u)
            return;
        if (state[0x30] == 2u || state[0x30] == 3u || state[0x30] == 5u) {
            draw(game, state+0x32, 10, x, y, colour);
            return;
        }
        name = header_name(header+split,state+8,name);
        for (i = 0; i < split; ++i) header[i] = state[0x32+i];
        for (i = split; i < length; ++i) header[name+i] = state[0x32+i];
        if (length+name) draw(game, header, length+name, x, y, colour);
        return;
    }
    for (i = 0; i < r->layout.count; ++i) {
        const AfMailSpan *s = &r->layout.spans[i];
        text = s->section ? r->letter.text+r->letter.offsets[s->section] : r->header;
        text += s->offset;
        pixels = 0;
        if (s->section == 2u)
            for (j = 0; j < s->length; ++j) pixels += (unsigned int)width(text[j]);
        if (s->length)
            draw(game, text, s->length, s->section == 2u ? x+192.0f-(float)pixels : x,
                 y+(float)s->y, colour);
    }
    if (r->total > 1u) {
        static const unsigned char prefix[] = "Left/Right: ";
        for (i = 0; i < sizeof(prefix)-1u; ++i) hint[i] = prefix[i];
        i += decimal(hint+i, r->page+1u);
        hint[i++] = '/';
        i += decimal(hint+i, r->total);
        draw(game, hint, i, x, y+164.0f, colour);
    }
}

void af_mail_snapshot_body(void *submenu, void *menu, void *game, float x,
                           float *y, float *end_x, float *end_y, const unsigned char *colour) {
    if (!submenu || !y)
        return;
    if (active(board(submenu)))
        *y += 96.0f;
    else
        af_mail_read_body(submenu, menu, game, x, y, end_x, end_y, colour);
}

void af_mail_snapshot_footer(void *submenu, void *game, float x, float y,
                             const unsigned char *colour) {
    if (!submenu)
        return;
    if (!active(board(submenu)))
        af_mail_read_footer(submenu, game, x, y, colour);
}
