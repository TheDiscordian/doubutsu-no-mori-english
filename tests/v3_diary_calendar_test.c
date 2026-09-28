/* Compile the actual local donor calendar sources beside the port. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "diary.h"
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef unsigned short lbRTC_year_t;
typedef unsigned char lbRTC_month_t,lbRTC_day_t,lbRTC_weekday_t;
typedef AFDiaryDate lbRTC_time_c;
typedef AFDiaryDate lbRTC_ymd_c;
enum {FALSE,TRUE,mPr_FOREIGNER=4,lbRTC_MONTHS_MAX=12,lbRTC_WEEK=7,
    lbRTC_SUNDAY=0,lbRTC_JUNE=6,lbRTC_JULY=7,lbRTC_AUGUST=8,lbRTC_SEPTEMBER=9,
    lbRTC_OCTOBER=10,lbRTC_NOVEMBER=11,
    mCD_FLAG_MOTHERS_DAY=1,mCD_FLAG_TOWN_DAY=2,mCD_FLAG_METEOR_SHOWER=4,
    mCD_FLAG_FOUNDERS_DAY=8,mCD_FLAG_HARVEST_MOON_9=16,mCD_FLAG_HARVEST_MOON_10=32,
    mCD_FLAG_OFFICERS_DAY=64};
typedef struct {
    u32 played_days[12],event_days[12];u16 event_flags;u8 edit,pad_63;
    lbRTC_year_t year;lbRTC_month_t month;u8 padding;
} mCD_player_calendar_c;
typedef struct {mCD_player_calendar_c calendar;} Private_c;
static struct {Private_c private_data[4];int town_day;} reference_save;
static struct {int player_no;Private_c *now_private;struct {lbRTC_time_c rtc_time;} time;} reference_common;
#define Save_Get(field) (reference_save.field)
#define Common_Get(field) (reference_common.field)
#define Common_GetPointer(field) (&reference_common.field)
#define VERSION 1
#define VER_GAFU01_00 2
static void mem_clear(u8 *p,unsigned int n,int value) {memset(p,value,n);}
static int lbRTC_GetDaysByMonth(unsigned int y,unsigned int m) {
    static const int lengths[12]={31,28,31,30,31,30,31,31,30,31,30,31};
    return lengths[m-1]+(m==2 && y%4==0 && (y%100!=0 || y%400==0));
}
/* Integer Julian-day calculation independent of the port's weekday formula. */
static int lbRTC_Week(int year,int month,int day) {
    int a=(14-month)/12,y=year+4800-a,m=month+12*a-3;
    return (day+(153*m+2)/5+365*y+y/4-y/100+y/400-32045+1)%7;
}
static void lbRk_HarvestMoonDay(lbRTC_ymd_c *d,int year) {*d=(lbRTC_ymd_c){year,9,29};}
#include "reference-calendar.inc"
static AFDiary live;
static u8 *record(unsigned int player) {return live.bytes+16+player*AF_DIARY_PLAYER;}
static void put(u8 *p,u32 v) {p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
static void encode(u8 *c,const mCD_player_calendar_c *r) {
    memset(c,0,104);
    for(int m=0;m<12;m++){put(c+4*m,r->played_days[m]);put(c+48+4*m,r->event_days[m]);}
    c[96]=r->event_flags>>8;c[97]=r->event_flags;c[98]=r->edit;
    c[100]=r->year>>8;c[101]=r->year;c[102]=r->month;
}
int main(void) {
    AFDiaryDates dates={23,9,29};int checks=0;
    reference_save.town_day=23;
    assert(lbRTC_Week(2026,9,27)==0);
    for(int p=0;p<4;p++)for(int delta=-15;delta<=15;delta++)for(int daycase=0;daycase<5;daycase++) {
        af_diary_reset(&live);memset(&reference_save.private_data,0,sizeof(reference_save.private_data));
        reference_common.player_no=p;reference_common.now_private=&reference_save.private_data[p];
        mCD_player_calendar_c *r=&reference_save.private_data[p].calendar;
        r->year=2026;r->month=5;r->edit=1;r->event_flags=127;
        for(int m=0;m<12;m++)r->played_days[m]=r->event_days[m]=0x7FFFFFFF;
        encode(record(p),r);
        int month=2026*12+4+delta;
        AFDiaryDate now={month/12,month%12+1,1};
        now.day=daycase==4?lbRTC_GetDaysByMonth(now.year,now.month):1+7*daycase;
        reference_common.time.rtc_time=now;
        assert(af_diary_weekday(now)==lbRTC_Week(now.year,now.month,now.day));
        mCD_calendar_wellcome_on();assert(af_diary_calendar_visit(&live,p,now,dates)==1);
        u8 encoded[104];encode(encoded,r);assert(!memcmp(record(p),encoded,104));checks++;
        for(int i=0;i<8;i++) {
            static const int events[]={11,4,16,1,17,19,255,2};
            mCD_calendar_event_on(now.year,now.month,now.day,events[i]);
            assert(af_diary_calendar_event(&live,p,now,dates,events[i])==1);
            encode(encoded,r);assert(!memcmp(record(p),encoded,104));checks++;
        }
        for(int d=1;d<=lbRTC_GetDaysByMonth(now.year,now.month);d++) {
            AFDiaryDate selected={now.year,now.month,d};
            assert(af_diary_calendar_mark(&live,p,now,selected,dates)==mCD_make_icon(now.year,now.month,d,p));checks++;
        }
        assert(record(p)[104]==' '); /* Rollover never clears or rewrites text. */
    }
    assert(af_diary_days(2000,2)==29 && af_diary_days(2100,2)==28);
    printf("%d calendar comparisons against donor C pass\n",checks);return 0;
}
