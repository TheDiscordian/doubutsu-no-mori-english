/* One persistent identity/collection/season adapter for all added creatures. */
#include "save_runtime.h"
#include "creature_spawns.h"
typedef af_save_u8 u8;
typedef af_save_u32 u32;
#ifdef __mips__
#define state ((struct AfSaveRuntime *)0x8046C000u)
#else
extern struct AfSaveRuntime af_creature_test_state;
#define state (&af_creature_test_state)
#endif
extern int af_creature_item_type(u32);
extern void af_v3_require_save_state(void);
extern void af_v3_save_halt(int) __attribute__((noreturn));

u32 af_v3_creature_profile_byte(u32 byte) {
    if (byte>=3) return 0;
    u32 result=0;
    for (u32 bit=0;bit<8;bit++) {
        u32 index=byte*8+bit;
        if (index>=17) break;
        u32 item=index<9 ? 0x2320+index : 0x2D20+index-9;
        if (af_creature_item_type(item)==(index<9 ? 8 : 18)) result|=1u<<bit;
    }
    return result;
}

void af_v3_creature_player_clear(u32 player) {
    if (player>=4) return;
    af_v3_require_save_state();
    for (u32 i=0;i<4;i++) state->working[AF_SAVE_CREATURE_OFFSET+4+player*4+i]=0;
}

/* Keep the two source season bytes with the town, not the transient acre actor.
 * Older saves initialize on first use. Failure leaves the saved bytes intact. */
int af_v3_creature_season(SpawnTerms *out,SpawnDate date,SpawnRandom random,void *ctx) {
    if (!out || !random || date.month<1 || date.month>12 || date.day<1 || date.day>31) return 0;
    af_v3_require_save_state();
    u8 *bytes=state->working+AF_SAVE_CREATURE_OFFSET+20;
    SpawnSeason season={bytes[0],bytes[1]};
    if (!bytes[2]) {
        float r=random(ctx);
        if (!(r>=0.0f && r<1.0f)) return 0;
        season.term=((date.month-1)*2+(date.day>15)+1)%24;
        season.offset=(unsigned)(r*6.0f);
    }
    if (!af_v3_spawn_terms(out,&season,date,random,ctx)) return 0;
    bytes[0]=(u8)season.term;bytes[1]=(u8)season.offset;bytes[2]=1;
    return 1;
}
