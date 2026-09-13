#include "ui.h"

unsigned int af_ui_address_name(unsigned char *out, const unsigned char *saved) {
    unsigned int i;
    if (!out || !saved) return 0;
    out[6] = out[7] = ' ';
    /* This hook receives an entire 18-byte Mail_nm, not a loose string. */
    if (saved[0x10] == 2) {
        static const unsigned char museum[] = "Museum";
        for (i = 0; i < 6; ++i) out[i] = museum[i];
        return 6;
    }
    if (saved[0x10] == 1 && saved[0xC] < 216 &&
            af_ui_load_name(out, 8, 0xE000u | saved[0xC])) return 8;
    /* A failed lookup must not leak partially filled output into fallback. */
    for (i = 0; i < 6; ++i) out[i] = saved[i];
    return 6;
}

const unsigned char *af_ui_prompt(const unsigned char *source, int *length) {
    static const unsigned char original[2][12] = {
        {0x1E,0xEE,0x19,0x00,0x12,0x14,0xC2,0x97,0xB2,0x12,0x17,0x21},
        {0x91,0xDC,0xBA,0x9D,0x10,0xCB,0x02,0xE7,0x96,0xB7,0xF4,0x0C}
    };
    static const unsigned char choose[] = "Choose an addressee.";
    static const unsigned char empty[] = "Your address book is empty!";
    unsigned int row, i;
    if (!source || !length || *length != 12) return source;
    for (row = 0; row < 2; ++row) {
        for (i = 0; i < 12 && source[i] == original[row][i]; ++i) {}
        if (i == 12) {
            *length = row ? sizeof(empty)-1 : sizeof(choose)-1;
            return row ? empty : choose;
        }
    }
    return source;
}

void af_ui_address_draw(void *game, const unsigned char *saved, int length, float x, float y,
                         int r, int g, int b, int a, int shadow, int proportional,
                         float sx, float sy, int mode) {
    unsigned char name[8];
    if (saved && length == 6) {
        length = (int)af_ui_address_name(name, saved);
        saved = name;
    }
    af_ui_draw(game, saved, length, x, y, r, g, b, a, shadow, proportional, sx, sy, mode);
}

void af_ui_prompt_draw(void *game, const unsigned char *text, int length, float x, float y,
                        int r, int g, int b, int a, int shadow, int proportional,
                        float sx, float sy, int mode) {
    const unsigned char *english = af_ui_prompt(text, &length);
    int width = 0, i;
    if (english != text) {
        for (i = 0; i < length; ++i) width += af_ui_width(english[i], 0);
        x += 72.0f - (float)width * sx * 0.5f;
    }
    af_ui_draw(game, english, length, x, y, r, g, b, a, shadow, proportional, sx, sy, mode);
}
