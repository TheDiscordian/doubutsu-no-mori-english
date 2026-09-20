#include "scenery.h"
/* This code is in the already loaded equipment package, not in the packet it
   transfers. Reloading an owner always refreshes the packet and its I-cache. */
void af_v3_scenery_boot(void *actor,void *game,u32 variant) {
    void *code=(void *)0x804B5000u;
    if (af_scenery_dma(code,AF_SCENERY_VROM,AF_SCENERY_BYTES)
            || af_scenery_crc(code,AF_SCENERY_BYTES)!=AF_SCENERY_CRC) {
        af_scenery_fault("V3 scenery","Invalid scene code");return;
    }
    af_scenery_writeback(code,AF_SCENERY_BYTES);
    af_scenery_invalidate(code,AF_SCENERY_BYTES);
    ((void (*)(void *,void *,u32))code)(actor,game,variant);
}
void af_v3_scenery_cherry(void *a,void *b) { af_v3_scenery_boot(a,b,0); }
void af_v3_scenery_winter(void *a,void *b) { af_v3_scenery_boot(a,b,1); }
void af_v3_scenery_xmas(void *a,void *b) { af_v3_scenery_boot(a,b,2); }
void af_v3_scenery_ordinary(void *a,void *b) { af_v3_scenery_boot(a,b,3); }
