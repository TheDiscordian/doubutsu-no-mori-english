/* Shared held-parent ownership; stored in the existing four-player extension. */
#include "save_runtime.h"
typedef af_save_u8 u8;
typedef af_save_u32 u32;
#ifdef __mips__
#define state ((struct AfSaveRuntime *)0x8046C000u)
#define players ((u8 *)0x80126EC0u)
#define active (*(u8 *volatile *)0x80136FD8u)
#else
extern struct AfSaveRuntime af_collection_state;
extern u8 af_collection_players[4*0xBD0], *af_collection_active;
#define state (&af_collection_state)
#define players af_collection_players
#define active af_collection_active
#endif
extern u32 af_v3_held_item_collection(u32);
extern void af_v3_prior_catalogue_record(u32);
extern int af_v3_prior_catalogue_owned(const u8 *,u32);
extern void af_v3_require_save_state(void);
extern void af_v3_save_halt(int) __attribute__((noreturn));

static u32 player_slot(const u8 *private) {
    for (u32 i=0;i<4;++i) if (private==players+i*0xBD0u) return i;
    return 4;
}

void af_v3_held_catalogue_record(u32 argument) {
    u32 item=(unsigned short)argument, display=af_v3_held_item_collection(item);
    if (!display) {
        /* Never pass an unavailable added parent to native tool tables. */
        if (item-0x2224u>=56u) af_v3_prior_catalogue_record(argument);
        return;
    }
    af_v3_require_save_state();
    u32 player=player_slot(active);
    if (player==4) af_v3_save_halt(AF_SAVE_ARGUMENT);
    int result=af_v3_save_collect(state->working,player,display,1);
    if (result<0) af_v3_save_halt(result);
}

int af_v3_held_catalogue_owned(const u8 *private,u32 item) {
    u32 display=af_v3_held_item_collection(item);
    if (!display) return item-0x2224u<56u ? 0 : af_v3_prior_catalogue_owned(private,item);
    u32 player=player_slot(private);
    if (player==4) return 0;
    af_v3_require_save_state();
    int result=af_v3_save_collect(state->working,player,display,0);
    if (result<0) af_v3_save_halt(result);
    return result;
}
