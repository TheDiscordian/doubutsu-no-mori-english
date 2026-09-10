/* Bound the native AM/PM glyphs; wrapping repeats p's descender after m. */
#include <PR/mbi.h>

const Gfx clock_texture[] __attribute__((section(".clock"), aligned(8))) = {
    gsDPLoadTextureBlock_4b(0x08000000, G_IM_FMT_I, 16, 16, 15,
                          G_TX_CLAMP, G_TX_CLAMP, 4, 4, 0, 0),
};
