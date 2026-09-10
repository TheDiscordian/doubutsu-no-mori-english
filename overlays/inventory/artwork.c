/* Load the complete horizontal English heading in the original texture slot. */
#include <PR/mbi.h>

const Gfx items_texture[] __attribute__((section(".items"), aligned(8))) = {
    gsDPLoadTextureBlock_4b(0x0C00AD00, G_IM_FMT_I, 64, 16, 15,
                          G_TX_CLAMP, G_TX_CLAMP, 6, 4, 0, 0),
};
