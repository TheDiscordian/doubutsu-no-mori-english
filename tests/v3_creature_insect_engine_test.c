/* Controlled native services exercise the actual shared adapter and driver.
 * Complete donor actions have the companion category fixture; this fixture
 * checks their environment, per-slot controller, and collision connections. */
#include "creature_insect_collision.h"
#include "creature_insect_manager.h"
#include "creature_insect_player.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

static AfInsectGameView game;
GAME *af_insect_game=(GAME *)&game;
static AfInsectController controller;
static union { max_align_t alignment; u8 bytes[0x1400]; } player_storage;
static PLAYER_ACTOR *player=(PLAYER_ACTOR *)player_storage.bytes;
static ACTOR neighbour;
const xyz_t af_insect_ball={100,200,300};
const void *af_insect_demo_clip;
u8 af_insect_reset_flag;
AfInsectBgContext af_insect_bg_context;
static u32 unit;
static int visible=1,inset,main_index,weather_calls,body_calls,catch_calls,destructions;
static u32 block_kind=1;
static int bg_calls,column_excluded,ground_checks;
static uintptr_t caught;
static unsigned phases;
const u32 af_insect_tree_bee_query=0x804B6BB4;
static int footprints,frame_hit,unit_valid=1,bee_checks;
static float expected_frame;
static void footprint(void *a,GAME *g,int l,int r) {
    assert(a==player && g==af_insect_game && !l && !r);footprints++;
}
static int crossing(void *fc,float frame) {
    assert(fc==player_storage.bytes+0x174 && frame==expected_frame);
    return frame_hit;
}
static int bee_query(u32 item) {bee_checks++;return item==0x5E || item==0x81;}
void *af_test_insect_player_resolve(u32 address) {
    if (address==0x808B9594) return footprint;
    if (address==0x808B5844) return crossing;
    if (address==af_insect_tree_bee_query) return bee_query;
    assert(!"Unexpected native insect-player binding");return NULL;
}
int mFI_Wpos2UtNum(int *x,int *z,xyz_t pos) {
    assert(pos.x==120 && pos.y==5 && pos.z==200);
    *x=3;*z=5;return unit_valid;
}

PLAYER_ACTOR *af_insect_native_player(GAME *g) {assert(g==af_insect_game);return player;}
f32 af_insect_distance_xz(const xyz_t *a,const xyz_t *b) {
    return sqrtf(SQ(a->x-b->x)+SQ(a->z-b->z));
}
f32 af_insect_distance(const xyz_t *a,const xyz_t *b) {
    return sqrtf(SQ(a->x-b->x)+SQ(a->y-b->y)+SQ(a->z-b->z));
}
s16 af_insect_angle(const xyz_t *a,const xyz_t *b) {(void)a;(void)b;return 0x4000;}
f32 sin_s(s16 angle) {(void)angle;return 0;}
f32 cos_s(s16 angle) {(void)angle;return 1;}
int chase_f(f32 *value,f32 target,f32 step) {
    if (fabsf(*value-target)<=step) {*value=target;return 1;}
    *value+=*value<target?step:-step;return 0;
}
void xyz_t_move(xyz_t *to,const xyz_t *from) {*to=*from;}
static void nature(ACTOR *a) {(void)a;weather_calls++;}
static void action(ACTOR *a,GAME *g) {
    assert(a==(ACTOR *)&controller.insects[0] && g==af_insect_game);
    phases|=1u<<af_insect_step();body_calls++;
    assert(af_insect_source_frame(g)==game.frame*2+af_insect_step());
}
static void init(ACTOR *actor,GAME *g) {
    assert(g==af_insect_game);actor->mv_proc=action;
}
void aITT_actor_init(ACTOR *a,GAME *g) {init(a,g);}
void aIKR_actor_init(ACTOR *a,GAME *g) {init(a,g);}
void aIAB_actor_init(ACTOR *a,GAME *g) {init(a,g);}
void aIMN_actor_init(ACTOR *a,GAME *g) {init(a,g);}
void aIDG_actor_init(ACTOR *a,GAME *g) {init(a,g);}
void aIKA_actor_init(ACTOR *a,GAME *g) {init(a,g);}

void af_insect_native_columns(AfInsectColumn *columns,int *count,void *units,int side,
                               int grounded,u16 m0,u16 m1) {
    (void)units;assert(side==3 && grounded==0 && m0==0 && m1==0);
    *count=2;
    columns[0]=(AfInsectColumn){{320,0,320},50,12,1,0,8,8};
    columns[1]=(AfInsectColumn){{360,0,320},50,12,1,0,9,8};
}
void af_insect_native_bg(xyz_t *out,ACTOR *actor,f32 radius,f32 height,int attribute,int reverse,int type) {
    assert(!out && actor && radius>0 && height==0 && attribute==1 && reverse==0 && type==1);
    AfInsectColumn columns[16];int count;
    af_insect_columns(columns,&count,NULL,3,0,0,0);
    assert(count==2 && columns[1].radius==12 && columns[1].x==9);
    column_excluded=columns[0].radius==0;
    bg_calls++;
}
int af_insect_world_block(int *x,int *z,xyz_t pos) {
    if (pos.x<0 || pos.z<0) return 0;
    *x=(int)pos.x/640;*z=(int)pos.z/640;return 1;
}
int mFI_BkNum2WposXZ(f32 *x,f32 *z,int bx,int bz) {*x=bx*640.0f;*z=bz*640.0f;return 1;}
int af_insect_block_mode(void) {return inset;}
u32 af_insect_block_kind(int bx,int bz) {(void)bx;(void)bz;return block_kind;}
void af_insect_ground_check(xyz_t *rev,AfInsectBgContext *ctx,ACTOR *a,f32 height,
                            AfInsectCollisionResult *result,s_xyz *angle,int attr) {
    assert(ctx==&af_insect_bg_context && result==&a->bg_collision_check.result);
    assert(height==0 && !angle && !attr);rev->y=0;ground_checks++;
}
void af_insect_apply_reverse(ACTOR *a,xyz_t r,int type) {
    assert(!type);a->world.position.x+=r.x;a->world.position.y+=r.y;a->world.position.z+=r.z;
}
void af_insect_project(const f32 *matrix,const xyz_t *p,xyz_t *out,f32 *w) {
    assert(matrix==game.projection);*out=*p;*w=1;
}
int af_insect_visible(const ACTOR *a) {(void)a;return visible;}
int af_insect_pipe_destroy(GAME *g,void *pipe) {
    assert(g==af_insect_game && pipe==controller.insects[0].col_pipe);
    destructions++;return 1;
}
void af_insect_world_to_eye(ACTOR *a,f32 h) {assert(h==0);a->eye=a->world;}
const u32 *af_insect_unit(xyz_t p) {(void)p;return &unit;}
int af_insect_player_main(GAME *g) {assert(g==af_insect_game);return main_index;}
uintptr_t mPlib_Get_item_net_catch_label(void) {return caught;}
static void catch_request(PLAYER_ACTOR *p,GAME *g,ACTOR *a,int type,xyz_t *position,f32 radius) {
    assert(p==player && g==af_insect_game && a==(ACTOR *)controller.insects);
    assert(type==0 && position==&a->world.position && radius==8);catch_calls++;
}

static aINS_INSECT_ACTOR *reset(void) {
    memset(&game,0,sizeof(game));memset(&controller,0,sizeof(controller));
    memset(&neighbour,0,sizeof(neighbour));memset(&player_storage,0,sizeof(player_storage));
    player=(PLAYER_ACTOR *)player_storage.bytes;
    typedef void (*Catch)(PLAYER_ACTOR *,GAME *,ACTOR *,int,xyz_t *,f32);
    *(Catch *)(player_storage.bytes+0x1230)=catch_request;
    game.nature=nature;game.frame=3;
    weather_calls=body_calls=catch_calls=destructions=bg_calls=ground_checks=0;
    phases=0;caught=0;visible=1;inset=0;
    af_v3_insect_bind_controller(&controller);
    aINS_INSECT_ACTOR *i=controller.insects;
    i->type=32;i->exist_flag=1;
    ACTOR *a=(ACTOR *)i;
    a->state_bitfield=0x01000050;
    a->world.position=(xyz_t){320,0,320};a->last_world_position=a->world.position;
    player->actor_class.world.position=(xyz_t){323,4,324};
    assert(af_v3_insect_init(i,af_insect_game)==1);
    return i;
}
static void connected_slot(void) {
    aINS_INSECT_ACTOR *i=reset();ACTOR *a=(ACTOR *)i;
    i->bg_type=1;i->target_speed=2;i->speed_step=4;
    a->status_data.displacement=(xyz_t){2,0,0};
    assert(af_v3_insect_slot(i,af_insect_game)==1);
    assert(weather_calls==1 && body_calls==2 && phases==3 && bg_calls==2 && !column_excluded);
    assert(catch_calls==1 && destructions==0 && i->life_time==215998);
    assert(a->world.position.x==322 && a->world.position.z==322);
    assert(a->eye.position.x==322 && a->player_angle_y==0x4000);
    assert(a->player_distance_y==4 && fabsf(a->player_distance_xz-sqrtf(5))<0.001f);
    assert(!(a->state_bitfield&0x01000000) && (a->state_bitfield&0x40));
    i->insect_flags.bit_1=1;assert(af_v3_insect_slot(i,af_insect_game)==1 && catch_calls==1);
    i->insect_flags.destruct=1;caught=(uintptr_t)i;
    assert(af_v3_insect_slot(i,af_insect_game)==1 && !destructions);
    caught=0;assert(af_v3_insect_slot(i,af_insect_game)==1 && destructions==1 && !i->exist_flag);
    assert(af_v3_insect_slot(i,af_insect_game)==1 && destructions==1);
    i=reset();i->tools_actor.init_matrix=1;af_v3_insect_slot(i,af_insect_game);
    assert(!weather_calls && body_calls==2);
}
static void terrain_and_stress(void) {
    aINS_INSECT_ACTOR *i=reset();ACTOR *a=(ACTOR *)i;
    i->bg_type=3;AfInsectExtra *e=af_insect_extra(i);e->ut_x=e->ut_z=8;
    game.lists[3].head=&neighbour;neighbour.world.position=a->world.position;
    neighbour.last_world_position=neighbour.world.position;neighbour.last_world_position.x-=2;
    af_insect_environment(i,af_insect_game);
    assert(column_excluded && i->patience==5);
    i->bg_type=1;af_insect_environment(i,af_insect_game);
    assert(!column_excluded && i->patience==10); /* scoped exclusion is restored */
    game.lists[3].head=NULL;af_insect_environment(i,af_insect_game);assert(i->patience==9.5f);
    a->last_world_position=(xyz_t){620,0,320};a->world.position=(xyz_t){645,0,320};
    af_insect_acre_wall(a,6);assert(a->world.position.x==634);
    inset=1;af_insect_acre_wall(a,6);assert(a->world.position.x==594);
    assert(af_insect_acre_inset(0,0));
    block_kind=2;assert(!af_insect_acre_inset(0,0));block_kind=1;
    inset=0;assert(!af_insect_acre_inset(0,0));inset=1;
    assert(ground_checks==2);
}
static void ownership_and_culling(void) {
    aINS_INSECT_ACTOR *i=reset();ACTOR *a=(ACTOR *)i;visible=0;
    assert(af_insect_occupied_acre(0,0) && !af_insect_occupied_acre(1,0));
    i->exist_flag=0;controller.insects[AF_INSECT_RELEASE_SLOT].exist_flag=1;
    assert(!af_insect_occupied_acre(0,0)); /* release/held slot is excluded */
    controller.insects[1].exist_flag=1;assert(af_insect_occupied_acre(0,0));
    controller.insects[1].exist_flag=controller.insects[AF_INSECT_RELEASE_SLOT].exist_flag=0;i->exist_flag=1;
    a->actor_specific=1;af_v3_insect_slot(i,af_insect_game);assert(destructions==1);
    i=reset();a=(ACTOR *)i;visible=0;a->state_bitfield=0;a->player_distance_xz=601;a->block_x=1;
    af_v3_insect_slot(i,af_insect_game);assert(destructions==1 && !body_calls);
    i=reset();a=(ACTOR *)i;visible=0;a->state_bitfield=0x40;
    af_v3_insect_slot(i,af_insect_game);assert(!(a->state_bitfield&0x40) && !destructions);
    aINS_INSECT_ACTOR copy=*i;assert(af_v3_insect_slot(&copy,af_insect_game)==-1);
    i->type=0;copy=*i;assert(af_v3_insect_slot(i,af_insect_game)==0 && !memcmp(i,&copy,sizeof(copy)));
}
static void primitives(void) {
    assert(af_insect_ball_position()==&af_insect_ball);
    af_insect_demo_clip=NULL;af_insect_reset_flag=0;assert(!af_insect_demo_active());
    af_insect_reset_flag=1;assert(af_insect_demo_active());
    af_insect_reset_flag=0;af_insect_demo_clip=&game;assert(af_insect_demo_active());
    af_insect_demo_clip=NULL;assert(!af_insect_demo_active());
    for (unsigned i=0;i<128;i++) assert(af_insect_is_stump(i)==((i>=1&&i<=4)||(i>=123&&i<=126)));
    assert(!af_insect_is_flower(0x83B) && af_insect_is_flower(0x83C));
    assert(af_insect_is_flower(0x84D) && !af_insect_is_flower(0x84E));
    main_index=0x2F;assert(af_insect_putting_net_away(af_insect_game));
    main_index=0x2E;assert(!af_insect_putting_net_away(af_insect_game));
    unit=0xFFFFFFCC;assert(mCoBG_Wpos2BgAttribute_Original((xyz_t){0})==12);
    assert(mCoBG_CheckHole_OrgAttr(22) && mCoBG_CheckHole_OrgAttr(62));
    assert(!mCoBG_CheckHole_OrgAttr(3) && !mCoBG_CheckHole_OrgAttr(12));
}
static void player_events(void) {
    reset();
    *(xyz_t *)(player_storage.bytes+0xD10)=(xyz_t){120,5,200};
    void (*calls[])(void *,GAME *,int,int)={af_insect_player_axe,af_insect_player_rock,af_insect_player_dig};
    const float frames[]={15,13,14};
    for (unsigned i=0;i<3;i++) {
        expected_frame=frames[i];frame_hit=0;af_v3_insect_events_reset();
        calls[i](player,af_insect_game,0,0);assert(!af_insect_events()->pl_action);
        frame_hit=1;unit_valid=0;calls[i](player,af_insect_game,0,0);
        assert(!af_insect_events()->pl_action);unit_valid=1;
        calls[i](player,af_insect_game,0,0);
        assert(af_insect_events()->pl_action==(int)i+1);
        assert(af_insect_events()->pl_action_ut_x==3 && af_insect_events()->pl_action_ut_z==5);
        for (int step=0;step<2;step++) {
            af_insect_begin_step(step);assert(af_insect_events()->pl_action==(int)i+1);
        }
    }
    assert(footprints==9);
    const u32 plain[]={0x804,0x861,0x868};
    for (unsigned i=0;i<3;i++) {
        af_v3_insect_events_reset();assert(!af_insect_player_tree(plain[i],4,6));
        assert(af_insect_events()->pl_action==aINS_PL_ACT_SHAKE_TREE);
        assert(af_insect_events()->pl_action_ut_x==4 && af_insect_events()->pl_action_ut_z==6);
    }
    const u32 other[]={0x800,0x803,0x80C,0x831,0x867,0x7F,0x80,0x5E,0x81};
    for (unsigned i=0;i<sizeof(other)/sizeof(*other);i++) {
        af_v3_insect_events_reset();int result=af_insect_player_tree(other[i],4,6);
        assert(result==(other[i]==0x5E || other[i]==0x81));assert(!af_insect_events()->pl_action);
    }
    assert(bee_checks==12);
    af_v3_insect_unbind_controller(&controller);expected_frame=14;
    af_insect_player_dig(player,af_insect_game,0,0);af_insect_player_tree(0x804,4,6);
    assert(!af_insect_events()->pl_action && footprints==10);
}
int main(void) {
    connected_slot();terrain_and_stress();ownership_and_culling();primitives();player_events();
    puts("Shared native adapter: movement, collision, stress, capture, lifetime, and cleanup pass");
}
