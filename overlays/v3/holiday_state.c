/* Shared saved town/calendar/lighthouse state from complete GAFE01 routines. */
#include "holiday_state.h"
#include "holiday_world.h"
#include "holiday_native.h"
typedef unsigned int u32;
static int date_valid(AFDiaryDate d) {return d.day && d.day<=af_diary_days(d.year,d.month);}
static int valid(const AFDiary *s) {return af_diary_valid(s) && s->bytes[5]==2;}
static AFDiaryDate start(const AFDiary *s) {
    return (AFDiaryDate){(u32)s->bytes[8]*256+s->bytes[9],s->bytes[10],s->bytes[11]};
}
static int ordinal(AFDiaryDate d) {
    unsigned int y=d.year-1,total=y*365+y/4-y/100+y/400+d.day;
    for(unsigned int m=1;m<d.month;m++)total+=af_diary_days(d.year,m);
    return (int)total;
}
static void clear(AFDiary *s) {for(u32 i=8;i<15;i++)s->bytes[i]=0;}
int af_holiday_state_init(AFDiary *s,u32 random_thirty) {
    if(!s || random_thirty>=30 || af_diary_upgrade(s)!=AF_DIARY_OK)return 0;
    if(!s->bytes[6]) {u32 day=random_thirty+1;s->bytes[6]=day+(day>=4);}
    return 1;
}
int af_holiday_state_period(const AFDiary *s,AFDiaryDate d) {
    if(!valid(s) || !date_valid(d))return -1;
    if(!s->bytes[11])return AF_HOLIDAY_NONE;
    int days=ordinal(d)-ordinal(start(s));
    return days<0 || days>17?AF_HOLIDAY_NONE:days==0?AF_HOLIDAY_DAY_ZERO:
        days<=7?AF_HOLIDAY_WEEK:AF_HOLIDAY_AFTER;
}
int af_holiday_state_day(const AFDiary *s,AFDiaryDate d) {
    if(!valid(s) || !date_valid(d))return -1;
    if(!s->bytes[11])return 0;
    int n=ordinal(d)-ordinal(start(s))-1;
    return n<0?0:n>6?6:n;
}
int af_holiday_state_available(AFDiary *s,AFDiaryDate d) {
    int p=af_holiday_state_period(s,d);
    if(p<0)return -1;
    if(!s->bytes[11])return 1;
    if(p!=AF_HOLIDAY_NONE)return 0;
    clear(s);return 1;
}
int af_holiday_state_after(const AFDiary *s,AFDiaryDate d) {
    int p=af_holiday_state_period(s,d);
    return p<0?-1:p!=AF_HOLIDAY_NONE && (s->bytes[13]&15)!=0;
}
int af_holiday_state_start(AFDiary *s,AFDiaryDate d,u32 player) {
    if(!valid(s) || !s->bytes[6] || !date_valid(d) || player>=4)return 0;
    clear(s);s->bytes[8]=d.year>>8;s->bytes[9]=d.year;s->bytes[10]=d.month;s->bytes[11]=d.day;
    s->bytes[13]=1u<<player;return 1;
}
int af_holiday_state_check(const AFDiary *s,AFDiaryDate d,u32 player) {
    int p=af_holiday_state_period(s,d);
    if(p<0 || player>4)return -1;
    if(player==4 || p!=AF_HOLIDAY_AFTER || s->bytes[14]&(1u<<player))return 0;
    if(s->bytes[12]==127) {
        if(s->bytes[13]&(1u<<(player+4)))return s->bytes[10]==1?1:3;
    } else if(s->bytes[13]&(1u<<player))return s->bytes[10]==1?2:4;
    return 0;
}
int af_holiday_state_complete(AFDiary *s,AFDiaryDate d,u32 player) {
    if(!valid(s) || !s->bytes[11] || !date_valid(d) || player>=4)return 0;
    s->bytes[14]|=1u<<player;
    /* Preserve source order: Event_Check runs AFTER setting this player's bit. */
    int check=af_holiday_state_check(s,d,player);
    if(check==2 || check==4)s->bytes[14]|=15;
    return 1;
}
static int previous(AFDiaryDate *d) {
    if(--d->day)return 1;
    if(!(--d->month)) {if(d->year==1)return 0;d->year--;d->month=12;}
    d->day=af_diary_days(d->year,d->month);return 1;
}
int af_holiday_state_switch_check(const AFDiary *s,AFDiaryDate d,u32 hour) {
    if(!date_valid(d) || hour>=24 || (hour<6 && !previous(&d)))return -1;
    int p=af_holiday_state_period(s,d);
    if(p<0)return -1;
    return p!=AF_HOLIDAY_WEEK || (s->bytes[12]&(1u<<af_holiday_state_day(s,d)))!=0;
}
int af_holiday_state_enter(const AFDiary *s,AFDiaryDate d,u32 hour,u32 player,int working) {
    int p=af_holiday_state_period(s,d);
    if(p<0 || hour>=24 || player>4)return -1;
    return player<4 && !working && p==AF_HOLIDAY_WEEK && hour>=18 && hour<22 &&
        !(s->bytes[12]&(1u<<af_holiday_state_day(s,d)));
}
int af_holiday_state_switch_on(AFDiary *s,AFDiaryDate d,u32 player) {
    int day=af_holiday_state_day(s,d);
    if(day<0 || !s->bytes[11] || player>4)return 0;
    s->bytes[12]|=1u<<day;if(player<4)s->bytes[13]|=1u<<(player+4);return 1;
}
int af_holiday_state_dates(const AFDiary *s,u32 year,AFDiaryDates *out) {
    if(!valid(s) || !s->bytes[6] || !out || year<2000 || year>2032)return 0;
    AFDiaryDate moon={year,0,0};
    if(year>=2002 && year<=2030) {
        moon.month=af_holiday_harvest_days[(year-2002)*2];moon.day=af_holiday_harvest_days[(year-2002)*2+1];
    } else {
        AFDiaryDate lunar={year,8,15};
        if(!af_holiday_state_lunar(&moon,&lunar))return 0;
    }
    if(moon.year!=year || !date_valid(moon))return 0;
    *out=(AFDiaryDates){s->bytes[6],moon.month,moon.day};return 1;
}
int af_holiday_state_clock(AFDiary *s,const unsigned char rtc[8],u32 working,AFHolidayClock *out) {
    if(!rtc || !out || rtc[2]>=24 || working>1)return 0;
    AFHolidayClock c={0};c.date=(AFDiaryDate){(u32)rtc[6]*256+rtc[7],rtc[5],rtc[3]};
    if(!date_valid(c.date) || !af_holiday_state_dates(s,c.date.year,&c.special))return 0;
    int year=(int)c.date.year-1980;
    c.hour=rtc[2];c.working=working;
    c.vernal_day=(int)(20.8431f+0.242194f*(float)year)-year/4;
    c.autumnal_day=(int)(23.2488f+0.242194f*(float)year)-year/4;
    /* A working player exits source scheduling before vacation updates. */
    int available=working?0:af_holiday_state_available(s,c.date);
    if(available<0)return 0;
    c.vacation_available=(u32)available;*out=c;return 1;
}
static AFDiaryDate now(void) {
    return (AFDiaryDate){(u32)af_holiday_rtc[6]*256+af_holiday_rtc[7],af_holiday_rtc[5],af_holiday_rtc[3]};
}
static int after(void *context) {
    AFHolidayNpc *a=context;
    if(!a || a->failed)return -1;
    return af_holiday_state_after(af_v3_diary_data(),now());
}
static void quest_start(void *context) {
    AFHolidayNpc *a=context;
    if(!a || a->failed)return;
    if(!af_holiday_state_start(af_v3_diary_data(),now(),a->world.player))a->failed=1;
}
int af_holiday_npc_event_world(AFHolidayNpc *a,AFHolidayEventWorld *out) {
    if(!a || !out || a->failed)return 0;
    AFDiary *d=af_v3_diary_data();
    if(!valid(d))return 0;
    if(!d->bytes[6] && !af_holiday_state_init(d,(u32)(af_holiday_random_native()*30.0f)))return 0;
    AFDiaryDates dates;
    if(!af_holiday_state_dates(d,now().year,&dates))return 0;
    *out=(AFHolidayEventWorld){dates,after,quest_start};return 1;
}
int af_holiday_calendar_update(void) {
    const AFNpcExtras *t=&af_v3_npc_extras;
    if(t->magic!=AF_NPC_EXTRA_MAGIC || t->version!=1 || t->stride!=44 ||
       !t->count || t->count>AF_NPC_EXTRA_MAX)return -1;
    const AFNpcExtra *actor=0;
    for(u32 i=0;i<t->count;i++)if(t->rows[i].name==0xD090)actor=t->rows+i;
    if(!actor || actor->profile!=0xCC)return -1;
    if(actor->flags!=3)return 0;
    AFDiary *d=af_v3_diary_data();
    if(!valid(d))return -1;
    if(!d->bytes[6] && !af_holiday_state_init(d,(u32)(af_holiday_random_native()*30.0f)))return -1;
    unsigned char rtc[8];for(u32 i=0;i<8;i++)rtc[i]=af_holiday_rtc[i];
    AFHolidayClock clock;
    if(!af_holiday_state_clock(d,rtc,0,&clock))return -1;
    /* All 49 source rows feed the same 44-owner native directory. Existing
     * native/camper rows remain; native hourly dispatch owns ACTIVE/RUN/SHOW. */
    return af_holiday_native_schedule(&clock);
}
int af_holiday_calendar_before_cleanup(void) {
    (void)af_holiday_calendar_update();
    /* Retain camper scheduling and the native first-entry return value. The
     * caller's job gate, cleanup loops, and hourly update remain unchanged. */
    return af_holiday_calendar_previous();
}
