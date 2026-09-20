#include "scenery.h"
/* This code is in the already loaded equipment package, not in the packet it
   transfers. The cache word starts clear in the startup-loaded module. */
static int load(void) {
    void *code=(void *)0x804B5000u;
#ifdef AF_V3_SCENERY_TREES
    volatile u32 *ready=(volatile u32 *)0x804ADFECu;
    if (*ready==AF_SCENERY_CRC) return 1;
#endif
    if (af_scenery_dma(code,AF_SCENERY_VROM,AF_SCENERY_BYTES)
            || af_scenery_crc(code,AF_SCENERY_BYTES)!=AF_SCENERY_CRC) {
        af_scenery_fault("V3 scenery","Invalid scene code");return 0;
    }
    af_scenery_writeback(code,AF_SCENERY_BYTES);
    af_scenery_invalidate(code,AF_SCENERY_BYTES);
#ifdef AF_V3_SCENERY_TREES
    *ready=AF_SCENERY_CRC;
#endif
    return 1;
}
void af_v3_scenery_boot(void *actor,void *game,u32 variant) {
    if (load()) ((void (*)(void *,void *,u32))0x804B5000u)(actor,game,variant);
}
void af_v3_scenery_cherry(void *a,void *b) { af_v3_scenery_boot(a,b,0); }
void af_v3_scenery_winter(void *a,void *b) { af_v3_scenery_boot(a,b,1); }
void af_v3_scenery_xmas(void *a,void *b) { af_v3_scenery_boot(a,b,2); }
void af_v3_scenery_ordinary(void *a,void *b) { af_v3_scenery_boot(a,b,3); }
#ifdef AF_V3_SCENERY_TREES
u32 af_v3_tree_grow_dispatch(u32 item,int days,int plant) {
    if (!load()) return item;
    return ((u32 (*)(u32,int,int))AF_SCENERY_GROW)(item,days,plant);
}
u32 af_v3_tree_stump_dispatch(u32 item,int flag) {
    if (!load()) return item;
    return ((u32 (*)(u32,int))AF_SCENERY_STUMP)(item,flag);
}
#ifdef AF_V3_SCENERY_DAILY
void af_v3_tree_renew_dispatch(void *time,int *gyroids) {
    if (load()) ((void (*)(void *,int *))AF_SCENERY_RENEW)(time,gyroids);
}
#endif
/* The original prologues are leaf instructions; no relocated operands or
   incoming interior references may exist. Source bytes are checked at build. */
__asm__(".set noreorder\n"
        ".section .tree_fallbacks,\"ax\"\n"
        ".globl af_v3_native_tree_grow\naf_v3_native_tree_grow:\n"
        "sw $a0,0($sp)\nandi $a0,$a0,65535\nj 0x800A5978\nnop\n"
        ".globl af_v3_native_tree_stump\naf_v3_native_tree_stump:\n"
        "sw $a1,4($sp)\nsll $a1,$a1,16\nj 0x800A56F8\nnop\n"
        ".set reorder\n");
#endif
