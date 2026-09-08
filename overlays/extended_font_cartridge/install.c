/* Installed once before graph/audio threads; all code and pixels remain owned. */
#include "font.h"

extern const unsigned char af_font_resource[];
extern void af_glyph_draw_char(void *,void *,void *);
extern void af_glyph_load_texture(void);
extern int af_glyph_skip_tag(const void *,int);
typedef unsigned int u32;

static int native_width(const unsigned char *text,int bytes,int cut) {
    u32 width=0;
    (void)cut;
    while (bytes>0) {
        u32 count=af_glyph_size(text,(u32)bytes);
        width+=af_glyph_width(text,(u32)bytes);
        text+=count;bytes-=(int)count;
    }
    return (int)((width+1u)&~1u);
}

struct Hook { u32 address, first, second; const void *target; };
static const struct Hook hooks[] = {
    {0x80090178u,0x3C028014u,0x2442A680u,af_glyph_texture},
    {0x8009028Cu,0x27BDFFE8u,0xAFBF0014u,af_glyph_code_width},
    {0x800902CCu,0x27BDFFD0u,0xAFB40028u,native_width},
    {0x8009069Cu,0x27BDFFE0u,0xAFBF0014u,af_glyph_load_texture},
    {0x800918A8u,0x27BDFFE8u,0xAFBF0014u,af_glyph_draw_char}
};
static const u32 cursor_original[10] = {
    0x24010080,0x14410008,0x8FA50050,0x02002025,0x0C027701,
    0x8FA50050,0x8FA50050,0x00A22821,0x1000FFE1,0xAFA50050
};
static const u32 cursor_patch[10] = {
    0x02002025,0,0x8FA50050,0x10400006,0x8FA50050,
    0x24A50002,0xAFA50050,0x080288DB,0,0
};

int af_font_install(void) {
    u32 i;
    volatile u32 *cursor=(volatile u32 *)0x800A23C4u;
    for (i=0;i<5u;++i) {
        volatile const u32 *native=(volatile const u32 *)hooks[i].address;
        if (native[0]!=hooks[i].first || native[1]!=hooks[i].second) return 0;
    }
    for (i=0;i<10u;++i) if (cursor[i]!=cursor_original[i]) return 0;
    if (!af_glyph_bind(af_font_resource,AF_GLYPH_BYTES)) return 0;
    for (i=0;i<5u;++i) {
        volatile u32 *native=(volatile u32 *)hooks[i].address;
        native[0]=0x08000000u|(((u32)hooks[i].target&0x0FFFFFFFu)>>2);
        native[1]=0;
    }
    for (i=0;i<10u;++i) cursor[i]=i==1u
        ? 0x0C000000u|(((u32)af_glyph_skip_tag&0x0FFFFFFFu)>>2) : cursor_patch[i];
    /* Flush the contiguous font functions and the distinct cursor patch only
       after all guards pass. No native rendering thread exists at this point. */
    ((void (*)(void *,u32))0x8002FE00u)((void *)0x80090178u,0x1738u);
    ((void (*)(void *,u32))0x80034CE0u)((void *)0x80090178u,0x1738u);
    ((void (*)(void *,u32))0x8002FE00u)((void *)cursor,40u);
    ((void (*)(void *,u32))0x80034CE0u)((void *)cursor,40u);
    return 1;
}
