/* Native data bindings on the host; not an emulator or hardware test. */
#include "diary_native.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

/* Compile the real native lunar implementation beside the diary provider. */
typedef int s32;
typedef unsigned char lbRTC_day_t;
typedef AFDiaryDate lbRTC_ymd_t;
typedef struct {unsigned char month,day;} lbRekiPhase;
enum {FALSE=0,TRUE=1,lbRTC_MONTHS_MAX=12,lbRk_YEAR_MIN=2000,lbRk_YEAR_MAX=2032,
    lbRk_YEAR_NUM=33,lbRk_KYUU_LEAP_MONTH=13,lbRk_KYUU_MONTH_START=1,
    lbRk_KYUU_MONTH_END=12,lbRk_KYUU_DAY_START=1};
#define UNUSED __attribute__((unused))
#include "reference-reki.inc"
static unsigned int lunar_calls;
int af_diary_native_lunar(AFDiaryDate *out,const AFDiaryDate *in) {
    assert(in->year>=2000 && in->year<=2032);lunar_calls++;
    return lbRk_ToSeiyouReki(out,in);
}
AFDiaryNative af_diary_native_context;
AFDiaryScreen af_diary_native_screen;
AFDiary af_diary_native_candidate;
unsigned int af_diary_native_candidate_guard[4];
const unsigned char af_diary_native_art[16]={0};
const unsigned char af_diary_native_rtc[8]={0,30,12,21,0,6,7,234};
const unsigned char af_diary_native_player=
#ifdef AF_TEST_DIARY_VISITOR
    4;
#else
    0;
#endif
const unsigned char af_diary_native_players[4][0xBD0]={
    {[0xA92]=6,[0xA93]=21},{[0xA92]=6,[0xA93]=19},
    {[0xA92]=255,[0xA93]=255},{[0xA92]=2,[0xA93]=29}};
static AFDiary live;
static unsigned char game[0x1E00] __attribute__((aligned(16)));
static unsigned int saves,opened;
static int live_player_result=1;
int af_diary_native_live_check(int player) {assert(player>=0 && player<4);return live_player_result;}
AFDiary *af_v3_diary_data(void) {return &live;}
int af_diary_native_width(unsigned int code,int font) {assert(font==1);return code=='i'?2:6;}
int af_v3_diary_preflight(const AFDiary *candidate) {
    assert(candidate==&af_diary_native_candidate && candidate!=&live);saves++;return 1;
}
void af_diary_submenu_open(void *s,int program,int data0,int data1,void *data2,void *data3) {
    assert(s==game+0x1CBC && program==2 && (unsigned int)data0==AF_DIARY_SCREEN_MAGIC);
    assert(data1>=0 && data1<4 && data2==&af_diary_native_screen && !data3);
    *(unsigned int *)((unsigned char *)s+4)=program;opened++;
}
static unsigned int find(const AFDiaryEventMonth *c,unsigned int day,unsigned int type) {
    for(unsigned int i=0;i<c->counts[day-1];i++) {
        unsigned int e=c->events[day-1][i];
        if(e<AF_DIARY_EVENT_BIRTHDAY && af_diary_event_rules[e].type==type)return 1;
    }
    return 0;
}
static void calendar_checks(void) {
    AFDiaryEventMonth c={0};unsigned int months=0;
    for(unsigned int y=1999;y<=2033;y++)for(unsigned int m=1;m<=12;m++) {
        assert(af_diary_events_month(&c,y,m,2,29)==1);months++;
        unsigned int calls=lunar_calls;
        assert(af_diary_events_month(&c,y,m,2,29)==1 && lunar_calls==calls);
        for(unsigned int d=1;d<=31;d++) {
            assert(c.counts[d-1]<=AF_DIARY_EVENT_MAX);
            if(d>af_diary_days(y,m))assert(c.counts[d-1]==0);
            if(m==6 || m==11)assert(find(&c,d,m==6?20:2)==
                (d<=af_diary_days(y,m) && af_diary_weekday((AFDiaryDate){y,m,d})==0));
            if(m==8)assert(find(&c,d,11)==(af_diary_weekday((AFDiaryDate){y,m,d})==6));
            if(m==10)assert(find(&c,d,13)==(d==31));
            if(m==12)assert(find(&c,d,5)==(d==24));
            if(m==4)assert(find(&c,d,12)==(d>=5 && d<=7));
        }
    }
    assert(months==420);
    assert(af_diary_events_month(&c,2026,6,6,21)==1 && c.counts[20]==3);
    assert(find(&c,21,27) && !find(&c,20,27));
    assert(af_diary_events_month(&c,2026,5,255,255)==1 && find(&c,10,28));
    assert(af_diary_events_month(&c,2026,10,255,255)==1 && find(&c,12,1));
    AFDiaryDate lunar={2026,8,15},date;
    assert(lbRk_ToSeiyouReki(&date,&lunar));
    assert(af_diary_events_month(&c,date.year,date.month,255,255)==1 && find(&c,date.day,22));
    lunar.month=9;lunar.day=13;assert(lbRk_ToSeiyouReki(&date,&lunar));
    assert(af_diary_events_month(&c,date.year,date.month,255,255)==1 && find(&c,date.day,21));
    assert(af_diary_events_month(&c,2026,2,2,29)==1 && !c.counts[28]);
    assert(af_diary_events_month(&c,2028,2,2,29)==1 && c.counts[28]==1);
    assert(af_diary_events_month(&c,2026,0,0,0)==AF_DIARY_ARGUMENT);
}
static void visitor_checks(void) {
    static AFDiary before;
    const AFDiaryDate today={2026,6,21};
    af_diary_reset(&live);
    for(unsigned owner=0;owner<4;owner++) {
        assert(af_diary_calendar_visit(&live,owner,today,(AFDiaryDates){0,0,0})==1);
        live.bytes[16+owner*AF_DIARY_PLAYER+AF_DIARY_CALENDAR+5*AF_DIARY_PAGE]='A'+owner;
    }
    before=live;
    assert(af_diary_native_visit()==0 && af_diary_native_attend(27)==0);
    assert(!memcmp(&live,&before,sizeof(live)));
    for(unsigned owner=0;owner<4;owner++) {
        *(unsigned int *)(game+0x1CC0)=0;
        assert(af_diary_native_open(game,(int)owner));
        AFDiaryScreen *s=&af_diary_native_screen;
        assert(s->menu.viewer==4 && s->menu.owner==owner);
        assert(af_diary_menu_input(&s->menu,&s->access,AF_DIARY_A,0,0)==1);
        assert(s->calendar(s->access.context,&s->menu,&s->draw)==1 && !s->draw.event_attended);
        unsigned char days[37],marks[37];
        assert(af_diary_menu_grid(&s->menu,&live,(AFDiaryDates){0,0,0},days,marks)==1);
        for(unsigned i=0;i<37;i++)assert(marks[i]==0);
        assert(af_diary_menu_input(&s->menu,&s->access,AF_DIARY_A,0,0)==1);
        assert(s->menu.state==AF_DIARY_READ && s->menu.draft.readonly);
        assert(s->menu.draft.text[0]=='A'+owner);
        assert(af_diary_command(&s->menu.draft,8,'Z',s->access.widths)==AF_DIARY_READONLY);
        assert(af_diary_lock(&live,4,owner,1)==AF_DIARY_READONLY);
        assert(af_diary_commit(&live,&s->menu.draft,&af_diary_native_candidate,
            s->access.widths,s->access.capacity,s->access.context)==AF_DIARY_READONLY);
        assert(af_diary_menu_input(&s->menu,&s->access,AF_DIARY_START,0,0)==1);
        assert(s->menu.state==AF_DIARY_DAY);
        assert(!memcmp(&live,&before,sizeof(live)) && saves==0);
        assert(af_diary_lock(&live,owner,owner,1)==1);
        *(unsigned int *)(game+0x1CC0)=0;
        assert(af_diary_native_open(game,(int)owner));
        assert(af_diary_menu_input(&s->menu,&s->access,AF_DIARY_A,0,0)==1);
        assert(af_diary_menu_input(&s->menu,&s->access,AF_DIARY_A,0,0)==1);
        assert(s->menu.state==AF_DIARY_WARNING && s->menu.error==AF_DIARY_LOCKED);
        assert(af_diary_lock(&live,owner,owner,0)==1);
    }
    assert(!af_diary_native_open(game,4));
    assert(!memcmp(&live,&before,sizeof(live)) && saves==0);
    puts("Visiting player opens all four unlocked diaries, reads without editing, respects locks, suppresses foreign calendar marks, and preserves all saved pages");
}
int main(void) {
    if(af_diary_native_player==4) {visitor_checks();return 0;}
    calendar_checks();af_diary_reset(&live);
    assert(af_diary_native_selected()==65535);
    live_player_result=0;assert(af_diary_native_live_player(0)==0);
    assert(live.bytes[16+102]==0);
    live_player_result=1;assert(af_diary_native_live_player(0)==1);
    assert(live.bytes[16+102]==6 && af_diary_native_visit()==0);
    assert(!af_diary_native_open(0,0) && !af_diary_native_open(game,4));
    assert(af_diary_native_open(game,0) && opened==1);
    AFDiaryScreen *s=&af_diary_native_screen;
    assert(s->menu.today.year==2026 && s->menu.today.month==6 && s->menu.today.day==21);
    assert(s->access.live==&live && s->access.scratch==&af_diary_native_candidate);
    assert(s->access.widths['i']==2 && s->access.widths['W']==6);
    assert(!af_diary_native_open(game,1) && s->menu.owner==0);
    assert(s->access.event_count(s->access.context,s->menu.today,0)==3);
    assert(af_diary_menu_input(&s->menu,&s->access,AF_DIARY_A,0,0)==1);
    assert(s->menu.events==3);
    assert(s->calendar(s->access.context,&s->menu,&s->draw)==1);
    assert(s->draw.event_length==12 && !memcmp(s->draw.event_label,"Father's Day",12));
    assert(!s->draw.event_attended && s->draw.day_types[21]==4);
    assert(af_diary_native_attend(11)==0); /* August fireworks are not happening. */
    assert(af_diary_native_attend(27)==1);
    assert(live.bytes[16+97]==0); /* Never index donor special flags with native IDs. */
    assert(s->calendar(s->access.context,&s->menu,&s->draw)==1 && s->draw.event_attended);
    s->menu.event_index=2;
    assert(s->calendar(s->access.context,&s->menu,&s->draw)==1 && s->draw.event_length==8);
    assert(!memcmp(s->draw.event_label,"birthday",8) && s->draw.event_attended);
    assert(s->access.capacity(s->access.context,&af_diary_native_candidate)==1 && saves==1);
    af_diary_native_candidate_guard[1]=0;
    assert(s->access.capacity(s->access.context,&af_diary_native_candidate)<0 && saves==1);
    assert(s->access.capacity(s->access.context,&live)<0 && saves==1);
    *(unsigned int *)(game+0x1CC0)=0;
    assert(af_diary_native_open(game,1) && s->menu.owner==1);
    assert(s->access.event_count(s->access.context,(AFDiaryDate){2026,6,19},1)==1);
    assert(s->access.event_count(s->access.context,(AFDiaryDate){2026,6,21},1)==2);
    puts("Native diary entry, all styles, owner birthdays, real lunar dates, 420 calendar months, and guarded preflight pass");
}
