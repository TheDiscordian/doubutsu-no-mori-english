#include "accent_mail.h"
#ifdef __mips__
static int code_width(unsigned char code) {
    return ((int (*)(unsigned int,int))0x8009028Cu)(code,0);
}
#else
extern int af_mail_view_test_width(unsigned char);
#define code_width af_mail_view_test_width
#endif

int af_accent_next_line(AfMailLine *line, const unsigned char *text, unsigned int length) {
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
            advance = (int)af_accent_glyph_width(text[result.consumed+1u],AF_ACCENT_CATALOG_ID);
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
