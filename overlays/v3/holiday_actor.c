/* Shared holiday actor movement and conversation lifecycle. Native callbacks
 * translate semantics; no donor actor layout is cast onto the N64 actor. */
#include "holiday_actor.h"
typedef unsigned int u32;

/* main, initializer, talk enabled, return state; the conversation phase is owned
 * by holiday_talk.c after an actual demo accepts the talk request. */
static const unsigned char states[AF_HACT_THINKS][4]={
    {1,1,0,0},{0,1,0,1},{3,1,0,2},{0,3,1,3},{0,3,1,4},
    {2,2,1,5},{4,4,1,6},{5,5,1,6},{4,4,1,8},{6,2,1,8},
    {4,4,1,10},{5,5,1,10},{4,4,1,12},{6,2,1,12},{7,6,1,14}
};
static int valid(const AFHolidayActorOps *o) {
    return o && o->event && o->field_event && o->variant && o->shrine && o->runner &&
        o->motion && o->request && o->force_action && o->weight && o->hide_request &&
        o->clear_interrupts && o->demo_flags && o->walk_wander && o->destination &&
        o->repeat_animation && o->clap_sound && o->remove && o->random &&
        o->talk_request && o->request_demo && o->transport && o->restore_melody;
}
static int actor_valid(const AFHolidayActor *a) {
    return a && a->ready && !a->deleted && a->think<AF_HACT_THINKS;
}
static void request(const AFHolidayActorOps *o,u32 action,int point,short x,short z) {
    o->request(o->context,4,action,point?AF_HACT_POINT:0,x,z);
}
static void goal(AFHolidayActor *a) {
    int x=-160,z=40;
    switch(a->think) {
    case 6:x=160;z=-120;break;
    case 8:x=200;break;
    case 10:x=-120;z=-120;break;
    }
    a->goal_x=(short)(a->center_x+x);a->goal_z=(short)(a->center_z+z);
}
int af_holiday_actor_construct(AFHolidayActor *a,const AFHolidayWorld *w,u32 gender) {
    if(!a || !w || !w->diary || gender>1 || w->player>4 ||
            !af_diary_valid(w->diary) || !w->today.year ||
            !w->today.day || w->today.day>af_diary_days(w->today.year,w->today.month))return -1;
    /* Source player -1 resolves to the active resident, not all residents.
     * Visitors leave every resident's calendar untouched. */
    if(w->player<AF_DIARY_PLAYERS &&
            af_diary_calendar_refresh(w->diary,w->player,w->today,w->dates)<0)return -1;
    *a=(AFHolidayActor){.date=w->today,.event=AF_HACT_NO_EVENT,.gender=gender,.ready=1};
    return 1;
}
int af_holiday_actor_set_think(AFHolidayActor *a,const AFHolidayActorOps *o,u32 index) {
    if(!actor_valid(a) || !valid(o) || index>=AF_HACT_THINKS)return -1;
    void *c=o->context;const unsigned char *row=states[index];
    a->think=index;a->return_think=row[3];a->talk_enabled=row[2];
    o->talk_request(c,a->talk_enabled);
    switch(row[1]) {
    case 1:request(o,AF_HACT_WAIT,0,0,0);break;
    case 2:o->force_action(c,AF_HACT_RUN);request(o,AF_HACT_WAIT,0,0,0);break;
    case 3:o->walk_wander(c);o->weight(c,0x50);break;
    case 4:goal(a);request(o,AF_HACT_TURN,1,a->goal_x,a->goal_z);break;
    case 5:a->timer=300;request(o,AF_HACT_WALK,1,a->goal_x,a->goal_z);break;
    case 6: {
        AFHolidayMotion m;o->force_action(c,AF_HACT_WAIT);request(o,AF_HACT_WAIT,0,0,0);
        a->timer=300;o->motion(c,&m);o->destination(c,m.x-20.0f,m.z+50.0f);
        u32 roll=o->random(c,2);if(roll>=2)return -1;
        o->repeat_animation(c,roll==0);break;
    }
    }
    a->suppress_request=1;return 1;
}
int af_holiday_actor_think_init(AFHolidayActor *a,const AFHolidayActorOps *o) {
    if(!actor_valid(a) || !valid(o))return -1;
    o->weight(o->context,0xFE);o->hide_request(o->context,0);
    return af_holiday_actor_set_think(a,o,0);
}
int af_holiday_actor_think(AFHolidayActor *a,const AFHolidayWorld *w,const AFHolidayActorOps *o) {
    if(!actor_valid(a) || !w || !valid(o))return -1;
    void *c=o->context;AFHolidayMotion m;short p[3];
    o->demo_flags(c,0x800,0);
    switch(states[a->think][0]) {
    case 0:break;
    case 1: {
        u32 event=o->event(c),next=4,variant=0;
        if(event==AF_HACT_NO_EVENT)break;
        if(event>=28 && event!=101 && event!=102)return -1;
        if(event==8 || event==20) {
            static const unsigned char field[4]={5,2,14,1};
            u32 f=o->field_event(c);if(f>=4)return -1;next=field[f];
        }
        if(!o->variant(c,event,a->gender,&variant))return -1;
        o->clear_interrupts(c);o->demo_flags(c,0x20,1);
        if(event==101 || event==102) {
            if(!w->lighthouse_after)return -1;
            if(w->player==4 || w->lighthouse_after(w->context)) {
                a->deleted=1;o->remove(c);
            } else next=3;
        }
        if(!a->deleted && af_holiday_actor_set_think(a,o,next)<0)return -1;
        if(event==26 && a->date.day!=31) {
            --a->date.year;a->date.month=12;a->date.day=31;
        }
        a->event=event;a->variant=variant;break;
    }
    case 2:
        if(o->runner(c,p))request(o,AF_HACT_TURN2,1,p[0],p[1]);
        break;
    case 3:
        if(o->shrine(c,p)) {
            /* The donor uses position[1], not position[2], for Z. */
            a->center_x=p[0];a->center_z=p[1];
            return af_holiday_actor_set_think(a,o,6);
        }
        break;
    case 4:
        o->motion(c,&m);
        if(m.action==AF_HACT_TURN && m.step==255)
            return af_holiday_actor_set_think(a,o,a->think+1);
        break;
    case 5:
        o->motion(c,&m);
        if(m.action==AF_HACT_WALK && m.step==255)
            return af_holiday_actor_set_think(a,o,a->think+1);
        if((short)m.destination_x!=a->goal_x || (short)m.destination_z!=a->goal_z)
            return af_holiday_actor_set_think(a,o,a->think-1);
        break;
    case 6:
        if(a->timer>0)--a->timer;
        else return af_holiday_actor_set_think(a,o,a->think>=13?6:a->think+1);
        break;
    case 7:
        if(a->timer>0)--a->timer;
        else if(af_holiday_actor_set_think(a,o,a->think)<0)return -1;
        o->motion(c,&m);if(m.clapping)o->clap_sound(c);break;
    }
    return 1;
}
int af_holiday_actor_request(AFHolidayActor *a,const AFHolidayActorOps *o) {
    if(!actor_valid(a) || !valid(o))return -1;
    if(!a->talk_enabled || a->talk.active)return 0;
    if(a->suppress_request) {a->suppress_request=0;return 0;}
    o->request_demo(o->context);return 1;
}
int af_holiday_actor_prepare(AFHolidayActor *a,const AFHolidayWorld *w,const AFHolidayActorOps *o) {
    if(!actor_valid(a) || !valid(o) || !w || !a->talk_enabled || a->talk.active)return -1;
    /* Do not advance the shared RNG for dialogue with no random branch. */
    int random_repeat=0;
    if(a->event==101 || a->event==102)
        random_repeat=w->lighthouse_after && w->lighthouse_after(w->context)==1;
    else if(a->event<28 && w->player<4 && w->items.claimed &&
            w->items.claimed(w->items.context,a->event)==1)
        random_repeat=af_diary_calendar_event_check(w->diary,w->player,
            w->today,a->date,a->event)==1;
    AFHolidayAction out;u32 repeat=random_repeat?o->random(o->context,3):0;
    if(repeat>=3)return -1;
    int r=af_holiday_talk_prepare(&a->talk,w,a->event,a->date,a->gender,a->variant,repeat,&out);
    if(r>0)o->transport(o->context,&out);
    return r;
}
int af_holiday_actor_start(AFHolidayActor *a,const AFHolidayWorld *w,const AFHolidayActorOps *o) {
    if(!actor_valid(a) || !valid(o))return -1;
    AFHolidayAction out;int r=af_holiday_talk_start(&a->talk,w,&out);
    if(r>0) {a->talk_enabled=0;o->talk_request(o->context,0);o->transport(o->context,&out);}
    return r;
}
int af_holiday_actor_talk(AFHolidayActor *a,const AFHolidayWorld *w,const AFHolidayActorOps *o,
        int continuation,int delivered,int can_talk) {
    if(!actor_valid(a) || !valid(o))return -1;
    AFHolidayAction out;int r=af_holiday_talk_step(&a->talk,w,continuation,delivered,can_talk,&out);
    if(r<0)return r;
    o->transport(o->context,&out);
    if(out.effects&AF_HOLIDAY_END) {
        if(af_holiday_actor_set_think(a,o,a->return_think)<0)return -1;
        o->restore_melody(o->context);return 1;
    }
    return 0;
}
