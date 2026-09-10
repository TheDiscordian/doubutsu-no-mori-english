#include <PR/mbi.h>

#define LABEL(name, address, width, smask) \
    Gfx name[] __attribute__((section("." #name))) = { \
        gsDPLoadTextureBlock_4b((void *)(address), G_IM_FMT_I, width, 16, 15, \
            G_TX_CLAMP, G_TX_CLAMP, smask, 4, G_TX_NOLOD, G_TX_NOLOD) \
    }

LABEL(cash, 0x0C001288, 64, 6);
LABEL(payment, 0x0C002A08, 64, 6);
LABEL(owe, 0x0C001588, 96, G_TX_NOMASK);
LABEL(bells, 0x0C002088, 32, 5);
