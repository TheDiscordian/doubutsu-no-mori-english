#ifndef AF_V3_INSECT_COLONY_H
#define AF_V3_INSECT_COLONY_H
#include "creature_insect_manager.h"
#include "creature_insect_engine.h"
#define AF_INSECT_COLONY_ID 0xB5
#define AF_INSECT_COLONY_PART 4
typedef struct {
    ACTOR actor;
    int action,alpha;
    ACTOR *insect;
    int failures;
    mActor_name_t *foreground;
} AfInsectColony;
typedef struct {
    s16 id;u8 part,pad;u32 flags;u16 item;s16 bank;u32 bytes;
    mActor_proc constructor,destructor,move,draw,save;
} AfInsectProfile;
extern const AfInsectProfile af_insect_colony_profile;
extern const u8 af_insect_colony_art[];
extern const u32 af_insect_colony_art_bytes,af_insect_colony_model;
extern const s8 af_insect_colony_rates[2][2];
void af_insect_colony_reset(void);
void af_insect_controller_end(GAME *);
void af_insect_colony_draw(ACTOR *,GAME *);
int af_insect_net_index(const ACTOR *,int,int);
extern void af_insect_delete_actor(ACTOR *);
extern ACTOR *af_insect_create_actor(void *,GAME *,s16,f32,f32,f32,
    s16,s16,s16,s8,s8,s16,u16,s16,s8,int);
extern f32 af_insect_net_swing(PLAYER_ACTOR *,GAME *);
extern void af_insect_net_request(PLAYER_ACTOR *,GAME *,ACTOR *,int,f32);
extern void af_insect_net_force(PLAYER_ACTOR *,GAME *,ACTOR *,int);
extern int af_insect_net_change(PLAYER_ACTOR *,ACTOR *,int);
#ifdef __mips__
_Static_assert(sizeof(AfInsectProfile)==0x24,"native resident actor profile");
_Static_assert(sizeof(AfInsectColony)==0x188,"colony allocation size");
#endif
#endif
