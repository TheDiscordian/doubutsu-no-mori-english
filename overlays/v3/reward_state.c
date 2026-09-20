/* Source trophy/celebration state in the explicit V3 format-3 extension. */
#include "save_runtime.h"
#include "save_rewards.h"
typedef af_save_u8 u8;
typedef af_save_u32 u32;
#ifdef __mips__
#define state ((struct AfSaveRuntime *)0x8046C000u)
#define players ((u8 *)0x80126EC0u)
#define active (*(u8 *volatile *)0x80136FD8u)
#else
extern struct AfSaveRuntime af_reward_state;
extern u8 af_reward_players[4*0xBD0], *af_reward_active;
#define state (&af_reward_state)
#define players af_reward_players
#define active af_reward_active
#endif
extern void af_v3_require_save_state(void);
extern void af_v3_save_halt(int) __attribute__((noreturn));
extern void af_v3_catalogue_clear(u8 *);
extern void af_v3_reward_stop_fanfare(void *);

int af_v3_reward_data_valid(const u8 *data) { return data && af_save_rewards_valid(data); }

int af_v3_reward_flag(u32 player,u32 category,u32 index,u32 mark) {
    if (player>=4 || category>1 || index>(category?3u:32u) || mark>1) return AF_SAVE_ARGUMENT;
    af_v3_require_save_state();
    u32 offset=8,bit=index;
    if (!category) {
        bit=index<28 ? index : index-28;
        offset=(index<28 ? 3u : 7u)-(bit>>3);
        bit&=7;
    }
    u8 *p=state->working+AF_SAVE_REWARD_OFFSET+player*AF_REWARD_PLAYER_BYTES+offset;
    u32 mask=1u<<bit;
    if (mark) *p|=mask;
    return (*p&mask)!=0;
}

static u32 player_slot(const u8 *p) {
    for (u32 i=0;i<4;++i) if (p==players+i*0xBD0u) return i;
    return 4;
}

void af_v3_reward_player_clear(u8 *p) {
    u32 slot=player_slot(p);
    if (slot<4) {
        af_v3_require_save_state();
        u8 *flags=state->working+AF_SAVE_REWARD_OFFSET+slot*AF_REWARD_PLAYER_BYTES;
        for (u32 i=0;i<AF_REWARD_PLAYER_BYTES;++i) flags[i]=0;
    }
    af_v3_catalogue_clear(p);
}

void af_v3_reward_settle(void *actor,void *game) {
    (void)game;
    if (!actor) return;
    int type=*(int *)((u8 *)actor+0xD18);
    if ((u32)type>=4) return;
    u32 slot=player_slot(active);
    if (slot==4) af_v3_save_halt(AF_SAVE_ARGUMENT);
    af_v3_require_save_state();
    af_v3_reward_stop_fanfare(actor);
    (void)af_v3_reward_flag(slot,1,(u32)type,1);
}
