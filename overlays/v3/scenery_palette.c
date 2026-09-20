#include <ultra64.h>
/* Six palette commands, a complete material call, and return. Pointer words
   use explicit bank fixups; no segment-six assumptions cross owner lifetimes. */
Gfx scenery_palette[] __attribute__((section(".palette"))) = {
    gsDPLoadTLUT_pal16(8, (void *)0x01000000),
    gsSPDisplayList((Gfx *)0x02000000),
    gsSPEndDisplayList(),
};
