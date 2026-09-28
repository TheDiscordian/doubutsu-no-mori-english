/* Calendar dates are N64 event dates, not the localized GC holiday schedule. */
#include "diary_events.h"

static unsigned int md(AFDiaryDate d) {return (unsigned int)d.month*256+d.day;}
static int endpoint(AFDiaryDate *out,unsigned int word,AFDiaryDate selected) {
    unsigned int month=word>>24,day=(word>>16)&255;
    if(month==50)month=selected.month;
    if(month>=80) {
        /* lbRk_ToSeiyouReki only checks year >= 1 before indexing its 2000..2032
         * table. Guard both ends here, including the adjacent browsing years. */
        if(month>92 || selected.year<2000 || selected.year>2032 || !day)return 0;
        AFDiaryDate lunar={selected.year,month-80,day};
        return af_diary_native_lunar(out,&lunar) && out->year==selected.year &&
            out->day && out->day<=af_diary_days(out->year,out->month);
    }
    if(month<1 || month>12)return 0;
    unsigned int days=af_diary_days(selected.year,month);
    if(day==99)day=days;
    else if(day&128) {
        unsigned int week=(day&0x78)>>3,weekday=day&7;
        if(weekday>6)return 0;
        if(week==9) {
            if(month>selected.month)week=1;
            else if(month<selected.month)week=15;
            else {
                int n=(int)selected.day-af_diary_weekday(selected)+(int)weekday;
                if(n<1 || n>(int)days)return 0;
                day=n;week=0;
            }
        }
        if(week==15)day=days-(af_diary_weekday((AFDiaryDate){selected.year,month,days})+7-weekday)%7;
        else if(week) {
            if(week>5)return 0;
            day=1+7*(week-1)+(weekday+7-af_diary_weekday((AFDiaryDate){selected.year,month,1}))%7;
        }
    }
    if(!day || day>days)return 0;
    *out=(AFDiaryDate){selected.year,month,day};return 1;
}
static int occurs(const AFDiaryEventRule *rule,AFDiaryDate date) {
    const unsigned int *row=af_diary_event_master[rule->row];
    AFDiaryDate start,end;
    if(row[2]!=rule->type || !endpoint(&start,row[0],date))return 0;
    if(rule->single)return md(date)==md(start);
    if(!endpoint(&end,row[1],date))return 0;
    unsigned int a=md(start),b=md(end),now=md(date);
    return a<=b?(now>=a && now<=b):(now>=a || now<=b);
}
int af_diary_events_month(AFDiaryEventMonth *cache,unsigned int year,unsigned int month,
    unsigned int birth_month,unsigned int birth_day) {
    if(!cache || !af_diary_days(year,month) || birth_month>255 || birth_day>255)return AF_DIARY_ARGUMENT;
    if(cache->valid && cache->year==year && cache->month==month &&
       cache->birthday_month==birth_month && cache->birthday_day==birth_day)return AF_DIARY_OK;
    cache->valid=0;cache->year=year;cache->month=month;
    cache->birthday_month=birth_month;cache->birthday_day=birth_day;
    for(unsigned int day=1;day<=31;day++) {
        unsigned int n=0;
        if(day<=af_diary_days(year,month)) {
            for(unsigned int event=0;event<AF_DIARY_EVENT_BIRTHDAY;event++) {
                const AFDiaryEventRule *rule=af_diary_event_rules+event;
                if(rule->row>=81 || rule->single>1 || rule->reserved ||
                   af_diary_event_master[rule->row][2]!=rule->type)return AF_DIARY_ARGUMENT;
                if(occurs(rule,(AFDiaryDate){year,month,day})) {
                    if(n==AF_DIARY_EVENT_MAX)return AF_DIARY_FULL;
                    cache->events[day-1][n++]=event;
                }
            }
            if(month==birth_month && day==birth_day) {
                if(n==AF_DIARY_EVENT_MAX)return AF_DIARY_FULL;
                cache->events[day-1][n++]=AF_DIARY_EVENT_BIRTHDAY;
            }
        }
        cache->counts[day-1]=n;
    }
    cache->valid=1;return AF_DIARY_OK;
}
int af_diary_events_draw(const AFDiaryEventMonth *c,const AFDiaryMenu *m,
    const AFDiary *live,AFDiaryDraw *draw) {
    if(!c || !c->valid || !m || !draw || c->year!=m->selected.year ||
       c->month!=m->selected.month || !m->selected.day ||
       m->selected.day>af_diary_days(c->year,c->month))return AF_DIARY_ARGUMENT;
    int first=af_diary_weekday((AFDiaryDate){c->year,c->month,1});
    unsigned int days=af_diary_days(c->year,c->month);
    for(unsigned int i=0;i<37;i++)draw->day_types[i]=0;
    for(unsigned int day=1;day<=days;day++) {
        unsigned int cell=first+day-1,type=cell%7?1:2;
        for(unsigned int e=0;e<c->counts[day-1];e++)
            if(c->events[day-1][e]!=AF_DIARY_EVENT_BIRTHDAY)type=3;
        if(c->year==m->today.year && c->month==m->today.month && day==m->today.day)type=4;
        draw->day_types[cell]=type;
    }
    draw->event_length=0;draw->event_label=0;draw->event_attended=0;
    if(m->state!=AF_DIARY_MONTH && m->events) {
        if(m->events!=c->counts[m->selected.day-1] || m->event_index>=m->events)return AF_DIARY_ARGUMENT;
        unsigned int event=c->events[m->selected.day-1][m->event_index];
        if(event>=AF_DIARY_EVENT_COUNT)return AF_DIARY_ARGUMENT;
        const AFDiaryEventLabel *label=af_diary_event_labels+event;
        if(!label->text || !label->size || label->size>48)return AF_DIARY_ARGUMENT;
        draw->event_label=label->text;draw->event_length=label->size;
        int mark=af_diary_calendar_mark(live,m->owner,m->today,m->selected,(AFDiaryDates){0,0,0});
        if(mark<0)return mark;
        /* The donor also treats being present on one's birthday as attendance.
         * Other events need a real participation mark, never mere occurrence. */
        draw->event_attended=event==AF_DIARY_EVENT_BIRTHDAY?mark!=0:mark==2;
    }
    return AF_DIARY_OK;
}
