/* Keep the native cash-label allocation; load the English 64-by-16 I4 donor. */
#include <PR/mbi.h>

const Gfx cash_texture[] __attribute__((section(".cash"), aligned(8))) = {
    gsDPLoadTextureBlock_4b(0x0400B4D0, G_IM_FMT_I, 64, 16, 15,
                          G_TX_CLAMP, G_TX_CLAMP, 6, 4, 0, 0),
};
