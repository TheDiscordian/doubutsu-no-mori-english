/* Display-only English recipients and matching header editing geometry. */
#ifndef AF_LETTER_NPC_COUNT
#define AF_LETTER_NPC_COUNT 216u
#endif
extern int af_load_display_name(unsigned char *, unsigned int, unsigned int);
extern int af_letter_code_width(unsigned int, int);
extern void af_mail_draw(void *, const unsigned char *, unsigned int, float, float, const unsigned char *);
extern void af_letter_native_cursor(void *, void *, float, float);
extern void af_letter_native_point(void *, void *, float, float);

#ifdef __mips__
static unsigned char *state(void *submenu, unsigned int at) {
    unsigned char *overlay = *(unsigned char **)((unsigned char *)submenu+0x2C);
    return overlay ? *(unsigned char **)(overlay+at) : 0;
}
static void cursor(void *submenu, void *game, unsigned char *editor, float x, float y) {
    ((void (*)(void *, void *, float, float))*(unsigned int *)(editor+0x2C))(submenu, game, x, y);
}
#else
extern unsigned char *af_letter_test_state(void *, unsigned int);
extern void af_letter_test_cursor(void *, void *, unsigned char *, float, float);
#define state af_letter_test_state
#define cursor af_letter_test_cursor
#endif

unsigned int af_letter_prefix_width(const unsigned char *text, unsigned int length) {
    unsigned int width = 0;
    if (!text || length > 10u) return 0;
    while (length--) width += af_letter_code_width(*text++, 0);
    return width;
}

void af_letter_header(void *submenu, void *game, void *menu, float x, float y,
                      const unsigned char *colour) {
    unsigned char *board, name[8], header[18];
    unsigned int i, length, split, size, playing;
    static const unsigned char red[3] = {185, 0, 0};
    if (!submenu || !game || !menu || !colour) return;
    board = state(submenu, 0x106E4);
    if (!board) return;
    playing = *(unsigned int *)((unsigned char *)menu+4) == 1u;
    length = board[5]; split = board[0x2F];
    if (length > 10u || split > length || board[3] > 6u) return;
    if (!playing && (board[0x30] == 2u || board[0x30] == 3u || board[0x30] == 5u)) {
        af_mail_draw(game, board+0x32, 10, x, y, colour);
        return;
    }
    size = playing && !board[0] ? 6u : board[3];
    for (i = 0; i < 8u; ++i) name[i] = i < 6u ? board[8+i] : ' ';
#ifdef AF_MUSEUM_HEADER
    /* Enabled by the current incremental installer; keep baseline ABI builds reproducible. */
    if (board[0x18] == 2u) {
        static const unsigned char museum[] = "Museum";
        size = 6;
        for (i = 0; i < size; ++i) name[i] = museum[i];
    } else
#endif
    if (board[0x18] == 1u && board[0x14] < AF_LETTER_NPC_COUNT
            && af_load_display_name(name, 8, 0xE000u|board[0x14])) {
        size = 8;
        if (board[0] || !playing) while (size && name[size-1u] == ' ') --size;
    }
    if (!playing) {
        /* New-letter initialization need not reset the persistent read cache.
           Compose only from this board, even if its heap address is reused. */
        for (i = 0; i < split; ++i) header[i] = board[0x32+i];
        for (i = 0; i < size; ++i) header[split+i] = name[i];
        for (i = split; i < length; ++i) header[size+i] = board[0x32+i];
        if (length+size) af_mail_draw(game, header, length+size, x, y, colour);
        return;
    }
    af_mail_draw(game, board+0x32, split, x, y, colour);
    x += (float)af_letter_prefix_width(board+0x32, split);
    af_mail_draw(game, name, size, x, y, red);
    if (split < 10u)
        af_mail_draw(game, board+0x32+split, length-split, x+80.0f, y, colour);
}

void af_letter_cursor(void *submenu, void *game, float x, float y) {
    unsigned char *board, *editor;
    int column;
    if (!submenu || !game) return;
    board = state(submenu, 0x106E4); editor = state(submenu, 0x106E0);
    if (!board || !editor) return;
    if (board[0]) {
        af_letter_native_cursor(submenu, game, x, y);
        return;
    }
    if (board[2] == 1u) {
        unsigned int split = board[0x2F];
        if (split > 10u) return;
        /* Retain the native marker graphics and their GC-matching 36px origin. */
        x += (float)af_letter_prefix_width(board+0x32, split)-(float)(split*12u);
        af_letter_native_point(submenu, game, x, y);
        return;
    }
    column = *(short *)(editor+0x20)-1;
    if (column < 0 || column > 10) return;
    x += 57.0f+(float)af_letter_prefix_width(board+0x32, (unsigned int)column);
    if (board[2] == 2u) x += 80.0f;
    cursor(submenu, game, editor, x, 36.0f-y);
}
