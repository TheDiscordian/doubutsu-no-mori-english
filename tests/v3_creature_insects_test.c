/* Execute the complete converted bodies with controlled engine inputs.
 * Engine outputs are observed here, not claimed as native engine verification.
 */
#include "creature_insects.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
struct GAME { int unused; };
static GAME game;
static AfInsectController controller;
static PLAYER_ACTOR player;
static xyz_t ball={100000,100000,100000};
static uintptr_t caught;
static void *stung;
static int demo,flower,stump,wet,grounded,away,environment_calls,effects,requests;
static u16 foreground;

const xyz_t *af_insect_ball_position(void) {return &ball;}
int af_insect_demo_active(void) {return demo;}
int af_insect_same_block(const ACTOR *a,const GAME *g) {(void)a;(void)g;return 1;}
u32 af_insect_source_frame(const GAME *g) {(void)g;return 20;}
PLAYER_ACTOR *af_insect_player(GAME *g) {(void)g;return &player;}
int af_insect_is_flower(mActor_name_t item) {(void)item;return flower;}
int af_insect_is_stump(mActor_name_t item) {(void)item;return stump;}
int af_insect_putting_net_away(GAME *g) {(void)g;return away;}
void af_insect_effect(int kind,xyz_t p,int p0,s16 angle,GAME *g,mActor_name_t item,int p1,int p2) {
    (void)p;(void)p0;(void)angle;(void)g;(void)item;(void)p1;(void)p2;
    assert(kind==69 || kind==70 || kind==84);effects++;
}
f32 fqrand(void) {return 0.5f;}
f32 sin_s(s16 n) {return sinf(n*(6.28318530718f/65536.0f));}
f32 cos_s(s16 n) {return cosf(n*(6.28318530718f/65536.0f));}
s16 atans_table(f32 z,f32 x) {return (s16)(atan2f(x,z)*(65536.0f/6.28318530718f));}
int chase_f(f32 *v,f32 goal,f32 step) {
    float d=goal-*v;
    if (fabsf(d)<=step) {*v=goal;return 1;}
    *v+=d<0?-step:step;return 0;
}
int chase_angle(s16 *v,s16 goal,s16 step) {
    int d=(s16)(goal-*v);
    if (ABS(d)<=step) {*v=goal;return 1;}
    *v+=(s16)(d<0?-step:step);return 0;
}
void xyz_t_move(xyz_t *a,const xyz_t *b) {*a=*b;}
void none_proc1(void) {}
int mFI_Wpos2UtNum(int *x,int *z,xyz_t p) {*x=(int)p.x/40;*z=(int)p.z/40;return 1;}
int mFI_BkNum2WposXZ(f32 *x,f32 *z,int bx,int bz) {*x=bx*640.0f;*z=bz*640.0f;return 1;}
mActor_name_t *mFI_GetUnitFG(xyz_t p) {(void)p;return &foreground;}
f32 mCoBG_GetBgY_OnlyCenter_FromWpos(xyz_t p,f32 d) {(void)p;(void)d;return 0;}
f32 mCoBG_GetBgY_OnlyCenter_FromWpos2(xyz_t p,f32 d) {(void)p;(void)d;return 100;}
f32 mCoBG_GetBgY_AngleS_FromWpos(s_xyz *angle,xyz_t p,f32 d) {(void)angle;(void)p;(void)d;return 0;}
f32 mCoBG_GetWaterHeight_File(xyz_t p,const char *file,int line) {(void)p;(void)file;(void)line;return 0;}
int mCoBG_GetWaterFlow(xyz_t *p,u32 attr) {(void)attr;*p=(xyz_t){1,0,0};return 1;}
u32 mCoBG_Wpos2BgAttribute_Original(xyz_t p) {(void)p;return (u32)wet;}
u32 mCoBG_Wpos2Attribute(xyz_t p,s8 *dig) {(void)p;(void)dig;return 0;}
int mCoBG_CheckWaterAttribute(u32 attr) {return attr!=0;}
int mCoBG_CheckHole_OrgAttr(u32 attr) {(void)attr;return 0;}
int mPlib_Check_StopNet(xyz_t *p) {(void)p;return 0;}
int mPlib_Check_DigScoop(xyz_t *p) {(void)p;return 0;}
int mPlib_Check_HitAxe(xyz_t *p) {(void)p;return 0;}
uintptr_t mPlib_Get_item_net_catch_label(void) {return caught;}
int mPlib_Check_stung_mosquito(void *p) {return p==stung;}
int mPlib_request_main_stung_mosquito_type1(void *p) {requests++;stung=p;return 1;}
void sAdo_OngenPos(u32 owner,u32 sound,xyz_t *p) {(void)owner;(void)sound;(void)p;}
void sAdo_OngenTrgStart(u32 sound,xyz_t *p) {(void)sound;(void)p;}
void af_insect_environment(aINS_INSECT_ACTOR *insect,GAME *g) {
    (void)g;environment_calls++;
    ACTOR *a=(ACTOR *)insect;
    a->bg_collision_check.result.on_ground=grounded;
    a->player_distance_xz=10;
    a->player_distance_y=0;
}
void af_insect_position_integrate(ACTOR *a) {
    a->world.position.x+=a->position_speed.x*0.5f;
    a->world.position.y+=a->position_speed.y*0.5f;
    a->world.position.z+=a->position_speed.z*0.5f;
}

static aINS_INSECT_ACTOR *start(unsigned n,int release) {
    assert(n<8);
    aINS_INSECT_ACTOR *i=controller.insects+n%3;
    memset(i,0,sizeof(*i));
    memset(i->col_pipe,0xA5,sizeof(i->col_pipe));
    af_v3_insect_bind_controller(&controller);
    caught=0;stung=NULL;demo=stump=wet=grounded=away=environment_calls=effects=requests=0;
    flower=1;
    memset(&player,0,sizeof(player));player.actor_class.world.position.x=100;
    i->exist_flag=1;i->type=(int)n+32;
    ACTOR *a=(ACTOR *)i;
    a->actor_specific=(s16)release;
    a->world.position=(xyz_t){320,20,320};a->home=a->world;
    a->scale=(xyz_t){0.01f,0.01f,0.01f};a->drawn=1;
    assert(af_v3_insect_init(i,&game)==1);
    for (unsigned p=0;p<sizeof(i->col_pipe);p++) assert(i->col_pipe[p]==0xA5);
    assert(i->item==0x2D20+n);
    return i;
}
static void advance(aINS_INSECT_ACTOR *i) {assert(af_v3_insect_tick(i,&game)==1);}

static void category_release(void) {
    for (unsigned n=0;n<8;n++) {
        aINS_INSECT_ACTOR *i=start(n,1);
        assert(i->life_time==0 && i->alpha_time==80 && i->alpha0==255);
        assert(i->insect_flags.bit_1 && i->insect_flags.bit_2);
        assert(af_insect_extra(i)->ut_x==-1 && af_insect_extra(i)->ut_z==-1);
        assert(af_v3_insect_catch_range(i)==0.0f);
        advance(i);
        assert(environment_calls==2 && i->alpha_time==78);
        for (unsigned f=0;f<45;f++) advance(i);
        assert(i->insect_flags.destruct && i->alpha0==0);
    }
}
static void digging_and_rocks(void) {
    aINS_INSECT_ACTOR *i=start(1,0);
    assert(i->action==2 && !i->tools_actor.actor_class.drawn);
    assert(af_insect_extra(i)->ut_x==8 && af_insect_extra(i)->ut_z==8);
    assert(af_v3_insect_event(3,7,8));
    advance(i);assert(i->action==2 && !effects);
    assert(af_v3_insect_event(3,8,8));
    advance(i);assert(i->action==3 && effects==3 && i->tools_actor.actor_class.drawn);
    grounded=1;advance(i);assert(i->action==0);
    for (int action=1;action<=2;action++) {
        i=start(4,0);assert(i->action==3);
        assert(af_v3_insect_event(action,8,7));
        advance(i);assert(i->action==3);
        assert(af_v3_insect_event(action,8,8));advance(i);assert(i->action==4 && i->tools_actor.actor_class.drawn);
        /* First substep lands/stops; the second resumes flight from the rock
         * because this fixture has no nearby player/tool stress. */
        grounded=1;advance(i);assert(i->action==0);
    }
}
static void trees_and_flowers(void) {
    for (unsigned n=3;n<=5;n+=2) {
        aINS_INSECT_ACTOR *i=start(n,0);
        assert(i->action==2 && !i->tools_actor.actor_class.drawn && i->insect_flags.bit_1);
        assert(af_v3_insect_event(4,7,8));
        advance(i);assert(i->action==2);
        assert(af_v3_insect_event(4,8,8));advance(i);
        assert(i->action==3 && i->tools_actor.actor_class.drawn && !i->insect_flags.bit_1);
        assert(af_v3_insect_catch_range(i)==8.0f);
        stump=1;advance(i);
        assert(i->action==9 && i->move_proc==af_v3_insect_position);
        ((ACTOR *)i)->world.position.y=-1;advance(i);assert(i->action==1);
    }
    aINS_INSECT_ACTOR *i=start(0,0);
    int timer=i->timer;
    advance(i);assert(i->timer==timer-2 && i->life_time==215998);
    flower=0;advance(i);assert(i->action==1 && i->insect_flags.bit_2);
    assert(i->target_speed==0.1f);
    /* Explicit GAFE01-r0 behaviour, not the later Australian snail bugfix. */
    i=start(0,0);caught=(uintptr_t)i;advance(i);assert(i->action==2);
}
static void water_and_mosquito(void) {
    aINS_INSECT_ACTOR *i=start(2,0);
    assert(i->action==2 && effects==1);
    i->tools_actor.actor_class.speed=i->speed_step=0;
    advance(i);assert(i->action==3 && i->timer==29);
    for (unsigned f=0;f<16;f++) advance(i);
    assert(i->action==2 && effects==2);
    /* Shared ground-insect drowning transitions emit the donor splash. */
    i=start(1,1);grounded=wet=1;
    advance(i);assert(i->action==4 && i->insect_flags.bit_1);
    ((ACTOR *)i)->world.position.y=-20;advance(i);
    assert(i->insect_flags.destruct && effects==1);
    i=start(7,0);
    advance(i);assert(i->action==4);
    for (unsigned f=0;f<91;f++) advance(i);
    assert(requests==1 && i->action==5);
    stung=NULL;advance(i);assert(i->action==0 && i->insect_flags.bit_2);
    i=start(7,0);demo=1;advance(i);assert(i->action==0);
}
static void bounds(void) {
    assert(!af_v3_insect_init(NULL,&game));
    assert(!af_v3_insect_tick(NULL,&game));
    aINS_INSECT_ACTOR *i=start(0,0),before;
    for (int n=-1;n<=41;n++) if (n<32 || n>39) {
        i->type=n;before=*i;
        assert(!af_v3_insect_init(i,&game) && !af_v3_insect_tick(i,&game));
        assert(!memcmp(i,&before,sizeof(*i)));
    }
    before.type=32;assert(af_v3_insect_init(&before,&game)==-1);
    assert(!af_insect_extra(&before));
    assert(!af_v3_insect_event(5,1,1) && !af_v3_insect_event(1,-1,1));
    assert(!af_v3_insect_event(1,1,32768));
    assert(af_v3_insect_event(4,8,8));
    af_v3_insect_events_reset();assert(af_insect_events()->pl_action==0);
    af_v3_insect_unbind_controller(&controller);
    assert(!af_v3_insect_event(1,1,1) && !af_insect_extra(i));
    assert(af_v3_insect_init(i,&game)==0); /* still an out-of-range identity */
    i->type=32;assert(af_v3_insect_init(i,&game)==-1);
}
int main(void) {
    category_release();digging_and_rocks();trees_and_flowers();water_and_mosquito();bounds();
    puts("Eight species: source behaviour, shared stepping, interactions, and bounds pass");
    return 0;
}
