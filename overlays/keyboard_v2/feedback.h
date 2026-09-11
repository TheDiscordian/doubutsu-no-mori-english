#ifndef AF_V2_FEEDBACK_H
#define AF_V2_FEEDBACK_H

/* Native 64x64 stick frames use three rows: up, neutral, down. Right-facing
 * frames mirror the left-facing art. Bit 4 carries that mirror flag. */
static unsigned int af_v2_stick(unsigned int held, int x, int y) {
    static const unsigned char frames[9]={3,1,19,4,0,20,5,2,21};
    unsigned int h=held&0x300u, v=held&0xC00u;
    if (h || v) {
        if (h==0x300u || v==0xC00u) return 0;
        x=h==0x200u ? -1 : h==0x100u;
        y=v==0x800u ? -1 : v==0x400u;
    } else {
        /* Use the editor's dead zone, without consuming or changing input. */
        if ((unsigned int)(x+128)>255u || (unsigned int)(y+128)>255u) return 0;
        x=x<=-25 ? -1 : x>=25;
        y=y>=25 ? -1 : y<=-25;
    }
    return frames[(y+1)*3+x+1];
}

/* guOrtho's 16.16 horizontal element truncates 25.6 to 25. The font's
 * polygon vertices therefore shrink around x=160, unlike RDP key rectangles.
 * Undo that only for this keyboard's text, retaining glyph ink and metrics. */
static float af_v2_text_x(float x) { return 160.0f+(x-160.0f)*(128.0f/125.0f); }
static float af_v2_text_scale(float scale) { return scale*(128.0f/125.0f); }

#endif
