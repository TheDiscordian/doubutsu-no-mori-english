/* Donor hunt scheduling and real native event/save ownership. The temporary
 * GC record is 44 bytes; the native common slot holds only 40. Keep the full
 * record in owned memory, using a native slot as its lifetime marker. */
#include "carried_quest.h"
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
extern const u8 af_cw_native_rtc[8];
extern u8 *af_v3_card_data(void);
extern u32 af_carried_quantity(u32);
extern float fqrand(void);
extern int af_cw_prior_calendar_before_cleanup(void);
extern void *af_cw_native_get_save(int,int),*af_cw_native_reserve_save(int,int);
extern void *af_cw_native_get_common(int,int),*af_cw_native_reserve_common(int,int);
extern void af_carried_spirit_event_bind(void *,const volatile u16 *);
#ifdef __mips__
const u32 af_cw_available=0;
#endif
static int range(unsigned d,unsigned lo,unsigned hi) {return lo>hi?(d>=lo || d<=hi):(d>=lo && d<=hi);}
static unsigned after(AFDiaryDate d,int n) {
    int day=(int)d.day+n;
    if(day<1) {
        if(d.month==1) {d.month=12;--d.year;} else --d.month;
        day+=(int)af_diary_days(d.year,d.month);
    } else {
        unsigned days=af_diary_days(d.year,d.month);
        if(day>(int)days) {day-=(int)days;if(d.month==12)d.month=1;else ++d.month;}
    }
    return (unsigned)d.month*256u+(unsigned)day;
}
int af_cw_plan(u8 *cards,AFDiaryDate date,float (*random)(void)) {
    int saved=af_carried_quest_day(cards);
    if(saved<0 || !random || date.year<2000 || date.year>2099 ||
       !date.day || date.day>af_diary_days(date.year,date.month))return -1;
    unsigned today=(unsigned)date.month*256u+date.day,lo=after(date,-7),hi=after(date,4);
    if(!saved || !range((unsigned)saved,lo,hi)) {
        float r=random();if(!(r>=0 && r<1))return -1;
        saved=(int)after(date,2+(int)(r*3.0f));
        if(!af_carried_quest_set_day(cards,(unsigned)saved))return -1;
    }
    return range((unsigned)saved,lo,today);
}
static int enabled(void) {
    return *(const volatile u32 *)&af_cw_available==1 && af_carried_quantity(0x2D28)==1;
}
static AFHolidayNativeDay *day(void) {
    unsigned slot=af_holiday_native_index[AF_CW_NATIVE];
    return slot<AF_HN_DAYS && af_holiday_native_days[slot].type==AF_CW_NATIVE?
        af_holiday_native_days+slot:0;
}
int af_cw_calendar_before_cleanup(void) {
    int previous=af_cw_prior_calendar_before_cleanup();
    if(enabled()) {
        AFDiaryDate today={(unsigned)af_cw_native_rtc[6]*256u+af_cw_native_rtc[7],
            af_cw_native_rtc[5],af_cw_native_rtc[3]};
        if(af_cw_plan(af_v3_card_data(),today,fqrand)==1)
            (void)af_holiday_native_append(AF_CW_NATIVE,15,0x0101,0x0C1F);
    }
    /* Rebind after directory reset; stale slots must not keep spirits alive. */
    (void)af_cw_get_common(AF_CW_SOURCE,AF_CW_COMMON);
    return previous;
}
static int valid(int source,int id,int expected) {
    return source==AF_CW_SOURCE && id==expected && enabled() && day()!=0;
}
void *af_cw_get_save(int source,int id) {
    return valid(source,id,AF_CW_SAVED)?af_cw_native_get_save(AF_CW_NATIVE,id):0;
}
void *af_cw_reserve_save(int source,int id) {
    return valid(source,id,AF_CW_SAVED)?af_cw_native_reserve_save(AF_CW_NATIVE,id):0;
}
void *af_cw_get_common(int source,int id) {
    AFHolidayNativeDay *d=day();
    if(!valid(source,id,AF_CW_COMMON) || !af_cw_state.present ||
       !af_cw_native_get_common(AF_CW_NATIVE,id)) {
        af_carried_spirit_event_bind(0,0);return 0;
    }
    af_carried_spirit_event_bind(&af_cw_state.common,&d->status);
    return &af_cw_state.common;
}
void *af_cw_reserve_common(int source,int id) {
    if(!valid(source,id,AF_CW_COMMON) || !af_cw_native_reserve_common(AF_CW_NATIVE,id))return 0;
    for(unsigned i=0;i<sizeof(af_cw_state.common);i++)((u8 *)&af_cw_state.common)[i]=0;
    af_cw_state.present=1;
    return af_cw_get_common(source,id);
}
int af_cw_check_keep(int type) {
    /* Source manager callbacks use the mapped native control identity. Native
     * keep bit arrays are not extended implicitly for an additional event. */
    if(type!=AF_CW_NATIVE || !enabled())return 0;
    if(!af_cw_native_get_common(AF_CW_NATIVE,AF_CW_COMMON))af_cw_state.keep=0;
    return af_cw_state.keep!=0;
}
void af_cw_set_keep(int type) {if(type==AF_CW_NATIVE && enabled())af_cw_state.keep=1;}
void af_cw_clear_keep(int type) {
    if(type==AF_CW_NATIVE) {af_cw_state.keep=0;af_carried_spirit_event_bind(0,0);}
}
void **af_cw_placement(void) {return &af_cw_state.placement;}
void af_cw_finish_hunt(void) {
    if(enabled())(void)af_carried_quest_set_day(af_v3_card_data(),0);
}
