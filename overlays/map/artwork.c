/* Native commands for the supplied English map label and separator geometry. */
#include <PR/mbi.h>

const Gfx acre_texture[] __attribute__((section(".acre"), aligned(8))) = {
    gsDPLoadTextureBlock_4b(0x0C00B460, G_IM_FMT_I, 32, 16, 15,
                          G_TX_CLAMP, G_TX_CLAMP, 5, 4, 0, 0),
};

const Gfx acre_separator[] __attribute__((section(".dash"), aligned(8))) = {
    gsDPPipeSync(),
    gsDPSetCombineMode(G_CC_PRIMITIVE, G_CC_PRIMITIVE),
    gsDPSetPrimColor(0, 255, 85, 55, 55, 255),
    gsSPVertex(0x0C006F10, 4, 0),
    gsSP2Triangles(0, 1, 2, 0, 1, 3, 2, 0),
    gsSPEndDisplayList(),
};
