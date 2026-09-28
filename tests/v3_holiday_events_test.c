/* One connected calendar/owner/conversation check. Placement and native event
 * services are host doubles; no emulator or hardware execution is implied. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "holiday_events.h"
#include "holiday_talk.h"
#include "holiday-events-data.h"
typedef unsigned char u8;
typedef struct {int ignored;} ACTOR;
typedef struct {int actor_info;} GAME_PLAY;
enum {FALSE=0,TRUE=1,mAc_PROFILE_EV_MIKO=1,ACTOR_PART_NPC=1};
static unsigned int reference_status[128];
static int notification;
static ACTOR miko;
static int mEv_check_status(unsigned int e,unsigned int mask) {return (reference_status[e]&mask)!=0;}
static ACTOR *Actor_info_name_search(int *info,int profile,int part) {
    (void)info;assert(profile==mAc_PROFILE_EV_MIKO && part==ACTOR_PART_NPC);return &miko;
}
static void Actor_delete(ACTOR *a) {assert(a==&miko);notification=-2;}
static void mEv_actor_dying_message(unsigned int e,ACTOR *a) {(void)a;notification=(int)e;}
#include "holiday-events-reference.inc"
static AFHolidayDay days[AF_HE_CAPACITY];
static AFHolidayClock clock_value={.date={2026,1,1},.special={17,9,25},
    .hour=10,.vernal_day=20,.autumnal_day=23,.vacation_available=1};
static unsigned int count,kept[128],placed,shown,culled,dispatched,wandering;
static int placement_ok=1,show_result=1,cull_result=1,dispatch_result=1;
static int dispatch(void *c,unsigned int t,unsigned int phase) {
    (void)c;assert(t<128 && phase<5);++dispatched;return dispatch_result;
}
static int keep(void *c,unsigned int t) {(void)c;return kept[t];}
static void set_keep(void *c,unsigned int t,int value) {(void)c;kept[t]=value;}
static int place(void *c,unsigned int t,unsigned int kind,unsigned int id,int adjust) {
    (void)c;assert(t<128 && id==0x51 && kind>=1 && kind<=3);
    assert(adjust==(kind==AF_HE_WANDER?1:2));++placed;return placement_ok;
}
static int show(void *c,unsigned int t,unsigned int id) {(void)c;assert(t<128 && id==0x51);++shown;return show_result;}
static int cull(void *c,unsigned int t) {(void)c;assert(t<128);++culled;return cull_result;}
static void wander(void *c,int present) {(void)c;wandering=present;}
static const AFHolidayOwnerOps ops={0,dispatch,keep,set_keep,place,show,cull,wander};
static AFHolidayDay *find(unsigned int type) {
    for(unsigned int i=0;i<count;i++)if(days[i].type==type)return days+i;
    return NULL;
}
static void plan(unsigned int month,unsigned int day,unsigned int hour) {
    clock_value.date.month=month;clock_value.date.day=day;clock_value.hour=hour;
    int n=af_holiday_event_plan(event_data,sizeof(event_data),&clock_value,days,AF_HE_CAPACITY);
    assert(n>=0);count=(unsigned int)n;
    /* Mere planning must not tell the actor an event is running. */
    assert(af_holiday_event_current(event_data,sizeof(event_data),days,count)==255);
    for(unsigned int i=0;i<count;i++)assert(!(days[i].status&(AF_HE_RUN|AF_HE_SHOW)));
}
static AFHolidayOwner owner(unsigned int type) {
    AFHolidayOwner o;assert(af_holiday_event_owner(event_data,sizeof(event_data),type,&o)==1);return o;
}
static void start(void) {
    for(unsigned int i=0;i<count;i++) {
        AFHolidayOwner o=owner(days[i].type);
        assert(af_holiday_event_clock(days+i,&o,&ops)==1);
    }
}
static void compare_reference(void) {
    memset(reference_status,0,sizeof(reference_status));
    for(unsigned int i=0;i<count;i++)reference_status[days[i].type]=days[i].status;
    assert(af_holiday_event_current(event_data,sizeof(event_data),days,count)==mSC_get_soncho_event());
    assert(af_holiday_event_field(days,count)==mSC_get_soncho_field_event());
    notification=-1;ACTOR a={0};GAME_PLAY play={0};mSC_delete_soncho(&a,&play);
    assert(af_holiday_event_cleanup(event_data,sizeof(event_data),days,count)==notification);
}
static AFDiary diary;
static unsigned int claimed,given,last_item;
static unsigned int resolve(void *c,unsigned int item) {
    (void)c;
    /* The connected event check only selects Nature Day's installed tree model.
     * All other identity/selection cases retain the earlier world check. */
    return item==nature_source_item?nature_native_item:0;
}
static int has(void *c,unsigned int event) {(void)c;assert(event==9);return claimed;}
static int give(void *c,unsigned int item) {(void)c;++given;last_item=item;return 1;}
static void mark(void *c,unsigned int event) {(void)c;assert(event==9 && given==1);claimed=1;}
static int free_slots(void *c) {(void)c;return 15;}
int main(void) {
    plan(3,19,10);assert(!find(82) && !find(13));
    plan(3,20,10);assert(find(82) && find(13) && !(find(15)->status&AF_HE_ACTIVE));
    start();assert(af_holiday_event_current(event_data,sizeof(event_data),days,count)==8);
    compare_reference();
    plan(9,23,11);start();assert(af_holiday_event_field(days,count)==0);compare_reference();
    find(15)->status|=AF_HE_SHOW;compare_reference();
    find(12)->status|=AF_HE_SHOW;compare_reference();
    plan(6,21,11);assert(find(89) && !find(90)); /* Father's Day beats fishing. */
    plan(6,28,11);assert(find(90) && !find(89));start();compare_reference();
    plan(11,11,11);assert(find(101));start();compare_reference();
    plan(11,3,11);assert(find(100)); /* Day after first Monday. */
    plan(11,27,11);assert(find(104)); /* Day after fourth Thursday. */
    plan(11,26,16);assert(find(103) && find(56));start();compare_reference();
    plan(7,17,11);assert(find(91));
    plan(7,16,11);assert(!find(91));
    plan(9,25,19);assert(find(43) && find(97));start();compare_reference();
    plan(10,31,18);assert(find(99)->hours==0xFC0000);start();compare_reference();
    assert(owner(99).kind==AF_HE_HALLOWEEN); /* Not ordinary Tortimer's costume. */
    plan(11,1,0);assert(find(99)->hours==1);start();compare_reference();
    plan(12,31,23);assert(find(64)->hours==0x800000);start();compare_reference();
    plan(1,1,0);assert(find(64)->hours==1);start();compare_reference();
    plan(1,1,6);start();assert(af_holiday_event_current(event_data,sizeof(event_data),days,count)==0);compare_reference();
    plan(7,25,6);assert(find(35)->hours==(1u<<6));assert(find(35)->begin==0x719 && find(35)->end==0x719);
    start();compare_reference();
    plan(8,31,6);assert(find(35));plan(9,1,6);assert(!find(35));
    plan(1,15,11);assert(find(4));start();compare_reference();
    clock_value.vacation_available=0;plan(1,15,11);assert(!find(4));clock_value.vacation_available=1;
    /* Every reward branch uses the source's live RUN precedence and cleanup,
     * including deferred autumn fishing, not a hand-maintained second list. */
    for(unsigned int event=0;event<28;event++) {
        count=2;days[0]=(AFHolidayDay){.type=event_data[16+event],.status=AF_HE_RUN};
        days[1]=(AFHolidayDay){.type=102,.status=AF_HE_RUN};compare_reference();
    }
    /* Complete shared owner placement/show/leave/stop lifecycle and failures. */
    plan(6,28,11);AFHolidayDay *d=find(90);AFHolidayOwner o=owner(90);
    assert(o.kind==AF_HE_WANDER);kept[90]=0;placed=shown=culled=0;
    placement_ok=-1;assert(af_holiday_event_clock(d,&o,&ops)==1);
    assert((d->status&AF_HE_ERROR) && !(d->status&AF_HE_RUN) && placed==1 && kept[90]);
    placement_ok=1;d->status&=~AF_HE_ERROR;assert(af_holiday_event_clock(d,&o,&ops)==1);
    assert((d->status&AF_HE_RUN) && placed==2 && wandering);
    assert(af_holiday_event_clock(d,&o,&ops)==1 && placed==2);
    assert(af_holiday_event_wade(d,&o,&ops,1,1,0)==0 && shown==0);
    assert(af_holiday_event_wade(d,&o,&ops,0,0,0)==0 && shown==0);
    show_result=2;assert(af_holiday_event_wade(d,&o,&ops,0,1,0)==1 && !(d->status&AF_HE_SHOW));
    show_result=0;assert(af_holiday_event_wade(d,&o,&ops,0,1,0)==0);
    show_result=1;assert(af_holiday_event_wade(d,&o,&ops,0,1,0)==1 && (d->status&AF_HE_SHOW));
    d->status|=AF_HE_STOP;cull_result=0;assert(af_holiday_event_wade(d,&o,&ops,0,1,0)==0 && (d->status&AF_HE_SHOW));
    cull_result=1;assert(af_holiday_event_wade(d,&o,&ops,0,1,0)==1 && !(d->status&(AF_HE_SHOW|AF_HE_STOP)));
    d->status&=~AF_HE_ACTIVE;assert(af_holiday_event_clock(d,&o,&ops)==1 && !(d->status&AF_HE_RUN) && !kept[90] && !wandering);
    /* The source's outside-field early return is not a failed reservation. */
    placement_ok=0;d->status=AF_HE_ACTIVE|AF_HE_EXIST;
    assert(af_holiday_event_clock(d,&o,&ops)==1 && (d->status&AF_HE_RUN) && !(d->status&AF_HE_ERROR));
    placement_ok=1;
    /* Malformed/capacity/job gates cannot damage the caller's existing directory. */
    AFHolidayDay before[AF_HE_CAPACITY];memcpy(before,days,sizeof(days));
    clock_value.date=(AFDiaryDate){2026,3,20};clock_value.hour=10;
    assert(af_holiday_event_plan(event_data,sizeof(event_data),&clock_value,days,1)==-2);
    assert(!memcmp(before,days,sizeof(days)));
    clock_value.special.town_day=0;assert(af_holiday_event_plan(event_data,sizeof(event_data),&clock_value,days,48)==-1);
    assert(!memcmp(before,days,sizeof(days)));clock_value.special.town_day=17;
    clock_value.working=1;assert(af_holiday_event_plan(event_data,sizeof(event_data),&clock_value,days,48)==0);
    assert(!memcmp(before,days,sizeof(days)));clock_value.working=0;
    /* Actual scheduled owner -> accepted conversation -> calendar attendance ->
     * real shared reward transaction. Scheduling and spawn alone do not count. */
    plan(4,22,11);start();compare_reference();af_diary_reset(&diary);
    unsigned int event=af_holiday_event_current(event_data,sizeof(event_data),days,count);assert(event==9);
    AFHolidayWorld w={.diary=&diary,.dates=clock_value.special,.today=clock_value.date,
        .player=0,.rewards=reward_data,.reward_bytes=sizeof(reward_data),
        .items={0,resolve,has,give,mark},.free_slots=free_slots};
    assert(af_diary_calendar_event_check(&diary,0,w.today,w.today,event)==0);
    AFHolidayTalk talk={0};AFHolidayAction action;
    assert(af_holiday_talk_prepare(&talk,&w,event,w.today,0,0,0,&action)==AF_DIARY_OK);
    assert(af_diary_calendar_event_check(&diary,0,w.today,w.today,event)==0);
    assert(af_holiday_talk_start(&talk,&w,&action)==AF_DIARY_OK);
    assert(af_diary_calendar_event_check(&diary,0,w.today,w.today,event)==1);
    assert(af_holiday_talk_step(&talk,&w,1,0,0,&action)==AF_DIARY_OK && !given);
    assert(af_holiday_talk_step(&talk,&w,0,1,0,&action)==AF_DIARY_OK && given==1 && claimed && last_item==nature_native_item);
    assert(af_holiday_talk_step(&talk,&w,0,0,1,&action)==AF_DIARY_OK && (action.effects&AF_HOLIDAY_END));
    puts("PASS: calendar boundaries, all event priorities, donor cleanup, shared owner lifecycle, and connected attendance/handover");
    return 0;
}
