#ifndef AF_V3_INSECT_SPAWNS_H
#define AF_V3_INSECT_SPAWNS_H
#include "creature_spawns.h"

typedef struct {
    const SpawnU16 *foreground; /* 16 x 16 native item IDs */
    const SpawnU16 *deposits;   /* one buried-item mask per row */
    const SpawnU32 *collision; /* 16 x 16 native unit words */
    unsigned block;
    int weather;              /* native: clear=0, rain=1, snow=2 */
} InsectHabitat;
typedef struct {
    unsigned actor, x, z, extra;
    int colony;
} InsectBirth;
typedef int (*InsectCreate)(void *, const InsectBirth *);

int af_v3_insect_spawn_time(unsigned);
int af_v3_insect_spawn_terms(SpawnTerms *, SpawnSeason *, SpawnDate, SpawnRandom, void *);
int af_v3_insect_spawn_plan(SpawnPlan *, const SpawnU8 *, unsigned, SpawnTerms,
                            unsigned, unsigned, int);
int af_v3_insect_spawn_tree(unsigned);
/* -1 means no birth, -2 requests the complete original native manager when
 * the native-population alternative wins. A nonnegative result is a row index.
 * The plan is a disposable copy; source habitat filtering changes its weights.
 */
int af_v3_insect_spawn_choose(SpawnPlan *, const InsectHabitat *, int, int,
                              SpawnRandom, void *);
/* Returns successful creations, zero for no spawn, or -1 for invalid input.
 * Callback failure stops the source group; every selected tile is removed.
 * last_result receives the donor manager's final creation result. A partial
 * group can contain live insects while the final attempt returns failure.
 */
int af_v3_insect_spawn_group(const SpawnRow *, const InsectHabitat *,
                             const SpawnU8 *, unsigned, SpawnRandom,
                             InsectCreate, void *, int *last_result);
#endif
