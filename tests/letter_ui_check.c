#include <assert.h>
#include <string.h>
#include "../overlays/letter_ui/ui.h"

extern void af_ui_board_init(void *);
extern void af_ui_address_draw(void *, const unsigned char *, int, float, float,
                              int, int, int, int, int, int, float, float, int);
extern void af_ui_prompt_draw(void *, const unsigned char *, int, float, float,
                             int, int, int, int, int, int, float, float, int);
static int lookup_ok = 1, lookups, init_calls, draw_length;
static unsigned int identity, mode;
static unsigned char board[192], drawn[64];
static float drawn_x;

int af_ui_load_name(unsigned char *out, unsigned int size, unsigned int code) {
    assert(size == 8); identity = code; ++lookups;
    assert(code == 0xE084 || code == 0xE08C);
    memcpy(out, code == 0xE084 ? "Limberg " : "Buzz    ", 8); return lookup_ok;
}
int af_ui_width(unsigned int code, int ignored) { (void)ignored; return code == 'i' ? 2 : 6; }
void af_ui_draw(void *game, const unsigned char *text, int length, float x, float y,
                int r, int g, int b, int a, int shadow, int proportional, float sx, float sy, int kind) {
    (void)game; (void)y; (void)r; (void)g; (void)b; (void)a;
    (void)shadow; (void)proportional; (void)sx; (void)sy; (void)kind;
    assert(length >= 0 && length <= 64); memcpy(drawn, text, (unsigned int)length);
    draw_length = length; drawn_x = x;
}
void af_ui_original_board_init(void *submenu) { assert(submenu); ++init_calls; }
void af_ui_test_state(void *submenu, unsigned char **out, unsigned int *kind) {
    assert(submenu); *out = board; *kind = mode;
}

static void original_defaults(const unsigned char *name) {
    unsigned int first = 0, end = 6;
    memset(board, 0, sizeof(board)); memset(board+0x32, ' ', 122);
    memcpy(board+0x1A, name, 6);
    memcpy(board+0x32, "\x0A\xC3\x1C", 3); board[5] = 3;
    while (end && name[end-1] == ' ') --end;
    while (first < end && name[first] == ' ') ++first;
    memcpy(board+0x9C, name+first, end-first);
    memcpy(board+0x9C+end-first, "\x60\x7C", 2);
    board[7] = (unsigned char)(end+2);
}

int main(void) {
    unsigned char saved[18] = {0}, before[192], name[8], original[18];
    unsigned int i;
    memcpy(saved, "\x7B\xCE\xCB\x03  ", 6); saved[0xC] = 132; saved[0x10] = 1;
    memcpy(original, saved, sizeof(saved));
    assert(af_ui_address_name(name, saved) == 8);
    assert(memcmp(name, "Limberg ", 8) == 0 && identity == 0xE084);
    assert(memcmp(saved, original, 18) == 0);
    /* A canonical museum identity must not depend on its saved Japanese name. */
    saved[0x10] = 2; memcpy(original, saved, sizeof(saved)); i = (unsigned int)lookups;
    assert(af_ui_address_name(name, saved) == 6 && memcmp(name, "Museum", 6) == 0);
    assert(memcmp(saved, original, 18) == 0 && (unsigned int)lookups == i);
    saved[0x10] = 7;
    assert(af_ui_address_name(name, saved) == 6 && memcmp(name, saved, 6) == 0);
    assert((unsigned int)lookups == i);
    saved[0x10] = 1;
    /* A correct stored NPC name remains the same visible English name. */
    memcpy(saved, "Buzz  ", 6); saved[0xC] = 140;
    assert(af_ui_address_name(name, saved) == 8 && memcmp(name, "Buzz    ", 8) == 0);
    lookup_ok = 0;
    assert(af_ui_address_name(name, saved) == 6 && memcmp(name, saved, 6) == 0);
    lookup_ok = 1; saved[0x10] = 0; memcpy(saved, "Player", 6); i = (unsigned int)lookups;
    assert(af_ui_address_name(name, saved) == 6 && memcmp(name, "Player", 6) == 0);
    assert((unsigned int)lookups == i);
    saved[0x10] = 1; saved[0xC] = 216;
    assert(af_ui_address_name(name, saved) == 6 && (unsigned int)lookups == i);
    saved[0xC] = 132;
    af_ui_address_draw(0, saved, 6, 70, 80, 1, 2, 3, 255, 0, 0, .75f, .75f, 0);
    assert(draw_length == 8 && memcmp(drawn, "Limberg ", 8) == 0);

    const unsigned char prompt[12] = {0x1E,0xEE,0x19,0x00,0x12,0x14,0xC2,0x97,0xB2,0x12,0x17,0x21};
    const unsigned char empty[12] = {0x91,0xDC,0xBA,0x9D,0x10,0xCB,0x02,0xE7,0x96,0xB7,0xF4,0x0C};
    int length = 12;
    assert(memcmp(af_ui_prompt(prompt, &length), "Choose an addressee.", 20) == 0 && length == 20);
    length = 12;
    assert(memcmp(af_ui_prompt(empty, &length), "Your address book is empty!", 27) == 0 && length == 27);
    length = 6; assert(af_ui_prompt(saved, &length) == saved && length == 6);
    af_ui_prompt_draw(0, prompt, 12, 88, 112, 80, 80, 230, 255, 0, 0, 1, 1, 0);
    assert(draw_length == 20 && drawn_x == 100.0f);

    const unsigned char *names[] = {(const unsigned char *)"Xena  ", (const unsigned char *)"Longer",
        (const unsigned char *)" Xena ", (const unsigned char *)"      "};
    for (i = 0; i < 4; ++i) {
        unsigned int end = 6;
        while (end && names[i][end-1] == ' ') --end;
        original_defaults(names[i]); memcpy(before, board, 192); mode = i & 1 ? 2 : 0;
        af_ui_board_init(board);
        assert(board[5] == 3 && board[0x2F] == 3 && memcmp(board+0x32, "To ", 3) == 0);
        assert(board[7] == 5+end && memcmp(board+0x9C, "from ", 5) == 0);
        assert(memcmp(board+0xA1, names[i], end) == 0);
        assert(memcmp(board+8, before+8, 0x27) == 0); /* All identities and metadata. */
        assert(memcmp(board+0x3C, before+0x3C, 96) == 0);
        assert(memcmp(board+0xAC, before+0xAC, 20) == 0);
        memcpy(before, board, 192); af_ui_defaults(board, mode); assert(memcmp(board, before, 192) == 0);
    }
    assert(init_calls == 4);
    for (i = 1; i <= 5; i += 2) {
        original_defaults(names[0]); memcpy(before, board, 192);
        af_ui_defaults(board, i); assert(memcmp(board, before, 192) == 0);
    }
    original_defaults(names[0]); memcpy(board+0x32, "Hi there! ", 10); board[0x2F] = 2;
    memcpy(board+0x9C, "Custom signoff! ", 16); memcpy(before, board, 192);
    af_ui_defaults(board, 0); assert(memcmp(board, before, 192) == 0);
    af_ui_defaults(0, 0); assert(!af_ui_address_name(0, saved));
    return 0;
}
