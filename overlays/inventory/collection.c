/* Complete English headings in the original larger texture slots. */
#include <PR/mbi.h>

const Gfx insects_texture[] __attribute__((section(".insects"), aligned(8))) = {
    gsDPLoadTextureBlock_4b(0x0C001D28, G_IM_FMT_I, 80, 16, 15,
                          G_TX_CLAMP, G_TX_CLAMP, G_TX_NOMASK, 4, 0, 0),
};
const Gfx fish_texture[] __attribute__((section(".fish"), aligned(8))) = {
    gsDPLoadTextureBlock_4b(0x0C00E438, G_IM_FMT_I, 64, 16, 15,
                          G_TX_CLAMP, G_TX_CLAMP, 6, 4, 0, 0),
};
