/* The complete checked donor think file runs beside the port. Native event,
 * movement, and demo services are doubles here, not gameplay verification. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "holiday_actor.h"
typedef unsigned char u8;
typedef unsigned short u16;
typedef short s16;
typedef unsigned int u32;
typedef float f32;
typedef int GAME_PLAY;
typedef struct NPC NPC_ACTOR;
typedef void (*aNPC_TALK_REQUEST_PROC)(NPC_ACTOR *,GAME_PLAY *);
typedef struct {float x,y,z;} Position;
typedef struct {struct {Position position;} world;struct {int weight;} status_data;} ACTOR;
struct NPC {
    ACTOR actor_class;
    struct {int idx,step;} action;
    struct {float dst_pos_x,dst_pos_z;} movement;
    struct {int animation_id;struct {struct {struct {int mode;} frame_control;} keyframe;} main_animation;} draw;
    struct {unsigned demo_flg;int hide_request;} condition_info;
    struct {unsigned interrupt_flags;void (*think_proc)(NPC_ACTOR *,GAME_PLAY *,int);} think;
    struct {aNPC_TALK_REQUEST_PROC talk_request_proc;} talk_info;
};
typedef struct Soncho NPC_SONCHO2;
typedef void (*aEV_SONCHO2_PROC)(NPC_SONCHO2 *,GAME_PLAY *);
struct Soncho {
    NPC_ACTOR npc_class;
    aEV_SONCHO2_PROC _994;
    unsigned short year;
    u8 month,day;
    short timer,center_x,center_z,goal_x,goal_z;
    u8 think_idx,think,talk,_9ac,event;
    unsigned item;
};
enum {
    FALSE,TRUE,mFI_UT_WORLDSIZE_X=40,mFI_UT_WORLDSIZE_Z=40,
    aES2_THINK_0=0,aES2_THINK_AEROBICS,aES2_THINK_BALL_TOSS,aES2_THINK_3,aES2_THINK_4,
    aES2_THINK_FOOT_RACE,aES2_THINK_LIGHTHOUSE_QUEST_START,aES2_THINK_7,aES2_THINK_8,
    aES2_THINK_9,aES2_THINK_a,aES2_THINK_b,aES2_THINK_c,aES2_THINK_d,aES2_THINK_TUG_O_WAR,
    aES2_TALK_0=0,aES2_TALK_1,aES2_TALK_2,aES2_TALK_LIGHTHOUSE_QUEST_START_1,
    aES2_TALK_LIGHTHOUSE_QUEST_START_2,aES2_TALK_5,aES2_TALK_6,aES2_TALK_7,aES2_TALK_8,
    aES2_TALK_9,aES2_TALK_a,aES2_TALK_TUG_O_WAR,
    aNPC_ACT_WAIT=0,aNPC_ACT_WALK,aNPC_ACT_RUN,aNPC_ACT_TURN,aNPC_ACT_TURN2,
    aNPC_ACT_TYPE_DEFAULT=0,aNPC_ACT_TYPE_TO_POINT=3,aNPC_ACT_OBJ_DEFAULT=0,
    aNPC_COND_DEMO_SKIP_FORWARD_CHECK=0x20,aNPC_COND_DEMO_SKIP_FOOTSTEPS=0x800,
    aNPC_THINK_PROC_INIT=0,aNPC_THINK_PROC_MAIN=1,aNPC_THINK_SPECIAL=9,
    aNPC_THINK_TYPE_INIT=0,aNPC_THINK_TYPE_CHK_INTERRUPT=1,aNPC_THINK_TYPE_MAIN=2,
    aNPC_SCHEDULE_PROC_INIT=0,aNPC_SCHEDULE_PROC_MAIN=1,aNPC_SCHEDULE_TYPE_WALK_WANDER=5,
    mSC_EVENT_SPRING_SPORTS_FAIR=8,mSC_EVENT_FALL_SPORTS_FAIR=20,
    mSC_SPECIAL_EVENT_JAN_VACATION=101,mSC_SPECIAL_EVENT_FEB_VACATION=102,
    mSC_EVENT_NEW_YEARS_EVE_COUNTDOWN=26,mPr_FOREIGNER=4,lbRTC_DECEMBER=12,
    mEv_EVENT_SPORTS_FAIR_FOOT_RACE=123,aTKC_FLAG_RACE_ACTIVE=1,
    MASSTYPE_HEAVY=254,cKF_FRAMECONTROL_REPEAT=1,aNPC_ANIM_CLAP1=67,aNPC_ANIM_WAIT1=5,NA_SE_2F=47
};
typedef struct {unsigned flags;short pos_0A[1][2];} aEv_tokyoso_c;
typedef struct {
    NPC_SONCHO2 npc;
    unsigned player_no,event,field,after,roll,variant,deleted,wanders,sounds,randoms,requests;
    unsigned priority,requested_action,requested_type;
    short requested_x,requested_z;
    int shrine,race,interrupt;
    short shrine_pos[3];aEv_tokyoso_c race_data;
    unsigned claimed[28],gives,marks,free,restores,demos,quests;
    AFHolidayAction transport;
} Env;
static Env *ref;
#define Common_Get(f) (ref->f)
static void aES2_setup_think_proc(NPC_SONCHO2 *,GAME_PLAY *,u8);
static void mActor_NONE_PROC1(NPC_ACTOR *a,GAME_PLAY *p) {(void)a;(void)p;}
static void aES2_norm_talk_request(NPC_ACTOR *a,GAME_PLAY *p) {(void)a;(void)p;}
static int request(void *v,unsigned priority,unsigned action,unsigned type,short x,short z) {
    Env *e=v;++e->requests;
    if(priority<e->priority)return 0;
    e->priority=priority;e->requested_action=action;e->requested_type=type;
    e->requested_x=x;e->requested_z=z;return 1;
}
static int aES2_set_request_act(NPC_SONCHO2 *s,u8 priority,int action,int type,int obj,int x,int z) {
    assert(s==&ref->npc && obj==0);return request(ref,priority,action,type,x,z);
}
static unsigned event(void *v) {return ((Env *)v)->event;}
static unsigned field_event(void *v) {return ((Env *)v)->field;}
static u8 mSC_get_soncho_event(void) {return event(ref);}
static u8 mSC_get_soncho_field_event(void) {return field_event(ref);}
static int after(void *v) {return ((Env *)v)->after;}
static int mSC_LightHouse_Talk_After_Check(void) {return after(ref);}
static int variant(void *v,unsigned event,unsigned gender,unsigned *out) {
    (void)gender;assert(event==((Env *)v)->event);*out=((Env *)v)->variant;return 1;
}
static unsigned mSC_trophy_item(unsigned event) {assert(event==ref->event);return ref->variant;}
static int shrine(void *v,short p[3]) {
    Env *e=v;if(!e->shrine)return 0;memcpy(p,e->shrine_pos,sizeof(e->shrine_pos));return 1;
}
static int mFI_SetOyasiroPos(short p[3]) {return shrine(ref,p);}
static void *mEv_get_save_area(int event,int type) {
    assert(event==mEv_EVENT_SPORTS_FAIR_FOOT_RACE && type==8);return ref->race?&ref->race_data:NULL;
}
static int runner(void *v,short p[2]) {
    Env *e=v;if(!e->race || !(e->race_data.flags&1))return 0;
    memcpy(p,e->race_data.pos_0A[0],4);return 1;
}
static void motion(void *v,AFHolidayMotion *m) {
    NPC_ACTOR *n=&((Env *)v)->npc.npc_class;
    *m=(AFHolidayMotion){n->actor_class.world.position.x,n->actor_class.world.position.z,
        n->movement.dst_pos_x,n->movement.dst_pos_z,n->action.idx,n->action.step,
        n->draw.animation_id==aNPC_ANIM_CLAP1};
}
static void force_action(void *v,unsigned action) {((Env *)v)->npc.npc_class.action.idx=action;}
static void weight(void *v,unsigned w) {((Env *)v)->npc.npc_class.actor_class.status_data.weight=w;}
static void hide(void *v,int h) {((Env *)v)->npc.npc_class.condition_info.hide_request=h;}
static void clear_interrupts(void *v) {((Env *)v)->npc.npc_class.think.interrupt_flags=0;}
static void flags(void *v,unsigned flags,int replace) {
    unsigned *p=&((Env *)v)->npc.npc_class.condition_info.demo_flg;
    *p=replace?flags:*p|flags;
}
static void wander(void *v) {++((Env *)v)->wanders;}
static void destination(void *v,float x,float z) {
    NPC_ACTOR *n=&((Env *)v)->npc.npc_class;n->movement.dst_pos_x=x;n->movement.dst_pos_z=z;
}
static unsigned random_value(void *v,unsigned bound) {
    Env *e=v;++e->randoms;assert(e->roll<bound);return e->roll;
}
static float random_f(float bound) {assert(bound==1);return random_value(ref,2)*.5f;}
#define RANDOM_F(n) random_f(n)
static void repeat_animation(void *v,int clap) {
    NPC_ACTOR *n=&((Env *)v)->npc.npc_class;
    n->draw.main_animation.keyframe.frame_control.mode=1;
    n->draw.animation_id=clap?aNPC_ANIM_CLAP1:aNPC_ANIM_WAIT1;
}
static void clap_sound(void *v) {++((Env *)v)->sounds;}
static void sAdo_OngenPos(u32 actor,int sound,Position *p) {
    (void)actor;assert(sound==47 && p==&ref->npc.npc_class.actor_class.world.position);clap_sound(ref);
}
static void remove_actor(void *v) {++((Env *)v)->deleted;}
static void Actor_delete(ACTOR *p) {assert(p==&ref->npc.npc_class.actor_class);remove_actor(ref);}
static void talk_request(void *v,int enabled) {
    ((Env *)v)->npc.npc_class.talk_info.talk_request_proc=enabled?aES2_norm_talk_request:mActor_NONE_PROC1;
}
static void change_schedule(NPC_ACTOR *n,GAME_PLAY *p,int s) {
    (void)p;assert(n==&ref->npc.npc_class && s==aNPC_SCHEDULE_TYPE_WALK_WANDER);wander(ref);
}
static void set_destination(NPC_ACTOR *n,float x,float z) {assert(n==&ref->npc.npc_class);destination(ref,x,z);}
static void animation_init(ACTOR *a,int anim,int force) {
    assert(a==&ref->npc.npc_class.actor_class && !force);ref->npc.npc_class.draw.animation_id=anim;
}
static int think_dispatch(NPC_ACTOR *n,GAME_PLAY *p,int state,int type) {
    assert(n==&ref->npc.npc_class);
    if(type==aNPC_THINK_TYPE_CHK_INTERRUPT)return ref->interrupt;
    assert(state==aNPC_THINK_SPECIAL || state==-1);
    n->think.think_proc(n,p,type==aNPC_THINK_TYPE_INIT?0:1);return 0;
}
static struct {
    void (*chg_schedule_proc)(NPC_ACTOR *,GAME_PLAY *,int);
    void (*set_dst_pos_proc)(NPC_ACTOR *,float,float);
    void (*animation_init_proc)(ACTOR *,int,int);
    int (*think_proc)(NPC_ACTOR *,GAME_PLAY *,int,int);
} clip={change_schedule,set_destination,animation_init,think_dispatch};
#define CLIP(name) (&clip)
#include "reference-holiday-think.inc"

static void request_demo(void *v) {++((Env *)v)->demos;}
static void transport(void *v,const AFHolidayAction *a) {((Env *)v)->transport=*a;}
static void restore(void *v) {++((Env *)v)->restores;}
static AFHolidayActorOps ops(Env *e) {
    return (AFHolidayActorOps){e,event,field_event,variant,shrine,runner,motion,request,
        force_action,weight,hide,clear_interrupts,flags,wander,destination,repeat_animation,
        clap_sound,remove_actor,random_value,talk_request,request_demo,transport,restore};
}
static void same(const AFHolidayActor *a,const Env *e,const Env *r) {
    assert(a->think==r->npc.think_idx && a->return_think==r->npc.think);
    assert(a->suppress_request==r->npc._9ac);
    assert(a->date.year==r->npc.year && a->date.month==r->npc.month && a->date.day==r->npc.day);
    assert(a->event==r->npc.event && a->variant==r->npc.item);
    assert(a->timer==r->npc.timer && a->center_x==r->npc.center_x && a->center_z==r->npc.center_z);
    assert(a->goal_x==r->npc.goal_x && a->goal_z==r->npc.goal_z);
    assert(!memcmp(&e->npc.npc_class,&r->npc.npc_class,sizeof(NPC_ACTOR)));
    assert(!memcmp(&e->player_no,&r->player_no,sizeof(Env)-__builtin_offsetof(Env,player_no)));
}
static AFDiary diary,before;
static unsigned char table[1024];static unsigned table_bytes;
static void scenario(unsigned state,unsigned event_id,unsigned field,unsigned variant_bits) {
    Env e={0},r;AFHolidayActor a={.ready=1,.date={2007,1,1},.event=255};
    e.npc.year=2007;e.npc.month=1;e.npc.day=1;e.npc.event=255;
    e.event=event_id;e.field=field;e.after=(variant_bits>>4)&1;e.player_no=variant_bits&1?4:0;
    e.roll=variant_bits>>1&1;e.priority=variant_bits&4?5:1;
    e.shrine=variant_bits&8;e.race=variant_bits&8;e.race_data.flags=variant_bits&16?1:0;
    e.shrine_pos[0]=280;e.shrine_pos[1]=420;e.shrine_pos[2]=999;
    e.race_data.pos_0A[0][0]=123;e.race_data.pos_0A[0][1]=345;
    e.npc.npc_class.actor_class.world.position=(Position){32,0,64};r=e;ref=&r;
    AFHolidayActorOps o=ops(&e);af_diary_reset(&diary);
    AFHolidayWorld w={.diary=&diary,.today={2007,1,1},.player=e.player_no,.context=&e,.lighthouse_after=after};
    assert(af_holiday_actor_set_think(&a,&o,state)==1);aES2_setup_think_proc(&r.npc,NULL,state);
    same(&a,&e,&r);
    for(unsigned step=0;step<4 && !a.deleted;++step) {
        e.npc.npc_class.action.idx=r.npc.npc_class.action.idx=step%5;
        e.npc.npc_class.action.step=r.npc.npc_class.action.step=step&1?255:0;
        e.npc.npc_class.movement.dst_pos_x=r.npc.npc_class.movement.dst_pos_x=step&2?a.goal_x:0;
        e.npc.npc_class.movement.dst_pos_z=r.npc.npc_class.movement.dst_pos_z=step&2?a.goal_z:0;
        a.timer=r.npc.timer=step&1?1:0;
        assert(af_holiday_actor_think(&a,&w,&o)==1);aES2_think_main_proc(&r.npc,NULL);
        same(&a,&e,&r);
    }
}
static unsigned resolve(void *v,unsigned item) {(void)v;return item^0x4000u;}
static int claimed(void *v,unsigned event) {return ((Env *)v)->claimed[event];}
static int give(void *v,unsigned item) {
    Env *e=v;assert(item);if(!e->free)return 0;--e->free;++e->gives;return 1;
}
static void mark(void *v,unsigned event) {Env *e=v;e->claimed[event]=1;++e->marks;}
static int slots(void *v) {return ((Env *)v)->free;}
static void lighthouse_start(void *v) {++((Env *)v)->quests;}
static void connected(void) {
    Env e={0};e.event=0;e.free=15;
    AFHolidayActor a;AFHolidayActorOps o=ops(&e);af_diary_reset(&diary);
    AFHolidayWorld w={.diary=&diary,.dates={23,9,29},.today={2007,1,1},.player=2,
        .context=&e,.free_slots=slots,.lighthouse_after=after,.lighthouse_start=lighthouse_start,
        .rewards=table,.reward_bytes=table_bytes,.items={&e,resolve,claimed,give,mark}};
    before=diary;assert(af_holiday_actor_construct(&a,&w,0)==1);
    for(unsigned p=0;p<4;++p)if(p!=2)assert(!memcmp(diary.bytes+16+p*AF_DIARY_PLAYER,
        before.bytes+16+p*AF_DIARY_PLAYER,AF_DIARY_PLAYER));
    assert(af_holiday_actor_think_init(&a,&o)==1);
    assert(af_holiday_actor_think(&a,&w,&o)==1 && a.think==4 && e.wanders==1);
    before=diary;
    assert(af_holiday_actor_request(&a,&o)==0 && !e.demos);
    assert(af_holiday_actor_request(&a,&o)==1 && e.demos==1);
    assert(af_holiday_actor_prepare(&a,&w,&o)==1 && !e.randoms);
    assert(!memcmp(&diary,&before,sizeof(diary)) && !e.gives && !e.marks);
    assert(af_holiday_actor_start(&a,&w,&o)==1 && !a.talk_enabled);
    assert(af_diary_calendar_event_check(&diary,2,w.today,w.today,0)==1);
    assert(af_holiday_actor_start(&a,&w,&o)==0);
    assert(af_holiday_actor_talk(&a,&w,&o,1,0,0)==0 && a.talk.phase==1);
    assert(!e.gives && !e.marks);
    assert(af_holiday_actor_talk(&a,&w,&o,0,1,0)==0 && e.gives==1 && e.marks==1);
    assert(e.transport.effects==(AF_HOLIDAY_ITEM_NAME|AF_HOLIDAY_HANDOVER));
    assert(af_holiday_actor_talk(&a,&w,&o,0,1,0)==0 && e.gives==1);
    assert(af_holiday_actor_talk(&a,&w,&o,0,0,1)==1 && a.think==4 && e.wanders==2 && e.restores==1);
    assert(a.talk_enabled && a.suppress_request && !a.talk.active);
    assert(af_holiday_actor_prepare(&a,&w,&o)==1 && e.randoms==1);
    assert(e.transport.message==0x3286);
    before=diary;w.player=4;assert(af_holiday_actor_construct(&a,&w,0)==1);
    assert(!memcmp(&diary,&before,sizeof(diary)));
    AFHolidayActor saved=a;AFHolidayActorOps bad=o;bad.walk_wander=0;
    assert(af_holiday_actor_think_init(&a,&bad)==-1 && !memcmp(&a,&saved,sizeof(a)));
    assert(af_holiday_actor_set_think(&a,&o,15)==-1);
    e.event=8;e.field=4;assert(af_holiday_actor_think(&a,&w,&o)==-1);
}
int main(int argc,char **argv) {
    assert(argc==2);FILE *f=fopen(argv[1],"rb");assert(f);
    table_bytes=fread(table,1,sizeof(table),f);assert(feof(f));fclose(f);
    for(unsigned state=0;state<15;++state)for(unsigned bits=0;bits<32;++bits)
        scenario(state,255,0,bits);
    for(unsigned event=0;event<28;++event)for(unsigned field=0;field<4;++field)
        scenario(0,event,field,0);
    for(unsigned event=101;event<=102;++event)for(unsigned bits=0;bits<32;++bits)
        scenario(0,event,0,bits);
    connected();puts("holiday actor: complete donor think comparison and connected conversation/calendar/handover pass");
}
