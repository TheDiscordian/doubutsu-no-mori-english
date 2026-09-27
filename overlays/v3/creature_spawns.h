#ifndef AF_V3_CREATURE_SPAWNS_H
#define AF_V3_CREATURE_SPAWNS_H
typedef unsigned char SpawnU8;
typedef unsigned short SpawnU16;
typedef unsigned int SpawnU32;
#define AF_SPAWN_CAPACITY 64
typedef struct { SpawnU16 actor, area; float weight; } SpawnRow;
typedef struct { unsigned count; SpawnRow rows[AF_SPAWN_CAPACITY]; } SpawnPlan;
typedef struct { int year, month, day; } SpawnDate;
typedef struct { unsigned term, offset; } SpawnSeason;
typedef struct { unsigned current, next; float rate; } SpawnTerms;
typedef float (*SpawnRandom)(void *);
typedef int (*SpawnSite)(void *, unsigned, unsigned, unsigned);
typedef struct { unsigned actor, x, z; } SpawnPosition;

int af_v3_spawn_time(unsigned hour);
int af_v3_spawn_terms(SpawnTerms *, SpawnSeason *, SpawnDate, SpawnRandom, void *);
int af_v3_spawn_plan(SpawnPlan *, const SpawnU8 *, unsigned, unsigned,
                    SpawnTerms, unsigned, unsigned, int);
int af_v3_spawn_pick(const SpawnPlan *, unsigned, int, SpawnRandom, void *);
int af_v3_spawn_position(SpawnPosition *, unsigned, SpawnSite, SpawnRandom, void *);
#endif
