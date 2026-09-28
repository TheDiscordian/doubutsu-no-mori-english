/* Native effects keep their overlay loader. Imported profiles are checked
 * subresources, not independent DMA-directory entries or executable overlays.
 * This bridge lives in the native scene-owned effect controller itself.
 */
#include "room_rigs.h"
extern void af_effect_native_load(u32,u32,void *,void *,void *);
extern int af_effect_dma(void *,u32,u32);
extern u32 af_effect_crc(void *,u32);
extern void af_effect_fault(const char *,const char *);
#ifndef AF_EFFECT_CODE_START
#define AF_EFFECT_CODE_START 0x804C8000u
#define AF_EFFECT_CODE_END 0x804CC000u
#endif
#ifndef AF_EFFECT_ROOM_COUNT
#define AF_EFFECT_ROOM_COUNT AF_EFFECT_COUNT
#endif
#ifdef __mips__
#define effect_room_loader (*(int (**volatile)(void))0x804B1E08u)
#else
extern int (*effect_room_loader)(void);
#endif

static void invalid(void) {
    af_effect_fault("V3 effects","Invalid effect profile");
    /* A fault handler must not allow the caller to publish a corrupt profile. */
    for (;;) {}
}

void af_v3_effect_profile_load(u32 first,u32 last,void *ram,void *ram_end,void *destination) {
    if (first<AF_EFFECT_PROFILES || first>=AF_EFFECT_PROFILES+AF_EFFECT_COUNT*64u) {
        af_effect_native_load(first,last,ram,ram_end,destination);
        return;
    }
    if ((first-AF_EFFECT_PROFILES)%64u || last-first!=32u ||
            (uptr)ram_end-(uptr)ram!=32u || ((uptr)destination&7u)) invalid();
    u32 low=AF_EFFECT_CODE_START,high=AF_EFFECT_CODE_END;
    if ((first-AF_EFFECT_PROFILES)/64u<AF_EFFECT_ROOM_COUNT) {
        if (!effect_room_loader || !effect_room_loader()) invalid();
    }
#ifdef AF_EFFECT_SKY_START
    else {
        /* This complete code packet is checked and loaded at startup. It is
         * independent of the lazily loaded room callbacks. */
        low=AF_EFFECT_SKY_START;high=AF_EFFECT_SKY_END;
    }
#else
    else invalid();
#endif
#ifdef __mips__
    if ((uptr)destination<0x80000000u || (uptr)destination>0x80800000u-32u) invalid();
#endif
    if (af_effect_dma(destination,first,32)) invalid();
    u32 *profile=destination;
    if (profile[7]!=0x41464550u || af_effect_crc(destination,24)!=profile[6]) invalid();
    for (u32 i=0;i<4;++i)
        if ((profile[i]&3u) || profile[i]<low || profile[i]>=high) invalid();
}
