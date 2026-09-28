#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "holiday_active.h"
#include "holiday_native.h"
#include "holiday-active-identities.h"
AFHolidayDedicatedCommon af_holiday_dedicated_common;
AFHolidayNativeDay af_holiday_native_days[64];
unsigned char af_holiday_native_index[128];
const unsigned char af_holiday_active_hour=10;
short af_holiday_active_too_short;
int af_holiday_active_delete;
const int af_holiday_active_rumour_count=2;
const unsigned int af_holiday_active_rumours[]={3,4};
static unsigned int rumours;
static AFHolidayPlace place={.block={3,2}};
static int location[128];
int af_holiday_native_check_status(int t,int m) {
    assert(t>=0 && t<128);int i=af_holiday_native_index[t];
    if(i==255)return 0;
    unsigned int s=af_holiday_native_days[i].status;
    return (m==32 || !(s&32)) && (s&m);
}
int af_holiday_active_set(int t) {
    int i=af_holiday_native_index[t];assert(i<64);
    int changed=!(af_holiday_native_days[i].status&1);af_holiday_native_days[i].status|=1;return changed;
}
int af_holiday_active_clear(int t) {
    int i=af_holiday_native_index[t];assert(i<64);
    int changed=!!(af_holiday_native_days[i].status&1);af_holiday_native_days[i].status&=~1;return changed;
}
AFHolidayPlace *af_holiday_native_get_place(int t,unsigned char id) {
    assert(t>=0 && t<128 && id==81);return location[t]?&place:0;
}
void af_holiday_active_clear_rumours(void) {rumours=0;}
void af_holiday_active_spread_rumour(int i) {assert(i>=0 && i<2);rumours|=1u<<i;}
int af_holiday_dedicated_native(void *m,AFHolidayControl *ctrl,AFHolidayDedicatedCommon *c,
        const AFHolidayDedicatedServices *s,unsigned int phase) {
    assert(m && ctrl && s && c==&af_holiday_dedicated_common && phase==2);
    c->fieldday_event_id=15;return 7;
}

/* Reference uses the complete unchanged donor function with donor identities.
 * Only field access and engine I/O are doubled. */
typedef AFHolidayActiveEvent Event_c;
typedef AFHolidayPlace mEv_place_data_c;
typedef struct {int type;unsigned int active_hours;unsigned short status;} mEv_event_today_c;
static mEv_event_today_c event_today[64];
static unsigned char index_today[128];
static struct {
    struct {struct {int hour;} rtc_time;} time;
    struct {short fieldday_event_over_status,too_short;} event_common;
} ref_common;
static struct {struct {int delete_event_id;} event_save_common;} ref_saved;
#define Common_Get(path) (ref_common.path)
#define Save_Get(path) (ref_saved.path)
#define FALSE 0
#define mEv_TODAY_EVENT_NUM 64
static int mEv_check_status(int t,int m) {
    assert(t>=0 && t<128);int i=index_today[t];if(i==255)return 0;
    unsigned int s=event_today[i].status;return (m==32 || !(s&32)) && (s&m);
}
static int set_active(int t) {
    int i=index_today[t];assert(i<64);int changed=!(event_today[i].status&1);
    event_today[i].status|=1;return changed;
}
static int clear_active(int t) {
    int i=index_today[t];assert(i<64);int changed=!!(event_today[i].status&1);
    event_today[i].status&=~1;return changed;
}
static mEv_place_data_c *mEv_get_common_place(int t,int id) {
    assert(id==81);return location[af_holiday_native_ids[t]]?&place:0;
}
static void mEv_clear_rumor(void) {}
static void mEv_spread_rumor(int i) {(void)i;assert(0);}
static const int n_event_rumors=0,event_rumor_table[]={0};
#include "holiday-active-source.h"
static void reset(void) {
    memset(af_holiday_native_days,0,sizeof(af_holiday_native_days));
    for(int i=0;i<64;i++)af_holiday_native_days[i].type=~0u;
    memset(af_holiday_native_index,255,128);memset(location,0,sizeof(location));
    af_holiday_dedicated_common=(AFHolidayDedicatedCommon){-1,-1};
    af_holiday_active_too_short=0;af_holiday_active_delete=0;rumours=0;
}
static void add(int slot,int t,unsigned int hours,unsigned int status) {
    assert(slot<64 && t<128);af_holiday_native_index[t]=slot;
    af_holiday_native_days[slot]=(AFHolidayNativeDay){.type=t,.hours=hours,.status=status};
}
int main(void) {
    _Static_assert(mEv_EVENT_SPORTS_FAIR==16 && mEv_EVENT_SPORTS_FAIR_BALL_TOSS==12 &&
        mEv_EVENT_SPORTS_FAIR_TUG_OF_WAR==14 && mEv_EVENT_SPORTS_FAIR_FOOT_RACE==15,"Source sports IDs");
    const unsigned int hours[]={1u<<10,1u<<9,0x10000400,0x20000000,0x20000400};
    const unsigned int statuses[]={0,1,17,33};
    const int over[]={-1,16,12},shorts[]={0,12};
    for(unsigned int o=0;o<3;o++)for(unsigned int h=0;h<5;h++)
    for(unsigned int s=0;s<4;s++)for(unsigned int sh=0;sh<2;sh++)for(int here=0;here<3;here++) {
        reset();memset(index_today,255,128);memset(event_today,0,sizeof(event_today));
        for(int i=0;i<64;i++)event_today[i].type=-1;
        ref_common.time.rtc_time.hour=10;ref_common.event_common.fieldday_event_over_status=over[o];
        ref_common.event_common.too_short=shorts[sh];ref_saved.event_save_common.delete_event_id=0;
        af_holiday_dedicated_common.fieldday_event_over_status=over[o];
        af_holiday_active_too_short=shorts[sh]?af_holiday_native_ids[shorts[sh]]:0;
        for(int donor=11;donor<=16;donor++) {
            int i=donor-11,t=af_holiday_native_ids[donor];
            add(i,t,hours[h],statuses[s]);location[t]=here!=0;
            index_today[donor]=i;event_today[i]=(mEv_event_today_c){donor,hours[h],statuses[s]};
        }
        Event_c expected={.block_x=here==2?9:2,.block_z=3},actual=expected;
        update_active(&expected);af_holiday_active_update(&actual);
        assert(actual.changed_num==expected.changed_num);
        assert(af_holiday_active_too_short==(ref_common.event_common.too_short?
            af_holiday_native_ids[ref_common.event_common.too_short]:0));
        for(int i=0;i<6;i++)assert(af_holiday_native_days[i].hours==event_today[i].active_hours &&
            af_holiday_native_days[i].status==event_today[i].status);
    }
    reset();add(0,3,1u<<10,0);add(1,4,1u<<9,1);add(63,70,0x10000000,0);
    Event_c event={.block_x=2,.block_z=3};af_holiday_active_update(&event);
    assert(event.changed_num==3 && rumours==1 && af_holiday_native_days[63].status==1);
    af_holiday_active_delete=3;af_holiday_native_days[0].status|=16;af_holiday_active_update(&event);
    assert(af_holiday_active_delete==0 && af_holiday_native_days[0].hours==0x20000000 && rumours==0);
    af_holiday_native_days[0].status&=~16;af_holiday_active_update(&event);
    assert(af_holiday_native_days[0].hours==0);
    reset();add(0,0,1u<<10,0);af_holiday_active_delete=7;
    af_holiday_active_update(&event);assert(af_holiday_native_days[0].hours&0x40000000);
    reset();add(0,af_holiday_native_ids[12],1u<<10,0);
    af_holiday_active_delete=af_holiday_native_ids[12];af_holiday_active_update(&event);
    assert(af_holiday_native_days[0].status==1 && af_holiday_active_delete==af_holiday_native_ids[12]);
    AFHolidayControl control={0};AFHolidayDedicatedServices services={0};
    assert(af_holiday_dedicated_current(&event,&control,&services,2)==7);
    assert(af_holiday_dedicated_common.fieldday_event_id==15);
    puts("Connected hourly path: complete donor sports comparison, native/camper cleanup, shared owner state");
    return 0;
}
