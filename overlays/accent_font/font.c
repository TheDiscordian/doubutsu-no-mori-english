/* Extended glyph primitives shared by native drawing and bounded text callers.
 * No production hook or caller is installed by this compilation unit alone. */
#include "../extended_font/font.h"
#define AF_GLYPH_ACCENT_COUNT 16u

#ifdef AF_GLYPH_HOST_TEST
extern const unsigned char *af_glyph_native_texture(void);
extern unsigned int af_glyph_native_offset(unsigned int code);
#else
static const unsigned char *af_glyph_native_texture(void) {
    return (const unsigned char *)0x8013A680u;
}
static unsigned int af_glyph_native_offset(unsigned int code) {
    return code < 256u ? ((const unsigned char *)0x80106AF4u)[code] : 0u;
}
#endif

static const unsigned char codes[AF_GLYPH_ACCENT_COUNT] = {
    0xD0,0xAE,0xA7,0xAB,0xBA,0x2A,0x3B,0x5C,0x60,0x7C,0xBF,0xF7,0x08,0x0A,0x87,0x12
};
static const unsigned char *glyph_resource;
static unsigned int active_glyph; /* Zero means native; slot+1 selects a glyph. */

static unsigned int word(const unsigned char *p) {
    return ((unsigned int)p[0]<<24) | ((unsigned int)p[1]<<16)
        | ((unsigned int)p[2]<<8) | p[3];
}

int af_glyph_bind(const unsigned char *resource, unsigned int bytes) {
    unsigned int i,count;
    /* Rebinding during an active native draw would invalidate queued texture
       addresses. The owner retains the resource until every queued frame ends. */
    if (active_glyph) return 0;
    if (!resource || ((unsigned long)resource & 7u) || bytes != AF_GLYPH_BYTES || word(resource) != 0x41464758u
            || word(resource+4) != 1u || word(resource+8) != 192u
            || word(resource+12) != 16u
            || (word(resource+16) != AF_GLYPH_COUNT && word(resource+16) != AF_GLYPH_MAIL_COUNT
                && word(resource+16) != AF_GLYPH_ACCENT_COUNT)
            || word(resource+20) != AF_GLYPH_TEXTURE_OFFSET || word(resource+24) != 1536u
            || word(resource+28)) return 0;
    count = word(resource+16);
    for (i=0; i<16u; ++i) {
        if (resource[32+i] != (i<count ? codes[i] : 0u)) return 0;
        if (i<count && ((0xFB23u>>i)&1u)) {
            if (!resource[48+i] || resource[48+i]>6u) return 0;
        } else if (resource[48+i] != (i<count ? 12u : 0u)) return 0;
    }
    glyph_resource = resource;
    return 1;
}

int af_glyph_index(const unsigned char *text, unsigned int bytes) {
    unsigned int i;
    if (!glyph_resource || !text || bytes<2u || text[0]!=0x80u) return -1;
    for (i=0; i<glyph_resource[19]; ++i) if (text[1]==codes[i]) return (int)i;
    return -1;
}

unsigned int af_glyph_size(const unsigned char *text, unsigned int bytes) {
    return af_glyph_index(text, bytes)>=0 ? 2u : (bytes ? 1u : 0u);
}

unsigned int af_glyph_width(const unsigned char *text, unsigned int bytes) {
    int index;
    if (!text || !bytes) return 0;
    index = af_glyph_index(text, bytes);
    return index>=0 ? glyph_resource[48+index] : 12u-af_glyph_native_offset(text[0]);
}

int af_glyph_string_width(const unsigned char *text, unsigned int bytes) {
    unsigned int at=0, width=0;
    if (!text || bytes>1024u) return -1;
    while (at<bytes) {
        width += af_glyph_width(text+at, bytes-at);
        at += af_glyph_size(text+at, bytes-at);
    }
    /* Retail prefix-width API rounds an odd result up to an even pixel. */
    return (int)((width+1u)&~1u);
}

unsigned int af_glyph_begin(const unsigned char *text, unsigned int bytes) {
    unsigned int previous = active_glyph;
    active_glyph = (unsigned int)(af_glyph_index(text, bytes)+1);
    return previous;
}

void af_glyph_end(unsigned int previous) {
    active_glyph = glyph_resource && previous<=glyph_resource[19] ? previous : 0u;
}

int af_glyph_code_width(unsigned int code, int cut) {
    (void)cut; /* Preserve the approved always-proportional native width patch. */
    if (code==0x80u && active_glyph) return glyph_resource[47+active_glyph];
    return (int)(12u-af_glyph_native_offset(code));
}

int af_glyph_texture_code(int code) {
    return code==0x80 && active_glyph ? (int)active_glyph-1 : code;
}

const unsigned char *af_glyph_texture(void) {
    return active_glyph ? glyph_resource+AF_GLYPH_TEXTURE_OFFSET : af_glyph_native_texture();
}
