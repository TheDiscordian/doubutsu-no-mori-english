/* Native-field adapter against the complete donor decision function. Engine
 * services are doubles: this does not claim native movement or visual playback. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "holiday_motion.h"
typedef unsigned char u8;
typedef unsigned short u16;
typedef AFHolidayPosition xyz_t;
static AFHolidayNpc npc;
static AFNpcExtra record={.name=0xD090,.profile=0xCC,.actor_bytes=sizeof(AFHolidayNpc)};
const AFHolidayCane af_holiday_cane={.duration=29,.start=1,.end=29,.mode=1,.morph=-5};
#define B(o) (((unsigned char *)&npc)[o])
#define W(o) (*(unsigned int *)((unsigned char *)&npc+(o)))
#define S(o) (*(short *)((unsigned char *)&npc+(o)))
#define F(o) (*(float *)((unsigned char *)&npc+(o)))
static int owner=1,fatigue,mood,path_ok,behind,range_ok,roll,ux,uz,bx,bz;
typedef struct {unsigned calls,rng,paths,turns,ranges,action,type,priority;u16 args[6];} Observation;
static Observation seen;
static unsigned old_animation,keyframes,old_decisions,old_inits,blocks,sounds;
static int last_index,last_talk,last_subtype;
const AFNpcExtra *af_v3_npc_extra_owned(const void *a) {assert(a==&npc);return owner?&record:NULL;}
int af_holiday_fatigue(void *a) {(void)a;return fatigue;}
int af_holiday_mood(void *a) {(void)a;return mood;}
float af_holiday_random_native(void) {++seen.rng;return (roll+0.125f)*0.1f;}
int af_holiday_move_next(u16 *p,void *a) {
    (void)a;++seen.paths;if(path_ok) {p[2]=123;p[3]=456;}return path_ok;
}
int af_holiday_ones_way(void *a,u16 *p) {(void)a;assert(p[2]==123 && p[3]==456);++seen.turns;return behind;}
int af_holiday_range(void *a,void *unused,xyz_t p,u8 type) {
    (void)a;assert(!unused && p.x==-111 && p.z==222 && type==1);++seen.ranges;return range_ok;
}
int af_holiday_request_native(void *a,u8 priority,u8 action,u8 type,u16 *p) {
    (void)a;++seen.calls;seen.priority=priority;seen.action=action;seen.type=type;
    memcpy(seen.args,p,sizeof(seen.args));return 1;
}
void af_holiday_wander_original(void *a) {assert(a==&npc);++old_decisions;}
void af_holiday_wander_init_original(void *a,void *g) {assert(a==&npc && g==npc.game);++old_inits;}
void af_holiday_unit(int *x,int *z,xyz_t p) {assert(p.x==120 && p.y==17 && p.z==240);*x=ux;*z=uz;}
void af_holiday_block(int *x,int *z,xyz_t p) {assert(p.x==120 && p.y==88 && p.z==240);*x=bx;*z=bz;++blocks;}
void af_holiday_schedule_native(void *a,void *g,u8 type) {
    assert(a==&npc && g==npc.game && type==4);af_holiday_motion_wander_init(a,g);
}
void af_holiday_sound_native(unsigned a,unsigned sound,const void *p) {
    assert(a==(unsigned)(__UINTPTR_TYPE__)&npc && sound==47 && p==(unsigned char *)&npc+0x28);++sounds;
}
void af_holiday_animation_original(void *a,int index,int talk) {
    assert(a==&npc);++old_animation;last_index=index;last_talk=talk;last_subtype=B(0x729);
    W(0x704)=index;W(0x190)=99;
}
void af_holiday_keyframe_init(void *kf,void *skeleton,const void *animation,float start,float end,
        float frame,float speed,float morph,int mode,void *diff) {
    assert(kf==(unsigned char *)&npc+0x354 && (__UINTPTR_TYPE__)skeleton==0x80601234);
    assert(animation==&af_holiday_cane && start==1 && end==29 && frame==1 && speed==1.5f);
    assert(morph==-5 && mode==1 && !diff && B(0x729)==3);++keyframes;
}

/* Structures describe the donor function's semantics, not donor offsets. */
typedef struct {int current_type,saved_type;} mNPS_schedule_c;
typedef struct {
    struct {int idx;short move_x,move_z;} action;
    struct {int collision_flag;} collision;
    struct {u8 range_type;} movement;
    struct {int idx;} think;
    struct {mNPS_schedule_c *schedule;} npc_info;
} NPC_ACTOR;
typedef NPC_ACTOR ACTOR;
enum {FALSE=0,TRUE=1,aNPC_REQUEST_ARG_NUM=6,aNPC_ACT_TYPE_DEFAULT=0,
    aNPC_ACT_TYPE_TO_POINT=3,aNPC_ACT_WAIT=0,aNPC_ACT_WALK=1,aNPC_ACT_RUN=2,
    aNPC_ACT_TURN=3,aNPC_THINK_WALK_WANDER=2,mNpc_FEEL_SLEEPY=4,mNPS_SCHED_FIELD=0};
#define bzero(p,n) memset(p,0,n)
#define RANDOM(n) ((int)(af_holiday_random_native()*(n)))
#define aNPC_IS_NRM_NPC(n) (0)
#define mNpc_GetNpcLooks(n) (0)
#define aNPC_check_fatigue af_holiday_fatigue
#define aNPC_get_feel_info af_holiday_mood
#define aNPC_moveRangeCheck2 af_holiday_range
#define aNPC_think_wander_move_next af_holiday_move_next
#define aNPC_think_wander_check_ones_way af_holiday_ones_way
#define aNPC_set_request_act af_holiday_request_native
#include "reference-holiday-wander.inc"

int main(void) {
    npc.constructed=1;npc.actor.think=4;npc.game=&npc;
    S(0x7CC)=-111;S(0x7CE)=222;B(0x8CF)=1;
    unsigned comparisons=0;
    for(unsigned bits=0;bits<128;++bits)for(roll=0;roll<10;++roll) {
        fatigue=bits&1;mood=bits&2?4:0;path_ok=!!(bits&4);behind=!!(bits&8);
        range_ok=!!(bits&16);B(0x7C5)=bits&32?3:0;B(0x910)=!!(bits&64);
        NPC_ACTOR donor={.action={B(0x7C5),-111,222},.collision={B(0x910)},
            .movement={1},.think={aNPC_THINK_WALK_WANDER}};
        seen=(Observation){0};af_holiday_motion_decide(&npc);Observation port=seen;
        seen=(Observation){0};aNPC_think_wander_decide_next(&donor);
        assert(!memcmp(&port,&seen,sizeof(seen)));assert(seen.action!=2);++comparisons;
    }
    owner=0;af_holiday_motion_decide(&npc);assert(old_decisions==1);
    assert(!af_holiday_motion_bind(&npc));owner=1;npc.actor.think=6;
    af_holiday_motion_decide(&npc);assert(old_decisions==2);npc.actor.think=4;
    assert(af_holiday_motion_bind(&npc));
    F(0x28)=120;F(0x2C)=17;F(0x30)=240;F(0x10)=88;bx=2;bz=3;
    for(ux=0;ux<16;++ux)for(uz=0;uz<16;++uz) {
        unsigned before=blocks;npc.ops.walk_wander(&npc);
        assert(blocks-before==(unsigned)(ux==0 || ux==15 || uz==0 || uz==15));
        if(blocks!=before)assert(!B(0x8CF) && F(0x8D0)==1600 && F(0x8D4)==2240 && F(0x10)==88);
    }
    assert(old_inits==256);owner=0;af_holiday_motion_wander_init(&npc,npc.game);
    assert(old_inits==257);owner=1;
    F(0x73C)=1.5f;W(0x36C)=0x80601234;
    for(int type=0;type<4;++type) {
        B(0x729)=type;unsigned before=keyframes;
        af_holiday_motion_animation(&npc,67,1);
        assert(last_subtype==(type==3?0:type) && B(0x729)==type);
        assert(keyframes-before==(unsigned)(type==3));
        assert(last_index==67 && last_talk==1 && W(0x190)==(type==3?0:99));
    }
    owner=0;B(0x729)=1;af_holiday_motion_animation(&npc,5,0);
    assert(last_subtype==1 && B(0x729)==1 && keyframes==1);owner=1;
    assert(af_holiday_motion_resources(&npc) && keyframes==2);
    npc.ops.repeat_animation(&npc,1);assert(W(0x1AC)==1 && last_index==67 && keyframes==3);
    AFHolidayMotion m;npc.ops.motion(&npc,&m);assert(m.clapping);
    npc.ops.clap_sound(&npc);assert(sounds==1);
    npc.ops.repeat_animation(&npc,0);npc.ops.motion(&npc,&m);assert(!m.clapping && last_index==5);
    printf("holiday motion: %u donor decisions, edge init, complete cane arguments, and native fallback pass\n",comparisons);
}
