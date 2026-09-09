#ifndef AF_MAIL_GLYPH_H
#define AF_MAIL_GLYPH_H

#define AF_MAIL_GLYPH_CATALOG_ID 4u

/* Exact advances of the separately bound fourteen-cell font. The template
 * parser opts in by catalogue; literal saved fields remain single-byte text.
 */
static inline unsigned int af_mail_glyph_width(unsigned int code) {
    static const unsigned char codes[14] = {
        0xD0,0xAE,0xA7,0xAB,0xBA,0x2A,0x3B,0x5C,0x60,0x7C,0xBF,0xF7,0x08,0x0A
    };
    unsigned int i;
    for (i = 0; i < 14u; ++i)
        if (codes[i] == code)
            return !i ? 3u : (0x04DCu >> i) & 1u ? 12u : 6u;
    return 0;
}

static inline unsigned int af_mail_glyph_upper(unsigned int code) {
    return code == 0x60u ? 0x08u : code == 0x7Cu ? 0x0Au : code;
}

#endif
