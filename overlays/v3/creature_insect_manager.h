#ifndef AF_V3_INSECT_MANAGER_H
#define AF_V3_INSECT_MANAGER_H
#include "creature_insects.h"
#include "creature_insect_spawns.h"
typedef struct {int type;xyz_t position;int extra;GAME *game;} AfInsectInit;
typedef struct {
    ACTOR *(*make)(AfInsectInit *,int);
    void (*reload)(GAME *);
    void (*destroy)(ACTOR *,GAME *);
    ACTOR *(*release)(GAME *,int,xyz_t *);
} AfNativeInsectClip;
extern AfNativeInsectClip *af_insect_native_clip;
extern const u8 af_insect_calendar[];
extern const u32 af_insect_calendar_bytes;
#ifdef __mips__
extern const u32 af_v3_insect_spawn_mode;
#else
extern u32 af_v3_insect_spawn_mode;
#endif
extern const u8 af_insect_rtc[];
extern const u16 *af_insect_foreground(int,int),*af_insect_deposits(int,int);
extern const SpawnU32 *af_insect_collision_map(int,int);
extern u32 af_insect_block_kind(int,int);
extern int af_insect_weather(void),af_insect_rank(void);
extern void af_insect_tile_position(xyz_t *,int,int,int,int);
extern int af_insect_spawn_original(void *,GAME *);
extern u32 af_v3_creature_profile_byte(u32);
/* These are real remaining dependencies, not no-op colony/save substitutes. */
extern int af_insect_colony_present(int,int,GAME *);
extern int af_insect_make_colony(AfInsectInit *,int,int);
extern int af_insect_saved_season(SpawnTerms *,SpawnDate,SpawnRandom,void *);
int af_insect_occupied_acre(int,int);
void af_v3_insect_spawn_reset(void);
int af_v3_insect_spawn(void *,GAME *);
#ifdef __mips__
_Static_assert(sizeof(AfInsectInit)==24,"native insect creation parameters");
_Static_assert(sizeof(AfNativeInsectClip)==16,"native insect clip is not expanded");
#endif
#endif
