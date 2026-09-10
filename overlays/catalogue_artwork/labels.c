#include <PR/mbi.h>

#define LABEL(name, address, width, smask) \
    Gfx name[] __attribute__((section("." #name))) = { \
        gsDPLoadTextureBlock((void *)(address), G_IM_FMT_IA, G_IM_SIZ_8b, \
            width, 16, 0, G_TX_CLAMP, G_TX_CLAMP, smask, 4, G_TX_NOLOD, G_TX_NOLOD) \
    }

LABEL(top, 0x0C0009B8, 32, 5);
LABEL(bottom, 0x0C000DB8, 64, 6);
