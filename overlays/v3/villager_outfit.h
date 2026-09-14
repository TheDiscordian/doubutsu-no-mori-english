#ifndef AF_V3_VILLAGER_OUTFIT_H
#define AF_V3_VILLAGER_OUTFIT_H
#include "storage.h"
/* Use the installed resource reader, including its identity/enabled checks. */
#ifdef AF_V3_OUTFIT_READY
#define outfit_ready ((int (*)(unsigned int))AF_V3_OUTFIT_READY)
#else
#ifdef AF_V3_IMPORTED_OUTFIT_SOURCE
__attribute__((noinline))
#endif
static int outfit_ready(unsigned int cloth) {
    if (cloth >= 0x2400u && cloth < 0x2500u) return 1;
#ifdef AF_V3_IMPORTED_OUTFIT_SOURCE
#ifdef __mips__
    return cloth == 0x34BFu &&
        ((unsigned int (*)(int, unsigned int))AF_V3_IMPORTED_OUTFIT_SOURCE)(0x10BF, 0)
        == AF_V3_CLOTHING_VROM;
#else
    extern unsigned int af_v3_clothing_source(int, unsigned int);
    return cloth == 0x34BFu && af_v3_clothing_source(0x10BF, 0) == AF_V3_CLOTHING_VROM;
#endif
#else
    return 0;
#endif
}
#endif
#endif
