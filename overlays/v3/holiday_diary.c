/* Calendar labels, dates, and attendance share the actual holiday selector.
 * Source event IDs are not native event IDs or display-label indices. */
#include "holiday_calendar.h"
#include "holiday_dialogue.h"
extern const AFHolidayDialogue af_holiday_dialogue_data;
/* Existing nineteen labels stay stable. 255 means a native-only celebration;
 * exercise uses the source's separate special-event identity 103. */
static const unsigned char source_events[19]={
    0,255,255,5,11,7,8,255,12,103,15,17,255,20,255,21,255,26,22
};
static int within(unsigned int now,unsigned int start,unsigned int end,int single) {
    if(single)return now==start;
    return start<=end?(now>=start && now<=end):(now>=start || now<=end);
}
static int push(AFDiaryEventMonth *c,unsigned int day,unsigned int event) {
    unsigned int n=c->counts[day-1];
    if(n>=AF_DIARY_EVENT_MAX)return 0;
    c->events[day-1][n]=event;c->counts[day-1]=n+1;return 1;
}
int af_holiday_diary_dates(AFDiaryDate date,AFDiaryDates *out) {
    if(!out)return 0;
    if(af_holiday_calendar_mode()==AF_HCAL_ORIGINAL) {*out=(AFDiaryDates){0,0,0};return 1;}
    AFHolidayClock c;if(!af_holiday_calendar_clock(date,&c))return 0;
    *out=c.special;return 1;
}
int af_holiday_diary_month(AFDiaryEventMonth *c,unsigned int year,unsigned int month,
        unsigned int birth_month,unsigned int birth_day) {
    unsigned int mode=af_holiday_calendar_mode();AFHolidayClock clock;
    if(!c || !af_diary_days(year,month) || birth_month>255 || birth_day>255)return AF_DIARY_ARGUMENT;
    if(mode==AF_HCAL_ORIGINAL) {
        if(c->calendar_mode)c->valid=0;
        return af_diary_events_month(c,year,month,birth_month,birth_day);
    }
    if(!af_holiday_calendar_clock((AFDiaryDate){year,month,1},&clock))return AF_DIARY_ARGUMENT;
    if(c->valid && c->year==year && c->month==month && c->birthday_month==birth_month &&
       c->birthday_day==birth_day && c->calendar_mode==mode &&
       c->special.town_day==clock.special.town_day && c->special.harvest_month==clock.special.harvest_month &&
       c->special.harvest_day==clock.special.harvest_day)return AF_DIARY_OK;
    c->valid=0;
    int result=af_diary_events_month(c,year,month,birth_month,birth_day);
    if(result!=AF_DIARY_OK)return result;
    c->valid=0;c->calendar_mode=mode;c->special=clock.special;
    for(unsigned int day=1;day<=af_diary_days(year,month);day++) {
        clock.date.day=day;unsigned int today=month*256+day;
        if(mode==AF_HCAL_GC) {
            unsigned int keep=0;
            for(unsigned int i=0;i<c->counts[day-1];i++) {
                unsigned int event=c->events[day-1][i];
                if(event==AF_DIARY_EVENT_BIRTHDAY ||
                   !af_holiday_calendar_native_sources[af_diary_event_rules[event].row][0])
                    c->events[day-1][keep++]=event;
            }
            c->counts[day-1]=keep;
            for(unsigned int event=0;event<19;event++) {
                const AFDiaryEventRule *r=af_diary_event_rules+event;
                const unsigned char *raw=af_holiday_calendar_native_sources[r->row];unsigned int dates[2];
                if(!raw[0])continue;
                int resolved=af_holiday_event_dates(&clock,raw,dates);
                if(resolved<0)return AF_DIARY_ARGUMENT;
                if(!resolved)continue;
                if(within(today,dates[0]>>16,dates[1]>>16,r->single) && !push(c,day,event))return AF_DIARY_FULL;
            }
        }
        for(unsigned int event=0;event<28;event++) {
            int represented=0;
            for(unsigned int i=0;i<19;i++)if(source_events[i]==event)represented=1;
            if(represented)continue;
            unsigned int type=af_holiday_event_data[16+event];int found=0;
            for(unsigned int i=0;i<49;i++) {
                const unsigned char *row=af_holiday_event_data+48+i*12;
                if(row[10] || row[11]!=type)continue;
                unsigned int dates[2];found=1;
                int resolved=af_holiday_event_dates(&clock,row,dates);
                if(resolved<0)return AF_DIARY_ARGUMENT;
                if(!resolved)continue;
                /* All additional calendar holidays are single named dates.
                 * Daily source hours and Tortimer's overlap priority do not
                 * hide a date in the diary. */
                if(today==(dates[0]>>16) && !push(c,day,20+event))return AF_DIARY_FULL;
            }
            if(!found)return AF_DIARY_ARGUMENT;
        }
    }
    c->valid=1;return AF_DIARY_OK;
}
int af_holiday_diary_draw(const AFDiaryEventMonth *c,const AFDiaryMenu *m,
        const AFDiary *live,AFDiaryDraw *draw) {
    if(!c || !c->valid || !m || !draw || c->year!=m->selected.year ||
       c->month!=m->selected.month || !m->selected.day ||
       m->selected.day>af_diary_days(c->year,c->month))return AF_DIARY_ARGUMENT;
    if(!c->calendar_mode)return af_diary_events_draw(c,m,live,draw);
    int first=af_diary_weekday((AFDiaryDate){c->year,c->month,1});
    for(unsigned int i=0;i<37;i++)draw->day_types[i]=0;
    for(unsigned int day=1;day<=af_diary_days(c->year,c->month);day++) {
        unsigned int cell=first+day-1,type=cell%7?1:2;
        for(unsigned int i=0;i<c->counts[day-1];i++)
            if(c->events[day-1][i]!=AF_DIARY_EVENT_BIRTHDAY)type=3;
        if(c->year==m->today.year && c->month==m->today.month && day==m->today.day)type=4;
        draw->day_types[cell]=type;
    }
    draw->event_length=0;draw->event_label=0;draw->event_attended=0;
    if(m->state!=AF_DIARY_MONTH && m->events) {
        if(m->events!=c->counts[m->selected.day-1] || m->event_index>=m->events)return AF_DIARY_ARGUMENT;
        unsigned int event=c->events[m->selected.day-1][m->event_index],source=255;
        if(event<20) {
            const AFDiaryEventLabel *label=af_diary_event_labels+event;
            if(!label->text || !label->size || label->size>48)return AF_DIARY_ARGUMENT;
            draw->event_label=label->text;draw->event_length=label->size;
            if(event<19)source=source_events[event];
        } else {
            source=event-20;
            if(source>=28 || af_holiday_dialogue_data.magic!=0x41464844 ||
               af_holiday_dialogue_data.version!=1 || af_holiday_dialogue_data.count!=3)return AF_DIARY_ARGUMENT;
            draw->event_label=af_holiday_dialogue_data.events[source];draw->event_length=16;
            while(draw->event_length && draw->event_label[draw->event_length-1]==' ')--draw->event_length;
            if(!draw->event_length)return AF_DIARY_ARGUMENT;
        }
        if(m->viewer==4)return AF_DIARY_OK;
        if(event==AF_DIARY_EVENT_BIRTHDAY) {
            int mark=af_diary_calendar_mark(live,m->owner,m->today,m->selected,c->special);
            if(mark<0)return mark;
            draw->event_attended=mark!=0;
        } else if(source!=255) {
            int mark=af_diary_calendar_event_check(live,m->owner,m->today,m->selected,source);
            if(mark<0)return mark;
            draw->event_attended=mark!=0;
        }
    }
    return AF_DIARY_OK;
}
