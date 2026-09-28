#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "holiday_native.h"
#include "holiday-native-data.h"

AFHolidayNativeDay af_holiday_native_days[AF_HN_DAYS];
unsigned char af_holiday_native_index[128];
unsigned int af_holiday_native_count;
static int notified=-1;
static void *notified_actor;
void af_holiday_native_death(int type,void *actor) {notified=type;notified_actor=actor;}

static void reset(unsigned int natives) {
    memset(af_holiday_native_days,0,sizeof(af_holiday_native_days));
    memset(af_holiday_native_index,255,sizeof(af_holiday_native_index));
    af_holiday_native_count=natives;
    for(unsigned int i=0;i<AF_HN_DAYS;i++)af_holiday_native_days[i].type=~0u;
    for(unsigned int i=0;i<natives;i++) {
        unsigned int type=i+1==natives?70:i;
        af_holiday_native_days[i]=(AFHolidayNativeDay){type,0x40000001,0x101,0x202,AF_HE_RUN|AF_HE_SHOW,0x1234};
        af_holiday_native_index[type]=i;
    }
}
int main(void) {
    AFHolidayDay plan[48],snapshot[48];unsigned int n=0;
    for(unsigned int source=0;source<128;source++) {
        int type=af_holiday_native_type(source);
        if(type<0)continue;
        assert(type==(int)(71+n));
        plan[n++]=(AFHolidayDay){0xFFF,0x101,0x1231,source,AF_HE_EXIST|AF_HE_ACTIVE};
    }
    assert(n==44 && af_holiday_native_type(128)==-1);
    reset(20);AFHolidayNativeDay retained[20];
    memcpy(retained,af_holiday_native_days,sizeof(retained));
    assert(af_holiday_native_merge(plan,n)==44 && af_holiday_native_count==64);
    assert(!memcmp(retained,af_holiday_native_days,sizeof(retained)));
    assert(af_holiday_native_snapshot(snapshot,44)==44);
    for(unsigned int i=0;i<44;i++) {
        assert(snapshot[i].type==plan[i].type && snapshot[i].status==AF_HE_EXIST);
        assert(af_holiday_native_days[20+i].reserved==0);
    }
    assert(af_holiday_native_current()==255 && af_holiday_native_field()==3);
    assert(af_holiday_native_cleanup()==-1); /* Scheduled is not running. */
    unsigned int source=af_holiday_event_data[16+9];
    unsigned int type=(unsigned int)af_holiday_native_type(source);
    AFHolidayNativeDay *d=&af_holiday_native_days[af_holiday_native_index[type]];
    d->status|=AF_HE_RUN|AF_HE_SHOW;
    assert(af_holiday_native_current()==9 && af_holiday_native_cleanup()==(int)source);
    assert(af_holiday_native_merge(plan,n)==44 && d->status==(AF_HE_EXIST|AF_HE_RUN|AF_HE_SHOW));
    assert(!(d->status&AF_HE_ACTIVE));
    d->status|=AF_HE_ERROR;
    assert(af_holiday_native_current()==255 && af_holiday_native_cleanup()==-1);
    assert(af_holiday_native_notify(source,d)==1 && notified==(int)type && notified_actor==d);
    assert(af_holiday_native_notify(127,d)==0 && af_holiday_native_notify(source,0)==0);

    /* Full admission fails before changing native events or the shared index. */
    reset(21);AFHolidayNativeDay before[64];unsigned char index[128];
    memcpy(before,af_holiday_native_days,sizeof(before));memcpy(index,af_holiday_native_index,128);
    assert(af_holiday_native_merge(plan,n)==-2);
    assert(af_holiday_native_count==21 && !memcmp(before,af_holiday_native_days,sizeof(before)));
    assert(!memcmp(index,af_holiday_native_index,128));
    reset(1);plan[43].type=plan[0].type;
    assert(af_holiday_native_merge(plan,n)==-1 && af_holiday_native_count==1);
    plan[43].type=107;plan[43].status|=AF_HE_RUN;
    assert(af_holiday_native_merge(plan,n)==-1 && af_holiday_native_count==1);
    plan[43].status=AF_HE_EXIST;af_holiday_native_index[70]=65;
    assert(af_holiday_native_merge(plan,n)==-1);
    memset(snapshot,0xA5,sizeof(snapshot));AFHolidayDay old[48];memcpy(old,snapshot,sizeof(old));
    assert(af_holiday_native_snapshot(snapshot,48)==-1 && !memcmp(old,snapshot,sizeof(old)));

    reset(1);
    AFHolidayClock clock={{2026,4,22},{10,9,25},12,0,20,23,0};
    assert(af_holiday_native_schedule(&clock)>0);
    assert(af_holiday_native_current()==255);
    assert(af_holiday_native_snapshot(snapshot,48)>0);
    assert(af_holiday_native_snapshot(snapshot,0)==-2);
    assert(af_holiday_native_days[0].type==70 && af_holiday_native_days[0].reserved==0x1234);
    clock.special.town_day=0;
    memcpy(before,af_holiday_native_days,sizeof(before));
    assert(af_holiday_native_schedule(&clock)==-1 && !memcmp(before,af_holiday_native_days,sizeof(before)));
    puts("All 44 mapped events: native retention, 64-slot admission, transactional rejection, live flags, cleanup, and schedule bridge pass.");
    return 0;
}
