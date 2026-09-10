#include <PR/mbi.h>

#define LABEL(name, address, width, smask) \
    Gfx name[] __attribute__((section("." #name))) = { \
        gsDPLoadTextureBlock((void *)(address), G_IM_FMT_IA, G_IM_SIZ_8b, \
            width, 16, 0, G_TX_CLAMP, G_TX_CLAMP, smask, 4, G_TX_NOLOD, G_TX_NOLOD) \
    }

LABEL(latest, 0x0C000858, 80, G_TX_NOMASK);
LABEL(entry, 0x0C000D58, 64, 6);
LABEL(quit, 0x0C001158, 32, 5);
LABEL(write, 0x0C001458, 64, 6);
