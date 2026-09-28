/* Monthly calendar persistence from GAFE01 m_calendar.c and its UI mark reader.
 * Operates on the endian-independent diary storage, not native player offsets. */
#include "diary.h"
typedef af_diary_u8 u8;
typedef af_diary_u32 u32;
static u32 word(const u8 *p) {return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];}
static void put(u8 *p,u32 v) {p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
unsigned int af_diary_days(unsigned int year,unsigned int month) {
    static const u8 days[]={31,28,31,30,31,30,31,31,30,31,30,31};
    if(!year || year>65535 || month<1 || month>12)return 0;
    return days[month-1]+(month==2 && !(year%4) && (year%100 || !(year%400)));
}
static int date_valid(AFDiaryDate d) {return d.day && d.day<=af_diary_days(d.year,d.month);}
int af_diary_weekday(AFDiaryDate d) {
    static const u8 month_offsets[]={0,3,2,5,0,3,5,1,4,6,2,4};
    if(!date_valid(d))return -1;
    u32 y=d.year-(d.month<3);
    return (int)((y+y/4-y/100+y/400+month_offsets[d.month-1]+d.day)%7);
}
static int dates_valid(AFDiaryDates dates,AFDiaryDate current) {
    return dates.town_day>=1 && dates.town_day<=31 &&
        date_valid((AFDiaryDate){current.year,dates.harvest_month,dates.harvest_day});
}
static u8 *calendar(AFDiary *d,u32 player) {return d->bytes+16+player*AF_DIARY_PLAYER;}
static const u8 *cal(const AFDiary *d,u32 player) {return d->bytes+16+player*AF_DIARY_PLAYER;}
static void clear(u8 *c) {for(u32 i=0;i<AF_DIARY_CALENDAR;i++)c[i]=0;}
static void clear_month(u8 *c,u32 month) {
    static const u8 masks[]={0,0,0,0,0,1,2,12,16,32,64,0};
    put(c+month*4,0);put(c+48+month*4,0);c[97]&=(u8)~masks[month];
}
static void check_delete(u8 *c,AFDiaryDate d,AFDiaryDates dates) {
    u32 year=(u32)c[100]<<8|c[101];
    int interval=(int)d.month-c[102]+((int)d.year-(int)year)*12;
    if(!year || interval>=12 || interval<=-12) {clear(c);return;}
    for(int i=0;i<interval;i++)clear_month(c,(c[102]+i)%12);
    for(int i=0;i>interval;i--)clear_month(c,(c[102]+11+i)%12);
    if(d.day!=af_diary_days(d.year,d.month)) {
        u32 mask=(1u<<d.day)-1;
        put(c+4*(d.month-1),word(c+4*(d.month-1))&mask);
        put(c+48+4*(d.month-1),word(c+48+4*(d.month-1))&mask);
        switch(d.month) {
        case 6: {
            /* GAFE01 uses the weekday of the following day here. Preserve the
             * donor rule; do not silently substitute the Japanese revision. */
            int weekday=af_diary_weekday((AFDiaryDate){d.year,d.month,d.day+1});
            if(((int)d.day-weekday)/7+1<3)c[97]&=~1u;
            break;
        }
        case 7: if(d.day<dates.town_day)c[97]&=~2u;break;
        case 8:
            if(d.day<12)c[97]&=~4u;
            if(d.day<21)c[97]&=~8u;
            break;
        case 9: case 10:
            if(d.month==dates.harvest_month && d.day<dates.harvest_day)
                c[97]&=(u8)~(d.month==9?16u:32u);
            break;
        case 11: if(d.day<11)c[97]&=~64u;break;
        }
    }
}
int af_diary_calendar_refresh(AFDiary *d,u32 player,AFDiaryDate now,AFDiaryDates dates) {
    if(player>=4 || !af_diary_valid(d) || !date_valid(now) || !dates_valid(dates,now))return AF_DIARY_ARGUMENT;
    check_delete(calendar(d,player),now,dates);return AF_DIARY_OK;
}
int af_diary_calendar_visit(AFDiary *d,u32 player,AFDiaryDate now,AFDiaryDates dates) {
    int result=af_diary_calendar_refresh(d,player,now,dates);
    if(result<0)return result;
    u8 *c=calendar(d,player);
    put(c+4*(now.month-1),word(c+4*(now.month-1))|(1u<<(now.day-1)));
    c[100]=now.year>>8;c[101]=now.year;c[102]=now.month;return AF_DIARY_OK;
}
int af_diary_calendar_event(AFDiary *d,u32 player,AFDiaryDate now,AFDiaryDates dates,u32 event) {
    if(player>=4 || !af_diary_valid(d) || !date_valid(now) || !dates_valid(dates,now) || event>255)
        return AF_DIARY_ARGUMENT;
    u8 *c=calendar(d,player);check_delete(c,now,dates);
    switch(event) {
    case 11:c[97]|=1;break;
    case 4:c[97]|=2;break;
    case 16:c[97]|=4;break;
    case 1:c[97]|=8;break;
    case 17:if(now.month==9)c[97]|=16;else if(now.month==10)c[97]|=32;break;
    case 19:c[97]|=64;break;
    case 255:break;
    default:put(c+48+4*(now.month-1),word(c+48+4*(now.month-1))|(1u<<(now.day-1)));break;
    }
    return AF_DIARY_OK;
}
int af_diary_calendar_mark(const AFDiary *d,u32 player,AFDiaryDate today,AFDiaryDate selected,AFDiaryDates dates) {
    if(player>=4 || !af_diary_valid(d) || !date_valid(today) || !date_valid(selected) ||
       !dates_valid(dates,selected))return AF_DIARY_ARGUMENT;
    int delta=((int)today.year-selected.year)*12+(int)today.month-selected.month;
    if(delta<0 || delta>=12)return 0;
    const u8 *c=cal(d,player);u32 flag=0;
    switch(selected.month) {
    case 6: {
        AFDiaryDate next=selected;
        if(++next.day>30) {next.day=1;next.month=7;}
        int weekday=af_diary_weekday(next);
        if(weekday==0 && 1+((int)selected.day-weekday)/7==3)flag=1;
        break;
    }
    case 7:if(selected.day==dates.town_day)flag=2;break;
    case 8:if(selected.day==12)flag=4;else if(selected.day==21)flag=8;break;
    case 11:if(selected.day==11)flag=64;break;
    default:if(selected.month==dates.harvest_month && selected.day==dates.harvest_day)flag=48;break;
    }
    if((c[97]&flag) || (word(c+48+4*(selected.month-1))&(1u<<(selected.day-1))))return 2;
    return (word(c+4*(selected.month-1))>>(selected.day-1))&1;
}
