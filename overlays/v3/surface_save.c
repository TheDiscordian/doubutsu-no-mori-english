/* Shared surface profile and collection adapters; native ownership stays intact. */
#include "save_runtime.h"
typedef af_save_u8 u8;
typedef af_save_u32 u32;
typedef unsigned short u16;
struct SurfaceItem {u16 item,price;u32 enabled;u8 name[16];};
#ifdef __mips__
#define header ((const u32 *)0x804BC800u)
#define state ((struct AfSaveRuntime *)0x8046C000u)
#define players ((u8 *)0x80126EC0u)
#define active (*(u8 *volatile *)0x80136FD8u)
#else
extern u32 af_surface_test_header[64];
extern struct AfSaveRuntime af_surface_test_state;
extern u8 af_surface_test_players[4*0xBD0],*af_surface_test_active;
#define header af_surface_test_header
#define state (&af_surface_test_state)
#define players af_surface_test_players
#define active af_surface_test_active
#endif
extern void af_surface_prior_record(u32),af_surface_prior_clear(u8 *);
extern int af_surface_prior_owned(const u8 *,u32);
extern void af_v3_require_save_state(void);
extern void af_v3_save_halt(int) __attribute__((noreturn));

u32 af_v3_surface_profile_byte(u32 index) {
    if (index>=64 || header[0]!=0x41465349u || header[1]!=1 || header[2]!=10 || header[3]!=24) return 0;
    const struct SurfaceItem *rows=(const struct SurfaceItem *)(header+4);
    u32 result=0;
    for (u32 i=0;i<10;i++) {
        u32 item=rows[i].item,kind=i/5,position=73+i%5;
        if (item==0x2600+kind*256+position && rows[i].enabled==1 && index==kind*32+(position>>3))
            result|=1u<<(position&7u);
    }
    return result;
}

static int extended(u32 item) {return (item>>8)-0x26u<2u && (item&255u)>=64u;}
static u32 slot(const u8 *private) {
    for (u32 i=0;i<4;i++) if (private==players+i*0xBD0) return i;
    return 4;
}
static int enabled(u32 item) {
    return (af_v3_surface_profile_byte(((item>>8)-0x26u)*32u+((item&255u)>>3))>>(item&7u))&1u;
}

void af_v3_surface_record(u32 argument) {
    u32 item=(u16)argument;
    if (!extended(item)) {af_surface_prior_record(argument);return;}
    if (!enabled(item)) return;
    af_v3_require_save_state();
    int result=af_v3_save_collect(state->working,slot(active),item,1);
    if (result<0) af_v3_save_halt(result);
}

int af_v3_surface_owned(const u8 *private,u32 item) {
    if (!extended(item)) return af_surface_prior_owned(private,item);
    u32 player=slot(private);
    if (player>=4 || !enabled(item)) return 0;
    af_v3_require_save_state();
    int result=af_v3_save_collect(state->working,player,item,0);
    if (result<0) af_v3_save_halt(result);
    return result;
}

void af_v3_surface_player_clear(u8 *private) {
    u32 player=slot(private);
    if (player<4) {
        af_v3_require_save_state();
        u8 *bits=state->working+AF_SAVE_SURFACE_OFFSET+AF_SAVE_SURFACE_PROFILE*(player+1);
        for (u32 i=0;i<AF_SAVE_SURFACE_PROFILE;i++) bits[i]=0;
    }
    af_surface_prior_clear(private);
}
