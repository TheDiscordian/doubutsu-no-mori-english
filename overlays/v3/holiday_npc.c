/* Actual N64 NPC lifecycle/clip bridge. Actor registration and required services
 * must link together before any descriptor can expose these entry points. */
#include "holiday_npc.h"
#include "holiday_motion.h"
#include "holiday_world.h"
#ifndef __mips__
#error Native NPC bridge requires the checked o32 target
#endif
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
#define FN(at,ret,...) ((ret (*)(__VA_ARGS__))(at))
#define BYTE(a,at) (((u8 *)(a))[at])
#define WORD(a,at) (*(u32 *)((u8 *)(a)+(at)))
#define REAL(a,at) (*(float *)((u8 *)(a)+(at)))
#define CALLBACK(a,at) (*(void (**)(AFHolidayNpc *,void *,int))((u8 *)(a)+(at)))
#define TALK_REQUEST(a) (*(void (**)(AFHolidayNpc *,void *))((u8 *)(a)+0x91C))
_Static_assert(sizeof(void *)==4,"Native o32 pointers");
_Static_assert(__builtin_offsetof(AFHolidayNpc,game)==0x93C,"Complete native NPC prefix");
const unsigned int af_holiday_npc_bytes=sizeof(AFHolidayNpc);
static u32 clip(u32 offset) {return (*(const u32 *const *)0x80136EECu)[offset/4];}
static void none(AFHolidayNpc *a,void *game) {(void)a;(void)game;}
static void remove_actor(void *context) {
    AFHolidayNpc *a=context;a->actor.deleted=1;
    FN(0x800567E8u,void,void *)(a);
}
static int fail(AFHolidayNpc *a) {a->failed=1;remove_actor(a);return 0;}
int af_holiday_npc_world(AFHolidayNpc *a,AFHolidayWorld *w,unsigned int *gender) {
    if(!a || w!=&a->world)return 0;
    AFHolidayEventWorld event={0};
    if(!af_holiday_npc_event_world(a,&event) ||
            !af_holiday_world_bind(a,event.dates,gender))return 0;
    w->lighthouse_after=event.lighthouse_after;w->lighthouse_start=event.lighthouse_start;
    return 1;
}
static int refresh(AFHolidayNpc *a,void *game) {
    unsigned int gender;
    if(!a || !a->constructed || a->failed || a->actor.deleted)return 0;
    a->game=game;
    return af_holiday_npc_world(a,&a->world,&gender)?1:fail(a);
}
static void motion(void *context,AFHolidayMotion *m) {
    AFHolidayNpc *a=context;
    /* clapping is supplied by the animation service, whose donor/native indices
     * are not interchangeable. Preserve that part of the observation. */
    a->ops.motion(context,m);
    m->x=REAL(a,0x28);m->z=REAL(a,0x30);
    m->destination_x=REAL(a,0x8BC);m->destination_z=REAL(a,0x8C0);
    m->action=BYTE(a,0x7C5);m->step=BYTE(a,0x7C6);
}
static int request(void *context,u32 priority,u32 action,u32 type,short x,short z) {
    u16 args[6]={0,0,(u16)x,(u16)z,0,0};
    return FN(clip(0xF8),int,void *,u8,u8,u8,u16 *)(context,priority,action,type,args);
}
static void force_action(void *context,u32 action) {BYTE(context,0x7C5)=action;}
static void weight(void *context,u32 value) {BYTE(context,0xD6)=value;}
static void hide(void *context,int value) {BYTE(context,0x7FD)=value;}
static void interrupts(void *context) {WORD(context,0x7A8)=0;}
static void flags(void *context,u32 value,int replace) {
    WORD(context,0x80C)=replace?value:WORD(context,0x80C)|value;
}
static void destination(void *context,float x,float z) {
    FN(clip(0x10C),void,void *,float,float)(context,x,z);
}
static void talk_request(void *context,int enabled) {
    TALK_REQUEST(context)=enabled?af_holiday_npc_request:none;
}
static void request_demo(void *context) {
    FN(0x8007CDD8u,int,int,void *,void (*)(AFHolidayNpc *))(7,context,af_holiday_npc_prepare);
}
/* Keep the provider's animation identity observer outside the native primitive
 * slots. A per-call copy prevents overwriting it or recursively calling motion. */
static AFHolidayActorOps operations(AFHolidayNpc *a) {
    AFHolidayActorOps o=a->ops;o.context=a;
    o.motion=motion;o.request=request;o.force_action=force_action;o.weight=weight;
    o.hide_request=hide;o.clear_interrupts=interrupts;o.demo_flags=flags;
    o.destination=destination;o.remove=remove_actor;o.talk_request=talk_request;
    o.request_demo=request_demo;
    return o;
}
void af_holiday_npc_ctor(AFHolidayNpc *a,void *game) {
    typedef struct {
        void (*move)(AFHolidayNpc *,void *),(*draw)(AFHolidayNpc *,void *);
        int schedule;
        void (*request)(AFHolidayNpc *,void *);
        int (*start)(AFHolidayNpc *,void *),(*end)(AFHolidayNpc *,void *);
        int extra;
    } Ctor;
    static const Ctor data={af_holiday_npc_move,af_holiday_npc_draw,4,none,
        af_holiday_npc_start,af_holiday_npc_end,0};
    a->game=game;a->constructed=a->failed=0;a->actor=(AFHolidayActor){0};
    a->ops=(AFHolidayActorOps){0};a->world=(AFHolidayWorld){0};
    unsigned int gender;
    if(!af_holiday_world_resources(a) || !af_holiday_motion_bind(a) || !af_holiday_dialogue_bind(a) ||
            !af_holiday_npc_bind(a) || !a->ops.motion ||
            !af_holiday_npc_world(a,&a->world,&gender)) {fail(a);return;}
    if(FN(clip(0xBC),int,void *,void *)(a,game)!=1)return;
    if(af_holiday_actor_construct(&a->actor,&a->world,gender)<0) {fail(a);return;}
    a->ops.context=a;CALLBACK(a,0x7C0)=af_holiday_npc_schedule;
    /* Native ctor can invoke the registered schedule during construction. */
    a->constructed=1;
    FN(clip(0xC0),void,void *,void *,const Ctor *)(a,game,&data);
    if(a->failed || !af_holiday_npc_resources(a) || !af_holiday_motion_resources(a)) {fail(a);return;}
    WORD(a,0x8AC)=0xFFFFFFFFu;REAL(a,0x134)=1350.0f;
    void *player=FN(0x800B1C84u,void *,void *)(game);
    if(!player) {fail(a);return;}
    destination(a,REAL(player,0x28),REAL(player,0x30));
}
void af_holiday_npc_dtor(AFHolidayNpc *a,void *game) {
    if(a->constructed) {FN(clip(0xC4),void,void *,void *)(a,game);a->constructed=0;}
    af_holiday_npc_unregister(a);
}
void af_holiday_npc_init(AFHolidayNpc *a,void *game) {
    if(refresh(a,game))FN(clip(0xCC),void,void *,void *)(a,game);
}
void af_holiday_npc_move(AFHolidayNpc *a,void *game) {
    if(refresh(a,game))FN(clip(0xD0),void,void *,void *)(a,game);
}
void af_holiday_npc_draw(AFHolidayNpc *a,void *game) {
    if(a->constructed && !a->failed)FN(clip(0xE4),void,void *,void *)(a,game);
}
void af_holiday_npc_save(AFHolidayNpc *a,void *game) {
    (void)game;if(a->constructed)FN(0x800AB6C8u,void,void *)(a);
}
void af_holiday_npc_schedule(AFHolidayNpc *a,void *game,int type) {
    if(!refresh(a,game))return;
    if(type==0) {
        CALLBACK(a,0x7A4)=af_holiday_npc_think;
        FN(clip(0x110),int,void *,void *,int,int)(a,game,8,0);
    } else if(type==1 && !FN(clip(0x110),int,void *,void *,int,int)(a,game,-1,1))
        FN(clip(0x110),int,void *,void *,int,int)(a,game,-1,2);
}
void af_holiday_npc_think(AFHolidayNpc *a,void *game,int type) {
    if(!refresh(a,game))return;
    AFHolidayActorOps o=operations(a);
    int result=type==0?af_holiday_actor_think_init(&a->actor,&o):
        type==1?af_holiday_actor_think_elapsed(&a->actor,&a->world,&o,
            *(const volatile u8 *)0x80145048u):1;
    if(result<0)fail(a);
}
void af_holiday_npc_request(AFHolidayNpc *a,void *game) {
    if(!refresh(a,game))return;
    AFHolidayActorOps o=operations(a);
    if(af_holiday_actor_request(&a->actor,&o)<0)fail(a);
}
void af_holiday_npc_prepare(AFHolidayNpc *a) {
    if(!refresh(a,a->game))return;
    AFHolidayActorOps o=operations(a);
    if(af_holiday_actor_prepare(&a->actor,&a->world,&o)<0 || a->failed)fail(a);
}
int af_holiday_npc_start(AFHolidayNpc *a,void *game) {
    if(!refresh(a,game))return 0;
    AFHolidayActorOps o=operations(a);
    int r=af_holiday_actor_start(&a->actor,&a->world,&o);
    return r<0 || a->failed?fail(a):r;
}
int af_holiday_npc_end(AFHolidayNpc *a,void *game) {
    if(!refresh(a,game))return 0;
    AFHolidayActorOps o=operations(a);
    int continuation=af_holiday_npc_continue(a);
    int delivered=FN(0x8007B49Cu,u16,int,int)(4,1)==2;
    int can_talk=!FN(0x8007CF00u,int,int,void *)(8,a) && !FN(0x8007CF00u,int,int,void *)(7,a);
    int r=af_holiday_actor_talk(&a->actor,&a->world,&o,continuation,delivered,can_talk);
    /* A full/stale handover is recoverable; do not destroy a speaking actor or
     * pretend delivery succeeded. Keep the offer for the transport to recover. */
    if(r==AF_DIARY_CHANGED)return 0;
    return r<0 || a->failed?fail(a):r;
}
