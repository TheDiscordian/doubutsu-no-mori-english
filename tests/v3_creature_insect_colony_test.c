/* Actual colony lifecycle and draw with controlled native engine services.
 * No ROM/save modification or native-execution claim. */
#include "creature_insect_colony.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

static AfInsectGameView view;
static GAME *game=(GAME *)&view;
static PLAYER_ACTOR player;
static AfInsectColony colony;
static aINS_INSECT_ACTOR single;
static mActor_name_t foreground;
static uintptr_t caught;
static int created,make_calls,delete_calls,request_calls,force_calls,reset_calls,change_calls;
static int allocation_ok=1,carried_ok=1,change_ok=1,stop_net,has_player=1;
static f32 swing;
static ACTOR *last_change;

PLAYER_ACTOR *af_insect_player(GAME *g) {assert(g==game);return has_player?&player:0;}
int af_insect_same_block(const ACTOR *a,const GAME *g) {
    assert(g==game);return a->block_x==view.acre_x && a->block_z==view.acre_z;
}
mActor_name_t *mFI_GetUnitFG(xyz_t p) {assert(p.x==420 && p.z==380);return &foreground;}
f32 mCoBG_GetBgY_OnlyCenter_FromWpos(xyz_t p,f32 offset) {
    assert(p.x==420 && p.z==380 && offset==-10.0f);return 7.0f;
}
void af_insect_world_to_eye(ACTOR *a,f32 offset) {assert(a==&colony.actor && offset==0);}
uintptr_t mPlib_Get_item_net_catch_label(void) {assert(has_player);return caught;}
int mPlib_Check_StopNet(xyz_t *p) {(void)p;return stop_net;}
f32 af_insect_net_swing(PLAYER_ACTOR *p,GAME *g) {assert(p==&player && g==game);return swing;}
void af_insect_net_request(PLAYER_ACTOR *p,GAME *g,ACTOR *a,int type,f32 radius) {
    assert(p==&player && g==game && a==&colony.actor && type==1 && radius==24);request_calls++;
}
void af_insect_net_force(PLAYER_ACTOR *p,GAME *g,ACTOR *a,int type) {
    assert(p==&player && g==game && a==&colony.actor && type==1);force_calls++;
}
int af_insect_net_change(PLAYER_ACTOR *p,ACTOR *a,int type) {
    assert(p==&player && type==0);change_calls++;last_change=a;
    if (change_ok) caught=(uintptr_t)a;
    return change_ok;
}
int chase_f(f32 *f,f32 target,f32 step) {
    if (fabsf(*f-target)<=step) {*f=target;return 1;}
    *f+=*f<target?step:-step;return 0;
}
void af_insect_delete_actor(ACTOR *a) {assert(a==&colony.actor);delete_calls++;a->mv_proc=0;a->dw_proc=0;}
void af_v3_insect_events_reset(void) {reset_calls++;}
ACTOR *af_insect_create_actor(void *info,GAME *g,s16 id,f32 x,f32 y,f32 z,
        s16 rx,s16 ry,s16 rz,s8 bx,s8 bz,s16 field,u16 item,s16 params,s8 npc,int bank) {
    assert(info==(u8 *)game+0x1C78 && g==game && id==0xB5);
    assert(x==420 && y==0 && z==380 && !rx && !ry && !rz && bx==2 && bz==3);
    assert(field==-1 && !item && params==-1 && npc==-1 && bank==-1);
    created++;return allocation_ok?&colony.actor:0;
}
static ACTOR *make(AfInsectInit *init,int type) {
    assert(type==1 && init->type==38 && !init->extra && init->game==game);
    assert(init->position.x==420 && init->position.y==7 && init->position.z==380);
    make_calls++;return carried_ok?(ACTOR *)&single:0;
}
static AfNativeInsectClip clip={make,0,0,0};
AfNativeInsectClip *af_insect_native_clip=&clip;

typedef struct {u32 a,b;} Command;
typedef struct {u8 prefix[0x298];Command *opaque;u8 *end;u8 pad[8];Command *xlu;u8 *xend;} Graphics;
static Graphics gfx;
static _Alignas(16) u8 arena[1024];
static Command translucent[32];
const u8 af_insect_colony_art[944]={0};
const u32 af_insect_colony_art_bytes=944,af_insect_colony_model=688;
const s8 af_insect_colony_rates[2][2]={{2,1},{1,-2}};
static int setup_calls,hilite_calls,matrix_calls,writebacks;
void af_insect_xlu_setup(Graphics *g) {assert(g==&gfx);g->xlu++;setup_calls++;}
void *af_insect_hilite(xyz_t *p,GAME *g) {
    assert(p==&colony.actor.world.position && g==game);
    gfx.end-=48;gfx.xlu+=4;hilite_calls++;return 0;
}
void af_insect_matrix(void *p) {assert(!((uintptr_t)p&15));memset(p,0x57,64);matrix_calls++;}
void af_insect_writeback(void *p,int bytes) {assert(p==gfx.end && bytes==112);writebacks++;}

static void fresh(void) {
    memset(&colony,0,sizeof(colony));foreground=0x2806;caught=0;
    colony.actor.id=AF_INSECT_COLONY_ID;colony.actor.part=4;
    colony.actor.world.position=(xyz_t){420,0,380};colony.actor.scale=(xyz_t){.01f,.01f,.01f};
    colony.actor.block_x=2;colony.actor.block_z=3;colony.actor.player_distance_xz=50;
    colony.actor.mv_proc=af_insect_colony_profile.move;
    view.acre_x=2;view.acre_z=3;
    af_insect_colony_profile.constructor(&colony.actor,game);
    assert(colony.alpha==255 && colony.action==0 && colony.actor.world.position.y==7);
    assert(colony.actor.home.position.y==7 && colony.actor.shape_info.rotation.x==0x2000);
    allocation_ok=carried_ok=change_ok=has_player=1;stop_net=0;swing=0;
    make_calls=delete_calls=request_calls=force_calls=change_calls=0;last_change=0;
}
static void tick(void) {af_insect_colony_profile.move(&colony.actor,game);}
int main(void) {
    assert(af_insect_colony_profile.id==0xB5 && af_insect_colony_profile.part==4);
    assert(af_insect_colony_profile.bank==3 && af_insect_colony_profile.flags==0x10);
    assert(af_insect_colony_profile.bytes==sizeof(colony) && !af_insect_colony_profile.save);
    fresh();af_insect_colony_reset();
    AfInsectInit request={38,{420,0,380},0,game};
    assert(af_insect_make_colony(&request,2,3));request.position.x=999;
    allocation_ok=0;af_insect_controller_end(game);assert(created==1 && reset_calls==1);
    allocation_ok=1;af_insect_controller_end(game);assert(created==2);
    af_insect_controller_end(game);assert(created==2 && reset_calls==3);
    request.position.x=420;assert(af_insect_make_colony(&request,2,3));
    af_insect_colony_reset();af_insect_controller_end(game);assert(created==2);
    assert(!af_insect_make_colony(0,2,3) && !af_insect_make_colony(&request,-1,3));
    request.type=37;assert(!af_insect_make_colony(&request,2,3));
    ACTOR other={0};view.lists[4].head=&other;other.next_actor=&colony.actor;
    assert(af_insect_colony_present(2,3,game) && !af_insect_colony_present(3,3,game));
    assert(!af_insect_colony_present(2,3,0));
    assert(af_insect_net_index(&colony.actor,1,-1)==38);
    assert(af_insect_net_index(&other,1,-1)==8 && af_insect_net_index(0,1,-1)==8);
    for (int i=0;i<40;i++) assert(af_insect_net_index(&other,0,i)==i);
    tick();assert(request_calls==1 && !force_calls && !make_calls);
    swing=1;colony.actor.player_distance_xz=39;tick();assert(force_calls==1);
    swing=0;stop_net=1;tick();assert(force_calls==2);
    colony.actor.player_distance_xz=40;tick();assert(request_calls==2);
    caught=(uintptr_t)&colony;tick();
    assert(make_calls==1 && change_calls==1 && caught==(uintptr_t)&single && colony.action==2);
    assert(colony.actor.shape_info.rotation.x==0 && colony.alpha==255);
    for (int i=0;i<8;i++) tick();
    assert(colony.alpha==15 && !delete_calls);
    tick();assert(colony.alpha==0 && delete_calls==1);
    af_insect_colony_profile.destructor(&colony.actor,game);assert(change_calls==1);
    fresh();carried_ok=0;caught=(uintptr_t)&colony;tick();tick();
    assert(make_calls==2 && colony.action==2 && colony.failures==2);
    for (int i=0;i<9;i++) if (colony.actor.mv_proc) tick();
    af_insect_colony_profile.destructor(&colony.actor,game);assert(!caught && !last_change);
    has_player=0;af_insect_colony_profile.destructor(&colony.actor,game); /* Scene teardown. */
    fresh();has_player=0;tick();assert(!request_calls && !force_calls);
    fresh();foreground=0x2F03;tick();assert(colony.action==0 && request_calls==1);
    foreground=0;tick();assert(colony.action==2 && colony.alpha==240);
    fresh();view.acre_x=4;tick();assert(delete_calls==1);
    fresh();view.acre_x=4;colony.actor.state_bitfield=0x40;tick();assert(!delete_calls);
    fresh();colony.actor.world.position.x=colony.actor.world.position.z=-1;tick();assert(!request_calls);
    fresh();memcpy(&view,&(Graphics *){&gfx},sizeof(Graphics *));
    gfx.opaque=(Command *)arena;gfx.end=arena+sizeof(arena);gfx.xlu=translucent;gfx.xend=(u8 *)(translucent+32);
    view.frame=5;colony.alpha=123;
    af_insect_colony_profile.draw(&colony.actor,game);
    assert(setup_calls==1 && hilite_calls==1 && matrix_calls==1 && writebacks==1);
    assert(gfx.xlu==translucent+10 && gfx.end==arena+864);
    Command *scroll=(Command *)(gfx.end+64);
    assert(scroll[0].a==0xE8000000 && scroll[4].a==0xDF000000);
    assert(scroll[1].a==(0xF2000000u|(10u<<12)|5u));
    assert(scroll[3].a==(0xF2000000u|(5u<<12)|4086u));
    assert(translucent[5].a==0xDB060018 && translucent[6].a==0xDB060020);
    assert(translucent[7].a==0xDA380003 && translucent[8].a==0xFA0000FF && translucent[8].b==123);
    assert(translucent[9].b==0x060002B0);
    gfx.xend=(u8 *)gfx.xlu+72;af_insect_colony_profile.draw(&colony.actor,game);assert(setup_calls==1);
    gfx.xend=(u8 *)(translucent+32);gfx.end=arena+168;
    af_insect_colony_profile.draw(&colony.actor,game);assert(setup_calls==1);
    puts("Ground colony: creation/retry, catch handoff, bee preservation, fade/cleanup, and complete bounded scrolling draw passed");
    return 0;
}
