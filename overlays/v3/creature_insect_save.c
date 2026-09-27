/* Persistent monthly insect seasons, independent of the fish half-months.
 * Installed only with the format-eight codec/format-nine disk envelope. */
#define AF_V3_CLOTHING_PROFILE 1
#define AF_V3_REWARD_PROFILE 1
#define AF_V3_SURFACE_PROFILE 1
#define AF_V3_CREATURE_PROFILE 1
#define AF_V3_INSECT_SEASONS 1
#include "save_runtime.h"
#include "creature_insect_spawns.h"
#ifdef __mips__
#define state ((struct AfSaveRuntime *)0x8046C000u)
#else
extern struct AfSaveRuntime af_creature_test_state;
#define state (&af_creature_test_state)
#endif
extern void af_v3_require_save_state(void);

int af_insect_saved_season(SpawnTerms *out,SpawnDate date,SpawnRandom random,void *ctx) {
    if (!out || !random || date.month<1 || date.month>12 || date.day<1 || date.day>31) return 0;
    af_v3_require_save_state();
    unsigned char *bytes=state->working+AF_SAVE_INSECT_SEASON_OFFSET;
    if (bytes[2]>1 || bytes[0]>11 || bytes[1]>5 ||
            (!bytes[2] && (bytes[0] || bytes[1]))) return 0;
    SpawnSeason season={bytes[0],bytes[1]};
    if (!bytes[2]) {
        float r=random(ctx);
        if (!(r>=0.0f && r<1.0f)) return 0;
        /* The source initializes to next month; December wraps to January. */
        season.term=(unsigned)date.month%12;
        season.offset=(unsigned)(r*6.0f);
    }
    if (!af_v3_insect_spawn_terms(out,&season,date,random,ctx)) return 0;
    bytes[0]=(unsigned char)season.term;bytes[1]=(unsigned char)season.offset;bytes[2]=1;
    return 1;
}
