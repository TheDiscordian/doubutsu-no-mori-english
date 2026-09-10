#include "ui.h"
extern void af_ui_original_board_init(void *);

void af_ui_defaults(unsigned char *board, unsigned int mode) {
    unsigned int i, first, end, footer_end, matches;
    const unsigned char *name;
    static const unsigned char to[3] = {'T','o',' '};
    static const unsigned char from[5] = {'f','r','o','m',' '};
    if (!board || (mode != 0 && mode != 2)) return;
    /* Translate only exact stock defaults in a draft. Do not migrate arbitrary
       saved mail, custom templates, recipient identities, or player names. */
    matches = board[0x2F] == 0 && board[0x32] == 0x0A &&
              board[0x33] == 0xC3 && board[0x34] == 0x1C;
    for (i = 3; i < 10; ++i) if (board[0x32+i] != ' ') matches = 0;
    if (matches) {
        for (i = 0; i < 3; ++i) board[0x32+i] = to[i];
        board[0x2F] = 3; board[5] = 3;
    }
    name = board+0x1A; /* Sender's native PersonalID, six saved name bytes. */
    end = 6;
    while (end && name[end-1] == ' ') --end;
    first = 0;
    while (first < end && name[first] == ' ') ++first;
    footer_end = end-first;
    matches = board[0x9C+footer_end] == 0x60 && board[0x9D+footer_end] == 0x7C;
    for (i = 0; i < footer_end; ++i) if (board[0x9C+i] != name[first+i]) matches = 0;
    for (i = footer_end+2; i < 16; ++i) if (board[0x9C+i] != ' ') matches = 0;
    if (matches) {
        for (i = 0; i < 16; ++i) board[0x9C+i] = ' ';
        for (i = 0; i < 5; ++i) board[0x9C+i] = from[i];
        for (i = 0; i < end; ++i) board[0xA1+i] = name[i];
        board[7] = 5+end;
    }
}

void af_ui_board_init(void *submenu) {
    unsigned char *overlay, *board;
    if (!submenu) return;
    af_ui_original_board_init(submenu);
#ifdef __mips__
    overlay = *(unsigned char **)((unsigned char *)submenu+0x2C);
    if (!overlay) return;
    board = *(unsigned char **)(overlay+0x106E4);
    af_ui_defaults(board, *(unsigned int *)(overlay+0x103E8+0x38));
#else
    extern void af_ui_test_state(void *, unsigned char **, unsigned int *);
    unsigned int mode;
    (void)overlay;
    af_ui_test_state(submenu, &board, &mode);
    af_ui_defaults(board, mode);
#endif
}
