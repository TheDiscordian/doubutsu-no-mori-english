/* Actual resident menu entry, clock/player data, and save-capacity admission. */
#include "diary_native.h"
#ifdef AF_DIARY_HOLIDAYS
#include "holiday_calendar.h"
#endif
#define CANDIDATE_GUARD 0xAF445941u
const unsigned int af_diary_native_context_bytes=sizeof(AFDiaryNative);
_Static_assert(sizeof(AFDiaryNative)<=0x6F0,"Diary context exceeds guarded state reservation");

static AFDiaryDate now(void) {
    return (AFDiaryDate){(unsigned int)af_diary_native_rtc[6]*256+af_diary_native_rtc[7],
        af_diary_native_rtc[5],af_diary_native_rtc[3]};
}
unsigned short af_diary_native_selected(void) {
    unsigned short selected=0;
    for(unsigned int style=0;style<16;style++) {
        const unsigned char *p=af_diary_native_profiles[63+style];
        unsigned int index=(unsigned int)p[0]*256+p[1],item=(unsigned int)p[2]*256+p[3];
        if(index==1087+style && item==0x30FC+style*4 && !p[4] && !p[5] && !p[6] && p[7]==1)
            selected|=1u<<style;
    }
    return selected;
}
static int prepare_calendar(AFDiaryNative *c,AFDiaryDate date,unsigned int owner) {
    if(!c || owner>=4)return AF_DIARY_ARGUMENT;
    const unsigned char *player=af_diary_native_players[owner];
    int result=
#ifdef AF_DIARY_HOLIDAYS
        af_holiday_diary_month
#else
        af_diary_events_month
#endif
        (&c->calendar,date.year,date.month,player[0xA92],player[0xA93]);
    c->calendar_error=result<0?result:0;return result;
}
static unsigned int event_count(void *context,AFDiaryDate date,unsigned int owner) {
    AFDiaryNative *c=context;
    if(!date.day || date.day>af_diary_days(date.year,date.month) ||
       prepare_calendar(c,date,owner)!=AF_DIARY_OK)return 0;
    return c->calendar.counts[date.day-1];
}
static int calendar(void *context,const AFDiaryMenu *menu,AFDiaryDraw *draw) {
    AFDiaryNative *c=context;
    if(prepare_calendar(c,menu->selected,menu->owner)!=AF_DIARY_OK)return c->calendar_error;
    return
#ifdef AF_DIARY_HOLIDAYS
        af_holiday_diary_draw
#else
        af_diary_events_draw
#endif
        (&c->calendar,menu,c->live,draw);
}
static int special_dates(AFDiaryDate date,AFDiaryDates *out) {
#ifdef AF_DIARY_HOLIDAYS
    return af_holiday_diary_dates(date,out);
#else
    (void)date;*out=(AFDiaryDates){0,0,0};return 1;
#endif
}
static int capacity(void *context,const AFDiary *candidate) {
    AFDiaryNative *c=context;
    if(c!=&af_diary_native_context || c->live!=af_v3_diary_data() ||
       candidate!=&af_diary_native_candidate)return AF_DIARY_ARGUMENT;
    for(unsigned int i=0;i<4;i++)
        if(af_diary_native_candidate_guard[i]!=CANDIDATE_GUARD)return AF_DIARY_ARGUMENT;
    return af_v3_diary_preflight(candidate);
}
int af_diary_native_open(void *game,int owner) {
    unsigned int viewer=af_diary_native_player;
    if(!game || owner<0 || owner>=4 || viewer>=4 || !af_diary_native_selected())return 0;
    void *submenu=(unsigned char *)game+0x1CBC;
    /* Do not disturb an already-owned editor or its width/calendar buffers. */
    if(*(unsigned int *)((unsigned char *)submenu+4))return 0;
    AFDiaryNative *c=&af_diary_native_context;
    c->live=af_v3_diary_data();c->calendar.valid=0;c->calendar_error=0;
    for(unsigned int i=0;i<256;i++) {
        int width=af_diary_native_width(i,1);
        if(width<1 || width>12)return 0;
        c->widths[i]=width;
    }
    for(unsigned int i=0;i<4;i++)af_diary_native_candidate_guard[i]=CANDIDATE_GUARD;
    AFDiaryDates dates;if(!special_dates(now(),&dates))return 0;
    AFDiaryMenuAccess access={c->live,&af_diary_native_candidate,c->widths,capacity,c,event_count};
    return af_diary_screen_open(&af_diary_native_screen,submenu,&access,viewer,owner,
        now(),dates,af_diary_native_art,calendar);
}
int af_diary_native_visit(void) {
    if(af_diary_native_player>=4 || !af_diary_native_selected())return AF_DIARY_UNCHANGED;
    AFDiary *live=af_v3_diary_data();AFDiaryDate date=now();
    if(!date.day || date.day>af_diary_days(date.year,date.month))return AF_DIARY_ARGUMENT;
    const unsigned char *c=live->bytes+16+af_diary_native_player*AF_DIARY_PLAYER;
    unsigned int offset=(date.month-1)*4,mask=1u<<(date.day-1);
    unsigned int played=(unsigned int)c[offset]<<24|(unsigned int)c[offset+1]<<16|
        (unsigned int)c[offset+2]<<8|c[offset+3];
    if((unsigned int)c[100]*256+c[101]==date.year && c[102]==date.month && (played&mask))
        return AF_DIARY_UNCHANGED;
    AFDiaryDates dates;if(!special_dates(date,&dates))return AF_DIARY_ARGUMENT;
    return af_diary_calendar_visit(live,af_diary_native_player,date,dates);
}
int af_diary_native_live_player(int player) {
    int result=af_diary_native_live_check(player);
    /* This caller runs only after mEv_run's title, player-select, demo, and
     * player-control gates. The original live-player result is unchanged. */
    if(result && player==af_diary_native_player)(void)af_diary_native_visit();
    return result;
}
int af_diary_native_attend(unsigned int native_event) {
    if(af_diary_native_player>=4 || !af_diary_native_selected())return AF_DIARY_UNCHANGED;
    AFDiaryDate date=now();AFDiaryNative *c=&af_diary_native_context;
    if(!date.day || date.day>af_diary_days(date.year,date.month) ||
       prepare_calendar(c,date,af_diary_native_player)!=AF_DIARY_OK)return AF_DIARY_ARGUMENT;
    for(unsigned int i=0;i<c->calendar.counts[date.day-1];i++) {
        unsigned int event=c->calendar.events[date.day-1][i];
        if(event<AF_DIARY_EVENT_BIRTHDAY && af_diary_event_rules[event].type==native_event)
            return af_diary_calendar_event(af_v3_diary_data(),af_diary_native_player,
                date,(AFDiaryDates){0,0,0},254);
    }
    return AF_DIARY_UNCHANGED;
}
