/* Shared native NPC services for ordinary residents and guarded special actors.
 * Ownership, callback lifetime, and admission come from the same registry. */
#include "holiday_participants.h"
#include "constants.h"
extern const u32 *volatile af_hp_native_npc_clip;
extern int af_holiday_observers_clip(void);
#define FN(word,ret,...) ((ret (*)(__VA_ARGS__))(word))
static u32 clip(unsigned int offset) {return af_hp_native_npc_clip[offset/4];}
static int live(void) {return af_hp_native_npc_clip && af_holiday_observers_clip();}
static int birth(ACTOR *a,GAME *g) {
    return live() && af_hp_admit(a,g) && FN(clip(0xBC),int,ACTOR *,GAME *)(a,g)==1;
}
static void ctor(ACTOR *a,GAME *g,const aNPC_ct_data_c *source) {
    if(!live() || !source || source->schedule!=aNPC_CT_SCHED_TYPE_SPECIAL) {
        Actor_delete(a);return;
    }
    aNPC_ct_data_c data=*source;
    data.schedule=4; /* native SPECIAL, not donor WALK_WANDER */
    if(!af_hp_npc_callbacks(a,&data)) {Actor_delete(a);return;}
    FN(clip(0xC0),void,ACTOR *,GAME *,const aNPC_ct_data_c *)(a,g,&data);
    af_hp_constructed(a);
}
static void dtor(ACTOR *a,GAME *g) {if(live())FN(clip(0xC4),void,ACTOR *,GAME *)(a,g);}
static void init(ACTOR *a,GAME *g) {if(live())FN(clip(0xCC),void,ACTOR *,GAME *)(a,g);}
static void move(ACTOR *a,GAME *g) {if(live())FN(clip(0xD0),void,ACTOR *,GAME *)(a,g);}
static void draw(ACTOR *a,GAME *g) {if(live())FN(clip(0xE4),void,ACTOR *,GAME *)(a,g);}
static int think(NPC_ACTOR *a,GAME_PLAY *g,int which,int phase) {
    if(!live() || (which!=-1 && which!=aNPC_THINK_SPECIAL) || phase<0 || phase>2)return 0;
    return FN(clip(0x110),int,NPC_ACTOR *,GAME_PLAY *,int,int)(a,g,which<0?-1:8,phase);
}
static void destination(NPC_ACTOR *a,f32 x,f32 z) {
    if(live())FN(clip(0x10C),void,NPC_ACTOR *,f32,f32)(a,x,z);
}
/* All source animation constants are already matched to native indices. */
static void animation(ACTOR *a,int id,int reset) {
    if(live())FN(clip(0x104),void,ACTOR *,int,int)(a,id,reset);
}
const AFHPNpcServices af_hp_npc_services={birth,ctor,dtor,init,move,draw,animation,think,destination};
