/* Startup-only world-label hooks, installed together with the existing font. */
#include "names.h"
typedef unsigned int u32;
extern int af_font_install(void);

struct Hook { u32 address, before, after; const void *target; };
static const struct Hook world_hooks[] = {
    {0x800CBF90u,0x0C00BD30u,0,af_world_reset},
    {0x800CC324u,0x0C0259D0u,0,af_world_load},
    {0x800CC32Cu,0x3C048014u,0,af_world_measure},
    {0x800CC330u,0x248446BDu,0,0},
    {0x800CC334u,0x2405000Au,0x3C088014u,0},
    {0x800CC338u,0x0C027070u,0x250846A0u,0},
    {0x800CC33Cu,0x24060020u,0x080330DBu,0},
    {0x800CC340u,0x44829000u,0,0},
    {0x800CC9A8u,0x0C0243A6u,0,af_world_draw}
};

#ifdef __mips__
static volatile u32 *word(u32 address) { return (volatile u32 *)address; }
static void flush(void) {
    ((void (*)(void *,u32))0x8002FE00u)((void *)0x800CBF90u,0xA20u);
    ((void (*)(void *,u32))0x80034CE0u)((void *)0x800CBF90u,0xA20u);
}
#else
extern volatile u32 *af_world_test_word(u32);
extern void af_world_test_flush(void);
#define word af_world_test_word
#define flush af_world_test_flush
#endif

int af_world_font_install(void) {
    u32 i;
    for (i=0;i<sizeof(world_hooks)/sizeof(world_hooks[0]);++i)
        if (*word(world_hooks[i].address)!=world_hooks[i].before) return 0;
    /* The font installer checks all its guards before its first write. Nothing
       below can fail, so no rejected install can leave a partial world hook. */
    if (!af_font_install()) return 0;
    for (i=0;i<sizeof(world_hooks)/sizeof(world_hooks[0]);++i) {
        const struct Hook *hook=world_hooks+i;
        *word(hook->address)=hook->target
            ? 0x0C000000u|(((u32)(unsigned long)hook->target&0x0FFFFFFFu)>>2) : hook->after;
    }
    flush();
    return 1;
}
