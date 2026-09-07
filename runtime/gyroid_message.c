/* Measured wrapping for the gyroid's owner message, not stored Mail_c text. */
#ifdef __mips__
static int code_width(unsigned char code) {
    return ((int (*)(unsigned int, int))0x8009028Cu)(code, 1);
}
#else
extern int af_gyroid_test_width(unsigned char);
#define code_width af_gyroid_test_width
#endif

void af_set_gyroid_message(void *window, int slot, const unsigned char *source, int length) {
    unsigned char output[68];
    unsigned char *destination;
    int used = 0, rows = 0, width = 0, i;
    if (!window || slot != 0 || !source)
        return;
    if (length > 68)
        length = 68;
    for (i = 0; i < length && used < 68 && rows < 5; ++i) {
        unsigned char code = source[i];
        output[used++] = code;
        if (code == 0xCDu) {
            width = 0;
            ++rows;
        } else {
            int advance = code_width(code);
            if (advance <= 0 || advance > 12)
                return;
            width += advance;
            /* GAFE01 tests width after appending the glyph, strictly >186.
             * Do not move words, trim spaces, or replace explicit newlines.
             */
            if (used < 68 && width > 186) {
                output[used++] = 0xCDu;
                width = 0;
                ++rows;
            }
        }
    }
    while (used < 68)
        output[used++] = ' ';
    /* Stage before publishing: overlapping source/destination is also safe. */
    destination = (unsigned char *)window+0x132;
    for (i = 0; i < 68; ++i)
        destination[i] = output[i];
}
